"""Workspace adapter for the existing business-email improvement capability."""

from __future__ import annotations

import re
import time

import streamlit as st

from ai_service import AIServiceError, DeepSeekEmailService, SenderDetails
from communication_analysis_service import CommunicationAnalysis
from config import DeepSeekSettings, MAX_INPUT_CHARS
from content_risk_service import ADVISORY_NOTICE, analyze_content_risk
from localization_service import COUNTRY_REGION_OPTIONS, build_localization_guidance
from product_identity import APP_VERSION_LABEL
from ui.components import (
    OptimizationOption,
    WorkflowStep,
    primary_action_button,
    render_before_after_panel,
    render_copy_button,
    render_email_editor,
    render_email_subject_card,
    render_loading_state,
    render_notice_bar,
    render_optimization_option_cards,
    render_optimization_summary,
    render_section_header,
    render_workspace_shell,
    secondary_action_button,
    tertiary_action_button,
)
from ui.state import return_to_home


IMPROVE_TONES = {
    "正式 · Formal": ("Formal", "正式专业", "改善商务表达和结构。", "business_center"),
    "友好 · Friendly": ("Friendly", "友好协作", "让沟通自然、合作且专业。", "handshake"),
    "简洁 · Concise": ("Concise", "简洁清晰", "减少冗余，让重点更清楚。", "short_text"),
    "高管简洁 · Executive": ("Executive", "简洁高层", "突出结论和下一步行动。", "analytics"),
}

TONE_CARD_KEYS = {
    "正式 · Formal": "formal",
    "友好 · Friendly": "friendly",
    "简洁 · Concise": "concise",
    "高管简洁 · Executive": "executive",
}
TONE_LABELS_BY_CARD_KEY = {value: key for key, value in TONE_CARD_KEYS.items()}

IMPROVE_WORKFLOW_STEPS = (
    WorkflowStep("draft", "草稿", "Draft"),
    WorkflowStep("optimize", "优化目标", "Optimize"),
    WorkflowStep("result", "优化结果", "Result"),
)


def _workflow_steps(step: int) -> tuple[WorkflowStep, ...]:
    return tuple(
        WorkflowStep(
            item.key,
            item.label,
            item.helper,
            "current" if index == step else "complete" if index < step else "upcoming",
        )
        for index, item in enumerate(IMPROVE_WORKFLOW_STEPS, start=1)
    )


def _set_step(step: int) -> None:
    st.session_state["improve__step"] = max(1, min(3, int(step)))
    st.session_state["improve__error"] = ""


def _draft() -> str:
    return str(st.session_state.get("saved_improve_original_email", ""))


def _clear_draft() -> None:
    for key in (
        "improve__draft_subject",
        "improve_original_email",
        "saved_improve_original_email",
        "improved_subject",
        "improved_body",
        "improved_subject_editor",
        "improved_body_editor",
    ):
        st.session_state[key] = ""
    st.session_state["improved"] = False
    st.session_state["improve__error"] = ""
    st.session_state["improve_high_risk_confirmed"] = False
    st.session_state["improve_confirmed_digest"] = ""
    _set_step(1)


def _save_draft(value: str) -> None:
    st.session_state["saved_improve_original_email"] = value.strip()
    st.session_state["improve__error"] = ""
    st.session_state["improve_high_risk_confirmed"] = False
    st.session_state["improve_confirmed_digest"] = ""
    st.session_state["improved"] = False


def _digest(value: str) -> str:
    import hashlib

    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _split_draft(value: str) -> tuple[str, str]:
    """Separate an optional visible subject without changing source facts."""
    match = re.search(r"(?im)^subject\s*:\s*(.+)$", value)
    if not match:
        return "", value
    body = (value[: match.start()] + value[match.end() :]).lstrip("\n\r ")
    return match.group(1).strip(), body


def _compose_draft(subject: str, body: str) -> str:
    if subject.strip():
        return f"Subject: {subject.strip()}\n\n{body.strip()}".strip()
    return body.strip()


