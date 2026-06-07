"""
DSL Executor - 解析并执行模板 DSL，驱动采集流程。

负责：
1. 解析 DSL 字典
2. 根据 strategy.fetch_mode 选择适配器
3. 执行分页循环
4. 列表页字段提取
5. 详情页补充（如启用）
6. 字段映射、标准化、去重判断
7. 将结果写入 job_records 表
"""

from __future__ import annotations

import logging
import re
import time
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_record import JobRecord
from app.spiders.adapters import FetchResult, get_adapter

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 白名单标准化函数
# ---------------------------------------------------------------------------

def _transform(value: Optional[str], transforms: list[str]) -> Optional[str]:
    """按白名单 transforms 顺序处理字段值。"""
    if value is None:
        return None
    v = str(value)
    for t in transforms:
        v = _APPLY_TRANSFORM[t](v)
    return v


def _trim(v: str) -> str:
    return v.strip()


def _normalize_space(v: str) -> str:
    return re.sub(r"\s+", " ", v).strip()


def _normalize_city(v: str) -> str:
    mapping = {
        "北京": "北京", "上海市": "上海", "上海": "上海",
        "广州市": "广州", "广州": "广州", "深圳市": "深圳", "深圳": "深圳",
        "杭州市": "杭州", "杭州": "杭州", "成都市": "成都", "成都": "成都",
        "南京市": "南京", "南京": "南京", "武汉市": "武汉", "武汉": "武汉",
        "西安市": "西安", "西安": "西安", "重庆市": "重庆", "重庆": "重庆",
    }
    for key, val in mapping.items():
        if key in v:
            return val
    return v


def _normalize_education(v: str) -> str:
    v_low = v.lower()
    if "博士" in v or "phd" in v_low or "doctor" in v_low:
        return "博士"
    if "硕士" in v or "master" in v_low:
        return "硕士"
    if "本科" in v or "bachelor" in v_low:
        return "本科"
    if "大专" in v or "专科" in v or "college" in v_low:
        return "大专"
    return v.strip()


def _parse_salary(v: str) -> str:
    """尝试将薪资文本解析为结构化字符串，如 "10000-20000 CNY/月"。"""
    return v.strip()


def _parse_salary_structured(v: str) -> dict[str, Any]:
    """解析薪资文本，返回 {salary_min, salary_max, salary_currency, salary_period}。"""
    result = {
        "salary_min": None,
        "salary_max": None,
        "salary_currency": "CNY",
        "salary_period": None,
    }
    v = v.strip()
    # 匹配 "10000-20000元/月" 或 "10k-20k/月" 或 "15K-30K"
    pattern = r"(\d+\.?\d*)\s*[kK]?\s*[-~至到]+\s*(\d+\.?\d*)\s*[kK]?"
    m = re.search(pattern, v)
    if m:
        n1, n2 = float(m.group(1)), float(m.group(2))
        # 处理 k 单位
        if "k" in v.lower():
            n1 *= 1000
            n2 *= 1000
        result["salary_min"] = Decimal(str(int(n1)))
        result["salary_max"] = Decimal(str(int(n2)))
    else:
        # 只匹配单个数字
        single = re.search(r"(\d+\.?\d*)", v)
        if single:
            n = float(single.group(1))
            if "k" in v.lower() or "K" in v:
                n *= 1000
            result["salary_min"] = Decimal(str(int(n)))
            result["salary_max"] = Decimal(str(int(n)))

    if "月" in v or "month" in v.lower():
        result["salary_period"] = "月"
    elif "年" in v or "year" in v.lower():
        result["salary_period"] = "年"
    elif "日" in v or "day" in v.lower():
        result["salary_period"] = "日"

    if "USD" in v or "$" in v:
        result["salary_currency"] = "USD"
    return result


def _parse_date(v: str) -> Optional[str]:
    return v.strip()


def _normalize_experience(v: str) -> str:
    return v.strip()


def _extract_digits(v: str) -> str:
    return re.sub(r"\D", "", v)


_APPLY_TRANSFORM = {
    "trim": _trim,
    "normalize_space": _normalize_space,
    "normalize_city": _normalize_city,
    "normalize_education": _normalize_education,
    "parse_salary": _parse_salary,
    "parse_date": _parse_date,
    "normalize_experience": _normalize_experience,
    "extract_digits": _extract_digits,
}


# ---------------------------------------------------------------------------
# 字段提取
# ---------------------------------------------------------------------------

