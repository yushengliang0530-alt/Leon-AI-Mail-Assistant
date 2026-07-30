"""Minimal Phase 1A state for the V2.0 home prototype."""

import streamlit as st


__all__ = [
    "advance_compose_question",
    "back_compose_question",
    "edit_compose_answer",
    "get_home_view",
    "get_selected_home_action",
    "initialize_home_state",
    "open_legacy_improve",
    "open_supplier_workflow",
    "return_to_compose_review",
    "return_to_home",
    "save_compose_answer",
    "set_compose_step",
    "set_compose_task",
    "set_selected_home_action",
]


HOME_VIEW_KEY = "system__home_view"
HOME_ACTION_KEY = "system__selected_home_action"
SUPPLIER_VIEW = "compose_supplier"

COMPOSE_DEFAULTS = {
    "compose__scenario_family": "follow_up_supplier",
    "compose__task_id": "",
    "compose__step": 1,
    "compose__question_index": 0,
    "compose__answers": {},
    "compose__completed_questions": (),
    "compose__review_ready": False,
    "compose__review_confirmed": False,
    "compose__edit_field_key": "",
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
    if previous != task_id:
        for key in tuple(st.session_state):
            if key.startswith("compose__answer_widget__"):
                del st.session_state[key]
        st.session_state["compose__question_index"] = 0
        st.session_state["compose__answers"] = {}
        st.session_state["compose__completed_questions"] = ()
        st.session_state["compose__review_ready"] = False
        st.session_state["compose__review_confirmed"] = False
        st.session_state["compose__edit_field_key"] = ""
        st.session_state["compose__fields"] = {}
        st.session_state["compose__result_subject"] = ""
        st.session_state["compose__result_body"] = ""
        st.session_state["compose__analysis"] = None
    st.session_state["compose__task_id"] = task_id
    st.session_state["compose__step"] = 2
    st.session_state["compose__error"] = ""


def set_compose_step(step: int) -> None:
    st.session_state["compose__step"] = max(1, min(4, int(step)))
    st.session_state["compose__error"] = ""


def save_compose_answer(field_key: str, value: str, *, completed: bool) -> None:
    answers = dict(st.session_state.get("compose__answers", {}))
    clean_value = str(value).strip()
    if clean_value:
        answers[field_key] = clean_value
    else:
        answers.pop(field_key, None)
    st.session_state["compose__answers"] = answers

    completed_keys = list(
        st.session_state.get("compose__completed_questions", ())
    )
    if completed and field_key not in completed_keys:
        completed_keys.append(field_key)
    st.session_state["compose__completed_questions"] = tuple(completed_keys)
    st.session_state["compose__review_confirmed"] = False
    st.session_state["compose__result_subject"] = ""
    st.session_state["compose__result_body"] = ""
    st.session_state["compose__analysis"] = None


def advance_compose_question(total_questions: int) -> None:
    current = int(st.session_state.get("compose__question_index", 0))
    if current + 1 >= total_questions:
        st.session_state["compose__review_ready"] = True
        st.session_state["compose__step"] = 3
    else:
        st.session_state["compose__question_index"] = current + 1
    st.session_state["compose__error"] = ""


def back_compose_question() -> None:
    current = int(st.session_state.get("compose__question_index", 0))
    if current <= 0:
        st.session_state["compose__step"] = 1
    else:
        st.session_state["compose__question_index"] = current - 1
    st.session_state["compose__error"] = ""


def edit_compose_answer(field_key: str, question_index: int) -> None:
    st.session_state["compose__edit_field_key"] = field_key
    st.session_state["compose__question_index"] = question_index
    st.session_state["compose__step"] = 2
    st.session_state["compose__error"] = ""


def return_to_compose_review() -> None:
    st.session_state["compose__edit_field_key"] = ""
    st.session_state["compose__review_ready"] = True
    st.session_state["compose__step"] = 3
    st.session_state["compose__error"] = ""


def return_to_home() -> None:
    st.session_state[HOME_VIEW_KEY] = "home"
    st.session_state[HOME_ACTION_KEY] = None


def get_home_view() -> str:
    return str(st.session_state.get(HOME_VIEW_KEY, "home"))
