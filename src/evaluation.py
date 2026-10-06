"""ML8: final training on the full train set and the one-time evaluation on the test set.

The test set may be used only once per project: the first run writes
`test_evaluated.json`; if that file exists, the run aborts.
"""

import json
import time
from datetime import datetime
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from sklearn.metrics import (  # noqa: E402
    accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score, precision_recall_fscore_support,
)
from sklearn.pipeline import Pipeline  # noqa: E402

from preprocessing import TARGET  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TRAIN_PARQUET = ROOT / "data" / "processed" / "train.parquet"
TEST_PARQUET = ROOT / "data" / "processed" / "test.parquet"

# Sequential blue ramp (light -> dark), surface white for "near zero"
CMAP = LinearSegmentedColormap.from_list(
    "seq_blue", ["#ffffff", "#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"])
INK, INK_MUTED = "#1f1f1f", "#6b6b6b"


def n_fmt(v: int) -> str:
    return f"{v:,}".replace(",", " ")


def md_table(headers: list[str], rows: list[tuple]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(str(v) for v in r) + " |" for r in rows]
    return "\n".join(lines)


def plot_confusion(cm: np.ndarray, labels: list[str], title: str, path: Path) -> None:
    """Row-normalised confusion matrix (each row = recall of the true class), counts annotated."""
    row_sum = cm.sum(axis=1, keepdims=True)
    norm = np.divide(cm, row_sum, out=np.zeros_like(cm, dtype=float), where=row_sum > 0)
    n = len(labels)
    size = max(4.5, 1.6 + 0.95 * n)
    fig, ax = plt.subplots(figsize=(size + 2.2, size + 0.6))
    im = ax.imshow(norm, cmap=CMAP, vmin=0, vmax=1)
    # 2px surface gaps between cells
    ax.set_xticks(np.arange(-0.5, n, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, n, 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=2)
    ax.tick_params(which="minor", length=0)
    for i in range(n):
        for j in range(n):
            if cm[i, j] == 0:
                ax.text(j, i, "0", ha="center", va="center", fontsize=8, color=INK_MUTED)
                continue
            color = "white" if norm[i, j] > 0.55 else INK
            pct = 100 * norm[i, j]
            if 0.1 <= pct <= 99.9 or pct == 100:
                pct_str = f"{pct:.1f}%"
            else:
                pct_str = f"{pct:.2f}%" if pct >= 0.01 else "<0.01%"
            ax.text(j, i, f"{cm[i, j]:,}".replace(",", " ") + f"\n{pct_str}",
                    ha="center", va="center", fontsize=8, color=color)
    ax.set_xticks(range(n), labels, rotation=35, ha="right", fontsize=9, color=INK)
    ax.set_yticks(range(n), labels, fontsize=9, color=INK)
    ax.set_xlabel("Jósolt osztály", fontsize=10, color=INK)
    ax.set_ylabel("Valódi osztály", fontsize=10, color=INK)
    ax.set_title(title, fontsize=11, color=INK, loc="left")
    for s in ax.spines.values():
        s.set_visible(False)
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("A valódi osztály hány %-a (sor szerint)", fontsize=9, color=INK)
    cbar.outline.set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor="white")
    plt.close(fig)


def plot_all(reports: Path, title: str, cm: np.ndarray, classes: list[str],
             bcm: np.ndarray, bin_labels: list[str]) -> None:
    plot_confusion(cm, classes, f"{title}: confusion matrix a teszthalmazon (Traffic Type)",
                   reports / "confusion_matrix.png")
    plot_confusion(bcm, bin_labels, f"{title}:\nBenign vagy Malicious (teszthalmaz)",
                   reports / "confusion_matrix_binary.png")


def replot_from_summary(project_dir: Path) -> None:
    """Redraw the figures from the stored confusion matrices (no access to the test set)."""
    s = json.loads((project_dir / "test_evaluated.json").read_text(encoding="utf-8"))
    plot_all(project_dir / "reports", s["project"], np.array(s["confusion"]), s["labels"],
             np.array(s["binary_confusion"]), ["Benign", "Malicious"])


