"""Fairness audit (ethical analysis support).

Computes per-group metrics for a protected attribute and the two gap metrics
most used in the literature:
  * Demographic parity difference: max - min selection rate (P(y_hat=1)).
  * Equal opportunity difference:  max - min true positive rate (recall).
Also reports the false positive rate gap (equalized odds component).
"""
import pandas as pd


def group_metrics(y_true, y_pred, groups: pd.Series, min_size: int = 100) -> pd.DataFrame:
    df = pd.DataFrame({"y": y_true.values, "p": y_pred, "g": groups.fillna("Unknown").values})
    rows = []
    for g, d in df.groupby("g"):
        if len(d) < min_size:
            continue
        pos, neg = d[d.y == 1], d[d.y == 0]
        rows.append({
            "group": g,
            "n": len(d),
            "base_rate": d.y.mean(),
            "selection_rate": d.p.mean(),
            "tpr": pos.p.mean() if len(pos) else float("nan"),
            "fpr": neg.p.mean() if len(neg) else float("nan"),
            "accuracy": (d.y == d.p).mean(),
        })
    return pd.DataFrame(rows).sort_values("n", ascending=False).reset_index(drop=True)


def gaps(table: pd.DataFrame) -> dict:
    return {
        "demographic_parity_diff": float(table.selection_rate.max() - table.selection_rate.min()),
        "equal_opportunity_diff": float(table.tpr.max() - table.tpr.min()),
        "fpr_diff": float(table.fpr.max() - table.fpr.min()),
        "disparate_impact_ratio": float(table.selection_rate.min() / table.selection_rate.max()),
    }


def native_country_grouped(series: pd.Series) -> pd.Series:
    """US vs non-US: individual countries are too small to audit reliably."""
    return series.fillna("Unknown").where(series.fillna("Unknown") == "United-States", "Non-US/Unknown")
