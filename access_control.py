"""Small, replaceable access gate for invited external testers."""

from collections.abc import Mapping
import hmac
import os
from urllib.parse import urlparse


def configured_access_code(secrets: Mapping[str, object] | None) -> str:
    """Read the optional test code from the supplied secrets mapping only."""
    if not secrets:
        return ""
    return str(secrets.get("APP_ACCESS_CODE", "")).strip()


def verify_access_code(expected: str, provided: str) -> bool:
    """Compare non-empty access codes without exposing either value."""
    if not expected:
        return True
    return hmac.compare_digest(expected, provided)


def runtime_environment(
    app_url: str = "",
    environment: Mapping[str, str] | None = None,
) -> str:
    """Return a reader-safe environment label without exposing host details."""
    env = os.environ if environment is None else environment
    sharing_mode = env.get("STREAMLIT_SHARING_MODE", "").lower()
    hostname = (urlparse(app_url).hostname or "").lower()
    is_streamlit_cloud = sharing_mode == "true" or hostname.endswith(
        ".streamlit.app"
    )
    return "云端部署" if is_streamlit_cloud else "本地开发"
