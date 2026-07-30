import unittest

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
