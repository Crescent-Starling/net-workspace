"""Streamlit 前端入口 — NetWorkspace 个人招聘情报工作台。"""

import os
import sys
import urllib.request
import urllib.parse
import json

import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------------------------------------------------------------
# 基础配置
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="NetWorkspace",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_BASE = os.getenv("NWS_API_URL", "http://localhost:8000/api/v1")

# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def api_fetch(path: str, method: str = "GET", body: dict | None = None,
              token: str | None = None) -> dict:
    """最简 HTTP 客户端，不依赖 requests。"""
    url = f"{API_BASE}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": True, "message": json.loads(e.read()).get("detail", str(e))}


def login_sidebar():
    """侧边栏登录。"""
    with st.sidebar:
        st.title("🔎 NetWorkspace")
        if "token" not in st.session_state:
            st.session_state.token = None

        if not st.session_state.token:
            with st.form("login_form"):
                username = st.text_input("用户名（邮箱）")
                password = st.text_input("密码", type="password")
                if st.form_submit_button("登录"):
                    resp = api_fetch("/auth/login", "POST", {
                        "username": username, "password": password,
                    })
                    if "access_token" in resp:
                        st.session_state.token = resp["access_token"]
                        st.rerun()
                    else:
                        st.error(resp.get("message", "登录失败"))
            st.stop()
        else:
            st.success("已登录")
            if st.button("退出"):
                st.session_state.token = None
                st.rerun()
            return st.session_state.token


# ---------------------------------------------------------------------------
# 页面
# ---------------------------------------------------------------------------

def page_dashboard(token: str):
    """数据看板 — 岗位统计 + 可视化。"""
    st.title("📊 数据看板")

    # 1. 统计卡片
    # 需要 API 支持 /job_records/stats，这里先用 /job_records 列表代替
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("总岗位数", "?")
    with col2:
        st.metric("活跃岗位", "?")
    with col3:
        st.metric("本周期新增", "?")
    with col4:
        st.metric("覆盖城市", "?")

    # 2. 图表区（占位，真正跑通后端后再绑定数据）
    st.subheader("岗位分布")
    c1, c2 = st.columns(2)
    with c1:
        st.caption("城市分布（示例）")
        example_df = pd.DataFrame({
            "city": ["北京", "上海", "广州", "深圳", "杭州"],
            "count": [120, 95, 60, 80, 45],
        })
        fig = px.bar(example_df, x="city", y="count", color="count")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.caption("薪资分布（示例）")
        example_df2 = pd.DataFrame({
            "salary_range": ["5-10K", "10-15K", "15-25K", "25K+"],
            "count": [80, 120, 90, 40],
        })
        fig2 = px.pie(example_df2, names="salary_range", values="count")
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("最近抓取记录")
    st.info("💡 任务执行后，这里会显示最新抓取的岗位记录。")


def page_job_records(token: str):
    """岗位记录浏览与搜索。"""
    st.title("📋 岗位记录")

    # 搜索栏
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        keyword = st.text_input("关键词搜索", placeholder="职位名 / 公司名")
    with col2:
        city = st.text_input("城市", placeholder="如：北京")
    with col3:
        st.write("")
        search_clicked = st.button("搜索", use_container_width=True)

    # 调用 API（需要后端实现 GET /job_records）
    # 目前先显示占位
    st.info("📡 等待后端实现 GET /api/v1/job_records 接口后，此处将展示真实数据。")

    # 示例表格
    example_df = pd.DataFrame([
        {"职位": "Python 后端开发", "公司": "某某科技", "城市": "北京", "薪资": "20-30K·13薪"},
        {"职位": "数据分析师", "公司": "某某金融", "城市": "上海", "薪资": "15-25K·14薪"},
    ])
    st.dataframe(example_df, use_container_width=True)


