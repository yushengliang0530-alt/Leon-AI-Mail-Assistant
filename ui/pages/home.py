"""V2.1 workspace home: direct, task-led entry points."""

from collections.abc import Callable
import html

import streamlit as st

from product_identity import APP_VERSION_LABEL
from ui.components import (
    TaskCard,
    render_global_header,
    render_notice_bar,
    render_section_header,
    render_task_card,
)
from ui.state import (
    open_create_workspace,
    open_explore_more,
    open_improve_workspace,
    open_reply_workspace,
)
from ui.styles import inject_workspace_home_styles


HOME_TASK_CARDS = {
    card.action: card
    for card in (
        TaskCard(
            action="reply",
            title="回复收到的邮件",
            description="理解对方要求、确认回复立场、生成专业回复并完成发送前检查。",
            icon="reply",
            action_label="开始回复",
            primary=True,
        ),
        TaskCard(
            action="create",
            title="创建商务邮件",
            description="通过引导完成一封结构清晰、可人工审核的商务邮件。",
            icon="edit_note",
            action_label="开始创建",
        ),
        TaskCard(
            action="improve",
            title="优化已有草稿",
            description="优化英文表达、商务语气和邮件结构。",
            icon="edit_note",
            action_label="开始优化",
        ),
    )
}

WORKSPACE_ACTIONS = ("create", "improve")


def render_home(
    *,
    ai_service_status: str,
    environment_label: str,
    access_protection_label: str,
    render_additional_details: Callable[[], None] | None = None,
) -> None:
    """Render direct task routing without changing workflow state rules."""
    inject_workspace_home_styles()

    with st.container(key="home__workspace"):
        render_global_header(
            version=APP_VERSION_LABEL,
            service_status=ai_service_status,
        )
        st.markdown(
            """
            <section class="la-home-hero">
              <div class="la-home-kicker">BUSINESS COMMUNICATION WORKSPACE</div>
              <h1 class="la-home-title">今天需要完成什么商务沟通？</h1>
              <p class="la-home-copy">
                选择任务，Leon AI会一步步帮助你完成。
                <span class="la-home-copy-en">Choose a task and complete it with clear, guided steps.</span>
              </p>
            </section>
            """,
            unsafe_allow_html=True,
        )

        render_section_header("核心任务", "CORE TASKS")
        render_task_card(
            card=HOME_TASK_CARDS["reply"],
            on_click=open_reply_workspace,
        )

        render_section_header("常用任务", "EVERYDAY TASKS")
        task_columns = st.columns(2)
        callbacks = {
            "create": open_create_workspace,
            "improve": open_improve_workspace,
        }
        for column, action in zip(task_columns, WORKSPACE_ACTIONS, strict=True):
            with column:
                render_task_card(
                    card=HOME_TASK_CARDS[action],
                    on_click=callbacks[action],
                )

        st.button(
            "探索更多工作流 · Explore More",
            key="home__explore_more",
            type="secondary",
            icon=":material/apps:",
            use_container_width=True,
            on_click=open_explore_more,
        )

        render_notice_bar(
            "安全提醒",
            "请勿输入密码、银行账号、证件号码、API Key 或其他敏感凭证。发送前请人工确认事实、承诺和附件。",
        )
        st.markdown(
            f"""
            <div class="la-home-status">
              <span>AI 服务：{html.escape(ai_service_status)}</span>
              <span>运行环境：{html.escape(environment_label)}</span>
              <span>测试访问保护：{html.escape(access_protection_label)}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if render_additional_details:
            with st.expander("产品说明 · About Leon AI", expanded=False):
                render_additional_details()