def train_and_evaluate(project_dir: Path, title: str, pipeline: Pipeline, cv_score: float) -> None:
    marker = project_dir / "test_evaluated.json"
    if marker.exists():
        raise SystemExit(f"{marker} exists: the test set was already used for this project. Aborting.")

    tr = pd.read_parquet(TRAIN_PARQUET)
    te = pd.read_parquet(TEST_PARQUET)
    classes = list(tr[TARGET].value_counts().index)
    type_to_label = tr.groupby(TARGET)["Label"].first().to_dict()

    t0 = time.perf_counter()
    pipeline.fit(tr, tr[TARGET])
    fit_s = time.perf_counter() - t0
    t0 = time.perf_counter()
    pred = pipeline.predict(te)
    pred_s = time.perf_counter() - t0
    y = te[TARGET].to_numpy()

    model_dir = project_dir / "models"
    model_dir.mkdir(exist_ok=True)
    joblib.dump(pipeline, model_dir / "pipeline.joblib")

    # 8-class metrics
    acc = accuracy_score(y, pred)
    f1m = f1_score(y, pred, average="macro")
    bacc = balanced_accuracy_score(y, pred)
    p, r, f, s = precision_recall_fscore_support(y, pred, labels=classes, zero_division=0)
    cm = confusion_matrix(y, pred, labels=classes)

    # Benign / Malicious derived from the predicted Traffic Type
    yb = np.array([type_to_label[v] for v in y])
    pb = np.array([type_to_label[v] for v in pred])
    bin_labels = ["Benign", "Malicious"]
    bp, br, bf, bs = precision_recall_fscore_support(yb, pb, labels=bin_labels, zero_division=0)
    bcm = confusion_matrix(yb, pb, labels=bin_labels)

    reports = project_dir / "reports"
    reports.mkdir(exist_ok=True)
    plot_all(reports, title, cm, classes, bcm, bin_labels)

    summary = {
        "project": title, "evaluated_at": datetime.now().isoformat(timespec="seconds"),
        "test_rows": int(len(te)), "accuracy": acc, "macro_f1": f1m, "balanced_accuracy": bacc,
        "cv_macro_f1": cv_score, "fit_seconds": fit_s, "predict_seconds": pred_s,
        "per_class": {c: {"precision": float(p[i]), "recall": float(r[i]), "f1": float(f[i]), "support": int(s[i])}
                      for i, c in enumerate(classes)},
        "binary": {c: {"precision": float(bp[i]), "recall": float(br[i]), "f1": float(bf[i]), "support": int(bs[i])}
                   for i, c in enumerate(bin_labels)},
        "binary_confusion": bcm.tolist(), "confusion": cm.tolist(), "labels": classes,
    }
    marker.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    errors = [(classes[i], classes[j], int(cm[i, j])) for i in range(len(classes))
              for j in range(len(classes)) if i != j and cm[i, j] > 0]
    errors.sort(key=lambda e: -e[2])
    out = [f"# 02 – Végső eredmények a teszthalmazon: {title} (ML8)", "",
           f"A végső Pipeline a teljes train-halmazon tanult ({n_fmt(len(tr))} sor, {fit_s:.1f} s), "
           + f"majd **egyszer** futott a teszthalmazon ({n_fmt(len(te))} sor, jóslás {pred_s:.2f} s). "
           + "A teszthalmazt ezt megelőzően egyik lépés sem használta.", "",
           "## 1. Összesített metrikák", "",
           md_table(["Metrika", "Teszt", "Train CV (hangolás)"], [
               ("**Macro F1**", f"**{f1m:.4f}**", f"{cv_score:.4f}"),
               ("Balanced accuracy", f"{bacc:.4f}", "–"),
               ("Accuracy", f"{acc:.4f}", "–"),
           ]), "",
           f"A tárgy 70%-os accuracy-követelményét a modell teljesíti ({100 * acc:.2f}%), de ez önmagában "
           "nem bizonyító erejű: a teszthalmaz 65%-a DoS, a négy támadásosztály együtt 99% feletti. A fő "
           "metrika a macro F1, amely mind a 8 osztályt egyforma súllyal veszi figyelembe.", "",
           "## 2. Osztályonkénti eredmények (Traffic Type)", "",
           md_table(["Traffic Type", "Tesztsorok", "Precision", "Recall", "F1"],
                    [(c, int(s[i]), f"{p[i]:.3f}", f"{r[i]:.3f}", f"{f[i]:.3f}") for i, c in enumerate(classes)]), "",
           "![Confusion matrix](confusion_matrix.png)", "",
           "A cellák a valódi osztály (sor) hány százalékát mutatják az adott jósolt osztályban; az átló a recall.", "",
           "### A leggyakoribb tévesztések", "",
           md_table(["Valódi", "Jósolt", "Sorok"], errors[:10]) if errors else "Nincs tévesztés.", "",
           "## 3. Benign vagy Malicious", "",
           "A jósolt Traffic Type-ból levezetve (Audio, Background, Text, Video → Benign; a többi → Malicious).", "",
           md_table(["Label", "Tesztsorok", "Precision", "Recall", "F1"],
                    [(c, int(bs[i]), f"{bp[i]:.4f}", f"{br[i]:.4f}", f"{bf[i]:.4f}") for i, c in enumerate(bin_labels)]), "",
           f"- Benign flow, amelyet támadásnak minősített (téves riasztás): **{int(bcm[0, 1])}**",
           f"- Támadás, amelyet benignnek minősített (kihagyott támadás): **{int(bcm[1, 0])}**", "",
           "![Confusion matrix (binary)](confusion_matrix_binary.png)", ""]
    (reports / "02_eredmenyek.md").write_text("\n".join(out), encoding="utf-8")

    print(f"{title}: test macro F1 {f1m:.4f} (CV {cv_score:.4f}), accuracy {acc:.4f}, balanced acc {bacc:.4f}")
    for i, c in enumerate(classes):
        print(f"  {c:22s} P {p[i]:.3f} R {r[i]:.3f} F1 {f[i]:.3f} n={s[i]}")
    print(f"  binary: benign->malicious {int(bcm[0, 1])}, malicious->benign {int(bcm[1, 0])}")
