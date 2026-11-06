"""Automated checks: data integrity, leakage guard and software acceptance.

Run with:  python -m pytest -q
(requires `python -m src.pipeline` to have produced reports/metrics.json)
"""
import json

import pandas as pd
import pytest

from src import config, data, features
from src.predict import load_model, predict

METRICS = config.REPORTS_DIR / "metrics.json"


@pytest.fixture(scope="module")
def results():
    if not METRICS.exists():
        pytest.skip("Run `python -m src.pipeline` first")
    return json.loads(METRICS.read_text(encoding="utf-8"))


def test_dataset_checksum_and_shape():
    df = data.load_raw()
    assert df.shape == (48842, 15)
    assert set(df[config.TARGET].unique()) == {"<=50K", ">50K"}


def test_no_leakage_between_train_and_test():
    """The same census record (including fnlwgt) must never be in both sets."""
    raw = data.load_raw().drop_duplicates().reset_index(drop=True)
    df = features.clean(data.load_raw())
    X_train, X_test, y_train, y_test = features.split(df)
    key = lambda idx: set(pd.util.hash_pandas_object(raw.loc[idx].fillna("NA"), index=False))
    assert key(X_train.index).isdisjoint(key(X_test.index)), "Same record found in train and test"
    assert abs(y_train.mean() - y_test.mean()) < 0.005, "Split is not stratified"


def test_overlapping_profiles_do_not_inflate_metrics(results):
    """Identical feature profiles (different people) must not explain the score."""
    lc = results["leakage_check"]
    assert lc["f1_unseen_profiles"] >= lc["f1_seen_profiles"] - 0.02


def test_model_beats_baseline(results):
    m = results["models"]
    assert m["logreg"]["test"]["f1"] > m["baseline"]["test"]["f1"]
    assert m["logreg"]["test"]["accuracy"] > m["baseline"]["test"]["accuracy"]


def test_acceptance_criteria(results):
    failed = [k for k, ok in results["acceptance"]["checks"].items() if not ok]
    assert not failed, f"Acceptance criteria not met: {failed}"


def test_prediction_contract():
    sample = pd.read_csv(config.ROOT_DIR / "data" / "sample_new_people.csv")
    out = predict(sample, model=load_model())
    assert out["proba_gt_50k"].between(0, 1).all()
    assert set(out["prediction"]).issubset({"<=50K", ">50K"})
    with pytest.raises(ValueError):
        predict(sample.drop(columns=["age"]), model=load_model())
