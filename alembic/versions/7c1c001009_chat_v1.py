"""Normalize owner-scoped asynchronous chat storage."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import context, op

revision = "7c1c001009"
down_revision = "6b1c001008"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    conversation_missing = context.is_offline_mode() or not sa.inspect(bind).has_table(
        "conversations"
    )
    if conversation_missing:
        # Legacy deployments got this table from Base.create_all(); fresh Alembic
        # installs need the compatible parent table before normalized v1 FKs.
        op.create_table(
            "conversations",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column(
                "user_id", sa.String(128), nullable=False, server_default="local"
            ),
            sa.Column("title", sa.String(256)),
            sa.Column("messages", sa.JSON()),
            sa.Column("related_event_ids", postgresql.ARRAY(sa.Integer())),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )
        op.create_index("ix_conversations_user_id", "conversations", ["user_id"])
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "conversation_id",
            sa.Integer(),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("owner_id", sa.String(128), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("method", sa.String(128)),
        sa.Column(
            "related_subject_ids", sa.JSON(), nullable=False, server_default="[]"
        ),
        sa.Column("prompt_version", sa.String(128)),
        sa.Column("model_version", sa.String(255)),
        sa.Column("input_tokens", sa.Integer()),
        sa.Column("output_tokens", sa.Integer()),
        sa.Column("cost_micros", sa.Integer()),
        sa.Column("error_code", sa.String(128)),
        sa.Column("degraded", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "role IN ('user','assistant','system')", name="ck_chat_message_role"
        ),
    )
    op.create_index("ix_chat_message_owner_id", "chat_messages", ["owner_id"])
    op.create_index(
        "ix_chat_message_conversation_created",
        "chat_messages",
        ["conversation_id", "created_at"],
    )
    op.create_table(
        "chat_jobs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "conversation_id",
            sa.Integer(),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_message_id",
            sa.Uuid(),
            sa.ForeignKey("chat_messages.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "assistant_message_id",
            sa.Uuid(),
            sa.ForeignKey("chat_messages.id", ondelete="SET NULL"),
        ),
        sa.Column("owner_id", sa.String(128), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="queued"),
        sa.Column("camera", sa.String(255)),
        sa.Column("site_id", sa.String(255), nullable=False, server_default="default"),
        sa.Column("timezone", sa.String(128), nullable=False, server_default="UTC"),
        sa.Column("error_code", sa.String(128)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "status IN ('queued','running','ready','failed')", name="ck_chat_job_status"
        ),
    )
    op.create_index("ix_chat_job_owner_id", "chat_jobs", ["owner_id"])
    op.create_index("ix_chat_job_owner_status", "chat_jobs", ["owner_id", "status"])


def downgrade():
    op.drop_table("chat_jobs")
    op.drop_table("chat_messages")
    # conversations predates Alembic in legacy installs and may contain rollback
    # data, so this migration intentionally never deletes it.
