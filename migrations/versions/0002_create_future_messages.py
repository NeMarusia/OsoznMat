"""create future messages table

Revision ID: 0002_create_future_messages
Revises: 0001_create_users
Create Date: 2026-07-04
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_create_future_messages"
down_revision = "0001_create_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "future_messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("chat_id", sa.Integer(), nullable=False),
        sa.Column("node_id", sa.String(), nullable=False),
        sa.Column("source_node_id", sa.String(), nullable=True),
        sa.Column("send_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_future_messages_node_id", "future_messages", ["node_id"], unique=False)
    op.create_index("ix_future_messages_send_at", "future_messages", ["send_at"], unique=False)
    op.create_index("ix_future_messages_status", "future_messages", ["status"], unique=False)
    op.create_index("ix_future_messages_user_id", "future_messages", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_future_messages_user_id", table_name="future_messages")
    op.drop_index("ix_future_messages_status", table_name="future_messages")
    op.drop_index("ix_future_messages_send_at", table_name="future_messages")
    op.drop_index("ix_future_messages_node_id", table_name="future_messages")
    op.drop_table("future_messages")
