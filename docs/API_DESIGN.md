# API 设计文档（V1）

## 1. 文档目标

本文档用于定义 NetWorkspace V1 的核心 API 设计，重点覆盖以下五条主链路：

1. 站点接入
2. 模板管理
3. 采集任务
4. 搜索与数据查询
5. 审核与提案

本文档的目标不是穷举所有边角接口，而是先把核心资源、状态流转、请求结构和边界约定明确下来，作为后续后端模块拆分、数据库建模和前端对接的共同依据。

## 2. 设计原则

### 2.1 REST 优先，语义清晰

- 使用资源化路径表达核心对象
- 用 HTTP Method 表达操作类型
- 避免把所有动作都塞进一个通用 `action` 接口

### 2.2 工作区优先

除系统级管理员接口外，所有核心对象都应可追溯到某个 `workspace`。

### 2.3 结构化结果优先

接口返回应面向前端直接消费，不依赖文本日志解析。

### 2.4 AI 输出必须显式标记

凡是 Agent 或多模态参与生成的结果，都应明确：

- 是否由 AI 生成
- 依据了哪些输入
- 当前置信度如何
- 是否已经过用户确认

### 2.5 审计可追踪

关键变更类操作应可关联到审计日志，尤其包括：

- 站点接入
- 模板发布
- 模板修复
- 提案提交
- 审核动作

## 3. 通用约定

### 3.1 路径前缀

V1 推荐统一使用：

```text
/api/v1
```

### 3.2 鉴权方式

V1 建议：

- 登录后签发 `JWT access token`
- 管理端与普通工作台共用鉴权体系
- 服务端按 `user -> workspace -> resource` 做权限校验

示例：

```http
Authorization: Bearer <access_token>
```

### 3.3 响应格式

建议统一为：

```json
{
  "success": true,
  "message": "ok",
  "data": {},
  "meta": {}
}
```

失败时：

```json
{
  "success": false,
  "message": "template validation failed",
  "error_code": "TEMPLATE_VALIDATION_FAILED",
  "details": {
    "missing_fields": ["job_title", "job_url"]
  }
}
```

### 3.4 分页格式

列表接口建议统一返回：

```json
{
  "success": true,
  "data": {
    "items": []
  },
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 120,
    "has_next": true
  }
}
```

### 3.5 时间与状态

- 时间统一使用 ISO 8601
- 所有长流程对象必须有明确 `status`
- 状态枚举以数据库设计文档为准

### 3.6 HTTP 状态码建议

V1 建议遵循以下约定：

- `200 OK`：同步读取或更新成功
- `201 Created`：同步创建成功
- `202 Accepted`：已接受异步处理请求
- `400 Bad Request`：请求参数不合法
- `401 Unauthorized`：未登录或 token 无效
- `403 Forbidden`：无权访问当前工作区或资源
- `404 Not Found`：目标资源不存在
- `409 Conflict`：状态冲突，例如试图发布未测试模板
- `422 Unprocessable Entity`：结构合法但业务校验失败
- `500 Internal Server Error`：服务端未预期错误

### 3.7 异步接口返回建议

对于会触发后台任务的接口，建议统一返回：

```json
{
  "success": true,
  "message": "accepted",
  "data": {
    "resource_id": 1001,
    "status": "queued",
    "job_type": "onboarding_analysis"
  }
}
```

推荐配合：

- `202 Accepted`
- 前端轮询详情接口
- 后续可扩展为 `SSE` 或 WebSocket 推送

## 4. API 模块总览

V1 推荐按以下模块拆分：

1. 认证与用户
2. 工作区
3. 站点接入
4. 模板管理
5. 采集任务
6. 搜索与数据查询
7. 提案与审核
8. 审计与辅助信息

本阶段重点详细定义第 3 至第 7 模块。

## 5. 认证与工作区基础接口

这部分不是本文重点，但为了让主链路闭环，建议至少具备以下接口。

### 5.1 认证

#### `POST /auth/login`

用途：

- 用户登录并获取访问令牌

请求体：

```json
{
  "username": "demo_user",
  "password": "******"
}
```

响应体：

```json
{
  "success": true,
  "data": {
    "access_token": "<token>",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "username": "demo_user",
      "role": "user"
    }
  }
}
```

#### `GET /auth/me`

用途：

- 获取当前用户信息与可访问工作区

### 5.2 工作区

#### `GET /workspaces`

用途：

- 获取当前用户可访问的工作区列表

#### `GET /workspaces/{workspace_id}`

用途：

- 获取工作区基础信息

#### `PATCH /workspaces/{workspace_id}`

用途：

