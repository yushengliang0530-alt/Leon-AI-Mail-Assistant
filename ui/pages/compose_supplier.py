"""Four-step guided supplier workflow driven by Scenario configuration."""

import base64
import html
import json
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


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
        .st-key-compose__workspace {
            --compose-ink:#13223a;
            --compose-blue:#2858c7;
            --compose-line:#d9e1ec;
            --compose-muted:#66758a;
        }
        .st-key-compose__workspace .compose-header {
            display:flex;justify-content:space-between;align-items:flex-start;
            gap:1rem;margin:.45rem 0 1.3rem;padding-bottom:1.1rem;
            border-bottom:1px solid var(--compose-line);
        }
        .st-key-compose__workspace .compose-kicker {
            color:var(--compose-blue);font-size:.7rem;font-weight:760;
            letter-spacing:.11em;text-transform:uppercase;
        }
        .st-key-compose__workspace .compose-header h1 {
            margin:.35rem 0 .25rem;color:var(--compose-ink);
            font-size:clamp(1.65rem,4vw,2.35rem);line-height:1.15;
            letter-spacing:-.035em;
        }
        .st-key-compose__workspace .compose-header p {
            margin:0;color:var(--compose-muted);font-size:.82rem;
        }
        .st-key-compose__workspace .compose-current {
            flex:none;padding:.42rem .65rem;border:1px solid #cbd7e8;
            border-radius:999px;background:#f8faff;color:#425978;
            font-size:.68rem;font-weight:730;
        }
        .st-key-compose__workspace .compose-progress {
            display:grid;grid-template-columns:repeat(4,1fr);
            margin:0 0 1.55rem;border:1px solid var(--compose-line);
            border-radius:.8rem;overflow:hidden;background:#fff;
        }
        .st-key-compose__workspace .compose-progress span {
            padding:.72rem .8rem;border-right:1px solid var(--compose-line);
            color:#8793a4;font-size:.76rem;font-weight:680;
        }
        .st-key-compose__workspace .compose-progress span:last-child {
            border-right:0;
        }
        .st-key-compose__workspace .compose-progress .active {
            background:#eef3ff;color:var(--compose-blue);
        }
        .st-key-compose__workspace .compose-progress .done {
            color:#315f4d;background:#f4faf7;
        }
        .st-key-compose__workspace .compose-section-title {
            margin:1.15rem 0 .25rem;color:var(--compose-ink);
            font-size:1.12rem;font-weight:760;
        }
        .st-key-compose__workspace .compose-section-help {
            margin:0 0 1rem;color:var(--compose-muted);font-size:.82rem;
        }
        .st-key-compose__workspace .st-key-compose__question_card {
            max-width:42rem;margin:1.3rem auto;padding:1.65rem 1.75rem 1.4rem;
            border:1px solid var(--compose-line);border-radius:1rem;background:#fff;
            box-shadow:0 12px 34px rgba(28,48,79,.06);
        }
        .st-key-compose__workspace .compose-question-count {
            margin-bottom:.75rem;color:var(--compose-blue);
            font-size:.7rem;font-weight:750;letter-spacing:.08em;
            text-transform:uppercase;
        }
        .st-key-compose__workspace .compose-question-card h2 {
            margin:0 0 .35rem;color:var(--compose-ink);
            font-size:clamp(1.3rem,3vw,1.7rem);line-height:1.25;
            letter-spacing:-.025em;
        }
        .st-key-compose__workspace .compose-question-en {
            margin-bottom:.9rem;color:#8995a6;font-size:.76rem;font-weight:540;
        }
        .st-key-compose__workspace .compose-question-help {
            margin:0 0 1rem;color:var(--compose-muted);
            font-size:.8rem;line-height:1.55;
        }
        .st-key-compose__workspace .compose-required {
            margin-left:.3rem;color:#b14848;font-size:.66rem;font-weight:650;
        }
        .st-key-compose__workspace .st-key-compose__task__supplier_quotation button,
        .st-key-compose__workspace .st-key-compose__task__supplier_delivery button,
        .st-key-compose__workspace .st-key-compose__task__supplier_plan_update button,
        .st-key-compose__workspace .st-key-compose__task__supplier_delay_explanation button {
            min-height:6.3rem;justify-content:flex-start;text-align:left;
            white-space:normal;border-color:var(--compose-line);
            border-radius:.8rem;background:#fff;color:var(--compose-ink);
        }
        .st-key-compose__workspace div[data-testid="stButton"] > button p {
            width:100%;text-align:left;
        }
        .st-key-compose__workspace .st-key-compose__question_card div[data-testid="stButton"] > button p,
        .st-key-compose__workspace .st-key-compose__summary_card div[data-testid="stButton"] > button p {
            text-align:center;
        }
        .st-key-compose__workspace .st-key-compose__summary_card {
            margin:1rem 0 1.15rem;padding:.35rem 1.2rem;
            border:1px solid var(--compose-line);border-radius:.9rem;background:#fff;
            box-shadow:0 10px 28px rgba(28,48,79,.05);
        }
        .st-key-compose__workspace .compose-summary-row {
            display:grid;grid-template-columns:minmax(7.5rem,.65fr) 2fr;
            gap:1rem;padding:.85rem 0;border-bottom:1px solid #e8edf4;
        }
        .st-key-compose__workspace .compose-summary-row:last-child {
            border-bottom:0;
        }
        .st-key-compose__workspace .compose-summary-label {
            color:#708097;font-size:.72rem;font-weight:680;
        }
        .st-key-compose__workspace .compose-summary-value {
            color:#263955;font-size:.84rem;line-height:1.5;
        }
        .st-key-compose__workspace .compose-analysis-grid {
            display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.6rem;
        }
        .st-key-compose__workspace .compose-analysis-item {
            padding:.75rem .8rem;border:1px solid var(--compose-line);
            border-radius:.65rem;background:#fff;
        }
        .st-key-compose__workspace .compose-analysis-item b {
            display:block;margin-bottom:.18rem;color:#64758c;font-size:.68rem;
        }
        .st-key-compose__workspace .compose-analysis-item span {
            color:#263955;font-size:.8rem;line-height:1.5;
        }
        @media (max-width:640px) {
            .st-key-compose__workspace {overflow-x:hidden;}
            .st-key-compose__workspace .compose-header {
                flex-direction:column;
            }
            .st-key-compose__workspace .compose-progress span {
                padding:.65rem .45rem;font-size:.7rem;text-align:center;
            }
            .st-key-compose__workspace div[data-testid="stHorizontalBlock"] {
                flex-direction:column;gap:.5rem;
            }
            .st-key-compose__workspace div[data-testid="column"] {
                width:100% !important;flex:1 1 100% !important;
            }
            .st-key-compose__workspace .compose-analysis-grid {
                grid-template-columns:1fr;
            }
            .st-key-compose__workspace .st-key-compose__question_card {
                margin:1rem 0;padding:1.25rem 1rem;
            }
            .st-key-compose__workspace .compose-summary-row {
                grid-template-columns:1fr;gap:.25rem;
            }
            .st-key-compose__workspace div[data-testid="stButton"] > button {
                min-height:44px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _progress(step: int) -> None:
    labels = ("① 场景", "② 问答", "③ 确认", "④ 邮件")
    items = "".join(
        f'<span class="{"active" if number == step else "done" if number < step else ""}">'
        f"{label}</span>"
        for number, label in enumerate(labels, start=1)
    )
    st.markdown(
        f'<div class="compose-progress">{items}</div>',
        unsafe_allow_html=True,
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


def _copy_button(label: str, value: str, key: str) -> None:
    encoded = base64.b64encode(value.encode("utf-8")).decode("ascii")
    st.iframe(
        f"""
        <button id="{html.escape(key)}" onclick="copyValue()" style="
          width:100%;height:40px;border:1px solid #d7e0eb;border-radius:9px;
          background:#fff;color:#263955;font:600 13px -apple-system,
          BlinkMacSystemFont,'Segoe UI',sans-serif;cursor:pointer">
          {html.escape(label)}
        </button>
        <script>
        async function copyValue() {{
          const button = document.getElementById({json.dumps(key)});
          try {{
            const bytes = Uint8Array.from(
              atob({json.dumps(encoded)}), c => c.charCodeAt(0));
            await navigator.clipboard.writeText(new TextDecoder().decode(bytes));
            button.textContent = "已复制";
          }} catch (error) {{
            button.textContent = "复制失败，请手动复制";
          }}
        }}
        </script>
        """,
        height=46,
        width="stretch",
    )


def _render_analysis(analysis: CommunicationAnalysis) -> None:
    rows = (
        ("沟通目的", analysis.purpose),
        ("行动要求", analysis.action_required),
        ("截止时间", analysis.deadline),
        ("商务语气", analysis.tone),
        ("承诺风险", analysis.commitment_risk),
        ("歧义风险", analysis.ambiguity_risk),
    )
    cards = "".join(
        (
            '<div class="compose-analysis-item">'
            f"<b>{html.escape(label)}</b><span>{html.escape(value)}</span></div>"
        )
        for label, value in rows
    )
    st.markdown(
        f'<div class="compose-analysis-grid">{cards}</div>',
        unsafe_allow_html=True,
    )


def _render_step_one() -> None:
    st.markdown(
        '<div class="compose-section-title">请选择供应商任务</div>'
        '<p class="compose-section-help">选择最接近当前工作的任务，下一步只填写相关事实。</p>',
        unsafe_allow_html=True,
    )
    rows = (SUPPLIER_SCENARIOS[:2], SUPPLIER_SCENARIOS[2:])
    for row in rows:
        columns = st.columns(2)
        for column, scenario in zip(columns, row, strict=True):
            with column:
                st.button(
                    f"**{scenario.title_zh}**  \n"
                    f"{scenario.title_en}  \n\n{scenario.description}",
                    key=f"compose__task__{scenario.id}",
                    use_container_width=True,
                    on_click=set_compose_task,
                    args=(scenario.id,),
                )


def _render_advanced(scenario: Scenario) -> tuple[str, str, str, SenderDetails]:
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
    required_note = "必填问题" if field.required else "可选问题"

    with st.container(border=True, key="compose__question_card"):
        st.markdown(
            (
                f'<div class="compose-question-count">{html.escape(scenario.title_zh)}'
                f" · 问题 {question_index + 1} / {total} · {required_note}</div>"
                f"<h2>{html.escape(field.label_zh)}？</h2>"
                f'<div class="compose-question-en">{html.escape(field.label_en)}</div>'
            ),
            unsafe_allow_html=True,
        )
        if field.help_text:
            st.markdown(
                f'<p class="compose-question-help">{html.escape(field.help_text)}</p>',
                unsafe_allow_html=True,
            )
        answer = _render_answer_input(field)

        error = str(st.session_state.get("compose__error", ""))
        if error:
            st.error(error)

        left, middle, right = st.columns((1, 1, 1.35))
        with left:
            back_label = "取消修改" if editing else "Back · 上一题"
            back_clicked = st.button(
                back_label,
                key="compose__question_back",
                use_container_width=True,
            )
        with middle:
            skip_clicked = False
            if not field.required and not editing:
                skip_clicked = st.button(
                    "暂时跳过",
                    key="compose__question_skip",
                    use_container_width=True,
                )
        with right:
            next_label = "保存修改" if editing else (
                "进入确认" if question_index + 1 == total else "Next · 下一题"
            )
            next_clicked = st.button(
                next_label,
                key="compose__question_next",
                type="primary",
                use_container_width=True,
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


def _render_step_three(
    scenario: Scenario,
    scenario_service: ScenarioService,
) -> None:
    answers = dict(st.session_state.get("compose__answers", {}))
    validation = validate_scenario_facts(scenario, answers)
    st.markdown(
        '<div class="compose-section-title">本次商务沟通信息</div>'
        '<p class="compose-section-help">生成前请核对事实。AI只会使用下列已填写内容。</p>',
        unsafe_allow_html=True,
    )
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

    with st.container(border=True, key="compose__summary_card"):
        for index, field in enumerate(scenario.fields):
            value = validation.cleaned_facts.get(field.key)
            if not value:
                continue
            content, action = st.columns((5, 1))
            with content:
                st.markdown(
                    (
                        f'<div class="compose-summary-label">{html.escape(field.label_zh)}</div>'
                        f'<div class="compose-summary-value">{html.escape(value)}</div>'
                    ),
                    unsafe_allow_html=True,
                )
            with action:
                st.button(
                    "修改",
                    key=f"compose__review_edit__{field.key}",
                    on_click=edit_compose_answer,
                    args=(field.key, index),
                )

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

    back, generate = st.columns((1, 1.7))
    with back:
        st.button(
            "返回继续修改",
            key="compose__review_back",
            use_container_width=True,
            on_click=edit_compose_answer,
            args=(
                scenario.fields[-1].key,
                len(scenario.fields) - 1,
            ),
        )
    with generate:
        generate_clicked = st.button(
            "生成英文邮件",
            key="compose__generate",
            type="primary",
            use_container_width=True,
            disabled=bool(st.session_state["compose__request_in_progress"]),
        )
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
    _generate_from_review(
        scenario,
        scenario_service,
        facts=validation.cleaned_facts,
        tone=tone,
        country_region=country_region,
        recipient=recipient,
        sender=sender,
    )


def _render_step_four(scenario: Scenario) -> None:
    st.markdown(
        '<div class="compose-section-title">您的英文邮件</div>'
        '<p class="compose-section-help">可以在复制前直接修改主题和正文。</p>',
        unsafe_allow_html=True,
    )
    subject = st.text_input(
        "邮件主题 · Subject",
        key="compose__result_subject",
    )
    body = st.text_area(
        "邮件正文 · Email Body",
        key="compose__result_body",
        height=300,
    )
    copy_columns = st.columns(2)
    with copy_columns[0]:
        _copy_button("复制主题 · Copy Subject", subject, "compose-copy-subject")
    with copy_columns[1]:
        _copy_button("复制正文 · Copy Body", body, "compose-copy-body")

    duration = st.session_state.get("compose__duration_seconds")
    tokens = st.session_state.get("compose__usage_tokens")
    status_parts = ["AI 服务：DeepSeek", "状态：连接成功"]
    if isinstance(duration, (int, float)):
        status_parts.append(f"本次生成耗时：{duration:.2f} 秒")
    if isinstance(tokens, int):
        status_parts.append(f"本次用量：{tokens} tokens")
    st.caption(" · ".join(status_parts))

    analysis = st.session_state.get("compose__analysis")
    if not isinstance(analysis, CommunicationAnalysis):
        analysis = CommunicationAnalysis()

    st.markdown("#### 商务沟通分析")
    _render_analysis(analysis)

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

    with st.expander("发送前检查 · Pre-send Review", expanded=True):
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

    action_columns = st.columns(2)
    with action_columns[0]:
        st.button(
            "← 返回信息确认",
            key="compose__edit_information",
            use_container_width=True,
            on_click=set_compose_step,
            args=(3,),
        )
    with action_columns[1]:
        st.button(
            "返回工作台",
            key="compose__finish",
            use_container_width=True,
            on_click=return_to_home,
        )


def render_supplier_workflow(
    *,
    scenario_service: ScenarioService,
    render_privacy_notice: Callable[[], None] | None = None,
) -> None:
    _inject_styles()
    step = int(st.session_state.get("compose__step", 1))
    task_id = str(st.session_state.get("compose__task_id", ""))
    scenario = get_supplier_scenario(task_id) if task_id else None

    with st.container(key="compose__workspace"):
        st.button(
            "← 返回工作台",
            key="compose__return_home",
            on_click=return_to_home,
        )
        current = (
            f"{scenario.title_en}" if scenario else "Follow Up Supplier"
        )
        st.markdown(
            f"""
            <div class="compose-header">
              <div>
                <div class="compose-kicker">LEON AI · SCENARIO WORKFLOW</div>
                <h1>催供应商</h1>
                <p>Follow Up Supplier · 只填写必要事实，不需要编写 Prompt。</p>
              </div>
              <div class="compose-current">当前：{html.escape(current)} · {step}/4</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        _progress(step)

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
            _render_step_four(scenario)
        else:
            st.session_state["compose__step"] = 1
            st.warning("任务状态已重置，请重新选择供应商任务。")

        if render_privacy_notice:
            with st.expander("隐私与测试说明", expanded=False):
                render_privacy_notice()
