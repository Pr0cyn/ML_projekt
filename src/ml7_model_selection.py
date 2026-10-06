"""ML7: model selection with 5-fold stratified CV on the train set only.

Every candidate is a full Pipeline (preprocessing from ML5-ML6 + model), so the
imputer and the scaler are refitted on the training part of each fold.
"""

import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

from preprocessing import RANDOM_STATE, TARGET, load_selected_columns, preprocessing_steps

ROOT = Path(__file__).resolve().parents[1]
TRAIN_PARQUET = ROOT / "data" / "processed" / "train.parquet"
REPORT = ROOT / "reports" / "04_modellvalasztas.md"
OOF_PARQUET = ROOT / "data" / "processed" / "ml7_oof_predictions.parquet"
N_SPLITS = 5


def candidates(cols: list[str]) -> dict[str, Pipeline]:
    pre = lambda: preprocessing_steps(cols)  # noqa: E731 - fresh steps per pipeline
    return {
        "DecisionTree": Pipeline(pre() + [("model", DecisionTreeClassifier(
            class_weight="balanced", random_state=RANDOM_STATE))]),
        "RandomForest": Pipeline(pre() + [("model", RandomForestClassifier(
            n_estimators=100, class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1))]),
        "LogisticRegression": Pipeline(pre() + [
            ("scale", StandardScaler()),
            ("model", LogisticRegression(class_weight="balanced", max_iter=2000, random_state=RANDOM_STATE))]),
        "HistGradientBoosting": Pipeline(pre() + [("model", HistGradientBoostingClassifier(
            class_weight="balanced", random_state=RANDOM_STATE))]),
    }


def complexity(name: str, pipe: Pipeline) -> str:
    m = pipe.named_steps["model"]
    if name == "DecisionTree":
        return f"1 fa, mélység {m.get_depth()}, {m.get_n_leaves()} levél"
    if name == "RandomForest":
        nodes = sum(t.tree_.node_count for t in m.estimators_)
        nodes_str = f"{nodes:,}".replace(",", " ")
        return f"{len(m.estimators_)} fa, összesen {nodes_str} csomópont"
    if name == "LogisticRegression":
        return f"{m.coef_.size} együttható ({m.coef_.shape[0]} osztály × {m.coef_.shape[1]} jellemző)"
    if name == "HistGradientBoosting":
        return f"{m.n_iter_} iteráció × {len(m.classes_)} osztály = {m.n_iter_ * len(m.classes_)} fa"
    return ""


def md_table(headers: list[str], rows: list[tuple]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(str(v) for v in r) + " |" for r in rows]
    return "\n".join(lines)


