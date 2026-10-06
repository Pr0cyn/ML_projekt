"""ML3: stratified sample (all benign rows + at most N rows per Traffic Subtype),
followed by exact-duplicate removal.

Only the row index and the label columns are loaded into pandas for sampling;
the selected rows are then fetched from Parquet by row number with DuckDB.
Neither step learns anything from the feature values.
"""

from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_PARQUET = ROOT / "data" / "processed" / "raw.parquet"
SAMPLE_PARQUET = ROOT / "data" / "processed" / "sample.parquet"
REPORT = ROOT / "reports" / "01b_mintavetel.md"

N_PER_SUBTYPE = 20_000
N_CANDIDATES = [10_000, 20_000, 50_000, 100_000]
RANDOM_STATE = 42

LABEL_COLS = ["Label", "Traffic Type", "Traffic Subtype"]
ID_COLS = ["Flow ID", "Src IP", "Src Port", "Dst IP", "Dst Port", "Timestamp"]


def md_table(headers: list[str], rows: list[tuple]) -> str:
    def fmt(v) -> str:
        if isinstance(v, float):
            return f"{v:.2f}"
        if isinstance(v, int):
            return f"{v:,}".replace(",", " ")
        return str(v)

    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(fmt(v) for v in r) + " |" for r in rows]
    return "\n".join(lines)


def sample_index(idx: pd.DataFrame, n: int) -> pd.DataFrame:
    """All benign rows, plus at most n rows per malicious Traffic Subtype."""
    parts = [idx[idx["Label"] == "Benign"]]
    for _, g in idx[idx["Label"] != "Benign"].groupby("Traffic Subtype", sort=True):
        parts.append(g if len(g) <= n else g.sample(n=n, random_state=RANDOM_STATE))
    return pd.concat(parts).sort_values("rid")


