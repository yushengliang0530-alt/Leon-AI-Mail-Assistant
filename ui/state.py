"""Minimal Phase 1A state for the V2.0 home prototype."""

import streamlit as st


HOME_VIEW_KEY = "system__home_view"
HOME_ACTION_KEY = "system__selected_home_action"
SUPPLIER_VIEW = "compose_supplier"

COMPOSE_DEFAULTS = {
    "compose__scenario_family": "follow_up_supplier",
    "compose__task_id": "",
    "compose__step": 1,
    "compose__fields": {},
    "compose__result_subject": "",
    "compose__result_body": "",
    "compose__analysis": None,
    "compose__duration_seconds": None,
    "compose__usage_tokens": None,
    "compose__request_in_progress": False,
    "compose__error": "",
}


def initialize_home_state() -> None:
    if HOME_VIEW_KEY not in st.session_state:
        st.session_state[HOME_VIEW_KEY] = "home"
    if HOME_ACTION_KEY not in st.session_state:
        st.session_state[HOME_ACTION_KEY] = None
    for key, value in COMPOSE_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = (
                value.copy() if isinstance(value, dict) else value
            )


def set_selected_home_action(action: str) -> None:
    st.session_state[HOME_ACTION_KEY] = action


def get_selected_home_action() -> str | None:
    value = st.session_state.get(HOME_ACTION_KEY)
    return value if isinstance(value, str) else None


def open_legacy_improve() -> None:
    st.session_state[HOME_VIEW_KEY] = "legacy_improve"
    st.session_state["writing_mode"] = "优化英文邮件"


def open_supplier_workflow() -> None:
    st.session_state[HOME_VIEW_KEY] = SUPPLIER_VIEW
    st.session_state[HOME_ACTION_KEY] = None


def set_compose_task(task_id: str) -> None:
    previous = str(st.session_state.get("compose__task_id", ""))
    if previous and previous != task_id:
        for key in tuple(st.session_state):
            if key.startswith("compose__field__"):
                del st.session_state[key]
        st.session_state["compose__fields"] = {}
        st.session_state["compose__result_subject"] = ""
        st.session_state["compose__result_body"] = ""
        st.session_state["compose__analysis"] = None
    st.session_state["compose__task_id"] = task_id
    st.session_state["compose__step"] = 2
    st.session_state["compose__error"] = ""


def set_compose_step(step: int) -> None:
    st.session_state["compose__step"] = max(1, min(3, int(step)))
    st.session_state["compose__error"] = ""


def return_to_home() -> None:
    st.session_state[HOME_VIEW_KEY] = "home"
    st.session_state[HOME_ACTION_KEY] = None


def get_home_view() -> str:
    return str(st.session_state.get(HOME_VIEW_KEY, "home"))
