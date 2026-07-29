"""DeepSeek API client, response parsing, signatures, and safe error mapping."""

from dataclasses import dataclass
import json
import logging
import re
from typing import Callable

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    OpenAI,
    RateLimitError,
)

from config import DeepSeekSettings
from prompts import generation_messages, improvement_messages, repair_messages


logger = logging.getLogger(__name__)


TONE_CLOSINGS = {
    "Formal": "Best regards,",
    "Friendly": "Kind regards,",
    "Strong": "Regards,",
    "Concise": "Regards,",
    "Executive": "Sincerely,",
}


class AIServiceError(Exception):
    """A safe, user-facing AI service error."""

    def __init__(self, message: str, code: str) -> None:
        super().__init__(message)
        self.user_message = message
        self.code = code


@dataclass(frozen=True)
class EmailResult:
    subject: str
    body: str
    usage_tokens: int | None = None


@dataclass(frozen=True)
class CompletionResult:
    content: str
    usage_tokens: int | None = None


@dataclass(frozen=True)
class SenderDetails:
    name: str = ""
    job_title: str = ""
    company: str = ""
    contact_information: str = ""


def build_signature(tone: str, sender: SenderDetails) -> str:
    lines = [
        TONE_CLOSINGS[tone],
        sender.name.strip(),
        sender.job_title.strip(),
        sender.company.strip(),
        sender.contact_information.strip(),
    ]
    return "\n".join(line for line in lines if line)


def strip_terminal_closing(body: str) -> str:
    """Remove only a standalone closing phrase at the very end of the body."""
    closing_pattern = re.compile(
        r"(?:^|\n)\s*(?:best regards|kind regards|regards|sincerely)[,.]?\s*$",
        flags=re.IGNORECASE,
    )
    clean_body = body.strip()
    while closing_pattern.search(clean_body):
        clean_body = closing_pattern.sub("", clean_body).rstrip()
    return clean_body


def append_signature(body: str, tone: str, sender: SenderDetails) -> str:
    clean_body = strip_terminal_closing(body)
    signature = build_signature(tone, sender)
    return f"{clean_body}\n\n{signature}" if clean_body else signature


def _extract_json_candidate(content: str) -> str:
    candidate = content.strip()
    candidate = re.sub(r"^```(?:json)?\s*", "", candidate, flags=re.IGNORECASE)
    candidate = re.sub(r"\s*```$", "", candidate)
    if candidate.startswith("{") and candidate.endswith("}"):
        return candidate
    start = candidate.find("{")
    end = candidate.rfind("}")
    if start >= 0 and end > start:
        return candidate[start : end + 1]
    return candidate


def parse_email_result(content: str) -> EmailResult:
    if not content or not content.strip():
        raise ValueError("empty response")
    data = json.loads(_extract_json_candidate(content))
    if not isinstance(data, dict):
        raise ValueError("response is not an object")

    subject = data.get("subject")
    body = data.get("body")
    if not isinstance(subject, str) or not subject.strip():
        raise ValueError("missing subject")
    if not isinstance(body, str) or not body.strip():
        raise ValueError("missing body")
    return EmailResult(subject=subject.strip(), body=body.strip())


def create_client(settings: DeepSeekSettings) -> OpenAI:
    if not settings.is_configured:
        raise AIServiceError(
            "尚未配置 DeepSeek API Key，请按照 README 中的说明完成配置。",
            "missing_api_key",
        )
    return OpenAI(
        api_key=settings.api_key,
        base_url=settings.base_url,
        timeout=settings.timeout_seconds,
        max_retries=0,
    )