def main() -> None:
    con = duckdb.connect()
    src = f"read_parquet('{RAW_PARQUET.as_posix()}', file_row_number=true)"

    idx = con.execute(
        f'SELECT file_row_number AS rid, "Label", "Traffic Type", "Traffic Subtype" '
        f"FROM {src} ORDER BY rid"
    ).df()
    n_total = len(idx)

    # --- Sample sizes per Traffic Type for candidate N values (counts only)
    full_counts = idx["Traffic Type"].value_counts()
    cand = {}
    for n in N_CANDIDATES:
        capped = idx.groupby(["Label", "Traffic Type", "Traffic Subtype"]).size()
        capped = capped.where(capped.index.get_level_values("Label") == "Benign", capped.clip(upper=n))
        cand[n] = capped.groupby(level="Traffic Type").sum()

    sub_sizes = idx.groupby("Traffic Subtype").size()
    n_subtypes = len(sub_sizes)
    n_capped = int((sub_sizes > N_PER_SUBTYPE).sum())

    # --- Draw the sample with the chosen N and fetch the rows
    sel = sample_index(idx, N_PER_SUBTYPE)[["rid"]]
    con.register("sel", sel)
    df = con.execute(
        f"SELECT * EXCLUDE (file_row_number) FROM {src} "
        f"WHERE file_row_number IN (SELECT rid FROM sel) ORDER BY file_row_number"
    ).df()
    n_sampled = len(df)
    assert n_sampled == len(sel)

    # --- Exact duplicates
    feature_cols = [c for c in df.columns if c not in ID_COLS + LABEL_COLS]
    dedup_key = feature_cols + LABEL_COLS
    dup_all = df.duplicated(keep="first")
    dup_key = df.duplicated(subset=dedup_key, keep="first")
    conflict = df.groupby(feature_cols, dropna=False)["Traffic Type"].transform("nunique") > 1

    before_sub = df.groupby(["Traffic Type", "Traffic Subtype"]).size()
    removed_sub = df[dup_key].groupby(["Traffic Type", "Traffic Subtype"]).size()
    df = df[~dup_key].reset_index(drop=True)
    conflict_after = conflict[~dup_key.values].sum()

    SAMPLE_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(SAMPLE_PARQUET, index=False)

    # --- Report
    out = ["# 01b – Rétegzett minta és duplikátumszűrés (ML3)", ""]
    out += ["## 1. Az N megválasztása", "",
            "A minta az összes benign sorból és Traffic Subtype-onként legfeljebb N véletlenszerűen "
            f"választott malicious sorból áll (`random_state={RANDOM_STATE}`). Ha egy alosztálynak N-nél "
            "kevesebb sora van, mind bekerül. A táblázat a minta méretét mutatja Traffic Type szerint "
            "a duplikátumszűrés előtt, néhány lehetséges N-re.", ""]
    rows = [(t, int(full_counts[t]), *[int(cand[n][t]) for n in N_CANDIDATES]) for t in full_counts.index]
    rows.append(("**Összesen**", n_total, *[int(cand[n].sum()) for n in N_CANDIDATES]))
    out += [md_table(["Traffic Type", "Teljes adat"] + [f"N = {n:,}".replace(",", " ") for n in N_CANDIDATES], rows), ""]
    out += [f"**Választott: N = {N_PER_SUBTYPE:,}**".replace(",", " ") + ". Indokok:",
            f"- A {n_subtypes} Traffic Subtype közül {n_capped} alosztálynak van N-nél több sora. A többi {n_subtypes - n_capped} "
            "teljes egészében bekerül, köztük a DoS ICMP (9), a DoS MAC (30), a Mirai GREETH (43) "
            "és mind a 6 benign alosztály.",
            "- A kb. 310 ezer soros minta 77 jellemzővel elég ahhoz, hogy a legnagyobb osztályokat is jól "
            "lefedje. Ugyanakkor elég kicsi ahhoz, hogy az 5-fold keresztvalidáció a lassabb modellekkel "
            "(LogisticRegression, RandomForest) is percek alatt lefusson.",
            "- Nagyobb N főleg a DoS-t és az Information Gatheringet növelné. A ritka osztályok mérete nem "
            "változna, így a kiegyensúlyozatlanság csak romlana.",
            "- Mellékhatás: az alosztályonkénti plafon miatt a mintában a Traffic Type arányok eltérnek a teljes "
            f"adatétól. A DoS (12 alosztály) aránya {100.0 * cand[N_PER_SUBTYPE]['DoS'] / cand[N_PER_SUBTYPE].sum():.1f}%, "
            f"az egyetlen alosztályú Information Gatheringé {100.0 * cand[N_PER_SUBTYPE]['Information Gathering'] / cand[N_PER_SUBTYPE].sum():.1f}% "
            "(a duplikátumszűrés előtt). "
            "Ez szándékos, mert így a ritkább osztályok nagyobb súlyt kapnak.", ""]

    out += ["## 2. Pontos duplikátumok", "",
            f"Mintavétel után: **{n_sampled:,}** sor.".replace(",", " "), "",
            md_table(["Duplikátum-kulcs", "Duplikátum sorok a mintában"], [
                ("mind a 86 oszlop", int(dup_all.sum())),
                (f"{len(feature_cols)} jellemző + 3 címke (azonosító oszlopok nélkül)", int(dup_key.sum())),
            ]), "",
            "**A szűrés kulcsa: a 77 jellemző és a 3 címke, a 6 azonosító oszlop (Flow ID, Src/Dst IP, "
            "Src/Dst Port, Timestamp) nélkül.** A teljes sorra nézve gyakorlatilag nincs duplikátum, mert a "
            "Flow ID és a Timestamp minden sorban más. Ezek az oszlopok viszont nem kerülnek a modellbe "
            "(ML5, azonosító kategória). A modell szemszögéből ezért két sor akkor azonos, ha a jellemzőik "
            "megegyeznek. Ha az ilyen sorok bennmaradnának, ugyanaz a jellemzővektor a train- és a "
            "teszthalmazba is bekerülhetne, ami túl optimista teszteredményt adna. A megtartott sor mindig "
            "az eredeti fájlban előbb szereplő.", ""]
    rows = [(t, s, int(before_sub[(t, s)]), int(removed_sub.get((t, s), 0)),
             int(before_sub[(t, s)] - removed_sub.get((t, s), 0))) for t, s in before_sub.index]
    out += ["### Alosztályonként", "",
            md_table(["Traffic Type", "Traffic Subtype", "Minta", "Törölt duplikátum", "Marad"], rows), ""]
    after_type = df["Traffic Type"].value_counts()
    rows = [(t, int(n), 100.0 * n / len(df)) for t, n in after_type.items()]
    out += ["### A végleges minta Traffic Type szerint", "",
            md_table(["Traffic Type", "Sorok", "%"], rows), "",
            f"Végleges minta: **{len(df):,}** sor, {df.shape[1]} oszlop → `data/processed/sample.parquet`.".replace(",", " "), ""]
    out += ["## 3. Ütköző címkék", "",
            f"A szűrés után **{int(conflict_after)}** sor olyan, hogy ugyanaz a jellemzővektor egynél több "
            "Traffic Type címkével is előfordul. Ezeket a sorokat egyetlen modell sem tudja mind helyesen "
            "osztályozni. Nem töröltem őket, mert valós mérésekből származnak, csak jelzem a létezésüket "
            "(a teljes adatban 118 ilyen jellemzővektor van, 4 762 sorban).", ""]

    REPORT.write_text("\n".join(out), encoding="utf-8")
    print(f"Sampled {n_sampled:,} rows, removed {int(dup_key.sum()):,} duplicates "
          f"(all-86-col duplicates: {int(dup_all.sum()):,}), final {len(df):,} rows.")
    print(after_type.to_string())


if __name__ == "__main__":
    main()
