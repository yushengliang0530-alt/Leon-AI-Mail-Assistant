import json
import unittest
from unittest.mock import Mock

from models.incoming_email import parse_incoming_email_analysis
from models.preflight import (
    PreflightItem,
    SemanticPreflightResult,
    parse_semantic_preflight,
)
from models.reply_generation import CoverageItem, CoverageResult
from preflight_prompts import preflight_check_messages
from services.preflight_service import PreflightService, report_from_items
from tests.test_incoming_email_analysis import VALID_ANALYSIS


def semantic_json(status: str = "GOOD") -> str:
    return json.dumps(
        {
            "summary": "The reply is ready for final review.",
            "checks": [
                {
                    "item_id": item_id,
                    "status": status,
                    "title": item_id,
                    "message": "Checked.",
                    "suggestion": None,
                }
                for item_id in (
                    "action_clarity",
                    "deadline_clarity",
                    "salutation",
                    "tone_alignment",
                    "commitment_risk",
                )
            ],
        }
    )


def coverage(status: str = "addressed") -> CoverageResult:
    counts = {
        "addressed": int(status == "addressed"),
        "partially_addressed": int(status == "partially_addressed"),
        "postponed": int(status == "postponed"),
        "not_addressed": int(status == "not_addressed"),
    }
    return CoverageResult(
        items=(CoverageItem("request_1", status, "Coverage note."),),
        addressed_count=counts["addressed"],
        partial_count=counts["partially_addressed"],
        postponed_count=counts["postponed"],
        not_addressed_count=counts["not_addressed"],
        covered_count=counts["addressed"] + counts["postponed"],
        total_count=1,
    )


class PreflightModelTests(unittest.TestCase):
    def test_normal_and_markdown_json_parse(self) -> None:
        for content in (
            semantic_json(),
            f"```json\n{semantic_json()}\n```",
        ):
            result = parse_semantic_preflight(content)
            self.assertEqual(len(result.items), 5)
            self.assertEqual(result.items[0].item_id, "action_clarity")

    def test_invalid_json_status_and_missing_check_are_rejected(self) -> None:
        invalid_status = json.loads(semantic_json())
        invalid_status["checks"][0]["status"] = "SAFE"
        missing = json.loads(semantic_json())
        missing["checks"].pop()
        for content in ("not json", json.dumps(invalid_status), json.dumps(missing)):
            with self.assertRaises((ValueError, json.JSONDecodeError)):
                parse_semantic_preflight(content)

    def test_prompt_checks_without_rewriting(self) -> None:
        prompt = "\n".join(
            message["content"]
            for message in preflight_check_messages({"target_tone": "Formal"})
        )
        self.assertIn("Do not rewrite", prompt)
        self.assertIn("target_tone", prompt)
        self.assertIn("WARNING", prompt)

    def test_report_uses_highest_severity_without_score(self) -> None:
        items = (
            PreflightItem("a", "x", "GOOD", "A", "OK", None, "local"),
            PreflightItem("b", "x", "CHECK", "B", "Check", None, "local"),
            PreflightItem("c", "x", "WARNING", "C", "Risk", None, "ai"),
        )
        report = report_from_items(items)
        self.assertEqual(report.overall_status, "WARNING")
        self.assertNotIn("%", report.summary)


class PreflightServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.analysis = parse_incoming_email_analysis(
            json.dumps(VALID_ANALYSIS)
        )
        self.decisions = {
            "request_1": {
                "item_id": "request_1",
                "stance": "unable_to_confirm",
                "next_update_time": "5:00 PM this Friday",
                "user_notes": "private internal note",
            }
        }
        self.backend = Mock()
        self.backend.check_reply_preflight.return_value = (
            parse_semantic_preflight(semantic_json())
        )
        self.service = PreflightService(self.backend)

    def inspect(
        self,
        body: str = "Dear Team,\n\nWe cannot confirm the date yet.",
        coverage_result: CoverageResult | None = None,
    ):
        return self.service.inspect(
            analysis=self.analysis,
            decisions=self.decisions,
            subject="Delivery Update",
            body=body,
            coverage=coverage_result or coverage(),
            target_tone="Formal",
        )

    def test_all_good_combines_local_and_mocked_ai(self) -> None:
        report = self.inspect()
        self.assertEqual(report.overall_status, "GOOD")
        self.assertEqual(len(report.items), 9)
        self.backend.check_reply_preflight.assert_called_once()
        payload = self.backend.check_reply_preflight.call_args.kwargs["payload"]
        self.assertEqual(payload["target_tone"], "Formal")
        self.assertNotIn("user_notes", payload["decisions"]["request_1"])

    def test_attachment_creates_check(self) -> None:
        report = self.inspect(
            "Dear Team,\n\nPlease find attached the updated plan."
        )
        attachment = next(
            item for item in report.items if item.item_id == "attachment"
        )
        self.assertEqual(attachment.status, "CHECK")
        self.assertEqual(report.overall_status, "CHECK")

    def test_coverage_partial_missing_and_postponed_are_visible(self) -> None:
        for status in (
            "partially_addressed",
            "not_addressed",
            "postponed",
        ):
            with self.subTest(status=status):
                report = self.inspect(coverage_result=coverage(status))
                item = next(
                    item for item in report.items
                    if item.item_id == "coverage__request_1"
                )
                self.assertEqual(item.status, "CHECK")

    def test_missing_coverage_is_check_not_fake_good(self) -> None:
        report = self.service.inspect(
            analysis=self.analysis,
            decisions=self.decisions,
            subject="Delivery Update",
            body="Dear Team,\n\nWe cannot confirm the date yet.",
            coverage=None,
            target_tone="Formal",
        )
        self.assertEqual(report.items[0].item_id, "coverage_unavailable")
        self.assertEqual(report.items[0].status, "CHECK")

    def test_new_date_and_amount_create_warning(self) -> None:
        report = self.inspect(
            "Dear Team,\n\nWe guarantee delivery on 2026-08-15 "
            "and payment of USD 50,000."
        )
        grounding = next(
            item for item in report.items if item.item_id == "fact_grounding"
        )
        self.assertEqual(grounding.status, "WARNING")
        self.assertEqual(report.overall_status, "WARNING")

    def test_semantic_commitment_risk_is_preserved_as_warning(self) -> None:
        data = json.loads(semantic_json())
        data["checks"][-1].update(
            {
                "status": "WARNING",
                "message": "The reply makes an unconditional commitment.",
                "suggestion": "Confirm authority before sending.",
            }
        )
        self.backend.check_reply_preflight.return_value = (
            parse_semantic_preflight(json.dumps(data))
        )
        report = self.inspect()
        commitment = next(
            item for item in report.items
            if item.item_id == "commitment_risk"
        )
        self.assertEqual(commitment.status, "WARNING")
        self.assertEqual(report.overall_status, "WARNING")

    def test_confirmed_date_is_not_invented(self) -> None:
        report = self.inspect(
            "Dear Team,\n\nThe original schedule was 25 July."
        )
        grounding = next(
            item for item in report.items if item.item_id == "fact_grounding"
        )
        self.assertEqual(grounding.status, "GOOD")

    def test_long_email_check_and_warning_thresholds(self) -> None:
        for count, expected in ((451, "CHECK"), (701, "WARNING")):
            report = self.inspect("word " * count)
            length = next(
                item for item in report.items if item.item_id == "email_length"
            )
            self.assertEqual(length.status, expected)


if __name__ == "__main__":
    unittest.main()
