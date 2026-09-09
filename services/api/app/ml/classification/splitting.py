# AGNIDRISHTI API — Phase 8 Spatial Grouped Dataset Splitting
"""
Grouped cross-validation and train/val/test splitting for Phase 8.
Prevents spatial autocorrelation leakage by ensuring that observations from the same
geographic ~5km grid cell are strictly segregated to a single split partition.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from sklearn.model_selection import GroupShuffleSplit

from app.ml.classification.constants import RANDOM_SEED
from app.ml.classification.dataset import DatasetRecord


def split_grouped_dataset(
    records: list[DatasetRecord],
    test_size: float = 0.15,
    val_size: float = 0.15,
    random_state: int = RANDOM_SEED,
) -> tuple[list[DatasetRecord], list[DatasetRecord], list[DatasetRecord]]:
    """
    Deterministically split dataset records into (train, val, test) partitions
    grouped strictly by spatial_group (~5km grid cell).

    Steps:
    1. First GroupShuffleSplit reserves `test_size` proportion of groups for Test.
    2. Second GroupShuffleSplit splits remaining records into Train and Validation
       where `val_size` proportion of total groups goes to Validation.
    """
    if not records:
        return [], [], []

    groups = np.array([r.spatial_group for r in records])
    indices = np.arange(len(records))

    # Step 1: Split into (train_val, test)
    gss_test = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    train_val_idx, test_idx = next(gss_test.split(indices, groups=groups))

    train_val_records = [records[i] for i in train_val_idx]
    test_records = [records[i] for i in test_idx]

    # Step 2: Split train_val into (train, val)
    # Adjust val_size relative to train_val subset
    rel_val_size = val_size / (1.0 - test_size)
    groups_train_val = np.array([r.spatial_group for r in train_val_records])
    indices_train_val = np.arange(len(train_val_records))

    gss_val = GroupShuffleSplit(n_splits=1, test_size=rel_val_size, random_state=random_state)
    train_idx, val_idx = next(gss_val.split(indices_train_val, groups=groups_train_val))

    train_records = [train_val_records[i] for i in train_idx]
    val_records = [train_val_records[i] for i in val_idx]

    return train_records, val_records, test_records


def audit_group_leakage(
    train: Sequence[DatasetRecord],
    val: Sequence[DatasetRecord],
    test: Sequence[DatasetRecord],
) -> dict[str, int]:
    """
    Audit that no spatial group is shared across splits.
    Returns dictionary with overlap counts. All overlap counts MUST be 0.
    """
    train_groups = {r.spatial_group for r in train}
    val_groups = {r.spatial_group for r in val}
    test_groups = {r.spatial_group for r in test}

    return {
        "train_val_overlap": len(train_groups.intersection(val_groups)),
        "train_test_overlap": len(train_groups.intersection(test_groups)),
        "val_test_overlap": len(val_groups.intersection(test_groups)),
    }
