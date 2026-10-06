"""ML5: column selection evidence, computed on the train set only.

For every column we record: keep/drop | category | reason | evidence.
Categories: identifier/network address, other label column, constant or
near-constant, highly correlated pair. Then a few candidate column sets are
compared with 5-fold stratified CV (macro F1) on train.
"""

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import mutual_info_classif
from sklearn.model_selection import StratifiedKFold, cross_validate

ROOT = Path(__file__).resolve().parents[1]
TRAIN_PARQUET = ROOT / "data" / "processed" / "train.parquet"
REPORT = ROOT / "reports" / "02_oszlopok.md"
OPTIONS_JSON = ROOT / "src" / "column_options.json"

TARGET = "Traffic Type"
RANDOM_STATE = 42
ID_COLS = ["Flow ID", "Src IP", "Src Port", "Dst IP", "Dst Port", "Timestamp"]
OTHER_LABELS = ["Label", "Traffic Subtype"]
NEAR_CONST_SHARE = 0.999  # top value covers >= 99.9% of rows
CORR_THRESHOLD = 0.95
TOP_K = 15


def md_table(headers: list[str], rows: list[tuple]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(str(v) for v in r) + " |" for r in rows]
    return "\n".join(lines)


def n_fmt(v: int) -> str:
    return f"{v:,}".replace(",", " ")


def purity(col: pd.Series, y: pd.Series) -> float:
    """Share of rows whose class equals the majority class of their column value.

    1.0 means the value alone determines the class.
    """
    ct = pd.crosstab(col, y)
    return float(ct.max(axis=1).sum() / len(col))


def cv_macro_f1(X: pd.DataFrame, y: pd.Series) -> tuple[float, float, float]:
    model = RandomForestClassifier(
        n_estimators=100, class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1
    )
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    t0 = time.perf_counter()
    res = cross_validate(model, X, y, cv=cv, scoring="f1_macro", n_jobs=1)
    return float(res["test_score"].mean()), float(res["test_score"].std()), time.perf_counter() - t0


