"""Stage 5 - Train the model.

Hyper-parameters are tuned with stratified 5-fold cross-validation using ONLY
the training set. The test set stays untouched until stage 6.
"""
import joblib
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_validate

from src import config


def cv_strategy() -> StratifiedKFold:
    return StratifiedKFold(n_splits=config.CV_FOLDS, shuffle=True,
                           random_state=config.RANDOM_STATE)


def fit(pipeline, grid, X_train, y_train):
    """Tune (if a grid is given) and refit on the full training set.
    Returns the fitted estimator and its cross-validation summary."""
    if grid:
        search = GridSearchCV(pipeline, grid, scoring="f1", cv=cv_strategy(), n_jobs=-1)
        search.fit(X_train, y_train)
        best, best_params = search.best_estimator_, search.best_params_
    else:
        best, best_params = pipeline.fit(X_train, y_train), {}

    scores = cross_validate(
        best, X_train, y_train, cv=cv_strategy(), n_jobs=-1,
        scoring=["accuracy", "precision", "recall", "f1", "roc_auc"],
    )
    cv_summary = {
        metric.replace("test_", ""): {
            "mean": float(values.mean()), "std": float(values.std()),
        }
        for metric, values in scores.items() if metric.startswith("test_")
    }
    return best, best_params, cv_summary


def save(model, name: str = "logreg"):
    config.MODELS_DIR.mkdir(parents=True, exist_ok=True)
    path = config.MODELS_DIR / f"{name}.joblib"
    joblib.dump(model, path)
    return path
