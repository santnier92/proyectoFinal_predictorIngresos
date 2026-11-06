"""Performance and scalability benchmark (architectural driver: performance / data volume).

Usage:
    python -m src.benchmark            # real dataset + 1,000,000-row scale test
    python -m src.benchmark --rows 200000

Measures training time, batch inference throughput, single-record latency and
memory footprint. The scale test resamples the training set (with replacement)
up to N rows to simulate "millions of records" with the same data types.
"""
import argparse
import json
import time
import tracemalloc

import numpy as np
from sklearn.base import clone

from src import config, data, features, models

N_REPEATS_LATENCY = 200


def _timed(fn, *args):
    start = time.perf_counter()
    out = fn(*args)
    return out, time.perf_counter() - start


def measure(model, X_train, y_train, X_test, label):
    tracemalloc.start()
    fitted, fit_s = _timed(model.fit, X_train, y_train)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    _, batch_s = _timed(fitted.predict_proba, X_test)
    one = X_test.iloc[[0]]
    lat = []
    for _ in range(N_REPEATS_LATENCY):
        _, s = _timed(fitted.predict_proba, one)
        lat.append(s)
    return {
        "scenario": label,
        "train_rows": int(len(X_train)),
        "train_seconds": round(fit_s, 2),
        "train_peak_memory_mb": round(peak / 1e6, 1),
        "batch_rows": int(len(X_test)),
        "batch_seconds": round(batch_s, 3),
        "throughput_rows_per_second": int(len(X_test) / batch_s),
        "single_record_latency_ms_p50": round(1000 * float(np.percentile(lat, 50)), 2),
        "single_record_latency_ms_p95": round(1000 * float(np.percentile(lat, 95)), 2),
    }


def run(scale_rows: int):
    df = features.clean(data.load_raw())
    X_train, X_test, y_train, y_test = features.split(df)
    pipe, _ = models.candidates()["logreg"]
    pipe.set_params(model__C=1.0)

    results = {
        "dataset": {
            "rows": int(len(df)), "raw_columns": len(config.COLUMNS),
            "numeric_features": len(config.NUMERIC_FEATURES),
            "categorical_features": len(config.CATEGORICAL_FEATURES),
            "csv_size_mb": round(config.DATA_RAW.stat().st_size / 1e6, 2),
            "in_memory_mb": round(float(df.memory_usage(deep=True).sum()) / 1e6, 1),
        },
        "runs": [],
    }
    results["runs"].append(measure(clone(pipe), X_train, y_train, X_test, "Dataset real"))

    rng = np.random.default_rng(config.RANDOM_STATE)
    idx = rng.integers(0, len(X_train), size=scale_rows)
    X_big, y_big = X_train.iloc[idx].reset_index(drop=True), y_train.iloc[idx].reset_index(drop=True)
    tidx = rng.integers(0, len(X_test), size=min(scale_rows, 1_000_000))
    X_big_test = X_test.iloc[tidx].reset_index(drop=True)
    results["runs"].append(measure(clone(pipe), X_big, y_big, X_big_test, f"Escala {scale_rows:,} filas"))

    out = config.REPORTS_DIR / "performance.json"
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(results, indent=2, ensure_ascii=False))
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=1_000_000)
    run(parser.parse_args().rows)
