"""DeepSeek API client, response parsing, signatures, and safe error mapping."""

from dataclasses import dataclass, replace
from contextlib import nullcontext
import hashlib
import json
import logging
import re
import time
from typing import Callable, ContextManager, Mapping
import uuid

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
from incoming_analysis_prompts import (
    incoming_analysis_messages,
    incoming_analysis_repair_messages,
)
from models.incoming_email import (
    IncomingAnalysisParseError,
    IncomingEmailAnalysis,
    parse_incoming_email_analysis,
)
from models.reply_generation import (
    CoverageResult,
    GeneratedReply,
    parse_coverage,
    parse_generated_reply,
    with_usage,
)
from models.preflight import (
    SemanticPreflightResult,
    parse_semantic_preflight,
    with_usage as with_preflight_usage,
)
from preflight_prompts import (
    preflight_check_messages,
    preflight_repair_messages,
)
from reply_prompts import (
    coverage_check_messages,
    reply_format_repair_messages,
    reply_generation_messages,
)
from communication_analysis_service import (
    CommunicationAnalysis,
    parse_communication_analysis,
)
from prompts import (
    generation_messages,
    improvement_messages,
    repair_messages,
    scenario_generation_messages,
)


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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
    communication_analysis: CommunicationAnalysis = CommunicationAnalysis()


@dataclass(frozen=True)
class CompletionResult:
    content: str
    usage_tokens: int | None = None
    choices_count: int = 0
    finish_reason: str | None = None
    response_id: str | None = None


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
    body = data.get("body", data.get("email_body"))
    if not isinstance(subject, str) or not subject.strip():
        raise ValueError("missing subject")
    if not isinstance(body, str) or not body.strip():
        raise ValueError("missing body")
    return EmailResult(
        subject=subject.strip(),
        body=body.strip(),
        communication_analysis=parse_communication_analysis(
            data.get("communication_analysis")
        ),
    )


def parse_email_fallback(content: str) -> EmailResult:
    """Extract recognizable plain-email output without exposing broken JSON."""
    candidate = content.strip()
    candidate = re.sub(r"^```(?:json|text)?\s*", "", candidate, flags=re.I)
    candidate = re.sub(r"\s*```$", "", candidate).strip()
    if not candidate or candidate.startswith("{") or candidate.startswith("["):
        raise ValueError("unsafe fallback content")

    subject_match = re.search(
        r"(?im)^\s*subject\s*:\s*(.+?)\s*$",
        candidate,
    )
    body_match = re.search(
        r"(?is)(?:^|\n)\s*(?:body|email body)\s*:\s*(.+)$",
        candidate,
    )
    if body_match:
        body = body_match.group(1).strip()
        subject = (
            subject_match.group(1).strip()
            if subject_match
            else "Business Email"
        )
    elif re.search(r"(?im)^\s*(?:dear|hello|hi)\b", candidate):
        subject = (
            subject_match.group(1).strip()
            if subject_match
            else "Business Email"
        )
        body = re.sub(
            r"(?im)^\s*subject\s*:\s*.+?\s*$",
            "",
            candidate,
            count=1,
        ).strip()
    else:
        raise ValueError("no recognizable email")

    if not body:
        raise ValueError("empty fallback body")
    return EmailResult(subject=subject, body=body)


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


def _validation_paths(exc: Exception) -> str:
    if not isinstance(exc, IncomingAnalysisParseError):
        return "analysis"
    reason = exc.reason
    suffixes = (
        "_must_be_object",
        "_must_be_text",
        "_must_not_be_empty",
        "_must_be_boolean",
    )
    for suffix in suffixes:
        if reason.endswith(suffix):
            return reason[: -len(suffix)]
    special = {
        "duplicate_item_id": "item_id",
        "unknown_related_request_id": (
            "questions_requiring_reply.related_request_id"
        ),
        "unexpected_analysis_fields": "analysis",
        "empty_analysis": "analysis",
        "invalid_or_truncated_json": "analysis",
    }
    return special.get(reason, "analysis")


def _incoming_parse_failure(
    exc: Exception,
    *,
    repair: bool,
) -> tuple[str, int, str]:
    reason = (
        exc.reason
        if isinstance(exc, IncomingAnalysisParseError)
        else "invalid_or_truncated_json"
    )
    invalid_json = reason in {
        "empty_analysis",
        "invalid_or_truncated_json",
    }
    if repair:
        code = (
            "IA_REPAIR_INVALID_JSON"
            if invalid_json
            else "IA_REPAIR_SCHEMA_VALIDATION"
        )
        return code, 10, _validation_paths(exc)
    code = "IA_INVALID_JSON" if invalid_json else "IA_SCHEMA_VALIDATION"
    stage = 6 if invalid_json else 8
    return code, stage, _validation_paths(exc)


