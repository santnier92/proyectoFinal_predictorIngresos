"""Central configuration for the income predictor project.

Every path, column name and threshold used by the pipeline lives here so the
experiment is reproducible and easy to audit.
"""
from pathlib import Path

# --- Paths -------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT_DIR / "data" / "raw" / "adult.csv"
DATA_PROCESSED_DIR = ROOT_DIR / "data" / "processed"
MODELS_DIR = ROOT_DIR / "models"
REPORTS_DIR = ROOT_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

# --- Data source -------------------------------------------------------------
# Official source: UCI Machine Learning Repository (Becker & Kohavi, 1996), CC BY 4.0.
# The CSV versioned in data/raw is adult.data + adult.test merged (48,842 rows).
UCI_URL = "https://archive.ics.uci.edu/static/public/2/adult.zip"
MIRROR_URL = "https://raw.githubusercontent.com/jbrownlee/Datasets/master/adult-all.csv"
RAW_SHA256 = "21e0ea2f925a00338929a8c86c27354c72ac1c79819bcca81c7d91c3d64218c2"

COLUMNS = [
    "age", "workclass", "fnlwgt", "education", "education_num",
    "marital_status", "occupation", "relationship", "race", "sex",
    "capital_gain", "capital_loss", "hours_per_week", "native_country", "income",
]
TARGET = "income"
POSITIVE_LABEL = ">50K"

# fnlwgt is a census sampling weight (not a personal attribute) and
# education duplicates education_num, so both are excluded from the features.
DROP_COLUMNS = ["fnlwgt", "education"]

NUMERIC_FEATURES = [
    "age", "education_num", "capital_gain", "capital_loss", "hours_per_week",
]
CATEGORICAL_FEATURES = [
    "workclass", "marital_status", "occupation", "relationship",
    "race", "sex", "native_country",
]
# Protected attributes audited in the fairness analysis.
SENSITIVE_FEATURES = ["sex", "race", "native_country"]

# --- Experiment --------------------------------------------------------------
RANDOM_STATE = 42
TEST_SIZE = 0.20
CV_FOLDS = 5
DECISION_THRESHOLD = 0.50

# --- Software acceptance criteria (evaluated on the hold-out test set) -------
ACCEPTANCE = {
    "min_f1": 0.60,                # F1 of the positive class (>50K)
    "min_roc_auc": 0.85,
    "min_accuracy_gain_vs_baseline": 0.05,
    "max_train_test_f1_gap": 0.03,  # overfitting guard
    "max_cv_f1_std": 0.02,          # stability across folds
}
