"""Leon AI V2.0 production workspace home."""

from collections.abc import Callable
from dataclasses import dataclass

import streamlit as st

from product_identity import (
    APP_NAME_EN,
    APP_NAME_ZH,
    APP_VERSION_LABEL,
)
from ui.state import (
    get_selected_home_action,
    open_legacy_improve,
    open_reply_workspace,
    open_supplier_workflow,
    set_selected_home_action,
)

@dataclass(frozen=True)
class TaskCard:
    action: str
    title: str
    description: str
    icon: str
    status: str | None = None
    primary: bool = False


HOME_TASK_CARDS = {
    card.action: card
    for card in (
        TaskCard(
            "reply",
            "回复收到的邮件",
            "识别对方要求、必须回复的问题和潜在风险，生成专业回复。",
            "reply",
            primary=True,
        ),
        TaskCard(
            "supplier",
            "催供应商",
            "催报价、催交期、更新计划或要求解释延期。",
            "local_shipping",
        ),
        TaskCard(
            "improve",
            "优化已有草稿",
            "改善语法、结构、语气和行动要求。",
            "edit_note",
        ),
    )
}

WORKSPACE_ACTIONS = ("supplier", "improve")


def render_task_card(
    *,
    card: TaskCard,
    on_click: Callable[[], None] | None = None,
) -> None:
    display_title = card.title
    if card.status:
        display_title += f"　·　{card.status}"
    st.button(
        f"**{display_title}**  \n{card.description}",
        key=f"home__action__{card.action}",
        type="primary" if card.primary else "secondary",
        icon=f":material/{card.icon}:",
        use_container_width=True,
        on_click=on_click or set_selected_home_action,
        args=() if on_click else (card.action,),
    )


def _render_selected_action() -> None:
    selected = get_selected_home_action()
    if not selected:
        return

    with st.container(key="home__action_feedback"):
        if selected == "supplier":
            st.markdown("#### 催供应商")
            st.write("通过几个业务问题生成完整的供应商跟进邮件，无需编写 Prompt。")
            st.button(
                "开始催供应商邮件",
                key="home__open_supplier_workflow",
                type="primary",
                on_click=open_supplier_workflow,
            )
        elif selected == "improve":
            st.markdown("#### 优化已有草稿")
            st.write("优化语法、结构、语气和行动要求，并保留原邮件事实。")
            st.button(
                "开始优化英文邮件",
                key="home__open_legacy_improve",
                type="primary",
                on_click=open_legacy_improve,
            )


