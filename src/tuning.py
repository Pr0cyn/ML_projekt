"""Shared GridSearchCV routine for the two model projects (projects/decision_tree, projects/random_forest).

Tuning uses the train set only, with the same 5 stratified folds as ML7, so the
tuned results are directly comparable with the ML7 defaults.
"""

import json
import time
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import f1_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline

from preprocessing import RANDOM_STATE, TARGET

ROOT = Path(__file__).resolve().parents[1]
TRAIN_PARQUET = ROOT / "data" / "processed" / "train.parquet"
ML7_OOF_PARQUET = ROOT / "data" / "processed" / "ml7_oof_predictions.parquet"
N_SPLITS = 5


def one_se_rule(simplicity: Callable[[dict], tuple]) -> Callable[[dict], int]:
    """Refit rule ("one standard error"): among candidates whose mean score is within
    one standard error (std / sqrt(n_splits)) of the best, pick the simplest
    (smallest `simplicity` tuple)."""

    def pick(cv_results: dict) -> int:
        mean = np.asarray(cv_results["mean_test_score"])
        se = np.asarray(cv_results["std_test_score"]) / np.sqrt(N_SPLITS)
        best = int(np.argmax(mean))
        ok = np.flatnonzero(mean >= mean[best] - se[best])
        return int(min(ok, key=lambda i: (simplicity(cv_results["params"][i]), -mean[i])))

    return pick


def best_score_rule(cv_results: dict) -> int:
    return int(np.argmax(cv_results["mean_test_score"]))


def fmt_params(p: dict) -> str:
    return ", ".join(f"{k.removeprefix('model__')}={v}" for k, v in p.items())


def md_table(headers: list[str], rows: list[tuple]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(str(v) for v in r) + " |" for r in rows]
    return "\n".join(lines)


def run_grid_search(
    project_dir: Path, title: str, ml7_name: str, pipeline: Pipeline, param_grid: dict,
    refit_rule: Callable[[dict], int], rule_text: str, describe_model: Callable[[Pipeline], str],
) -> None:
    tr = pd.read_parquet(TRAIN_PARQUET)
    y = tr[TARGET].to_numpy()
    classes = list(tr[TARGET].value_counts().index)
    cv = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=RANDOM_STATE)

    search = GridSearchCV(pipeline, param_grid, scoring="f1_macro", cv=cv, refit=refit_rule, n_jobs=-1)
    t0 = time.perf_counter()
    search.fit(tr, y)
    secs = time.perf_counter() - t0
    res = search.cv_results_
    chosen = search.best_index_
    best = int(np.argmax(res["mean_test_score"]))
    n_combos = len(res["params"])
    print(f"{title}: {n_combos} combinations in {secs:.0f}s, chosen {fmt_params(res['params'][chosen])}")

    # Per-class F1: ML7 default (same folds) vs tuned (out-of-fold predictions)
    tuned = clone(pipeline).set_params(**res["params"][chosen])
    tuned_pred = cross_val_predict(tuned, tr, y, cv=cv, n_jobs=-1)
    default_pred = pd.read_parquet(ML7_OOF_PARQUET)[ml7_name].to_numpy()
    f1_def = f1_score(y, default_pred, labels=classes, average=None)
    f1_tun = f1_score(y, tuned_pred, labels=classes, average=None)

    # Save artifacts
    out_dir = project_dir / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "best_params.json").write_text(
        json.dumps({k: v for k, v in res["params"][chosen].items()}, indent=2, default=str), encoding="utf-8")
    table = pd.DataFrame({
        "params": [fmt_params(p) for p in res["params"]],
        "mean_f1_macro": res["mean_test_score"], "std_f1_macro": res["std_test_score"],
        "mean_fit_s": res["mean_fit_time"], "rank": res["rank_test_score"],
    }).sort_values("rank")
    table.to_csv(project_dir / "cv_results.csv", index=False)

    # Report
    rows = [(r.rank, r.params, f"{r.mean_f1_macro:.4f}", f"{r.std_f1_macro:.4f}", f"{r.mean_fit_s:.1f} s")
            for r in table.itertuples()]
    grid_desc = [f"- `{k.removeprefix('model__')}`: {', '.join(str(v) for v in vals)}" for k, vals in param_grid.items()]
    out = [f"# 01 – Hiperparaméter-hangolás: {title}", "",
           f"GridSearchCV a **train-halmazon** ({len(tr):,} sor), ".replace(",", " ")
           + f"{N_SPLITS}-fold rétegzett keresztvalidációval, ugyanazokon a foldokon, mint az ML7, macro F1 "
           f"alapján. {n_combos} kombináció × {N_SPLITS} fold = {n_combos * N_SPLITS} tanítás, "
           f"összesen {secs:.0f} másodperc. A teszthalmazt nem érintettem.", "",
           "## A rács", "", *grid_desc, "",
           "## Kiválasztási szabály", "", rule_text, "",
           "## Eredmény", "",
           md_table(["", "Beállítás", "Macro F1 (CV)", "Szórás"], [
               ("Alapbeállítás (ML7)", "sklearn alapértékek, class_weight=balanced",
                f"{f1_score(y, default_pred, average='macro'):.4f}*", "–"),
               ("Legjobb CV-átlag", fmt_params(res["params"][best]),
                f"{res['mean_test_score'][best]:.4f}", f"{res['std_test_score'][best]:.4f}"),
               ("**Választott**", f"**{fmt_params(res['params'][chosen])}**",
                f"**{res['mean_test_score'][chosen]:.4f}**", f"{res['std_test_score'][chosen]:.4f}"),
           ]), "",
           "\\* Az alapbeállítás értéke itt az összesített keresztvalidált jóslatokon számolt macro F1, ezért "
           "kicsit eltérhet az ML7 foldonkénti átlagától.", "",
           f"A választott modell a teljes train-halmazon újratanítva: {describe_model(search.best_estimator_)}.", "",
           "## F1 osztályonként: alapbeállítás vs. hangolt (keresztvalidált jóslatok)", "",
           md_table(["Traffic Type", "Sorok (train)", "Alapbeállítás", "Hangolt", "Változás"],
                    [(c, int((y == c).sum()), f"{a:.3f}", f"{b:.3f}", f"{b - a:+.3f}")
                     for c, a, b in zip(classes, f1_def, f1_tun)]), "",
           "## Minden kombináció (rangsor szerint)", "",
           md_table(["Rang", "Beállítás", "Macro F1", "Szórás", "Tanítás / fold"], rows), ""]
    (out_dir / "01_hangolas.md").write_text("\n".join(out), encoding="utf-8")
    print(f"best mean {res['mean_test_score'][best]:.4f}, chosen {res['mean_test_score'][chosen]:.4f}; "
          f"{describe_model(search.best_estimator_)}")
    for c, a, b in zip(classes, f1_def, f1_tun):
        print(f"  {c:22s} {a:.3f} -> {b:.3f}")
