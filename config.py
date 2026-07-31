"""Application configuration loaded from safe runtime sources."""

from dataclasses import dataclass
import os
from typing import Mapping, Any

from product_identity import (
    APP_BRAND,
    APP_NAME_EN,
    APP_NAME_ZH,
    APP_VERSION,
    APP_VERSION_LABEL,
    PRODUCT_NAME_EN,
    PRODUCT_NAME_ZH,
)


DEFAULT_MODEL = "deepseek-v4-flash"
DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_TIMEOUT_SECONDS = 45.0
DEFAULT_MAX_TOKENS = 1600
MAX_INPUT_CHARS = 8000


@dataclass(frozen=True)
class DeepSeekSettings:
    api_key: str
    model: str
    base_url: str
    timeout_seconds: float
    max_tokens: int

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)


def load_settings(secrets: Mapping[str, Any] | None = None) -> DeepSeekSettings:
    """Load secrets first, then environment overrides where specified."""
    secrets = secrets or {}
    api_key = str(secrets.get("DEEPSEEK_API_KEY", "")).strip()
    if not api_key:
        api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()

    model = os.getenv("DEEPSEEK_MODEL", "").strip()
    if not model:
        model = str(secrets.get("DEEPSEEK_MODEL", DEFAULT_MODEL)).strip()

    base_url = os.getenv("DEEPSEEK_BASE_URL", "").strip()
    if not base_url:
        base_url = str(
            secrets.get("DEEPSEEK_BASE_URL", DEFAULT_BASE_URL)
        ).strip()

    return DeepSeekSettings(
        api_key=api_key,
        model=model or DEFAULT_MODEL,
        base_url=base_url or DEFAULT_BASE_URL,
        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
        max_tokens=DEFAULT_MAX_TOKENS,
    )
