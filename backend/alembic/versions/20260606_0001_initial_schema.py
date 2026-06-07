"""initial schema

Revision ID: 20260606_0001
Revises:
Create Date: 2026-06-06 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260606_0001"
down_revision = None
branch_labels = None
depends_on = None


def json_type() -> sa.JSON:
    return sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("username", name="uq_users_username"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_role_status", "users", ["role", "status"])

    op.create_table(
        "workspaces",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_workspaces_user_id_users", ondelete="CASCADE"),
        sa.UniqueConstraint("slug", name="uq_workspaces_slug"),
    )
    op.create_index("ix_workspaces_user_id", "workspaces", ["user_id"])

    op.create_table(
        "sources",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("source_name", sa.String(length=100), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("content_type", sa.String(length=32), nullable=False),
        sa.Column("site_locale", sa.String(length=32), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("domain", name="uq_sources_domain"),
    )
    op.create_index("ix_sources_source_type_status", "sources", ["source_type", "status"])

    op.create_table(
        "templates",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("workspace_id", sa.BigInteger(), nullable=True),
        sa.Column("source_id", sa.BigInteger(), nullable=False),
        sa.Column("template_name", sa.String(length=100), nullable=False),
        sa.Column("display_name", sa.String(length=150), nullable=False),
        sa.Column("template_scope", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("current_version_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name="fk_templates_workspace_id_workspaces",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["sources.id"],
            name="fk_templates_source_id_sources",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("workspace_id", "template_name", name="uq_templates_workspace_template_name"),
        sa.UniqueConstraint(
            "source_id",
            "template_name",
            "template_scope",
            name="uq_templates_source_template_name_template_scope",
        ),
    )
    op.create_index("ix_templates_workspace_id", "templates", ["workspace_id"])
    op.create_index("ix_templates_source_id", "templates", ["source_id"])
    op.create_index("ix_templates_template_scope_status", "templates", ["template_scope", "status"])

    op.create_table(
        "template_versions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("template_id", sa.BigInteger(), nullable=False),
        sa.Column("version", sa.String(length=32), nullable=False),
        sa.Column("dsl_content", json_type(), nullable=False),
        sa.Column("generation_source", sa.String(length=32), nullable=False),
        sa.Column("confidence_level", sa.String(length=16), nullable=True),
        sa.Column("change_summary", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["template_id"],
            ["templates.id"],
            name="fk_template_versions_template_id_templates",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name="fk_template_versions_created_by_user_id_users",
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint("template_id", "version", name="uq_template_versions_template_id_version"),
    )
    op.create_index("ix_template_versions_template_id", "template_versions", ["template_id"])
    op.create_index("ix_template_versions_generation_source", "template_versions", ["generation_source"])

    op.create_foreign_key(
        "fk_templates_current_version_id_template_versions",
        "templates",
        "template_versions",
        ["current_version_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "onboarding_requests",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("workspace_id", sa.BigInteger(), nullable=False),
        sa.Column("source_id", sa.BigInteger(), nullable=True),
        sa.Column("submitted_by_user_id", sa.BigInteger(), nullable=False),
        sa.Column("target_url", sa.Text(), nullable=False),
        sa.Column("content_type_hint", sa.String(length=32), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("site_guess", sa.String(length=64), nullable=True),
        sa.Column("render_mode_guess", sa.String(length=32), nullable=True),
        sa.Column("risk_flags", json_type(), nullable=True),
        sa.Column("analysis_summary", json_type(), nullable=True),
        sa.Column("published_template_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name="fk_onboarding_requests_workspace_id_workspaces",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["sources.id"],
            name="fk_onboarding_requests_source_id_sources",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["submitted_by_user_id"],
            ["users.id"],
            name="fk_onboarding_requests_submitted_by_user_id_users",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["published_template_id"],
            ["templates.id"],
            name="fk_onboarding_requests_published_template_id_templates",
            ondelete="SET NULL",
        ),
    )
    op.create_index("ix_onboarding_requests_workspace_id", "onboarding_requests", ["workspace_id"])
    op.create_index(
        "ix_onboarding_requests_submitted_by_user_id",
        "onboarding_requests",
        ["submitted_by_user_id"],
    )
    op.create_index("ix_onboarding_requests_status", "onboarding_requests", ["status"])

    op.create_table(
        "template_test_runs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("template_version_id", sa.BigInteger(), nullable=False),
        sa.Column("onboarding_request_id", sa.BigInteger(), nullable=True),
        sa.Column("test_url", sa.Text(), nullable=False),
        sa.Column("test_status", sa.String(length=32), nullable=False),
        sa.Column("sample_size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("items_found", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("detail_success_rate", sa.Numeric(5, 4), nullable=True),
        sa.Column("field_completeness", json_type(), nullable=True),
        sa.Column("sample_result", json_type(), nullable=True),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["template_version_id"],
            ["template_versions.id"],
            name="fk_template_test_runs_template_version_id_template_versions",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["onboarding_request_id"],
            ["onboarding_requests.id"],
            name="fk_template_test_runs_onboarding_request_id_onboarding_requests",
            ondelete="SET NULL",
        ),
    )
    op.create_index("ix_template_test_runs_template_version_id", "template_test_runs", ["template_version_id"])
    op.create_index(
        "ix_template_test_runs_onboarding_request_id",
        "template_test_runs",
        ["onboarding_request_id"],
    )
    op.create_index("ix_template_test_runs_test_status", "template_test_runs", ["test_status"])

    op.create_table(
        "crawl_tasks",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("workspace_id", sa.BigInteger(), nullable=False),
        sa.Column("template_version_id", sa.BigInteger(), nullable=False),
        sa.Column("created_by_user_id", sa.BigInteger(), nullable=False),
        sa.Column("task_name", sa.String(length=150), nullable=False),
        sa.Column("task_status", sa.String(length=32), nullable=False),
        sa.Column("task_params", json_type(), nullable=False),
        sa.Column("schedule_type", sa.String(length=32), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_records", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name="fk_crawl_tasks_workspace_id_workspaces",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["template_version_id"],
            ["template_versions.id"],
            name="fk_crawl_tasks_template_version_id_template_versions",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name="fk_crawl_tasks_created_by_user_id_users",
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_crawl_tasks_workspace_id", "crawl_tasks", ["workspace_id"])
    op.create_index("ix_crawl_tasks_template_version_id", "crawl_tasks", ["template_version_id"])
    op.create_index("ix_crawl_tasks_task_status", "crawl_tasks", ["task_status"])
    op.create_index("ix_crawl_tasks_scheduled_at", "crawl_tasks", ["scheduled_at"])

    op.create_table(
        "task_run_logs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("task_id", sa.BigInteger(), nullable=False),
        sa.Column("log_level", sa.String(length=16), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("payload", json_type(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["crawl_tasks.id"],
            name="fk_task_run_logs_task_id_crawl_tasks",
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_task_run_logs_task_id", "task_run_logs", ["task_id"])
    op.create_index("ix_task_run_logs_log_level", "task_run_logs", ["log_level"])
    op.create_index("ix_task_run_logs_event_type", "task_run_logs", ["event_type"])

    op.create_table(
        "job_records",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("workspace_id", sa.BigInteger(), nullable=False),
        sa.Column("task_id", sa.BigInteger(), nullable=False),
        sa.Column("source_id", sa.BigInteger(), nullable=False),
        sa.Column("source_job_id", sa.String(length=255), nullable=True),
        sa.Column("job_url", sa.Text(), nullable=False),
        sa.Column("job_title", sa.String(length=255), nullable=False),
        sa.Column("job_category", sa.String(length=100), nullable=True),
        sa.Column("company_name", sa.String(length=255), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("education", sa.String(length=100), nullable=True),
        sa.Column("experience_text", sa.String(length=100), nullable=True),
        sa.Column("salary_text", sa.String(length=100), nullable=True),
        sa.Column("salary_min", sa.Numeric(12, 2), nullable=True),
        sa.Column("salary_max", sa.Numeric(12, 2), nullable=True),
        sa.Column("salary_currency", sa.String(length=16), nullable=True),
        sa.Column("salary_period", sa.String(length=32), nullable=True),
        sa.Column("publish_date", sa.Date(), nullable=True),
        sa.Column("job_description", sa.Text(), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("raw_data", json_type(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name="fk_job_records_workspace_id_workspaces",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["crawl_tasks.id"],
            name="fk_job_records_task_id_crawl_tasks",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["sources.id"],
            name="fk_job_records_source_id_sources",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "workspace_id",
            "source_id",
            "source_job_id",
            name="uq_job_records_workspace_source_source_job_id",
        ),
    )
    op.create_index("ix_job_records_workspace_id", "job_records", ["workspace_id"])
    op.create_index("ix_job_records_task_id", "job_records", ["task_id"])
    op.create_index("ix_job_records_source_id", "job_records", ["source_id"])
    op.create_index("ix_job_records_job_title", "job_records", ["job_title"])
    op.create_index("ix_job_records_company_name", "job_records", ["company_name"])
    op.create_index("ix_job_records_city", "job_records", ["city"])
    op.create_index("ix_job_records_education", "job_records", ["education"])
    op.create_index("ix_job_records_publish_date", "job_records", ["publish_date"])
    op.create_index("ix_job_records_captured_at", "job_records", ["captured_at"])
    op.create_index("ix_job_records_is_active", "job_records", ["is_active"])

    op.create_table(
        "proposals",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("workspace_id", sa.BigInteger(), nullable=False),
        sa.Column("submitted_by_user_id", sa.BigInteger(), nullable=False),
        sa.Column("proposal_type", sa.String(length=32), nullable=False),
        sa.Column("target_type", sa.String(length=32), nullable=False),
        sa.Column("target_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("review_status", sa.String(length=32), nullable=False),
        sa.Column("reviewed_by_user_id", sa.BigInteger(), nullable=True),
        sa.Column("review_comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name="fk_proposals_workspace_id_workspaces",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["submitted_by_user_id"],
            ["users.id"],
            name="fk_proposals_submitted_by_user_id_users",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by_user_id"],
            ["users.id"],
            name="fk_proposals_reviewed_by_user_id_users",
            ondelete="SET NULL",
        ),
    )
    op.create_index("ix_proposals_workspace_id", "proposals", ["workspace_id"])
    op.create_index("ix_proposals_submitted_by_user_id", "proposals", ["submitted_by_user_id"])
    op.create_index("ix_proposals_review_status", "proposals", ["review_status"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("workspace_id", sa.BigInteger(), nullable=True),
        sa.Column("actor_type", sa.String(length=32), nullable=False),
        sa.Column("actor_id", sa.BigInteger(), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("target_type", sa.String(length=64), nullable=False),
        sa.Column("target_id", sa.BigInteger(), nullable=False),
        sa.Column("before_snapshot", json_type(), nullable=True),
        sa.Column("after_snapshot", json_type(), nullable=True),
        sa.Column("metadata", json_type(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name="fk_audit_logs_workspace_id_workspaces",
            ondelete="SET NULL",
        ),
    )
    op.create_index("ix_audit_logs_workspace_id", "audit_logs", ["workspace_id"])
    op.create_index("ix_audit_logs_actor_type_actor_id", "audit_logs", ["actor_type", "actor_id"])
    op.create_index("ix_audit_logs_target_type_target_id", "audit_logs", ["target_type", "target_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_index("ix_audit_logs_target_type_target_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_actor_type_actor_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_workspace_id", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("ix_proposals_review_status", table_name="proposals")
    op.drop_index("ix_proposals_submitted_by_user_id", table_name="proposals")
    op.drop_index("ix_proposals_workspace_id", table_name="proposals")
    op.drop_table("proposals")

    op.drop_index("ix_job_records_is_active", table_name="job_records")
    op.drop_index("ix_job_records_captured_at", table_name="job_records")
    op.drop_index("ix_job_records_publish_date", table_name="job_records")
    op.drop_index("ix_job_records_education", table_name="job_records")
    op.drop_index("ix_job_records_city", table_name="job_records")
    op.drop_index("ix_job_records_company_name", table_name="job_records")
    op.drop_index("ix_job_records_job_title", table_name="job_records")
    op.drop_index("ix_job_records_source_id", table_name="job_records")
    op.drop_index("ix_job_records_task_id", table_name="job_records")
    op.drop_index("ix_job_records_workspace_id", table_name="job_records")
    op.drop_table("job_records")

    op.drop_index("ix_task_run_logs_event_type", table_name="task_run_logs")
    op.drop_index("ix_task_run_logs_log_level", table_name="task_run_logs")
    op.drop_index("ix_task_run_logs_task_id", table_name="task_run_logs")
    op.drop_table("task_run_logs")

    op.drop_index("ix_crawl_tasks_scheduled_at", table_name="crawl_tasks")
    op.drop_index("ix_crawl_tasks_task_status", table_name="crawl_tasks")
    op.drop_index("ix_crawl_tasks_template_version_id", table_name="crawl_tasks")
    op.drop_index("ix_crawl_tasks_workspace_id", table_name="crawl_tasks")
    op.drop_table("crawl_tasks")

    op.drop_index("ix_template_test_runs_test_status", table_name="template_test_runs")
    op.drop_index("ix_template_test_runs_onboarding_request_id", table_name="template_test_runs")
    op.drop_index("ix_template_test_runs_template_version_id", table_name="template_test_runs")
    op.drop_table("template_test_runs")

    op.drop_index("ix_onboarding_requests_status", table_name="onboarding_requests")
    op.drop_index("ix_onboarding_requests_submitted_by_user_id", table_name="onboarding_requests")
    op.drop_index("ix_onboarding_requests_workspace_id", table_name="onboarding_requests")
    op.drop_table("onboarding_requests")

    op.drop_constraint("fk_templates_current_version_id_template_versions", "templates", type_="foreignkey")
    op.drop_index("ix_template_versions_generation_source", table_name="template_versions")
    op.drop_index("ix_template_versions_template_id", table_name="template_versions")
    op.drop_table("template_versions")

    op.drop_index("ix_templates_template_scope_status", table_name="templates")
    op.drop_index("ix_templates_source_id", table_name="templates")
    op.drop_index("ix_templates_workspace_id", table_name="templates")
    op.drop_table("templates")

    op.drop_index("ix_sources_source_type_status", table_name="sources")
    op.drop_table("sources")

    op.drop_index("ix_workspaces_user_id", table_name="workspaces")
    op.drop_table("workspaces")

    op.drop_index("ix_users_role_status", table_name="users")
    op.drop_table("users")