def _extract_field(html: str, selector: str, extract: str, attr_name: Optional[str] = None) -> Optional[str]:
    """从 HTML 中用 selector + extract 方式提取值。"""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        logger.warning("BeautifulSoup not installed")
        return None

    soup = BeautifulSoup(html, "html.parser")

    if extract == "text":
        el = soup.select_one(selector)
        return el.get_text(strip=True) if el else None
    elif extract == "html":
        el = soup.select_one(selector)
        return str(el) if el else None
    elif extract == "attr":
        el = soup.select_one(selector)
        return el.get(attr_name) if el and attr_name else None
    elif extract == "exists":
        el = soup.select_one(selector)
        return "true" if el else "false"
    return None


def _extract_fields_from_html(html: str, field_defs: dict[str, dict]) -> dict[str, Optional[str]]:
    """根据 list.fields / detail.fields 定义从 HTML 提取所有字段。"""
    result: dict[str, Optional[str]] = {}
    for fname, fdef in field_defs.items():
        selector = fdef.get("selector", "")
        extract = fdef.get("extract", "text")
        attr_name = fdef.get("attr_name")
        result[fname] = _extract_field(html, selector, extract, attr_name)
    return result


# ---------------------------------------------------------------------------
# URL 补全
# ---------------------------------------------------------------------------

