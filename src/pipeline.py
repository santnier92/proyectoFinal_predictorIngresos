"""End-to-end ML workflow (stages 1-7). Run with:

    python -m src.pipeline

Outputs:
    models/logreg.joblib            selected model
    reports/metrics.json            every number quoted in README and report
    reports/model_comparison.csv    baseline vs candidates
    reports/fairness_*.csv          per-group audit
    reports/figures/*.png           confusion matrices, ROC, thresholds, EDA
"""
import json
import os
import warnings

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from sklearn.exceptions import UndefinedMetricWarning

from src import config, data, evaluate, fairness, features, models, train

# The majority-class baseline never predicts the positive class, so its
# precision is undefined (reported as 0). Silence that expected warning,
# also inside the joblib workers used by cross-validation.
warnings.filterwarnings("ignore", category=UndefinedMetricWarning)
os.environ.setdefault("PYTHONWARNINGS", "ignore::UserWarning")


def stage(n: int, title: str):
    print(f"\n=== Stage {n}: {title} ===")


def eda_figures(raw: pd.DataFrame):
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.6))
    raw[config.TARGET].value_counts().plot.bar(ax=axes[0], color=["#4C72B0", "#DD8452"])
    axes[0].set_title("Target distribution")
    axes[0].tick_params(axis="x", rotation=0)
    pd.crosstab(raw.sex, raw[config.TARGET], normalize="index")[config.POSITIVE_LABEL].plot.bar(
        ax=axes[1], color="#55A868")
    axes[1].set_title("P(>50K) by sex")
    axes[1].tick_params(axis="x", rotation=0)
    pd.crosstab(raw.race, raw[config.TARGET], normalize="index")[config.POSITIVE_LABEL].sort_values().plot.barh(
        ax=axes[2], color="#8172B3")
    axes[2].set_title("P(>50K) by race")
    fig.tight_layout()
    fig.savefig(config.FIGURES_DIR / "eda_target_and_groups.png", dpi=150)
    plt.close(fig)


def coefficient_figure(model, path):
    prep, lr = model.named_steps["prep"], model.named_steps["model"]
    names = prep.get_feature_names_out()
    coefs = pd.Series(lr.coef_[0], index=names).sort_values()
    top = pd.concat([coefs.head(10), coefs.tail(10)])
    fig, ax = plt.subplots(figsize=(7, 6))
    top.plot.barh(ax=ax, color=np.where(top > 0, "#55A868", "#C44E52"))
    ax.set_title("Logistic regression - top coefficients (log-odds)")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return coefs


