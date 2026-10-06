"""Shared preprocessing steps used inside the sklearn Pipelines (ML6-ML8).

Module-level functions (not lambdas) so the fitted Pipeline can be saved with joblib.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import FunctionTransformer

SELECTED_COLUMNS_JSON = Path(__file__).resolve().parent / "selected_columns.json"
TARGET = "Traffic Type"
RANDOM_STATE = 42


def load_selected_columns() -> list[str]:
    return json.loads(SELECTED_COLUMNS_JSON.read_text(encoding="utf-8"))["columns"]


def inf_to_nan(X: pd.DataFrame) -> pd.DataFrame:
    """Replace +inf / -inf with NaN so the imputer can handle them."""
    return X.replace([np.inf, -np.inf], np.nan)


def negative_to_nan(X: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Treat negative values in the given columns as missing (NaN)."""
    X = X.copy()
    for c in columns:
        X.loc[X[c] < 0, c] = np.nan
    return X


def column_selector(columns: list[str]) -> ColumnTransformer:
    """Keep only the selected feature columns (ML5 decision), in a fixed order."""
    return ColumnTransformer(
        [("keep", "passthrough", columns)], remainder="drop", verbose_feature_names_out=False
    ).set_output(transform="pandas")


def inf_to_nan_step() -> FunctionTransformer:
    return FunctionTransformer(inf_to_nan, feature_names_out="one-to-one").set_output(transform="pandas")


def negative_to_nan_step(columns: list[str]) -> FunctionTransformer:
    return FunctionTransformer(
        negative_to_nan, kw_args={"columns": columns}, feature_names_out="one-to-one"
    ).set_output(transform="pandas")