def _make_absolute_url(base_url: str, url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    if url.startswith("http://") or url.startswith("https://"):
        return url.split("?")[0].split("#")[0]
    # 相对路径
    from urllib.parse import urljoin
    return urljoin(base_url, url).split("?")[0].split("#")[0]


# ---------------------------------------------------------------------------
# 去重检查
# ---------------------------------------------------------------------------

async def _is_duplicate(db: AsyncSession, workspace_id: int, primary_keys: list[str],
                        record: dict, fallback_keys: list[str]) -> bool:
    """检查 job_records 中是否已存在相同记录。"""
    from sqlalchemy import select, and_

    # 优先用 primary_keys
    if "source_job_id" in primary_keys and record.get("source_job_id"):
        stmt = select(JobRecord).where(
            JobRecord.workspace_id == workspace_id,
            JobRecord.source_job_id == str(record["source_job_id"]),
        )
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            return True

    if "job_url" in primary_keys and record.get("job_url"):
        stmt = select(JobRecord).where(
            JobRecord.workspace_id == workspace_id,
            JobRecord.job_url == str(record["job_url"]),
        )
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            return True

    # fallback: job_title + company_name + city
    if fallback_keys:
        conditions = [JobRecord.workspace_id == workspace_id]
        if record.get("job_title"):
            conditions.append(JobRecord.job_title == str(record["job_title"]))
        if record.get("company_name"):
            conditions.append(JobRecord.company_name == str(record["company_name"]))
        if record.get("city"):
            conditions.append(JobRecord.city == str(record["city"]))
        if len(conditions) >= 2:
            stmt = select(JobRecord).where(and_(*conditions))
            result = await db.execute(stmt)
            if result.scalar_one_or_none():
                return True

    return False


# ---------------------------------------------------------------------------
# 核心执行器
# ---------------------------------------------------------------------------

class DSLExecutor:
    """解析 DSL 并执行完整采集流程。"""

    def __init__(self, dsl: dict[str, Any], db: AsyncSession, workspace_id: int,
                 task_id: int, source_id: int, user_id: int):
        self.dsl = dsl
        self.db = db
        self.workspace_id = workspace_id
        self.task_id = task_id
        self.source_id = source_id
        self.user_id = user_id
        self.logger = logger

    # ---- 解析 DSL 各块 ----
    def _meta(self) -> dict:
        return self.dsl.get("meta", {})

    def _entry(self) -> dict:
        return self.dsl.get("entry", {})

    def _strategy(self) -> dict:
        return self.dsl.get("strategy", {})

    def _pagination(self) -> dict:
        return self.dsl.get("pagination", {})

    def _list_block(self) -> dict:
        return self.dsl.get("list", {})

    def _detail_block(self) -> dict:
        return self.dsl.get("detail", {})

    def _field_mapping(self) -> dict:
        return self.dsl.get("field_mapping", {})

    def _normalization(self) -> dict:
        return self.dsl.get("normalization", {})

    def _dedup(self) -> dict:
        return self.dsl.get("dedup", {})

    def _validation(self) -> dict:
        return self.dsl.get("validation", {})

    def _runtime(self) -> dict:
        return self.dsl.get("runtime", {})

    # ---- 构建起始 URL ----
    def _build_start_urls(self, task_params: dict) -> list[str]:
        entry = self._entry()
        raw_urls = entry.get("start_urls", [])
        param_schema = entry.get("parameter_schema", {})
        built: list[str] = []
        for url_template in raw_urls:
            try:
                built.append(url_template.format(**task_params))
            except KeyError:
                # 未提供的参数保留原占位符，由调用方处理
                built.append(url_template)
        return built

    # ---- 分页 URL 生成 ----
    def _build_page_url(self, base_url: str, page: int) -> str:
        pag = self._pagination()
        ptype = pag.get("type", "none")
        if ptype == "query_param":
            sep = "&" if "?" in base_url else "?"
            return f"{base_url}{sep}{pag.get('param_name', 'page')}={page}"
        if ptype == "next_link":
            # 需要在抓取后从页面中提取下一页链接，这里先返回 base_url
            return base_url
        # 默认不翻页
        return base_url

    # ---- 主执行入口 ----
    async def execute(self, task_params: dict, log_callback=None) -> dict[str, Any]:
        """执行完整采集任务，返回统计信息。"""
        stats = {"total_fetched": 0, "new_records": 0, "duplicate_skipped": 0, "errors": 0}
        strategy = self._strategy()
        fetch_mode = strategy.get("fetch_mode", "html_list_detail")
        runtime = self._runtime()
        timeout = runtime.get("timeout_seconds", 30)
        interval_ms = runtime.get("request_interval_ms", 1500)
        max_pages = self._pagination().get("max_pages", 5)

        adapter = get_adapter(fetch_mode, timeout=timeout)

        start_urls = self._build_start_urls(task_params)
        if not start_urls:
            if log_callback:
                await log_callback("error", "no_start_urls", "没有可用的起始 URL")
            return stats

        current_url = start_urls[0]
        for page in range(1, max_pages + 1):
            if log_callback:
                await log_callback("info", "page_start", f"开始抓取第 {page} 页: {current_url}")

            # 1. 抓取列表页
            fetch_result: FetchResult = await adapter.fetch(current_url, timeout=timeout)
            if not fetch_result.ok:
                stats["errors"] += 1
                if log_callback:
                    await log_callback("error", "fetch_failed", f"抓取失败: {fetch_result.error}")
                break

            list_html = fetch_result.html
            list_fields_def = self._list_block().get("fields", {})
            item_selector = self._list_block().get("item_selector", "")

            # 2. 解析列表项
            items = self._parse_list_items(list_html, item_selector, list_fields_def)
            if not items:
                if log_callback:
                    await log_callback("warn", "no_items", f"第 {page} 页未识别到列表项，终止翻页")
                break

            stats["total_fetched"] += len(items)

            # 3. 处理每个列表项
            for item_idx, item in enumerate(items):
                try:
                    await self._process_item(item, task_params, log_callback, stats)
                except Exception as e:
                    stats["errors"] += 1
                    self.logger.exception("处理列表项失败")
                # 请求间隔
                if interval_ms > 0:
                    await self._async_sleep(interval_ms / 1000)

            # 4. 翻页
            if page >= max_pages:
                break
            next_url = self._build_page_url(start_urls[0], page + 1)
            # 简单判断：如果下一页 URL 和当前相同且不是 query_param 翻页，则停止
            if next_url == current_url and self._pagination().get("type") != "query_param":
                break
            current_url = next_url

        if log_callback:
            await log_callback("info", "task_complete", f"任务完成: 新增 {stats['new_records']} 条，跳过重复 {stats['duplicate_skipped']} 条")

        return stats

    async def _async_sleep(self, seconds: float):
        import asyncio
        await asyncio.sleep(seconds)

    def _parse_list_items(self, html: str, item_selector: str, field_defs: dict) -> list[dict[str, Optional[str]]]:
        """用 item_selector 找到所有列表项，从每个项中提取字段。"""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            return []
        soup = BeautifulSoup(html, "html.parser")
        item_els = soup.select(item_selector)
        items: list[dict[str, Optional[str]]] = []
        for el in item_els:
            item_html = str(el)
            fields = _extract_fields_from_html(item_html, field_defs)
            items.append(fields)
        return items

    async def _process_item(self, list_fields: dict[str, Optional[str]],
                            task_params: dict, log_callback, stats: dict):
        """处理单个列表项：字段映射、详情页补充、标准化、去重、入库。"""
        # 字段映射
        mapped = self._apply_field_mapping(list_fields)

        # 详情页补充
        detail_block = self._detail_block()
        if detail_block.get("enabled", False):
            detail_url_field = detail_block.get("url_from", "")
            detail_url = mapped.get(detail_url_field) or list_fields.get(detail_url_field)
            if detail_url:
                detail_url = _make_absolute_url("", detail_url)
                mapped = await self._fetch_detail(detail_url, detail_block, mapped)

        # 标准化
        mapped = self._apply_normalization(mapped)

        # 解析薪资结构化数据
        if mapped.get("salary_text"):
            sal = _parse_salary_structured(mapped["salary_text"])
            mapped["salary_min"] = sal["salary_min"]
            mapped["salary_max"] = sal["salary_max"]
            mapped["salary_currency"] = sal["salary_currency"]
            mapped["salary_period"] = sal["salary_period"]

        # 去重
        dedup_cfg = self._dedup()
        is_dup = await _is_duplicate(
            self.db, self.workspace_id,
            dedup_cfg.get("primary_keys", []),
            mapped,
            dedup_cfg.get("fallback_keys", []),
        )
        if is_dup:
            stats["duplicate_skipped"] += 1
            return

        # 验证
        if not self._pass_validation(mapped):
            stats["errors"] += 1
            return

        # 入库
        now = datetime.now()

        # 确保 Decimal 转为 float（JSON 序列化兼容）
        salary_min = mapped.get("salary_min")
        salary_max = mapped.get("salary_max")
        if isinstance(salary_min, Decimal):
            salary_min = float(salary_min)
        if isinstance(salary_max, Decimal):
            salary_max = float(salary_max)

        # raw_data 中的 Decimal 也要转
        raw = {**list_fields, **mapped}
        for k, v in raw.items():
            if isinstance(v, Decimal):
                raw[k] = float(v)

        record = JobRecord(
            workspace_id=self.workspace_id,
            task_id=self.task_id,
            source_id=self.source_id,
            source_job_id=mapped.get("source_job_id"),
            job_url=mapped.get("job_url", ""),
            job_title=mapped.get("job_title", ""),
            job_category=mapped.get("job_category"),
            company_name=mapped.get("company_name"),
            city=mapped.get("city"),
            education=mapped.get("education"),
            experience_text=mapped.get("experience_text"),
            salary_text=mapped.get("salary_text"),
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency=mapped.get("salary_currency"),
            salary_period=mapped.get("salary_period"),
            publish_date=None,  # 需要从 normalization 解析
            job_description=mapped.get("job_description"),
            captured_at=now,
            first_seen_at=now,
            last_seen_at=now,
            is_active=True,
            raw_data=raw,
        )
        self.db.add(record)
        stats["new_records"] += 1

    def _apply_field_mapping(self, list_fields: dict) -> dict:
        """将列表页字段名映射为系统统一字段名。"""
        mapping = self._field_mapping()
        result: dict[str, Any] = {}
        for src_field, unified_field in mapping.items():
            result[unified_field] = list_fields.get(src_field)
        return result

    def _apply_normalization(self, record: dict) -> dict:
        """对每个字段应用白名单 transforms。"""
        norm_cfg = self._normalization()
        for target_field, cfg in norm_cfg.items():
            transforms = cfg.get("transforms", [])
            if not transforms:
                continue
            current_val = record.get(target_field)
            if current_val is None:
                # 尝试从 source_field 读取
                source_field = cfg.get("source_field")
                if source_field:
                    current_val = record.get(source_field)
            record[target_field] = _transform(current_val, transforms)
        return record

    async def _fetch_detail(self, url: str, detail_block: dict, mapped: dict) -> dict:
        """抓取详情页并补充字段。"""
        runtime = self._runtime()
        timeout = runtime.get("timeout_seconds", 30)
        adapter = get_adapter("html_list_only", timeout=timeout)  # 用简单 html 适配器
        result = await adapter.fetch(url, timeout=timeout)
        if not result.ok:
            return mapped
        detail_fields_def = detail_block.get("fields", {})
        detail_fields = _extract_fields_from_html(result.html, detail_fields_def)
        # 合并到 mapped（详情页字段覆盖）
        for k, v in detail_fields.items():
            mapped[k] = v
        return mapped

    def _pass_validation(self, record: dict) -> bool:
        """检查是否满足 validation 规则。"""
        val_cfg = self._validation()
        required = val_cfg.get("required_fields", [])
        for f in required:
            if not record.get(f):
                return False
        return True
