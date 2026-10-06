"""ML4: 70/30 train/test split, stratified by Traffic Type.

After this step the test set is locked: every later step that learns from the
data (column selection, imputation, scaling, model selection) uses train only.
"""

from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
SAMPLE_PARQUET = PROCESSED / "sample.parquet"
TRAIN_PARQUET = PROCESSED / "train.parquet"
TEST_PARQUET = PROCESSED / "test.parquet"
REPORT = ROOT / "reports" / "01d_split.md"

TARGET = "Traffic Type"
TEST_SIZE = 0.30
RANDOM_STATE = 42

ID_COLS = ["Flow ID", "Src IP", "Src Port", "Dst IP", "Dst Port", "Timestamp"]
LABEL_COLS = ["Label", "Traffic Type", "Traffic Subtype"]


def md_table(headers: list[str], rows: list[tuple]) -> str:
    def fmt(v) -> str:
        if isinstance(v, float):
            return f"{v:.3f}"
        if isinstance(v, int):
            return f"{v:,}".replace(",", " ")
        return str(v)

    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(fmt(v) for v in r) + " |" for r in rows]
    return "\n".join(lines)


def proportion_rows(full: pd.Series, train: pd.Series, test: pd.Series) -> list[tuple]:
    n_full, n_train, n_test = full.value_counts(), train.value_counts(), test.value_counts()
    rows = []
    for cls in n_full.index:
        p_full = 100.0 * n_full[cls] / len(full)
        p_train = 100.0 * n_train.get(cls, 0) / len(train)
        p_test = 100.0 * n_test.get(cls, 0) / len(test)
        rows.append((cls, int(n_full[cls]), int(n_train.get(cls, 0)), int(n_test.get(cls, 0)),
                     p_full, p_train, p_test, max(abs(p_train - p_full), abs(p_test - p_full))))
    return rows


def main() -> None:
    df = pd.read_parquet(SAMPLE_PARQUET)
    train, test = train_test_split(
        df, test_size=TEST_SIZE, stratify=df[TARGET], random_state=RANDOM_STATE
    )
    train = train.reset_index(drop=True)
    test = test.reset_index(drop=True)
    train.to_parquet(TRAIN_PARQUET, index=False)
    test.to_parquet(TEST_PARQUET, index=False)

    # Sanity check: no feature vector may appear in both sets (ML3 deduplicated on this key)
    feature_cols = [c for c in df.columns if c not in ID_COLS + LABEL_COLS]
    overlap = len(train[feature_cols + LABEL_COLS].merge(test[feature_cols + LABEL_COLS], how="inner"))

    headers = ["Osztály", "Minta", "Train", "Test", "Minta %", "Train %", "Test %", "Max. eltérés (%-pont)"]
    type_rows = proportion_rows(df[TARGET], train[TARGET], test[TARGET])
    sub_rows = proportion_rows(df["Traffic Subtype"], train["Traffic Subtype"], test["Traffic Subtype"])
    max_dev_type = max(r[-1] for r in type_rows)
    max_dev_sub = max(r[-1] for r in sub_rows)
    missing_sub_test = [r[0] for r in sub_rows if r[3] == 0]

    out = ["# 01d – Train/test split (ML4)", ""]
    n = lambda v: f"{v:,}".replace(",", " ")
    out += [f"- Minta: **{n(len(df))}** sor → train: **{n(len(train))}** ({100 * len(train) / len(df):.1f}%), "
            f"test: **{n(len(test))}** ({100 * len(test) / len(df):.1f}%).",
            f"- `train_test_split(test_size={TEST_SIZE}, stratify=Traffic Type, random_state={RANDOM_STATE})`.",
            f"- A legnagyobb aránybeli eltérés a mintához képest Traffic Type szerint **{max_dev_type:.3f}** "
            f"százalékpont, Traffic Subtype szerint {max_dev_sub:.3f} százalékpont.",
            f"- Train és test között közös (jellemzők + címkék szerint azonos) sor: **{overlap}**.",
            "- **Innentől a teszthalmaz zárolva van.** Csak egyszer, az ML8 végső kiértékelésénél használjuk.", ""]
    out += ["## Osztályarányok Traffic Type szerint (erre rétegeztünk)", "", md_table(headers, type_rows), ""]
    out += ["## Ellenőrzés Traffic Subtype szerint (erre nem rétegeztünk)", "",
            "A rétegzés csak a Traffic Type-ra vonatkozik, az alosztályok aránya a véletlen miatt kicsit "
            "jobban ingadozhat. "
            + (f"A tesztbe nem jutott sor ezekből: {', '.join(missing_sub_test)}."
               if missing_sub_test else "Minden alosztályból jutott sor a tesztbe is."), "",
            md_table(headers, sub_rows), ""]
    REPORT.write_text("\n".join(out), encoding="utf-8")

    print(f"train {train.shape}, test {test.shape}, max dev type {max_dev_type:.3f} pp, "
          f"subtype {max_dev_sub:.3f} pp, overlap {overlap}, subtypes missing from test: {missing_sub_test}")


if __name__ == "__main__":
    main()
