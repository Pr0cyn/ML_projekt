"""ML1: sanity check of the raw CSV without loading it into memory."""

from pathlib import Path

import duckdb

RAW_CSV = Path(__file__).resolve().parents[1] / "data" / "raw" / "data.csv"


def main() -> None:
    size_gb = RAW_CSV.stat().st_size / 1024**3
    print(f"File: {RAW_CSV.name}, size: {size_gb:.2f} GB")

    with RAW_CSV.open("r", encoding="utf-8") as f:
        header = f.readline().strip().split(",")
    print(f"Columns: {len(header)}")
    label_cols = [c for c in header if c in ("Label", "Traffic Type", "Traffic Subtype")]
    print(f"Label columns found: {label_cols}")

    con = duckdb.connect()
    n_rows = con.execute(
        "SELECT COUNT(*) FROM read_csv_auto(?, header=true)", [str(RAW_CSV)]
    ).fetchone()[0]
    print(f"Rows (excluding header): {n_rows:,}")


if __name__ == "__main__":
    main()