- 更新工作区名称、描述等基础信息

## 6. 站点接入链路

站点接入链路对应“用户只提供链接，系统生成并验证模板”的工作流。

### 6.1 核心资源

- `onboarding_request`
- `onboarding_capture`
- `template_draft`
- `template_test_run`

V1 可以将 `onboarding_capture` 和 `template_draft` 作为 `onboarding_request` 的嵌套视图返回，不必单独暴露为顶层数据库表。

### 6.2 关键状态流转

建议状态：

- `submitted`
- `identified`
- `analyzing`
- `draft_generated`
- `testing`
- `awaiting_confirmation`
- `published`
- `failed`
- `abandoned`

### 6.3 创建接入请求

#### `POST /workspaces/{workspace_id}/onboarding-requests`

用途：

- 用户提交目标链接，启动智能站点接入流程

请求体：

```json
{
  "target_url": "https://example.com/jobs?keyword=data",
  "content_type_hint": "job",
  "needs_detail_page": true
}
```

响应体：

```json
{
  "success": true,
  "message": "accepted",
  "data": {
    "id": 1001,
    "workspace_id": 10,
    "target_url": "https://example.com/jobs?keyword=data",
    "status": "submitted",
    "job_type": "onboarding_analysis",
    "created_at": "2026-06-06T10:00:00+08:00"
  }
}
```

服务端动作：

1. 创建 `onboarding_request`
2. 做 URL 基础校验
3. 投递异步分析任务
4. 记录审计日志

### 6.4 获取接入请求列表

#### `GET /workspaces/{workspace_id}/onboarding-requests`

常用查询参数：

- `status`
- `page`
- `page_size`

用途：

- 工作区内查看历史接入请求

### 6.5 获取接入请求详情

#### `GET /workspaces/{workspace_id}/onboarding-requests/{request_id}`

用途：

- 查看接入请求当前状态、识别结果、AI 分析摘要、模板草稿和测试情况

建议返回结构：

```json
{
  "success": true,
  "data": {
    "id": 1001,
    "status": "awaiting_confirmation",
    "target_url": "https://example.com/jobs?keyword=data",
    "source_guess": {
      "domain": "example.com",
      "site_guess": "job_site",
      "render_mode_guess": "browser",
      "risk_flags": ["dynamic_render"]
    },
    "analysis_summary": {
      "page_type": "search_list",
      "has_pagination": true,
      "needs_detail_page": true,
      "confidence": "medium"
    },
    "draft_template": {
      "version": "draft-1",
      "generated_by": "agent",
      "confidence": "medium"
    },
    "latest_test_run": {
      "status": "passed",
      "sample_size": 5,
      "field_completeness": {
        "job_title": 1.0,
        "company_name": 0.8,
        "job_url": 1.0
      }
    }
  }
}
```

### 6.6 触发重新分析

#### `POST /workspaces/{workspace_id}/onboarding-requests/{request_id}/reanalyze`

用途：

- 当用户希望基于最新页面重新跑识别、截图、结构理解和模板草稿生成时使用

说明：

- 该接口不直接覆盖已发布模板
- 仅更新当前接入请求下的分析结果

### 6.7 手动更新接入草稿参数

#### `PATCH /workspaces/{workspace_id}/onboarding-requests/{request_id}`

可修改字段：

- `content_type_hint`
- `needs_detail_page`
- `notes`

用途：

- 在重新生成前，让用户补充最少量的结构性提示

### 6.8 触发模板测试

#### `POST /workspaces/{workspace_id}/onboarding-requests/{request_id}/test-runs`

用途：

- 基于当前模板草稿执行一次小样本测试

请求体：

```json
{
  "sample_pages": 1,
  "sample_details": 5
}
```

响应体：

```json
{
  "success": true,
  "message": "accepted",
  "data": {
    "test_run_id": 3001,
    "status": "queued"
  }
}
```

### 6.9 发布为个人模板

#### `POST /workspaces/{workspace_id}/onboarding-requests/{request_id}/publish`

用途：

- 用户确认测试结果后，将草稿发布为工作区内可用模板

请求体：

```json
{
  "template_name": "example_jobs",
  "display_name": "Example 招聘模板"
}
```

服务端动作：

1. 校验接入请求状态为 `awaiting_confirmation`
2. 创建 `templates`
3. 创建 `template_versions`
4. 建立 `published_template_id`
5. 更新接入请求状态为 `published`
6. 写入审计日志

### 6.10 放弃接入请求

#### `POST /workspaces/{workspace_id}/onboarding-requests/{request_id}/abandon`

用途：

- 用户终止当前接入流程

## 7. 模板管理链路

