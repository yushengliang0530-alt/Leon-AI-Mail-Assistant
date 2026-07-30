"""Phase 3 reply workspace: analysis followed by local decision guidance."""

from collections.abc import Callable
import hashlib
import html
import json
import time

import streamlit as st

from ai_service import AIServiceError, SenderDetails
from content_risk_service import ADVISORY_NOTICE, analyze_content_risk
from localization_service import COUNTRY_REGION_OPTIONS
from models.incoming_email import IncomingEmailAnalysis
from services.incoming_email_analysis import (
    IncomingEmailAnalysisService,
    IncomingEmailInputError,
    source_digest,
)
from services.reply_item_service import normalize_reply_items
from services.reply_generation_service import ReplyGenerationService
from ui.pages.reply_decision import (
    render_reply_decisions,
    render_reply_summary,
)
from ui.pages.reply_generation import render_reply_result
from ui.state import (
    clear_reply_state,
    prepare_reply_reanalysis,
    return_to_home,
    start_reply_decisions,
    sync_reply_source,
)


URGENCY_LABELS = {
    "low": "低",
    "normal": "正常",
    "high": "高",
    "urgent": "紧急",
}
RISK_LABELS = {"low": "低", "medium": "中", "high": "高"}


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
        .st-key-reply__workspace {--reply-ink:#13223a;--reply-blue:#2858c7;
          --reply-line:#d9e1ec;--reply-muted:#66758a;}
        .st-key-reply__workspace .reply-header{display:flex;justify-content:
          space-between;gap:1rem;align-items:flex-start;margin:1.2rem 0 1.35rem;}
        .st-key-reply__workspace .reply-kicker{color:var(--reply-blue);
          font-size:.7rem;font-weight:760;letter-spacing:.11em;}
        .st-key-reply__workspace h1{margin:.35rem 0 .25rem;color:var(--reply-ink);
          font-size:2rem;letter-spacing:-.035em;}
        .st-key-reply__workspace .reply-sub{color:var(--reply-muted);
          font-size:.88rem;line-height:1.6;}
        .st-key-reply__workspace .reply-task{padding:.4rem .7rem;border:1px
          solid #c7d3e6;border-radius:999px;background:#f8faff;color:#425978;
          font-size:.72rem;font-weight:700;white-space:nowrap;}
        .st-key-reply__workspace .reply-progress{display:grid;
          grid-template-columns:repeat(5,1fr);gap:.4rem;margin-bottom:1.35rem;}
        .st-key-reply__workspace .reply-progress span{padding:.62rem .75rem;
          border-bottom:2px solid var(--reply-line);color:#8995a5;font-size:.76rem;}
        .st-key-reply__workspace .reply-progress .active{border-color:
          var(--reply-blue);color:var(--reply-blue);font-weight:750;}
        .st-key-reply__workspace .reply-card{padding:1rem 1.05rem;margin:.7rem 0;
          border:1px solid var(--reply-line);border-radius:.85rem;background:#fff;
          box-shadow:0 7px 24px rgba(28,48,79,.04);}
        .st-key-reply__workspace .reply-card h3{margin:0 0 .5rem;color:
          var(--reply-ink);font-size:.9rem;}
        .st-key-reply__workspace .reply-card p,.st-key-reply__workspace
          .reply-card li{color:#4e6079;font-size:.82rem;line-height:1.6;}
        .st-key-reply__workspace .reply-meta{color:#8794a6;font-size:.72rem;}
        @media(max-width:640px){.st-key-reply__workspace .reply-header{
          flex-direction:column}.st-key-reply__workspace h1{font-size:1.7rem}
          .st-key-reply__workspace div[data-testid="stHorizontalBlock"]{
          flex-direction:column}.st-key-reply__workspace div[data-testid="column"]{
          width:100%!important;flex:1 1 100%!important}
          .st-key-reply__workspace .reply-progress span{font-size:.64rem;
          padding:.48rem .25rem}}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _progress(step: int) -> None:
    st.markdown(
        f"""
        <div class="reply-progress">
          <span class="{'active' if step == 1 else ''}">01　分析来信</span>
          <span class="{'active' if step == 2 else ''}">02　查看分析</span>
          <span class="{'active' if step == 3 else ''}">03　确认立场</span>
          <span class="{'active' if step == 4 else ''}">04　生成回复</span>
          <span class="{'active' if step == 5 else ''}">05　覆盖检查</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _risk_panel(email: str) -> object:
    risk = analyze_content_risk(email)
    st.session_state["reply__risk_result"] = risk
    if email.strip():
        if risk.risk_items:
            with st.expander("内容风险提醒", expanded=risk.requires_confirmation):
                st.warning(risk.summary)
                for item in risk.risk_items:
                    st.markdown(
                        f"**{item.category}**：{item.description}  \n"
                        f"建议：{item.suggestion}"
                    )
                st.caption(ADVISORY_NOTICE)
        else:
            st.caption(risk.summary)
    return risk


def _render_input(service: IncomingEmailAnalysisService) -> None:
    st.markdown("### 粘贴收到的邮件")
    st.caption("Paste the incoming email · 支持单封邮件和简单纯文本邮件线程。")
    st.text_input(
        "邮件主题 · Subject（可选）",
        key="reply__original_subject",
        placeholder="例如：Updated Delivery Schedule Required",
        on_change=sync_reply_source,
    )
    st.text_area(
        "收到的邮件正文 · Incoming Email（必填）",
        key="reply__original_email",
        height=300,
        max_chars=service.max_input_chars + 1,
        placeholder=(
            "请粘贴收到的英文商务邮件。可以包含 From、Sent、To、Subject "
            "等普通邮件头。"
        ),
        on_change=sync_reply_source,
    )
    options = COUNTRY_REGION_OPTIONS
    current_region = str(st.session_state.get("reply__country_region", ""))
    if current_region not in options:
        st.session_state["reply__country_region"] = options[0]
    st.selectbox(
        "收件人国家或地区 · Country or Region（可选）",
        options,
        key="reply__country_region",
        on_change=sync_reply_source,
    )
    with st.expander("隐私与保密提醒", expanded=False):
        st.markdown(
            "- 邮件内容会发送至 DeepSeek API 进行分析。\n"
            "- 请删除密码、API Key、身份证件、银行账号及不必要的商业机密。\n"
            "- 风险检查仅供辅助，仍需遵守公司的保密和数据处理规定。"
        )

    email = str(st.session_state.get("reply__original_email", ""))
    risk = _risk_panel(email)
    digest = source_digest(
        str(st.session_state.get("reply__original_subject", "")),
        email,
        str(st.session_state.get("reply__country_region", "")),
    )
    if risk.requires_confirmation:
        st.checkbox(
            "我已核对风险，并确认可以将此内容提交给AI分析。",
            key="reply__risk_confirmed",
        )

    if st.session_state.get("reply__safe_error"):
        st.error(st.session_state["reply__safe_error"])

    if st.button(
        "分析来信",
        key="reply__analyze",
        type="primary",
        use_container_width=True,
        disabled=st.session_state.get("reply__request_status") == "running",
    ):
        st.session_state["reply__safe_error"] = ""
        if risk.requires_confirmation and not st.session_state.get(
            "reply__risk_confirmed", False
        ):
            st.session_state["reply__risk_confirmed_digest"] = ""
            st.session_state["reply__safe_error"] = (
                "检测到高风险内容，请确认已完成核对后再分析。"
            )
            st.rerun()
        if risk.requires_confirmation:
            st.session_state["reply__risk_confirmed_digest"] = digest
        started = time.perf_counter()
        st.session_state["reply__request_status"] = "running"
        try:
            with st.spinner("正在分析对方要求和待回复事项…"):
                analysis = service.analyze(
                    original_subject=st.session_state["reply__original_subject"],
                    original_email=email,
                    country_region=st.session_state["reply__country_region"],
                )
            st.session_state["reply__analysis"] = analysis
            st.session_state["reply__analysis_digest"] = digest
            st.session_state["reply__source_digest"] = digest
            st.session_state["reply__duration"] = time.perf_counter() - started
            st.session_state["reply__tokens"] = analysis.usage_tokens
            st.session_state["reply__request_status"] = "success"
            st.session_state["reply__step"] = 2
            st.rerun()
        except (IncomingEmailInputError, AIServiceError) as exc:
            message = (
                exc.user_message if isinstance(exc, AIServiceError) else str(exc)
            )
            st.session_state["reply__safe_error"] = message
            st.session_state["reply__request_status"] = "error"
            st.rerun()


def _list_card(title: str, items: list[str], empty: str) -> None:
    body = (
        "<ol>" + "".join(f"<li>{html.escape(item)}</li>" for item in items) + "</ol>"
        if items
        else f"<p>{html.escape(empty)}</p>"
    )
    st.markdown(
        f'<div class="reply-card"><h3>{html.escape(title)}</h3>{body}</div>',
        unsafe_allow_html=True,
    )


def _render_result(analysis: IncomingEmailAnalysis) -> None:
    st.markdown("### 来信分析结果")
    st.caption("Analysis Ready · 以下内容用于帮助理解来信，尚未生成回复邮件。")
    for title, value in (
        ("邮件摘要", analysis.summary),
        ("对方意图", analysis.sender_intent),
    ):
        st.markdown(
            f'<div class="reply-card"><h3>{title}</h3><p>'
            f"{html.escape(value)}</p></div>",
            unsafe_allow_html=True,
        )
    _list_card(
        "对方要求",
        [
            item.description
            + (f"｜截止：{item.deadline}" if item.deadline else "")
            + ("｜信息待确认" if item.uncertain else "")
            for item in analysis.sender_requests
        ],
        "未识别到明确行动要求。",
    )
    _list_card(
        "必须回复的问题",
        [
            item.question
            + (f"｜截止：{item.deadline}" if item.deadline else "")
            + ("｜信息待确认" if item.uncertain else "")
            for item in analysis.questions_requiring_reply
        ],
        "未识别到必须回复的问题。",
    )
    facts = [
        f"{item.value}：{item.meaning}"
        + ("（待确认）" if item.uncertain else "")
        for item in (*analysis.key_dates, *analysis.key_numbers)
    ]
    _list_card("关键日期与数字", facts, "邮件中没有明确的关键日期或数字。")
    risk_items = [
        f"{RISK_LABELS[item.level]}｜{item.description} 建议：{item.suggestion}"
        for item in analysis.risks
    ]
    _list_card(
        f"风险和紧急程度 · {URGENCY_LABELS[analysis.urgency]}",
        risk_items,
        "未识别到明确风险，但仍建议人工核对。",
    )
    _list_card("建议回复策略", list(analysis.reply_strategy), "暂无额外策略建议。")
    _list_card("不确定事项", list(analysis.uncertainties), "未标记不确定事项。")

    duration = st.session_state.get("reply__duration")
    tokens = st.session_state.get("reply__tokens")
    meta = []
    if isinstance(duration, (int, float)):
        meta.append(f"分析耗时 {duration:.2f} 秒")
    if isinstance(tokens, int):
        meta.append(f"本次用量 {tokens} tokens")
    if meta:
        st.caption(" · ".join(meta))
    items = normalize_reply_items(analysis)
    st.info(
        f"已整理出 {len(items)} 个待处理事项。下一步将逐项确认您的回复立场，"
        "不会在本阶段生成邮件。"
    )

    if st.button(
        "开始逐项确认",
        key="reply__start_decisions",
        type="primary",
        use_container_width=True,
        disabled=not items,
        on_click=start_reply_decisions,
        args=(items,),
    ):
        st.rerun()

    left, middle, right = st.columns(3)
    with left:
        st.button(
            "修改原邮件",
            key="reply__modify",
            use_container_width=True,
            on_click=prepare_reply_reanalysis,
        )
    with middle:
        st.button(
            "重新分析",
            key="reply__reanalyze",
            use_container_width=True,
            on_click=prepare_reply_reanalysis,
        )
    with right:
        st.button(
            "清空当前分析",
            key="reply__clear",
            use_container_width=True,
            on_click=clear_reply_state,
        )


def render_reply_workspace(
    *,
    analysis_service: IncomingEmailAnalysisService,
    generation_service: ReplyGenerationService,
    render_privacy_notice: Callable[[], None] | None = None,
) -> None:
    _inject_styles()
    step = int(st.session_state.get("reply__step", 1))
    with st.container(key="reply__workspace"):
        st.button(
            "← 返回工作台",
            key="reply__return_home",
            on_click=return_to_home,
        )
        st.markdown(
            f"""
            <div class="reply-header">
              <div>
                <div class="reply-kicker">LEON AI · REPLY WORKSPACE</div>
                <h1>回复收到的邮件</h1>
                <div class="reply-sub">Reply Workspace<br>
                  先理解来信，再逐项确认您的处理立场。</div>
              </div>
              <div class="reply-task">回复收到的邮件 · {step}/5</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        _progress(step)
        analysis = st.session_state.get("reply__analysis")
        digest_valid = (
            analysis is not None
            and st.session_state.get("reply__analysis_digest")
            == st.session_state.get("reply__source_digest")
        )
        items = tuple(st.session_state.get("reply__normalized_items", ()))
        if not digest_valid:
            st.session_state["reply__step"] = 1
            _render_input(analysis_service)
        elif step == 3 and st.session_state.get("reply__decision_summary") is None:
            render_reply_decisions(items)
        elif step == 3:
            if render_reply_summary(items):
                _generate_and_check(generation_service, analysis, items)
        elif step in (4, 5):
            if render_reply_result():
                _run_coverage(generation_service, items)
        else:
            _render_result(analysis)
        if render_privacy_notice:
            with st.expander("隐私与测试说明", expanded=False):
                render_privacy_notice()


def _email_digest(subject: str, body: str) -> str:
    raw = json.dumps([subject, body], ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _run_coverage(
    service: ReplyGenerationService,
    items: tuple,
) -> None:
    st.session_state["reply__coverage_error"] = ""
    st.session_state["reply__coverage_status"] = "running"
    started = time.perf_counter()
    try:
        with st.spinner("正在独立检查回复覆盖情况…"):
            result = service.check_coverage(
                items=items,
                decisions=dict(st.session_state.get("reply__decisions", {})),
                subject=st.session_state["reply__subject"],
                body=st.session_state["reply__body"],
            )
        st.session_state["reply__coverage"] = result
        st.session_state["reply__summary"] = (
            f"本次回复覆盖 {result.covered_count} / "
            f"{result.total_count} 项"
        )
        st.session_state["reply__coverage_status"] = "success"
        st.session_state["reply__coverage_digest"] = _email_digest(
            st.session_state["reply__subject"],
            st.session_state["reply__body"],
        )
        st.session_state["reply__coverage_duration"] = (
            time.perf_counter() - started
        )
        st.session_state["reply__coverage_tokens"] = result.usage_tokens
    except AIServiceError:
        st.session_state["reply__coverage"] = None
        st.session_state["reply__coverage_status"] = "error"
        st.session_state["reply__coverage_error"] = (
            "覆盖检查暂时不可用，请重新检查。"
        )
    st.session_state["reply__step"] = 5
    st.rerun()


def _generate_and_check(
    service: ReplyGenerationService,
    analysis: IncomingEmailAnalysis,
    items: tuple,
) -> None:
    st.session_state["reply__step"] = 4
    st.session_state["reply__generation_status"] = "running"
    st.session_state["reply__generation_error"] = ""
    started = time.perf_counter()
    sender = SenderDetails(
        name=str(st.session_state.get("shared_sender_name", "")),
        job_title=str(st.session_state.get("shared_job_title", "")),
        company=str(st.session_state.get("shared_company", "")),
        contact_information=str(
            st.session_state.get("shared_contact_information", "")
        ),
    )
    try:
        with st.spinner("正在根据已确认立场生成英文回复…"):
            result = service.generate(
                analysis=analysis,
                items=items,
                decisions=dict(st.session_state.get("reply__decisions", {})),
                sender=sender,
                country_region=str(
                    st.session_state.get("reply__country_region", "")
                ),
            )
        st.session_state["reply__generated_email"] = result
        st.session_state["reply__subject"] = result.subject
        st.session_state["reply__body"] = result.body
        st.session_state["reply__generation_status"] = "success"
        st.session_state["reply__generation_duration"] = (
            time.perf_counter() - started
        )
        st.session_state["reply__generation_tokens"] = result.usage_tokens
        st.session_state["reply__generation_digest"] = (
            st.session_state.get("reply__decision_digest", "")
        )
    except AIServiceError as exc:
        st.session_state["reply__generation_status"] = "error"
        st.session_state["reply__generation_error"] = exc.user_message
        st.session_state["reply__step"] = 3
        st.rerun()
    _run_coverage(service, items)
