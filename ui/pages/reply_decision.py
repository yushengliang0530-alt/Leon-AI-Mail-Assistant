"""Guided local stance confirmation rendered inside the Reply workspace."""

import streamlit as st

from content_risk_service import ADVISORY_NOTICE, analyze_content_risk
from models.reply_decision import ReplyDecision, ReplyItem
from services.reply_item_service import (
    STANCE_LABELS,
    build_decision_summary,
    decision_digest,
    decision_publishable_text,
    validate_decision,
)
from ui.components import (
    DecisionOption,
    DecisionSummaryEntry,
    render_decision_focus_card,
    render_decision_option_cards,
    render_decision_summary_cards,
    render_guided_action_bar,
    render_notice_bar,
    render_section_header,
    render_status_badge,
    secondary_action_button,
    tertiary_action_button,
)
from ui.state import (
    clear_reply_decisions,
    return_to_reply_analysis,
    return_to_reply_decisions,
    set_reply_item_index,
)


STANCE_CARD_OPTIONS = (
    DecisionOption("accept", "可以确认", "已核实，可以明确回复"),
    DecisionOption("partial", "部分确认", "区分可确认与待核实的部分"),
    DecisionOption("unable_to_confirm", "暂时无法确认", "说明尚需内部核实"),
    DecisionOption("request_info", "需要更多信息", "请对方补充必要信息"),
    DecisionOption("decline", "无法同意", "说明原因或提出替代方案"),
    DecisionOption("no_response", "无需回复", "明确不在本次邮件中回应"),
    DecisionOption("custom", "自定义", "按您的处理方式说明"),
)


def _invalidate_generated_reply() -> None:
    for key in (
        "reply__generated_email",
        "reply__coverage",
        "reply__generation_duration",
        "reply__coverage_duration",
        "reply__generation_tokens",
        "reply__coverage_tokens",
    ):
        st.session_state[key] = None
    for key in (
        "reply__subject",
        "reply__body",
        "reply__presentation_subject",
        "reply__presentation_body",
        "reply__summary",
        "reply__generation_digest",
        "reply__coverage_digest",
        "reply__generation_error",
        "reply__coverage_error",
    ):
        st.session_state[key] = ""
    st.session_state["reply__generation_status"] = "idle"
    st.session_state["reply__coverage_status"] = "idle"


def _clear_decision_error() -> None:
    st.session_state["reply__decision_error"] = ""


def _widget_key(item_id: str, field: str) -> str:
    epoch = int(st.session_state.get("reply__decision_widget_epoch", 0))
    return f"reply__decision_widget__{item_id}__{epoch}__{field}"


def _existing(item_id: str) -> dict:
    decisions = st.session_state.get("reply__decisions", {})
    return dict(decisions.get(item_id, {}))


def _seed_widgets(item: ReplyItem) -> None:
    existing = _existing(item.item_id)
    defaults = ReplyDecision(
        item_id=item.item_id,
        stance="",
        uncertain=item.uncertain,
    ).to_dict()
    defaults.update(existing)
    for field, value in defaults.items():
        if field == "item_id":
            continue
        key = _widget_key(item.item_id, field)
        if key not in st.session_state:
            st.session_state[key] = value


def _read_decision(item: ReplyItem) -> ReplyDecision:
    def value(field: str, default=""):
        return st.session_state.get(
            _widget_key(item.item_id, field), default
        )

    stance = str(value("stance")).strip()
    return ReplyDecision(
        item_id=item.item_id,
        stance=stance,
        confirmed_facts=str(value("confirmed_facts")).strip(),
        accepted_part=str(value("accepted_part")).strip(),
        declined_part=str(value("declined_part")).strip(),
        reason=str(value("reason")).strip(),
        alternative=str(value("alternative")).strip(),
        requested_information=str(
            value("requested_information")
        ).strip(),
        next_update_time=str(value("next_update_time")).strip(),
        custom_instruction=str(value("custom_instruction")).strip(),
        include_in_reply=bool(value("include_in_reply", True)),
        user_notes=str(value("user_notes")).strip(),
        uncertain=item.uncertain,
        no_response_confirmed=bool(
            value("no_response_confirmed", False)
        ),
    )


