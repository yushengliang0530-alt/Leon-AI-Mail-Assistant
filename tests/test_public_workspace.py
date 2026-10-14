import ast
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from ai_service import AIServiceError, DeepSeekEmailService, SenderDetails
from config import load_settings
from public_usage import PublicUsage
from tests.test_ai_service import FakeClient
from ui.public_usage import session_request_guard


ROOT = Path(__file__).resolve().parents[1]
RESULT = json.dumps({"subject": "Synthetic test", "body": "Please confirm the plan."})


class PublicWorkspaceTests(unittest.TestCase):
    def service(self, client, usage, state=None):
        with patch("ui.public_usage.st.session_state", {} if state is None else state), patch(
            "ui.public_usage.public_allowance", return_value=usage,
        ):
            guard = session_request_guard()
        return DeepSeekEmailService(
            load_settings({"DEEPSEEK_API_KEY": "test-placeholder-key"}),
            client_factory=lambda _: client, request_guard=guard,
        )

    def generate(self, service):
        return service.generate_email(recipient="", requested_subject="", chinese_brief="请确认计划", tone="Formal", sender=SenderDetails())

    def test_each_format_repair_consumes_real_call_allowance(self):
        client = FakeClient(["not json", RESULT])
        service = self.service(client, PublicUsage(per_session=2))
        self.generate(service)
        self.assertEqual(len(client.completions.calls), 2)
        with self.assertRaises(AIServiceError) as caught:
            self.generate(service)
        self.assertEqual(caught.exception.code, "public_usage_limit")
        self.assertEqual(len(client.completions.calls), 2)

    def test_repair_blocked_at_limit_is_not_a_free_second_call(self):
        client = FakeClient(["not json", RESULT])
        with self.assertRaises(AIServiceError):
            self.generate(self.service(client, PublicUsage(per_session=1)))
        self.assertEqual(len(client.completions.calls), 1)

    def test_two_sessions_share_global_guard_without_sharing_results(self):
        usage = PublicUsage(global_daily=1)
        a, b = FakeClient([RESULT]), FakeClient([RESULT])
        self.generate(self.service(a, usage))
        with self.assertRaises(AIServiceError):
            self.generate(self.service(b, usage))
        self.assertEqual(len(b.completions.calls), 0)

    def test_rerun_guard_reuses_session_identity(self):
        state, usage = {}, PublicUsage(per_session=1)
        self.generate(self.service(FakeClient([RESULT]), usage, state))
        client = FakeClient([RESULT])
        with self.assertRaises(AIServiceError):
            self.generate(self.service(client, usage, state))
        self.assertEqual(len(client.completions.calls), 0)

    def test_app_factory_is_the_only_live_client_constructor(self):
        paths = [ROOT / "app.py", *sorted((ROOT / "ui").rglob("*.py"))]
        constructors = []
        for path in paths:
            for node in ast.walk(ast.parse(path.read_text())):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "DeepSeekEmailService":
                    constructors.append(path)
                    self.assertIn("request_guard", {item.arg for item in node.keywords})
        self.assertEqual(constructors, [ROOT / "app.py"])

    def test_public_home_and_workspaces_never_connect_auth_or_call_model_on_navigation(self):
        with patch("ai_service.OpenAI", side_effect=AssertionError("unexpected paid client")):
            app = AppTest.from_file(str(ROOT / "app.py"))
            app.secrets = {"APP_ACCESS_CODE": "test-only-obsolete", "DEEPSEEK_API_KEY": "test-placeholder-key"}
            app.run()
            for action, workspace in (("reply", "reply"), ("create", "create"), ("improve", "improve")):
                app.button(key=f"home__action__{action}").click().run()
                self.assertFalse(list(app.exception))
                self.assertFalse(any("保存草稿" in button.label or "登录" == button.label for button in app.button))
                keys = [widget.key for widget in (*app.button, *app.text_input, *app.text_area) if widget.key]
                self.assertEqual(len(keys), len(set(keys)))
                app.button(key=f"workspace__{workspace}__return_home").click().run()
            self.assertFalse(list(app.exception))
            self.assertFalse(any(key.startswith(("auth__", "account__")) for key in app.session_state.filtered_state))

    def test_two_browser_sessions_keep_drafts_and_sender_separate(self):
        first = AppTest.from_file(str(ROOT / "app.py"))
        second = AppTest.from_file(str(ROOT / "app.py"))
        for app in (first, second):
            app.secrets = {"DEEPSEEK_API_KEY": "test-placeholder-key"}
            app.run()
            app.button(key="home__action__improve").click().run()
        first.text_area(key="improve_original_email").set_value("Synthetic draft for session A").run()
        first.session_state["shared_sender_name"] = "Synthetic sender A"
        second.run()
        self.assertEqual(second.text_area(key="improve_original_email").value, "")
        self.assertEqual(second.session_state["shared_sender_name"], "")
        self.assertNotEqual(first.session_state["public__usage_session"], second.session_state["public__usage_session"])

    def test_ui_limit_keeps_previous_result_and_does_not_call_model_again(self):
        client, usage = FakeClient([RESULT]), PublicUsage(per_session=1)
        with patch("ai_service.OpenAI", return_value=client), patch(
            "ui.public_usage.public_allowance", return_value=usage,
        ):
            app = AppTest.from_file(str(ROOT / "app.py"))
            app.secrets = {"DEEPSEEK_API_KEY": "test-placeholder-key"}
            app.run()
            app.button(key="home__action__improve").click().run()
            app.text_area(key="improve_original_email").set_value("Please confirm the plan.")
            app.button(key="improve__draft_continue").click().run()
            app.button(key="improve__start").click().run()
            saved = "Synthetic edited result must survive a rejected request."
            app.text_area(key="improved_body_editor").set_value(saved).run()
            app.button(key="improve__again").click().run()
            app.button(key="improve__start").click().run()
            self.assertFalse(list(app.exception))
            self.assertTrue(any("额度已用完" in item.value for item in app.error))
            self.assertEqual(app.session_state["improved_body"], saved)
            self.assertFalse(app.session_state["request_in_progress"])
            self.assertEqual(len(client.completions.calls), 1)
            app.button(key="improve__view_previous_result").click().run()
            self.assertEqual(app.text_area(key="improved_body_editor").value, saved)
            self.assertEqual(len(client.completions.calls), 1)


if __name__ == "__main__":
    unittest.main()
