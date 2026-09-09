# AGNIDRISHTI — Phase 7 Feature Matrix CSV Export Utility
"""
CLI utility to export canonical, versioned fusion_v1 feature matrices for Phase 8 modeling.

Guarantees:
- Canonical deterministic column ordering matching fusion_v1 registry.
- Deterministic row ordering (sorted by observation_id ASC).
- Missing values exported as empty strings (no fake numeric sentinels).
- Zero training labels or predictive fire scores.
- Raw geographic coordinates (lat/lon) excluded from model features.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import sys
from pathlib import Path

from sqlalchemy import select

from app.db.models.feature_fusion_profile import ThermalFeatureFusionProfileModel
from app.db.session import get_session_factory
from app.services.fusion.feature_registry import SCHEMA_VERSION_V1, fusion_v1_registry


async def export_features_csv(
    output_path: Path,
    limit: int | None = None,
    schema_version: str = SCHEMA_VERSION_V1,
) -> int:
    registry = fusion_v1_registry
    model_eligible_specs = [f for f in registry.features if f.model_eligible]
    model_feature_names = [f.name for f in model_eligible_specs]

    # Deterministic header
    header = [
        "observation_id",
        "fusion_status",
        "feature_coverage_fraction",
        *model_feature_names,
        "schema_version",
        "schema_hash",
    ]

    session_factory = get_session_factory()
    async with session_factory() as session:
        stmt = (
            select(ThermalFeatureFusionProfileModel)
            .where(ThermalFeatureFusionProfileModel.schema_version == schema_version)
            .order_by(ThermalFeatureFusionProfileModel.observation_id.asc())
        )
        if limit is not None and limit > 0:
            stmt = stmt.limit(limit)

        res = await session.execute(stmt)
        profiles = res.scalars().all()

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(header)

            for p in profiles:
                f_vec = p.feature_vector or {}
                row = [
                    p.observation_id,
                    p.fusion_status,
                    round(p.feature_coverage_fraction, 4),
                ]
                for name in model_feature_names:
                    val = f_vec.get(name)
                    # Preserve honest NULLs as empty string
                    if val is None:
                        row.append("")
                    else:
                        row.append(val)

                row.append(p.schema_version)
                row.append(p.schema_hash)
                writer.writerow(row)

    return len(profiles)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export canonical Phase 7 fusion feature matrix to CSV.")
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="../../data/exports/fusion_v1_matrix.csv",
        help="Target CSV output file path",
    )
    parser.add_argument(
        "--limit",
        "-l",
        type=int,
        default=None,
        help="Maximum rows to export (default: all)",
    )
    parser.add_argument(
        "--schema-version",
        type=str,
        default=SCHEMA_VERSION_V1,
        help="Schema version (default: 'fusion_v1')",
    )

    args = parser.parse_args()
    out_p = Path(args.output).resolve()

    count = asyncio.run(export_features_csv(out_p, limit=args.limit, schema_version=args.schema_version))
    print(f"Exported {count} fusion profiles to {out_p}", file=sys.stderr)


if __name__ == "__main__":
    main()
