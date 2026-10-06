"""ML8 for this project: final training on train, one-time evaluation on test."""

import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR.parents[1] / "src"))

from evaluation import train_and_evaluate  # noqa: E402
from tune import build_pipeline  # noqa: E402

TITLE = "DecisionTree"


def main() -> None:
    params = json.loads((PROJECT_DIR / "best_params.json").read_text(encoding="utf-8"))
    cv = pd.read_csv(PROJECT_DIR / "cv_results.csv").sort_values("rank")
    chosen = ", ".join(f"{k.removeprefix('model__')}={v}" for k, v in params.items())
    cv_score = float(cv.loc[cv["params"] == chosen, "mean_f1_macro"].iloc[0])
    pipeline = build_pipeline().set_params(**params)
    train_and_evaluate(PROJECT_DIR, TITLE, pipeline, cv_score)


if __name__ == "__main__":
    main()