def run():
    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    results = {}

    stage(1, "Define the task")
    task = ("Binary classification: predict whether a person's annual income is >50K USD "
            "(1994 US Census) from demographic and employment attributes.")
    print(task)
    results["task"] = task

    stage(2, "Collect relevant data")
    raw = data.load_raw()
    profile = data.describe(raw)
    print(json.dumps(profile, indent=2))
    results["data_profile"] = profile
    eda_figures(raw)

    stage(3, "Represent the input")
    df = features.clean(raw)
    X_train, X_test, y_train, y_test = features.split(df)
    results["split"] = {
        "rows_after_dedup": int(len(df)),
        "train_rows": int(len(X_train)), "test_rows": int(len(X_test)),
        "train_positive_rate": float(y_train.mean()), "test_positive_rate": float(y_test.mean()),
        "n_features_raw": int(X_train.shape[1]),
    }
    print(results["split"])

    stage(4, "Choose a model")
    cands = models.candidates()
    print("Candidates:", list(cands))

    stage(5, "Train the model")
    fitted, comparison = {}, []
    for name, (pipe, grid) in cands.items():
        est, params, cv = train.fit(pipe, grid, X_train, y_train)
        fitted[name] = est
        tr_pred, tr_proba = evaluate.predict_with_threshold(est, X_train)
        te_pred, te_proba = evaluate.predict_with_threshold(est, X_test)
        m_train = evaluate.metrics(y_train, tr_pred, tr_proba)
        m_test = evaluate.metrics(y_test, te_pred, te_proba)
        results.setdefault("models", {})[name] = {
            "best_params": params, "cv": cv, "train": m_train, "test": m_test,
        }
        comparison.append({
            "model": name, **{k: round(v, 4) for k, v in m_test.items()
                              if k in ("accuracy", "precision", "recall", "f1", "roc_auc")},
            "cv_f1_mean": round(cv["f1"]["mean"], 4), "cv_f1_std": round(cv["f1"]["std"], 4),
            "train_f1": round(m_train["f1"], 4),
        })
        print(f"{name:15s} params={params} test_f1={m_test['f1']:.4f} auc={m_test['roc_auc']:.4f}")
    pd.DataFrame(comparison).to_csv(config.REPORTS_DIR / "model_comparison.csv", index=False)
    model_path = train.save(fitted["logreg"], "logreg")
    print("Saved", model_path.relative_to(config.ROOT_DIR))

    stage(6, "Evaluate performance")
    lr = fitted["logreg"]
    y_pred, proba = evaluate.predict_with_threshold(lr, X_test)
    evaluate.plot_confusion(y_test, y_pred, config.FIGURES_DIR / "confusion_matrix_logreg.png",
                            "Logistic Regression - test set")
    b_pred, _ = evaluate.predict_with_threshold(fitted["baseline"], X_test)
    evaluate.plot_confusion(y_test, b_pred, config.FIGURES_DIR / "confusion_matrix_baseline.png",
                            "Baseline (majority class) - test set")
    evaluate.plot_roc({n: fitted[n].predict_proba(X_test)[:, 1]
                       for n in ("baseline", "logreg", "decision_tree")},
                      y_test, config.FIGURES_DIR / "roc_curve.png")
    best_t, best_f1 = evaluate.plot_threshold_tradeoff(y_test, proba, config.FIGURES_DIR / "threshold_tradeoff.png")
    results["threshold_analysis"] = {"best_threshold_for_f1": best_t, "best_f1": best_f1}
    coefs = coefficient_figure(lr, config.FIGURES_DIR / "logreg_coefficients.png")
    results["top_coefficients"] = {
        "positive": {k: round(float(v), 3) for k, v in coefs.tail(8)[::-1].items()},
        "negative": {k: round(float(v), 3) for k, v in coefs.head(8).items()},
    }
    # Leakage sanity check: different people can share an identical feature
    # profile once fnlwgt is dropped. Compare performance on test profiles that
    # also appear in train vs. profiles never seen during training.
    key = lambda X: pd.util.hash_pandas_object(X.fillna("NA"), index=False)
    seen = key(X_test).isin(set(key(X_train))).values
    results["leakage_check"] = {
        "test_rows_with_profile_seen_in_train": int(seen.sum()),
        "share": float(seen.mean()),
        "f1_seen_profiles": evaluate.metrics(y_test[seen], y_pred[seen], proba[seen])["f1"],
        "f1_unseen_profiles": evaluate.metrics(y_test[~seen], y_pred[~seen], proba[~seen])["f1"],
    }
    print("Leakage check:", results["leakage_check"])

    m = results["models"]
    results["acceptance"] = evaluate.acceptance(m["logreg"]["test"], m["logreg"]["train"],
                                                m["baseline"]["test"], m["logreg"]["cv"])
    print(json.dumps(results["acceptance"], indent=2))

    # Fairness audit on the test set
    groups = {
        "sex": X_test["sex"],
        "race": X_test["race"],
        "native_country": fairness.native_country_grouped(X_test["native_country"]),
    }
    results["fairness"] = {}
    for model_name in ("logreg", "logreg_unaware"):
        pred, _ = evaluate.predict_with_threshold(fitted[model_name], X_test)
        for attr, g in groups.items():
            table = fairness.group_metrics(y_test, pred, g)
            table.round(4).to_csv(config.REPORTS_DIR / f"fairness_{model_name}_{attr}.csv", index=False)
            results["fairness"].setdefault(model_name, {})[attr] = {
                "gaps": fairness.gaps(table),
                "groups": table.round(4).to_dict(orient="records"),
            }
    print(json.dumps({k: {a: v["gaps"] for a, v in d.items()} for k, d in results["fairness"].items()}, indent=2))

    stage(7, "Use the trained model on new data")
    sample = X_test.sample(5, random_state=config.RANDOM_STATE)
    sample.to_csv(config.ROOT_DIR / "data" / "sample_new_people.csv", index=False)
    from src.predict import predict
    preview = predict(sample, model=lr)
    print(preview[["age", "education_num", "occupation", "hours_per_week",
                   "proba_gt_50k", "prediction"]].to_string(index=False))

    with open(config.REPORTS_DIR / "metrics.json", "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2, ensure_ascii=False, default=str)
    print("\nReports written to", config.REPORTS_DIR.relative_to(config.ROOT_DIR))
    return results


if __name__ == "__main__":
    run()
