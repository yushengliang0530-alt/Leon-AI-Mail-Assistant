import json
import unittest
from types import SimpleNamespace

from ai_service import (
    AIServiceError,
    DeepSeekEmailService,
    EmailResult,
    SenderDetails,
    append_signature,
    build_signature,
    parse_email_fallback,
    parse_email_result,
)
from config import DeepSeekSettings
from prompts import generation_messages
from tests.test_incoming_email_analysis import VALID_ANALYSIS
from tests.test_preflight import semantic_json


def fake_response(content: str):
    return SimpleNamespace(
        usage=SimpleNamespace(total_tokens=123),
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=content),
            )
        ]
    )


class FakeCompletions:
    def __init__(self, contents: list[str]) -> None:
        self.contents = list(contents)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return fake_response(self.contents.pop(0))


class FakeClient:
    def __init__(self, contents: list[str]) -> None:
        self.completions = FakeCompletions(contents)
        self.chat = SimpleNamespace(completions=self.completions)


class DeepSeekEmailServiceTests(unittest.TestCase):
    def settings(self, api_key: str = "test-placeholder-key") -> DeepSeekSettings:
        return DeepSeekSettings(
            api_key=api_key,
            model="deepseek-v4-flash",
            base_url="https://api.deepseek.com",
            timeout_seconds=45,
            max_tokens=1600,
        )

    def test_parse_tolerates_json_code_fence(self) -> None:
        result = parse_email_result(
            '```json\n{"subject":"Delivery","body":"Dear Team,\\nPlease confirm."}\n```'
        )
        self.assertEqual(result.subject, "Delivery")
        self.assertIn("Please confirm.", result.body)

    def test_communication_analysis_is_parsed(self) -> None:
        result = parse_email_result(
            json.dumps(
                {
                    "subject": "Delivery",
                    "body": "Please confirm.",
                    "communication_analysis": {
                        "purpose": "良好：目的清晰",
                        "action_required": "明确",
                        "deadline": "未提供",
                        "tone": "正式且适当",
                        "commitment_risk": "未发现明显风险",
                        "ambiguity_risk": "未发现明显风险",
                        "localization_note": "核对称谓",
                        "improvement_suggestions": ["增加回复期限"],
                    },
                }
            )
        )
        self.assertTrue(result.communication_analysis.available)
        self.assertEqual(result.communication_analysis.deadline, "未提供")

    def test_plain_email_fallback(self) -> None:
        result = parse_email_fallback(
            "Subject: Delivery Update\n\nBody: Dear Team,\n\nPlease confirm."
        )
        self.assertEqual(result.subject, "Delivery Update")
        self.assertIn("Dear Team", result.body)
        self.assertFalse(result.communication_analysis.available)

    def test_generation_uses_json_mode_and_appends_local_signature(self) -> None:
        fake_client = FakeClient(
            [
                json.dumps(
                    {
                        "subject": "Delivery Confirmation",
                        "body": "Dear Team,\n\nPlease confirm the delivery date.",
                    }
                )
            ]
        )
        service = DeepSeekEmailService(
            self.settings(),
            client_factory=lambda _: fake_client,
        )

        result = service.generate_email(
            recipient="Project Team",
            requested_subject="",
            chinese_brief="请确认交付日期。",
            tone="Formal",
            sender=SenderDetails(
                name="Alice Wang",
                job_title="Project Manager",
                company="Northstar Engineering",
                contact_information="alice@example.com",
            ),
        )

        self.assertEqual(result.subject, "Delivery Confirmation")
        self.assertTrue(
            result.body.endswith(
                "Best regards,\n"
                "Alice Wang\n"
                "Project Manager\n"
                "Northstar Engineering\n"
                "alice@example.com"
            )
        )
        self.assertNotIn("Leon", result.body)
        self.assertEqual(result.usage_tokens, 123)
        request = fake_client.completions.calls[0]
        self.assertEqual(request["model"], "deepseek-v4-flash")
        self.assertEqual(request["response_format"], {"type": "json_object"})
        self.assertEqual(request["extra_body"], {"thinking": {"type": "disabled"}})

    def test_only_chinese_brief_is_enough(self) -> None:
        fake_client = FakeClient(
            ['{"subject":"Meeting Confirmation","body":"Please confirm the meeting."}']
        )
        service = DeepSeekEmailService(
            self.settings(),
            client_factory=lambda _: fake_client,
        )
        result = service.generate_email(
            recipient="",
            requested_subject="",
            chinese_brief="请确认会议。",
            tone="Executive",
            sender=SenderDetails(),
        )
        self.assertEqual(result.subject, "Meeting Confirmation")
        self.assertTrue(result.body.endswith("Sincerely,"))
        self.assertNotIn("Leon", result.body)

    def test_scenario_generation_uses_facts_and_local_signature(self) -> None:
        fake_client = FakeClient(
            [
                json.dumps(
                    {
                        "subject": "Updated Delivery Plan Required",
                        "body": "Dear Supplier Team,\n\nPlease send the revised plan.",
                    }
                )
            ]
        )
        service = DeepSeekEmailService(
            self.settings(),
            client_factory=lambda _: fake_client,
        )
        result = service.generate_scenario_email(
            scenario_id="supplier_plan_update",
            scenario_title="更新计划 / Request Plan Update",
            facts={
                "supplier_name": "ABC Components",
                "requested_reply": "By Friday",
                "required_action": "Send the revised plan.",
            },
            tone="Formal",
            sender=SenderDetails(name="Alice Wang"),
        )
        self.assertTrue(result.body.endswith("Best regards,\nAlice Wang"))
        prompt = fake_client.completions.calls[0]["messages"][1]["content"]
        self.assertIn('"supplier_name": "ABC Components"', prompt)
        self.assertNotIn('"project_name"', prompt)

    def test_preflight_parses_and_uses_one_repair_retry(self) -> None:
        fake_client = FakeClient(["invalid", semantic_json("CHECK")])
        service = DeepSeekEmailService(
            self.settings(),
            client_factory=lambda _: fake_client,
        )
        result = service.check_reply_preflight(payload={"email": {}})
        self.assertEqual(result.items[0].status, "CHECK")
        self.assertEqual(result.usage_tokens, 246)
        self.assertEqual(len(fake_client.completions.calls), 2)

    def test_preflight_invalid_json_raises_safe_error(self) -> None:
        fake_client = FakeClient(["invalid", "still invalid"])
        service = DeepSeekEmailService(
            self.settings(),
            client_factory=lambda _: fake_client,
        )
        with self.assertRaises(AIServiceError) as context:
            service.check_reply_preflight(payload={"email": {}})
        self.assertEqual(context.exception.code, "preflight_parse_error")
        self.assertNotIn("still invalid", context.exception.user_message)
        self.assertEqual(len(fake_client.completions.calls), 2)

    def test_improvement_preserves_content_and_uses_local_signature(self) -> None:
        fake_client = FakeClient(
            [
                json.dumps(
                    {
                        "subject": "Action Required",
                        "email_body": (
                            "Dear Jason,\n\nPlease review the delayed item "
                            "and reply as soon as possible."
                        ),
                        "communication_analysis": {
                            "purpose": "良好：目的清晰",
                            "action_required": "明确",
                            "deadline": "未提供",
                            "tone": "保持紧迫且专业",
                            "commitment_risk": "未发现明显风险",
                            "ambiguity_risk": "建议明确具体事项",
                            "localization_note": "称谓自然",
                            "improvement_suggestions": [],
                        },
                    }
                )
            ]
        )
        service = DeepSeekEmailService(
            self.settings(),
            client_factory=lambda _: fake_client,
        )
        result = service.improve_email(
            original_email="Dear Jason, please check the delayed item ASAP.",
            tone="Formal",
            sender=SenderDetails(name="Alice Wang"),
            country_region="新加坡 / Singapore",
        )
        self.assertIn("delayed item", result.body)
        self.assertTrue(result.body.endswith("Best regards,\nAlice Wang"))
        self.assertTrue(result.communication_analysis.available)
        self.assertEqual(len(fake_client.completions.calls), 1)

    def test_tone_prompts_are_distinct(self) -> None:
        prompts = {
            tone: generation_messages(
                recipient="",
                requested_subject="",
                chinese_brief="请确认日期。",
                tone=tone,
            )[1]["content"]
            for tone in ["Formal", "Friendly", "Strong", "Executive"]
        }
        self.assertEqual(len(set(prompts.values())), 4)
        self.assertIn("never threaten", prompts["Strong"])
        self.assertIn("outcome-focused", prompts["Executive"])

    def test_signature_variations(self) -> None:
        self.assertEqual(
            build_signature("Formal", SenderDetails(name="Alice Wang")),
            "Best regards,\nAlice Wang",
        )
        self.assertEqual(
            build_signature(
                "Friendly",
                SenderDetails(company="Northstar Engineering"),
            ),
            "Kind regards,\nNorthstar Engineering",
        )
        self.assertEqual(
            build_signature("Strong", SenderDetails()),
            "Regards,",
        )
        self.assertEqual(
            build_signature("Executive", SenderDetails()),
            "Sincerely,",
        )

    def test_model_closing_is_not_duplicated(self) -> None:
        body = "Dear Team,\n\nPlease confirm by Friday.\n\nBest regards"
        result = append_signature(
            body,
            "Formal",
            SenderDetails(name="Alice Wang"),
        )
        self.assertEqual(result.count("Best regards"), 1)
        self.assertTrue(result.endswith("Best regards,\nAlice Wang"))

    def test_invalid_json_gets_only_one_repair_request(self) -> None:
        fake_client = FakeClient(
            [
                "Subject: Delivery\nBody: Please confirm.",
                '{"subject":"Delivery","body":"Please confirm."}',
            ]
        )
        service = DeepSeekEmailService(
            self.settings(),
            client_factory=lambda _: fake_client,
        )
        result = service.improve_email(
            original_email="Please confirm.",
            tone="Concise",
            sender=SenderDetails(),
        )
        self.assertEqual(result.subject, "Delivery")
        self.assertEqual(len(fake_client.completions.calls), 2)
        self.assertEqual(result.usage_tokens, 246)

    def test_second_parse_failure_returns_safe_chinese_error(self) -> None:
        fake_client = FakeClient(["not json", "still not json"])
        service = DeepSeekEmailService(
            self.settings(),
            client_factory=lambda _: fake_client,
        )
        with self.assertRaises(AIServiceError) as context:
            service.improve_email(
                original_email="Please confirm.",
                tone="Formal",
                sender=SenderDetails(),
            )
        self.assertEqual(context.exception.code, "parse_error")
        self.assertEqual(len(fake_client.completions.calls), 2)

    def test_non_json_email_falls_back_after_one_repair(self) -> None:
        fake_client = FakeClient(
            [
                "Subject: Delivery Update\n\nBody: Dear Team,\nPlease confirm.",
                "still not json",
            ]
        )
        service = DeepSeekEmailService(
            self.settings(),
            client_factory=lambda _: fake_client,
        )
        result = service.improve_email(
            original_email="Dear Team, please confirm.",
            tone="Formal",
            sender=SenderDetails(),
        )
        self.assertEqual(result.subject, "Delivery Update")
        self.assertIn("Dear Team", result.body)
        self.assertFalse(result.communication_analysis.available)
        self.assertEqual(len(fake_client.completions.calls), 2)

    def test_missing_api_key_is_safe(self) -> None:
        service = DeepSeekEmailService(self.settings(api_key=""))
        with self.assertRaises(AIServiceError) as context:
            service.generate_email(
                recipient="",
                requested_subject="",
                chinese_brief="请确认日期。",
                tone="Formal",
                sender=SenderDetails(),
            )
        self.assertEqual(context.exception.code, "missing_api_key")
        self.assertNotIn("Traceback", context.exception.user_message)

    def test_incoming_analysis_uses_dedicated_schema_and_counts_tokens(
        self,
    ) -> None:
        fake_client = FakeClient([json.dumps(VALID_ANALYSIS)])
        service = DeepSeekEmailService(
            self.settings(),
            client_factory=lambda _: fake_client,
        )

        result = service.analyze_incoming_email(
            original_subject="Delivery",
            original_email="Please confirm the revised date.",
            country_region="Malaysia",
        )

        self.assertEqual(result.summary, VALID_ANALYSIS["summary"])
        self.assertEqual(result.usage_tokens, 123)
        request = fake_client.completions.calls[0]
        self.assertIn(
            "untrusted data",
            request["messages"][0]["content"],
        )

    def test_incoming_analysis_repairs_once_then_fails_safely(self) -> None:
        fake_client = FakeClient(["not json", "still not json"])
        service = DeepSeekEmailService(
            self.settings(),
            client_factory=lambda _: fake_client,
        )

        with self.assertRaises(AIServiceError) as context:
            service.analyze_incoming_email(
                original_subject="",
                original_email="Please confirm.",
                country_region="",
            )

        self.assertEqual(context.exception.code, "analysis_parse_error")
        self.assertEqual(len(fake_client.completions.calls), 2)
        self.assertIn(
            "IncomingEmailAnalysis",
            fake_client.completions.calls[1]["messages"][0]["content"],
        )

    def test_incoming_analysis_accepts_one_successful_repair(self) -> None:
        fake_client = FakeClient(
            ["broken", json.dumps(VALID_ANALYSIS)]
        )
        service = DeepSeekEmailService(
            self.settings(),
            client_factory=lambda _: fake_client,
        )

        result = service.analyze_incoming_email(
            original_subject="Delivery",
            original_email="Please confirm.",
            country_region="",
        )

        self.assertEqual(result.usage_tokens, 246)
        self.assertEqual(len(fake_client.completions.calls), 2)

    def test_truncated_analysis_repairs_once_without_logging_content(
        self,
    ) -> None:
        private_email = "PRIVATE-INCOMING-EMAIL-CONTENT"
        private_response = '{"summary": "PRIVATE-MODEL-CONTENT"'
        fake_client = FakeClient(
            [private_response, json.dumps(VALID_ANALYSIS)]
        )
        service = DeepSeekEmailService(
            self.settings(),
            client_factory=lambda _: fake_client,
        )

        with self.assertLogs("ai_service", level="WARNING") as captured:
            result = service.analyze_incoming_email(
                original_subject="Delivery",
                original_email=private_email,
                country_region="",
            )

        logs = "\n".join(captured.output)
        self.assertEqual(result.summary, VALID_ANALYSIS["summary"])
        self.assertEqual(len(fake_client.completions.calls), 2)
        self.assertIn("invalid_or_truncated_json", logs)
        self.assertNotIn(private_email, logs)
        self.assertNotIn("PRIVATE-MODEL-CONTENT", logs)

    def test_failed_repair_logs_only_safe_failure_categories(self) -> None:
        private_email = "PRIVATE-FAILED-EMAIL"
        fake_client = FakeClient(
            ['{"summary": "PRIVATE-FIRST"', "PRIVATE-SECOND"]
        )
        service = DeepSeekEmailService(
            self.settings(),
            client_factory=lambda _: fake_client,
        )

        with self.assertLogs("ai_service", level="WARNING") as captured:
            with self.assertRaises(AIServiceError) as context:
                service.analyze_incoming_email(
                    original_subject="",
                    original_email=private_email,
                    country_region="",
                )

        logs = "\n".join(captured.output)
        self.assertEqual(context.exception.code, "analysis_parse_error")
        self.assertEqual(len(fake_client.completions.calls), 2)
        self.assertIn("invalid_or_truncated_json", logs)
        self.assertNotIn(private_email, logs)
        self.assertNotIn("PRIVATE-FIRST", logs)
        self.assertNotIn("PRIVATE-SECOND", logs)


if __name__ == "__main__":
    unittest.main()