模板链路用于管理官方模板、个人模板以及模板版本。

### 7.1 核心资源

- `template`
- `template_version`
- `template_test_run`

### 7.2 获取模板列表

#### `GET /workspaces/{workspace_id}/templates`

常用查询参数：

- `scope`
- `status`
- `source_id`
- `keyword`
- `page`
- `page_size`

用途：

- 获取工作区可见的模板列表

说明：

- `official` 模板和当前工作区的 `personal` 模板都应返回
- 若未来支持共享模板，可在这里增加 `shared` 作用域

### 7.3 获取模板详情

#### `GET /workspaces/{workspace_id}/templates/{template_id}`

返回内容建议包括：

- 模板基础信息
- 当前版本
- 可用参数
- 最近测试结果
- 最近任务运行摘要

### 7.4 创建手动模板

#### `POST /workspaces/{workspace_id}/templates`

用途：

- 用户手动创建一个草稿模板，而不是走站点接入向导

请求体：

```json
{
  "source_id": 11,
  "template_name": "manual_example",
  "display_name": "手动模板示例",
  "dsl_content": {}
}
```

说明：

- 服务端应同时创建模板主记录和初始版本

### 7.5 更新模板基础信息

#### `PATCH /workspaces/{workspace_id}/templates/{template_id}`

可修改字段：

- `display_name`
- `status`
- `description`

### 7.6 创建模板新版本

#### `POST /workspaces/{workspace_id}/templates/{template_id}/versions`

用途：

- 基于当前模板创建新版本
- 适用于手动编辑、Agent 修复、管理员调整

请求体：

```json
{
  "dsl_content": {},
  "generation_source": "manual",
  "change_summary": "修复分页规则"
}
```

说明：

- 不直接替换历史版本
- 新版本默认可为 `draft` 或待验证状态

### 7.7 获取模板版本列表

#### `GET /workspaces/{workspace_id}/templates/{template_id}/versions`

### 7.8 获取模板版本详情

#### `GET /workspaces/{workspace_id}/templates/{template_id}/versions/{version_id}`

建议返回：

- DSL 正文
- 变更摘要
- 生成来源
- 置信度
- 关联测试结果

### 7.9 设置当前生效版本

#### `POST /workspaces/{workspace_id}/templates/{template_id}/activate-version`

请求体：

```json
{
  "version_id": 2002
}
```

用途：

- 切换当前生效版本

前置条件建议：

- 目标版本测试通过
- 当前用户对模板有修改权限

### 7.10 测试模板版本

#### `POST /workspaces/{workspace_id}/templates/{template_id}/versions/{version_id}/test-runs`

用途：

- 对指定模板版本进行样本抓取测试

### 7.11 触发模板修复建议

#### `POST /workspaces/{workspace_id}/templates/{template_id}/repair-suggestions`

用途：

- 当模板疑似失效时，由 Agent 基于最新页面给出修复版本建议

请求体：

```json
{
  "target_url": "https://example.com/jobs",
  "reason": "detail_failed"
}
```

返回：

- 一个建议中的新版本草稿
- 变更摘要
- 置信度

### 7.12 归档模板

#### `POST /workspaces/{workspace_id}/templates/{template_id}/archive`

用途：

- 归档不再使用的个人模板

## 8. 采集任务链路

任务链路负责把模板真正执行起来，并将结果落到岗位数据表。

### 8.1 核心资源

- `crawl_task`
- `task_run_log`

### 8.2 状态流转

建议任务状态：

- `draft`
- `queued`
- `running`
- `succeeded`
- `failed`
- `cancelled`

### 8.3 创建采集任务

#### `POST /workspaces/{workspace_id}/tasks`

用途：

- 用户基于某个模板创建采集任务

请求体：

```json
{
  "template_version_id": 2002,
  "task_name": "上海数据分析岗位抓取",
  "input_params": {
    "keyword": "数据分析",
    "city": "上海",
    "page": 1
  },
  "schedule_type": "manual"
}
```

服务端动作：

1. 校验模板版本可用
2. 校验参数符合 `parameter_schema`
3. 创建任务记录
4. 若为手动执行则投递队列
5. 记录审计日志

建议：

- 若 `schedule_type = manual`，返回 `202 Accepted`
- 若只是创建定时任务配置但不立即执行，可返回 `201 Created`

### 8.4 获取任务列表

#### `GET /workspaces/{workspace_id}/tasks`

常用查询参数：

- `status`
- `template_id`
- `created_by`
- `page`
- `page_size`

### 8.5 获取任务详情

#### `GET /workspaces/{workspace_id}/tasks/{task_id}`

