"""Reader-safe environment label; public workspaces have no access-code gate."""

from collections.abc import Mapping
import os
from urllib.parse import urlparse


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
