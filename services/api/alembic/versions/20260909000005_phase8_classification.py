"""Phase 8 Classification Engine Intelligence Profiles

Revision ID: 20260909000005
Revises: 20260909000004
Create Date: 2026-09-09 22:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260909000005"
down_revision: str | None = "20260909000004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    # 1. thermal_classification_labels
    if "thermal_classification_labels" not in existing_tables:
        op.create_table(
            "thermal_classification_labels",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("observation_id", sa.String(length=64), nullable=False),
            sa.Column("label", sa.String(length=64), nullable=False),
            sa.Column("label_source", sa.String(length=64), nullable=False),
            sa.Column("label_provenance", sa.String(length=32), nullable=False),
            sa.Column("label_version", sa.String(length=32), server_default="label_v1", nullable=False),
            sa.Column("confidence_tier", sa.String(length=32), nullable=False),
            sa.Column("reference", sa.String(length=255), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(
                ["observation_id"],
                ["thermal_observations.observation_id"],
                ondelete="CASCADE",
                name="fk_classification_labels_observation_id",
            ),
            sa.PrimaryKeyConstraint("id", name="pk_thermal_classification_labels"),
            sa.UniqueConstraint(
                "observation_id",
                "label_version",
                name="uq_classification_observation_label_version",
            ),
        )
        op.create_index(
            "ix_classification_labels_observation_id",
            "thermal_classification_labels",
            ["observation_id"],
            unique=False,
        )
        op.create_index(
            "ix_classification_labels_label",
            "thermal_classification_labels",
            ["label"],
            unique=False,
        )
        op.create_index(
            "ix_classification_labels_provenance",
            "thermal_classification_labels",
            ["label_provenance"],
            unique=False,
        )

    # 2. thermal_classification_predictions
    if "thermal_classification_predictions" not in existing_tables:
        op.create_table(
            "thermal_classification_predictions",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("observation_id", sa.String(length=64), nullable=False),
            sa.Column("model_version", sa.String(length=64), nullable=False),
            sa.Column("fusion_schema_version", sa.String(length=32), server_default="fusion_v1", nullable=False),
            sa.Column("fusion_schema_hash", sa.String(length=64), nullable=False),
            sa.Column("fusion_source_fingerprint", sa.String(length=64), nullable=False),
            sa.Column("classification_status", sa.String(length=32), nullable=False),
            sa.Column("predicted_class", sa.String(length=64), nullable=True),
            sa.Column("class_score", sa.Float(), nullable=True),
            sa.Column("class_probabilities", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("evidence_coverage", sa.Float(), nullable=True),
            sa.Column("validation_status", sa.String(length=64), nullable=False),
            sa.Column("model_artifact_hash", sa.String(length=64), nullable=True),
            sa.Column("predicted_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(
                ["observation_id"],
                ["thermal_observations.observation_id"],
                ondelete="CASCADE",
                name="fk_classification_predictions_observation_id",
            ),
            sa.PrimaryKeyConstraint("id", name="pk_thermal_classification_predictions"),
            sa.UniqueConstraint(
                "observation_id",
                "model_version",
                name="uq_classification_observation_model_version",
            ),
        )
        op.create_index(
            "ix_classification_predictions_observation_id",
            "thermal_classification_predictions",
            ["observation_id"],
            unique=False,
        )
        op.create_index(
            "ix_classification_predictions_model_version",
            "thermal_classification_predictions",
            ["model_version"],
            unique=False,
        )
        op.create_index(
            "ix_classification_predictions_status",
            "thermal_classification_predictions",
            ["classification_status"],
            unique=False,
        )
        op.create_index(
            "ix_classification_predictions_class",
            "thermal_classification_predictions",
            ["predicted_class"],
            unique=False,
        )


def downgrade() -> None:
    op.drop_table("thermal_classification_predictions")
    op.drop_table("thermal_classification_labels")
