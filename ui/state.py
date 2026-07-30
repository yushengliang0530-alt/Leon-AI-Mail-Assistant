"""Minimal Phase 1A state for the V2.0 home prototype."""

import streamlit as st


HOME_VIEW_KEY = "system__home_view"
HOME_ACTION_KEY = "system__selected_home_action"


def initialize_home_state() -> None:
    if HOME_VIEW_KEY not in st.session_state:
        st.session_state[HOME_VIEW_KEY] = "home"
    if HOME_ACTION_KEY not in st.session_state:
        st.session_state[HOME_ACTION_KEY] = None


def set_selected_home_action(action: str) -> None:
    st.session_state[HOME_ACTION_KEY] = action


def get_selected_home_action() -> str | None:
    value = st.session_state.get(HOME_ACTION_KEY)
    return value if isinstance(value, str) else None


def open_legacy_improve() -> None:
    st.session_state[HOME_VIEW_KEY] = "legacy_improve"
    st.session_state["writing_mode"] = "优化英文邮件"


def return_to_home() -> None:
    st.session_state[HOME_VIEW_KEY] = "home"
    st.session_state[HOME_ACTION_KEY] = None


def get_home_view() -> str:
    return str(st.session_state.get(HOME_VIEW_KEY, "home"))
