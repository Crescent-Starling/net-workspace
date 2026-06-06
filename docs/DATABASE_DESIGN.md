# 数据库设计草案（V1）

## 1. 设计原则

1. 同时保留原始数据与结构化数据。
2. 支持历史快照分析，而不只是当前状态展示。
3. 支持多站点、多模板、多工作区。
4. 支持模板版本和任务日志追踪。
5. 支持 Agent 生成与修复过程的审计。

## 2. 核心表

### 2.1 users

存储用户基本信息与角色。

关键字段建议：

- `id`
- `username`
- `email`
- `password_hash`
- `role`
- `status`
- `created_at`

### 2.2 workspaces

每个用户的独立工作区。

关键字段建议：

- `id`
- `user_id`
- `name`
- `description`
- `status`
- `created_at`
- `updated_at`

### 2.3 sources

站点来源定义。

关键字段建议：

- `id`
- `domain`
- `source_name`
- `source_type`
- `status`
- `created_at`

### 2.4 templates

模板主表。

关键字段建议：

- `id`
- `workspace_id`
- `source_id`
- `template_name`
- `template_scope`
- `current_version_id`
- `status`
- `created_at`

说明：

- `template_scope` 可区分 `official`、`personal`、`proposal`

### 2.5 template_versions

模板版本表。

关键字段建议：

- `id`
- `template_id`
- `version`
- `dsl_content`
- `generation_source`
- `confidence`
- `created_by`
- `created_at`

### 2.6 crawl_tasks

采集任务主表。

关键字段建议：

- `id`
- `workspace_id`
- `template_version_id`
- `task_name`
- `task_status`
- `task_params`
- `scheduled_at`
- `started_at`
- `finished_at`

### 2.7 task_run_logs

任务运行日志。

关键字段建议：

- `id`
- `task_id`
- `log_level`
- `message`
- `event_type`
- `created_at`

### 2.8 job_records

结构化岗位记录主表。

关键字段建议：

- `id`
- `workspace_id`
- `task_id`
- `source_id`
- `source_job_id`
- `job_url`
- `job_title`
- `job_category`
- `company_name`
- `city`
- `education`
- `experience_text`
- `salary_min`
- `salary_max`
- `salary_currency`
- `salary_period`
- `publish_date`
- `captured_at`
- `first_seen_at`
- `last_seen_at`
- `is_active`
- `raw_data`

### 2.9 template_test_runs

模板测试运行记录。

关键字段建议：

- `id`
- `template_version_id`
- `test_url`
- `test_status`
- `sample_result`
- `field_completeness`
- `created_at`

### 2.10 proposals

个人能力升级为共享能力的提案。

关键字段建议：

- `id`
- `workspace_id`
- `proposal_type`
- `target_id`
- `title`
- `description`
- `review_status`
- `review_comment`
- `created_at`

### 2.11 audit_logs

记录关键行为。

关键字段建议：

- `id`
- `actor_type`
- `actor_id`
- `action`
- `target_type`
- `target_id`
- `before_snapshot`
- `after_snapshot`
- `created_at`

## 3. 保留但不一定首批实现的表

- `knowledge_documents`
- `search_histories`
- `export_records`
- `agent_sessions`
- `agent_actions`

## 4. 数据设计重点

### 4.1 原始数据必须保留

无论后续如何结构化，`raw_data` 必须保留，方便：

- 回溯
- 重新解析
- 审计
- 新字段补提取

### 4.2 历史分析必须有时间字段

至少保留：

- `captured_at`
- `first_seen_at`
- `last_seen_at`
- `publish_date`

### 4.3 去重必须有稳定键

优先使用：

- `source_id + source_job_id`

没有稳定 ID 时，再退化为：

- `job_title + company_name + city + job_url`

## 5. 下一步

本草案用于确定方向，下一版应补充：

1. 表关系图
2. 字段类型
3. 索引策略
4. 迁移顺序
5. PostgreSQL / MySQL 差异方案
