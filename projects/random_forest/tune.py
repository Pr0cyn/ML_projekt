"""Random forest project, step 1: GridSearchCV on the train set."""

import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR.parents[1] / "src"))

from sklearn.ensemble import RandomForestClassifier  # noqa: E402
from sklearn.pipeline import Pipeline  # noqa: E402

from preprocessing import RANDOM_STATE, load_selected_columns, preprocessing_steps  # noqa: E402
from tuning import best_score_rule, run_grid_search  # noqa: E402

PARAM_GRID = {
    "model__class_weight": ["balanced", "balanced_subsample"],
    "model__min_samples_leaf": [1, 2, 5],
    "model__max_features": ["sqrt", 0.3],
}


def describe(pipe: Pipeline) -> str:
    m = pipe.named_steps["model"]
    nodes = sum(t.tree_.node_count for t in m.estimators_)
    depth = max(t.get_depth() for t in m.estimators_)
    nodes_str = f"{nodes:,}".replace(",", " ")
    return f"{len(m.estimators_)} fa, összesen {nodes_str} csomópont, legmélyebb fa: {depth}"


def build_pipeline(n_jobs: int = -1) -> Pipeline:
    return Pipeline(preprocessing_steps(load_selected_columns()) + [
        ("model", RandomForestClassifier(n_estimators=100, random_state=RANDOM_STATE, n_jobs=n_jobs))])


def main() -> None:
    # n_jobs=1 inside the forest: GridSearchCV already runs the fits in parallel
    pipe = build_pipeline(n_jobs=1)
    rule_text = (
        "**Legjobb átlagos macro F1.** A RandomForestnél a rács elemei (`class_weight`, `min_samples_leaf`, "
        "`max_features`) az értelmezhetőséget nem változtatják érdemben, mert száz fa szavazata így is, úgy "
        "is fekete doboz. Ezért itt nincs „egyszerűbb” jelölt, amelyet a zajon belül előnyben kellene "
        "részesíteni. `class_weight='balanced_subsample'`: a súlyokat minden fa a saját bootstrap-mintáján "
        "számolja újra. `max_features`: kérdésenként hány oszlop közül választhat a fa (sqrt ≈ 7, 0.3 ≈ 16)."
    )
    run_grid_search(PROJECT_DIR, "RandomForest", "RandomForest", pipe, PARAM_GRID,
                    best_score_rule, rule_text, describe)


if __name__ == "__main__":
    main()
