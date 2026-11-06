"""Stage 4 - Choose a model.

Three candidates are compared under the same preprocessing:
  * baseline      - DummyClassifier (always predicts the majority class).
                    Any useful model must beat it.
  * logreg        - Logistic Regression (selected model, see ADR-002).
  * decision_tree - Shallow decision tree, interpretable alternative.
  * logreg_unaware- Logistic Regression WITHOUT sex/race/native_country,
                    used only in the fairness experiment.
"""
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeClassifier

from src import config
from src.features import build_preprocessor


def _pipe(estimator, numeric=None, categorical=None) -> Pipeline:
    return Pipeline([
        ("prep", build_preprocessor(numeric, categorical)),
        ("model", estimator),
    ])


def candidates() -> dict:
    """Return (pipeline, hyper-parameter grid) per candidate."""
    unaware_cat = [c for c in config.CATEGORICAL_FEATURES if c not in config.SENSITIVE_FEATURES]
    return {
        "baseline": (
            _pipe(DummyClassifier(strategy="most_frequent")),
            {},
        ),
        "logreg": (
            _pipe(LogisticRegression(max_iter=2000, solver="lbfgs")),
            {"model__C": [0.01, 0.1, 1.0, 10.0]},
        ),
        "decision_tree": (
            _pipe(DecisionTreeClassifier(random_state=config.RANDOM_STATE)),
            {"model__max_depth": [4, 6, 8, 10], "model__min_samples_leaf": [20, 50]},
        ),
        "logreg_unaware": (
            _pipe(LogisticRegression(max_iter=2000, solver="lbfgs"),
                  categorical=unaware_cat),
            {"model__C": [0.01, 0.1, 1.0, 10.0]},
        ),
    }