def _safe_api_error(exc: Exception) -> AIServiceError:
    logger.warning("DeepSeek request failed: %s", type(exc).__name__)
    if isinstance(exc, AuthenticationError):
        return AIServiceError(
            "DeepSeek API Key无效，请检查密钥是否正确或是否已失效。",
            "invalid_api_key",
        )
    if isinstance(exc, RateLimitError):
        return AIServiceError(
            "请求过于频繁，请稍后再试。",
            "rate_limit",
        )
    if isinstance(exc, APITimeoutError):
        return AIServiceError(
            "AI生成时间过长，请稍后重试。",
            "timeout",
        )
    if isinstance(exc, APIConnectionError):
        return AIServiceError(
            "暂时无法连接DeepSeek API，请检查网络后重试。",
            "connection",
        )

    status_code = getattr(exc, "status_code", None)
    error_text = str(exc).lower()
    if status_code == 402 or "insufficient balance" in error_text:
        return AIServiceError(
            "DeepSeek API账户余额可能不足，请登录DeepSeek开放平台检查余额。",
            "insufficient_balance",
        )
    if isinstance(exc, NotFoundError) or (
        status_code == 404 and "model" in error_text
    ):
        return AIServiceError(
            "当前DeepSeek模型不可用，请检查DEEPSEEK_MODEL配置。",
            "model_unavailable",
        )
    if isinstance(exc, BadRequestError) and "model" in error_text:
        return AIServiceError(
            "当前DeepSeek模型不可用，请检查DEEPSEEK_MODEL配置。",
            "model_unavailable",
        )
    return AIServiceError(
        "邮件生成失败，请稍后重试。",
        "unknown",
    )


class DeepSeekEmailService:
    def __init__(
        self,
        settings: DeepSeekSettings,
        client_factory: Callable[[DeepSeekSettings], OpenAI] = create_client,
    ) -> None:
        self.settings = settings
        self._client_factory = client_factory

    def _completion(self, messages: list[dict[str, str]]) -> CompletionResult:
        client = self._client_factory(self.settings)
        try:
            response = client.chat.completions.create(
                model=self.settings.model,
                messages=messages,
                response_format={"type": "json_object"},
                max_tokens=self.settings.max_tokens,
                temperature=0.25,
                stream=False,
                extra_body={"thinking": {"type": "disabled"}},
            )
        except (
            AuthenticationError,
            RateLimitError,
            APITimeoutError,
            APIConnectionError,
            APIStatusError,
        ) as exc:
            raise _safe_api_error(exc) from None

        usage = getattr(response, "usage", None)
        total_tokens = getattr(usage, "total_tokens", None) if usage else None
        if not response.choices:
            return CompletionResult(content="", usage_tokens=total_tokens)
        return CompletionResult(
            content=response.choices[0].message.content or "",
            usage_tokens=total_tokens,
        )

    def _request_and_parse(
        self,
        messages: list[dict[str, str]],
    ) -> EmailResult:
        first_completion = self._completion(messages)
        try:
            parsed = parse_email_result(first_completion.content)
            return EmailResult(
                subject=parsed.subject,
                body=parsed.body,
                usage_tokens=first_completion.usage_tokens,
            )
        except (json.JSONDecodeError, ValueError):
            logger.warning("DeepSeek response parsing failed; attempting one repair")

        repaired_completion = self._completion(
            repair_messages(first_completion.content)
        )
        try:
            parsed = parse_email_result(repaired_completion.content)
            token_values = [
                value
                for value in (
                    first_completion.usage_tokens,
                    repaired_completion.usage_tokens,
                )
                if value is not None
            ]
            return EmailResult(
                subject=parsed.subject,
                body=parsed.body,
                usage_tokens=sum(token_values) if token_values else None,
            )
        except (json.JSONDecodeError, ValueError):
            raise AIServiceError(
                "AI返回结果格式异常，请重新生成。",
                "parse_error",
            ) from None

    def generate_email(
        self,
        *,
        recipient: str,
        requested_subject: str,
        chinese_brief: str,
        tone: str,
        sender: SenderDetails,
    ) -> EmailResult:
        result = self._request_and_parse(
            generation_messages(
                recipient=recipient,
                requested_subject=requested_subject,
                chinese_brief=chinese_brief,
                tone=tone,
            )
        )
        return EmailResult(
            subject=result.subject,
            body=append_signature(result.body, tone, sender),
            usage_tokens=result.usage_tokens,
        )

    def improve_email(
        self,
        *,
        original_email: str,
        tone: str,
        sender: SenderDetails,
    ) -> EmailResult:
        result = self._request_and_parse(
            improvement_messages(
                original_email=original_email,
                tone=tone,
            )
        )
        return EmailResult(
            subject=result.subject,
            body=append_signature(result.body, tone, sender),
            usage_tokens=result.usage_tokens,
        )
