# 模板 DSL 设计文档（V1）

## 1. 文档目标

本文档定义 NetWorkspace 中“站点采集模板”的声明式 DSL（Domain Specific Language）设计，用于统一描述：

1. 一个站点如何进入采集流程
2. 列表页如何识别记录
3. 详情页如何补全字段
4. 如何翻页
5. 如何进行字段映射、清洗和去重
6. AI 生成模板时允许输出什么结构

本 DSL 的目标不是允许任意编程，而是提供**足够强但可控**的声明式表达能力，支撑：

- 官方模板
- 个人模板
- Agent 生成模板草稿
- 模板版本管理
- 模板测试与回滚

## 2. 设计原则

### 2.1 声明式优先

模板描述“抓什么、从哪里抓、怎么映射”，而不是直接写采集脚本。

### 2.2 AI 可生成，人类可审阅

模板结构必须足够清晰，让 Agent 能生成草稿，也让用户和管理员能快速读懂。

### 2.3 执行器负责行为，DSL 负责定义

DSL 只定义规则，不直接包含底层执行代码。  
执行行为由 `SpiderCore` 中的模板执行器负责。

### 2.4 可验证、可版本化、可回滚

模板必须：

- 能进行小样本测试
- 能记录版本
- 能比较差异
- 能回滚到历史版本

### 2.5 默认受限，不允许任意代码执行

V1 不支持在模板中执行任意 Python / JS 代码。  
允许的转换能力应通过有限白名单函数提供。

## 3. 模板对象模型

一个完整模板由以下逻辑块组成：

1. `meta`
2. `source`
3. `entry`
4. `strategy`
5. `pagination`
6. `list`
7. `detail`
8. `field_mapping`
9. `normalization`
10. `dedup`
11. `validation`
12. `runtime`

## 4. 顶层结构

示例：

```yaml
meta:
  template_name: "shixiseng_basic"
  display_name: "实习僧基础模板"
  scope: "official"
  version: "1.0.0"
  language: "zh-CN"
  description: "用于抓取实习僧岗位列表及详情"

source:
  source_name: "实习僧"
  domain: "shixiseng.com"
  content_type: "job"

entry:
  page_type: "search_list"
  start_urls:
    - "https://www.example.com/jobs?keyword={{ keyword }}&city={{ city }}&page={{ page }}"
  parameter_schema:
    keyword:
      type: "string"
      required: true
    city:
      type: "string"
      required: false
    page:
      type: "integer"
      required: false

strategy:
  fetch_mode: "html_list_detail"
  renderer: "browser"

pagination:
  type: "query_param"
  param_name: "page"
  start: 1
  max_pages: 10

list:
  item_selector: ".job-card"
  fields:
    title:
      selector: ".job-title"
      extract: "text"
    company:
      selector: ".company-name"
      extract: "text"
    salary:
      selector: ".salary"
      extract: "text"
    detail_url:
      selector: "a.job-link"
      extract: "attr"
      attr_name: "href"

detail:
  enabled: true
  url_from: "detail_url"
  fields:
    description:
      selector: ".job-description"
      extract: "text"
    education:
      selector: ".education"
      extract: "text"
    publish_date:
      selector: ".publish-date"
      extract: "text"

field_mapping:
  title: "job_title"
  company: "company_name"
  salary: "salary_text"
  detail_url: "job_url"
  description: "job_description"
  education: "education"
  publish_date: "publish_date"

normalization:
  city:
    source_field: "city"
    transforms: ["trim", "normalize_city"]
  salary_text:
    source_field: "salary_text"
    transforms: ["trim", "parse_salary"]

dedup:
  primary_keys:
    - "source_job_id"
  fallback_keys:
    - "job_title"
    - "company_name"
    - "job_url"

validation:
  required_fields:
    - "job_title"
    - "job_url"
  min_field_completeness: 0.6

runtime:
  timeout_seconds: 30
  request_interval_ms: 1500
  retry_times: 3
```

## 5. 各模块详细定义

### 5.1 meta

用于描述模板本身。

建议字段：

- `template_name`：内部唯一名
- `display_name`：用户可见名称
- `scope`：`official` / `personal` / `proposal`
- `version`：语义化版本
- `language`：模板内容主要语言
- `description`
- `created_by`
- `tags`

### 5.2 source

用于描述站点来源。

建议字段：

- `source_name`
- `domain`
- `subdomain_pattern`
- `content_type`：`job` / `company` / `article` 等
- `site_locale`

### 5.3 entry

用于定义入口 URL 和模板参数。

建议字段：

- `page_type`
  - `homepage`
  - `search_list`
  - `category_list`
  - `detail_page`