def render_home(
    *,
    ai_service_status: str,
    environment_label: str,
    access_protection_label: str,
    render_additional_details: Callable[[], None] | None = None,
) -> None:
    st.markdown(
        """
        <style>
        .st-key-home__workspace {
            --workspace-ink:#14213d;
            --workspace-blue:#2563eb;
            --workspace-blue-dark:#1d4ed8;
            --workspace-blue-soft:#eff6ff;
            --workspace-line:#dce6f3;
            --workspace-muted:#64748b;
            overflow-x:hidden;
        }
        .st-key-home__workspace .workspace-brand {
            display:flex;
            align-items:center;
            justify-content:space-between;
            gap:1.5rem;
            margin-bottom:3rem;
        }
        .st-key-home__workspace .workspace-wordmark {
            display:flex;
            align-items:center;
            gap:.75rem;
            min-width:0;
        }
        .st-key-home__workspace .workspace-brand-copy {
            min-width:0;
        }
        .st-key-home__workspace .workspace-brand-title {
            color:var(--workspace-ink);
            font-size:1.05rem;
            font-weight:780;
            line-height:1.25;
            letter-spacing:-.015em;
        }
        .st-key-home__workspace .workspace-brand-subtitle {
            margin-top:.125rem;
            color:#7c8ba1;
            font-size:.72rem;
            font-weight:520;
            line-height:1.35;
        }
        .st-key-home__workspace .workspace-mark {
            width:2.5rem;
            height:2.5rem;
            display:grid;
            place-items:center;
            flex:0 0 2.5rem;
            border-radius:.75rem;
            background:var(--workspace-ink);
            color:#fff;
            font-family:Georgia,serif;
            font-size:.88rem;
            box-shadow:0 8px 20px rgba(20,33,61,.12);
        }
        .st-key-home__workspace .workspace-version {
            flex:none;
            padding:.375rem .75rem;
            border:1px solid var(--workspace-line);
            border-radius:999px;
            color:#52627a;
            background:#fff;
            font-size:.68rem;
            font-weight:700;
            letter-spacing:.035em;
        }
        .st-key-home__workspace .workspace-hero {
            position:relative;
            padding-left:1.5rem;
            margin-bottom:2rem;
            border-left:3px solid var(--workspace-blue);
        }
        .st-key-home__workspace .workspace-kicker {
            margin-bottom:.55rem;
            color:var(--workspace-blue);
            font-size:.7rem;
            font-weight:750;
            letter-spacing:.12em;
            text-transform:uppercase;
        }
        .st-key-home__workspace .workspace-hero h1 {
            margin:0;
            color:var(--workspace-ink);
            font-size:clamp(1.85rem,4vw,2.65rem);
            font-weight:780;
            letter-spacing:-.035em;
            line-height:1.14;
        }
        .st-key-home__workspace .workspace-product {
            margin-top:.55rem;
            color:#8290a3;
            font-size:.78rem;
            font-weight:550;
        }
        .st-key-home__workspace .workspace-question {
            margin:2rem 0 .5rem;
            color:var(--workspace-ink);
            font-size:1.45rem;
            font-weight:760;
            letter-spacing:-.025em;
        }
        .st-key-home__workspace .workspace-helper {
            margin:0 0 1.5rem;
            color:var(--workspace-muted);
            font-size:.88rem;
            line-height:1.6;
        }
        .st-key-home__workspace .workspace-section {
            display:flex;
            align-items:center;
            gap:.625rem;
            margin:2rem 0 .75rem;
            color:var(--workspace-ink);
            font-size:.82rem;
            font-weight:760;
            letter-spacing:.01em;
        }
        .st-key-home__workspace .workspace-section-line {
            width:.1875rem;
            height:1rem;
            flex:0 0 .1875rem;
            border-radius:999px;
            background:var(--workspace-blue);
        }
        .st-key-home__workspace .workspace-section-en {
            color:#8a98ab;
            font-size:.68rem;
            font-weight:540;
            letter-spacing:.075em;
        }
        .st-key-home__workspace div[data-testid="stButton"] > button {
            display:flex;
            align-items:center;
            width:100%;
            height:auto;
            min-height:8rem;
            padding:1.75rem 2rem;
            border-color:var(--workspace-line);
            border-radius:1.25rem;
            background:#fff;
            color:var(--workspace-ink);
            text-align:left;
            white-space:normal;
            line-height:1.45;
            box-shadow:0 8px 24px rgba(28,48,79,.055);
            transition:border-color .16s ease,box-shadow .16s ease,
              transform .16s ease,background .16s ease;
        }
        .st-key-home__workspace div[data-testid="stButton"] > button > div {
            width:100%;
            min-width:0;
        }
        .st-key-home__workspace div[data-testid="stButton"] > button > div > span {
            display:grid;
            grid-template-columns:4rem minmax(0,1fr) 3rem;
            align-items:center;
            column-gap:1.5rem;
            width:100%;
            min-width:0;
        }
        .st-key-home__workspace div[data-testid="stButton"] > button > div > span::after {
            content:"→";
            display:grid;
            place-items:center;
            width:2.75rem;
            height:2.75rem;
            justify-self:end;
            border-radius:999px;
            background:var(--workspace-blue-soft);
            color:var(--workspace-blue);
            font-size:1.125rem;
            font-weight:650;
            line-height:1;
        }
        .st-key-home__workspace div[data-testid="stButton"] > button
          > div > span > span:first-child {
            display:grid;
            place-items:center;
            width:4rem;
            height:4rem;
            margin:0;
            border-radius:1rem;
            background:var(--workspace-blue-soft);
            color:var(--workspace-blue);
            line-height:1;
            flex:none;
        }
        .st-key-home__workspace div[data-testid="stButton"] > button
          [data-testid="stIconMaterial"] {
            width:auto;
            height:auto;
            margin:0;
            background:transparent;
            color:inherit;
            font-size:1.625rem;
            line-height:1;
        }
        .st-key-home__workspace div[data-testid="stButton"] > button
          [data-testid="stMarkdownContainer"] {
            min-width:0;
            width:100%;
            align-self:center;
        }
        .st-key-home__workspace div[data-testid="stButton"] > button p {
            width:100%;
            margin:0;
            text-align:left;
            color:var(--workspace-muted);
            font-size:.82rem;
            line-height:1.55;
        }
        .st-key-home__workspace div[data-testid="stButton"] > button p strong {
            display:block;
            margin-bottom:.5rem;
            color:var(--workspace-ink);
            font-size:1rem;
            font-weight:760;
            line-height:1.35;
        }
        .st-key-home__workspace div[data-testid="stButton"] > button p br {
            display:none;
        }
        .st-key-home__workspace div[data-testid="stButton"] > button:hover {
            border-color:#a9bde0;
            background:#fbfdff;
            color:var(--workspace-ink);
            transform:translateY(-1px);
            box-shadow:0 12px 28px rgba(28,48,79,.08);
        }
        .st-key-home__workspace div[data-testid="stButton"] > button:focus-visible {
            outline:3px solid rgba(40,88,199,.24);
            outline-offset:2px;
            border-color:var(--workspace-blue);
        }
        .st-key-home__workspace div[data-testid="stButton"] > button:active {
            transform:translateY(0);
            box-shadow:0 3px 12px rgba(28,48,79,.08);
        }
        .st-key-home__workspace .st-key-home__action__reply button {
            min-height:8.25rem;
            padding:2rem 2.5rem;
            border-color:var(--workspace-blue) !important;
            border-radius:1.25rem;
            background:var(--workspace-blue) !important;
            color:#fff !important;
            box-shadow:0 16px 34px rgba(37,99,235,.2) !important;
        }
        .st-key-home__workspace .st-key-home__action__reply button
          > div > span > span:first-child {
            background:rgba(255,255,255,.16);
            color:#fff;
        }
        .st-key-home__workspace .st-key-home__action__reply button p strong {
            color:#fff !important;
            font-size:1.08rem;
        }
        .st-key-home__workspace .st-key-home__action__reply button p {
            color:rgba(255,255,255,.88) !important;
        }
        .st-key-home__workspace .st-key-home__action__reply button
          > div > span::after {
            background:rgba(255,255,255,.17);
            color:#fff;
        }
        .st-key-home__workspace .st-key-home__action__reply button:hover {
            border-color:var(--workspace-blue-dark) !important;
            background:var(--workspace-blue-dark) !important;
        }
        .st-key-home__workspace .st-key-home__action__supplier button,
        .st-key-home__workspace .st-key-home__action__improve button {
            min-height:8rem;
            padding:1.75rem 2rem;
            background:#fff;
        }
        .st-key-home__workspace .workspace-footer {
            display:grid;
            grid-template-columns:2.75rem minmax(0,1fr) auto;
            align-items:center;
            gap:1rem;
            margin-top:2.5rem;
            padding:1.25rem 1.5rem;
            border:1px solid var(--workspace-line);
            border-radius:1rem;
            background:#f4f8fd;
            color:var(--workspace-muted);
            font-size:.78rem;
            line-height:1.65;
        }
        .st-key-home__workspace .workspace-security-icon {
            width:2.75rem;
            height:2.75rem;
            display:grid;
            place-items:center;
            border-radius:.75rem;
            background:#fff;
            color:var(--workspace-blue);
            box-shadow:0 4px 14px rgba(37,99,235,.08);
        }
        .st-key-home__workspace .workspace-security-icon svg {
            width:1.35rem;
            height:1.35rem;
        }
        .st-key-home__workspace .workspace-security-copy strong {
            color:var(--workspace-ink);
            font-weight:750;
        }
        .st-key-home__workspace .workspace-security-link {
            color:var(--workspace-blue);
            font-size:.75rem;
            font-weight:700;
            white-space:nowrap;
        }
        .st-key-home__workspace .workspace-status {
            display:flex;
            flex-wrap:wrap;
            gap:.375rem 1rem;
            margin-top:.5rem;
            color:#8290a3;
            font-size:.68rem;
        }
        @media (max-width:640px) {
            .st-key-home__workspace {
                overflow-x:hidden;
            }
            .st-key-home__workspace .workspace-brand {
                align-items:flex-start;
                margin-bottom:2rem;
            }
            .st-key-home__workspace .workspace-version {
                padding:.25rem .5rem;
                font-size:.62rem;
            }
            .st-key-home__workspace .workspace-question {
                margin-top:1.5rem;
                font-size:1.25rem;
            }
            .st-key-home__workspace div[data-testid="stHorizontalBlock"] {
                flex-direction:column;
                gap:.55rem;
            }
            .st-key-home__workspace div[data-testid="column"] {
                width:100% !important;
                flex:1 1 100% !important;
            }
            .st-key-home__workspace div[data-testid="stButton"] > button {
                height:auto;
                min-height:6.5rem;
                padding:1rem;
                border-radius:1rem;
            }
            .st-key-home__workspace div[data-testid="stButton"] > button > div > span {
                grid-template-columns:3rem minmax(0,1fr) 2.75rem;
                column-gap:1rem;
            }
            .st-key-home__workspace div[data-testid="stButton"] > button
              > div > span > span:first-child {
                width:3rem;
                height:3rem;
                border-radius:.75rem;
            }
            .st-key-home__workspace div[data-testid="stButton"] > button
              [data-testid="stIconMaterial"] {
                font-size:1.25rem;
            }
            .st-key-home__workspace div[data-testid="stButton"] > button
              > div > span::after {
                width:2.5rem;
                height:2.5rem;
            }
            .st-key-home__workspace div[data-testid="stButton"] > button p,
            .st-key-home__workspace .st-key-home__action__supplier button p,
            .st-key-home__workspace .st-key-home__action__improve button p {
                min-height:0;
            }
            .st-key-home__workspace div[data-testid="stButton"] > button p strong,
            .st-key-home__workspace .st-key-home__action__supplier button p strong,
            .st-key-home__workspace .st-key-home__action__improve button p strong {
                min-height:0;
            }
            .st-key-home__workspace .st-key-home__action__reply button,
            .st-key-home__workspace .st-key-home__action__supplier button,
            .st-key-home__workspace .st-key-home__action__improve button {
                height:auto;
                min-height:6.5rem;
                padding:1rem;
            }
            .st-key-home__workspace .workspace-footer {
                grid-template-columns:2.75rem minmax(0,1fr);
                gap:.75rem 1rem;
                padding:1rem;
            }
            .st-key-home__workspace .workspace-security-link {
                grid-column:2;
                white-space:normal;
            }
        }
        @media (prefers-reduced-motion:reduce) {
            .st-key-home__workspace div[data-testid="stButton"] > button {
                transition:none;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.container(key="home__workspace"):
        st.markdown(
            f"""
            <div class="workspace-brand">
                <div class="workspace-wordmark">
                    <span class="workspace-mark">LA</span>
                    <div class="workspace-brand-copy">
                        <div class="workspace-brand-title">Leon AI Copilot</div>
                        <div class="workspace-brand-subtitle">Business Communication Copilot</div>
                    </div>
                </div>
                <span class="workspace-version">{APP_VERSION_LABEL}</span>
            </div>
            <div class="workspace-hero">
                <div class="workspace-kicker">BUSINESS EMAIL WORKSPACE</div>
                <h1>{APP_NAME_ZH}</h1>
                <div class="workspace-product">{APP_NAME_EN}</div>
            </div>
            <div class="workspace-question">Hi.<br>今天有什么商务沟通需要完成？</div>
            <p class="workspace-helper">不用写复杂 Prompt，选择任务并填写必要事实即可完成商务邮件。</p>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="workspace-section">
                <span class="workspace-section-line"></span>
                <span>主要任务</span>
                <span class="workspace-section-en">PRIMARY WORKFLOW</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_task_card(
            card=HOME_TASK_CARDS["reply"],
            on_click=open_reply_workspace,
        )

        st.markdown(
            """
            <div class="workspace-section">
                <span class="workspace-section-line"></span>
                <span>常用任务</span>
                <span class="workspace-section-en">EVERYDAY TASKS</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        tool_columns = st.columns(2)
        for column, action in zip(
            tool_columns,
            WORKSPACE_ACTIONS,
            strict=True,
        ):
            with column:
                render_task_card(card=HOME_TASK_CARDS[action])

        _render_selected_action()

        if render_additional_details:
            with st.expander("产品说明 · About Leon AI"):
                render_additional_details()

        st.markdown(
            f"""
            <div class="workspace-footer">
                <div class="workspace-security-icon" aria-hidden="true">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                      stroke-width="1.8" stroke-linecap="round"
                      stroke-linejoin="round">
                        <path d="M12 3 5 6v5c0 4.6 2.8 8.2 7 10 4.2-1.8 7-5.4 7-10V6l-7-3Z"/>
                        <path d="m9 12 2 2 4-4"/>
                    </svg>
                </div>
                <div class="workspace-security-copy">
                    <strong>安全提醒</strong>：请勿输入密码、银行账号、证件号码、API Key 或其他敏感凭证。<br>
                    AI 生成和检查结果仅供辅助，发送前请人工确认事实、承诺和附件。
                    <div class="workspace-status">
                        <span>AI 服务：{ai_service_status}</span>
                        <span>运行环境：{environment_label}</span>
                        <span>测试访问保护：{access_protection_label}</span>
                    </div>
                </div>
                <span class="workspace-security-link">隐私与数据安全 →</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
