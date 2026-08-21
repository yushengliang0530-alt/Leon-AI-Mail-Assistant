"""Secondary task catalog for the V2.1 workspace home."""

from collections.abc import Callable
import html

import streamlit as st

from product_identity import APP_VERSION_LABEL
from ui.components import render_global_header, render_html, render_page_header


CATALOG_ITEMS = (
    {
        "key": "supplier",
        "title": "供应商沟通",
        "subtitle": "Supplier Communication",
        "description": "通过引导式流程完成催交期、催计划和延期说明等供应商邮件。",
        "icon": "local_shipping",
        "available": True,
    },
    {
        "key": "meeting",
        "title": "会议助手",
        "subtitle": "Meeting Assistant",
        "description": "准备会议邀请、行动项确认和后续沟通。",
        "icon": "calendar_month",
        "available": False,
    },
    {
        "key": "report",
        "title": "项目汇报",
        "subtitle": "Project Report",
        "description": "整理项目进展、风险和需要管理层关注的事项。",
        "icon": "summarize",
        "available": False,
    },
    {
        "key": "approval",
        "title": "审批助手",
        "subtitle": "Approval Assistant",
        "description": "准备清晰的审批请求、背景说明和所需决定。",
        "icon": "fact_check",
        "available": False,
    },
)


def render_explore_more(
    *,
    service_status: str,
    on_return_home: Callable[[], None],
    on_open_supplier: Callable[[], None],
) -> None:
    """Render a catalog only; unfinished capabilities remain non-interactive."""
    with st.container(key="explore__catalog"):
        render_global_header(
            version=APP_VERSION_LABEL,
            service_status=service_status,
        )
        st.button(
            "← 返回工作台",
            key="explore__return_home",
            type="secondary",
            on_click=on_return_home,
        )
        render_page_header(
            icon="grid_view",
            title="探索更多工作流",
            description="Explore More · 这里汇集适合后续扩展的商务沟通任务。",
            eyebrow="LEON AI · EXPLORE MORE",
        )
        for item in CATALOG_ITEMS:
            if item["available"]:
                st.button(
                    f"**{item['title']}**  \n{item['description']}",
                    key=f"explore__open__{item['key']}",
                    icon=f":material/{item['icon']}:",
                    type="secondary",
                    use_container_width=True,
                    on_click=on_open_supplier,
                )
            else:
                render_html(
                    f"""
                    <article class="la-explore-card" aria-label="{html.escape(item['title'])}">
                      <div>
                        <strong>{html.escape(item['title'])}</strong>
                        <small>{html.escape(item['subtitle'])}</small>
                        <p>{html.escape(item['description'])}</p>
                      </div>
                      <span class="la-explore-card__status">规划中</span>
                    </article>
                    """
                )
