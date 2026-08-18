"""Four-step guided supplier workflow driven by Scenario configuration."""

import time
from collections.abc import Callable

import streamlit as st

from ai_service import AIServiceError, SenderDetails
from communication_analysis_service import CommunicationAnalysis
from content_risk_service import ADVISORY_NOTICE, analyze_content_risk
from data.email_scenarios import SUPPLIER_SCENARIOS, get_supplier_scenario
from localization_service import (
    COUNTRY_REGION_OPTIONS,
    LocalizationGuidance,
    build_localization_guidance,
)
from models.scenario import Scenario, ScenarioField
from services.scenario_service import ScenarioService, validate_scenario_facts
from product_identity import APP_VERSION_LABEL
from ui.components import (
    ReviewItem,
    ScenarioCard,
    WorkflowStep,
    primary_action_button,
    render_copy_button,
    render_email_editor,
    render_email_subject_card,
    render_guided_action_bar,
    render_guided_question_header,
    render_loading_state,
    render_review_items,
    render_scenario_cards,
    render_section_header,
    render_workspace_shell,
    secondary_action_button,
    tertiary_action_button,
)
from ui.state import (
    advance_compose_question,
    back_compose_question,
    edit_compose_answer,
    return_to_compose_review,
    return_to_home,
    save_compose_answer,
    set_compose_step,
    set_compose_task,
)


TONE_OPTIONS = {
    "正式 · Formal": "Formal",
    "友好 · Friendly": "Friendly",
    "明确强硬 · Strong": "Strong",
    "高管简洁 · Executive": "Executive",
}
TONE_LABEL_BY_VALUE = {value: key for key, value in TONE_OPTIONS.items()}


CREATE_WORKFLOW_STEPS = (
    WorkflowStep("scenario", "场景", "Scenario"),
    WorkflowStep("details", "信息", "Details"),
    WorkflowStep("review", "确认", "Review"),
    WorkflowStep("email", "邮件", "Email"),
)


def _workflow_steps(step: int) -> tuple[WorkflowStep, ...]:
    return tuple(
        WorkflowStep(
            item.key,
            item.label,
            item.helper,
            "current" if index == step else "done" if index < step else "upcoming",
        )
        for index, item in enumerate(CREATE_WORKFLOW_STEPS, start=1)
    )


def _render_answer_input(field: ScenarioField) -> str:
    key = f"compose__answer_widget__{field.key}"
    answers = dict(st.session_state.get("compose__answers", {}))
    if key not in st.session_state:
        st.session_state[key] = str(answers.get(field.key, ""))
    common = {
        "key": key,
        "placeholder": field.placeholder,
        "label_visibility": "collapsed",
        "max_chars": field.max_length,
    }
    if field.field_type == "textarea":
        return st.text_area(field.label_zh, height=135, **common)
    return st.text_input(field.label_zh, **common)


def _localization_context(guidance: LocalizationGuidance) -> str:
    return (
        f"Recommended salutation: {guidance.recommended_salutation}\n"
        f"Salutation risk: {guidance.salutation_risk}\n"
        f"Politeness guidance: {guidance.politeness_guidance}\n"
        f"Cross-cultural note: {guidance.cross_cultural_note}"
    )


def _render_step_one() -> None:
    render_section_header("选择商务任务", "SCENARIO")
    st.markdown("#### 催供应商")
    st.caption("催交期、催文件、催更新计划或要求解释延期。")
    cards = tuple(
        ScenarioCard(
            key=scenario.id,
            title=scenario.title_zh,
            description=scenario.description,
            icon="local_shipping",
        )
        for scenario in SUPPLIER_SCENARIOS
    )
    selected = render_scenario_cards(
        cards,
        key_prefix="compose__task__",
    )
    if selected:
        set_compose_task(selected)
        st.rerun()

    with st.expander("更多场景", expanded=False):
        render_scenario_cards(
            (
                ScenarioCard("meeting", "会议沟通", "会议邀请与行动项确认即将推出。", "calendar_month", False, "Coming soon"),
                ScenarioCard("report", "项目汇报", "项目进展与风险汇报即将推出。", "monitoring", False, "Coming soon"),
                ScenarioCard("approval", "请求审批", "审批沟通工作流即将推出。", "fact_check", False, "Coming soon"),
            ),
            key_prefix="compose__coming_soon__",
        )


