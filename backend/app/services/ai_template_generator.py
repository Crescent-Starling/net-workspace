"""
AI 模板生成服务 — 接入 DeepSeek API，根据招聘网站页面内容自动生成 DSL 模板。

工作流：
1. 用户提交招聘网站 URL
2. 系统抓取页面 HTML（或接收用户上传的 HTML）
3. 将 HTML 结构 + 用户意图一同发给 DeepSeek，生成 DSL JSON
4. 返回 DSL 模板草稿，用户可编辑后保存
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 客户端初始化
# ---------------------------------------------------------------------------

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

_client: AsyncOpenAI | None = None


def get_openai_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        if not DEEPSEEK_API_KEY or DEEPSEEK_API_KEY == "YOUR_DEEPSEEK_API_KEY_HERE":
            raise RuntimeError(
                "DeepSeek API Key 未配置。请在 backend/.env 中设置 DEEPSEEK_API_KEY。"
                "获取 Key: https://platform.deepseek.com/api_keys"
            )
        _client = AsyncOpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL,
        )
    return _client


# ---------------------------------------------------------------------------
# DSL 生成 Prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """你是一个招聘网站数据采集专家。你的任务是根据用户提供的招聘网站页面 HTML 内容，生成一个符合 NetWorkspace DSL 规范的 YAML 模板。

## NetWorkspace DSL 规范

DSL 是一个 YAML/JSON 格式的声明式爬虫配置，包含以下字段：

### meta
```yaml
meta:
  name: "模板名称"
  version: "1.0"
  author: "system"
  description: "模板描述"
  scope: "official"   # official | personal | proposal
```

### entry
```yaml
entry:
  start_urls:
    - "https://example.com/jobs?page={page}"
  parameter_schema:
    page:
      type: "int"
      default: 1
```

### strategy
```yaml
strategy:
  fetch_mode: "html_list_detail"   # html_list_detail | api_json | browser
  concurrent: 1
```

### pagination
```yaml
pagination:
  type: "query_param"   # query_param | next_link | none
  param_name: "page"
  max_pages: 5
```

### list
```yaml
list:
  item_selector: "div.job-item"   # CSS selector，匹配每个岗位卡片
  fields:
    job_title:
      selector: "h3.title"
      extract: "text"
    company_name:
      selector: "span.company"
      extract: "text"
    job_url:
      selector: "a"
      extract: "attr"
      attr_name: "href"
    city:
      selector: "span.city"
      extract: "text"
    salary_text:
      selector: "span.salary"
      extract: "text"
```

### detail（可选，从列表页 URL 进入详情页补充字段）
```yaml
detail:
  enabled: false
  url_from: "job_url"
  fields:
    job_description:
      selector: "div.description"
      extract: "html"
```

### field_mapping
将列表页字段名映射为系统统一字段名：
```yaml
field_mapping:
  job_title: "job_title"
  company_name: "company_name"
  job_url: "job_url"
  city: "city"
  salary_text: "salary_text"
```

### normalization
字段标准化配置：
```yaml
normalization:
  city:
    source_field: "city"
    transforms:
      - "normalize_city"
  education:
    source_field: "education"
    transforms:
      - "normalize_education"
  salary_text:
    source_field: "salary_text"
    transforms:
      - "trim"
```

### dedup
去重配置：
```yaml
dedup:
  primary_keys:
    - "job_url"
  fallback_keys:
    - "job_title"
    - "company_name"
    - "city"
```

### validation
必填字段验证：
```yaml
validation:
  required_fields:
    - "job_title"
    - "company_name"
```

### runtime
```yaml
runtime:
  timeout_seconds: 30
  request_interval_ms: 1500
  max_retries: 3
```

## 输出要求

只输出纯 JSON（不要 markdown 代码块），严格符合上述 DSL 结构。
如果页面是 JavaScript 渲染的（内容在 script 标签或 __NEXT_DATA__ 中），fetch_mode 设为 "browser"。
如果页面返回 JSON API，fetch_mode 设为 "api_json"，并在 list 中用 JSONPath 提取。
"""

_USER_PROMPT_TEMPLATE = """请分析以下招聘网站的页面内容，生成对应的 DSL 模板。

## 网站 URL
{url}

## 页面 HTML（截取前 8000 字符）
```html
{html_snippet}
```

## 要求
1. 仔细观察 HTML 结构，找出岗位列表项的 CSS selector
2. 找出岗位标题、公司名、城市、薪资、链接等字段的 selector
3. 如果页面有分页，找出翻页方式
4. 生成完整可用的 DSL JSON
5. 在 meta 的 description 中注明哪些字段的置信度较低（high / medium / low）
"""


# ---------------------------------------------------------------------------
# 核心函数
# ---------------------------------------------------------------------------

async def generate_dsl_from_html(
    url: str,
    html: str,
    model: str = "deepseek-chat",
) -> dict[str, Any]:
    """
    根据页面 HTML 生成 DSL 模板。

    Args:
        url: 招聘网站 URL
        html: 页面 HTML 内容
        model: DeepSeek 模型名（deepseek-chat 或 deepseek-reasoner）

    Returns:
        dict: 生成的 DSL 模板字典

    Raises:
        RuntimeError: API 调用失败
    """
    client = get_openai_client()

    # 截取 HTML（避免超长输入）
    html_snippet = html[:8000] if len(html) > 8000 else html

    user_prompt = _USER_PROMPT_TEMPLATE.format(url=url, html_snippet=html_snippet)

    logger.info("正在调用 DeepSeek API 生成 DSL 模板，URL: %s", url)

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=4096,
        )
    except Exception as e:
        logger.exception("DeepSeek API 调用失败")
        raise RuntimeError(f"DeepSeek API 调用失败: {e}") from e

    content = response.choices[0].message.content or ""

    # 尝试解析 JSON（处理可能的 markdown 代码块包裹）
    content = content.strip()
    if content.startswith("```"):
        # 去掉 markdown 代码块
        lines = content.split("\n")
        lines = [l for l in lines if not l.startswith("```")]
        content = "\n".join(lines).strip()

    try:
        dsl = json.loads(content)
    except json.JSONDecodeError:
        logger.error("DeepSeek 返回内容无法解析为 JSON: %s", content[:500])
        raise RuntimeError(
            f"AI 生成的模板格式错误，无法解析为 JSON。原始返回：\n{content[:500]}"
        )

    # 补充 meta 信息
    if "meta" not in dsl:
        dsl["meta"] = {}
    dsl["meta"]["source_url"] = url
    dsl["meta"]["generated_by"] = "ai"
    dsl["meta"]["scope"] = "proposal"  # AI 生成的默认为 proposal，需人工确认

    logger.info("DSL 模板生成成功: %s", dsl.get("meta", {}).get("name", "unknown"))
    return dsl


async def generate_dsl_from_url(
    url: str,
    model: str = "deepseek-chat",
) -> dict[str, Any]:
    """
    直接根据 URL 抓取页面并生成 DSL 模板。
    先通过 httpx 抓取页面 HTML，再调用 generate_dsl_from_html。
    """
    import httpx

    logger.info("正在抓取页面: %s", url)
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    )
                },
            )
            resp.raise_for_status()
            html = resp.text
    except Exception as e:
        raise RuntimeError(f"抓取页面失败: {e}") from e

    return await generate_dsl_from_html(url, html, model)
