"""Strict structured model for analysis of an untrusted incoming email."""

from dataclasses import dataclass
import json
import re
from typing import Any


URGENCY_LEVELS = frozenset({"low", "normal", "high", "urgent"})
RISK_LEVELS = frozenset({"low", "medium", "high"})
ROOT_FIELDS = frozenset(
    {
        "summary",
        "sender_intent",
        "sender_requests",
        "questions_requiring_reply",
        "key_dates",
        "key_numbers",
        "risks",
        "urgency",
        "reply_strategy",
        "detected_subject",
        "uncertainties",
    }
)


@dataclass(frozen=True)
class SenderRequest:
    item_id: str
    description: str
    deadline: str | None
    needs_response: bool
    source_hint: str
    uncertain: bool


@dataclass(frozen=True)
class ReplyQuestion:
    item_id: str
    question: str
    required: bool
    related_request_id: str | None
    deadline: str | None
    uncertain: bool


@dataclass(frozen=True)
class KeyFact:
    value: str
    meaning: str
    uncertain: bool


@dataclass(frozen=True)
class AnalysisRisk:
    category: str
    level: str
    description: str
    suggestion: str


@dataclass(frozen=True)
class IncomingEmailAnalysis:
    summary: str
    sender_intent: str
    sender_requests: tuple[SenderRequest, ...]
    questions_requiring_reply: tuple[ReplyQuestion, ...]
    key_dates: tuple[KeyFact, ...]
    key_numbers: tuple[KeyFact, ...]
    risks: tuple[AnalysisRisk, ...]
    urgency: str
    reply_strategy: tuple[str, ...]
    detected_subject: str | None
    uncertainties: tuple[str, ...]
    usage_tokens: int | None = None


def _json_candidate(content: str) -> str:
    candidate = content.strip()
    candidate = re.sub(r"^```(?:json)?\s*", "", candidate, flags=re.I)
    candidate = re.sub(r"\s*```$", "", candidate)
    start = candidate.find("{")
    end = candidate.rfind("}")
    return candidate[start : end + 1] if start >= 0 and end > start else candidate


def _object(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return value


def _list(value: Any, name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a list")
    return value


def _text(value: Any, name: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be text")
    clean = value.strip()
    if not clean and not allow_empty:
        raise ValueError(f"{name} must not be empty")
    return clean


def _optional_text(value: Any, name: str) -> str | None:
    if value is None:
        return None
    return _text(value, name)


def _boolean(value: Any, name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be boolean")
    return value


def _sender_request(value: Any) -> SenderRequest:
    item = _object(value, "sender_request")
    return SenderRequest(
        item_id=_text(item.get("item_id"), "sender_request.item_id"),
        description=_text(
            item.get("description"),
            "sender_request.description",
        ),
        deadline=_optional_text(
            item.get("deadline"),
            "sender_request.deadline",
        ),
        needs_response=_boolean(
            item.get("needs_response"),
            "sender_request.needs_response",
        ),
        source_hint=_text(
            item.get("source_hint", ""),
            "sender_request.source_hint",
            allow_empty=True,
        ),
        uncertain=_boolean(
            item.get("uncertain"),
            "sender_request.uncertain",
        ),
    )


def _reply_question(value: Any) -> ReplyQuestion:
    item = _object(value, "reply_question")
    return ReplyQuestion(
        item_id=_text(item.get("item_id"), "reply_question.item_id"),
        question=_text(item.get("question"), "reply_question.question"),
        required=_boolean(item.get("required"), "reply_question.required"),
        related_request_id=_optional_text(
            item.get("related_request_id"),
            "reply_question.related_request_id",
        ),
        deadline=_optional_text(
            item.get("deadline"),
            "reply_question.deadline",
        ),
        uncertain=_boolean(
            item.get("uncertain"),
            "reply_question.uncertain",
        ),
    )


def _key_fact(value: Any, name: str) -> KeyFact:
    item = _object(value, name)
    return KeyFact(
        value=_text(item.get("value"), f"{name}.value"),
        meaning=_text(item.get("meaning"), f"{name}.meaning"),
        uncertain=_boolean(item.get("uncertain"), f"{name}.uncertain"),
    )


def _risk(value: Any) -> AnalysisRisk:
    item = _object(value, "risk")
    level = _text(item.get("level"), "risk.level")
    if level not in RISK_LEVELS:
        raise ValueError("invalid risk level")
    return AnalysisRisk(
        category=_text(item.get("category"), "risk.category"),
        level=level,
        description=_text(item.get("description"), "risk.description"),
        suggestion=_text(item.get("suggestion"), "risk.suggestion"),
    )


def parse_incoming_email_analysis(content: str) -> IncomingEmailAnalysis:
    """Parse and validate the model JSON without inventing fallback content."""
    if not isinstance(content, str) or not content.strip():
        raise ValueError("empty analysis")
    data = _object(json.loads(_json_candidate(content)), "analysis")
    if set(data) != ROOT_FIELDS:
        raise ValueError("analysis fields do not match schema")

    urgency = _text(data.get("urgency"), "urgency")
    if urgency not in URGENCY_LEVELS:
        raise ValueError("invalid urgency")

    requests = tuple(
        _sender_request(item)
        for item in _list(data.get("sender_requests"), "sender_requests")
    )
    questions = tuple(
        _reply_question(item)
        for item in _list(
            data.get("questions_requiring_reply"),
            "questions_requiring_reply",
        )
    )
    all_ids = [item.item_id for item in requests] + [
        item.item_id for item in questions
    ]
    if len(all_ids) != len(set(all_ids)):
        raise ValueError("duplicate item_id")
    request_ids = {item.item_id for item in requests}
    if any(
        item.related_request_id
        and item.related_request_id not in request_ids
        for item in questions
    ):
        raise ValueError("unknown related_request_id")

    strategy = tuple(
        _text(item, "reply_strategy item")
        for item in _list(data.get("reply_strategy"), "reply_strategy")
    )
    uncertainties = tuple(
        _text(item, "uncertainties item")
        for item in _list(data.get("uncertainties"), "uncertainties")
    )
    return IncomingEmailAnalysis(
        summary=_text(data.get("summary"), "summary"),
        sender_intent=_text(data.get("sender_intent"), "sender_intent"),
        sender_requests=requests,
        questions_requiring_reply=questions,
        key_dates=tuple(
            _key_fact(item, "key_date")
            for item in _list(data.get("key_dates"), "key_dates")
        ),
        key_numbers=tuple(
            _key_fact(item, "key_number")
            for item in _list(data.get("key_numbers"), "key_numbers")
        ),
        risks=tuple(
            _risk(item) for item in _list(data.get("risks"), "risks")
        ),
        urgency=urgency,
        reply_strategy=strategy,
        detected_subject=_optional_text(
            data.get("detected_subject"),
            "detected_subject",
        ),
        uncertainties=uncertainties,
    )
