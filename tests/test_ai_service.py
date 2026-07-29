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
    parse_email_result,
)
from config import DeepSeekSettings
from prompts import generation_messages


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


if __name__ == "__main__":
    unittest.main()
