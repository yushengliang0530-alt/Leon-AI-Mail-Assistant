"""Guided local stance confirmation for Phase 3B."""

import html

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
from ui.state import (
    clear_reply_decisions,
    return_to_reply_analysis,
    return_to_reply_decisions,
    set_reply_item_index,
)


STANCE_OPTIONS = tuple(STANCE_LABELS)


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


def _render_item_header(item: ReplyItem, index: int, total: int) -> None:
    status = "必须回复" if item.required else "可选事项"
    metadata = [status, f"ID: {item.item_id}"]
    if item.deadline:
        metadata.append(f"截止时间：{item.deadline}")
    if item.uncertain:
        metadata.append("信息待确认")
    st.markdown(
        f"""
        <div class="reply-card reply-decision-card">
          <div class="reply-meta">事项 {index + 1} / {total} ·
            {html.escape(" · ".join(metadata))}</div>
          <h3>{html.escape(item.description)}</h3>
          <p>请选择您准备如何处理这一事项。系统不会替您默认接受或承诺。</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_stance_fields(item: ReplyItem) -> None:
    stance_key = _widget_key(item.item_id, "stance")
    selected = st.session_state.get(stance_key, "")
    display = [STANCE_LABELS[value] for value in STANCE_OPTIONS]
    current_index = (
        STANCE_OPTIONS.index(selected) if selected in STANCE_OPTIONS else None
    )
    label = st.selectbox(
        "您的处理立场 · Response Position",
        display,
        index=current_index,
        placeholder="请选择，不会默认接受",
        key=f"{stance_key}__display",
        on_change=_clear_decision_error,
    )
    chosen = (
        STANCE_OPTIONS[display.index(label)] if label in display else ""
    )
    st.session_state[stance_key] = chosen
    if not chosen:
        return

    if chosen == "accept":
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
    elif chosen == "partial":
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
    elif chosen == "decline":
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
    elif chosen == "request_info":
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
    elif chosen == "unable_to_confirm":
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
    elif chosen == "no_response":
        st.warning("此事项将明确排除在生成的回复内容之外。")
        st.checkbox(
            "我确认不在后续回复中回应此事项。",
            key=_widget_key(item.item_id, "no_response_confirmed"),
        )
        st.session_state[_widget_key(item.item_id, "include_in_reply")] = False
        st.text_area(
            "不回复的内部原因（可选，不会写入邮件）",
            key=_widget_key(item.item_id, "user_notes"),
        )
    elif chosen == "custom":
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
                f"**{index + 1}. {html.escape(item.description)}**  \n"
                f"{marker} · `{html.escape(item.item_id)}`"
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
    st.markdown("### 逐项确认回复立场")
    st.caption("Decision Guidance · 每次只处理一个事项，不会自动生成邮件。")
    _render_item_header(item, index, len(items))
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
            st.warning(risk.summary)
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

    left, middle, right = st.columns(3)
    with left:
        if st.button(
            "返回",
            key=f"reply__decision_back__{item.item_id}",
            use_container_width=True,
        ):
            if index == 0:
                return_to_reply_analysis()
            else:
                set_reply_item_index(index - 1)
            st.rerun()
    with middle:
        st.button(
            "清除此项",
            key=f"reply__decision_clear__{item.item_id}",
            use_container_width=True,
            on_click=_clear_current,
            args=(item.item_id,),
        )
    with right:
        button_label = (
            "检查决策摘要" if index == len(items) - 1 else "保存并继续"
        )
        if st.button(
            button_label,
            key=f"reply__decision_next__{item.item_id}",
            type="primary",
            use_container_width=True,
        ):
            if not _save_decision(item):
                st.rerun()
            if index == len(items) - 1:
                _try_finish(items)
            else:
                set_reply_item_index(index + 1)
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


def _summary_list(
    title: str,
    items: tuple[ReplyItem, ...],
    decisions: dict[str, dict],
    *,
    show_stance: bool = True,
) -> None:
    if not items:
        return
    lines = []
    for item in items:
        stance = ""
        if show_stance and item.item_id in decisions:
            stance = (
                f" · {STANCE_LABELS.get(decisions[item.item_id]['stance'], '')}"
            )
        lines.append(
            f"<li>{html.escape(item.description + stance)}</li>"
        )
    st.markdown(
        f'<div class="reply-card"><h3>{html.escape(title)}</h3>'
        f"<ul>{''.join(lines)}</ul></div>",
        unsafe_allow_html=True,
    )


def render_reply_summary(items: tuple[ReplyItem, ...]) -> bool:
    decisions = dict(st.session_state.get("reply__decisions", {}))
    summary = build_decision_summary(items, decisions)
    st.session_state["reply__decision_summary"] = summary
    st.markdown("### 回复决策摘要")
    st.caption("Decision Summary · 仅整理您的决定，尚未生成回复邮件。")
    if st.session_state.get("reply__generation_error"):
        st.error(st.session_state["reply__generation_error"])
    _summary_list("已确认的回复事项", summary.decided, decisions)
    _summary_list("明确不回复的事项", summary.excluded, decisions)
    _summary_list(
        "已跳过的可选事项",
        summary.skipped_optional,
        decisions,
        show_stance=False,
    )
    _summary_list(
        "仍未完成的事项",
        summary.undecided,
        decisions,
        show_stance=False,
    )

    risk = st.session_state.get("reply__decision_risk")
    if risk is not None:
        level = {"low": "低", "medium": "中", "high": "高"}[
            risk.risk_level
        ]
        st.markdown(
            f'<div class="reply-card"><h3>内容风险 · {level}</h3>'
            f"<p>{html.escape(risk.summary)}</p></div>",
            unsafe_allow_html=True,
        )
    if summary.ready:
        st.success("回复立场已逐项确认，可以进入下一阶段。")
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
        "生成英文回复 · Generate Reply",
        key="reply__generate_reply",
        type="primary",
        use_container_width=True,
        disabled=not summary.ready,
    )
    left, right = st.columns(2)
    with left:
        st.button(
            "返回修改决定",
            key="reply__summary_back",
            use_container_width=True,
            on_click=return_to_reply_decisions,
        )
    with right:
        st.button(
            "返回来信分析",
            key="reply__summary_analysis",
            use_container_width=True,
            on_click=return_to_reply_analysis,
        )
    return generate
