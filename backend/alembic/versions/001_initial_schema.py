"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-03-18
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("external_id", sa.String(255), unique=True, index=True, nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("department", sa.String(255), nullable=True),
        sa.Column(
            "tier",
            sa.Enum("standard", "power_user", "vip", "admin", name="usertier"),
            nullable=False,
            server_default="standard",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- jobs ---
    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), index=True, nullable=False),
        sa.Column("original_filename", sa.String(500), nullable=False),
        sa.Column("original_path", sa.String(1000), nullable=False),
        sa.Column("translated_path", sa.String(1000), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=False),
        sa.Column("translated_pages", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "status",
            sa.Enum("pending", "validating", "processing", "completed", "failed", "cancelled", name="jobstatus"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("celery_task_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # --- quota_usage ---
    op.create_table(
        "quota_usage",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), index=True, nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("pages_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "period_type",
            sa.Enum("daily", "monthly", name="periodtype"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- audit_log ---
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("action", sa.String(100), nullable=False, index=True),
        sa.Column("resource_type", sa.String(50), nullable=False),
        sa.Column("resource_id", sa.String(255), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
    )

    # --- glossary_terms ---
    op.create_table(
        "glossary_terms",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_term", sa.String(500), unique=True, index=True, nullable=False),
        sa.Column("target_term", sa.String(500), nullable=False),
        sa.Column("context", sa.Text(), nullable=True),
        sa.Column("do_not_translate", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("glossary_terms")
    op.drop_table("audit_log")
    op.drop_table("quota_usage")
    op.drop_table("jobs")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS usertier")
    op.execute("DROP TYPE IF EXISTS jobstatus")
    op.execute("DROP TYPE IF EXISTS periodtype")
