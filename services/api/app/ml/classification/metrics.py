# AGNIDRISHTI API — Phase 8 Evaluation & Metrics Module
"""
Evaluation metrics calculation, confusion matrix generation, and reporting
for Phase 8 Intelligent Classification Engine.
Primary model selection metric: Macro F1.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from sklearn.metrics import (
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

from app.ml.classification.schemas import ClassMetric, MetricsSummary


def calculate_metrics(
    y_true: Sequence[str],
    y_pred: Sequence[str],
    class_names: list[str],
    validation_status: str,
) -> MetricsSummary:
    """
    Calculate comprehensive evaluation metrics across all evaluated classes.
    Respects scientific honesty: weak labels are evaluated as weak-label agreement.
    """
    macro_f1 = float(f1_score(y_true, y_pred, labels=class_names, average="macro", zero_division=0))
    weighted_f1 = float(f1_score(y_true, y_pred, labels=class_names, average="weighted", zero_division=0))
    balanced_acc = float(balanced_accuracy_score(y_true, y_pred))

    # Per-class metrics
    p_per_class = np.atleast_1d(precision_score(y_true, y_pred, labels=class_names, average=None, zero_division=0))
    r_per_class = np.atleast_1d(recall_score(y_true, y_pred, labels=class_names, average=None, zero_division=0))
    f1_per_class = np.atleast_1d(f1_score(y_true, y_pred, labels=class_names, average=None, zero_division=0))

    # Support counts
    true_counts: dict[str, int] = {c: int(np.sum(np.array(y_true) == c)) for c in class_names}

    per_class_metrics: dict[str, ClassMetric] = {}
    for i, name in enumerate(class_names):
        per_class_metrics[name] = ClassMetric(
            precision=round(float(p_per_class[i]), 4),
            recall=round(float(r_per_class[i]), 4),
            f1_score=round(float(f1_per_class[i]), 4),
            support=true_counts.get(name, 0),
        )

    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred, labels=class_names)
    cm_dict = {
        name: {col: int(cm[row_idx][col_idx]) for col_idx, col in enumerate(class_names)}
        for row_idx, name in enumerate(class_names)
    }

    return MetricsSummary(
        macro_f1=round(macro_f1, 4),
        weighted_f1=round(weighted_f1, 4),
        balanced_accuracy=round(balanced_acc, 4),
        per_class=per_class_metrics,
        confusion_matrix=cm_dict,
        class_names=class_names,
        total_eval_samples=len(y_true),
        evaluation_type=(
            "VERIFIED TEST PERFORMANCE"
            if "VERIFIED" in validation_status
            else "WEAK-LABEL AGREEMENT"
        ),
    )
