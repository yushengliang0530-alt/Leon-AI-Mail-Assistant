"""Strict models for the Phase 4 Send Ready inspection."""

from dataclasses import dataclass, replace
import json
import re


PREFLIGHT_STATUSES = ("GOOD", "CHECK", "WARNING")
SEMANTIC_CHECK_IDS = (
    "action_clarity",
    "deadline_clarity",
    "salutation",
    "tone_alignment",
    "commitment_risk",
)


def _json(content: str) -> dict:
    if not isinstance(content, str) or not content.strip():
        raise ValueError("empty preflight response")
    candidate = content.strip()
    candidate = re.sub(r"^```(?:json)?\s*", "", candidate, flags=re.I)
    candidate = re.sub(r"\s*```$", "", candidate)
    start, end = candidate.find("{"), candidate.rfind("}")
    if start >= 0 and end > start:
        candidate = candidate[start : end + 1]
    value = json.loads(candidate)
    if not isinstance(value, dict):
        raise ValueError("preflight response must be an object")
    return value


def _text(value: object, name: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be text")
    clean = value.strip()
    if not clean and not allow_empty:
        raise ValueError(f"{name} must be non-empty text")
    return clean


@dataclass(frozen=True)
class PreflightItem:
    item_id: str
    category: str
    status: str
    title: str
    message: str
    suggestion: str | None
    source: str


@dataclass(frozen=True)
class SemanticPreflightResult:
    summary: str
    items: tuple[PreflightItem, ...]
    usage_tokens: int | None = None


@dataclass(frozen=True)
class PreflightReport:
    overall_status: str
    summary: str
    items: tuple[PreflightItem, ...]
    usage_tokens: int | None = None


def parse_semantic_preflight(content: str) -> SemanticPreflightResult:
    data = _json(content)
    if set(data) != {"summary", "checks"} or not isinstance(
        data["checks"], list
    ):
        raise ValueError("preflight fields do not match schema")
    items: list[PreflightItem] = []
    for raw in data["checks"]:
        if not isinstance(raw, dict) or set(raw) != {
            "item_id",
            "status",
            "title",
            "message",
            "suggestion",
        }:
            raise ValueError("preflight item fields do not match schema")
        status = _text(raw["status"], "status")
        if status not in PREFLIGHT_STATUSES:
            raise ValueError("invalid preflight status")
        suggestion = raw["suggestion"]
        if suggestion is not None:
            suggestion = _text(
                suggestion, "suggestion", allow_empty=True
            ) or None
        item_id = _text(raw["item_id"], "item_id")
        items.append(
            PreflightItem(
                item_id=item_id,
                category=item_id,
                status=status,
                title=_text(raw["title"], "title"),
                message=_text(raw["message"], "message"),
                suggestion=suggestion,
                source="ai",
            )
        )
    actual_ids = tuple(item.item_id for item in items)
    if len(actual_ids) != len(set(actual_ids)):
        raise ValueError("duplicate preflight item")
    if set(actual_ids) != set(SEMANTIC_CHECK_IDS):
        raise ValueError("semantic preflight IDs do not match schema")
    order = {item_id: index for index, item_id in enumerate(SEMANTIC_CHECK_IDS)}
    return SemanticPreflightResult(
        summary=_text(data["summary"], "summary"),
        items=tuple(sorted(items, key=lambda item: order[item.item_id])),
    )


def with_usage(result, usage_tokens: int | None):
    return replace(result, usage_tokens=usage_tokens)
