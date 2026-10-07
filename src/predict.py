"""Classify network flows with a saved Pipeline.

Usage:
    uv run python src/predict.py <decision_tree|random_forest> <flows.csv|flows.parquet> [output.csv]

The input needs the CICFlowMeter columns (at least the 54 selected features; extra
columns such as IPs or labels are ignored by the Pipeline). The output adds the
predicted Traffic Type and the Label derived from it.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))  # the Pipeline refers to functions in preprocessing.py

import joblib  # noqa: E402
import pandas as pd  # noqa: E402

BENIGN_TYPES = {"Audio", "Background", "Text", "Video"}


def load_pipeline(project: str):
    return joblib.load(ROOT / "projects" / project / "models" / "pipeline.joblib")


def predict(project: str, flows: pd.DataFrame) -> pd.DataFrame:
    pred = load_pipeline(project).predict(flows)
    return pd.DataFrame({
        "predicted_traffic_type": pred,
        "predicted_label": ["Benign" if p in BENIGN_TYPES else "Malicious" for p in pred],
    }, index=flows.index)


def main() -> None:
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    project, path = sys.argv[1], Path(sys.argv[2])
    flows = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)
    result = predict(project, flows)
    if len(sys.argv) > 3:
        result.to_csv(sys.argv[3], index=False)
        print(f"Wrote {len(result):,} predictions to {sys.argv[3]}")
    print(result["predicted_traffic_type"].value_counts().to_string())


if __name__ == "__main__":
    main()
