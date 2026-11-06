"""Stage 2 - Collect relevant data.

Loads the Adult Income dataset from the versioned CSV and verifies its
integrity (SHA-256) so every run trains on exactly the same data.
"""
import hashlib
import urllib.request

import pandas as pd

from src import config


def sha256_of(path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_raw(url: str = config.MIRROR_URL) -> None:
    """Download the merged CSV if it is not present locally."""
    config.DATA_RAW.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, config.DATA_RAW)


def load_raw(verify: bool = True) -> pd.DataFrame:
    """Read the raw CSV. Missing values are encoded as '?' in the source."""
    if not config.DATA_RAW.exists():
        download_raw()
    if verify:
        checksum = sha256_of(config.DATA_RAW)
        if checksum != config.RAW_SHA256:
            raise ValueError(f"Unexpected dataset checksum: {checksum}")
    return pd.read_csv(
        config.DATA_RAW,
        header=None,
        names=config.COLUMNS,
        na_values="?",
        skipinitialspace=True,
    )


def describe(df: pd.DataFrame) -> dict:
    """Small data profile used by the README, the report and the notebook."""
    return {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "duplicates": int(df.duplicated().sum()),
        "missing_by_column": {k: int(v) for k, v in df.isna().sum().items() if v > 0},
        "target_distribution": df[config.TARGET].value_counts().to_dict(),
        "positive_rate": float((df[config.TARGET] == config.POSITIVE_LABEL).mean()),
    }
