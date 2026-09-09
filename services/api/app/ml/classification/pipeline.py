# AGNIDRISHTI API — Phase 8 ML Pipeline & Candidate Factory
"""
Scikit-learn Pipeline and ColumnTransformer definitions for Phase 8.
Ensures strictly isolated, training-only imputation, encoding, and scaling.
Includes Baseline (Dummy), Logistic Regression, Random Forest, and HistGradientBoosting candidates.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.ml.classification.constants import RANDOM_SEED


def build_preprocessor(
    numeric_features: Sequence[int | str],
    categorical_features: Sequence[int | str],
    scale_numeric: bool = True,
) -> ColumnTransformer:
    """
    Construct ColumnTransformer for numeric and categorical features.
    - Numeric: Median imputation with missingness indicators + optional standard scaling.
    - Categorical: Constant imputation ("MISSING") + robust one-hot encoding (handle_unknown='ignore').
    """
    numeric_steps: list[tuple[str, Any]] = [
        ("imputer", SimpleImputer(strategy="median", add_indicator=True))
    ]
    if scale_numeric:
        numeric_steps.append(("scaler", StandardScaler()))

    numeric_pipe = Pipeline(numeric_steps)

    categorical_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="constant", fill_value="MISSING")),
        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])

    transformers = []
    if numeric_features:
        transformers.append(("num", numeric_pipe, numeric_features))
    if categorical_features:
        transformers.append(("cat", categorical_pipe, categorical_features))

    return ColumnTransformer(transformers=transformers, remainder="drop")


def build_candidate_pipeline(
    model_family: str,
    numeric_features: Sequence[int | str],
    categorical_features: Sequence[int | str],
    random_state: int = RANDOM_SEED,
) -> Pipeline:
    """
    Construct complete end-to-end Pipeline with preprocessing and classifier estimator.
    Candidate families supported:
    - 'dummy': Trivial majority baseline proving non-trivial learning
    - 'logistic_regression': Scaled linear model with balanced class weighting
    - 'random_forest': Balanced tree ensemble
    - 'hist_gradient_boosting': Fast histogram gradient booster
    """
    family = model_family.lower()

    if family == "dummy":
        preprocessor = build_preprocessor(numeric_features, categorical_features, scale_numeric=False)
        classifier = DummyClassifier(strategy="most_frequent", random_state=random_state)
    elif family == "logistic_regression":
        preprocessor = build_preprocessor(numeric_features, categorical_features, scale_numeric=True)
        classifier = LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            random_state=random_state,
        )
    elif family == "random_forest":
        preprocessor = build_preprocessor(numeric_features, categorical_features, scale_numeric=False)
        classifier = RandomForestClassifier(
            n_estimators=100,
            class_weight="balanced",
            random_state=random_state,
            n_jobs=-1,
        )
    elif family in ("hist_gradient_boosting", "hist_gradient"):
        preprocessor = build_preprocessor(numeric_features, categorical_features, scale_numeric=False)
        classifier = HistGradientBoostingClassifier(
            class_weight="balanced",
            random_state=random_state,
        )
    else:
        raise ValueError(f"Unsupported model family: '{model_family}'")

    return Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", classifier),
    ])