def _restore_advanced_values() -> None:
    context = st.session_state.get("improve__presentation_options", {})
    if not isinstance(context, dict):
        context = {}
    sender = context.get("sender", {})
    if not isinstance(sender, dict):
        sender = {}
    values = {
        "improve_country_region": str(
            context.get("country_region", COUNTRY_REGION_OPTIONS[0])
        ),
        "improve_custom_region": str(context.get("custom_region", "")),
        "shared_sender_name": str(sender.get("name", "")),
        "shared_job_title": str(sender.get("job_title", "")),
        "shared_company": str(sender.get("company", "")),
        "shared_contact_information": str(sender.get("contact_information", "")),
    }
    for key, value in values.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _advanced_options() -> tuple[str, str, SenderDetails]:
    _restore_advanced_values()
    region = st.selectbox(
        "收件人所在国家或地区",
        COUNTRY_REGION_OPTIONS,
        key="improve_country_region",
        label_visibility="collapsed",
    )
    custom_region = ""
    if region == "其他 / Other":
        custom_region = st.text_input(
            "请填写国家或地区",
            key="improve_custom_region",
            placeholder="例如：Brazil",
            label_visibility="collapsed",
        )
    st.markdown("**发件人与邮件签名**")
    sender = SenderDetails(
        name=st.text_input(
            "发件人姓名",
            key="shared_sender_name",
            placeholder="例如：David Chen",
            label_visibility="collapsed",
        ),
        job_title=st.text_input(
            "职位",
            key="shared_job_title",
            placeholder="例如：Project Coordinator",
            label_visibility="collapsed",
        ),
        company=st.text_input(
            "公司",
            key="shared_company",
            placeholder="例如：ABC Engineering Co., Ltd.",
            label_visibility="collapsed",
        ),
        contact_information=st.text_input(
            "联系方式",
            key="shared_contact_information",
            placeholder="例如：david.chen@example.com",
            label_visibility="collapsed",
        ),
    )
    return region, custom_region, sender


def _save_presentation_options(
    *,
    region: str,
    custom_region: str,
    sender: SenderDetails,
) -> None:
    st.session_state["improve__presentation_options"] = {
        "country_region": region,
        "custom_region": custom_region,
        "sender": {
            "name": sender.name,
            "job_title": sender.job_title,
            "company": sender.company,
            "contact_information": sender.contact_information,
        },
    }


def _render_draft_step() -> None:
    render_section_header("粘贴邮件草稿", "DRAFT")
    st.caption("把已有邮件贴进来即可。Leon AI 会优化表达，同时保留原有事实与立场。")
    saved_subject, saved_body = _split_draft(_draft())
    if "improve__draft_subject" not in st.session_state:
        st.session_state["improve__draft_subject"] = saved_subject
    if "improve_original_email" not in st.session_state:
        st.session_state["improve_original_email"] = saved_body
    with st.container(key="improve__draft_canvas"):
        st.markdown('<div class="la-email-subject__label">Subject · 可选</div>', unsafe_allow_html=True)
        subject = st.text_input(
            "邮件主题",
            key="improve__draft_subject",
            placeholder="可选：粘贴或填写原邮件主题",
            label_visibility="collapsed",
        )
        st.markdown('<div class="la-email-editor__label">Email Body</div>', unsafe_allow_html=True)
        draft = st.text_area(
            "邮件正文",
            key="improve_original_email",
            placeholder="请粘贴需要优化的英文邮件全文。",
            height=360,
            max_chars=MAX_INPUT_CHARS + 1,
            label_visibility="collapsed",
        )
    left, right = st.columns((0.35, 0.65), gap="small")
    with left:
        clear_clicked = secondary_action_button("清空", key="improve__clear_draft")
    with right:
        continue_clicked = primary_action_button(
            "选择优化重点 →", key="improve__draft_continue"
        )
    if clear_clicked:
        _clear_draft()
        st.rerun()
    if continue_clicked:
        source = _compose_draft(subject, draft)
        if not draft.strip():
            st.session_state["improve__error"] = "请先粘贴需要优化的英文邮件。"
        elif len(source) > MAX_INPUT_CHARS:
            st.session_state["improve__error"] = f"原始英文邮件不能超过 {MAX_INPUT_CHARS} 个字符。"
        else:
            _save_draft(source)
            _set_step(2)
            st.rerun()
    if st.session_state.get("improve__error"):
        st.error(st.session_state["improve__error"])


