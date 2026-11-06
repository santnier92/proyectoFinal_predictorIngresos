"""Stage 7 - Use the trained model on new data.

Usage:
    python -m src.predict --input data/sample_new_people.csv
    python -m src.predict --input data/sample_new_people.csv --threshold 0.35

The output adds the probability of earning >50K and the predicted class.
This is a decision-SUPPORT tool: predictions must not be used as the sole
basis for decisions about real people (see README - scope).
"""
import argparse

import joblib
import pandas as pd

from src import config


def load_model(name: str = "logreg"):
    return joblib.load(config.MODELS_DIR / f"{name}.joblib")


def predict(df: pd.DataFrame, model=None, threshold: float = config.DECISION_THRESHOLD) -> pd.DataFrame:
    model = model or load_model()
    expected = config.NUMERIC_FEATURES + config.CATEGORICAL_FEATURES
    missing = [c for c in expected if c not in df.columns]
    if missing:
        raise ValueError(f"Missing input columns: {missing}")
    out = df.copy()
    out["proba_gt_50k"] = model.predict_proba(df[expected])[:, 1].round(4)
    out["prediction"] = (out["proba_gt_50k"] >= threshold).map({True: ">50K", False: "<=50K"})
    return out


def main():
    parser = argparse.ArgumentParser(description="Predict income bracket for new records")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default=None)
    parser.add_argument("--threshold", type=float, default=config.DECISION_THRESHOLD)
    args = parser.parse_args()

    result = predict(pd.read_csv(args.input), threshold=args.threshold)
    if args.output:
        result.to_csv(args.output, index=False)
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()