def _raise_incoming_analysis_error(
    *,
    request_id: str,
    stage: int,
    code: str,
    started: float,
    finish_reason: str | None = None,
    repair_result: str | None = None,
) -> None:
    logger.warning(
        "incoming_analysis request_id=%s stage=%d "
        "internal_error_code=%s finish_reason=%s repair_result=%s "
        "duration_ms=%d",
        request_id,
        stage,
        code,
        finish_reason or "none",
        repair_result or "not_attempted",
        round((time.perf_counter() - started) * 1000),
    )
    messages = {
        "IA_EMPTY_CONTENT": "AI未返回可分析内容，请重新分析。",
        "IA_TRUNCATED_OUTPUT": "AI返回内容不完整，请重新分析。",
        "IA_API_ERROR": "AI服务暂时异常，请稍后重试。",
        "IA_REPAIR_EMPTY": "AI格式修复未返回内容，请重新分析。",
        "IA_REPAIR_INVALID_JSON": "AI返回分析格式异常，请重新分析。",
        "IA_REPAIR_SCHEMA_VALIDATION": (
            "AI返回分析结构异常，请重新分析。"
        ),
    }
    raise AIServiceError(
        messages.get(code, "AI返回分析格式异常，请重新分析。"),
        code,
    )


class DeepSeekEmailService:
    def __init__(
        self,
        settings: DeepSeekSettings,
        client_factory: Callable[[DeepSeekSettings], OpenAI] = create_client,
        request_guard: Callable[[], ContextManager[None]] | None = None,
    ) -> None:
        self.settings = settings
        self._client_factory = client_factory
        self._request_guard = request_guard or nullcontext

    def _completion(self, messages: list[dict[str, str]]) -> CompletionResult:
        client = self._client_factory(self.settings)
        try:
            with self._request_guard():
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
        choices = getattr(response, "choices", None) or []
        response_id = str(getattr(response, "id", "") or "") or None
        if not choices:
            return CompletionResult(
                content="",
                usage_tokens=total_tokens,
                choices_count=0,
                response_id=response_id,
            )
        choice = choices[0]
        return CompletionResult(
            content=getattr(choice.message, "content", None) or "",
            usage_tokens=total_tokens,
            choices_count=len(choices),
            finish_reason=getattr(choice, "finish_reason", None),
            response_id=response_id,
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
                communication_analysis=parsed.communication_analysis,
            )
        except (json.JSONDecodeError, ValueError):
            logger.warning("DeepSeek response parsing failed; attempting one repair")

        repaired_completion = self._completion(
            repair_messages(first_completion.content)
        )
        token_values = [
            value
            for value in (
                first_completion.usage_tokens,
                repaired_completion.usage_tokens,
            )
            if value is not None
        ]
        try:
            parsed = parse_email_result(repaired_completion.content)
            return EmailResult(
                subject=parsed.subject,
                body=parsed.body,
                usage_tokens=sum(token_values) if token_values else None,
                communication_analysis=parsed.communication_analysis,
            )
        except (json.JSONDecodeError, ValueError):
            try:
                fallback = parse_email_fallback(first_completion.content)
                return EmailResult(
                    subject=fallback.subject,
                    body=fallback.body,
                    usage_tokens=sum(token_values) if token_values else None,
                    communication_analysis=fallback.communication_analysis,
                )
            except ValueError:
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
        country_region: str = "",
        localization_context: str = "",
    ) -> EmailResult:
        result = self._request_and_parse(
            generation_messages(
                recipient=recipient,
                requested_subject=requested_subject,
                chinese_brief=chinese_brief,
                tone=tone,
                country_region=country_region,
                localization_context=localization_context,
            )
        )
        return EmailResult(
            subject=result.subject,
            body=append_signature(result.body, tone, sender),
            usage_tokens=result.usage_tokens,
            communication_analysis=result.communication_analysis,
        )

    def improve_email(
        self,
        *,
        original_email: str,
        tone: str,
        sender: SenderDetails,
        country_region: str = "",
        localization_context: str = "",
    ) -> EmailResult:
        result = self._request_and_parse(
            improvement_messages(
                original_email=original_email,
                tone=tone,
                country_region=country_region,
                localization_context=localization_context,
            )
        )
        return EmailResult(
            subject=result.subject,
            body=append_signature(result.body, tone, sender),
            usage_tokens=result.usage_tokens,
            communication_analysis=result.communication_analysis,
        )

    def generate_scenario_email(
        self,
        *,
        scenario_id: str,
        scenario_title: str,
        facts: Mapping[str, str],
        tone: str,
        sender: SenderDetails,
        recipient: str = "",
        country_region: str = "",
        localization_context: str = "",
    ) -> EmailResult:
        result = self._request_and_parse(
            scenario_generation_messages(
                scenario_id=scenario_id,
                scenario_title=scenario_title,
                facts=dict(facts),
                tone=tone,
                recipient=recipient,
                country_region=country_region,
                localization_context=localization_context,
            )
        )
        return EmailResult(
            subject=result.subject,
            body=append_signature(result.body, tone, sender),
            usage_tokens=result.usage_tokens,
            communication_analysis=result.communication_analysis,
        )

    def analyze_incoming_email(
        self,
        *,
        original_subject: str,
        original_email: str,
        country_region: str = "",
    ) -> IncomingEmailAnalysis:
        """Analyze untrusted incoming-email data without producing a reply."""
        request_id = uuid.uuid4().hex[:12]
        input_digest = hashlib.sha256(
            original_email.encode("utf-8")
        ).hexdigest()[:12]
        started = time.perf_counter()
        logger.info(
            "incoming_analysis request_id=%s stage=1 event=request_started "
            "input_length=%d input_digest=%s model=%s max_tokens=%d "
            "response_format=json_object stream=false",
            request_id,
            len(original_email),
            input_digest,
            self.settings.model,
            self.settings.max_tokens,
        )
        try:
            first_completion = self._completion(
                incoming_analysis_messages(
                    original_subject=original_subject,
                    original_email=original_email,
                    country_region=country_region,
                )
            )
        except AIServiceError as exc:
            logger.warning(
                "incoming_analysis request_id=%s stage=1 "
                "internal_error_code=IA_API_ERROR api_error_type=%s "
                "duration_ms=%d",
                request_id,
                exc.code,
                round((time.perf_counter() - started) * 1000),
            )
            raise AIServiceError(exc.user_message, "IA_API_ERROR") from None

        logger.info(
            "incoming_analysis request_id=%s stages=1-4 http_status=200 "
            "choices_count=%d finish_reason=%s output_length=%d "
            "content_empty=%s usage_tokens=%s",
            request_id,
            first_completion.choices_count,
            first_completion.finish_reason or "none",
            len(first_completion.content),
            not bool(first_completion.content.strip()),
            first_completion.usage_tokens,
        )
        if not first_completion.content.strip():
            _raise_incoming_analysis_error(
                request_id=request_id,
                stage=3,
                code="IA_EMPTY_CONTENT",
                started=started,
                finish_reason=first_completion.finish_reason,
            )
        if first_completion.finish_reason == "length":
            _raise_incoming_analysis_error(
                request_id=request_id,
                stage=4,
                code="IA_TRUNCATED_OUTPUT",
                started=started,
                finish_reason=first_completion.finish_reason,
            )
        if first_completion.finish_reason not in {None, "stop"}:
            _raise_incoming_analysis_error(
                request_id=request_id,
                stage=4,
                code="IA_API_ERROR",
                started=started,
                finish_reason=first_completion.finish_reason,
            )

        direct_json = "success"
        try:
            json.loads(first_completion.content)
        except json.JSONDecodeError:
            direct_json = "failed"
        logger.info(
            "incoming_analysis request_id=%s stage=5 json_parse=%s",
            request_id,
            direct_json,
        )
        try:
            parsed = parse_incoming_email_analysis(first_completion.content)
            logger.info(
                "incoming_analysis request_id=%s stages=6-8 "
                "schema_validation=success repair_attempted=false "
                "duration_ms=%d usage_tokens=%s",
                request_id,
                round((time.perf_counter() - started) * 1000),
                first_completion.usage_tokens,
            )
            return replace(parsed, usage_tokens=first_completion.usage_tokens)
        except (json.JSONDecodeError, ValueError) as exc:
            code, stage, paths = _incoming_parse_failure(exc, repair=False)
            logger.warning(
                "incoming_analysis request_id=%s stage=%d "
                "internal_error_code=%s schema_validation=failed "
                "validation_paths=%s repair_attempted=true",
                request_id,
                stage,
                code,
                paths,
            )

        try:
            repaired_completion = self._completion(
                incoming_analysis_repair_messages(first_completion.content)
            )
        except AIServiceError:
            _raise_incoming_analysis_error(
                request_id=request_id,
                stage=10,
                code="IA_API_ERROR",
                started=started,
                repair_result="api_error",
            )
        token_values = [
            value
            for value in (
                first_completion.usage_tokens,
                repaired_completion.usage_tokens,
            )
            if value is not None
        ]
        logger.info(
            "incoming_analysis request_id=%s stages=9-10 "
            "repair_attempted=true finish_reason=%s output_length=%d "
            "content_empty=%s usage_tokens=%s",
            request_id,
            repaired_completion.finish_reason or "none",
            len(repaired_completion.content),
            not bool(repaired_completion.content.strip()),
            repaired_completion.usage_tokens,
        )
        if not repaired_completion.content.strip():
            _raise_incoming_analysis_error(
                request_id=request_id,
                stage=10,
                code="IA_REPAIR_EMPTY",
                started=started,
                repair_result="empty_content",
            )
        if repaired_completion.finish_reason == "length":
            _raise_incoming_analysis_error(
                request_id=request_id,
                stage=10,
                code="IA_REPAIR_INVALID_JSON",
                started=started,
                finish_reason=repaired_completion.finish_reason,
                repair_result="truncated",
            )
        try:
            parsed = parse_incoming_email_analysis(
                repaired_completion.content
            )
            logger.info(
                "incoming_analysis request_id=%s stage=10 "
                "repair_result=success duration_ms=%d usage_tokens=%s",
                request_id,
                round((time.perf_counter() - started) * 1000),
                sum(token_values) if token_values else None,
            )
            return replace(
                parsed,
                usage_tokens=sum(token_values) if token_values else None,
            )
        except (json.JSONDecodeError, ValueError) as exc:
            code, _, paths = _incoming_parse_failure(exc, repair=True)
            logger.warning(
                "incoming_analysis request_id=%s stage=10 "
                "internal_error_code=%s repair_result=failed "
                "validation_paths=%s duration_ms=%d",
                request_id,
                code,
                paths,
                round((time.perf_counter() - started) * 1000),
            )
            raise AIServiceError(
                "AI返回分析格式异常，请重新分析。",
                code,
            ) from None

    def generate_reply_email(self, *, payload: dict) -> GeneratedReply:
        first = self._completion(reply_generation_messages(payload))
        try:
            return with_usage(
                parse_generated_reply(first.content), first.usage_tokens
            )
        except (json.JSONDecodeError, ValueError):
            logger.warning("Reply generation parsing failed; attempting one repair")
        repaired = self._completion(
            reply_format_repair_messages(first.content, coverage=False)
        )
        tokens = [
            value
            for value in (first.usage_tokens, repaired.usage_tokens)
            if value is not None
        ]
        try:
            return with_usage(
                parse_generated_reply(repaired.content),
                sum(tokens) if tokens else None,
            )
        except (json.JSONDecodeError, ValueError):
            raise AIServiceError(
                "AI返回回复格式异常，请重新生成。",
                "reply_parse_error",
            ) from None

    def check_reply_coverage(
        self,
        *,
        payload: dict,
        expected_item_ids: tuple[str, ...],
    ) -> CoverageResult:
        first = self._completion(coverage_check_messages(payload))
        try:
            return with_usage(
                parse_coverage(first.content, expected_item_ids),
                first.usage_tokens,
            )
        except (json.JSONDecodeError, ValueError):
            logger.warning("Coverage parsing failed; attempting one repair")
        repaired = self._completion(
            reply_format_repair_messages(first.content, coverage=True)
        )
        tokens = [
            value
            for value in (first.usage_tokens, repaired.usage_tokens)
            if value is not None
        ]
        try:
            return with_usage(
                parse_coverage(repaired.content, expected_item_ids),
                sum(tokens) if tokens else None,
            )
        except (json.JSONDecodeError, ValueError):
            raise AIServiceError(
                "覆盖检查返回格式异常，请重新检查。",
                "coverage_parse_error",
            ) from None

    def check_reply_preflight(
        self, *, payload: dict
    ) -> SemanticPreflightResult:
        first = self._completion(preflight_check_messages(payload))
        try:
            return with_preflight_usage(
                parse_semantic_preflight(first.content),
                first.usage_tokens,
            )
        except (json.JSONDecodeError, ValueError):
            logger.warning("Preflight parsing failed; attempting one repair")
        repaired = self._completion(
            preflight_repair_messages(first.content)
        )
        tokens = [
            value
            for value in (first.usage_tokens, repaired.usage_tokens)
            if value is not None
        ]
        try:
            return with_preflight_usage(
                parse_semantic_preflight(repaired.content),
                sum(tokens) if tokens else None,
            )
        except (json.JSONDecodeError, ValueError):
            raise AIServiceError(
                "发送前检查返回格式异常，请重新检查。",
                "preflight_parse_error",
            ) from None
