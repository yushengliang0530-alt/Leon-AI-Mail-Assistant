"""Structured model and safe normalizer for incoming-email analysis."""

from dataclasses import dataclass
import json
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
        "recommended_reply_items",
        "detected_subject",
        "uncertainties",
    }
)
ROOT_ALIASES = {
    "requests": "sender_requests",
    "questions": "questions_requiring_reply",
    "dates": "key_dates",
    "numbers": "key_numbers",
    "strategy": "reply_strategy",
}


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
class RecommendedReplyItem:
    item_id: str
    description: str
    reason: str
    required: bool
    uncertain: bool


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
    recommended_reply_items: tuple[RecommendedReplyItem, ...]
    detected_subject: str | None
    uncertainties: tuple[str, ...]
    usage_tokens: int | None = None


class IncomingAnalysisParseError(ValueError):
    """A categorized parse error that never contains model or user content."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def _first_json_object(content: str) -> dict[str, Any]:
    decoder = json.JSONDecoder()
    for index, character in enumerate(content):
        if character != "{":
            continue
        try:
            value, _ = decoder.raw_decode(content[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    raise IncomingAnalysisParseError("invalid_or_truncated_json")


def _object(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise IncomingAnalysisParseError(f"{name}_must_be_object")
    return value


def _items(value: Any) -> list[Any]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return value
    return [value]


def _text(value: Any, name: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise IncomingAnalysisParseError(f"{name}_must_be_text")
    clean = value.strip()
    if not clean and not allow_empty:
        raise IncomingAnalysisParseError(f"{name}_must_not_be_empty")
    return clean


def _optional_text(value: Any, name: str) -> str | None:
    if value is None or value == "":
        return None
    if isinstance(value, dict):
        for key in ("value", "date", "deadline", "text"):
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
        raise IncomingAnalysisParseError(f"{name}_must_be_text")
    return _text(value, name)


def _boolean(value: Any, name: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes"}:
            return True
        if normalized in {"false", "no", ""}:
            return False
    raise IncomingAnalysisParseError(f"{name}_must_be_boolean")


def _sender_request(value: Any, index: int) -> SenderRequest:
    if isinstance(value, str):
        value = {
            "description": value,
            "needs_response": False,
            "uncertain": True,
        }
    item = _object(value, "sender_request")
    return SenderRequest(
        item_id=_text(
            item.get("item_id") or f"request_{index}",
            "sender_request.item_id",
        ),
        description=_text(
            item.get("description"),
            "sender_request.description",
        ),
        deadline=_optional_text(
            item.get("deadline"),
            "sender_request.deadline",
        ),
        needs_response=_boolean(
            item.get("needs_response", False),
            "sender_request.needs_response",
        ),
        source_hint=_text(
            item.get("source_hint", ""),
            "sender_request.source_hint",
            allow_empty=True,
        ),
        uncertain=_boolean(
            item.get("uncertain", True),
            "sender_request.uncertain",
        ),
    )


def _reply_question(value: Any, index: int) -> ReplyQuestion:
    if isinstance(value, str):
        value = {
            "question": value,
            "required": False,
            "uncertain": True,
        }
    item = _object(value, "reply_question")
    return ReplyQuestion(
        item_id=_text(
            item.get("item_id") or f"question_{index}",
            "reply_question.item_id",
        ),
        question=_text(item.get("question"), "reply_question.question"),
        required=_boolean(
            item.get("required", False),
            "reply_question.required",
        ),
        related_request_id=_optional_text(
            item.get("related_request_id"),
            "reply_question.related_request_id",
        ),
        deadline=_optional_text(
            item.get("deadline"),
            "reply_question.deadline",
        ),
        uncertain=_boolean(
            item.get("uncertain", True),
            "reply_question.uncertain",
        ),
    )


def _key_fact(value: Any, name: str) -> KeyFact:
    if isinstance(value, str):
        value = {"value": value, "meaning": "", "uncertain": True}
    item = _object(value, name)
    return KeyFact(
        value=_text(item.get("value"), f"{name}.value"),
        meaning=_text(
            item.get("meaning", ""),
            f"{name}.meaning",
            allow_empty=True,
        ),
        uncertain=_boolean(
            item.get("uncertain", True),
            f"{name}.uncertain",
        ),
    )


def _risk_level(value: Any) -> tuple[str, bool]:
    level = _text(value or "medium", "risk.level").lower()
    aliases = {
        "low": "low",
        "info": "low",
        "informational": "low",
        "medium": "medium",
        "moderate": "medium",
        "normal": "medium",
        "warning": "medium",
        "high": "high",
        "critical": "high",
        "severe": "high",
    }
    return aliases.get(level, "medium"), level not in aliases


def _risk(value: Any) -> tuple[AnalysisRisk, bool]:
    if isinstance(value, str):
        value = {
            "category": "unspecified",
            "level": "medium",
            "description": value,
            "suggestion": "",
        }
    item = _object(value, "risk")
    level, uncertain_level = _risk_level(item.get("level"))
    return (
        AnalysisRisk(
            category=_text(item.get("category"), "risk.category"),
            level=level,
            description=_text(item.get("description"), "risk.description"),
            suggestion=_text(
                item.get("suggestion", ""),
                "risk.suggestion",
                allow_empty=True,
            ),
        ),
        uncertain_level,
    )


def _recommended_reply_item(
    value: Any,
    index: int,
) -> RecommendedReplyItem:
    if isinstance(value, str):
        value = {
            "description": value,
            "reason": "",
            "required": False,
            "uncertain": True,
        }
    item = _object(value, "recommended_reply_item")
    return RecommendedReplyItem(
        item_id=f"recommendation_{index}",
        description=_text(
            item.get("description"),
            "recommended_reply_item.description",
        ),
        reason=_text(
            item.get("reason", ""),
            "recommended_reply_item.reason",
            allow_empty=True,
        ),
        required=_boolean(
            item.get("required", False),
            "recommended_reply_item.required",
        ),
        uncertain=_boolean(
            item.get("uncertain", True),
            "recommended_reply_item.uncertain",
        ),
    )


def _urgency(value: Any) -> tuple[str, bool]:
    level = _text(value or "normal", "urgency").lower()
    aliases = {
        "low": "low",
        "minor": "low",
        "normal": "normal",
        "medium": "normal",
        "moderate": "normal",
        "high": "high",
        "urgent": "urgent",
        "critical": "urgent",
        "immediate": "urgent",
    }
    return aliases.get(level, "normal"), level not in aliases


def _text_items(value: Any, name: str) -> tuple[str, ...]:
    return tuple(_text(item, f"{name}_item") for item in _items(value))


def _with_stable_ids(value: Any, prefix: str) -> list[Any]:
    items = _items(value)
    used = {
        str(item.get("item_id", "")).strip()
        for item in items
        if isinstance(item, dict) and item.get("item_id")
    }
    normalized: list[Any] = []
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            normalized.append(item)
            continue
        supplied_id = item.get("item_id")
        if isinstance(supplied_id, str) and supplied_id.strip():
            normalized.append(item)
            continue
        candidate = f"{prefix}_{index}"
        suffix = 1
        while candidate in used:
            candidate = f"{prefix}_{index}_auto_{suffix}"
            suffix += 1
        used.add(candidate)
        normalized.append({**item, "item_id": candidate})
    return normalized


def parse_incoming_email_analysis(content: str) -> IncomingEmailAnalysis:
    """Parse and validate the model JSON without inventing fallback content."""
    if not isinstance(content, str) or not content.strip():
        raise IncomingAnalysisParseError("empty_analysis")
    raw_data = _first_json_object(content)
    data = {
        key: value for key, value in raw_data.items() if key in ROOT_FIELDS
    }
    for alias, canonical in ROOT_ALIASES.items():
        if canonical not in data and alias in raw_data:
            data[canonical] = raw_data[alias]

    requests = tuple(
        _sender_request(item, index)
        for index, item in enumerate(
            _with_stable_ids(data.get("sender_requests"), "request"),
            start=1,
        )
    )
    questions = tuple(
        _reply_question(item, index)
        for index, item in enumerate(
            _with_stable_ids(
                data.get("questions_requiring_reply"),
                "question",
            ),
            start=1,
        )
    )
    all_ids = [item.item_id for item in requests] + [
        item.item_id for item in questions
    ]
    if len(all_ids) != len(set(all_ids)):
        raise IncomingAnalysisParseError("duplicate_item_id")
    request_ids = {item.item_id for item in requests}
    if any(
        item.related_request_id
        and item.related_request_id not in request_ids
        for item in questions
    ):
        raise IncomingAnalysisParseError("unknown_related_request_id")

    parsed_risks = tuple(_risk(item) for item in _items(data.get("risks")))
    urgency, urgency_was_unknown = _urgency(data.get("urgency"))
    uncertainties = list(
        _text_items(data.get("uncertainties"), "uncertainties")
    )
    if urgency_was_unknown:
        uncertainties.append(
            "AI returned an unsupported urgency label; it was normalized."
        )
    if any(was_unknown for _, was_unknown in parsed_risks):
        uncertainties.append(
            "AI returned an unsupported risk label; it was normalized."
        )

    return IncomingEmailAnalysis(
        summary=_text(data.get("summary"), "summary"),
        sender_intent=_text(data.get("sender_intent"), "sender_intent"),
        sender_requests=requests,
        questions_requiring_reply=questions,
        key_dates=tuple(
            _key_fact(item, "key_date")
            for item in _items(data.get("key_dates"))
        ),
        key_numbers=tuple(
            _key_fact(item, "key_number")
            for item in _items(data.get("key_numbers"))
        ),
        risks=tuple(risk for risk, _ in parsed_risks),
        urgency=urgency,
        reply_strategy=_text_items(
            data.get("reply_strategy"),
            "reply_strategy",
        ),
        recommended_reply_items=tuple(
            _recommended_reply_item(item, index)
            for index, item in enumerate(
                _items(data.get("recommended_reply_items")),
                start=1,
            )
        ),
        detected_subject=_optional_text(
            data.get("detected_subject"),
            "detected_subject",
        ),
        uncertainties=tuple(uncertainties),
    )
