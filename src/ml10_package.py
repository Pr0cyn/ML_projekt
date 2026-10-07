"""ML10: package the saved Pipelines with metadata and verify they load and predict.

The Pipelines were saved with joblib in ML8 (projects/<project>/models/pipeline.joblib).
This step writes models/metadata.json next to each and runs a smoke test: the
Pipeline is loaded in a fresh process and must reproduce the in-process predictions
on a few train rows (the test set is not touched).
"""

import json
import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from preprocessing import RANDOM_STATE, TARGET, load_selected_columns  # noqa: E402

TRAIN_PARQUET = ROOT / "data" / "processed" / "train.parquet"
PROJECTS = ["decision_tree", "random_forest"]


def main() -> None:
    tr = pd.read_parquet(TRAIN_PARQUET)
    sample = tr.groupby(TARGET, group_keys=False).sample(n=3, random_state=RANDOM_STATE)
    sample_path = ROOT / "data" / "processed" / "ml10_smoke_sample.parquet"
    sample.to_parquet(sample_path, index=False)

    for project in PROJECTS:
        pdir = ROOT / "projects" / project
        model_path = pdir / "models" / "pipeline.joblib"
        pipe = joblib.load(model_path)
        results = json.loads((pdir / "test_evaluated.json").read_text(encoding="utf-8"))
        meta = {
            "project": project,
            "model_file": "pipeline.joblib",
            "created": datetime.fromtimestamp(model_path.stat().st_mtime).isoformat(timespec="seconds"),
            "pipeline_steps": [name for name, _ in pipe.steps],
            "model": type(pipe.named_steps["model"]).__name__,
            "best_params": json.loads((pdir / "best_params.json").read_text(encoding="utf-8")),
            "features": load_selected_columns(),
            "target": TARGET,
            "classes": list(pipe.classes_),
            "train_rows": int(len(tr)),
            "test_macro_f1": results["macro_f1"],
            "test_accuracy": results["accuracy"],
            "versions": {"python": platform.python_version(), "scikit-learn": sklearn.__version__,
                         "numpy": np.__version__, "pandas": pd.__version__, "joblib": joblib.__version__},
            "load_note": "Add <repo>/src to sys.path before joblib.load (the Pipeline uses functions "
                         "from src/preprocessing.py); see src/predict.py.",
        }
        (pdir / "models" / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

        # Smoke test in a fresh process, through the public predict script
        expected = pipe.predict(sample)
        out_csv = pdir / "models" / "smoke_predictions.csv"
        subprocess.run([sys.executable, str(ROOT / "src" / "predict.py"), project, str(sample_path), str(out_csv)],
                       check=True, capture_output=True)
        got = pd.read_csv(out_csv)["predicted_traffic_type"].to_numpy()
        assert (got == expected).all(), f"{project}: fresh-process predictions differ"
        hits = int((got == sample[TARGET].to_numpy()).sum())
        size_mb = model_path.stat().st_size / 1e6
        print(f"{project}: metadata written, model {size_mb:.2f} MB, fresh-load predictions identical, "
              f"{hits}/{len(sample)} smoke rows correct")


if __name__ == "__main__":
    main()
