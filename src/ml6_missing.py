"""ML6: missing-value evidence and options, computed on the train set only.

1. Count NaN / +inf / -inf in the 54 selected columns, per column and per class.
2. Show what each option (row deletion, median imputation, median + missing
   indicator) would touch.
3. The only anomaly found in ML2 is negative `Flow IAT Min` (Audio/Text only):
   compare keeping it vs treating it as missing, with 5-fold CV inside a Pipeline.
"""

import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict, cross_validate
from sklearn.pipeline import Pipeline

from preprocessing import (
    RANDOM_STATE, TARGET, column_selector, inf_to_nan_step, load_selected_columns, negative_to_nan_step,
)

ROOT = Path(__file__).resolve().parents[1]
TRAIN_PARQUET = ROOT / "data" / "processed" / "train.parquet"
REPORT = ROOT / "reports" / "03_hianyzo_adatok.md"
NEG_COL = "Flow IAT Min"
WATCH_CLASSES = ["Audio", "Text"]


def md_table(headers: list[str], rows: list[tuple]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(str(v) for v in r) + " |" for r in rows]
    return "\n".join(lines)


def build_pipeline(columns: list[str], neg_as_missing: bool, add_indicator: bool) -> Pipeline:
    steps = [("select", column_selector(columns)), ("inf_to_nan", inf_to_nan_step())]
    if neg_as_missing:
        steps.append(("neg_to_nan", negative_to_nan_step([NEG_COL])))
    steps += [
        ("impute", SimpleImputer(strategy="median", add_indicator=add_indicator).set_output(transform="pandas")),
        ("model", RandomForestClassifier(n_estimators=100, class_weight="balanced",
                                         random_state=RANDOM_STATE, n_jobs=-1)),
    ]
    return Pipeline(steps)


