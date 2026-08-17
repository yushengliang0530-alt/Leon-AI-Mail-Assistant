"""Minimal Phase 1A state for the V2.0 home prototype."""

import streamlit as st


__all__ = [
    "advance_compose_question",
    "back_compose_question",
    "edit_compose_answer",
    "get_active_page",
    "get_home_view",
    "get_selected_home_action",
    "initialize_home_state",
    "invalidate_preflight",
    "open_create_workspace",
    "open_explore_more",
    "open_improve_workspace",
    "open_legacy_create_editor",
    "open_legacy_improve",
    "open_reply_workspace",
    "open_supplier_workflow",
    "clear_reply_decisions",
    "clear_reply_state",
    "prepare_reply_reanalysis",
    "return_to_reply_analysis",
    "return_to_reply_decisions",
    "return_to_reply_input",
    "reset_preflight_state",
    "set_reply_item_index",
    "start_reply_decisions",
    "return_to_compose_review",
    "return_to_home",
    "save_compose_answer",
    "set_compose_step",
    "set_compose_task",
    "set_selected_home_action",
    "sync_reply_source",
]


HOME_VIEW_KEY = "system__home_view"
HOME_ACTION_KEY = "system__selected_home_action"
ACTIVE_PAGE_KEY = "system__active_page"
WORKSPACE_KEY = "system__workspace"
NAVIGATION_HISTORY_KEY = "system__navigation_history"
SUPPLIER_VIEW = "compose_supplier"
REPLY_VIEW = "reply_analysis"
CREATE_VIEW = "create_workspace"
EXPLORE_VIEW = "explore_more"
LEGACY_CREATE_VIEW = "legacy_create"
LEGACY_IMPROVE_VIEW = "legacy_improve"

HOME_PAGE = "home"
REPLY_PAGE = "reply_workspace"
SUPPLIER_PAGE = "supplier_workspace"
IMPROVE_PAGE = "improve_workspace"
CREATE_PAGE = "create_workspace"
EXPLORE_PAGE = "explore_more"
CREATE_EDITOR_PAGE = "legacy_create_editor"
IMPROVE_EDITOR_PAGE = "legacy_improve_editor"

_LEGACY_VIEW_TO_PAGE = {
    "home": HOME_PAGE,
    REPLY_VIEW: REPLY_PAGE,
    SUPPLIER_VIEW: SUPPLIER_PAGE,
    LEGACY_IMPROVE_VIEW: IMPROVE_EDITOR_PAGE,
    CREATE_VIEW: CREATE_PAGE,
    EXPLORE_VIEW: EXPLORE_PAGE,
    LEGACY_CREATE_VIEW: CREATE_EDITOR_PAGE,
}

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

REPLY_DEFAULTS = {
    "reply__step": 1,
    "reply__original_subject": "",
    "reply__original_email": "",
    "reply__country_region": "",
    "reply__preserved_subject": "",
    "reply__preserved_email": "",
    "reply__preserved_country_region": "",
    "reply__source_digest": "",
    "reply__risk_result": None,
    "reply__risk_confirmed_digest": "",
    "reply__analysis": None,
    "reply__analysis_digest": "",
    "reply__request_status": "idle",
    "reply__safe_error": "",
    "reply__duration": None,
    "reply__tokens": None,
    "reply__normalized_items": (),
    "reply__zero_item_choice": None,
    "reply__acknowledgement_requested": False,
    "reply__decisions": {},
    "reply__decision_digest": "",
    "reply__current_item_index": 0,
    "reply__decision_risk": None,
    "reply__decision_risk_confirmed_digest": "",
    "reply__decision_summary": None,
    "reply__decision_error": "",
    "reply__show_all_items": False,
    "reply__decision_widget_epoch": 0,
    "reply__generated_email": None,
    "reply__subject": "",
    "reply__body": "",
    "reply__coverage": None,
    "reply__summary": "",
    "reply__generation_digest": "",
    "reply__coverage_digest": "",
    "reply__generation_status": "idle",
    "reply__coverage_status": "idle",
    "reply__generation_error": "",
    "reply__coverage_error": "",
    "reply__generation_duration": None,
    "reply__coverage_duration": None,
    "reply__generation_tokens": None,
    "reply__coverage_tokens": None,
    "reply__target_tone": "Formal",
}

PREFLIGHT_DEFAULTS = {
    "preflight__status": "idle",
    "preflight__source_digest": "",
    "preflight__local_items": (),
    "preflight__ai_items": (),
    "preflight__report": None,
    "preflight__error": "",
    "preflight__duration_seconds": None,
    "preflight__usage_tokens": None,
}


