"""Create application-owned versioned summaries."""

import sqlalchemy as sa

from alembic import op

revision = "6b1c001008"
down_revision = "5a1c001007"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "summaries",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("summary_type", sa.String(32), nullable=False),
        sa.Column("local_date", sa.Date(), nullable=False),
        sa.Column("timezone", sa.String(128), nullable=False),
        sa.Column("site_id", sa.String(255), nullable=False),
        sa.Column("camera_id", sa.String(255)),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("structured_content", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("source_subject_ids", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("generator", sa.String(32), nullable=False),
        sa.Column("model_version", sa.String(255), nullable=False),
        sa.Column("prompt_version", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="queued"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("superseded_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint(
            "status IN ('queued','running','ready','failed')",
            name="ck_summary_status",
        ),
        sa.UniqueConstraint(
            "summary_type", "local_date", "timezone", "site_id", "camera_id",
            "generator", "model_version", "prompt_version", name="uq_summary_generation",
            postgresql_nulls_not_distinct=True,
        ),
    )
    op.create_index(
        "ix_summary_lookup", "summaries",
        ["summary_type", "local_date", "site_id", "camera_id"],
    )
    op.create_index("ix_summary_status", "summaries", ["status", "created_at"])


def downgrade():
    op.drop_table("summaries")