def main() -> None:
    tr = pd.read_parquet(TRAIN_PARQUET)
    y = tr[TARGET]
    n = len(tr)
    decisions: dict[str, tuple[str, str, str, str]] = {}  # col -> (keep, category, reason, evidence)

    # --- 1. Identifier / network address columns
    id_ev = {}
    for c in ID_COLS:
        nu = tr[c].nunique()
        p = purity(tr[c], y)
        id_ev[c] = (nu, p)
        decisions[c] = ("kimarad", "azonosító / hálózati cím",
                        "tesztkörnyezet-specifikus, nem a forgalom viselkedését írja le, nem általánosít",
                        f"egyedi értékek: {n_fmt(nu)} ({100 * nu / n:.1f}%), tisztaság: {100 * p:.1f}%")
    ts_ranges = tr.groupby(TARGET)["Timestamp"].agg(["min", "max"]).sort_values("min")

    # --- 2. Other label columns
    sub_per_type = tr.groupby("Traffic Subtype")[TARGET].nunique().max()
    label_per_type = tr.groupby(TARGET)["Label"].nunique().max()
    decisions["Label"] = ("kimarad", "címkeoszlop",
                          "a célváltozóból származik, a modell bemeneteként szivárogtatná a választ",
                          f"minden Traffic Type-hoz pontosan {label_per_type} Label érték tartozik; "
                          f"tisztaság: {100 * purity(tr['Label'], y):.1f}%")
    decisions["Traffic Subtype"] = ("kimarad", "címkeoszlop",
                                    "a célváltozó finomabb bontása, egyértelműen meghatározza",
                                    f"minden alosztály pontosan {sub_per_type} Traffic Type-ba tartozik; "
                                    f"tisztaság: {100 * purity(tr['Traffic Subtype'], y):.1f}%")
    decisions[TARGET] = ("cél", "célváltozó", "ezt tanulja meg a modell", f"{y.nunique()} osztály")

    # --- 3. Constant / near-constant
    features = [c for c in tr.columns if c not in ID_COLS + OTHER_LABELS + [TARGET]]
    stats = {}
    for c in features:
        vc = tr[c].value_counts()
        stats[c] = dict(nunique=int(tr[c].nunique()), top=float(vc.index[0]),
                        share=float(vc.iloc[0] / n), var=float(tr[c].var()))
    constant = [c for c in features if stats[c]["nunique"] == 1]
    near_const = [c for c in features if c not in constant and stats[c]["share"] >= NEAR_CONST_SHARE]
    for c in constant:
        decisions[c] = ("kimarad", "konstans", "egyetlen értéket vesz fel, nem hordoz információt",
                        f"egyedi értékek: 1 (mindig {stats[c]['top']:g}), variancia: 0")
    for c in near_const:
        nontop = y[tr[c] != stats[c]["top"]].value_counts().to_dict()
        decisions[c] = ("kimarad", "közel konstans",
                        f"a leggyakoribb érték a sorok ≥ {100 * NEAR_CONST_SHARE:g}%-a",
                        f"leggyakoribb érték aránya: {100 * stats[c]['share']:.3f}%, eltérő sorok osztályai: {nontop}")
    top_share_rank = sorted(((stats[c]["share"], c) for c in features if c not in constant), reverse=True)[:5]

    # --- 4. Highly correlated pairs (greedy: highest |r| first, drop the member with lower MI)
    cand = [c for c in features if c not in constant + near_const]
    t0 = time.perf_counter()
    mi = pd.Series(mutual_info_classif(tr[cand], y, random_state=RANDOM_STATE, n_jobs=-1), index=cand)
    mi_time = time.perf_counter() - t0
    corr = tr[cand].corr(method="pearson").abs()
    upper = corr.where(np.triu(np.ones(corr.shape, dtype=bool), k=1)).stack()
    pairs = upper[upper > CORR_THRESHOLD].sort_values(ascending=False)
    dropped_corr: dict[str, tuple[str, float]] = {}
    pair_rows = []
    for (a, b), r in pairs.items():
        if a in dropped_corr or b in dropped_corr:
            winner_note = "már eldőlt (az egyik tag korábban kimaradt)"
            pair_rows.append((a, b, f"{r:.3f}", f"{mi[a]:.3f}", f"{mi[b]:.3f}", winner_note))
            continue
        keep, drop = (a, b) if mi[a] >= mi[b] else (b, a)
        dropped_corr[drop] = (keep, r)
        pair_rows.append((a, b, f"{r:.3f}", f"{mi[a]:.3f}", f"{mi[b]:.3f}", f"marad: **{keep}**"))
    for c, (keep, r) in dropped_corr.items():
        decisions[c] = ("kimarad", "erősen korreláló pár",
                        f"szinte ugyanazt méri, mint a(z) `{keep}`, amely több információt hordoz a célról",
                        f"\\|r\\| = {r:.3f} a(z) `{keep}` oszloppal; MI: {mi[c]:.3f} vs {mi[keep]:.3f}")

    kept = [c for c in cand if c not in dropped_corr]
    for c in kept:
        decisions[c] = ("marad", "jellemző", "nem konstans, és nincs \\|r\\| > 0,95 párja a megmaradó oszlopok között",
                        f"egyedi értékek: {n_fmt(stats[c]['nunique'])}, MI: {mi[c]:.3f}")

    # --- 5. Candidate column sets compared with CV on train
    options = {
        "A": ("csak azonosítók, címkék és konstansok nélkül", cand),
        "B": (f"A + korrelációs szűrés (\\|r\\| > {CORR_THRESHOLD})", kept),
        "C": (f"B közül a {TOP_K} legnagyobb MI-jű oszlop", list(mi[kept].sort_values(ascending=False).index[:TOP_K])),
    }
    cv_rows = []
    for key, (desc, cols) in options.items():
        mean, std, secs = cv_macro_f1(tr[cols], y)
        cv_rows.append((key, desc, len(cols), f"{mean:.4f} ± {std:.4f}", f"{secs:.0f} s"))
        print(f"option {key}: {len(cols)} cols, macro F1 {mean:.4f} ± {std:.4f}, {secs:.0f}s")
    OPTIONS_JSON.write_text(json.dumps({k: v[1] for k, v in options.items()}, indent=2), encoding="utf-8")

    # --- Report
    counts = pd.Series([d[1] for c, d in decisions.items() if d[0] == "kimarad"]).value_counts()
    out = ["# 02 – Oszlopválasztás (ML5, döntési pont)", "",
           f"Minden mérés a **train-halmazon** ({n_fmt(n)} sor) készült, a teszthalmazt nem érintettem.", ""]
    out += ["## Összefoglalás", "",
            f"- Kiinduló oszlopok: {len(tr.columns)} (ebből 1 célváltozó).",
            *[f"- Kimarad – {cat}: **{cnt}**" for cat, cnt in counts.items()],
            f"- **Marad (javasolt B opció): {len(kept)} jellemző.**", ""]

    out += ["## 1. Azonosítók és hálózati címek", "",
            "A **tisztaság** azt mutatja, hogy a sorok hány százalékában egyezik a sor osztálya az oszlop "
            "adott értékénél leggyakoribb osztállyal. 100% esetén az oszlop értéke önmagában megmondja az "
            "osztályt.", "",
            f"- A `Flow ID` a sorok {100 * id_ev['Flow ID'][0] / n:.0f}%-ában egyedi, ezért a magas tisztaság itt azt "
            "jelenti, hogy a modell egyedi kapcsolatokat magolna be, ami új adatra nem visz át. A `Timestamp` "
            "másodperces felbontású, és a felvételek időpontját kódolja (lásd lent).",
            f"- Az IP-címekből csak {id_ev['Src IP'][0]}, illetve {id_ev['Dst IP'][0]} különböző van, mégis a "
            "sorok kb. 82%-ában megmondják az osztályt. Ez a tesztkörnyezet felépítését tükrözi (melyik gép "
            "támadott melyiket), nem a forgalom viselkedését. Egy másik hálózaton használhatatlan lenne.",
            "- A portok hasonlóan működnek: a `Src Port` véletlenszerű kliensport, a `Dst Port` a célgép "
            "szolgáltatását jelzi.", "",
            md_table(["Oszlop", "Egyedi értékek", "Tisztaság"],
                     [(c, n_fmt(nu), f"{100 * p:.1f}%") for c, (nu, p) in id_ev.items()]), "",
            "A `Timestamp` osztályonkénti időtartománya. A legtöbb érték hibás, 1970-es dátum (epoch-hiba), "
            "a Mirai viszont 2023-as. Az évszám önmagában elárulná a Mirai osztályt, ez egyértelmű szivárgás:", "",
            md_table(["Traffic Type", "Első flow", "Utolsó flow"],
                     [(t, r["min"], r["max"]) for t, r in ts_ranges.iterrows()]), "",
            "Megjegyzés: a `Dst Port` vitatható eset, mert a szolgáltatást jelzi (pl. 22 = SSH), ami "
            "valós tudás is lehet. A port azonban könnyen megváltoztatható, és ebben az adatban "
            f"{100 * id_ev['Dst Port'][1]:.1f}%-ban megmondja az osztályt, vagyis főleg a tesztkörnyezet "
            "felépítését kódolja. Ezért a feladat szerint kimarad.", ""]

    out += ["## 2. Konstans és közel konstans oszlopok", "",
            f"Konstans (1 egyedi érték): {', '.join(f'`{c}`' for c in constant)}.", "",
            f"Közel konstans (a leggyakoribb érték ≥ {100 * NEAR_CONST_SHARE:g}%): "
            + (", ".join(f"`{c}`" for c in near_const) if near_const else "**nincs**") + ". "
            "A legmagasabb dominanciájú nem konstans oszlopok: "
            + ", ".join(f"`{c}` ({100 * s:.2f}%)" for s, c in top_share_rank) + ". "
            "A küszöböt szándékosan magasra tettem. Egy oszlop, amely a sorok 99,6%-ában 0, épp a "
            "0,4%-nyi benign forgalmat különítheti el, ezért alacsonyabb küszöbnél ellenőrizni kellene, "
            "melyik osztályban térnek el az értékek.", ""]

    out += ["## 3. Erősen korreláló párok", "",
            f"Pearson-korreláció, \\|r\\| > {CORR_THRESHOLD}. A párokat csökkenő |r| szerint dolgoztam fel. "
            "Mindkét tag még megvan → az marad, amelyiknek nagyobb a kölcsönös információja (MI) a Traffic "
            "Type-pal; a másik kimarad. Ha egy tag már korábban kimaradt, a pár már eldőlt. "
            f"Az MI számítása (`mutual_info_classif`, random_state={RANDOM_STATE}) {mi_time:.0f} másodpercig tartott.", "",
            md_table(["A oszlop", "B oszlop", "\\|r\\|", "MI (A)", "MI (B)", "Döntés"], pair_rows), ""]

    out += ["## 4. Opciók összevetése keresztvalidációval", "",
            "RandomForest (100 fa, `class_weight='balanced'`, random_state=42), 5-fold rétegzett "
            "keresztvalidáció a train-halmazon, macro F1. Ez csak az oszlophalmazok összehasonlítására "
            "szolgál, a modellválasztás az ML7-ben lesz. Megjegyzés: a korrelációs és MI-alapú szűrést a "
            "teljes train-halmazon számoltam, ezért a CV-értékek enyhén optimisták lehetnek, de az "
            "opciók egymáshoz mért különbsége ettől még értelmezhető.", "",
            md_table(["Opció", "Leírás", "Oszlopok", "Macro F1 (átlag ± szórás)", "Idő"], cv_rows), "",
            "**A különbségek kicsik: mindhárom átlag egy szóráson belül van.** A nagy szórást főleg a "
            "Background osztály okozza, amelyből foldonként csak 4–5 sor jut a validációra. A szűkítés tehát "
            "mérhetően nem rontja érdemben a teljesítményt, a döntést ezért az egyszerűség és a "
            "magyarázhatóság alapján lehet meghozni.", "",
            "**Előnyök és hátrányok:**", "",
            "- **A** – a legtöbb információ marad meg, de sok a redundáns oszlop: nehezebb elmagyarázni, "
            "a lineáris modellnél pedig a multikollinearitás instabil együtthatókat okoz.",
            "- **B** – csak a mérhetően felesleges oszlopok esnek ki (konstans, \\|r\\| > 0,95 másolat), "
            "ezért minden kidobott oszlop egy mért számmal indokolható. **Ezt javaslom.**",
            f"- **C** – a legegyszerűbb ({TOP_K} oszlop), de a k szám önkényes, és az MI egyenként nézi az "
            "oszlopokat, így kieshet olyan, ami csak más oszlopokkal együtt hasznos.", ""]

    out += ["## 5. Minden oszlop egyenként", "",
            md_table(["Oszlop", "Marad / kimarad", "Kategória", "Indok", "Bizonyíték"],
                     [(c, *decisions[c]) for c in tr.columns]), ""]
    REPORT.write_text("\n".join(out), encoding="utf-8")
    print(f"constant {len(constant)}, near-constant {len(near_const)}, corr-dropped {len(dropped_corr)}, kept {len(kept)}")


if __name__ == "__main__":
    main()