def _save_decision(item: ReplyItem) -> bool:
    decision = _read_decision(item)
    validation = validate_decision(item, decision)
    if not validation.valid:
        st.session_state["reply__decision_error"] = "\n".join(
            validation.errors
        )
        return False
    decisions = dict(st.session_state.get("reply__decisions", {}))
    serialized = decision.to_dict()
    if decisions.get(item.item_id) != serialized:
        decisions[item.item_id] = serialized
        st.session_state["reply__decisions"] = decisions
        st.session_state["reply__decision_digest"] = decision_digest(
            decisions
        )
        st.session_state["reply__decision_risk"] = None
        st.session_state["reply__decision_risk_confirmed_digest"] = ""
        st.session_state["reply__decision_summary"] = None
        _invalidate_generated_reply()
    st.session_state["reply__decision_error"] = ""
    return True


def _clear_current(item_id: str) -> None:
    decisions = dict(st.session_state.get("reply__decisions", {}))
    decisions.pop(item_id, None)
    st.session_state["reply__decisions"] = decisions
    st.session_state["reply__decision_digest"] = decision_digest(decisions)
    st.session_state["reply__decision_risk"] = None
    st.session_state["reply__decision_risk_confirmed_digest"] = ""
    st.session_state["reply__decision_summary"] = None
    _invalidate_generated_reply()
    st.session_state["reply__decision_error"] = ""
    prefix = f"reply__decision_widget__{item_id}__"
    for key in tuple(st.session_state):
        if key.startswith(prefix):
            del st.session_state[key]


def _render_stance_fields(item: ReplyItem) -> None:
    stance_key = _widget_key(item.item_id, "stance")
    selected = st.session_state.get(stance_key, "")
    epoch = int(st.session_state.get("reply__decision_widget_epoch", 0))
    chosen = render_decision_option_cards(
        STANCE_CARD_OPTIONS,
        selected=selected,
        key_prefix=f"reply__decision_option__{item.item_id}__{epoch}",
    )
    if chosen:
        st.session_state[stance_key] = chosen
        selected = chosen
        _clear_decision_error()
    if not selected:
        render_notice_bar(
            "请选择处理立场",
            "Leon AI 不会替您默认接受、承诺或拒绝任何事项。",
        )
        return

    if selected == "accept":
        st.text_area(
            "可以确认的行动或事实（必填）",
            key=_widget_key(item.item_id, "confirmed_facts"),
            placeholder="只填写已经确认、可以对外表达的内容。",
        )
        st.text_input(
            "确认日期或下一时间点（可选）",
            key=_widget_key(item.item_id, "next_update_time"),
            placeholder="没有确定日期时请留空。",
        )
    elif selected == "partial":
        st.text_area(
            "可以接受或确认的部分（必填）",
            key=_widget_key(item.item_id, "accepted_part"),
        )
        st.text_area(
            "不能接受或尚无法确认的部分（必填）",
            key=_widget_key(item.item_id, "declined_part"),
        )
        st.text_area(
            "可以对外说明的原因（可选）",
            key=_widget_key(item.item_id, "reason"),
        )
        st.text_area(
            "替代方案（可选）",
            key=_widget_key(item.item_id, "alternative"),
        )
    elif selected == "decline":
        st.text_area(
            "可以对外说明的原因（必填）",
            key=_widget_key(item.item_id, "reason"),
        )
        st.text_area(
            "替代方案或下一步（可选）",
            key=_widget_key(item.item_id, "alternative"),
        )
        st.text_area(
            "内部审批或核实备注（仅内部使用，可选）",
            key=_widget_key(item.item_id, "user_notes"),
        )
    elif selected == "request_info":
        st.text_area(
            "需要对方补充什么信息（必填）",
            key=_widget_key(item.item_id, "requested_information"),
        )
        st.text_area(
            "为什么需要这些信息（可选）",
            key=_widget_key(item.item_id, "reason"),
        )
        st.text_area(
            "收到信息后可以确认什么（可选）",
            key=_widget_key(item.item_id, "confirmed_facts"),
        )
    elif selected == "unable_to_confirm":
        st.text_area(
            "暂时无法确认的原因（必填）",
            key=_widget_key(item.item_id, "reason"),
        )
        st.text_area(
            "需要内部核实的事项（可选）",
            key=_widget_key(item.item_id, "user_notes"),
        )
        st.text_input(
            "预计下次更新时间（可选）",
            key=_widget_key(item.item_id, "next_update_time"),
            placeholder="尚无可靠日期时请留空。",
        )
    elif selected == "no_response":
        render_notice_bar(
            "此事项不会写入回复",
            "请确认这是有意的处理选择；稍后仍会在完整性检查中提示您。",
        )
        st.checkbox(
            "我确认不在后续回复中回应此事项。",
            key=_widget_key(item.item_id, "no_response_confirmed"),
        )
        st.session_state[_widget_key(item.item_id, "include_in_reply")] = False
        st.text_area(
            "不回复的内部原因（可选，不会写入邮件）",
            key=_widget_key(item.item_id, "user_notes"),
        )
    elif selected == "custom":
        st.text_area(
            "自定义处理指令（必填）",
            key=_widget_key(item.item_id, "custom_instruction"),
            placeholder="说明希望后续回复如何处理这一事项。",
        )