- `start_urls`
- `parameter_schema`

`parameter_schema` 应限制模板可接受的用户参数，常见类型：

- `string`
- `integer`
- `boolean`
- `enum`
- `date`

### 5.4 strategy

定义采集策略。

建议枚举：

- `api_only`
- `html_list_only`
- `html_list_detail`
- `browser_list_only`
- `browser_list_detail`

`renderer` 建议枚举：

- `request`
- `browser`
- `auto`

### 5.5 pagination

用于定义翻页方式。

V1 建议支持：

- `none`
- `query_param`
- `next_link`
- `button_click`
- `infinite_scroll`

字段建议：

- `type`
- `param_name`
- `start`
- `max_pages`
- `next_selector`
- `button_selector`
- `scroll_limit`

### 5.6 list

定义列表页解析规则。

核心字段：

- `item_selector`
- `empty_state_selector`
- `fields`

每个字段规则建议包含：

- `selector`
- `extract`
- `attr_name`
- `default_value`
- `required`

`extract` 建议支持：

- `text`
- `html`
- `attr`
- `exists`

### 5.7 detail

定义详情页抓取规则。

字段建议：

- `enabled`
- `url_from`
- `url_template`
- `fields`

说明：

- `url_from` 表示详情页 URL 从列表结果里的哪个字段获取
- 若站点需要拼接 URL，可使用 `url_template`

### 5.8 field_mapping

用于把页面字段映射到系统统一字段。

常见统一字段：

- `job_title`
- `company_name`
- `job_url`
- `city`
- `salary_text`
- `job_description`
- `education`
- `experience_text`
- `publish_date`
- `source_job_id`

### 5.9 normalization

定义字段标准化步骤。

V1 推荐用白名单转换函数：

- `trim`
- `normalize_space`
- `normalize_city`
- `normalize_education`
- `parse_salary`
- `parse_date`
- `normalize_experience`
- `extract_digits`

设计形式建议：

```yaml
normalization:
  salary_text:
    source_field: "salary_text"
    transforms:
      - "trim"
      - "parse_salary"
```

### 5.10 dedup

定义去重规则。

建议字段：

- `primary_keys`
- `fallback_keys`
- `workspace_scope`

去重优先级建议：

1. `source_job_id`
2. `job_url`
3. `job_title + company_name + city`

### 5.11 validation

定义模板测试和发布前的验证规则。

建议字段：

- `required_fields`
- `min_items_per_page`
- `min_field_completeness`
- `allow_empty_detail`

### 5.12 runtime

定义执行时建议参数。

建议字段：

- `timeout_seconds`
- `request_interval_ms`
- `retry_times`
- `concurrency`
- `user_agent_profile`
- `respect_robots`

## 6. 支持的字段提取方式

V1 允许以下提取方式：

### 6.1 基础提取

- 文本提取
- HTML 提取
- 属性提取
- 存在性判断

### 6.2 URL 处理

- 相对路径转绝对路径
- 补全域名
- 清洗 tracking 参数

### 6.3 有限转换

允许通过白名单函数进行有限转换，不允许内嵌任意表达式引擎。

## 7. 模板状态流转

模板建议有以下状态：

- `draft`
- `testing`
- `validated`
- `active`
- `inactive`
- `archived`

说明：

- AI 生成的草稿默认进入 `draft`
- 小样本测试通过后进入 `validated`
- 用户确认后进入 `active`

## 8. AI 生成模板的边界

Agent 可以生成：

- 顶层 DSL 结构
- 列表字段选择器
- 分页规则猜测
- 详情页字段规则
- 字段映射
- 标准化建议

Agent 不应直接决定：

- 模板正式发布
- 模板是否可用于大规模生产采集
- 是否覆盖已有官方模板

## 9. 模板测试输出建议

每次测试应输出：

- 测试 URL
- 识别的记录数
- 字段完整率
- 抽样记录预览
- 错误日志
- AI 置信度

## 10. 模板版本管理建议

每次模板变更都应记录：

- `template_id`
- `version`
- `change_summary`
- `generated_by`
- `reviewed_by`
- `created_at`

版本比较应能展示：

- 新增字段
- 删除字段
- 选择器变化
- 分页变化
- 测试结果差异

## 11. V1 不支持能力

为了保持可控性，V1 不支持：

- 任意 Python 代码块
- 任意 JavaScript 片段执行
- 动态网络请求脚本注入
- 无限制表达式求值

## 12. 结论

NetWorkspace 的模板 DSL 不应是“简化版采集代码”，而应是：

- 可读
- 可审阅
- 可生成
- 可执行
- 可测试
- 可回滚

的站点采集声明协议。
