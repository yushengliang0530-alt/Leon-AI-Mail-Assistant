"""Bind each public Streamlit session to one shared, thread-safe allowance."""

from contextlib import contextmanager
from uuid import uuid4

import streamlit as st

from ai_service import AIServiceError
from public_usage import PublicUsage, UsageLimitError


@st.cache_resource(show_spinner=False)
def public_allowance() -> PublicUsage:
    # shortcut: process memory resets on restart; use durable metering before scaling out.
    return PublicUsage()


def session_request_guard():
    if "public__usage_session" not in st.session_state:
        st.session_state["public__usage_session"] = uuid4().hex
    session_id = st.session_state["public__usage_session"]
    allowance = public_allowance()

    @contextmanager
    def guard():
        try:
            with allowance.reserve(session_id):
                yield
        except UsageLimitError as exc:
            raise AIServiceError(str(exc), "public_usage_limit") from None

    return guard