def main() -> None:
    tr = pd.read_parquet(TRAIN_PARQUET)
    cols = load_selected_columns()
    y = tr[TARGET]
    X = tr[cols]
    class_n = y.value_counts()

    # --- 1. NaN / inf counts
    n_nan = X.isna().sum()
    n_pinf = (X == np.inf).sum()
    n_ninf = (X == -np.inf).sum()
    bad = (X.isna() | np.isinf(X)).any(axis=1)
    total_bad_cells = int(n_nan.sum() + n_pinf.sum() + n_ninf.sum())

    # --- 2. Negative Flow IAT Min per class
    neg = X[NEG_COL] < 0
    neg_by_class = y[neg].value_counts()
    neg_rows = [(c, int(class_n[c]), int(neg_by_class.get(c, 0)), f"{100 * neg_by_class.get(c, 0) / class_n[c]:.1f}%",
                 f"{X.loc[neg & (y == c), NEG_COL].min():g}" if neg_by_class.get(c, 0) else "–")
                for c in class_n.index]

    # --- 3. CV comparison of the negative-value treatments
    variants = {
        "1": ("A negatív érték marad (valós mért értékként kezeljük)", False, False),
        "2": ("Negatív → NaN, medián-imputálás", True, False),
        "3": ("Negatív → NaN, medián-imputálás + hiányjelző oszlop", True, True),
    }
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    cv_rows = []
    for key, (desc, neg_nan, ind) in variants.items():
        pipe = build_pipeline(cols, neg_nan, ind)
        t0 = time.perf_counter()
        res = cross_validate(pipe, tr, y, cv=cv, scoring="f1_macro")
        pred = cross_val_predict(pipe, tr, y, cv=cv)
        secs = time.perf_counter() - t0
        per_class = f1_score(y, pred, labels=WATCH_CLASSES, average=None)
        cv_rows.append((key, desc, f"{res['test_score'].mean():.4f} ± {res['test_score'].std():.4f}",
                        *[f"{v:.3f}" for v in per_class], f"{secs:.0f} s"))
        print(f"variant {key}: macro F1 {res['test_score'].mean():.4f} ± {res['test_score'].std():.4f}, "
              f"F1 {dict(zip(WATCH_CLASSES, per_class.round(3)))}")

    # --- Report
    out = ["# 03 – Hiányzó adatok (ML6, döntési pont)", "",
           f"Minden mérés a **train-halmazon** ({len(tr):,} sor) és az ML5-ben kiválasztott "
           f"**{len(cols)} oszlopon** készült.".replace(",", " "), ""]
    out += ["## 1. NaN és végtelen értékek", "",
            "Az első lépés minden opciónál ugyanaz: a +inf és −inf értékeket NaN-ná alakítjuk "
            "(`inf_to_nan`), mert a scikit-learn modellek végtelen értékre hibát dobnak.", "",
            md_table(["Mérés", "Érték"], [
                ("NaN cellák", int(n_nan.sum())), ("+inf cellák", int(n_pinf.sum())),
                ("−inf cellák", int(n_ninf.sum())), ("Érintett sorok", int(bad.sum())),
                ("Érintett oszlopok", int(((n_nan + n_pinf + n_ninf) > 0).sum())),
            ]), "",
            "**A train-halmazban nincs hiányzó és végtelen érték** (összesen "
            f"{total_bad_cells} érintett cella). Ez egyezik az ML2-vel, ahol a teljes 8,66 millió sort és a "
            "nyers CSV-szöveget is ellenőriztem.", ""]

    out += ["## 2. A három opció, és mit érintene", "",
            md_table(["Opció", "Mit csinál", "Érintett sorok / osztály most", "Előny", "Hátrány"], [
                ("Sorok törlése", "a hiányos sort eldobjuk", f"{int(bad.sum())} sor, egyik osztály sem",
                 "egyszerű, nem talál ki értéket",
                 "éles használatban egy flow-t nem lehet „kihagyni”, azt is osztályozni kell; ha a hiány "
                 "egy osztályhoz kötődik, azt az osztályt tizedeli meg; a Pipeline nem tud sort törölni"),
                ("Medián-imputálás", "a hiányzó értéket a train-medián pótolja (`SimpleImputer`)",
                 f"{int(bad.sum())} sor, egyik osztály sem",
                 "minden sor megmarad; a medián robusztus a kiugró értékekre (a flow-adatok erősen ferdék)",
                 "elfedi, hogy az érték hiányzott"),
                ("Medián + hiányjelző", "mint előbb, és egy 0/1 oszlop jelzi, hol volt hiány (`add_indicator=True`)",
                 f"{int(bad.sum())} sor, egyik osztály sem",
                 "ha a hiány maga is információ, a modell látja",
                 "csak azokhoz az oszlopokhoz készül jelző, ahol a train-ben volt hiány; itt egyikben sem, "
                 "így most nem ad hozzá semmit"),
            ]), "",
            "Mivel most semmi nem hiányzik, ezen az adaton a három opció **ugyanazt az eredményt adja**. "
            "A választás arról szól, mi történjen egy új adaton, ahol már előfordulhat hiány vagy végtelen "
            "érték (pl. 0 hosszú flow → nullával osztás a /s oszlopokban).", ""]

    out += [f"## 3. Az egyetlen anomália: negatív `{NEG_COL}`", "",
            f"A `{NEG_COL}` a flow két egymást követő csomagja közötti legrövidebb idő. Fizikailag nem lehet "
            "negatív, ezért ez valószínűleg időbélyeg-hiba a felvételben (a csomagok nem időrendben "
            "érkeztek). A negatív értékek csak két benign osztályban fordulnak elő:", "",
            md_table(["Traffic Type", "Sorok (train)", "Negatív", "Az osztály %-a", "Minimum"], neg_rows), "",
            "**Ha ezeket a sorokat törölnénk, az Audio osztály kb. negyede és a Text osztály kb. hetede "
            "elveszne.** Ez pontosan az a helyzet, amire a feladat figyelmeztetett: a hiány (itt: a hibás "
            "érték) egy osztályhoz kötődik, így a sorok törlése megtizedelné azt az osztályt.", "",
            "A három kezelési mód 5-fold rétegzett keresztvalidációval, Pipeline-on belül (az imputálás "
            "foldonként csak a tanító részen illeszkedik), RandomForest modellel (100 fa, "
            "`class_weight='balanced'`). Az Audio és Text oszlop az adott osztály F1-értéke a "
            "keresztvalidált jóslatokon:", "",
            md_table(["Változat", "Kezelés", "Macro F1 (átlag ± szórás)", "F1 Audio", "F1 Text", "Idő"], cv_rows), ""]
    REPORT.write_text("\n".join(out), encoding="utf-8")
    print(f"NaN/inf cells in train: {total_bad_cells}, negative {NEG_COL}: {int(neg.sum())}")


if __name__ == "__main__":
    main()
