"""Import all models so Alembic can discover metadata."""

from app.models.audit_log import AuditLog
from app.models.job_record import JobRecord
from app.models.onboarding import OnboardingRequest, TemplateTestRun
from app.models.proposal import Proposal
from app.models.source import Source
from app.models.task import CrawlTask, TaskRunLog
from app.models.template import Template, TemplateVersion
from app.models.user import User
from app.models.workspace import Workspace

__all__ = [
    "AuditLog",
    "CrawlTask",
    "JobRecord",
    "OnboardingRequest",
    "Proposal",
    "Source",
    "TaskRunLog",
    "Template",
    "TemplateTestRun",
    "TemplateVersion",
    "User",
    "Workspace",
]

