# 后端目录说明

本目录用于承载 NetWorkspace 的后端 API 与业务逻辑。

## 目标

- 提供统一 API
- 支撑工作区、模板、任务、数据、分析和审核流程
- 解耦 Web 请求和采集执行
- 为 Agent 和知识库提供接口层

## 推荐技术栈

- FastAPI
- SQLAlchemy 2.0
- Pydantic
- Alembic
- Redis
- Celery 或 RQ

## 建议目录

```text
backend/
  app/
    api/
    core/
    models/
    schemas/
    services/
    repositories/
    tasks/
    agents/
    kb/
```
