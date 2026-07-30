import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from ai_service import AIServiceError, EmailResult
from config import APP_NAME_EN, APP_NAME_ZH, APP_VERSION


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


class StreamlitAppTests(unittest.TestCase):
    def create_home(self) -> AppTest:
        with patch(
            "access_control.configured_access_code",
            return_value="",
        ):
            app = AppTest.from_file(str(APP_PATH))
            app.run(timeout=10)
            app.session_state["access_granted"] = True
        self.assertFalse(list(app.exception))
        return app

    def create_app(self) -> AppTest:
        app = self.create_home()
        app.session_state["system__home_view"] = "legacy_improve"
        app.session_state["writing_mode"] = "写英文邮件"
        app.run(timeout=10)
        self.assertFalse(list(app.exception))
        return app

    def test_v2_home_identity_and_all_entries(self) -> None:
        app = self.create_home()
        rendered = "\n".join(item.value for item in app.markdown)
        self.assertIn("Leon AI", rendered)
        self.assertIn(APP_NAME_ZH, rendered)
        self.assertIn(APP_NAME_EN, rendered)
        self.assertIn("V2.0 DEVELOPMENT", rendered)
        self.assertIn("今天有什么商务沟通需要完成", rendered)
        for action in (
            "reply",
            "supplier",
            "meeting",
            "progress",
            "approval",
            "schedule",
            "improve",
            "preflight",
            "scenarios",
        ):
            self.assertIsNotNone(app.button(key=f"home__action__{action}"))

    def test_home_placeholders_do_not_call_ai(self) -> None:
        app = self.create_home()
        with (
            patch(
                "ai_service.DeepSeekEmailService.generate_email",
            ) as generate_mock,
            patch(
                "ai_service.DeepSeekEmailService.improve_email",
            ) as improve_mock,
        ):
            app.button(key="home__action__reply").click().run(timeout=10)
            self.assertTrue(
                any("Phase 3" in item.value for item in app.info)
            )
            app.button(key="home__action__supplier").click().run(timeout=10)
            self.assertTrue(
                any("Phase 2" in item.value for item in app.info)
            )
            app.button(key="home__action__preflight").click().run(timeout=10)
            self.assertTrue(
                any("Phase 4" in item.value for item in app.info)
            )
            self.assertEqual(generate_mock.call_count, 0)
            self.assertEqual(improve_mock.call_count, 0)

    def test_more_scenarios_shows_three_planned_categories(self) -> None:
        app = self.create_home()
        app.button(key="home__action__scenarios").click().run(timeout=10)
        rendered = "\n".join(item.value for item in app.markdown)
        self.assertIn("采购与供应商", rendered)
        self.assertIn("项目与工程", rendered)
        self.assertIn("行政与管理", rendered)

    def test_legacy_improve_is_reachable_and_can_return_home(self) -> None:
        app = self.create_home()
        app.button(key="home__action__improve").click().run(timeout=10)
        app.button(key="home__open_legacy_improve").click().run(timeout=10)
        self.assertIsNotNone(app.text_area(key="improve_original_email"))
        self.assertEqual(app.session_state["writing_mode"], "优化英文邮件")
        app.button(key="legacy__return_home").click().run(timeout=10)
        self.assertIsNotNone(app.button(key="home__action__reply"))

    def test_home_has_mobile_single_column_css(self) -> None:
        source = (
            APP_PATH.parent / "ui" / "pages" / "home.py"
        ).read_text(encoding="utf-8")
        self.assertIn("@media (max-width:640px)", source)
        self.assertIn("flex-direction:column", source)
        self.assertIn("overflow-x:hidden", source)

    def test_required_field_messages_are_in_chinese(self) -> None:
        app = self.create_app()
        app.button(key="legacy__generate_submit").click().run(timeout=10)
        self.assertEqual(app.error[0].value, "请先填写中文需求。")

        app.segmented_control[0].set_value("优化英文邮件").run(timeout=10)
        app.button(key="legacy__improve_submit").click().run(timeout=10)
        self.assertEqual(
            app.error[0].value,
            "请先粘贴需要优化的英文邮件。",
        )

    def test_v1_product_identity_and_country_options(self) -> None:
        app = self.create_app()
        rendered = "\n".join(item.value for item in app.markdown)
        self.assertIn(APP_NAME_ZH, rendered)
        self.assertIn(APP_NAME_EN, rendered)
        self.assertEqual(APP_VERSION, "2.0-dev")
        self.assertIn(
            "未指定 / Not Specified",
            app.selectbox(key="generate_country_region").options,
        )

    def test_app_has_no_persistent_user_content_storage(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        forbidden_storage = (
            "sqlite3",
            "sqlalchemy",
            "pickle.dump",
            "shelve.open",
            "open(\"user_",
            "open('user_",
        )
        for marker in forbidden_storage:
            self.assertNotIn(marker, source)

    def test_missing_key_does_not_crash(self) -> None:
        app = self.create_app()
        app.text_area(key="generate_request").set_value("请确认交付日期。")
        with patch(
            "ai_service.DeepSeekEmailService.generate_email",
            side_effect=AIServiceError(
                "尚未配置 DeepSeek API Key，请按照 README 中的说明完成配置。",
                "missing_api_key",
            ),
        ) as generate_mock:
            app.button(key="legacy__generate_submit").click().run(timeout=10)
            self.assertEqual(generate_mock.call_count, 1)
        self.assertFalse(list(app.exception))
        self.assertEqual(
            app.error[0].value,
            "尚未配置 DeepSeek API Key，请按照 README 中的说明完成配置。",
        )

    def test_overlong_inputs_do_not_call_api(self) -> None:
        app = self.create_app()
        with patch(
            "ai_service.DeepSeekEmailService.generate_email",
        ) as generate_mock:
            app.text_area(key="generate_request").set_value("中" * 8001)
            app.button(key="legacy__generate_submit").click().run(timeout=10)
            self.assertEqual(generate_mock.call_count, 0)
            self.assertEqual(
                app.error[0].value,
                "中文需求不能超过 8000 个字符。",
            )

        app.segmented_control[0].set_value("优化英文邮件").run(timeout=10)
        with patch(
            "ai_service.DeepSeekEmailService.improve_email",
        ) as improve_mock:
            app.text_area(key="improve_original_email").set_value("A" * 8001)
            app.button(key="legacy__improve_submit").click().run(timeout=10)
            self.assertEqual(improve_mock.call_count, 0)
            self.assertEqual(
                app.error[0].value,
                "原始英文邮件不能超过 8000 个字符。",
            )

    def test_page_inputs_and_sender_are_preserved(self) -> None:
        app = self.create_app()
        app.text_area(key="generate_request").set_value("请确认会议时间。")
        app.text_input(key="shared_sender_name").set_value("Alice Wang")
        app.segmented_control[0].set_value("优化英文邮件").run(timeout=10)
        self.assertEqual(
            app.text_input(key="shared_sender_name").value,
            "Alice Wang",
        )
        app.segmented_control[0].set_value("写英文邮件").run(timeout=10)
        self.assertEqual(
            app.text_area(key="generate_request").value,
            "请确认会议时间。",
        )

    def test_successful_result_is_saved_without_repeated_call(self) -> None:
        app = self.create_app()
        app.text_area(key="generate_request").set_value("请确认交付日期。")
        mocked_result = EmailResult(
            subject="Delivery Confirmation",
            body="Dear Team,\n\nPlease confirm.\n\nBest regards,",
            usage_tokens=321,
        )
        with patch(
            "ai_service.DeepSeekEmailService.generate_email",
            return_value=mocked_result,
        ) as generate_mock:
            app.button(key="legacy__generate_submit").click().run(timeout=10)
            self.assertFalse(list(app.exception))
            self.assertEqual(generate_mock.call_count, 1)
            self.assertEqual(
                app.text_input(key="subject_editor").value,
                "Delivery Confirmation",
            )
            self.assertTrue(app.session_state["deepseek_connected"])
            self.assertEqual(app.session_state["last_usage_tokens"], 321)
            app.run(timeout=10)
            self.assertEqual(generate_mock.call_count, 1)

    def test_high_risk_requires_confirmation_before_api(self) -> None:
        app = self.create_app()
        app.text_area(key="generate_request").set_value(
            "API Key: sk-testplaceholder123456"
        )
        mocked_result = EmailResult(
            subject="Safe",
            body="Dear Team,\n\nPlease confirm.\n\nBest regards,",
        )
        with patch(
            "ai_service.DeepSeekEmailService.generate_email",
            return_value=mocked_result,
        ) as generate_mock:
            app.button(key="legacy__generate_submit").click().run(timeout=10)
            self.assertEqual(generate_mock.call_count, 0)
            self.assertTrue(
                any(
                    "检测到高风险内容" in error.value
                    for error in app.error
                )
            )

            app.checkbox(key="generate_high_risk_confirmed").check().run(
                timeout=10
            )
            app.button(key="legacy__generate_submit").click().run(timeout=10)
            self.assertEqual(generate_mock.call_count, 1)

    def test_example_fills_fields_without_api_call(self) -> None:
        app = self.create_app()
        with (
            patch(
                "ai_service.DeepSeekEmailService.generate_email",
            ) as generate_mock,
            patch(
                "ai_service.DeepSeekEmailService.improve_email",
            ) as improve_mock,
        ):
            app.button(key="use_example_supplier_delivery_followup").click().run(
                timeout=10
            )
            self.assertIn(
                "供应商原计划本周提交",
                app.text_area(key="generate_request").value,
            )
            self.assertEqual(generate_mock.call_count, 0)
            self.assertEqual(improve_mock.call_count, 0)

    def test_access_gate_rejects_wrong_code_and_accepts_correct_code(self) -> None:
        with (
            patch(
                "access_control.configured_access_code",
                return_value="invite-123",
            ),
            patch(
                "ai_service.DeepSeekEmailService.generate_email",
            ) as generate_mock,
            patch(
                "ai_service.DeepSeekEmailService.improve_email",
            ) as improve_mock,
        ):
            app = AppTest.from_file(str(APP_PATH))
            app.run(timeout=10)
            self.assertTrue(
                any(
                    "Leon AI 内部测试版" in item.value
                    for item in app.markdown
                )
            )

            app.text_input(key="access_code_input").set_value("wrong")
            app.button[0].click().run(timeout=10)
            self.assertEqual(
                app.error[0].value,
                "访问码不正确，请重新输入。",
            )

            app.text_input(key="access_code_input").set_value("invite-123")
            app.button[0].click().run(timeout=10)
            self.assertFalse(list(app.exception))
            self.assertEqual(app.session_state["access_granted"], True)
            self.assertEqual(generate_mock.call_count, 0)
            self.assertEqual(improve_mock.call_count, 0)

            generate_mock.return_value = EmailResult(
                subject="Meeting",
                body="Please confirm.\n\nBest regards,",
            )
            app.session_state["system__home_view"] = "legacy_improve"
            app.session_state["writing_mode"] = "写英文邮件"
            app.run(timeout=10)
            app.text_area(key="generate_request").set_value("请确认会议。")
            app.button(key="legacy__generate_submit").click().run(timeout=10)
            self.assertEqual(generate_mock.call_count, 1)

            improve_mock.return_value = EmailResult(
                subject="Delivery",
                body="Please confirm the delivery date.\n\nBest regards,",
            )
            app.segmented_control[0].set_value("优化英文邮件").run(timeout=10)
            app.text_area(key="improve_original_email").set_value(
                "please confirm delivery date"
            )
            app.button(key="legacy__improve_submit").click().run(timeout=10)
            self.assertEqual(improve_mock.call_count, 1)


if __name__ == "__main__":
    unittest.main()