def _render_target_step(settings: DeepSeekSettings) -> None:
    draft = _draft()
    if not draft:
        _set_step(1)
        st.rerun()
    render_section_header("选择优化重点", "OPTIMIZE")
    st.caption("选择最符合当前沟通目的的表达方式。")
    selected_label = str(
        st.session_state.get("saved_improve_tone_choice", "正式 · Formal")
    )
    if selected_label not in IMPROVE_TONES:
        selected_label = "正式 · Formal"
    options = tuple(
        OptimizationOption(
            key=TONE_CARD_KEYS[label],
            title=title,
            description=description,
            icon=icon,
        )
        for label, (_, title, description, icon) in IMPROVE_TONES.items()
    )
    selected = render_optimization_option_cards(
        options,
        selected=TONE_CARD_KEYS[selected_label],
        key_prefix="improve__tone__",
    )
    if selected:
        selected_label = TONE_LABELS_BY_CARD_KEY[selected]
        st.session_state["saved_improve_tone_choice"] = selected_label
        st.session_state["improve_tone_choice"] = selected_label
        st.rerun()

    tone, _, _, _ = IMPROVE_TONES[selected_label]
    with st.expander("高级选项", expanded=False):
        st.caption("国家或地区、本地化与签名信息仅在需要时填写。")
        region, custom_region, sender = _advanced_options()

    guidance = build_localization_guidance(
        recipient="",
        country_region=region,
        custom_region=custom_region,
        tone=tone,
        source_text=draft,
    )
    risk = analyze_content_risk(draft)
    if risk.risk_level == "high":
        render_notice_bar("需要确认", risk.summary, icon="!")
        confirmed = st.checkbox(
            "我已检查并确认内容可以提交给 AI 处理。",
            key="improve_high_risk_confirmed",
        )
        st.session_state["improve_confirmed_digest"] = _digest(draft) if confirmed else ""
    elif risk.risk_level == "medium":
        render_notice_bar("需要留意", risk.summary, icon="!")
    else:
        render_notice_bar(
            "事实与立场",
            "Leon AI 会优化表达方式；发送前请再次核对关键事实和承诺。",
            icon="i",
        )

    back, optimize = st.columns((0.35, 0.65), gap="small")
    with back:
        back_clicked = secondary_action_button("← 修改草稿", key="improve__target_back")
    with optimize:
        optimize_clicked = primary_action_button(
            "开始优化",
            key="improve__start",
            disabled=bool(st.session_state.get("request_in_progress", False)),
        )
    if back_clicked:
        _set_step(1)
        st.rerun()
    if not optimize_clicked:
        return
    if risk.requires_confirmation and (
        not st.session_state.get("improve_high_risk_confirmed", False)
        or st.session_state.get("improve_confirmed_digest") != _digest(draft)
    ):
        st.session_state["improve__error"] = "检测到高风险内容。请先完成人工检查并勾选确认后再提交。"
        st.rerun()
    if st.session_state.get("request_in_progress", False):
        st.session_state["improve__error"] = "当前请求正在处理中，请稍候。"
        st.rerun()
    _save_presentation_options(region=region, custom_region=custom_region, sender=sender)
    st.session_state["request_in_progress"] = True
    started = time.perf_counter()
    try:
        render_loading_state(
            "正在优化邮件…",
            "正在改善表达、结构和商务语气，同时保留原有事实与立场。",
        )
        with st.spinner("正在优化英文邮件，请稍候……"):
            result = DeepSeekEmailService(settings).improve_email(
                original_email=draft,
                tone=tone,
                country_region=(custom_region.strip() if region == "其他 / Other" else region),
                localization_context=(
                    f"Recommended salutation: {guidance.recommended_salutation}\n"
                    f"Salutation risk: {guidance.salutation_risk}\n"
                    f"Politeness guidance: {guidance.politeness_guidance}\n"
                    f"Cross-cultural note: {guidance.cross_cultural_note}"
                ),
                sender=sender,
            )
        st.session_state["improved_subject"] = result.subject
        st.session_state["improved_body"] = result.body
        st.session_state["improved_subject_editor"] = result.subject
        st.session_state["improved_body_editor"] = result.body
        st.session_state["improved_analysis"] = result.communication_analysis
        st.session_state["improved"] = True
        st.session_state["deepseek_connected"] = True
        st.session_state["last_request_duration"] = time.perf_counter() - started
        st.session_state["last_usage_tokens"] = result.usage_tokens
        _set_step(3)
        st.rerun()
    except AIServiceError as exc:
        st.session_state["improve__error"] = exc.user_message
        st.error(exc.user_message)
    finally:
        st.session_state["request_in_progress"] = False


