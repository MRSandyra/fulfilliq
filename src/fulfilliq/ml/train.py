from __future__ import annotations

import hashlib
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .evaluate import evaluate
from .features import FEATURES, feature_frame


def temporal_splits(times: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    dates = sorted(times.dt.date.unique())
    if len(dates) < 3:
        raise ValueError("need at least three purchase dates for chronological splits")
    train_end = dates[max(0, int(len(dates) * 0.70) - 1)]
    validation_end = dates[max(int(len(dates) * 0.85) - 1, 1)]
    train = times.dt.date <= train_end
    validation = (times.dt.date > train_end) & (times.dt.date <= validation_end)
    test = times.dt.date > validation_end
    if not (train.any() and validation.any() and test.any()):
        raise ValueError("temporal split left an empty partition")
    return train, validation, test


def train_from_facts(facts_path: Path, output: Path) -> dict:
    facts = pd.read_json(facts_path, lines=True)
    X, y, times = feature_frame(facts)
    train, validation, test = temporal_splits(times)
    numeric = [
        x
        for x in FEATURES
        if x not in {"customer_state", "seller_state", "product_category_primary"}
    ]
    categorical = [x for x in FEATURES if x not in numeric]
    prep = ColumnTransformer(
        [
            (
                "numeric",
                Pipeline(
                    [("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]
                ),
                numeric,
            ),
            (
                "categorical",
                Pipeline(
                    [
                        ("impute", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical,
            ),
        ]
    )
    model = Pipeline(
        [
            ("preprocess", prep),
            (
                "classifier",
                LogisticRegression(max_iter=1000, random_state=42, class_weight="balanced"),
            ),
        ]
    )
    model.fit(X.loc[train], y.loc[train])
    validation_p = model.predict_proba(X.loc[validation])[:, 1]
    # Threshold uses validation only: choose the best F1 among bounded candidates.
    candidates = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
    threshold = max(candidates, key=lambda t: evaluate(y.loc[validation], validation_p, t)["f1"])
    test_p = model.predict_proba(X.loc[test])[:, 1]
    report = {
        "model_version": "logistic-regression-v1",
        "feature_names": FEATURES,
        "metrics": evaluate(y.loc[test], test_p, threshold),
        "baseline_prevalence": float(y.loc[train].mean()),
        "split_boundaries": {
            "train_end": str(times.loc[train].dt.date.max()),
            "validation_start": str(times.loc[validation].dt.date.min()),
            "validation_end": str(times.loc[validation].dt.date.max()),
            "test_start": str(times.loc[test].dt.date.min()),
        },
        "counts": {
            "train": int(train.sum()),
            "validation": int(validation.sum()),
            "test": int(test.sum()),
        },
        "training_hash": hashlib.sha256(facts_path.read_bytes()).hexdigest(),
    }
    output.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output / "model.joblib")
    (output / "metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