def _render_advanced(scenario: Scenario) -> tuple[str, str, str, SenderDetails]:
    context = st.session_state.get("compose__ui_generation_context", {})
    if not isinstance(context, dict):
        context = {}
    saved_sender = context.get("sender", {})
    if not isinstance(saved_sender, dict):
        saved_sender = {}
    restored_values = {
        "compose__tone_choice": TONE_LABEL_BY_VALUE.get(
            str(context.get("tone", scenario.default_tone)),
            TONE_LABEL_BY_VALUE[scenario.default_tone],
        ),
        "compose__country_region": str(
            context.get("country_region", COUNTRY_REGION_OPTIONS[0])
        ),
        "compose__recipient": str(context.get("recipient", "")),
        "compose__custom_region": str(context.get("custom_region", "")),
        "shared_sender_name": str(saved_sender.get("name", "")),
        "shared_job_title": str(saved_sender.get("job_title", "")),
        "shared_company": str(saved_sender.get("company", "")),
        "shared_contact_information": str(
            saved_sender.get("contact_information", "")
        ),
    }
    for key, value in restored_values.items():
        if key not in st.session_state:
            st.session_state[key] = value
    default_label = TONE_LABEL_BY_VALUE[scenario.default_tone]
    if st.session_state.get("compose__tone_task_id") != scenario.id:
        st.session_state["compose__tone_choice"] = default_label
        st.session_state["compose__tone_task_id"] = scenario.id
    tone_label = st.selectbox(
        "邮件语气 · Tone",
        list(TONE_OPTIONS),
        key="compose__tone_choice",
    )
    country_region = st.selectbox(
        "收件人国家或地区 · Country or Region",
        COUNTRY_REGION_OPTIONS,
        key="compose__country_region",
    )
    if country_region == "其他 / Other":
        st.text_input(
            "具体国家或地区 · Specify Region",
            key="compose__custom_region",
        )
    recipient = st.text_input(
        "收件人 · Recipient",
        key="compose__recipient",
        placeholder="例如：Mr. Smith 或 Supplier Team",
    )
    st.markdown("**发件人与邮件签名 · Sender & Signature**")
    sender = SenderDetails(
        name=st.text_input(
            "发件人姓名 · Sender Name",
            key="shared_sender_name",
            placeholder="例如：David Chen",
        ),
        job_title=st.text_input(
            "职位 · Job Title",
            key="shared_job_title",
            placeholder="例如：Project Coordinator",
        ),
        company=st.text_input(
            "公司 · Company",
            key="shared_company",
            placeholder="例如：ABC Engineering Co., Ltd.",
        ),
        contact_information=st.text_input(
            "联系方式 · Contact Information",
            key="shared_contact_information",
            placeholder="例如：david.chen@example.com",
        ),
    )
    return TONE_OPTIONS[tone_label], country_region, recipient, sender


def _render_step_two(
    scenario: Scenario,
) -> None:
    total = len(scenario.fields)
    question_index = min(
        max(int(st.session_state.get("compose__question_index", 0)), 0),
        total - 1,
    )
    field = scenario.fields[question_index]
    editing = st.session_state.get("compose__edit_field_key") == field.key

    with st.container(key="compose__question_card"):
        render_guided_question_header(
            current=question_index + 1,
            total=total,
            title=field.label_zh,
            helper=field.help_text or f"{field.label_en} · 如不确定，可暂时留空。",
            required=field.required,
        )
        answer = _render_answer_input(field)

        error = str(st.session_state.get("compose__error", ""))
        if error:
            st.error(error)

        back_label = "取消修改" if editing else "← 上一步"
        next_label = "保存修改" if editing else (
            "进入确认" if question_index + 1 == total else "继续 →"
        )
        back_clicked, next_clicked = render_guided_action_bar(
            back_label=back_label,
            back_key="compose__question_back",
            next_label=next_label,
            next_key="compose__question_next",
        )
        skip_clicked = False
        if not field.required and not editing:
            skip_clicked = tertiary_action_button(
                "暂时跳过",
                key="compose__question_skip",
            )

    if back_clicked:
        if editing:
            return_to_compose_review()
        else:
            if answer.strip() or not field.required:
                save_compose_answer(
                    field.key,
                    answer,
                    completed=bool(answer.strip()) or not field.required,
                )
            back_compose_question()
        st.rerun()

    if skip_clicked:
        save_compose_answer(field.key, "", completed=True)
        advance_compose_question(total)
        st.rerun()

    if next_clicked:
        clean_answer = answer.strip()
        if field.required and not clean_answer:
            message = f"请先回答：{field.label_zh}。"
            st.session_state["compose__error"] = message
            st.rerun()
        save_compose_answer(field.key, clean_answer, completed=True)
        if editing:
            return_to_compose_review()
        else:
            advance_compose_question(total)
        st.rerun()


