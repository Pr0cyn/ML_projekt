"""ML2: survey of the raw data (schema, label distributions, missing/inf values).

Everything is computed with DuckDB aggregates; the full table is never loaded
into pandas. The CSV is converted once, unchanged, to Parquet for faster scans.
"""

from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = ROOT / "data" / "raw" / "data.csv"
RAW_PARQUET = ROOT / "data" / "processed" / "raw.parquet"
REPORT = ROOT / "reports" / "01_felmeres.md"

LABEL_COLS = ["Label", "Traffic Type", "Traffic Subtype"]
TARGET = "Traffic Type"


def q(name: str) -> str:
    """Quote a column name for SQL."""
    return '"' + name.replace('"', '""') + '"'


def md_table(headers: list[str], rows: list[tuple]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for r in rows:
        lines.append("| " + " | ".join(fmt(v) for v in r) + " |")
    return "\n".join(lines)


def fmt(v) -> str:
    if isinstance(v, float):
        return f"{v:,.2f}".replace(",", " ")
    if isinstance(v, int):
        return f"{v:,}".replace(",", " ")
    return str(v)


def main() -> None:
    con = duckdb.connect()
    if not RAW_PARQUET.exists():
        RAW_PARQUET.parent.mkdir(parents=True, exist_ok=True)
        con.execute(
            f"COPY (SELECT * FROM read_csv_auto('{RAW_CSV.as_posix()}', header=true, sample_size=-1)) "
            f"TO '{RAW_PARQUET.as_posix()}' (FORMAT parquet)"
        )
    src = f"read_parquet('{RAW_PARQUET.as_posix()}')"

    schema = con.execute(f"DESCRIBE SELECT * FROM {src}").fetchall()
    cols = [(c[0], c[1]) for c in schema]
    n_rows = con.execute(f"SELECT COUNT(*) FROM {src}").fetchone()[0]
    float_cols = [c for c, t in cols if t in ("DOUBLE", "FLOAT")]

    out: list[str] = ["# 01 – Az adat felmérése (ML2)", ""]
    out += [f"- Sorok száma: **{fmt(n_rows)}**", f"- Oszlopok száma: **{len(cols)}**", ""]

    # --- 1. Columns and types
    type_counts: dict[str, int] = {}
    for _, t in cols:
        type_counts[t] = type_counts.get(t, 0) + 1
    out += ["## 1. Oszlopok és típusok", ""]
    out += ["Típusok összesítve: " + ", ".join(f"{t}: {n}" for t, n in type_counts.items()), ""]
    out += [md_table(["#", "Oszlop", "Típus"], [(i + 1, c, t) for i, (c, t) in enumerate(cols)]), ""]

    # --- 2. Label distributions
    out += ["## 2. A címkék eloszlása", ""]
    for lab in ["Label", "Traffic Type"]:
        rows = con.execute(
            f"SELECT {q(lab)}, COUNT(*) n, 100.0*COUNT(*)/{n_rows} pct "
            f"FROM {src} GROUP BY 1 ORDER BY n DESC"
        ).fetchall()
        out += [f"### {lab}", "", md_table([lab, "Sorok", "%"], rows), ""]
    rows = con.execute(
        f"SELECT {q('Traffic Type')}, {q('Traffic Subtype')}, {q('Label')}, COUNT(*) n, "
        f"100.0*COUNT(*)/{n_rows} pct FROM {src} GROUP BY 1,2,3 ORDER BY 1, n DESC"
    ).fetchall()
    out += ["### Traffic Subtype (a Traffic Type és a Label szerint)", "",
            md_table(["Traffic Type", "Traffic Subtype", "Label", "Sorok", "%"], rows), ""]

    # --- 3. Missing / inf per column
    aggs = []
    for c, t in cols:
        aggs.append(f"COUNT(*) FILTER (WHERE {q(c)} IS NULL)")
        if c in float_cols:
            aggs.append(f"COUNT(*) FILTER (WHERE isnan({q(c)}))")
            aggs.append(f"COUNT(*) FILTER (WHERE {q(c)} = 'inf'::DOUBLE)")
            aggs.append(f"COUNT(*) FILTER (WHERE {q(c)} = '-inf'::DOUBLE)")
    vals = list(con.execute(f"SELECT {', '.join(aggs)} FROM {src}").fetchone())
    stats = {}
    for c, _ in cols:
        null = vals.pop(0)
        nan, pinf, ninf = (vals.pop(0), vals.pop(0), vals.pop(0)) if c in float_cols else (0, 0, 0)
        stats[c] = (null, nan, pinf, ninf)
    bad_cols = [c for c, s in stats.items() if sum(s) > 0]

    out += ["## 3. Hiányzó és végtelen értékek oszloponként", ""]
    out += ["NULL = üres mező a CSV-ben, NaN = „NaN” érték, +inf / −inf = végtelen. "
            f"A {len(cols)} oszlopból **{len(bad_cols)}** érintett, a többiben egyik sem fordul elő.", ""]
    if bad_cols:
        rows = [(c, *stats[c], sum(stats[c]), 100.0 * sum(stats[c]) / n_rows) for c in bad_cols]
        out += [md_table(["Oszlop", "NULL", "NaN", "+inf", "−inf", "Összesen", "% (összes sor)"], rows), ""]

    # Cross-check on the raw text: DuckDB parsing must not hide inf/nan/empty fields
    raw_hits = {"inf": 0, "nan": 0, "empty": 0}
    tok_inf = {"inf", "+inf", "-inf", "infinity", "+infinity", "-infinity"}
    with RAW_CSV.open("r", encoding="utf-8") as f:
        next(f)
        for line in f:
            fields = line.rstrip("\r\n").lower().split(",")
            raw_hits["inf"] += any(x in tok_inf for x in fields)
            raw_hits["nan"] += "nan" in fields
            raw_hits["empty"] += "" in fields
    out += ["Ellenőrzés a nyers CSV szövegén (DuckDB-értelmezés nélkül, soronként): "
            f"`inf`/`infinity` tokent tartalmazó sor: **{fmt(raw_hits['inf'])}**, "
            f"`nan` tokent tartalmazó sor: **{fmt(raw_hits['nan'])}**, "
            f"üres mezőt tartalmazó sor: **{fmt(raw_hits['empty'])}**.", ""]
    zero_dur = con.execute(f"SELECT COUNT(*) FROM {src} WHERE {q('Flow Duration')} <= 0").fetchone()[0]
    out += [f"A `Flow Duration` ≤ 0 sorok száma: **{fmt(zero_dur)}**. Emiatt a /s-alapú "
            "oszlopokban (`Flow Bytes/s`, `Flow Packets/s`) nullával osztásból sem keletkezhet végtelen érték.", ""]

    # --- 4. Missing / inf per class (Traffic Type)
    def bad_expr(c: str) -> str:
        e = f"{q(c)} IS NULL"
        if c in float_cols:
            e += f" OR isnan({q(c)}) OR isinf({q(c)})"
        return f"({e})"

    classes = con.execute(
        f"SELECT {q(TARGET)}, COUNT(*) FROM {src} GROUP BY 1 ORDER BY 2 DESC"
    ).fetchall()
    class_names = [c for c, _ in classes]
    class_n = dict(classes)

    per_class_aggs = ", ".join(f"COUNT(*) FILTER (WHERE {bad_expr(c)})" for c in bad_cols)
    any_bad = " OR ".join(bad_expr(c) for c in bad_cols) if bad_cols else "FALSE"
    res = con.execute(
        f"SELECT {q(TARGET)}, {per_class_aggs + ', ' if bad_cols else ''}"
        f"COUNT(*) FILTER (WHERE {any_bad}) FROM {src} GROUP BY 1"
    ).fetchall()
    per_class = {r[0]: r[1:] for r in res}

    out += ["## 4. Hiányzó és végtelen értékek osztályonként (Traffic Type)", ""]
    out += ["Minden cellában: érintett sorok száma (az osztály hány %-a). "
            "Az utolsó oszlop azt mutatja, hány sor esne ki, ha minden olyan sort "
            "törölnénk, amelyben bármelyik oszlopban hiány vagy végtelen érték van.", ""]
    headers = ["Traffic Type", "Sorok"] + bad_cols + ["Bármelyik oszlopban"]
    rows = []
    for cl in class_names:
        cells = [f"{fmt(v)} ({100.0 * v / class_n[cl]:.2f}%)" for v in per_class[cl]]
        rows.append((cl, class_n[cl], *cells))
    out += [md_table(headers, rows), ""]

    # Same per Traffic Subtype, only the "any column" summary
    res = con.execute(
        f"SELECT {q(TARGET)}, {q('Traffic Subtype')}, COUNT(*) n, "
        f"COUNT(*) FILTER (WHERE {any_bad}) bad FROM {src} GROUP BY 1,2 ORDER BY 1, n DESC"
    ).fetchall()
    rows = [(t, s, n, b, 100.0 * b / n) for t, s, n, b in res]
    out += ["### Alosztályonként (Traffic Subtype), bármelyik oszlopban", "",
            md_table(["Traffic Type", "Traffic Subtype", "Sorok", "Érintett sorok", "%"], rows), ""]

    # --- 5. Negative values (possible hidden "missing" sentinels such as -1)
    num_cols = [c for c, t in cols if t in ("DOUBLE", "FLOAT", "BIGINT", "INTEGER")]
    neg = con.execute(
        "SELECT " + ", ".join(f"COUNT(*) FILTER (WHERE {q(c)} < 0)" for c in num_cols) + f" FROM {src}"
    ).fetchone()
    neg_cols = [(c, n) for c, n in zip(num_cols, neg) if n]
    out += ["## 5. Negatív értékek (rejtett hiányjelzők, pl. −1)", ""]
    out += ["A CICFlowMeter egyes verziói a −1 értékkel jelzik, ha egy mező nem mérhető. "
            "Ezért a numerikus oszlopokban a negatív értékeket is megszámoltam.", ""]
    if neg_cols:
        out += [md_table(["Oszlop", "Negatív értékű sorok"], neg_cols), ""]
        for c, _ in neg_cols:
            res = con.execute(
                f"SELECT {q(TARGET)}, COUNT(*) FILTER (WHERE {q(c)} < 0) n, MIN({q(c)}), "
                f"COUNT(*) FILTER (WHERE {q(c)} = -1) FROM {src} GROUP BY 1 HAVING n > 0 ORDER BY n DESC"
            ).fetchall()
            rows = [(t, n, 100.0 * n / class_n[t], mn, m1) for t, n, mn, m1 in res]
            out += [f"`{c}` osztályonként:", "",
                    md_table(["Traffic Type", "Negatív sorok", "% az osztályban", "Minimum", "Pontosan −1"], rows), ""]
    else:
        out += ["Egyik numerikus oszlopban sincs negatív érték.", ""]

    # --- Summary at the top
    n_benign = con.execute(f"SELECT COUNT(*) FROM {src} WHERE {q('Label')} = 'Benign'").fetchone()[0]
    n_sub = con.execute(f"SELECT COUNT(DISTINCT {q('Traffic Subtype')}) FROM {src}").fetchone()[0]
    smallest = classes[-1]
    summary = [
        "## Megállapítások", "",
        f"- **{fmt(n_rows)} sor, {len(cols)} oszlop.** Típusok: "
        + ", ".join(f"{t}: {n}" for t, n in type_counts.items()) + ".",
        f"- **A célváltozó (Traffic Type) {len(classes)} osztályú, és extrém kiegyensúlyozatlan.** "
        f"A legnagyobb osztály ({classes[0][0]}) {100.0 * classes[0][1] / n_rows:.2f}%, a legkisebb "
        f"({smallest[0]}) mindössze {fmt(smallest[1])} sor. Benign csak {fmt(n_benign)} sor "
        f"({100.0 * n_benign / n_rows:.3f}%). A Traffic Subtype {n_sub} egyedi értéket vesz fel.",
        f"- **Hiányzó (NULL/NaN) és végtelen (±inf) érték {'nincs' if not bad_cols else 'van'} az adatban.** "
        "Ezt a nyers szövegen is ellenőriztem (3. pont).",
        "- **Negatív értékek:** " + (", ".join(f"`{c}`: {fmt(n)} sor" for c, n in neg_cols) if neg_cols else "nincsenek")
        + " (részletek az 5. pontban).",
        "",
    ]
    out[5:5] = summary

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(out), encoding="utf-8")
    print(f"Rows: {n_rows:,}, columns: {len(cols)}, affected columns: {bad_cols}")
    print(f"Report written to {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
