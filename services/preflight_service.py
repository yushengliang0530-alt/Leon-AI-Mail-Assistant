"""Hybrid local and semantic Send Ready inspection."""

from dataclasses import asdict
import hashlib
import json
import re
from typing import Protocol

from models.incoming_email import IncomingEmailAnalysis
from models.preflight import (
    PREFLIGHT_STATUSES,
    PreflightItem,
    PreflightReport,
    SemanticPreflightResult,
)
from models.reply_generation import CoverageResult


class PreflightBackend(Protocol):
    def check_reply_preflight(
        self, *, payload: dict
    ) -> SemanticPreflightResult: ...


_ATTACHMENT_PATTERN = re.compile(
    r"\b(?:attachment|attachments|attached)\b", re.IGNORECASE
)
_DATE_PATTERNS = (
    re.compile(r"\b\d{1,4}[/-]\d{1,2}(?:[/-]\d{1,4})?\b"),
    re.compile(
        r"\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|"
        r"jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|"
        r"nov(?:ember)?|dec(?:ember)?)\s+\d{1,2}(?:,\s*\d{4})?\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b\d{1,2}\s+(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|"
        r"apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|"
        r"sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|"
        r"dec(?:ember)?)(?:\s+\d{4})?\b",
        re.IGNORECASE,
    ),
)
_AMOUNT_PATTERN = re.compile(
    r"(?:[$€£¥]\s?\d[\d,]*(?:\.\d+)?|"
    r"\b\d[\d,]*(?:\.\d+)?\s?(?:USD|EUR|GBP|CNY|RMB)\b)",
    re.IGNORECASE,
)
_SEVERITY = {status: index for index, status in enumerate(PREFLIGHT_STATUSES)}


def _public_decisions(decisions: dict[str, dict]) -> dict[str, dict]:
    excluded = {"user_notes", "no_response_confirmed"}
    return {
        item_id: {
            key: value
            for key, value in decision.items()
            if key not in excluded
        }
        for item_id, decision in decisions.items()
    }


