"""V2.1 workspace home: direct, task-led entry points."""

from collections.abc import Callable
import base64
from functools import lru_cache
import html
from pathlib import Path

import streamlit as st

from product_identity import APP_VERSION_LABEL
from ui.components import (
    TaskCard,
    render_global_header,
    render_html,
    render_notice_bar,
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


@lru_cache(maxsize=1)
def _character_data() -> str:
    asset = Path(__file__).resolve().parents[2] / "previews/account-upgrade/selected-03/character-cutout.png"
    return base64.b64encode(asset.read_bytes()).decode("ascii")


def render_home(
    *,
    ai_service_status: str,
    environment_label: str,
    render_additional_details: Callable[[], None] | None = None,
) -> None:
    """Render direct task routing without changing workflow state rules."""
    inject_workspace_home_styles()
    st.html((Path(__file__).parents[1] / "public_home.css").read_text(encoding="utf-8"))

    with st.container(key="home__workspace"):
        render_global_header(
            version=APP_VERSION_LABEL,
            service_status=ai_service_status,
        )
        with st.container(key="public__welcome"):
            hero, tasks = st.columns((1.05, 1), gap="large")
            with hero:
                render_html(
                    f"""
                    <section class="la-public-hero" aria-labelledby="public-hero-title">
                      <span class="la-public-eyebrow">WORK BETTER, WRITE CLEARER</span>
                      <h1 id="public-hero-title">让英文商务沟通<br><em>更清晰。</em></h1>
                      <p>从收到邮件到写好回复，<br>把每一步交给清晰的工作流程。</p>
                      <span class="la-public-english">Professional English. Clear communication.</span>
                      <img class="la-public-character" src="data:image/png;base64,{_character_data()}"
                           alt="身穿灰蓝职业装、手持平板的静态商务人物" width="1024" height="1536">
                      <span class="la-public-signature">LEON AI · BUSINESS EMAIL WORKSPACE</span>
                    </section>
                    """
                )
            with tasks:
                with st.container(key="public__tasks"):
                    render_html(
                        '<div class="la-public-intro"><span class="la-public-eyebrow">YOUR WORKSPACE STARTS HERE</span>'
                        '<h2>今天需要完成什么商务沟通？</h2>'
                        '<p>选择任务，Leon AI 会一步步帮助你完成。</p></div>'
                    )
                    callbacks = {"reply": open_reply_workspace, "create": open_create_workspace,
                                 "improve": open_improve_workspace}
                    for action, card in HOME_TASK_CARDS.items():
                        render_task_card(card=card, on_click=callbacks[action])
                    st.button(
                        "探索更多工作流 · Explore More", key="home__explore_more",
                        type="secondary", icon=":material/apps:", use_container_width=True,
                        on_click=open_explore_more,
                    )
                    st.caption("无需登录 · 内容仅保留在当前会话，请及时复制")

        render_notice_bar(
            "安全提醒",
            "请勿输入密码、银行账号、证件号码、API Key 或其他敏感凭证。发送前请人工确认事实、承诺和附件。",
        )
        render_html(
            f"""
            <div class="la-home-status">
              <span>AI 服务：{html.escape(ai_service_status)}</span>
              <span>运行环境：{html.escape(environment_label)}</span>
              <span>V2.1 · 免登录工作台</span>
            </div>
            """
        )

        with st.expander("使用说明与公共额度", expanded=False):
            st.write("每会话每日最多 20 次实际 AI 请求，整个应用进程每日最多 200 次，以 UTC 日期计算。分析、生成、检查及格式修复分别计次，失败请求也计次。")
            st.caption("这是小规模公共用量保护，不是按人配额或硬性金额上限；应用重启会重置额度。刷新或断线可能丢失当前会话内容。本工具不会自动发送商务邮件。")

        if render_additional_details:
            with st.expander("产品说明 · About Leon AI", expanded=False):
                render_additional_details()
