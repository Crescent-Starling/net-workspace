"""爬虫适配器模块。

根据 DSL strategy.fetch_mode 提供不同的抓取实现：
- api: 直接调用 HTTP API 并解析 JSON
- html_list_only / html_list_detail: httpx + BeautifulSoup
- browser_*: Playwright（预留接口，V1 未安装时降级为 httpx 模式）

所有适配器返回统一的 FetchResult。
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class FetchResult:
    """统一抓取结果。"""

    def __init__(self, ok: bool, html: str = "", json_data: Any = None, error: str = ""):
        self.ok = ok
        self.html = html
        self.json_data = json_data
        self.error = error


class BaseAdapter:
    """适配器基类。"""

    def __init__(self, timeout: int = 30):
        self._client = httpx.AsyncClient(
            headers={"User-Agent": "Mozilla/5.0 (compatible; NetWorkspace/1.0)"},
            timeout=httpx.Timeout(timeout),
            follow_redirects=True,
        )

    async def fetch(self, url: str, **kwargs) -> FetchResult:
        raise NotImplementedError


class RequestsAdapter(BaseAdapter):
    """用 httpx + BeautifulSoup 抓取 HTML 页面。"""

    async def fetch(self, url: str, **kwargs) -> FetchResult:
        # 支持 file:// 协议（本地开发测试用）
        if url.startswith("file://"):
            try:
                from urllib.request import url2pathname
                filepath = url2pathname(url[7:])  # 去掉 "file://"
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                return FetchResult(ok=True, html=content)
            except Exception as e:
                logger.warning("RequestsAdapter file:// fetch failed: %s", e)
                return FetchResult(ok=False, error=str(e))
        try:
            resp = await self._client.get(url)
            resp.raise_for_status()
            return FetchResult(ok=True, html=resp.text)
        except Exception as e:
            logger.warning("RequestsAdapter fetch failed: %s", e)
            return FetchResult(ok=False, error=str(e))


class ApiAdapter(BaseAdapter):
    """直接调用 API 并解析 JSON 响应。"""

    async def fetch(self, url: str, **kwargs) -> FetchResult:
        try:
            resp = await self._client.get(url)
            resp.raise_for_status()
            return FetchResult(ok=True, json_data=resp.json(), html=resp.text)
        except Exception as e:
            logger.warning("ApiAdapter fetch failed: %s", e)
            return FetchResult(ok=False, error=str(e))


class BrowserAdapter(BaseAdapter):
    """Playwright 浏览器适配器（V1 预留）。

    如果 playwright 未安装，降级为 RequestsAdapter。
    """

    def __init__(self, timeout: int = 30):
        super().__init__(timeout)
        self._fallback = RequestsAdapter(timeout=timeout)
        self._playwright_available = False
        try:
            import playwright  # noqa: F401
            self._playwright_available = True
        except ImportError:
            logger.warning("Playwright not installed, BrowserAdapter will use fallback (httpx)")

    async def fetch(self, url: str, **kwargs) -> FetchResult:
        if not self._playwright_available:
            return await self._fallback.fetch(url, **kwargs)
        # V1: Playwright 逻辑待实现
        return await self._fallback.fetch(url, **kwargs)


def get_adapter(fetch_mode: str, timeout: int = 30) -> BaseAdapter:
    """根据 fetch_mode 返回对应适配器实例。"""
    mode = fetch_mode.lower()
    if "api" in mode:
        return ApiAdapter(timeout=timeout)
    if "browser" in mode:
        return BrowserAdapter(timeout=timeout)
    # 默认：html
    return RequestsAdapter(timeout=timeout)
