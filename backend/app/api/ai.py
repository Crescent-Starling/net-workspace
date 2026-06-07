"""
AI 辅助站点接入 API — 调用 DeepSeek 生成 DSL 模板。

端点：
- POST /api/v1/ai/generate-template  根据 URL 或 HTML 生成 DSL 模板
- POST /api/v1/ai/refine-template    根据反馈优化已有 DSL 模板
"""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.services.ai_template_generator import (
    generate_dsl_from_html,
    generate_dsl_from_url,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])


# ---------------------------------------------------------------------------
# Request / Response Schemas
# ---------------------------------------------------------------------------

class GenerateTemplateRequest(BaseModel):
    """请求：根据 URL 生成 DSL 模板。"""
    url: str
    model: str = "deepseek-chat"
    html: str | None = None  # 可选：直接上传 HTML，跳过抓取步骤


class RefineTemplateRequest(BaseModel):
    """请求：根据反馈优化已有 DSL 模板。"""
    dsl: dict[str, Any]
    feedback: str
    model: str = "deepseek-chat"


class GenerateTemplateResponse(BaseModel):
    """响应：生成的 DSL 模板。"""
    ok: bool
    dsl: dict[str, Any] | None = None
    error: str | None = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/generate-template", response_model=GenerateTemplateResponse)
async def generate_template(
    body: GenerateTemplateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    根据招聘网站 URL（或上传的 HTML）调用 DeepSeek 生成 DSL 模板。

    流程：
    1. 如果提供了 html 字段，直接使用
    2. 否则用 httpx 抓取 url 的页面内容
    3. 调用 DeepSeek API 生成 DSL JSON
    4. 返回 DSL 模板草稿（scope=proposal，需人工确认后保存）
    """
    try:
        if body.html:
            logger.info("使用用户上传的 HTML 生成模板，长度: %d", len(body.html))
            dsl = await generate_dsl_from_html(body.url, body.html, model=body.model)
        else:
            logger.info("抓取 URL 并生成模板: %s", body.url)
            dsl = await generate_dsl_from_url(body.url, model=body.model)
        return GenerateTemplateResponse(ok=True, dsl=dsl)
    except RuntimeError as e:
        logger.warning("模板生成失败: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.exception("模板生成异常")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"模板生成失败: {e}",
        ) from e


@router.post("/refine-template", response_model=GenerateTemplateResponse)
async def refine_template(
    body: RefineTemplateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    根据人工反馈优化已有 DSL 模板。

    将已有 DSL + 用户反馈（如"城市字段选错了 selector"）
    发给 DeepSeek，返回修正后的 DSL。
    """
    try:
        from app.services.ai_template_generator import get_openai_client

        client = get_openai_client()

        prompt = f"""已有 DSL 模板：
```json
{json.dumps(body.dsl, ensure_ascii=False, indent=2)}
```

用户反馈：
{body.feedback}

请根据用户反馈修正 DSL 模板，只输出修正后的完整 JSON，不要加解释。"""

        response = await client.chat.completions.create(
            model=body.model,
            messages=[
                {"role": "system", "content": "你是招聘网站数据采集专家，负责修正 DSL 模板配置。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=4096,
        )

        content = response.choices[0].message.content or ""
        content = content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            lines = [l for l in lines if not l.startswith("```")]
            content = "\n".join(lines).strip()

        import json
        dsl = json.loads(content)
        return GenerateTemplateResponse(ok=True, dsl=dsl)

    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.exception("模板优化异常")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"模板优化失败: {e}",
        ) from e