def _generate_from_review(
    scenario: Scenario,
    scenario_service: ScenarioService,
    *,
    facts: dict[str, str],
    tone: str,
    country_region: str,
    recipient: str,
    sender: SenderDetails,
) -> None:
    validation = validate_scenario_facts(scenario, facts)
    if not validation.is_valid:
        st.session_state["compose__error"] = validation.errors[0]
        st.error(validation.errors[0])
        return
    combined_facts = "\n".join(validation.cleaned_facts.values())
    custom_region = str(st.session_state.get("compose__custom_region", ""))
    guidance = build_localization_guidance(
        recipient=recipient,
        country_region=country_region,
        custom_region=custom_region,
        tone=tone,
        source_text=combined_facts,
    )
    st.session_state["compose__review_confirmed"] = True
    st.session_state["compose__fields"] = validation.cleaned_facts
    st.session_state["compose__request_in_progress"] = True
    started = time.perf_counter()
    try:
        render_loading_state(
            "正在生成商务邮件…",
            "正在根据您确认的信息整理邮件结构和商务表达。",
        )
        with st.spinner("正在整理事实并生成英文邮件…"):
            result = scenario_service.generate(
                scenario=scenario,
                facts=validation.cleaned_facts,
                tone=tone,
                sender=sender,
                recipient=recipient,
                country_region=country_region,
                localization_context=_localization_context(guidance),
            )
        duration = time.perf_counter() - started
        st.session_state["compose__result_subject"] = result.subject
        st.session_state["compose__result_body"] = result.body
        st.session_state["compose__analysis"] = result.communication_analysis
        st.session_state["compose__duration_seconds"] = duration
        st.session_state["compose__usage_tokens"] = result.usage_tokens
        st.session_state["compose__error"] = ""
        st.session_state["compose__step"] = 4
        st.session_state["deepseek_connected"] = True
        st.session_state["last_request_duration"] = duration
        st.session_state["last_usage_tokens"] = result.usage_tokens
        st.rerun()
    except AIServiceError as exc:
        st.session_state["compose__review_confirmed"] = False
        st.session_state["compose__error"] = exc.user_message
        st.error(exc.user_message)
    finally:
        st.session_state["compose__request_in_progress"] = False


def _save_generation_context(
    *,
    tone: str,
    country_region: str,
    recipient: str,
    sender: SenderDetails,
) -> None:
    """Keep UI-only generation settings available when returning from the result."""
    st.session_state["compose__ui_generation_context"] = {
        "tone": tone,
        "country_region": country_region,
        "recipient": recipient,
        "custom_region": str(st.session_state.get("compose__custom_region", "")),
        "sender": {
            "name": sender.name,
            "job_title": sender.job_title,
            "company": sender.company,
            "contact_information": sender.contact_information,
        },
    }


def _regenerate_from_saved_review(
    scenario: Scenario,
    scenario_service: ScenarioService,
) -> None:
    """Regenerate only after an explicit user action, using saved confirmed facts."""
    context = st.session_state.get("compose__ui_generation_context", {})
    if not isinstance(context, dict):
        st.session_state["compose__error"] = "请先返回信息确认后重新生成邮件。"
        st.rerun()
    st.session_state["compose__custom_region"] = str(
        context.get("custom_region", "")
    )
    sender_values = context.get("sender", {})
    if not isinstance(sender_values, dict):
        sender_values = {}
    _generate_from_review(
        scenario,
        scenario_service,
        facts=dict(st.session_state.get("compose__fields", {})),
        tone=str(context.get("tone", scenario.default_tone)),
        country_region=str(context.get("country_region", COUNTRY_REGION_OPTIONS[0])),
        recipient=str(context.get("recipient", "")),
        sender=SenderDetails(
            name=str(sender_values.get("name", "")),
            job_title=str(sender_values.get("job_title", "")),
            company=str(sender_values.get("company", "")),
            contact_information=str(sender_values.get("contact_information", "")),
        ),
    )


