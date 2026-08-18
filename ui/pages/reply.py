"""Reply workspace: analysis followed by local decision guidance."""

from collections.abc import Callable
import hashlib
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
from services.reply_item_service import (
    build_acknowledgement_item,
    normalize_reply_items,
)
from services.reply_generation_service import ReplyGenerationService
from services.preflight_service import (
    PreflightService,
    preflight_source_digest,
    report_from_items,
)
from product_identity import APP_VERSION_LABEL
from ui.components import (
    AnalysisAction,
    AnalysisDate,
    AnalysisNotice,
    WorkflowStep,
    render_action_bar,
    render_analysis_action_cards,
    render_analysis_date_cards,
    render_analysis_notices,
    render_analysis_summary_panel,
    render_empty_state,
    render_loading_state,
    render_section_header,
    render_strategy_list,
    tertiary_action_button,
    render_workspace_shell,
)
from ui.pages.reply_decision import (
    render_reply_decisions,
    render_reply_summary,
)
from ui.pages.reply_generation import render_reply_result
from ui.pages.preflight import render_preflight_panel
from ui.state import (
    clear_reply_state,
    prepare_reply_reanalysis,
    invalidate_preflight,
    return_to_home,
    return_to_reply_decisions,
    start_reply_decisions,
    sync_reply_source,
)


URGENCY_PRESENTATION = {
    "low": ("低优先级", "info"),
    "normal": ("正常优先级", "info"),
    "high": ("高优先级", "warning"),
    "urgent": ("紧急", "risk"),
}
RISK_PRESENTATION = {
    "low": ("提示", "info"),
    "medium": ("需要确认", "warning"),
    "high": ("需要留意", "risk"),
}


REPLY_WORKFLOW = (
    ("email", "Email", "Incoming email"),
    ("analysis", "Analysis", "Understand the request"),
    ("decision", "Decision", "Confirm your position"),
    ("generate", "Generate", "Create the reply"),
    ("check", "Check", "Review before sending"),
)