def main() -> None:
    tr = pd.read_parquet(TRAIN_PARQUET)
    cols = load_selected_columns()
    y = tr[TARGET].to_numpy()
    classes = list(tr[TARGET].value_counts().index)
    type_to_label = tr.groupby(TARGET)["Label"].first().to_dict()  # each type has exactly one Label (ML5)
    cv = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=RANDOM_STATE)
    folds = list(cv.split(tr, y))

    results, oof = {}, {}
    for name, pipe in candidates(cols).items():
        pred = np.empty(len(y), dtype=object)
        scores = {"f1_macro": [], "accuracy": [], "balanced_accuracy": [], "fit_s": [], "predict_s": []}
        for i, (tr_idx, va_idx) in enumerate(folds):
            model = clone(pipe)
            t0 = time.perf_counter()
            model.fit(tr.iloc[tr_idx], y[tr_idx])
            t1 = time.perf_counter()
            p = model.predict(tr.iloc[va_idx])
            t2 = time.perf_counter()
            pred[va_idx] = p
            scores["f1_macro"].append(f1_score(y[va_idx], p, average="macro"))
            scores["accuracy"].append(accuracy_score(y[va_idx], p))
            scores["balanced_accuracy"].append(balanced_accuracy_score(y[va_idx], p))
            scores["fit_s"].append(t1 - t0)
            scores["predict_s"].append(t2 - t1)
            if i == 0:
                scores["complexity"] = complexity(name, model)
            print(f"{name} fold {i + 1}: macro F1 {scores['f1_macro'][-1]:.4f}, fit {t1 - t0:.1f}s", flush=True)
        results[name], oof[name] = scores, pred

    pd.DataFrame({"y_true": y, **{n: p.astype(str) for n, p in oof.items()}}).to_parquet(OOF_PARQUET, index=False)

    # --- Aggregate tables
    ms = lambda v: f"{np.mean(v):.4f} ± {np.std(v):.4f}"  # noqa: E731
    main_rows = [(n, ms(s["f1_macro"]), ms(s["accuracy"]), ms(s["balanced_accuracy"]),
                  f"{np.mean(s['fit_s']):.1f} s", f"{np.mean(s['predict_s']):.2f} s")
                 for n, s in results.items()]
    fold_rows = [(n, *[f"{v:.4f}" for v in s["f1_macro"]]) for n, s in results.items()]
    per_class = {n: f1_score(y, p, labels=classes, average=None) for n, p in oof.items()}
    class_rows = [(c, int((y == c).sum()), *[f"{per_class[n][i]:.3f}" for n in results]) for i, c in enumerate(classes)]

    yb = np.array([type_to_label[v] for v in y])
    bin_rows = []
    for n, p in oof.items():
        pb = np.array([type_to_label[v] for v in p])
        bin_rows.append((n, f"{recall_score(yb, pb, pos_label='Benign'):.4f}",
                         f"{precision_score(yb, pb, pos_label='Benign'):.4f}",
                         f"{f1_score(yb, pb, pos_label='Benign'):.4f}",
                         int(((yb == "Benign") & (pb == "Malicious")).sum()),
                         int(((yb == "Malicious") & (pb == "Benign")).sum())))

    interp = {
        "DecisionTree": "Magas: egyetlen fa, a döntési szabályok kiolvashatók és lerajzolhatók (ha a fa nem túl mély).",
        "RandomForest": "Közepes: sok fa szavaz, egy döntés nem követhető végig, de a jellemzők fontossága "
                        "(impurity és permutation importance) jól mérhető.",
        "LogisticRegression": "Magas: osztályonként egy-egy súly minden jellemzőhöz, előjellel és nagysággal "
                              "(skálázott adaton összevethetők).",
        "HistGradientBoosting": "Alacsony–közepes: sok, egymásra épülő kis fa; csak permutation importance-szel "
                                "értelmezhető.",
    }

    out = ["# 04 – Modellválasztás (ML7, döntési pont)", "",
           f"Minden mérés a **train-halmazon** ({len(tr):,} sor) készült, ".replace(",", " ")
           + f"{N_SPLITS}-fold rétegzett keresztvalidációval (`StratifiedKFold`, shuffle, random_state={RANDOM_STATE}). "
           "Mind a négy modell ugyanazokon a foldokon fut. Minden jelölt egy teljes Pipeline: az ML5–ML6 "
           "előfeldolgozás (54 oszlop, inf → NaN, medián-imputálás) + a modell, így az imputálás és a "
           "skálázás foldonként csak a tanító részen illeszkedik. A teszthalmazt nem érintettem.", "",
           "A modellek alapbeállításokkal futnak (hiperparaméter-hangolás nélkül), mindegyik "
           "`class_weight='balanced'`-del, hogy a ritka osztályok hibája nagyobb súllyal számítson. A "
           "feladat a DecisionTree, RandomForest és LogisticRegression összevetését kéri; a "
           "HistGradientBoosting a scikit-learn gradient boosting modellje, összehasonlításként szerepel.", ""]
    out += ["## 1. Fő eredmények (foldok átlaga ± szórása)", "",
            md_table(["Modell", "Macro F1", "Accuracy", "Balanced accuracy", "Tanítási idő / fold", "Jóslási idő / fold"],
                     main_rows), "",
            "A balanced accuracy az osztályonkénti recall átlaga, ezért a ritka osztályokat ugyanúgy súlyozza, "
            "mint a nagyokat. Az accuracy itt félrevezető, mert a DoS a sorok 65%-a.", ""]
    out += ["## 2. Macro F1 foldonként", "",
            md_table(["Modell"] + [f"Fold {i + 1}" for i in range(N_SPLITS)], fold_rows), ""]
    out += ["## 3. F1 osztályonként (a keresztvalidált jóslatokon)", "",
            md_table(["Traffic Type", "Sorok (train)"] + list(results), class_rows), ""]
    out += ["## 4. Benign vagy Malicious (a jósolt Traffic Type-ból levezetve)", "",
            "A modell nem jósol külön Label-t: a jósolt Traffic Type-ot alakítjuk át (Audio, Background, "
            "Text, Video → Benign; a többi → Malicious). A „kihagyott benign” azt jelenti, hogy egy benign "
            "flow-t támadásnak minősített (téves riasztás); a „benignnek vélt támadás” a veszélyesebb hiba.", "",
            md_table(["Modell", "Benign recall", "Benign precision", "Benign F1", "Kihagyott benign", "Benignnek vélt támadás"],
                     bin_rows), ""]
    out += ["## 5. Értelmezhetőség és méret", "",
            md_table(["Modell", "Méret (1. fold)", "Értelmezhetőség"],
                     [(n, results[n]["complexity"], interp[n]) for n in results]), ""]
    REPORT.write_text("\n".join(out), encoding="utf-8")
    for r in main_rows:
        print(r)


if __name__ == "__main__":
    main()