def _render_step_three(
    scenario: Scenario,
    scenario_service: ScenarioService,
) -> None:
    answers = dict(st.session_state.get("compose__answers", {}))
    validation = validate_scenario_facts(scenario, answers)
    render_section_header("邮件信息确认", "REVIEW")
    st.caption("生成前请核对事实。AI 只会使用下列已填写内容。")
    if not validation.is_valid:
        st.error(validation.errors[0])
        st.button(
            "返回补充信息",
            key="compose__review_fix_missing",
            on_click=edit_compose_answer,
            args=(
                scenario.required_fields[0].key,
                scenario.fields.index(scenario.required_fields[0]),
            ),
        )
        return

    fields_by_key = {field.key: (index, field) for index, field in enumerate(scenario.fields)}
    items = tuple(
        ReviewItem(key=key, label=fields_by_key[key][1].label_zh, value=value)
        for key, value in validation.cleaned_facts.items()
        if key in fields_by_key and value
    )
    with st.container(key="compose__summary_card"):
        selected_field = render_review_items(
            items,
            action_key_prefix="compose__review_edit__",
        )
    if selected_field:
        index, _ = fields_by_key[selected_field]
        edit_compose_answer(selected_field, index)
        st.rerun()

    with st.expander(
        "高级选项 · Tone, Region, Recipient & Signature",
        expanded=False,
    ):
        tone, country_region, recipient, sender = _render_advanced(scenario)

    combined_facts = "\n".join(validation.cleaned_facts.values())
    risk = analyze_content_risk(combined_facts)
    if risk.risk_level == "high":
        st.error(risk.summary)
        risk_confirmed = st.checkbox(
            "我已检查并确认这些内容可以提交给 AI。",
            key="compose__risk_confirmed",
        )
    else:
        risk_confirmed = True

    error = str(st.session_state.get("compose__error", ""))
    if error:
        st.error(error)

    back, generate = st.columns((1, 1.7), gap="small")
    with back:
        back_clicked = secondary_action_button("← 返回修改", key="compose__review_back")
    with generate:
        generate_clicked = primary_action_button(
            "生成英文邮件",
            key="compose__generate",
            disabled=bool(st.session_state["compose__request_in_progress"]),
        )
    if back_clicked:
        edit_compose_answer(scenario.fields[-1].key, len(scenario.fields) - 1)
        st.rerun()
    if not generate_clicked:
        return
    if not risk_confirmed:
        st.session_state["compose__error"] = (
            "检测到高风险内容，请人工检查并确认后再提交。"
        )
        st.rerun()
    if st.session_state["compose__request_in_progress"]:
        st.warning("邮件正在生成，请勿重复提交。")
        return
    _save_generation_context(
        tone=tone,
        country_region=country_region,
        recipient=recipient,
        sender=sender,
    )
    _generate_from_review(
        scenario,
        scenario_service,
        facts=validation.cleaned_facts,
        tone=tone,
        country_region=country_region,
        recipient=recipient,
        sender=sender,
    )


