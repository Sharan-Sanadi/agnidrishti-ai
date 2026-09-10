"""Phase 9 Model Explainability Intelligence Profiles

Revision ID: 20260909000006
Revises: 20260909000005
Create Date: 2026-09-09 23:15:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260909000006"
down_revision: str | None = "20260909000005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    if "thermal_classification_explanations" not in existing_tables:
        op.create_table(
            "thermal_classification_explanations",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("observation_id", sa.String(length=64), nullable=False),
            sa.Column("model_version", sa.String(length=64), nullable=False),
            sa.Column("explanation_version", sa.String(length=64), server_default="agnidrishti_explainer_v1", nullable=False),
            sa.Column("method_name", sa.String(length=64), nullable=False),
            sa.Column("method_version", sa.String(length=32), nullable=False),
            sa.Column("fusion_schema_version", sa.String(length=32), server_default="fusion_v1", nullable=False),
            sa.Column("fusion_schema_hash", sa.String(length=64), nullable=False),
            sa.Column("fusion_source_fingerprint", sa.String(length=64), nullable=False),
            sa.Column("model_artifact_hash", sa.String(length=64), nullable=False),
            sa.Column("classification_status", sa.String(length=32), nullable=False),
            sa.Column("predicted_class", sa.String(length=64), nullable=True),
            sa.Column("prediction_score", sa.Float(), nullable=True),
            sa.Column("explanation_status", sa.String(length=32), nullable=False),
            sa.Column("base_value", sa.Float(), nullable=True),
            sa.Column("explained_output", sa.Float(), nullable=True),
            sa.Column("additivity_error", sa.Float(), nullable=True),
            sa.Column("feature_contributions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("group_contributions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("top_supporting", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("top_opposing", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("quality_flags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(
                ["observation_id"],
                ["thermal_observations.observation_id"],
                ondelete="CASCADE",
                name="fk_classification_explanations_observation_id",
            ),
            sa.PrimaryKeyConstraint("id", name="pk_thermal_classification_explanations"),
            sa.UniqueConstraint(
                "observation_id",
                "model_version",
                "explanation_version",
                name="uq_classification_explanation_obs_model_version",
            ),
        )
        op.create_index(
            "ix_classification_explanations_observation_id",
            "thermal_classification_explanations",
            ["observation_id"],
            unique=False,
        )
        op.create_index(
            "ix_classification_explanations_model_version",
            "thermal_classification_explanations",
            ["model_version"],
            unique=False,
        )
        op.create_index(
            "ix_classification_explanations_status",
            "thermal_classification_explanations",
            ["explanation_status"],
            unique=False,
        )
        op.create_index(
            "ix_classification_explanations_class",
            "thermal_classification_explanations",
            ["predicted_class"],
            unique=False,
        )


def downgrade() -> None:
    op.drop_table("thermal_classification_explanations")
