"""Deterministic Phase 3B normalization, validation, and summaries."""

import hashlib
import json

from models.incoming_email import IncomingEmailAnalysis
from models.reply_decision import (
    STANCES,
    DecisionSummary,
    DecisionValidation,
    ReplyDecision,
    ReplyItem,
)


STANCE_LABELS = {
    "accept": "接受并确认",
    "partial": "部分接受",
    "decline": "拒绝",
    "request_info": "请求更多信息",
    "unable_to_confirm": "暂时无法确认",
    "no_response": "不在回复中回应",
    "custom": "自定义处理",
}


def normalize_reply_items(
    analysis: IncomingEmailAnalysis,
) -> tuple[ReplyItem, ...]:
    """Merge explicitly linked questions without fuzzy inference."""
    questions_by_request: dict[str, list] = {}
    unlinked_questions = []
    for question in analysis.questions_requiring_reply:
        if question.related_request_id:
            questions_by_request.setdefault(
                question.related_request_id, []
            ).append(question)
        else:
            unlinked_questions.append(question)

    items: list[ReplyItem] = []
    for request in analysis.sender_requests:
        linked = questions_by_request.get(request.item_id, [])
        question_text = "；".join(
            item.question
            for item in linked
            if item.question.casefold() not in request.description.casefold()
        )
        description = request.description
        if question_text:
            description = f"{description}（相关问题：{question_text}）"
        deadlines = [
            value
            for value in (
                request.deadline,
                *(question.deadline for question in linked),
            )
            if value
        ]
        unique_deadlines = tuple(dict.fromkeys(deadlines))
        items.append(
            ReplyItem(
                item_id=request.item_id,
                item_type="request",
                description=description,
                deadline=unique_deadlines[0] if unique_deadlines else None,
                required=request.needs_response
                or any(question.required for question in linked),
                source_request_id=request.item_id,
                source_question_ids=tuple(
                    question.item_id for question in linked
                ),
                uncertain=request.uncertain
                or any(question.uncertain for question in linked)
                or len(unique_deadlines) > 1,
            )
        )

    for question in unlinked_questions:
        items.append(
            ReplyItem(
                item_id=question.item_id,
                item_type="question",
                description=question.question,
                deadline=question.deadline,
                required=question.required,
                source_request_id=None,
                source_question_ids=(question.item_id,),
                uncertain=question.uncertain,
            )
        )
    return tuple(items)


def validate_decision(
    item: ReplyItem,
    decision: ReplyDecision | None,
) -> DecisionValidation:
    if decision is None or not decision.stance:
        if item.required:
            return DecisionValidation(False, ("请选择本事项的回复立场。",))
        return DecisionValidation(True, ())
    if decision.item_id != item.item_id:
        return DecisionValidation(False, ("回复决策与当前事项不匹配。",))
    if decision.stance not in STANCES:
        return DecisionValidation(False, ("回复立场无效，请重新选择。",))

    errors: list[str] = []
    if decision.stance == "accept" and not decision.confirmed_facts.strip():
        errors.append("请填写可以确认的行动或事实。")
    elif decision.stance == "partial":
        if not decision.accepted_part.strip():
            errors.append("请填写可以接受或确认的部分。")
        if not decision.declined_part.strip():
            errors.append("请填写不能接受或尚无法确认的部分。")
    elif decision.stance == "decline" and not decision.reason.strip():
        errors.append("请填写可以对外说明的原因。")
    elif (
        decision.stance == "request_info"
        and not decision.requested_information.strip()
    ):
        errors.append("请填写需要对方补充的信息。")
    elif decision.stance == "unable_to_confirm" and not (
        decision.reason.strip() or decision.user_notes.strip()
    ):
        errors.append("请填写暂时无法确认的原因或内部核实事项。")
    elif decision.stance == "no_response":
        if not decision.no_response_confirmed:
            errors.append("请明确确认此事项不在后续回复中回应。")
        if decision.include_in_reply:
            errors.append("不回复事项不能标记为包含在后续回复中。")
    elif (
        decision.stance == "custom"
        and not decision.custom_instruction.strip()
    ):
        errors.append("请填写自定义处理指令。")
    return DecisionValidation(not errors, tuple(errors))


def decision_digest(decisions: dict[str, dict]) -> str:
    payload = json.dumps(
        decisions,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def decision_publishable_text(
    decisions: dict[str, dict],
) -> str:
    excluded = {"user_notes", "no_response_confirmed"}
    values: list[str] = []
    for item_id in sorted(decisions):
        decision = decisions[item_id]
        if decision.get("stance") == "no_response":
            continue
        for key, value in decision.items():
            if key not in excluded and isinstance(value, str) and value.strip():
                values.append(value.strip())
    return "\n".join(values)


def build_decision_summary(
    items: tuple[ReplyItem, ...],
    decisions: dict[str, dict],
) -> DecisionSummary:
    decided: list[ReplyItem] = []
    excluded: list[ReplyItem] = []
    skipped: list[ReplyItem] = []
    undecided: list[ReplyItem] = []
    for item in items:
        raw = decisions.get(item.item_id)
        decision = ReplyDecision.from_dict(raw) if raw else None
        validation = validate_decision(item, decision)
        if not raw:
            (undecided if item.required else skipped).append(item)
        elif not validation.valid:
            undecided.append(item)
        elif decision and decision.stance == "no_response":
            excluded.append(item)
        else:
            decided.append(item)
    return DecisionSummary(
        decided=tuple(decided),
        excluded=tuple(excluded),
        skipped_optional=tuple(skipped),
        undecided=tuple(undecided),
        ready=not undecided,
    )
