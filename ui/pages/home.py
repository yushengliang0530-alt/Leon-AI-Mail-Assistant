"""Leon AI V2.0 workspace home prototype."""

from collections.abc import Callable

import streamlit as st

from config import APP_BRAND, APP_NAME_EN, APP_NAME_ZH
from ui.state import (
    get_selected_home_action,
    open_legacy_improve,
    set_selected_home_action,
)


PHASE_2_ACTIONS = {
    "supplier",
    "meeting",
    "progress",
    "approval",
    "schedule",
}


def _action_button(
    *,
    action: str,
    title: str,
    description: str,
    prominent: bool = False,
) -> None:
    st.button(
        f"**{title}**  \n{description}",
        key=f"home__action__{action}",
        type="primary" if prominent else "secondary",
        use_container_width=True,
        on_click=set_selected_home_action,
        args=(action,),
    )


def _render_selected_action() -> None:
    selected = get_selected_home_action()
    if not selected:
        return

    with st.container(key="home__action_feedback"):
        if selected == "reply":
            st.markdown("#### 回复收到的邮件")
            st.info("智能回复工作流将在 Phase 3 启用。")
        elif selected in PHASE_2_ACTIONS:
            st.markdown("#### 场景化写新邮件")
            st.info(
                "场景化邮件流程将在 Phase 2 启用。"
                "当前阶段仅展示工作台首页原型。"
            )
        elif selected == "preflight":
            st.markdown("#### 发送前检查")
            st.info("独立发送前检查将在 Phase 4 启用。")
        elif selected == "scenarios":
            st.markdown("#### 更多场景")
            columns = st.columns(3)
            for column, title, items in zip(
                columns,
                ("采购与供应商", "项目与工程", "行政与管理"),
                (
                    "催报价 · 催交期 · PO确认",
                    "技术澄清 · 风险升级 · 文件审批",
                    "会议安排 · 请求审批 · 客户来访",
                ),
                strict=True,
            ):
                with column:
                    st.markdown(f"**{title}**")
                    st.caption(items)
            st.caption("完整场景化表单将在 Phase 2 开始逐步启用。")
        elif selected == "improve":
            st.markdown("#### 优化已有草稿")
            st.write("现有 V1.0 草稿优化功能继续可用。")
            st.button(
                "进入 V1.0 草稿优化",
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
            --workspace-ink: #13223a;
            --workspace-blue: #2858c7;
            --workspace-blue-soft: #eef3ff;
            --workspace-line: #d9e1ec;
            --workspace-muted: #66758a;
        }
        .st-key-home__workspace .workspace-brand {
            display:flex;
            align-items:center;
            justify-content:space-between;
            gap:1rem;
            margin-bottom:2.65rem;
        }
        .st-key-home__workspace .workspace-wordmark {
            display:flex;
            align-items:center;
            gap:.7rem;
            color:var(--workspace-ink);
            font-size:1rem;
            font-weight:750;
        }
        .st-key-home__workspace .workspace-mark {
            width:2rem;
            height:2rem;
            display:grid;
            place-items:center;
            border-radius:.5rem;
            background:var(--workspace-ink);
            color:#fff;
            font-family:Georgia,serif;
            font-size:.9rem;
            box-shadow:0 8px 20px rgba(19,34,58,.16);
        }
        .st-key-home__workspace .workspace-version {
            padding:.3rem .58rem;
            border:1px solid #c7d3e6;
            border-radius:999px;
            color:#425978;
            background:#f8faff;
            font-size:.68rem;
            font-weight:700;
            letter-spacing:.035em;
        }
        .st-key-home__workspace .workspace-hero {
            position:relative;
            padding-left:1.35rem;
            margin-bottom:2.25rem;
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
            margin:2.35rem 0 .35rem;
            color:var(--workspace-ink);
            font-size:1.42rem;
            font-weight:760;
            letter-spacing:-.025em;
        }
        .st-key-home__workspace .workspace-helper {
            margin:0 0 1.25rem;
            color:var(--workspace-muted);
            font-size:.88rem;
        }
        .st-key-home__workspace .workspace-section {
            margin:1.75rem 0 .65rem;
            color:#52627a;
            font-size:.72rem;
            font-weight:750;
            letter-spacing:.08em;
            text-transform:uppercase;
        }
        .st-key-home__workspace div[data-testid="stButton"] > button {
            min-height:5.65rem;
            justify-content:flex-start;
            padding:1rem 1.05rem;
            border-color:var(--workspace-line);
            border-radius:.85rem;
            background:#fff;
            color:var(--workspace-ink);
            text-align:left;
            white-space:normal;
            line-height:1.45;
            box-shadow:0 7px 24px rgba(28,48,79,.045);
        }
        .st-key-home__workspace div[data-testid="stButton"] > button p {
            width:100%;
            text-align:left;
        }
        .st-key-home__workspace div[data-testid="stButton"] > button:hover {
            border-color:#9fb3d5;
            background:#fbfcff;
            color:var(--workspace-ink);
            transform:translateY(-1px);
        }
        .st-key-home__workspace .st-key-home__action__reply button {
            min-height:6.7rem;
            border-color:#2858c7 !important;
            background:#2858c7 !important;
            color:#fff !important;
            box-shadow:0 14px 32px rgba(40,88,199,.2) !important;
        }
        .st-key-home__workspace .st-key-home__action__improve button,
        .st-key-home__workspace .st-key-home__action__preflight button,
        .st-key-home__workspace .st-key-home__action__scenarios button {
            min-height:4.8rem;
            background:#f8faff;
        }
        .st-key-home__workspace .workspace-footer {
            margin-top:2rem;
            padding:1rem 1.05rem;
            border-top:1px solid var(--workspace-line);
            color:var(--workspace-muted);
            font-size:.78rem;
            line-height:1.65;
        }
        .st-key-home__workspace .workspace-status {
            display:flex;
            flex-wrap:wrap;
            gap:.45rem 1.1rem;
            margin-top:.45rem;
            color:#7f8da0;
            font-size:.7rem;
        }
        @media (max-width:640px) {
            .st-key-home__workspace {
                overflow-x:hidden;
            }
            .st-key-home__workspace .workspace-brand {
                margin-bottom:2rem;
            }
            .st-key-home__workspace .workspace-question {
                margin-top:1.85rem;
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
                min-height:4.9rem;
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
                    <span>{APP_BRAND}</span>
                </div>
                <span class="workspace-version">V2.0 DEVELOPMENT</span>
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
            '<div class="workspace-section">首先处理 · Reply workflow</div>',
            unsafe_allow_html=True,
        )
        _action_button(
            action="reply",
            title="回复收到的邮件　·　开发中",
            description="分析对方诉求、提取必须回复的问题，并协助生成完整回复。",
            prominent=True,
        )

        st.markdown(
            '<div class="workspace-section">高频商务场景</div>',
            unsafe_allow_html=True,
        )
        scene_rows = (
            (
                ("supplier", "催供应商", "催报价、催交期、更新计划或要求解释延期。"),
                ("meeting", "邀请会议", "生成包含时间、地点、议程和确认要求的会议邮件。"),
            ),
            (
                ("progress", "汇报项目进展", "整理进展、风险、影响和下一步。"),
                ("approval", "请求审批", "说明背景、原因、影响和需要管理层决定的事项。"),
            ),
        )
        for row in scene_rows:
            left, right = st.columns(2)
            for column, (action, title, description) in zip(
                (left, right),
                row,
                strict=True,
            ):
                with column:
                    _action_button(
                        action=action,
                        title=title,
                        description=description,
                    )
        _action_button(
            action="schedule",
            title="确认交期或计划",
            description="确认时间、里程碑和需要对方采取的行动。",
        )

        st.markdown(
            '<div class="workspace-section">处理已有内容</div>',
            unsafe_allow_html=True,
        )
        tool_columns = st.columns(3)
        tool_actions = (
            ("improve", "优化已有草稿", "改善语法、结构、语气和行动要求。"),
            ("preflight", "发送前检查　·　开发中", "检查遗漏、承诺、敏感信息和表达风险。"),
            ("scenarios", "更多场景", "采购、项目、行政和管理场景。"),
        )
        for column, (action, title, description) in zip(
            tool_columns,
            tool_actions,
            strict=True,
        ):
            with column:
                _action_button(
                    action=action,
                    title=title,
                    description=description,
                )

        _render_selected_action()

        if render_additional_details:
            with st.expander("产品说明 · About this development preview"):
                render_additional_details()

        st.markdown(
            f"""
            <div class="workspace-footer">
                <strong>安全提醒</strong>：请勿输入密码、银行账号、证件号码、API Key 或其他敏感凭证。<br>
                V2.0 目前处于开发阶段，部分工作流将在后续 Phase 逐步开放。
                <div class="workspace-status">
                    <span>AI 服务：{ai_service_status}</span>
                    <span>运行环境：{environment_label}</span>
                    <span>测试访问保护：{access_protection_label}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
