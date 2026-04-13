"""Add admin user-management fields to users."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260413_000002"
down_revision = "20260413_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add persisted admin user-management columns to the users table."""
    op.add_column("users", sa.Column("full_name", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("last_login", sa.DateTime(timezone=True), nullable=True))

    op.drop_constraint("conversations_user_id_fkey", "conversations", type_="foreignkey")
    op.create_foreign_key(
        "conversations_user_id_fkey",
        "conversations",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("messages_conversation_id_fkey", "messages", type_="foreignkey")
    op.create_foreign_key(
        "messages_conversation_id_fkey",
        "messages",
        "conversations",
        ["conversation_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("alarm_user_id_fkey", "alarm", type_="foreignkey")
    op.create_foreign_key(
        "alarm_user_id_fkey",
        "alarm",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("alarm_conversation_id_fkey", "alarm", type_="foreignkey")
    op.create_foreign_key(
        "alarm_conversation_id_fkey",
        "alarm",
        "conversations",
        ["conversation_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("documents_uploaded_by_fkey", "documents", type_="foreignkey")
    op.create_foreign_key(
        "documents_uploaded_by_fkey",
        "documents",
        "users",
        ["uploaded_by"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    """Remove admin user-management columns from the users table."""
    op.drop_constraint("documents_uploaded_by_fkey", "documents", type_="foreignkey")
    op.create_foreign_key(
        "documents_uploaded_by_fkey",
        "documents",
        "users",
        ["uploaded_by"],
        ["id"],
    )

    op.drop_constraint("alarm_conversation_id_fkey", "alarm", type_="foreignkey")
    op.create_foreign_key(
        "alarm_conversation_id_fkey",
        "alarm",
        "conversations",
        ["conversation_id"],
        ["id"],
    )

    op.drop_constraint("alarm_user_id_fkey", "alarm", type_="foreignkey")
    op.create_foreign_key(
        "alarm_user_id_fkey",
        "alarm",
        "users",
        ["user_id"],
        ["id"],
    )

    op.drop_constraint("messages_conversation_id_fkey", "messages", type_="foreignkey")
    op.create_foreign_key(
        "messages_conversation_id_fkey",
        "messages",
        "conversations",
        ["conversation_id"],
        ["id"],
    )

    op.drop_constraint("conversations_user_id_fkey", "conversations", type_="foreignkey")
    op.create_foreign_key(
        "conversations_user_id_fkey",
        "conversations",
        "users",
        ["user_id"],
        ["id"],
    )

    op.drop_column("users", "last_login")
    op.drop_column("users", "full_name")