def _summary_items(analysis: CommunicationAnalysis, tone_label: str) -> tuple[str, ...]:
    if analysis.improvement_suggestions:
        return analysis.improvement_suggestions
    return (
        f"已按“{IMPROVE_TONES[tone_label][1]}”方向调整表达。",
        "请在发送前核对日期、金额、姓名和商务承诺。",
    )


def _render_result_step(settings: DeepSeekSettings) -> None:
    if not st.session_state.get("improved", False):
        _set_step(2)
        st.rerun()
    render_section_header("优化完成", "RESULT")
    st.caption("请对比修改内容并确认最终版本。")
    draft = _draft()
    analysis = st.session_state.get("improved_analysis")
    if not isinstance(analysis, CommunicationAnalysis):
        analysis = CommunicationAnalysis()
    selected_label = str(st.session_state.get("saved_improve_tone_choice", "正式 · Formal"))
    if selected_label not in IMPROVE_TONES:
        selected_label = "正式 · Formal"

    original_subject, original_body = _split_draft(draft)
    render_before_after_panel(
        original_subject=original_subject,
        original_body=original_body,
        render_after=lambda: (
            render_email_subject_card(
                value_key="improved_subject_editor",
                on_change=lambda: None,
            ),
            render_email_editor(
                value_key="improved_body_editor",
                on_change=lambda: None,
            ),
        ),
    )
    subject = str(st.session_state.get("improved_subject_editor", ""))
    body = str(st.session_state.get("improved_body_editor", ""))
    render_copy_button(
        label="复制优化后的完整邮件",
        value=f"Subject: {subject}\n\n{body}",
        key="improve__copy_full_email",
        primary=True,
    )

    render_section_header("本次优化", "SUMMARY")
    render_optimization_summary(_summary_items(analysis, selected_label))
    with st.expander("沟通建议", expanded=False):
        st.markdown(f"**沟通目的**：{analysis.purpose}")
        st.markdown(f"**行动要求**：{analysis.action_required}")
        st.markdown(f"**商务语气**：{analysis.tone}")
        st.markdown(f"**截止时间**：{analysis.deadline}")
    with st.expander("需要留意", expanded=False):
        st.markdown(f"**承诺风险**：{analysis.commitment_risk}")
        st.markdown(f"**表达歧义**：{analysis.ambiguity_risk}")
        st.caption(ADVISORY_NOTICE)

    actions = st.columns((1, 1), gap="small")
    with actions[0]:
        again_clicked = secondary_action_button("再次优化", key="improve__again")
    with actions[1]:
        target_clicked = tertiary_action_button(
            "返回修改优化目标",
            key="improve__return_targets",
        )
    if target_clicked or again_clicked:
        _set_step(2)
        st.rerun()


def render_improve_workspace(*, settings: DeepSeekSettings, service_status: str) -> None:
    """Render a three-step UI adapter around the unchanged improvement service."""
    if "improve__step" not in st.session_state:
        st.session_state["improve__step"] = 1
    if "improve__error" not in st.session_state:
        st.session_state["improve__error"] = ""
    if "improve__presentation_options" not in st.session_state:
        st.session_state["improve__presentation_options"] = {}
    step = int(st.session_state["improve__step"])

    def render_task() -> None:
        if step == 1:
            _render_draft_step()
        elif step == 2:
            _render_target_step(settings)
        else:
            _render_result_step(settings)
        if st.session_state.get("improve__error") and step != 1:
            st.error(st.session_state["improve__error"])

    render_workspace_shell(
        workspace_key="improve",
        version=APP_VERSION_LABEL,
        service_status=service_status,
        title="优化已有邮件",
        description="Improve Draft Workspace · 优化表达、商务语气和结构，同时保留原有事实与立场。",
        eyebrow="LEON AI · IMPROVE DRAFT",
        steps=_workflow_steps(step),
        render_task=render_task,
        on_return_home=return_to_home,
        icon="polish",
    )
