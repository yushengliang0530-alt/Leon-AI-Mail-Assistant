"""Strict structured results for reply generation and coverage."""

from dataclasses import dataclass, replace
import json
import re


COVERAGE_STATUSES = frozenset(
    {"addressed", "partially_addressed", "postponed", "not_addressed"}
)


def _json(content: str) -> dict:
    if not isinstance(content, str) or not content.strip():
        raise ValueError("empty response")
    candidate = content.strip()
    candidate = re.sub(r"^```(?:json)?\s*", "", candidate, flags=re.I)
    candidate = re.sub(r"\s*```$", "", candidate)
    start, end = candidate.find("{"), candidate.rfind("}")
    if start >= 0 and end > start:
        candidate = candidate[start : end + 1]
    value = json.loads(candidate)
    if not isinstance(value, dict):
        raise ValueError("response must be an object")
    return value


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty text")
    return value.strip()


@dataclass(frozen=True)
class GeneratedReply:
    subject: str
    body: str
    usage_tokens: int | None = None


@dataclass(frozen=True)
class CoverageItem:
    item_id: str
    status: str
    note: str


@dataclass(frozen=True)
class CoverageResult:
    items: tuple[CoverageItem, ...]
    addressed_count: int
    partial_count: int
    postponed_count: int
    not_addressed_count: int
    covered_count: int
    total_count: int
    usage_tokens: int | None = None


def parse_generated_reply(content: str) -> GeneratedReply:
    data = _json(content)
    if set(data) != {"subject", "body"}:
        raise ValueError("generation fields do not match schema")
    return GeneratedReply(
        subject=_text(data["subject"], "subject"),
        body=_text(data["body"], "body"),
    )


def parse_coverage(
    content: str,
    expected_item_ids: tuple[str, ...],
) -> CoverageResult:
    data = _json(content)
    if set(data) != {"coverage"} or not isinstance(data["coverage"], list):
        raise ValueError("coverage fields do not match schema")
    items: list[CoverageItem] = []
    for raw in data["coverage"]:
        if not isinstance(raw, dict) or set(raw) != {
            "item_id",
            "status",
            "note",
        }:
            raise ValueError("coverage item fields do not match schema")
        status = _text(raw["status"], "status")
        if status not in COVERAGE_STATUSES:
            raise ValueError("invalid coverage status")
        items.append(
            CoverageItem(
                item_id=_text(raw["item_id"], "item_id"),
                status=status,
                note=_text(raw["note"], "note"),
            )
        )
    actual = tuple(item.item_id for item in items)
    if len(actual) != len(set(actual)):
        raise ValueError("duplicate coverage item")
    if set(actual) != set(expected_item_ids) or len(actual) != len(
        expected_item_ids
    ):
        raise ValueError("coverage IDs do not match expected items")
    order = {item_id: index for index, item_id in enumerate(expected_item_ids)}
    ordered = tuple(sorted(items, key=lambda item: order[item.item_id]))
    counts = {
        status: sum(item.status == status for item in ordered)
        for status in COVERAGE_STATUSES
    }
    return CoverageResult(
        items=ordered,
        addressed_count=counts["addressed"],
        partial_count=counts["partially_addressed"],
        postponed_count=counts["postponed"],
        not_addressed_count=counts["not_addressed"],
        covered_count=counts["addressed"] + counts["postponed"],
        total_count=len(ordered),
    )


def with_usage(result, usage_tokens: int | None):
    return replace(result, usage_tokens=usage_tokens)