def _render_step_four(
    scenario: Scenario,
    scenario_service: ScenarioService,
) -> None:
    render_section_header("邮件已生成", "EMAIL READY")
    st.caption("可以在复制前直接修改主题和正文。")
    subject = render_email_subject_card(
        value_key="compose__result_subject",
        on_change=lambda: None,
    )
    body = render_email_editor(
        value_key="compose__result_body",
        on_change=lambda: None,
    )
    render_copy_button(
        label="复制完整邮件",
        value=f"Subject: {subject}\n\n{body}",
        key="compose__copy_full_email",
        primary=True,
    )

    duration = st.session_state.get("compose__duration_seconds")
    tokens = st.session_state.get("compose__usage_tokens")
    status_parts = ["AI 服务：DeepSeek", "状态：连接成功"]
    if isinstance(duration, (int, float)):
        status_parts.append(f"本次生成耗时：{duration:.2f} 秒")
    if isinstance(tokens, int):
        status_parts.append(f"本次用量：{tokens} tokens")
    st.markdown(f'<div class="la-create-status">{" · ".join(status_parts)}</div>', unsafe_allow_html=True)

    analysis = st.session_state.get("compose__analysis")
    if not isinstance(analysis, CommunicationAnalysis):
        analysis = CommunicationAnalysis()

    with st.expander("沟通建议", expanded=False):
        st.markdown(f"**沟通目的**：{analysis.purpose}")
        st.markdown(f"**行动要求**：{analysis.action_required}")
        st.markdown(f"**截止时间**：{analysis.deadline}")
        st.markdown(f"**商务语气**：{analysis.tone}")

    facts = st.session_state.get("compose__fields", {})
    combined_facts = "\n".join(
        str(value) for value in facts.values()
    ) if isinstance(facts, dict) else ""
    risk = analyze_content_risk(combined_facts)
    with st.expander("风险提示 · Risk Guidance", expanded=False):
        if risk.risk_items:
            for item in risk.risk_items:
                st.markdown(
                    f"- **{item.category}**：{item.description} {item.suggestion}"
                )
        else:
            st.write(risk.summary)
        st.caption(ADVISORY_NOTICE)

    recipient = str(st.session_state.get("compose__recipient", ""))
    country_region = str(
        st.session_state.get(
            "compose__country_region",
            COUNTRY_REGION_OPTIONS[0],
        )
    )
    tone = TONE_OPTIONS.get(
        str(st.session_state.get("compose__tone_choice", "正式 · Formal")),
        scenario.default_tone,
    )
    guidance = build_localization_guidance(
        recipient=recipient,
        country_region=country_region,
        custom_region=str(st.session_state.get("compose__custom_region", "")),
        tone=tone,
        source_text=combined_facts,
    )
    with st.expander("本地化建议 · Localization Guidance", expanded=False):
        st.markdown(f"**推荐称谓**：{guidance.recommended_salutation}")
        st.markdown(f"**称谓风险**：{guidance.salutation_risk}")
        st.markdown(f"**礼貌程度**：{guidance.politeness_guidance}")
        st.markdown(f"**跨文化提醒**：{guidance.cross_cultural_note}")

    with st.expander("发送前检查 · Pre-send Review", expanded=False):
        st.markdown(
            "- 核对供应商名称、日期、项目和行动要求。\n"
            "- 确认正文没有加入未授权的承诺或责任。\n"
            "- 检查收件人、附件及回复时限是否正确。\n"
            "- 生成结果仅供辅助，发送前请人工确认。"
        )
        if analysis.improvement_suggestions:
            st.markdown("**建议进一步检查**")
            for suggestion in analysis.improvement_suggestions:
                st.markdown(f"- {suggestion}")

    actions = st.columns((1, 1), gap="small")
    with actions[0]:
        regenerate_clicked = secondary_action_button(
            "重新生成",
            key="compose__regenerate",
            disabled=bool(st.session_state["compose__request_in_progress"]),
        )
    with actions[1]:
        return_clicked = tertiary_action_button(
            "返回修改信息",
            key="compose__edit_information",
        )
    if return_clicked:
        set_compose_step(3)
        st.rerun()
    if regenerate_clicked:
        _regenerate_from_saved_review(scenario, scenario_service)


def render_create_workspace(
    *,
    scenario_service: ScenarioService,
    service_status: str,
    render_privacy_notice: Callable[[], None] | None = None,
) -> None:
    step = int(st.session_state.get("compose__step", 1))
    task_id = str(st.session_state.get("compose__task_id", ""))
    scenario = get_supplier_scenario(task_id) if task_id else None

    def render_task() -> None:
        error = str(st.session_state.get("compose__error", ""))
        if error and step != 2:
            st.error(error)

        if step == 1:
            _render_step_one()
        elif step == 2 and scenario:
            _render_step_two(scenario)
        elif step == 3 and scenario:
            _render_step_three(scenario, scenario_service)
        elif step == 4 and scenario:
            _render_step_four(scenario, scenario_service)
        else:
            st.session_state["compose__step"] = 1
            st.warning("任务状态已重置，请重新选择供应商任务。")

        if render_privacy_notice:
            with st.expander("隐私与测试说明", expanded=False):
                render_privacy_notice()

    render_workspace_shell(
        workspace_key="create",
        version=APP_VERSION_LABEL,
        service_status=service_status,
        title="创建商务邮件",
        description="Create Email Workspace · 选择商务任务，Leon AI 会一步步帮助你完成邮件。",
        eyebrow="LEON AI · CREATE EMAIL",
        steps=_workflow_steps(step),
        render_task=render_task,
        on_return_home=return_to_home,
    )


def render_supplier_workflow(
    *,
    scenario_service: ScenarioService,
    service_status: str = "已配置",
    render_privacy_notice: Callable[[], None] | None = None,
) -> None:
    """Legacy-compatible entry that renders the same Create Workspace experience."""
    render_create_workspace(
        scenario_service=scenario_service,
        service_status=service_status,
        render_privacy_notice=render_privacy_notice,
    )
