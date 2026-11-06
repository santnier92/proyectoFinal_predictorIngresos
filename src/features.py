"""Stage 3 - Represent the input in a form the model can process.

Cleaning, stratified hold-out split and the preprocessing pipeline.
All learned transformations (imputation, scaling, one-hot encoding) live
inside a scikit-learn Pipeline, so they are fitted ONLY on training folds
and never see the test set (prevents data leakage).
"""
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src import config


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Drop exact duplicates BEFORE splitting so the same record cannot land
    in both train and test, and remove non-informative columns."""
    out = df.drop_duplicates().drop(columns=config.DROP_COLUMNS).reset_index(drop=True)
    out[config.TARGET] = (out[config.TARGET] == config.POSITIVE_LABEL).astype(int)
    return out


def split(df: pd.DataFrame):
    """Stratified 80/20 split keeps the ~24% positive rate in both sets."""
    X = df.drop(columns=[config.TARGET])
    y = df[config.TARGET]
    return train_test_split(
        X, y,
        test_size=config.TEST_SIZE,
        stratify=y,
        random_state=config.RANDOM_STATE,
    )


def build_preprocessor(numeric=None, categorical=None) -> ColumnTransformer:
    numeric = numeric if numeric is not None else config.NUMERIC_FEATURES
    categorical = categorical if categorical is not None else config.CATEGORICAL_FEATURES
    numeric_pipe = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ])
    categorical_pipe = Pipeline([
        ("impute", SimpleImputer(strategy="constant", fill_value="Unknown")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", min_frequency=20)),
    ])
    return ColumnTransformer([
        ("num", numeric_pipe, numeric),
        ("cat", categorical_pipe, categorical),
    ])