def preflight_source_digest(
    *,
    subject: str,
    body: str,
    decisions: dict[str, dict],
    target_tone: str,
    coverage: CoverageResult | None,
) -> str:
    coverage_data = (
        [asdict(item) for item in coverage.items] if coverage else None
    )
    raw = json.dumps(
        {
            "subject": subject,
            "body": body,
            "decisions": decisions,
            "target_tone": target_tone,
            "coverage": coverage_data,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _tokens(text: str) -> set[str]:
    values: set[str] = set()
    for pattern in _DATE_PATTERNS:
        values.update(match.group(0).lower() for match in pattern.finditer(text))
    values.update(
        match.group(0).lower().replace(" ", "")
        for match in _AMOUNT_PATTERN.finditer(text)
    )
    return values


def _item(
    item_id: str,
    category: str,
    status: str,
    title: str,
    message: str,
    suggestion: str | None = None,
    *,
    source: str = "local",
) -> PreflightItem:
    return PreflightItem(
        item_id=item_id,
        category=category,
        status=status,
        title=title,
        message=message,
        suggestion=suggestion,
        source=source,
    )


def report_from_items(
    items: tuple[PreflightItem, ...],
    *,
    summary: str | None = None,
    usage_tokens: int | None = None,
) -> PreflightReport:
    overall = max(
        (item.status for item in items),
        key=lambda status: _SEVERITY[status],
        default="GOOD",
    )
    default_summary = {
        "GOOD": "邮件整体结构完整，可以进行最终人工确认。",
        "CHECK": "邮件基本完整，建议确认标记事项后发送。",
        "WARNING": "邮件存在需要重点确认的内容，建议检查后再发送。",
    }[overall]
    if summary is None or overall != "GOOD":
        summary = default_summary
    return PreflightReport(
        overall_status=overall,
        summary=summary,
        items=items,
        usage_tokens=usage_tokens,
    )


class PreflightService:
    def __init__(self, backend: PreflightBackend) -> None:
        self.backend = backend

    def build_local_items(
        self,
        *,
        analysis: IncomingEmailAnalysis,
        decisions: dict[str, dict],
        subject: str,
        body: str,
        coverage: CoverageResult | None,
    ) -> tuple[PreflightItem, ...]:
        items: list[PreflightItem] = []
        if coverage is None:
            items.append(
                _item(
                    "coverage_unavailable",
                    "coverage",
                    "CHECK",
                    "客户问题覆盖",
                    "回复覆盖结果当前不可用，无法确认是否逐项回应。",
                    "建议重新执行回复覆盖检查。",
                    source="coverage",
                )
            )
        else:
            mapping = {
                "addressed": ("GOOD", "已回复"),
                "partially_addressed": ("CHECK", "部分回复"),
                "postponed": ("CHECK", "已说明暂缓"),
                "not_addressed": ("CHECK", "没有回复"),
            }
            for coverage_item in coverage.items:
                status, label = mapping[coverage_item.status]
                items.append(
                    _item(
                        f"coverage__{coverage_item.item_id}",
                        "coverage",
                        status,
                        f"客户问题 · {coverage_item.item_id}",
                        f"{label}：{coverage_item.note}",
                        (
                            "请确认这是有意的回复安排。"
                            if coverage_item.status != "addressed"
                            else None
                        ),
                        source="coverage",
                    )
                )

        mentioned = bool(_ATTACHMENT_PATTERN.search(body))
        items.append(
            _item(
                "attachment",
                "attachment",
                "CHECK" if mentioned else "GOOD",
                "附件",
                (
                    "邮件提到了附件，请在发送前确认附件已添加。"
                    if mentioned
                    else "邮件正文未提及附件。"
                ),
                "请确认附件后再发送。" if mentioned else None,
            )
        )

        word_count = len(re.findall(r"\b[\w'-]+\b", body))
        if word_count > 700:
            length_status = "WARNING"
            length_message = f"正文约 {word_count} 个英文单词，阅读负担较大。"
        elif word_count > 450:
            length_status = "CHECK"
            length_message = f"正文约 {word_count} 个英文单词，建议确认是否精简。"
        else:
            length_status = "GOOD"
            length_message = f"正文约 {word_count} 个英文单词，长度合理。"
        items.append(
            _item(
                "email_length",
                "length",
                length_status,
                "邮件长度",
                length_message,
                "可考虑保留结论、行动和期限。" if word_count > 450 else None,
            )
        )

        public_decisions = _public_decisions(decisions)
        evidence = json.dumps(
            {
                "analysis": asdict(analysis),
                "decisions": public_decisions,
            },
            ensure_ascii=False,
        )
        added_facts = sorted(_tokens(f"{subject}\n{body}") - _tokens(evidence))
        if added_facts:
            items.append(
                _item(
                    "fact_grounding",
                    "facts",
                    "WARNING",
                    "日期与金额依据",
                    "回复出现未在来信分析或已确认决定中找到依据的内容："
                    + "、".join(added_facts),
                    "请确认这些日期或金额来自可靠信息。",
                )
            )
        else:
            items.append(
                _item(
                    "fact_grounding",
                    "facts",
                    "GOOD",
                    "日期与金额依据",
                    "未发现新增且无依据的明确日期或金额。",
                )
            )
        return tuple(items)

    def inspect(
        self,
        *,
        analysis: IncomingEmailAnalysis,
        decisions: dict[str, dict],
        subject: str,
        body: str,
        coverage: CoverageResult | None,
        target_tone: str,
    ) -> PreflightReport:
        local_items = self.build_local_items(
            analysis=analysis,
            decisions=decisions,
            subject=subject,
            body=body,
            coverage=coverage,
        )
        payload = {
            "analysis": asdict(analysis) | {"usage_tokens": None},
            "decisions": _public_decisions(decisions),
            "coverage": (
                [asdict(item) for item in coverage.items] if coverage else None
            ),
            "target_tone": target_tone,
            "email": {"subject": subject, "body": body},
        }
        semantic = self.backend.check_reply_preflight(payload=payload)
        return report_from_items(
            local_items + semantic.items,
            summary=semantic.summary,
            usage_tokens=semantic.usage_tokens,
        )