def _render_overview(
    items: tuple[ReplyItem, ...], current_index: int
) -> None:
    with st.expander("查看全部事项", expanded=False):
        decisions = st.session_state.get("reply__decisions", {})
        for index, item in enumerate(items):
            decision = decisions.get(item.item_id)
            state = (
                STANCE_LABELS.get(decision.get("stance"), "已填写")
                if decision
                else ("待确认" if item.required else "可跳过")
            )
            marker = "当前" if index == current_index else state
            st.markdown(
                f"**{index + 1}. {item.description}**  \n{marker}"
            )


def _try_finish(items: tuple[ReplyItem, ...]) -> None:
    decisions = dict(st.session_state.get("reply__decisions", {}))
    summary = build_decision_summary(items, decisions)
    if summary.undecided:
        first = items.index(summary.undecided[0])
        set_reply_item_index(first)
        st.session_state["reply__decision_error"] = (
            "仍有必须回复的事项尚未完成，请先确认当前事项。"
        )
        st.rerun()

    digest = decision_digest(decisions)
    risk = analyze_content_risk(decision_publishable_text(decisions))
    st.session_state["reply__decision_risk"] = risk
    if risk.requires_confirmation and st.session_state.get(
        "reply__decision_risk_confirmed_digest"
    ) != digest:
        st.session_state["reply__decision_error"] = (
            "决策内容包含高风险信息，请核对并确认后再查看摘要。"
        )
        st.rerun()
    st.session_state["reply__decision_summary"] = summary
    st.session_state["reply__decision_digest"] = digest
    st.session_state["reply__decision_error"] = ""
    st.session_state["reply__step"] = 3
    st.rerun()


def render_reply_decisions(items: tuple[ReplyItem, ...]) -> None:
    if not items:
        st.warning("本次分析没有识别出可逐项确认的要求或问题。")
        st.button(
            "返回分析结果",
            key="reply__decision_empty_back",
            on_click=return_to_reply_analysis,
        )
        return
    index = min(
        int(st.session_state.get("reply__current_item_index", 0)),
        len(items) - 1,
    )
    item = items[index]
    _seed_widgets(item)
    render_section_header("逐项确认回复立场", f"事项 {index + 1} / {len(items)}")
    st.caption("每次只处理一个事项；回复只会使用您确认的立场和事实。")
    render_decision_focus_card(
        index=index + 1,
        total=len(items),
        title=item.description,
        deadline=item.deadline,
        required=item.required,
        uncertain=item.uncertain,
    )
    st.markdown("#### 选择您的处理立场")
    _render_stance_fields(item)

    error = str(st.session_state.get("reply__decision_error", ""))
    if error:
        st.error(error)

    risk = st.session_state.get("reply__decision_risk")
    digest = decision_digest(
        dict(st.session_state.get("reply__decisions", {}))
    )
    if risk is not None and risk.requires_confirmation:
        with st.expander("决策内容风险提醒", expanded=True):
            render_notice_bar("需要确认", risk.summary, icon="!")
            for risk_item in risk.risk_items:
                st.markdown(
                    f"**{risk_item.category}**：{risk_item.description}  \n"
                    f"建议：{risk_item.suggestion}"
                )
            confirmed = st.checkbox(
                "我已核对风险，确认保留当前决策内容。",
                key="reply__decision_risk_confirmed",
            )
            if confirmed:
                st.session_state[
                    "reply__decision_risk_confirmed_digest"
                ] = digest
            st.caption(ADVISORY_NOTICE)

    button_label = "查看回复决策" if index == len(items) - 1 else "保存并继续 →"
    back_clicked, next_clicked = render_guided_action_bar(
        back_label="← 上一项" if index else "← 返回分析",
        back_key=f"reply__decision_back__{item.item_id}",
        next_label=button_label,
        next_key=f"reply__decision_next__{item.item_id}",
    )
    if back_clicked:
        if index == 0:
            return_to_reply_analysis()
        else:
            set_reply_item_index(index - 1)
        st.rerun()
    if next_clicked:
        if not _save_decision(item):
            st.rerun()
        if index == len(items) - 1:
            _try_finish(items)
        else:
            set_reply_item_index(index + 1)
            st.rerun()

    if tertiary_action_button(
        "清除此项",
        key=f"reply__decision_clear__{item.item_id}",
    ):
        _clear_current(item.item_id)
        st.rerun()

    if not item.required:
        if st.button(
            "跳过此可选事项",
            key=f"reply__decision_skip__{item.item_id}",
            use_container_width=True,
        ):
            _clear_current(item.item_id)
            if index == len(items) - 1:
                _try_finish(items)
            else:
                set_reply_item_index(index + 1)
                st.rerun()

    _render_overview(items, index)
    st.button(
        "清空全部回复决策",
        key="reply__decision_clear_all",
        on_click=clear_reply_decisions,
    )