建议返回：

- 任务基础信息
- 使用的模板与版本
- 当前状态
- 最新运行指标
- 产出记录数
- 最近日志摘要

### 8.6 获取任务运行日志

#### `GET /workspaces/{workspace_id}/tasks/{task_id}/logs`

用途：

- 查看结构化运行日志，而不是依赖文本流

建议字段：

- `log_level`
- `stage`
- `message`
- `details`
- `created_at`

### 8.7 取消任务

#### `POST /workspaces/{workspace_id}/tasks/{task_id}/cancel`

用途：

- 取消排队中或运行中的任务

### 8.8 重跑任务

#### `POST /workspaces/{workspace_id}/tasks/{task_id}/rerun`

用途：

- 复用相同模板与参数重新执行一次任务

说明：

- 建议创建新的任务实例，而不是覆盖原任务结果

### 8.9 获取任务产出摘要

#### `GET /workspaces/{workspace_id}/tasks/{task_id}/result-summary`

建议返回：

- 抓取记录数
- 去重后记录数
- 新增岗位数
- 更新岗位数
- 失败详情数

## 9. 搜索与数据查询链路

搜索链路服务于工作区中的历史数据检索、筛选、统计和可视化。

### 9.1 核心资源

- `job_record`
- `search_query`
- `aggregation_result`

### 9.2 查询岗位记录列表

#### `GET /workspaces/{workspace_id}/job-records`

常用查询参数建议：

- `keyword`
- `city`
- `education`
- `salary_min`
- `salary_max`
- `publish_date_from`
- `publish_date_to`
- `source_id`
- `task_id`
- `template_id`
- `is_active`
- `page`
- `page_size`
- `sort_by`
- `sort_order`

用途：

- 提供结构化结果列表页

### 9.3 查询岗位详情

#### `GET /workspaces/{workspace_id}/job-records/{record_id}`

建议返回：

- 标准化字段
- 原始字段摘要
- 关联来源信息
- 首次出现时间 / 最近出现时间
- 关联任务信息

### 9.4 条件搜索

#### `POST /workspaces/{workspace_id}/searches/jobs`

用途：

- 支持复杂结构化查询，避免把大量筛选条件塞进 URL

请求体示例：

```json
{
  "filters": {
    "keyword": "数据分析",
    "city": ["上海", "杭州"],
    "education": ["本科"],
    "salary_min": 150,
    "salary_period": "day"
  },
  "sort": {
    "by": "publish_date",
    "order": "desc"
  },
  "page": 1,
  "page_size": 20
}
```

### 9.5 获取筛选选项元数据

#### `GET /workspaces/{workspace_id}/searches/jobs/filter-metadata`

用途：

- 返回当前工作区可用的城市、学历、来源站点、薪资周期等筛选项

### 9.6 获取统计聚合结果

#### `POST /workspaces/{workspace_id}/analytics/jobs/aggregate`

用途：

- 返回图表所需聚合数据

请求体示例：

```json
{
  "filters": {
    "keyword": "数据分析"
  },
  "dimensions": ["city"],
  "metrics": ["count"]
}
```

可支持的典型维度：

- `city`
- `source`
- `education`
- `salary_period`
- `publish_date_by_week`

### 9.7 获取趋势分析

#### `POST /workspaces/{workspace_id}/analytics/jobs/trend`

用途：

- 面向时间序列的趋势图

请求体示例：

```json
{
  "filters": {
    "keyword": "数据分析"
  },
  "time_granularity": "week",
  "metric": "count"
}
```

### 9.8 自然语言问答入口

#### `POST /workspaces/{workspace_id}/assistant/query`

用途：

- 面向 AI 助手的自然语言查询入口

请求体：

```json
{
  "query": "近三个月上海数据分析岗位对 Python 的要求变化如何？"
}
```

返回建议：

- `interpreted_filters`
- `answer`
- `chart_suggestions`
- `evidence`

说明：

- V1 中该接口更适合作为增强层
- 结构化搜索仍是主链路

## 10. 提案与审核链路

审核链路用于把工作区中的个人能力，逐步沉淀为平台共享能力。

### 10.1 核心资源

- `proposal`
- `review_action`

### 10.2 提案类型建议

- `template_promotion`
- `shared_template_submission`
- `analysis_widget_submission`
- `rule_submission`

V1 可先聚焦：

- 个人模板提案为官方模板

### 10.3 创建提案

#### `POST /workspaces/{workspace_id}/proposals`

用途：

- 用户提交一个个人模板或其他工作区能力作为候选提案

请求体示例：

