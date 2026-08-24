"""Application-owned versioned semantic embedding records."""

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from alembic import op

revision = "5a1c001007"
down_revision = None
branch_labels = None
depends_on = None
DIMENSIONS = 512


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "embedding_records",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("subject_type", sa.String(64), nullable=False),
        sa.Column("subject_id", sa.Uuid(), nullable=False),
        sa.Column("subject_revision", sa.String(128), nullable=False),
        sa.Column("modality", sa.String(32), nullable=False),
        sa.Column("vector", Vector(DIMENSIONS), nullable=False),
        sa.Column("dimensions", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(128), nullable=False),
        sa.Column("model", sa.String(255), nullable=False),
        sa.Column("model_version", sa.String(255), nullable=False),
        sa.Column("source_claim_id", sa.Uuid(), nullable=False),
        sa.Column("source_job_id", sa.Uuid(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("camera", sa.String(255)),
        sa.Column("site", sa.String(255)),
        sa.Column("labels", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("occurred_at", sa.DateTime(timezone=True)),
        sa.Column("evidence_ids", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("superseded_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint(f"dimensions = {DIMENSIONS}", name="ck_embedding_dimensions"),
        sa.UniqueConstraint(
            "subject_type",
            "subject_id",
            "subject_revision",
            "modality",
            "provider",
            "model",
            "model_version",
            "content_hash",
            name="uq_embedding_identity",
        ),
    )
    op.create_index("ix_embedding_subject", "embedding_records", ["subject_type", "subject_id"])
    op.create_index("ix_embedding_filters", "embedding_records", ["camera", "site", "occurred_at"])
    op.create_index(
        "ix_embedding_active_model",
        "embedding_records",
        ["model", "model_version", "superseded_at"],
    )
    op.execute(
        "CREATE INDEX ix_embedding_vector_hnsw ON embedding_records "
        "USING hnsw (vector vector_cosine_ops)"
    )


def downgrade():
    op.drop_table("embedding_records")
