"""Phase 3C orchestration without UI or automatic background calls."""

from dataclasses import asdict
from typing import Protocol

from ai_service import SenderDetails, append_signature
from models.incoming_email import IncomingEmailAnalysis
from models.reply_decision import ReplyItem
from models.reply_generation import CoverageResult, GeneratedReply


class ReplyBackend(Protocol):
    def generate_reply_email(self, *, payload: dict) -> GeneratedReply: ...

    def check_reply_coverage(
        self, *, payload: dict, expected_item_ids: tuple[str, ...]
    ) -> CoverageResult: ...


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


class ReplyGenerationService:
    def __init__(self, backend: ReplyBackend) -> None:
        self.backend = backend

    def generate(
        self,
        *,
        analysis: IncomingEmailAnalysis,
        items: tuple[ReplyItem, ...],
        decisions: dict[str, dict],
        sender: SenderDetails,
        country_region: str = "",
    ) -> GeneratedReply:
        payload = {
            "analysis": asdict(analysis)
            | {"usage_tokens": None},
            "items": [asdict(item) for item in items],
            "decisions": _public_decisions(decisions),
            "country_region": country_region or None,
        }
        result = self.backend.generate_reply_email(payload=payload)
        return GeneratedReply(
            subject=result.subject,
            body=append_signature(result.body, "Formal", sender),
            usage_tokens=result.usage_tokens,
        )

    def check_coverage(
        self,
        *,
        items: tuple[ReplyItem, ...],
        decisions: dict[str, dict],
        subject: str,
        body: str,
    ) -> CoverageResult:
        payload = {
            "items": [asdict(item) for item in items],
            "decisions": _public_decisions(decisions),
            "email": {"subject": subject, "body": body},
        }
        return self.backend.check_reply_coverage(
            payload=payload,
            expected_item_ids=tuple(item.item_id for item in items),
        )
