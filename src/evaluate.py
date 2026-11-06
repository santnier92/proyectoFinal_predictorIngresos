"""Stage 6 - Evaluate performance.

Hold-out metrics, confusion matrix, ROC curve and the software acceptance
check defined in config.ACCEPTANCE.
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import (
    ConfusionMatrixDisplay, RocCurveDisplay, accuracy_score, confusion_matrix,
    f1_score, precision_score, recall_score, roc_auc_score,
)

from src import config


def predict_with_threshold(model, X, threshold=config.DECISION_THRESHOLD):
    proba = model.predict_proba(X)[:, 1]
    return (proba >= threshold).astype(int), proba


def metrics(y_true, y_pred, proba) -> dict:
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, proba)) if len(np.unique(proba)) > 1 else 0.5,
        "tp": int(tp), "fp": int(fp), "tn": int(tn), "fn": int(fn),
    }


def acceptance(test_m: dict, train_m: dict, baseline_m: dict, cv: dict) -> dict:
    a = config.ACCEPTANCE
    checks = {
        "f1_test >= min_f1": test_m["f1"] >= a["min_f1"],
        "roc_auc_test >= min_roc_auc": test_m["roc_auc"] >= a["min_roc_auc"],
        "accuracy gain vs baseline >= 0.05":
            test_m["accuracy"] - baseline_m["accuracy"] >= a["min_accuracy_gain_vs_baseline"],
        "|f1_train - f1_test| <= 0.03":
            abs(train_m["f1"] - test_m["f1"]) <= a["max_train_test_f1_gap"],
        "cv f1 std <= 0.02": cv["f1"]["std"] <= a["max_cv_f1_std"],
    }
    return {"checks": checks, "accepted": all(checks.values())}


def plot_confusion(y_true, y_pred, path, title):
    fig, ax = plt.subplots(figsize=(5, 4.2))
    ConfusionMatrixDisplay(
        confusion_matrix(y_true, y_pred, labels=[0, 1]),
        display_labels=["<=50K (0)", ">50K (1)"],
    ).plot(ax=ax, cmap="Blues", values_format="d", colorbar=False)
    ax.set_title(title)
    ax.set_xlabel("Predicted label")
    ax.set_ylabel("True label")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_roc(models_proba: dict, y_true, path):
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    for name, proba in models_proba.items():
        RocCurveDisplay.from_predictions(y_true, proba, name=name, ax=ax)
    ax.plot([0, 1], [0, 1], "--", color="grey", linewidth=1)
    ax.set_title("ROC curve - test set")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_threshold_tradeoff(y_true, proba, path):
    thresholds = np.linspace(0.1, 0.9, 33)
    rows = []
    for t in thresholds:
        pred = (proba >= t).astype(int)
        rows.append((precision_score(y_true, pred, zero_division=0),
                     recall_score(y_true, pred), f1_score(y_true, pred)))
    rows = np.array(rows)
    fig, ax = plt.subplots(figsize=(5.5, 4))
    for i, label in enumerate(["precision", "recall", "f1"]):
        ax.plot(thresholds, rows[:, i], label=label)
    ax.axvline(config.DECISION_THRESHOLD, ls="--", c="grey", lw=1)
    ax.set_xlabel("Decision threshold")
    ax.set_ylabel("Score")
    ax.set_title("Precision / recall trade-off (logreg)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    best = thresholds[rows[:, 2].argmax()]
    return float(best), float(rows[:, 2].max())
