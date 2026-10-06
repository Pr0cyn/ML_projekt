"""ML8 summary: side-by-side test results of the two projects (reports/05_eredmenyek.md).

Reads the one-time results stored by each project. For the uncertainty estimate it
re-predicts the test set with the two frozen, saved Pipelines (no refitting, no
tuning); the predictions are checked against the stored confusion matrices.
"""

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, f1_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from preprocessing import RANDOM_STATE, TARGET  # noqa: E402

TEST_PARQUET = ROOT / "data" / "processed" / "test.parquet"
REPORT = ROOT / "reports" / "05_eredmenyek.md"
PROJECTS = {"DecisionTree": ROOT / "projects" / "decision_tree",
            "RandomForest": ROOT / "projects" / "random_forest"}
N_BOOT = 2000


def md_table(headers: list[str], rows: list[tuple]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(str(v) for v in r) + " |" for r in rows]
    return "\n".join(lines)


def main() -> None:
    res = {n: json.loads((d / "test_evaluated.json").read_text(encoding="utf-8")) for n, d in PROJECTS.items()}
    te = pd.read_parquet(TEST_PARQUET)
    y = te[TARGET].to_numpy()
    labels = res["DecisionTree"]["labels"]

    preds = {}
    for n, d in PROJECTS.items():
        preds[n] = joblib.load(d / "models" / "pipeline.joblib").predict(te)
        assert (confusion_matrix(y, preds[n], labels=labels) == np.array(res[n]["confusion"])).all()

    # Paired bootstrap of the macro F1 difference (RF - DT) on the test rows
    rng = np.random.default_rng(RANDOM_STATE)
    diffs, f1s = [], {n: [] for n in PROJECTS}
    for _ in range(N_BOOT):
        idx = rng.integers(0, len(y), len(y))
        for n in PROJECTS:
            f1s[n].append(f1_score(y[idx], preds[n][idx], labels=labels, average="macro", zero_division=0))
        diffs.append(f1s["RandomForest"][-1] - f1s["DecisionTree"][-1])
    ci = {n: np.percentile(v, [2.5, 97.5]) for n, v in f1s.items()}
    dci = np.percentile(diffs, [2.5, 97.5])
    no_bg = [c for c in labels if c != "Background"]
    f1_no_bg = {n: f1_score(y, preds[n], labels=no_bg, average="macro") for n in PROJECTS}
    both_wrong = int(((preds["DecisionTree"] != y) & (preds["RandomForest"] != y)).sum())
    only = {n: int(((preds[n] != y) & (preds[o] == y)).sum())
            for n, o in [("DecisionTree", "RandomForest"), ("RandomForest", "DecisionTree")]}

    dt, rf = res["DecisionTree"], res["RandomForest"]
    out = ["# 05 – Végső eredmények a teszthalmazon (ML8)", "",
           "Mindkét projekt végső Pipeline-ja a teljes train-halmazon tanult, majd **egyszer** futott a "
           + "teszthalmazon (" + f"{dt['test_rows']:,}".replace(",", " ") + " sor). "
           + "A projektenkénti részletes riportok: `projects/decision_tree/reports/02_eredmenyek.md` és "
           "`projects/random_forest/reports/02_eredmenyek.md` (benne a confusion matrix képekkel).", "",
           "## 1. Összesített metrikák", "",
           md_table(["Metrika", "DecisionTree", "RandomForest"], [
               ("**Macro F1 (teszt)**", f"**{dt['macro_f1']:.4f}**", f"**{rf['macro_f1']:.4f}**"),
               ("Macro F1, 95% bootstrap-intervallum",
                f"{ci['DecisionTree'][0]:.3f} – {ci['DecisionTree'][1]:.3f}",
                f"{ci['RandomForest'][0]:.3f} – {ci['RandomForest'][1]:.3f}"),
               ("Macro F1 (train CV, hangolás)", f"{dt['cv_macro_f1']:.4f}", f"{rf['cv_macro_f1']:.4f}"),
               ("Macro F1 a Background nélkül (7 osztály)", f"{f1_no_bg['DecisionTree']:.4f}",
                f"{f1_no_bg['RandomForest']:.4f}"),
               ("Balanced accuracy", f"{dt['balanced_accuracy']:.4f}", f"{rf['balanced_accuracy']:.4f}"),
               ("Accuracy", f"{dt['accuracy']:.4f}", f"{rf['accuracy']:.4f}"),
               ("Tanítási idő (teljes train)", f"{dt['fit_seconds']:.1f} s", f"{rf['fit_seconds']:.1f} s"),
           ]), "",
           f"A 70%-os accuracy-követelményt mindkét modell teljesíti, de a 65%-os DoS-arány miatt ez "
           "önmagában nem bizonyít semmit; a fő metrika a macro F1.", "",
           "## 2. Osztályonkénti F1", "",
           md_table(["Traffic Type", "Tesztsorok", "DT precision", "DT recall", "DT F1",
                     "RF precision", "RF recall", "RF F1"],
                    [(c, dt["per_class"][c]["support"],
                      *[f"{dt['per_class'][c][m]:.3f}" for m in ("precision", "recall", "f1")],
                      *[f"{rf['per_class'][c][m]:.3f}" for m in ("precision", "recall", "f1")]) for c in labels]), "",
           "## 3. Benign vagy Malicious", "",
           md_table(["", "DecisionTree", "RandomForest"], [
               ("Benign recall", f"{dt['binary']['Benign']['recall']:.4f}", f"{rf['binary']['Benign']['recall']:.4f}"),
               ("Benign precision", f"{dt['binary']['Benign']['precision']:.4f}", f"{rf['binary']['Benign']['precision']:.4f}"),
               ("Malicious recall", f"{dt['binary']['Malicious']['recall']:.4f}", f"{rf['binary']['Malicious']['recall']:.4f}"),
               ("Téves riasztás (benign → malicious)", dt["binary_confusion"][0][1], rf["binary_confusion"][0][1]),
               ("Kihagyott támadás (malicious → benign)", dt["binary_confusion"][1][0], rf["binary_confusion"][1][0]),
           ]), "",
           "## 4. Mennyire biztos a különbség?", "",
           f"- **A macro F1 különbsége (RF − DT): {rf['macro_f1'] - dt['macro_f1']:+.4f}**, a páros bootstrap 95%-os "
           f"intervalluma {dci[0]:+.4f} – {dci[1]:+.4f} ({N_BOOT} újramintavételezés, random_state={RANDOM_STATE}).",
           f"- A Background osztály nélkül a különbség {f1_no_bg['RandomForest'] - f1_no_bg['DecisionTree']:+.4f}. "
           f"A Background osztályból mindössze {rf['per_class']['Background']['support']} tesztsor van, így egyetlen "
           "sor 0,1-et mozdít az osztály recallján, és ez a macro F1-ben 1/8-os súllyal jelenik meg.",
           f"- Hibás jóslatok: mindkét modell téved {both_wrong} sorban; csak a DT téved {only['DecisionTree']}, "
           f"csak az RF {only['RandomForest']} sorban.",
           "- A tesztértékek nem lettek modellválasztásra használva: mindkét modell a train-halmazon hangolt "
           "beállításokkal, előre rögzítve futott, és ez az összevetés csak beszámol az eredményről.", ""]
    REPORT.write_text("\n".join(out), encoding="utf-8")
    print(f"DT {dt['macro_f1']:.4f} CI {ci['DecisionTree']}, RF {rf['macro_f1']:.4f} CI {ci['RandomForest']}")
    print(f"diff {rf['macro_f1'] - dt['macro_f1']:+.4f} CI {dci}, no-bg {f1_no_bg}, both wrong {both_wrong}, only {only}")


if __name__ == "__main__":
    main()