def initialize_home_state() -> None:
    if HOME_VIEW_KEY not in st.session_state:
        st.session_state[HOME_VIEW_KEY] = "home"
    if HOME_ACTION_KEY not in st.session_state:
        st.session_state[HOME_ACTION_KEY] = None
    if ACTIVE_PAGE_KEY not in st.session_state:
        st.session_state[ACTIVE_PAGE_KEY] = HOME_PAGE
    if WORKSPACE_KEY not in st.session_state:
        st.session_state[WORKSPACE_KEY] = ""
    if NAVIGATION_HISTORY_KEY not in st.session_state:
        st.session_state[NAVIGATION_HISTORY_KEY] = ()
    for key, value in COMPOSE_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = (
                value.copy() if isinstance(value, dict) else value
            )
    for key, value in REPLY_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = (
                value.copy() if isinstance(value, dict) else value
            )
    for key, value in PREFLIGHT_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


def set_selected_home_action(action: str) -> None:
    st.session_state[HOME_ACTION_KEY] = action


def get_selected_home_action() -> str | None:
    value = st.session_state.get(HOME_ACTION_KEY)
    return value if isinstance(value, str) else None


def open_legacy_improve() -> None:
    _navigate_to(IMPROVE_EDITOR_PAGE, "improve", LEGACY_IMPROVE_VIEW)
    st.session_state["writing_mode"] = "优化英文邮件"


def open_supplier_workflow() -> None:
    _navigate_to(SUPPLIER_PAGE, "supplier", SUPPLIER_VIEW)


def open_reply_workspace() -> None:
    _navigate_to(REPLY_PAGE, "reply", REPLY_VIEW)


def open_create_workspace() -> None:
    """Open the presentation-only Create Email workspace shell."""
    _navigate_to(CREATE_PAGE, "create", CREATE_VIEW)


def open_explore_more() -> None:
    """Open the task catalog without touching any business workflow state."""
    _navigate_to(EXPLORE_PAGE, "explore", EXPLORE_VIEW)


def open_improve_workspace() -> None:
    """Open the presentation shell that preserves the current optimize editor."""
    _navigate_to(IMPROVE_PAGE, "improve", "improve_workspace")


def open_legacy_create_editor() -> None:
    """Open the existing V1 create-email UI without changing its behavior."""
    _navigate_to(CREATE_EDITOR_PAGE, "create", LEGACY_CREATE_VIEW)
    st.session_state["writing_mode"] = "写英文邮件"


def _navigate_to(page: str, workspace: str, legacy_view: str) -> None:
    current = str(st.session_state.get(ACTIVE_PAGE_KEY, HOME_PAGE))
    history = tuple(st.session_state.get(NAVIGATION_HISTORY_KEY, ()))
    if current != page:
        st.session_state[NAVIGATION_HISTORY_KEY] = history + (current,)
    st.session_state[ACTIVE_PAGE_KEY] = page
    st.session_state[WORKSPACE_KEY] = workspace
    st.session_state[HOME_VIEW_KEY] = legacy_view
    st.session_state[HOME_ACTION_KEY] = None


def sync_reply_source() -> None:
    from services.incoming_email_analysis import source_digest

    digest = source_digest(
        str(st.session_state.get("reply__original_subject", "")),
        str(st.session_state.get("reply__original_email", "")),
        str(st.session_state.get("reply__country_region", "")),
    )
    if digest == st.session_state.get("reply__source_digest"):
        return
    st.session_state["reply__source_digest"] = digest
    st.session_state["reply__risk_result"] = None
    st.session_state["reply__risk_confirmed_digest"] = ""
    st.session_state["reply__analysis"] = None
    st.session_state["reply__analysis_digest"] = ""
    st.session_state["reply__request_status"] = "idle"
    st.session_state["reply__safe_error"] = ""
    st.session_state["reply__duration"] = None
    st.session_state["reply__tokens"] = None
    _clear_reply_decision_values()


def return_to_reply_input() -> None:
    st.session_state["reply__step"] = 1
    st.session_state["reply__safe_error"] = ""


def prepare_reply_reanalysis() -> None:
    st.session_state["reply__original_subject"] = str(
        st.session_state.get("reply__preserved_subject", "")
    )
    st.session_state["reply__original_email"] = str(
        st.session_state.get("reply__preserved_email", "")
    )
    st.session_state["reply__country_region"] = str(
        st.session_state.get("reply__preserved_country_region", "")
    )
    st.session_state["reply__analysis"] = None
    st.session_state["reply__analysis_digest"] = ""
    st.session_state["reply__request_status"] = "idle"
    st.session_state["reply__safe_error"] = ""
    st.session_state["reply__duration"] = None
    st.session_state["reply__tokens"] = None
    _clear_reply_decision_values()
    st.session_state["reply__step"] = 1


def _clear_reply_decision_widgets() -> None:
    for key in tuple(st.session_state):
        if key.startswith("reply__decision_widget__"):
            del st.session_state[key]


