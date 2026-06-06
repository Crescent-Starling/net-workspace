# NetWorkspace

一个 AI 原生的招聘情报工作台，用于站点接入、数据采集、历史沉淀、分析展示，以及个人 AI 助手和工具搭建。

## 项目概述

本项目是对旧版招聘爬虫课程项目的全新重构。

核心目标：

- 保留旧项目最有价值的核心思路：把短时存在的招聘网站信息转化为可长期分析的历史数据资产。
- 使用更易维护的前后端架构进行重建。
- 支持官方模板、个人模板和 AI 辅助站点接入。
- 将用户个性化扩展隔离在个人工作区内，而不是直接修改主系统。

## 命名体系

- 产品名：`NetWorkspace`
- 采集引擎：`SpiderCore`
- AI 助手：`Todd`
- 仓库名：`net-workspace`

## 文档索引

- 产品需求文档：[`docs/PRD.md`](docs/PRD.md)
- 系统架构说明：[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- 数据库设计草案：[`docs/DATABASE_DESIGN.md`](docs/DATABASE_DESIGN.md)
- 模板 DSL 设计：[`docs/TEMPLATE_DSL.md`](docs/TEMPLATE_DSL.md)
- 智能站点接入工作流：[`docs/SITE_ONBOARDING_WORKFLOW.md`](docs/SITE_ONBOARDING_WORKFLOW.md)
- 开发说明：[`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md)
- 旧项目价值提炼：[`docs/LEGACY_REFERENCE.md`](docs/LEGACY_REFERENCE.md)
- 仓库与协作说明：[`docs/REPOSITORY_SETUP.md`](docs/REPOSITORY_SETUP.md)

## 项目结构

```text
net-workspace/
  README.md
  .gitignore
  docs/
    PRD.md
    LEGACY_REFERENCE.md
    REPOSITORY_SETUP.md
  frontend/
  backend/
    app/
  spiders/
  tests/
  archive/
```

## 推荐技术栈

- 前端：React + TypeScript + Vite + Ant Design + ECharts
- 后端：FastAPI + SQLAlchemy 2.0 + Pydantic + Alembic
- 队列：Redis + Celery 或 RQ
- 数据库：优先 PostgreSQL，也可使用 MySQL 8
- 采集层：Playwright + Requests + BeautifulSoup/lxml
- AI 层：LLM + 多模态页面理解 + RAG 知识库

## 开发语言约定

- 产品文档、设计说明、需求讨论、提交说明默认使用中文。
- 代码中的标识符、目录名、API 路径、数据库字段等技术标识保留英文。
- 必要的专业术语可以中英并用，但以中文表达为主。

## 仓库约定

- 不在旧目录中继续直接开发。
- 旧项目目录保留在新仓库外部，仅作为参考材料使用。
- 只有经过明确筛选的内容，才允许迁移进入新系统。
