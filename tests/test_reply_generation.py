import json
import unittest
from unittest.mock import Mock

from ai_service import SenderDetails
from models.incoming_email import parse_incoming_email_analysis
from models.reply_generation import (
    CoverageResult,
    GeneratedReply,
    parse_coverage,
    parse_generated_reply,
)
from services.reply_generation_service import ReplyGenerationService
from services.reply_item_service import normalize_reply_items
from reply_prompts import coverage_check_messages, reply_generation_messages
from tests.test_incoming_email_analysis import VALID_ANALYSIS


class ReplyGenerationModelTests(unittest.TestCase):
    def test_prompts_separate_generation_from_coverage(self) -> None:
        generation = "\n".join(
            item["content"] for item in reply_generation_messages({"x": 1})
        )
        coverage = "\n".join(
            item["content"] for item in coverage_check_messages({"x": 1})
        )
        self.assertIn("Never invent dates", generation)
        self.assertIn("Do not rewrite", coverage)
        self.assertIn("not_addressed", coverage)

    def test_generation_parses_json_and_fence(self) -> None:
        for content in (
            '{"subject":"Update","body":"Dear Team,\\nUpdate."}',
            '```json\n{"subject":"Update","body":"Dear Team,\\nUpdate."}\n```',
        ):
            result = parse_generated_reply(content)
            self.assertEqual(result.subject, "Update")

    def test_generation_rejects_empty_extra_and_invalid_json(self) -> None:
        for content in (
            "",
            '{"subject":"","body":"Body"}',
            '{"subject":"S","body":"B","coverage":[]}',
            "not json",
        ):
            with self.assertRaises((ValueError, json.JSONDecodeError)):
                parse_generated_reply(content)

    def test_coverage_all_statuses_and_local_summary(self) -> None:
        ids = ("a", "b", "c", "d")
        content = json.dumps(
            {
                "coverage": [
                    {"item_id": "a", "status": "addressed", "note": "Done"},
                    {
                        "item_id": "b",
                        "status": "partially_addressed",
                        "note": "Partial",
                    },
                    {"item_id": "c", "status": "postponed", "note": "Pending"},
                    {
                        "item_id": "d",
                        "status": "not_addressed",
                        "note": "Missing",
                    },
                ]
            }
        )
        result = parse_coverage(content, ids)
        self.assertEqual(result.covered_count, 2)
        self.assertEqual(result.partial_count, 1)
        self.assertEqual(result.not_addressed_count, 1)

    def test_coverage_rejects_missing_duplicate_unknown_and_bad_status(self) -> None:
        cases = [
            [{"item_id": "a", "status": "addressed", "note": "Done"}],
            [
                {"item_id": "a", "status": "addressed", "note": "Done"},
                {"item_id": "a", "status": "addressed", "note": "Again"},
            ],
            [
                {"item_id": "a", "status": "addressed", "note": "Done"},
                {"item_id": "x", "status": "addressed", "note": "Unknown"},
            ],
            [
                {"item_id": "a", "status": "perfect", "note": "Wrong"},
                {"item_id": "b", "status": "addressed", "note": "Done"},
            ],
        ]
        for coverage in cases:
            with self.assertRaises(ValueError):
                parse_coverage(
                    json.dumps({"coverage": coverage}), ("a", "b")
                )


class ReplyGenerationServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.analysis = parse_incoming_email_analysis(
            json.dumps(VALID_ANALYSIS)
        )
        self.items = normalize_reply_items(self.analysis)
        self.decisions = {
            self.items[0].item_id: {
                "item_id": self.items[0].item_id,
                "stance": "unable_to_confirm",
                "reason": "Internal verification is pending.",
                "user_notes": "Do not expose this internal detail.",
            }
        }
        self.backend = Mock()
        self.service = ReplyGenerationService(self.backend)

    def test_generate_uses_confirmed_data_and_appends_local_signature(self) -> None:
        self.backend.generate_reply_email.return_value = GeneratedReply(
            "Schedule Update", "Dear Team,\n\nWe cannot confirm the date."
        )
        result = self.service.generate(
            analysis=self.analysis,
            items=self.items,
            decisions=self.decisions,
            sender=SenderDetails(name="David Chen", company="ABC"),
        )
        self.assertIn("Best regards,", result.body)
        self.assertIn("David Chen\nABC", result.body)
        payload = self.backend.generate_reply_email.call_args.kwargs["payload"]
        self.assertNotIn(
            "user_notes", payload["decisions"][self.items[0].item_id]
        )

    def test_empty_sender_never_adds_leon(self) -> None:
        self.backend.generate_reply_email.return_value = GeneratedReply(
            "Update", "We cannot confirm the date."
        )
        result = self.service.generate(
            analysis=self.analysis,
            items=self.items,
            decisions=self.decisions,
            sender=SenderDetails(),
        )
        self.assertNotIn("Leon", result.body)
        self.assertTrue(result.body.endswith("Best regards,"))

    def test_target_tone_changes_prompt_payload_and_local_closing(self) -> None:
        self.backend.generate_reply_email.return_value = GeneratedReply(
            "Update", "We cannot confirm the date."
        )
        result = self.service.generate(
            analysis=self.analysis,
            items=self.items,
            decisions=self.decisions,
            sender=SenderDetails(),
            target_tone="Executive",
        )
        payload = self.backend.generate_reply_email.call_args.kwargs["payload"]
        self.assertEqual(payload["target_tone"], "Executive")
        self.assertTrue(result.body.endswith("Sincerely,"))

    def test_coverage_is_a_distinct_backend_call(self) -> None:
        expected = CoverageResult(
            items=(),
            addressed_count=0,
            partial_count=0,
            postponed_count=0,
            not_addressed_count=0,
            covered_count=0,
            total_count=0,
        )
        self.backend.check_reply_coverage.return_value = expected
        result = self.service.check_coverage(
            items=self.items,
            decisions=self.decisions,
            subject="Update",
            body="We cannot confirm the date.",
        )
        self.assertIs(result, expected)
        self.backend.generate_reply_email.assert_not_called()


if __name__ == "__main__":
    unittest.main()