def _clear_reply_decision_values() -> None:
    st.session_state["reply__normalized_items"] = ()
    st.session_state["reply__zero_item_choice"] = None
    st.session_state["reply__acknowledgement_requested"] = False
    st.session_state["reply__decisions"] = {}
    st.session_state["reply__decision_digest"] = ""
    st.session_state["reply__current_item_index"] = 0
    st.session_state["reply__decision_risk"] = None
    st.session_state["reply__decision_risk_confirmed_digest"] = ""
    st.session_state["reply__decision_summary"] = None
    st.session_state["reply__decision_error"] = ""
    st.session_state["reply__show_all_items"] = False
    st.session_state["reply__decision_widget_epoch"] = (
        int(st.session_state.get("reply__decision_widget_epoch", 0)) + 1
    )
    _clear_reply_decision_widgets()
    _clear_reply_generation_values()


def _clear_reply_generation_values() -> None:
    for key in (
        "reply__generated_email",
        "reply__coverage",
        "reply__generation_duration",
        "reply__coverage_duration",
        "reply__generation_tokens",
        "reply__coverage_tokens",
    ):
        st.session_state[key] = None
    for key in (
        "reply__subject",
        "reply__body",
        "reply__summary",
        "reply__generation_digest",
        "reply__coverage_digest",
        "reply__generation_error",
        "reply__coverage_error",
    ):
        st.session_state[key] = ""
    st.session_state["reply__generation_status"] = "idle"
    st.session_state["reply__coverage_status"] = "idle"
    reset_preflight_state()


def reset_preflight_state() -> None:
    for key, value in PREFLIGHT_DEFAULTS.items():
        st.session_state[key] = value


def invalidate_preflight() -> None:
    st.session_state["preflight__status"] = "stale"
    st.session_state["preflight__source_digest"] = ""
    st.session_state["preflight__report"] = None
    st.session_state["preflight__local_items"] = ()
    st.session_state["preflight__ai_items"] = ()
    st.session_state["preflight__error"] = ""
    st.session_state["preflight__duration_seconds"] = None
    st.session_state["preflight__usage_tokens"] = None


def start_reply_decisions(items: tuple[object, ...]) -> None:
    st.session_state["reply__normalized_items"] = items
    st.session_state["reply__acknowledgement_requested"] = bool(
        len(items) == 1
        and getattr(items[0], "item_type", "") == "acknowledgement"
    )
    st.session_state["reply__current_item_index"] = 0
    st.session_state["reply__decision_error"] = ""
    st.session_state["reply__decision_widget_epoch"] = (
        int(st.session_state.get("reply__decision_widget_epoch", 0)) + 1
    )
    st.session_state["reply__step"] = 3


def set_reply_item_index(index: int) -> None:
    items = tuple(st.session_state.get("reply__normalized_items", ()))
    upper = max(0, len(items) - 1)
    target = max(0, min(int(index), upper))
    st.session_state["reply__current_item_index"] = target
    st.session_state["reply__decision_widget_epoch"] = (
        int(st.session_state.get("reply__decision_widget_epoch", 0)) + 1
    )
    st.session_state["reply__decision_error"] = ""


def return_to_reply_analysis() -> None:
    st.session_state["reply__step"] = 2
    st.session_state["reply__decision_error"] = ""


def return_to_reply_decisions() -> None:
    st.session_state["reply__step"] = 3
    st.session_state["reply__decision_summary"] = None
    st.session_state["reply__decision_widget_epoch"] = (
        int(st.session_state.get("reply__decision_widget_epoch", 0)) + 1
    )
    st.session_state["reply__decision_error"] = ""


def clear_reply_decisions() -> None:
    _clear_reply_decision_values()
    st.session_state["reply__step"] = 1


def clear_reply_state() -> None:
    for key in tuple(st.session_state):
        if key.startswith("reply__"):
            del st.session_state[key]
    for key, value in REPLY_DEFAULTS.items():
        st.session_state[key] = value
    reset_preflight_state()


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
    st.session_state[ACTIVE_PAGE_KEY] = HOME_PAGE
    st.session_state[WORKSPACE_KEY] = ""


def get_home_view() -> str:
    return str(st.session_state.get(HOME_VIEW_KEY, "home"))


def get_active_page() -> str:
    """Return the presentation route while accepting legacy deep links."""
    active_page = str(st.session_state.get(ACTIVE_PAGE_KEY, HOME_PAGE))
    legacy_view = get_home_view()
    expected_page = _LEGACY_VIEW_TO_PAGE.get(legacy_view, IMPROVE_PAGE)
    if active_page == HOME_PAGE and expected_page != HOME_PAGE:
        return expected_page
    return active_page