def _summary_entries(
    items: tuple[ReplyItem, ...], decisions: dict[str, dict]
) -> tuple[DecisionSummaryEntry, ...]:
    entries: list[DecisionSummaryEntry] = []
    kinds = {
        "accept": "success",
        "partial": "warning",
        "unable_to_confirm": "info",
        "request_info": "warning",
        "decline": "risk",
        "no_response": "info",
        "custom": "info",
    }
    for number, item in enumerate(items, start=1):
        decision = decisions.get(item.item_id)
        if not decision:
            continue
        stance = str(decision.get("stance", ""))
        if stance == "no_response":
            explanation = "本次邮件中不回应此事项。"
        else:
            explanation = next(
                (
                    str(decision.get(field, "")).strip()
                    for field in (
                        "confirmed_facts", "accepted_part", "reason",
                        "requested_information", "custom_instruction",
                    )
                    if str(decision.get(field, "")).strip()
                ),
                "已记录您的处理立场。",
            )
        entries.append(
            DecisionSummaryEntry(
                number=number,
                title=item.description,
                position=STANCE_LABELS.get(stance, "已确认"),
                explanation=explanation,
                kind=kinds.get(stance, "info"),
            )
        )
    return tuple(entries)


def render_reply_summary(items: tuple[ReplyItem, ...]) -> bool:
    decisions = dict(st.session_state.get("reply__decisions", {}))
    summary = build_decision_summary(items, decisions)
    st.session_state["reply__decision_summary"] = summary
    render_section_header("回复策略确认", "DECISION SUMMARY")
    st.caption("以下内容会作为生成回复的唯一依据；系统尚未生成邮件。")
    if st.session_state.get("reply__generation_error"):
        st.error(st.session_state["reply__generation_error"])
    entries = _summary_entries(items, decisions)
    if entries:
        render_decision_summary_cards(entries)
    if summary.undecided:
        render_notice_bar(
            "仍有事项待确认",
            "请返回逐项确认，完成后再生成邮件。",
            icon="!",
        )

    risk = st.session_state.get("reply__decision_risk")
    if risk is not None:
        level = {"low": "低", "medium": "中", "high": "高"}[
            risk.risk_level
        ]
        render_notice_bar(f"内容风险 · {level}", risk.summary, icon="!")
    if summary.ready:
        render_status_badge("回复立场已确认", "success")
    else:
        st.warning("仍有必须回复的事项尚未完成。")
    st.selectbox(
        "目标语气 · Target Tone",
        ("Formal", "Friendly", "Strong", "Executive"),
        key="reply__target_tone",
        format_func=lambda value: {
            "Formal": "正式 · Formal",
            "Friendly": "友好 · Friendly",
            "Strong": "明确强硬 · Strong",
            "Executive": "高管简洁 · Executive",
        }[value],
        help="语气只影响表达方式，不会改变已确认的事实和立场。",
    )
    generate = st.button(
        "生成回复",
        key="reply__generate_reply",
        type="primary",
        use_container_width=True,
        disabled=not summary.ready,
    )
    if secondary_action_button(
        "返回修改回复立场", key="reply__summary_back"
    ):
        return_to_reply_decisions()
        st.rerun()
    if tertiary_action_button("返回来信分析", key="reply__summary_analysis"):
        return_to_reply_analysis()
        st.rerun()
    return generate
