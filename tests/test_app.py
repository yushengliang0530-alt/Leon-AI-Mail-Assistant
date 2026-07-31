import json
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from ai_service import AIServiceError, EmailResult
from config import APP_NAME_EN, APP_NAME_ZH, APP_VERSION
from models.incoming_email import parse_incoming_email_analysis
from models.reply_generation import CoverageItem, CoverageResult, GeneratedReply
from models.preflight import parse_semantic_preflight
from services.reply_item_service import (
    build_decision_summary,
    normalize_reply_items,
)
from tests.test_incoming_email_analysis import VALID_ANALYSIS
from tests.test_preflight import semantic_json


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

    def test_v2_home_identity_and_production_entries(self) -> None:
        app = self.create_home()
        rendered = "\n".join(item.value for item in app.markdown)
        self.assertIn("Leon AI", rendered)
        self.assertIn(APP_NAME_ZH, rendered)
        self.assertIn(APP_NAME_EN, rendered)
        self.assertIn("V2.0", rendered)
        self.assertNotIn("DEVELOPMENT", rendered)
        self.assertNotIn("开发中", rendered)
        self.assertNotIn("Phase", rendered)
        self.assertIn("今天有什么商务沟通需要完成", rendered)
        for action in (
            "reply",
            "supplier",
            "improve",
        ):
            self.assertIsNotNone(app.button(key=f"home__action__{action}"))

    def test_reply_home_entry_opens_real_analysis_workspace(self) -> None:
        app = self.create_home()
        app.button(key="home__action__reply").click().run(timeout=10)

        self.assertFalse(list(app.exception))
        rendered = "\n".join(item.value for item in app.markdown)
        self.assertIn("回复收到的邮件", rendered)
        self.assertIsNotNone(
            app.text_area(key="reply__original_email")
        )
        self.assertFalse(any("Phase 3" in item.value for item in app.info))

    def test_reply_empty_and_high_risk_input_do_not_call_ai(self) -> None:
        app = self.create_home()
        app.button(key="home__action__reply").click().run(timeout=10)
        with patch(
            "ai_service.DeepSeekEmailService.analyze_incoming_email",
        ) as analyze_mock:
            app.button(key="reply__analyze").click().run(timeout=10)
            self.assertEqual(analyze_mock.call_count, 0)
            self.assertTrue(
                any("请先粘贴" in item.value for item in app.error)
            )

            app.text_area(key="reply__original_email").set_value(
                "API Key: sk-example-placeholder-123456789"
            ).run(timeout=10)
            app.button(key="reply__analyze").click().run(timeout=10)
            self.assertEqual(analyze_mock.call_count, 0)
            self.assertIsNotNone(
                app.checkbox(key="reply__risk_confirmed")
            )

    def test_reply_analysis_is_saved_once_and_invalidated_by_edit(self) -> None:
        app = self.create_home()
        app.button(key="home__action__reply").click().run(timeout=10)
        analysis = parse_incoming_email_analysis(
            json.dumps(VALID_ANALYSIS)
        )
        with patch(
            "ai_service.DeepSeekEmailService.analyze_incoming_email",
            return_value=analysis,
        ) as analyze_mock:
            app.text_input(key="reply__original_subject").set_value(
                "Updated Delivery Schedule Required"
            )
            app.text_area(key="reply__original_email").set_value(
                "Please explain the delay and provide a recovery plan."
            ).run(timeout=10)
            app.button(key="reply__analyze").click().run(timeout=10)

            self.assertEqual(analyze_mock.call_count, 1)
            self.assertEqual(app.session_state["reply__step"], 2)
            self.assertIn(
                "The sender requests",
                "\n".join(item.value for item in app.markdown),
            )

            app.run(timeout=10)
            self.assertEqual(analyze_mock.call_count, 1)
            app.button(key="reply__modify").click().run(timeout=10)
            app.text_area(key="reply__original_email").set_value(
                "Changed email content."
            ).run(timeout=10)
            self.assertIsNone(app.session_state["reply__analysis"])
            self.assertEqual(
                app.session_state["reply__risk_confirmed_digest"],
                "",
            )

    def test_reply_high_risk_confirmation_is_bound_to_current_email(self) -> None:
        app = self.create_home()
        app.button(key="home__action__reply").click().run(timeout=10)
        analysis = parse_incoming_email_analysis(json.dumps(VALID_ANALYSIS))
        with patch(
            "ai_service.DeepSeekEmailService.analyze_incoming_email",
            return_value=analysis,
        ) as analyze_mock:
            app.text_area(key="reply__original_email").set_value(
                "API Key: sk-example-placeholder-123456789"
            ).run(timeout=10)
            app.checkbox(key="reply__risk_confirmed").check().run(timeout=10)
            app.button(key="reply__analyze").click().run(timeout=10)
            self.assertEqual(analyze_mock.call_count, 1)
            confirmed = app.session_state["reply__risk_confirmed_digest"]
            self.assertTrue(confirmed)

            app.button(key="reply__modify").click().run(timeout=10)
            app.text_area(key="reply__original_email").set_value(
                "API Key: sk-different-placeholder-987654321"
            ).run(timeout=10)
            self.assertEqual(
                app.session_state["reply__risk_confirmed_digest"],
                "",
            )
            self.assertIsNone(app.session_state["reply__analysis"])

    def test_reply_clear_does_not_reset_supplier_state(self) -> None:
        app = self.create_home()
        app.session_state["compose__task_id"] = "supplier_plan_update"
        app.button(key="home__action__reply").click().run(timeout=10)
        app.session_state["reply__step"] = 1
        app.session_state["reply__analysis"] = parse_incoming_email_analysis(
            json.dumps(VALID_ANALYSIS)
        )
        app.session_state["reply__source_digest"] = "same"
        app.session_state["reply__analysis_digest"] = "same"
        app.run(timeout=10)
        app.button(key="reply__clear").click().run(timeout=10)

        self.assertEqual(
            app.session_state["compose__task_id"],
            "supplier_plan_update",
        )
        self.assertIsNone(app.session_state["reply__analysis"])

    def test_reply_decision_workflow_stops_at_local_summary(self) -> None:
        app = self.create_home()
        app.button(key="home__action__reply").click().run(timeout=10)
        analysis = parse_incoming_email_analysis(json.dumps(VALID_ANALYSIS))
        with patch(
            "ai_service.DeepSeekEmailService.analyze_incoming_email",
            return_value=analysis,
        ) as analyze_mock:
            app.text_area(key="reply__original_email").set_value(
                "Please explain the delay by Friday."
            ).run(timeout=10)
            app.button(key="reply__analyze").click().run(timeout=10)
            self.assertEqual(analyze_mock.call_count, 1)

            app.button(key="reply__start_decisions").click().run(timeout=10)
            self.assertEqual(app.session_state["reply__step"], 3)
            self.assertEqual(
                len(app.session_state["reply__normalized_items"]), 1
            )

            epoch = app.session_state["reply__decision_widget_epoch"]
            app.selectbox(
                key=(
                    f"reply__decision_widget__request_1__{epoch}__"
                    "stance__display"
                )
            ).select("接受并确认").run(timeout=10)
            app.text_area(
                key=(
                    f"reply__decision_widget__request_1__{epoch}__"
                    "confirmed_facts"
                )
            ).set_value("We can provide the delay explanation.").run(timeout=10)
            app.button(
                key="reply__decision_next__request_1"
            ).click().run(timeout=10)

            self.assertEqual(analyze_mock.call_count, 1)
            self.assertEqual(app.session_state["reply__step"], 3)
            rendered = "\n".join(item.value for item in app.markdown)
            self.assertIn("回复决策摘要", rendered)
            self.assertIsNotNone(
                app.button(key="reply__generate_reply")
            )
            self.assertNotIn("邮件正文", rendered)

            app.button(key="reply__summary_back").click().run(timeout=10)
            restored = app.text_area(
                key=(
                    "reply__decision_widget__request_1__"
                    f"{app.session_state['reply__decision_widget_epoch']}__"
                    "confirmed_facts"
                )
            )
            self.assertEqual(
                restored.value,
                "We can provide the delay explanation.",
            )
            self.assertEqual(analyze_mock.call_count, 1)

    def test_reply_decision_high_risk_requires_current_confirmation(self) -> None:
        app = self.create_home()
        app.button(key="home__action__reply").click().run(timeout=10)
        analysis = parse_incoming_email_analysis(json.dumps(VALID_ANALYSIS))
        with patch(
            "ai_service.DeepSeekEmailService.analyze_incoming_email",
            return_value=analysis,
        ) as analyze_mock:
            app.text_area(key="reply__original_email").set_value(
                "Please explain the delay."
            ).run(timeout=10)
            app.button(key="reply__analyze").click().run(timeout=10)
            app.button(key="reply__start_decisions").click().run(timeout=10)
            epoch = app.session_state["reply__decision_widget_epoch"]
            app.selectbox(
                key=(
                    f"reply__decision_widget__request_1__{epoch}__"
                    "stance__display"
                )
            ).select("接受并确认").run(timeout=10)
            app.text_area(
                key=(
                    f"reply__decision_widget__request_1__{epoch}__"
                    "confirmed_facts"
                )
            ).set_value(
                "API Key: sk-qa-placeholder-123456789"
            ).run(timeout=10)
            app.button(
                key="reply__decision_next__request_1"
            ).click().run(timeout=10)

            self.assertEqual(app.session_state["reply__step"], 3)
            self.assertEqual(
                app.session_state["reply__decision_risk"].risk_level,
                "high",
            )
            self.assertIsNotNone(
                app.checkbox(key="reply__decision_risk_confirmed")
            )

            app.checkbox(
                key="reply__decision_risk_confirmed"
            ).check().run(timeout=10)
            app.button(
                key="reply__decision_next__request_1"
            ).click().run(timeout=10)
            self.assertEqual(app.session_state["reply__step"], 3)
            self.assertEqual(analyze_mock.call_count, 1)

    def test_phase3c_generates_then_checks_and_edit_only_rechecks(self) -> None:
        app = self.create_home()
        analysis = parse_incoming_email_analysis(json.dumps(VALID_ANALYSIS))
        items = normalize_reply_items(analysis)
        decisions = {
            items[0].item_id: {
                "item_id": items[0].item_id,
                "stance": "unable_to_confirm",
                "reason": "Internal verification is pending.",
                "include_in_reply": True,
                "no_response_confirmed": False,
            }
        }
        app.session_state["system__home_view"] = "reply_analysis"
        app.session_state["reply__analysis"] = analysis
        app.session_state["reply__analysis_digest"] = "same"
        app.session_state["reply__source_digest"] = "same"
        app.session_state["reply__normalized_items"] = items
        app.session_state["reply__decisions"] = decisions
        app.session_state["reply__decision_summary"] = (
            build_decision_summary(items, decisions)
        )
        app.session_state["reply__step"] = 3
        generated = GeneratedReply(
            "Delivery Update",
            "Dear Team,\n\nWe cannot currently confirm the revised date.",
        )
        coverage = CoverageResult(
            items=(
                CoverageItem(
                    items[0].item_id,
                    "postponed",
                    "The reply explicitly says the date cannot be confirmed.",
                ),
            ),
            addressed_count=0,
            partial_count=0,
            postponed_count=1,
            not_addressed_count=0,
            covered_count=1,
            total_count=1,
        )
        with (
            patch(
                "ai_service.DeepSeekEmailService.generate_reply_email",
                return_value=generated,
            ) as generate_mock,
            patch(
                "ai_service.DeepSeekEmailService.check_reply_coverage",
                return_value=coverage,
            ) as coverage_mock,
            patch(
                "ai_service.DeepSeekEmailService.check_reply_preflight",
                return_value=parse_semantic_preflight(semantic_json()),
            ) as preflight_mock,
        ):
            app.run(timeout=10)
            app.selectbox(key="reply__target_tone").select(
                "Executive"
            ).run(timeout=10)
            app.button(key="reply__generate_reply").click().run(timeout=10)
            self.assertEqual(app.session_state["reply__step"], 5)
            self.assertEqual(generate_mock.call_count, 1)
            self.assertEqual(coverage_mock.call_count, 1)
            self.assertEqual(preflight_mock.call_count, 0)
            self.assertIn("Sincerely,", app.session_state["reply__body"])
            rendered = "\n".join(item.value for item in app.markdown)
            self.assertIn("本次回复覆盖 1 / 1 项", rendered)

            app.button(key="preflight__run").click().run(timeout=10)
            self.assertEqual(preflight_mock.call_count, 1)
            self.assertEqual(
                app.session_state["preflight__status"], "success"
            )
            self.assertEqual(
                app.session_state["preflight__report"].overall_status,
                "CHECK",
            )
            app.run(timeout=10)
            self.assertEqual(preflight_mock.call_count, 1)

            app.text_area(key="reply__body").set_value(
                app.session_state["reply__body"] + "\nAdditional clarification."
            ).run(timeout=10)
            self.assertEqual(
                app.session_state["reply__coverage_status"], "stale"
            )
            self.assertEqual(
                app.session_state["preflight__status"], "stale"
            )
            app.button(key="reply__recheck_coverage").click().run(timeout=10)
            self.assertEqual(generate_mock.call_count, 1)
            self.assertEqual(coverage_mock.call_count, 2)

    def test_reply_analysis_failure_keeps_original_email(self) -> None:
        app = self.create_home()
        app.button(key="home__action__reply").click().run(timeout=10)
        original = "Please explain the delay."
        with patch(
            "ai_service.DeepSeekEmailService.analyze_incoming_email",
            side_effect=AIServiceError(
                "AI返回分析格式异常，请重新分析。",
                "analysis_parse_error",
            ),
        ) as analyze_mock:
            app.text_area(key="reply__original_email").set_value(
                original
            ).run(timeout=10)
            app.button(key="reply__analyze").click().run(timeout=10)

            self.assertEqual(analyze_mock.call_count, 1)
            self.assertEqual(
                app.text_area(key="reply__original_email").value,
                original,
            )
            self.assertTrue(
                any("格式异常" in item.value for item in app.error)
            )

    def create_supplier_workflow(self) -> AppTest:
        app = self.create_home()
        app.button(key="home__action__supplier").click().run(timeout=10)
        app.button(key="home__open_supplier_workflow").click().run(timeout=10)
        self.assertFalse(list(app.exception))
        return app

    def test_supplier_workflow_has_four_tasks_and_no_ai_navigation(self) -> None:
        with patch(
            "ai_service.DeepSeekEmailService.generate_scenario_email",
        ) as generate_mock:
            app = self.create_supplier_workflow()
            for task_id in (
                "supplier_quotation",
                "supplier_delivery",
                "supplier_plan_update",
                "supplier_delay_explanation",
            ):
                self.assertIsNotNone(
                    app.button(key=f"compose__task__{task_id}")
                )
            self.assertEqual(generate_mock.call_count, 0)

    def answer_supplier_question(
        self,
        app: AppTest,
        field_key: str,
        value: str,
        *,
        textarea: bool = False,
    ) -> AppTest:
        widget_key = f"compose__answer_widget__{field_key}"
        widget = (
            app.text_area(key=widget_key)
            if textarea
            else app.text_input(key=widget_key)
        )
        widget.set_value(value)
        app.button(key="compose__question_next").click().run(timeout=10)
        self.assertFalse(list(app.exception))
        return app

    def complete_quotation_questions(self, app: AppTest) -> AppTest:
        self.answer_supplier_question(
            app,
            "supplier_name",
            "ABC Components",
        )
        self.answer_supplier_question(
            app,
            "quotation_scope",
            "Control panels",
            textarea=True,
        )
        app.button(key="compose__question_skip").click().run(timeout=10)
        app.button(key="compose__question_skip").click().run(timeout=10)
        app.button(key="compose__question_skip").click().run(timeout=10)
        self.answer_supplier_question(
            app,
            "requested_reply",
            "By Friday",
        )
        app.button(key="compose__question_skip").click().run(timeout=10)
        self.answer_supplier_question(
            app,
            "required_action",
            "Send the formal quotation.",
            textarea=True,
        )
        self.assertEqual(app.session_state["compose__step"], 3)
        return app

    def test_supplier_questions_appear_in_order_and_advanced_is_review_only(
        self,
    ) -> None:
        app = self.create_supplier_workflow()
        app.button(key="compose__task__supplier_plan_update").click().run(
            timeout=10
        )
        self.assertIsNotNone(
            app.text_input(key="compose__answer_widget__supplier_name")
        )
        self.assertNotIn(
            "compose__answer_widget__original_plan_date",
            {item.key for item in app.text_input},
        )
        self.answer_supplier_question(
            app,
            "supplier_name",
            "ABC Components",
        )
        self.assertIsNotNone(
            app.text_input(key="compose__answer_widget__project_name")
        )
        self.assertFalse(any("高级选项" in item.label for item in app.expander))

    def test_supplier_required_question_cannot_be_skipped(self) -> None:
        app = self.create_supplier_workflow()
        app.button(key="compose__task__supplier_quotation").click().run(
            timeout=10
        )
        with patch(
            "ai_service.DeepSeekEmailService.generate_scenario_email",
        ) as generate_mock:
            app.button(key="compose__question_next").click().run(timeout=10)
            self.assertEqual(generate_mock.call_count, 0)
            self.assertTrue(
                any(
                    "请先回答：供应商名称" in error.value
                    for error in app.error
                )
            )
            self.assertEqual(app.session_state["compose__question_index"], 0)

    def test_supplier_back_preserves_answer(self) -> None:
        app = self.create_supplier_workflow()
        app.button(key="compose__task__supplier_plan_update").click().run(
            timeout=10
        )
        self.answer_supplier_question(
            app,
            "supplier_name",
            "ABC Components"
        )
        self.answer_supplier_question(
            app,
            "project_name",
            "North Plant Upgrade",
        )
        app.button(key="compose__question_back").click().run(timeout=10)
        self.assertEqual(
            app.text_input(
                key="compose__answer_widget__project_name"
            ).value,
            "North Plant Upgrade",
        )

    def test_supplier_review_is_correct_and_editable(self) -> None:
        app = self.create_supplier_workflow()
        app.button(key="compose__task__supplier_quotation").click().run(
            timeout=10
        )
        self.complete_quotation_questions(app)
        rendered = "\n".join(item.value for item in app.markdown)
        self.assertIn("本次商务沟通信息", rendered)
        self.assertIn("ABC Components", rendered)
        self.assertIn("Control panels", rendered)
        self.assertNotIn("项目名称</div>", rendered)
        self.assertTrue(any("高级选项" in item.label for item in app.expander))

        app.button(
            key="compose__review_edit__supplier_name"
        ).click().run(timeout=10)
        app.text_input(
            key="compose__answer_widget__supplier_name"
        ).set_value("XYZ Components")
        app.button(key="compose__question_next").click().run(timeout=10)
        rendered = "\n".join(item.value for item in app.markdown)
        self.assertIn("XYZ Components", rendered)
        self.assertNotIn("ABC Components", rendered)

    def test_supplier_generate_calls_ai_once_only_after_review(self) -> None:
        app = self.create_supplier_workflow()
        app.button(key="compose__task__supplier_quotation").click().run(
            timeout=10
        )
        mocked = EmailResult(
            subject="Quotation Follow-up",
            body="Please send the quotation.\n\nBest regards,",
            usage_tokens=245,
        )
        with patch(
            "ai_service.DeepSeekEmailService.generate_scenario_email",
            return_value=mocked,
        ) as generate_mock:
            self.complete_quotation_questions(app)
            self.assertEqual(generate_mock.call_count, 0)
            app.button(key="compose__generate").click().run(timeout=10)
            self.assertFalse(list(app.exception))
            self.assertEqual(generate_mock.call_count, 1)
            self.assertEqual(
                app.text_input(key="compose__result_subject").value,
                "Quotation Follow-up",
            )
            app.run(timeout=10)
            self.assertEqual(generate_mock.call_count, 1)

    def test_supplier_review_edit_can_generate_updated_email(self) -> None:
        app = self.create_supplier_workflow()
        app.button(key="compose__task__supplier_quotation").click().run(
            timeout=10
        )
        mocked = EmailResult(
            subject="Updated Quotation Follow-up",
            body="Please send the updated quotation.\n\nBest regards,",
        )
        with patch(
            "ai_service.DeepSeekEmailService.generate_scenario_email",
            return_value=mocked,
        ) as generate_mock:
            self.complete_quotation_questions(app)
            app.button(key="compose__generate").click().run(timeout=10)
            self.assertEqual(generate_mock.call_count, 1)

            app.button(key="compose__edit_information").click().run(timeout=10)
            app.button(
                key="compose__review_edit__supplier_name"
            ).click().run(timeout=10)
            app.text_input(
                key="compose__answer_widget__supplier_name"
            ).set_value("XYZ Components")
            app.button(key="compose__question_next").click().run(timeout=10)
            app.button(key="compose__generate").click().run(timeout=10)

            self.assertEqual(generate_mock.call_count, 2)
            latest_facts = generate_mock.call_args.kwargs["facts"]
            self.assertEqual(latest_facts["supplier_name"], "XYZ Components")

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

    def test_v2_product_identity_and_country_options(self) -> None:
        app = self.create_app()
        rendered = "\n".join(item.value for item in app.markdown)
        self.assertIn(APP_NAME_ZH, rendered)
        self.assertIn(APP_NAME_EN, rendered)
        self.assertEqual(APP_VERSION, "2.0")
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
