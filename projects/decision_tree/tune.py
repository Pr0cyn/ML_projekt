"""Decision tree project, step 1: GridSearchCV on the train set."""

import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR.parents[1] / "src"))

from sklearn.pipeline import Pipeline  # noqa: E402
from sklearn.tree import DecisionTreeClassifier  # noqa: E402

from preprocessing import RANDOM_STATE, load_selected_columns, preprocessing_steps  # noqa: E402
from tuning import one_se_rule, run_grid_search  # noqa: E402

PARAM_GRID = {
    "model__max_depth": [None, 25, 20, 15, 12, 10, 8],
    "model__min_samples_leaf": [1, 2, 5, 10],
}


def simplicity(params: dict) -> tuple:
    """Shallower tree first, then larger leaves (fewer, more general rules)."""
    depth = params["model__max_depth"]
    return (depth if depth is not None else 10**6, -params["model__min_samples_leaf"])


def describe(pipe: Pipeline) -> str:
    m = pipe.named_steps["model"]
    return f"mélység {m.get_depth()}, {m.get_n_leaves()} levél"


def build_pipeline() -> Pipeline:
    return Pipeline(preprocessing_steps(load_selected_columns()) + [
        ("model", DecisionTreeClassifier(class_weight="balanced", random_state=RANDOM_STATE))])


def main() -> None:
    pipe = build_pipeline()
    rule_text = (
        "**Egy standard hiba szabály:** megkeresem a legjobb átlagos macro F1-et, és az összes olyan "
        "kombinációt, amelynek átlaga ettől legfeljebb egy standard hibával marad el (standard hiba = a "
        "legjobb kombináció foldonkénti szórása / √5). Ezek közül a "
        "**legegyszerűbb fát** választom: előbb a legkisebb `max_depth`, azonos mélységnél a legnagyobb "
        "`min_samples_leaf`. Indok: a zajon belüli különbség nem valódi különbség, a kisebb fa viszont "
        "kevésbé tanul túl, és jobban magyarázható."
    )
    run_grid_search(PROJECT_DIR, "DecisionTree", "DecisionTree", pipe, PARAM_GRID,
                    one_se_rule(simplicity), rule_text, describe)


if __name__ == "__main__":
    main()
