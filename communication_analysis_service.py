"""Structured business-communication analysis and safe fallback values."""

from dataclasses import dataclass
from typing import Any, Mapping


ANALYSIS_UNAVAILABLE = "暂时无法完成完整分析，请人工检查邮件内容。"


@dataclass(frozen=True)
class CommunicationAnalysis:
    purpose: str = ANALYSIS_UNAVAILABLE
    action_required: str = "建议检查"
    deadline: str = "建议检查"
    tone: str = "建议检查"
    commitment_risk: str = "建议检查"
    ambiguity_risk: str = "建议检查"
    localization_note: str = "建议核对收件人的正式称谓和沟通习惯。"
    improvement_suggestions: tuple[str, ...] = ()
    available: bool = False


def _text(value: Any, default: str) -> str:
    return value.strip() if isinstance(value, str) and value.strip() else default


def parse_communication_analysis(
    value: Any,
) -> CommunicationAnalysis:
    if not isinstance(value, Mapping):
        return CommunicationAnalysis()

    suggestions_value = value.get("improvement_suggestions", ())
    suggestions: tuple[str, ...]
    if isinstance(suggestions_value, list):
        suggestions = tuple(
            item.strip()
            for item in suggestions_value
            if isinstance(item, str) and item.strip()
        )
    else:
        suggestions = ()

    return CommunicationAnalysis(
        purpose=_text(value.get("purpose"), "建议检查"),
        action_required=_text(value.get("action_required"), "建议检查"),
        deadline=_text(value.get("deadline"), "建议检查"),
        tone=_text(value.get("tone"), "建议检查"),
        commitment_risk=_text(value.get("commitment_risk"), "建议检查"),
        ambiguity_risk=_text(value.get("ambiguity_risk"), "建议检查"),
        localization_note=_text(
            value.get("localization_note"),
            "建议核对收件人的正式称谓和沟通习惯。",
        ),
        improvement_suggestions=suggestions,
        available=True,
    )
