"""Validated service boundary for incoming-email analysis."""

import hashlib
from typing import Protocol

from models.incoming_email import IncomingEmailAnalysis


DEFAULT_MAX_INCOMING_EMAIL_CHARS = 12_000


class IncomingEmailInputError(ValueError):
    """A safe validation error raised before an AI request."""


class IncomingAnalysisBackend(Protocol):
    def analyze_incoming_email(
        self,
        *,
        original_subject: str,
        original_email: str,
        country_region: str,
    ) -> IncomingEmailAnalysis: ...


def source_digest(subject: str, email: str, country_region: str) -> str:
    normalized = "\n".join(
        (
            str(subject).strip(),
            str(email).strip(),
            str(country_region).strip(),
        )
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class IncomingEmailAnalysisService:
    def __init__(
        self,
        backend: IncomingAnalysisBackend,
        *,
        max_input_chars: int = DEFAULT_MAX_INCOMING_EMAIL_CHARS,
    ) -> None:
        self._backend = backend
        self.max_input_chars = max_input_chars

    def analyze(
        self,
        *,
        original_subject: str,
        original_email: str,
        country_region: str,
    ) -> IncomingEmailAnalysis:
        clean_email = str(original_email).strip()
        if not clean_email:
            raise IncomingEmailInputError("请先粘贴收到的邮件。")
        if len(original_email) > self.max_input_chars:
            raise IncomingEmailInputError(
                f"邮件内容不能超过 {self.max_input_chars:,} 个字符。"
                "请只保留与本次回复相关的邮件内容后再分析。"
            )
        return self._backend.analyze_incoming_email(
            original_subject=str(original_subject).strip(),
            original_email=clean_email,
            country_region=str(country_region).strip(),
        )