```json
{
  "proposal_type": "template_promotion",
  "template_id": 501,
  "title": "将 Example 招聘模板提交为共享模板",
  "summary": "该模板已稳定运行 20 次，覆盖字段完整率较高。"
}
```

### 10.4 获取提案列表

#### `GET /workspaces/{workspace_id}/proposals`

常用查询参数：

- `status`
- `proposal_type`
- `page`
- `page_size`

说明：

- 普通用户默认只看自己工作区相关提案
- 管理员可查看全局提案

### 10.5 获取提案详情

#### `GET /workspaces/{workspace_id}/proposals/{proposal_id}`

建议返回：

- 提案基础信息
- 提案对象摘要
- 最近运行指标
- 审核历史
- 当前状态

### 10.6 提交审核

#### `POST /workspaces/{workspace_id}/proposals/{proposal_id}/submit`

用途：

- 将草稿提案正式提交审核

### 10.7 审核提案

#### `POST /admin/proposals/{proposal_id}/review`

用途：

- 管理员或审核角色对提案执行审核动作

请求体：

```json
{
  "action": "approve",
  "comment": "模板结构清晰，测试结果稳定，可进入官方模板库。"
}
```

建议动作：

- `approve`
- `reject`
- `request_changes`

审核通过后的建议动作：

1. 若为模板提案，则复制或提升为 `official` 模板
2. 记录审核结论
3. 写入审计日志

### 10.8 撤回提案

#### `POST /workspaces/{workspace_id}/proposals/{proposal_id}/withdraw`

用途：

- 用户在审核前主动撤回提案

## 11. 审计与透明度接口

这部分不是业务主链路，但对 AI 系统非常关键。

### 11.1 获取审计日志

#### `GET /workspaces/{workspace_id}/audit-logs`

常用查询参数：

- `entity_type`
- `entity_id`
- `action_type`
- `page`
- `page_size`

用途：

- 查看工作区内模板、接入流程、任务、提案等对象的关键操作记录

### 11.2 获取对象变更时间线

#### `GET /workspaces/{workspace_id}/timeline`

用途：

- 为前端提供统一的时间线视图

### 11.3 获取 AI 依据摘要

#### `GET /workspaces/{workspace_id}/onboarding-requests/{request_id}/evidence`

用途：

- 查看某次站点接入中 AI 的主要依据

建议返回：

- 页面截图摘要
- DOM 片段摘要
- 网络补充检索来源摘要
- 置信度

## 12. 错误码建议

建议统一维护错误码表。V1 可以先覆盖以下高频错误：

- `AUTH_INVALID_CREDENTIALS`
- `AUTH_TOKEN_EXPIRED`
- `WORKSPACE_FORBIDDEN`
- `RESOURCE_NOT_FOUND`
- `ONBOARDING_INVALID_URL`
- `ONBOARDING_STATE_CONFLICT`
- `TEMPLATE_VALIDATION_FAILED`
- `TEMPLATE_VERSION_NOT_TESTED`
- `TASK_PARAMETER_INVALID`
- `TASK_STATE_CONFLICT`
- `SEARCH_FILTER_INVALID`
- `PROPOSAL_STATE_CONFLICT`
- `REVIEW_PERMISSION_DENIED`

## 13. 后端模块映射建议

为方便实现，API 路由建议与服务模块同步划分：

- `app/api/auth.py`
- `app/api/workspaces.py`
- `app/api/onboarding.py`
- `app/api/templates.py`
- `app/api/tasks.py`
- `app/api/searches.py`
- `app/api/analytics.py`
- `app/api/proposals.py`
- `app/api/admin_reviews.py`
- `app/api/audit_logs.py`

对应服务层建议：

- `services/auth_service.py`
- `services/workspace_service.py`
- `services/onboarding_service.py`
- `services/template_service.py`
- `services/task_service.py`
- `services/search_service.py`
- `services/analytics_service.py`
- `services/proposal_service.py`
- `services/review_service.py`
- `services/audit_service.py`

## 14. V1 边界

V1 不建议直接暴露：

- 任意脚本执行接口
- 无确认自动发布的 AI 模板接口
- 允许用户直接修改官方模板的接口
- 高耦合的“万能 Agent 动作接口”

## 15. 结论

NetWorkspace 的 API 设计应围绕“固定主链路 + 可审计 AI 增强 + 工作区隔离”展开。

就 V1 而言，最关键的是先把以下五条链路打通：

1. 站点接入
2. 模板管理
3. 采集任务
4. 搜索与分析
5. 提案与审核

只要这五条链路定义稳定，后续无论是前端工作台、后台服务拆分，还是 Agent 能力接入，都会清晰很多。