def _reply_workflow_steps(step: int) -> tuple[WorkflowStep, ...]:
    """Project Reply state onto the shared display-only workflow navigation."""
    current_step = max(1, min(len(REPLY_WORKFLOW), step))
    return tuple(
        WorkflowStep(
            key=key,
            label=label,
            helper=helper,
            state=(
                "complete"
                if index < current_step
                else "current"
                if index == current_step
                else "upcoming"
            ),
        )
        for index, (key, label, helper) in enumerate(REPLY_WORKFLOW, start=1)
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
            render_loading_state(
                "正在分析来信…",
                "正在识别对方要求、关键日期和潜在风险。",
            )
            with st.spinner("正在分析对方要求和待回复事项…"):
                analysis = service.analyze(
                    original_subject=st.session_state["reply__original_subject"],
                    original_email=email,
                    country_region=st.session_state["reply__country_region"],
                )
            st.session_state["reply__analysis"] = analysis
            st.session_state["reply__analysis_digest"] = digest
            st.session_state["reply__source_digest"] = digest
            st.session_state["reply__preserved_subject"] = str(
                st.session_state["reply__original_subject"]
            )
            st.session_state["reply__preserved_email"] = email
            st.session_state["reply__preserved_country_region"] = str(
                st.session_state["reply__country_region"]
            )
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


def _render_result(analysis: IncomingEmailAnalysis) -> None:
    urgency_label, urgency_kind = URGENCY_PRESENTATION.get(
        analysis.urgency,
        ("正常优先级", "info"),
    )
    render_analysis_summary_panel(
        summary=analysis.summary,
        sender_intent=analysis.sender_intent,
        urgency_label=urgency_label,
        urgency_kind=urgency_kind,
    )

    requests_by_id = {
        request.item_id: request.description
        for request in analysis.sender_requests
    }
    questions = tuple(
        AnalysisAction(
            title=question.question,
            deadline=question.deadline,
            required=question.required,
            uncertain=question.uncertain,
            related_context=requests_by_id.get(question.related_request_id or ""),
        )
        for question in analysis.questions_requiring_reply
    )
    requests = tuple(
        AnalysisAction(
            title=request.description,
            deadline=request.deadline,
            required=request.needs_response,
            uncertain=request.uncertain,
        )
        for request in analysis.sender_requests
    )
    dates = tuple(
        AnalysisDate(
            value=item.value,
            meaning=item.meaning,
            uncertain=item.uncertain,
        )
        for item in analysis.key_dates
    )
    risk_notices = tuple(
        AnalysisNotice(
            title=(
                f"{RISK_PRESENTATION.get(risk.level, ('提示', 'info'))[0]}"
                f" · {risk.category}"
            ),
            body=(
                f"{risk.description} 建议：{risk.suggestion}"
                if risk.suggestion
                else risk.description
            ),
            kind=RISK_PRESENTATION.get(risk.level, ("提示", "info"))[1],
        )
        for risk in analysis.risks
    )

    primary, supporting = st.columns((1.35, 0.85), gap="large")
    with primary:
        render_section_header("需要逐项回复", "QUESTIONS")
        if questions:
            render_analysis_action_cards(questions, variant="question")
        else:
            render_empty_state(
                "未识别到明确需要逐项回复的问题",
                "系统仍会在下方整理对方要求，并可帮助您继续回复。",
            )

        render_section_header("对方要求", "REQUESTS")
        if requests:
            render_analysis_action_cards(requests, variant="request")
        else:
            render_empty_state(
                "未识别到明确行动要求",
                "请结合原邮件内容人工确认下一步。",
            )

    with supporting:
        render_section_header("关键日期", "KEY DATES")
        if dates:
            render_analysis_date_cards(dates)
        else:
            render_empty_state(
                "未识别到明确日期要求",
                "邮件中没有可确认的截止时间或计划日期。",
            )

        render_section_header("需要留意", "CHECK")
        if risk_notices:
            render_analysis_notices(risk_notices)
        else:
            render_analysis_notices(
                (
                    AnalysisNotice(
                        title="暂无明确风险",
                        body="仍建议在发送回复前核对承诺、日期和责任。",
                        kind="info",
                    ),
                )
            )

        render_section_header("建议回复思路", "STRATEGY")
        if analysis.reply_strategy:
            render_strategy_list(tuple(analysis.reply_strategy))
        else:
            render_empty_state(
                "暂无额外策略建议",
                "可先确认已收到，再区分已确认与待核实事项。",
            )

        if analysis.key_numbers or analysis.uncertainties:
            with st.expander("更多关键信息", expanded=False):
                if analysis.key_numbers:
                    st.caption("关键数字")
                    for item in analysis.key_numbers:
                        st.markdown(
                            f"- **{item.value}**：{item.meaning}"
                            + ("（待确认）" if item.uncertain else "")
                        )
                if analysis.uncertainties:
                    st.caption("不确定事项")
                    for item in analysis.uncertainties:
                        st.markdown(f"- {item}")

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
    if items:
        render_analysis_notices(
            (
                AnalysisNotice(
                    title="下一步",
                    body=(
                        f"已整理出 {len(items)} 个待处理事项。"
                        "确认立场后，Leon AI 才会生成回复。"
                    ),
                    kind="info",
                ),
            )
        )
        render_action_bar(
            primary_label="确认回复立场",
            primary_key="reply__start_decisions",
            on_primary=lambda: start_reply_decisions(items),
            secondary_label="修改原邮件",
            secondary_key="reply__modify",
            on_secondary=prepare_reply_reanalysis,
        )
    else:
        render_empty_state(
            "未识别到明确需要逐项回复的问题",
            "Leon AI 仍可以帮助您生成一封确认收到或回应状态更新的邮件。",
        )
        render_action_bar(
            primary_label="继续回复",
            primary_key="reply__continue_with_acknowledgement",
            on_primary=lambda: start_reply_decisions(
                (build_acknowledgement_item(),)
            ),
            secondary_label="返回修改邮件",
            secondary_key="reply__return_to_modify_from_zero",
            on_secondary=prepare_reply_reanalysis,
        )
    tertiary_action_button(
        "重新分析",
        key="reply__reanalyze",
        on_click=prepare_reply_reanalysis,
    )
    with st.expander("更多操作", expanded=False):
        tertiary_action_button(
            "清空当前分析",
            key="reply__clear",
            on_click=clear_reply_state,
        )


def render_reply_workspace(
    *,
    analysis_service: IncomingEmailAnalysisService,
    generation_service: ReplyGenerationService,
    preflight_service: PreflightService,
    render_privacy_notice: Callable[[], None] | None = None,
    service_status: str = "已配置",
) -> None:
    """Adapt the existing Reply flow to the shared V2.1 workspace shell."""
    step = int(st.session_state.get("reply__step", 1))
    analysis = st.session_state.get("reply__analysis")
    digest_valid = (
        analysis is not None
        and st.session_state.get("reply__analysis_digest")
        == st.session_state.get("reply__source_digest")
    )
    if not digest_valid:
        st.session_state["reply__step"] = 1
        step = 1

    def render_task() -> None:
        items = tuple(st.session_state.get("reply__normalized_items", ()))
        if not digest_valid:
            _render_input(analysis_service)
        elif step == 3 and st.session_state.get("reply__decision_summary") is None:
            render_reply_decisions(items)
        elif step == 3:
            if render_reply_summary(items):
                _generate_and_check(generation_service, analysis, items)
        elif step == 4:
            item_titles = {item.item_id: item.description for item in items}
            action = render_reply_result(item_titles=item_titles)
            if action == "recheck":
                _run_coverage(generation_service, items)
            elif action == "regenerate":
                _generate_and_check(generation_service, analysis, items)
            elif action == "back":
                return_to_reply_decisions()
                st.rerun()
            elif action == "preflight":
                st.session_state["reply__step"] = 5
                st.rerun()
        elif step == 5:
            # Streamlit clears widgets that are absent from the Check canvas.
            # These snapshots preserve only the user-edited presentation values.
            st.session_state["reply__subject"] = str(
                st.session_state.get("reply__presentation_subject", "")
            )
            st.session_state["reply__body"] = str(
                st.session_state.get("reply__presentation_body", "")
            )
            if render_preflight_panel():
                _run_preflight(preflight_service, analysis)
        else:
            _render_result(analysis)
        if render_privacy_notice:
            with st.expander("隐私与测试说明", expanded=False):
                render_privacy_notice()
    render_workspace_shell(
        workspace_key="reply",
        version=APP_VERSION_LABEL,
        service_status=service_status,
        title="回复收到的邮件",
        description="Reply Email Workspace · 分析来信、确认立场并生成专业商务回复。",
        eyebrow="LEON AI · 回复收到的邮件",
        steps=_reply_workflow_steps(step),
        render_task=render_task,
        on_return_home=return_to_home,
        icon="reply",
    )


def _email_digest(subject: str, body: str) -> str:
    raw = json.dumps([subject, body], ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _run_coverage(
    service: ReplyGenerationService,
    items: tuple,
) -> None:
    st.session_state["reply__coverage_error"] = ""
    st.session_state["reply__coverage_status"] = "running"
    invalidate_preflight()
    started = time.perf_counter()
    try:
        render_loading_state(
            "正在检查回复完整性…",
            "正在逐项核对已确认事项是否得到回应。",
        )
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
    st.session_state["reply__step"] = 4
    st.rerun()


def _run_preflight(
    service: PreflightService,
    analysis: IncomingEmailAnalysis,
) -> None:
    subject = str(st.session_state.get("reply__subject", "")).strip()
    body = str(st.session_state.get("reply__body", "")).strip()
    if not subject or not body:
        st.session_state["preflight__error"] = (
            "请先确认邮件主题和正文，再运行发送前检查。"
        )
        st.session_state["preflight__status"] = "error"
        st.rerun()

    decisions = dict(st.session_state.get("reply__decisions", {}))
    coverage = st.session_state.get("reply__coverage")
    if (
        st.session_state.get("reply__coverage_status") != "success"
        or st.session_state.get("reply__coverage_digest")
        != _email_digest(subject, body)
    ):
        coverage = None
    tone = str(st.session_state.get("reply__target_tone", "Formal"))
    local_items = service.build_local_items(
        analysis=analysis,
        decisions=decisions,
        subject=subject,
        body=body,
        coverage=coverage,
    )
    st.session_state["preflight__local_items"] = local_items
    st.session_state["preflight__status"] = "running"
    st.session_state["preflight__error"] = ""
    started = time.perf_counter()
    try:
        render_loading_state(
            "正在执行发送前检查…",
            "正在检查行动要求、截止时间、附件提示与承诺风险。",
        )
        with st.spinner("正在检查遗漏、语气和商务风险…"):
            report = service.inspect(
                analysis=analysis,
                decisions=decisions,
                subject=subject,
                body=body,
                coverage=coverage,
                target_tone=tone,
            )
        st.session_state["preflight__report"] = report
        st.session_state["preflight__ai_items"] = tuple(
            item for item in report.items if item.source == "ai"
        )
        st.session_state["preflight__usage_tokens"] = report.usage_tokens
        st.session_state["preflight__status"] = "success"
    except AIServiceError:
        st.session_state["preflight__report"] = report_from_items(
            local_items,
            summary=(
                "已完成本地规则检查；AI语义检查暂时不可用，"
                "请人工确认称谓、语气和承诺。"
            ),
        )
        st.session_state["preflight__ai_items"] = ()
        st.session_state["preflight__usage_tokens"] = None
        st.session_state["preflight__status"] = "partial"
        st.session_state["preflight__error"] = (
            "AI语义检查暂时不可用，已保留本地检查结果。"
        )
    st.session_state["preflight__source_digest"] = preflight_source_digest(
        subject=subject,
        body=body,
        decisions=decisions,
        target_tone=tone,
        coverage=coverage,
    )
    st.session_state["preflight__duration_seconds"] = (
        time.perf_counter() - started
    )
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
        render_loading_state(
            "正在生成商务回复…",
            "正在整理已确认立场，准备清晰、专业的英文回复。",
        )
        with st.spinner("正在根据已确认立场生成英文回复…"):
            result = service.generate(
                analysis=analysis,
                items=items,
                decisions=dict(st.session_state.get("reply__decisions", {})),
                sender=sender,
                country_region=str(
                    st.session_state.get("reply__country_region", "")
                ),
                target_tone=str(
                    st.session_state.get("reply__target_tone", "Formal")
                ),
            )
        st.session_state["reply__generated_email"] = result
        st.session_state["reply__subject"] = result.subject
        st.session_state["reply__body"] = result.body
        st.session_state["reply__presentation_subject"] = result.subject
        st.session_state["reply__presentation_body"] = result.body
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