def page_templates(token: str):
    """DSL 模板管理。"""
    st.title("📝 采集模板")

    tab1, tab2 = st.tabs(["我的模板", "官方模板"])

    with tab1:
        st.subheader("个人工作区模板")
        resp = api_fetch("/templates?template_scope=personal", token=token)
        if isinstance(resp, dict) and "data" in resp:
            templates = resp["data"]
            if templates:
                for t in templates:
                    with st.expander(f"{t.get('display_name', t.get('template_name'))}"):
                        st.json(t)
            else:
                st.info("暂无个人模板，可以创建一个。")
        else:
            st.warning("获取模板列表失败，请确认后端已启动。")

        with st.expander("➕ 创建新模板（YAML）"):
            yaml_text = st.text_area("DSL YAML", height=300,
                                    placeholder="在这里粘贴 DSL YAML 定义…")
            if st.button("保存模板"):
                # 把 YAML 转 dict，再 POST /templates
                try:
                    import yaml
                    dsl_dict = yaml.safe_load(yaml_text)
                    resp2 = api_fetch("/templates", "POST", {
                        "source_id": 1,
                        "template_name": dsl_dict.get("meta", {}).get("template_name", "my_template"),
                        "display_name": dsl_dict.get("meta", {}).get("display_name", "我的模板"),
                        "template_scope": "personal",
                        "dsl_content": dsl_dict,
                    }, token=token)
                    if "data" in resp2:
                        st.success("模板创建成功！")
                        st.rerun()
                    else:
                        st.error(f"创建失败：{resp2.get('message', '未知错误')}")
                except Exception as e:
                    st.error(f"YAML 解析失败：{e}")

    with tab2:
        st.subheader("官方模板")
        resp = api_fetch("/templates?template_scope=official", token=token)
        if isinstance(resp, dict) and "data" in resp:
            for t in resp["data"]:
                st.write(f"• {t.get('display_name', t.get('template_name'))}")
        else:
            st.warning("获取官方模板失败。")


def page_tasks(token: str):
    """任务管理 — 创建/查看/触发执行。"""
    st.title("🚀 采集任务")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("创建任务")
        with st.form("create_task_form"):
            task_name = st.text_input("任务名称")
            template_id = st.number_input("模板 ID", min_value=1, value=1)
            keyword = st.text_input("搜索关键词（可选）")
            city = st.text_input("城市（可选）")
            if st.form_submit_button("创建任务"):
                params = {}
                if keyword:
                    params["keyword"] = keyword
                if city:
                    params["city"] = city
                resp = api_fetch("/tasks", "POST", {
                    "template_version_id": 1,  # 简化：直接取 version=1
                    "task_name": task_name,
                    "task_params": params,
                }, token=token)
                if "data" in resp:
                    st.success(f"任务已创建，ID={resp['data'].get('id')}")
                    st.rerun()
                else:
                    st.error(f"创建失败：{resp.get('message', '未知错误')}")

    with col2:
        st.subheader("任务列表")
        resp = api_fetch("/tasks?workspace_id=1", token=token)
        if isinstance(resp, dict) and "data" in resp:
            tasks = resp["data"]
            if not tasks:
                st.info("暂无任务，请在左侧创建第一个任务。")
            for t in tasks:
                status_color = {"running": "🟡", "completed": "🟢", "failed": "🔴", "draft": "⚪"}.get(t.get("task_status"), "⚪")
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.write(f"{status_color} **{t.get('task_name')}** — {t.get('task_status')}")
                    st.caption(f"ID: {t.get('id')} | 记录数：{t.get('total_records', 0)}")
                with col_b:
                    if t.get("task_status") == "draft":
                        if st.button("▶ 执行", key=f"exec_{t['id']}"):
                            resp2 = api_fetch(f"/tasks/{t['id']}/execute", "POST", body=None, token=token)
                            if "data" in resp2:
                                st.success("执行已启动！")
                                st.rerun()
                            else:
                                st.error(f"启动失败：{resp2.get('message', '')}")
        else:
            st.warning("获取任务列表失败，请确认后端已启动。")


# ---------------------------------------------------------------------------
# 主程序
# ---------------------------------------------------------------------------

def main():
    token = login_sidebar()

    if not token:
        return

    # 侧边栏导航
    with st.sidebar:
        page = st.radio(
            "导航",
            ["📊 数据看板", "📋 岗位记录", "📝 采集模板", "🚀 采集任务"],
        )

    if page == "📊 数据看板":
        page_dashboard(token)
    elif page == "📋 岗位记录":
        page_job_records(token)
    elif page == "📝 采集模板":
        page_templates(token)
    elif page == "🚀 采集任务":
        page_tasks(token)


if __name__ == "__main__":
    main()
