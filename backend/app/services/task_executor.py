"""Task execution service - 连接 DSL 执行器与 API 层。"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import CrawlTask, TaskRunLog
from app.models.template import TemplateVersion
from app.spiders.dsl_executor import DSLExecutor

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 日志辅助
# ---------------------------------------------------------------------------

async def _write_log(
    db: AsyncSession,
    task_id: int,
    log_level: str,
    event_type: str,
    message: str,
    payload: dict[str, Any] | None = None,
) -> None:
    log = TaskRunLog(
        task_id=task_id,
        log_level=log_level,
        event_type=event_type,
        message=message,
        payload=payload,
    )
    db.add(log)
    await db.flush()


def _make_log_callback(db: AsyncSession, task_id: int):
    """返回一个可在 DSLExecutor 中使用的 async 日志回调。"""

    async def callback(
        log_level: str,
        event_type: str,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        await _write_log(db, task_id, log_level, event_type, message, payload)

    return callback


# ---------------------------------------------------------------------------
# 任务执行入口
# ---------------------------------------------------------------------------

async def execute_task(
    db: AsyncSession, task_id: int, user_id: int
) -> dict[str, Any]:
    """加载任务 → 加载 DSL → 调用 DSLExecutor → 更新任务状态。"""

    # 1. 加载任务
    result = await db.execute(select(CrawlTask).where(CrawlTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        return {"ok": False, "error": "task not found"}

    # 2. 加载 template_version + DSL
    result = await db.execute(
        select(TemplateVersion).where(TemplateVersion.id == task.template_version_id)
    )
    version = result.scalar_one_or_none()
    if not version:
        return {"ok": False, "error": "template version not found"}

    dsl_content = version.dsl_content
    if not dsl_content:
        return {"ok": False, "error": "DSL content is empty"}

    # 尝试从 DSL meta 读取 source_id
    source_id = (
        dsl_content.get("meta", {}).get("source_id")
        or task.task_params.get("source_id", 1)
    )

    # 3. 更新任务状态 → running
    task.task_status = "running"
    task.started_at = datetime.now()
    await db.flush()

    log_cb = _make_log_callback(db, task.id)

    try:
        # 4. 执行
        executor = DSLExecutor(
            dsl_content, db, task.workspace_id, task.id, source_id, user_id
        )
        task_params = task.task_params or {}
        stats = await executor.execute(task_params, log_callback=log_cb)

        # 5. 更新任务状态 → completed
        task.task_status = "completed"
        task.finished_at = datetime.now()
        task.total_records = stats.get("new_records", 0)
        await db.flush()

        await _write_log(
            db, task.id, "info", "task_completed",
            f"任务完成，新增 {stats.get('new_records', 0)} 条，"
            f"跳过重复 {stats.get('duplicate_skipped', 0)} 条",
            payload=stats,
        )

        return {"ok": True, "stats": stats}

    except Exception as e:
        logger.exception("Task execution failed")
        task.task_status = "failed"
        task.finished_at = datetime.now()
        task.error_summary = str(e)[:500]
        await db.flush()

        await _write_log(
            db, task.id, "error", "task_failed",
            f"任务失败: {str(e)[:200]}"
        )
        return {"ok": False, "error": str(e)}
