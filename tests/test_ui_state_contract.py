import unittest
from unittest.mock import patch

from ui import state


class UIStateImportContractTests(unittest.TestCase):
    def test_guided_workflow_state_api_is_importable(self) -> None:
        required_functions = (
            "advance_compose_question",
            "back_compose_question",
            "save_compose_answer",
            "return_to_compose_review",
            "edit_compose_answer",
            "set_compose_task",
            "set_compose_step",
        )
        self.assertTrue(set(required_functions).issubset(state.__all__))
        for function_name in required_functions:
            self.assertTrue(callable(getattr(state, function_name, None)))

    def test_compose_page_imports_only_declared_state_api(self) -> None:
        from ui.pages import compose_supplier

        for function_name in (
            "advance_compose_question",
            "back_compose_question",
            "save_compose_answer",
            "return_to_compose_review",
            "edit_compose_answer",
        ):
            self.assertIs(
                getattr(compose_supplier, function_name),
                getattr(state, function_name),
            )

    def test_reply_workspace_state_api_is_declared_and_callable(self) -> None:
        for function_name in (
            "open_reply_workspace",
            "sync_reply_source",
            "return_to_reply_input",
            "clear_reply_state",
        ):
            self.assertIn(function_name, state.__all__)
            self.assertTrue(callable(getattr(state, function_name, None)))

    def test_reply_source_change_invalidates_analysis_and_decisions(self) -> None:
        session = {
            **state.REPLY_DEFAULTS,
            "reply__original_subject": "Changed",
            "reply__original_email": "Changed email",
            "reply__country_region": "Other / 其他地区",
            "reply__source_digest": "stale",
            "reply__analysis": object(),
            "reply__analysis_digest": "stale",
            "reply__normalized_items": (object(),),
            "reply__decisions": {"request_1": {"stance": "accept"}},
            "reply__decision_summary": object(),
        }
        with patch.object(state.st, "session_state", session):
            state.sync_reply_source()
        self.assertIsNone(session["reply__analysis"])
        self.assertEqual(session["reply__decisions"], {})
        self.assertEqual(session["reply__normalized_items"], ())
        self.assertIsNone(session["reply__decision_summary"])

    def test_clear_reply_decisions_preserves_analysis(self) -> None:
        analysis = object()
        session = {
            **state.REPLY_DEFAULTS,
            "reply__analysis": analysis,
            "reply__analysis_digest": "same",
            "reply__source_digest": "same",
            "reply__decisions": {"request_1": {"stance": "accept"}},
            "reply__step": 2,
        }
        with patch.object(state.st, "session_state", session):
            state.clear_reply_decisions()
        self.assertIs(session["reply__analysis"], analysis)
        self.assertEqual(session["reply__decisions"], {})
        self.assertEqual(session["reply__step"], 1)

    def test_start_reply_decisions_sets_items_without_ai_state(self) -> None:
        items = (object(), object())
        session = {**state.REPLY_DEFAULTS}
        with patch.object(state.st, "session_state", session):
            state.start_reply_decisions(items)
        self.assertEqual(session["reply__normalized_items"], items)
        self.assertEqual(session["reply__current_item_index"], 0)
        self.assertEqual(session["reply__step"], 2)
        self.assertEqual(session["reply__request_status"], "idle")
