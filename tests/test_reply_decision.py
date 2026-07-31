import json
import unittest

from models.incoming_email import parse_incoming_email_analysis
from models.reply_decision import ReplyDecision, ReplyItem
from services.reply_item_service import (
    build_decision_summary,
    decision_digest,
    decision_publishable_text,
    normalize_reply_items,
    validate_decision,
)
from tests.test_incoming_email_analysis import VALID_ANALYSIS


class ReplyItemServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.analysis = parse_incoming_email_analysis(
            json.dumps(VALID_ANALYSIS)
        )
        self.items = normalize_reply_items(self.analysis)

    def test_linked_question_merges_and_preserves_stable_id(self) -> None:
        self.assertEqual(len(self.items), 1)
        item = self.items[0]
        self.assertEqual(item.item_id, "request_1")
        self.assertEqual(item.source_question_ids, ("question_1",))
        self.assertTrue(item.required)
        self.assertIn("相关问题", item.description)

    def test_unlinked_question_remains_separate(self) -> None:
        data = json.loads(json.dumps(VALID_ANALYSIS))
        data["questions_requiring_reply"][0]["related_request_id"] = None
        items = normalize_reply_items(
            parse_incoming_email_analysis(json.dumps(data))
        )
        self.assertEqual([item.item_id for item in items], [
            "request_1",
            "question_1",
        ])
        self.assertEqual(items[0].item_type, "request")
        self.assertEqual(items[1].item_type, "question")

    def test_missing_deadline_is_not_invented(self) -> None:
        data = json.loads(json.dumps(VALID_ANALYSIS))
        data["sender_requests"][0]["deadline"] = None
        data["questions_requiring_reply"][0]["deadline"] = None
        item = normalize_reply_items(
            parse_incoming_email_analysis(json.dumps(data))
        )[0]
        self.assertIsNone(item.deadline)

    def test_conflicting_deadlines_are_uncertain(self) -> None:
        data = json.loads(json.dumps(VALID_ANALYSIS))
        data["sender_requests"][0]["deadline"] = "Friday"
        data["questions_requiring_reply"][0]["deadline"] = "Monday"
        item = normalize_reply_items(
            parse_incoming_email_analysis(json.dumps(data))
        )[0]
        self.assertEqual(item.deadline, "Friday")
        self.assertTrue(item.uncertain)

    def test_question_deadline_fills_missing_request_deadline(self) -> None:
        data = json.loads(json.dumps(VALID_ANALYSIS))
        data["sender_requests"][0]["deadline"] = None
        item = normalize_reply_items(
            parse_incoming_email_analysis(json.dumps(data))
        )[0]
        self.assertEqual(item.deadline, "5:00 PM this Friday")

    def test_request_uncertainty_propagates(self) -> None:
        data = json.loads(json.dumps(VALID_ANALYSIS))
        data["sender_requests"][0]["uncertain"] = True
        item = normalize_reply_items(
            parse_incoming_email_analysis(json.dumps(data))
        )[0]
        self.assertTrue(item.uncertain)

    def test_optional_unlinked_question_stays_optional(self) -> None:
        data = json.loads(json.dumps(VALID_ANALYSIS))
        data["sender_requests"] = []
        question = data["questions_requiring_reply"][0]
        question["related_request_id"] = None
        question["required"] = False
        item = normalize_reply_items(
            parse_incoming_email_analysis(json.dumps(data))
        )[0]
        self.assertEqual(item.item_type, "question")
        self.assertFalse(item.required)

    def test_request_order_is_stable(self) -> None:
        data = json.loads(json.dumps(VALID_ANALYSIS))
        second = dict(data["sender_requests"][0])
        second["item_id"] = "request_2"
        second["description"] = "Provide a recovery plan."
        data["sender_requests"].append(second)
        items = normalize_reply_items(
            parse_incoming_email_analysis(json.dumps(data))
        )
        self.assertEqual(
            [item.item_id for item in items],
            ["request_1", "request_2"],
        )

    def test_recommendations_create_items_when_requests_and_questions_empty(
        self,
    ) -> None:
        data = json.loads(json.dumps(VALID_ANALYSIS))
        data["sender_requests"] = []
        data["questions_requiring_reply"] = []
        data["recommended_reply_items"] = [
            {
                "description": "Confirm receipt of the update.",
                "reason": "The email contains a project status update.",
                "required": True,
                "uncertain": False,
            },
            {
                "description": "Confirm whether the PIM impact will be assessed.",
                "reason": "The schedule changes may affect the PIM.",
                "required": True,
                "uncertain": True,
            },
        ]
        items = normalize_reply_items(
            parse_incoming_email_analysis(json.dumps(data))
        )
        self.assertEqual(len(items), 2)
        self.assertEqual(
            [item.item_type for item in items],
            ["recommendation", "recommendation"],
        )
        self.assertEqual(
            [item.item_id for item in items],
            ["recommendation_1", "recommendation_2"],
        )

    def test_pure_status_update_uses_recommended_reply_items(self) -> None:
        data = json.loads(json.dumps(VALID_ANALYSIS))
        data["sender_requests"] = []
        data["questions_requiring_reply"] = []
        data["summary"] = "The supplier shared revised document dates."
        data["recommended_reply_items"] = [
            {
                "description": "Acknowledge the revised document schedule.",
                "reason": "The status update changes several planned dates.",
                "required": False,
                "uncertain": False,
            }
        ]
        items = normalize_reply_items(
            parse_incoming_email_analysis(json.dumps(data))
        )
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].item_type, "recommendation")
        self.assertFalse(items[0].required)

    def test_pure_notification_has_no_invented_reply_item(self) -> None:
        data = json.loads(json.dumps(VALID_ANALYSIS))
        data["sender_requests"] = []
        data["questions_requiring_reply"] = []
        data["recommended_reply_items"] = []
        data["summary"] = "The office will be closed on Friday."
        items = normalize_reply_items(
            parse_incoming_email_analysis(json.dumps(data))
        )
        self.assertEqual(items, ())

    def test_exact_duplicate_recommendation_is_not_added_twice(self) -> None:
        data = json.loads(json.dumps(VALID_ANALYSIS))
        data["recommended_reply_items"] = [
            {
                "description": "  Explain   the delay. ",
                "reason": "Recommended coverage.",
                "required": True,
                "uncertain": False,
            }
        ]
        items = normalize_reply_items(
            parse_incoming_email_analysis(json.dumps(data))
        )
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].item_type, "request")


class ReplyDecisionValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        analysis = parse_incoming_email_analysis(json.dumps(VALID_ANALYSIS))
        self.item = normalize_reply_items(analysis)[0]

    def validate(self, **values):
        decision = ReplyDecision(item_id=self.item.item_id, **values)
        return validate_decision(self.item, decision)

    def test_no_default_decision_does_not_validate_required_item(self) -> None:
        self.assertFalse(validate_decision(self.item, None).valid)

    def test_accept_requires_confirmed_facts(self) -> None:
        self.assertFalse(self.validate(stance="accept").valid)
        self.assertTrue(
            self.validate(
                stance="accept", confirmed_facts="We can provide the update."
            ).valid
        )

    def test_partial_requires_both_parts(self) -> None:
        self.assertFalse(
            self.validate(stance="partial", accepted_part="Provide reason").valid
        )

    def test_decline_requires_public_reason(self) -> None:
        self.assertFalse(self.validate(stance="decline").valid)
        self.assertTrue(
            self.validate(
                stance="decline", reason="This is outside the agreed scope."
            ).valid
        )

    def test_request_info_accepts_required_information(self) -> None:
        self.assertTrue(
            self.validate(
                stance="request_info",
                requested_information="Please provide the production status.",
            ).valid
        )

    def test_invalid_stance_is_rejected(self) -> None:
        self.assertFalse(self.validate(stance="automatic_accept").valid)

    def test_mismatched_item_id_is_rejected(self) -> None:
        decision = ReplyDecision(
            item_id="another_item",
            stance="accept",
            confirmed_facts="Confirmed",
        )
        self.assertFalse(validate_decision(self.item, decision).valid)
        self.assertTrue(
            self.validate(
                stance="partial",
                accepted_part="Provide reason",
                declined_part="No confirmed date",
            ).valid
        )

    def test_request_info_custom_and_no_response_rules(self) -> None:
        self.assertFalse(self.validate(stance="request_info").valid)
        self.assertFalse(self.validate(stance="custom").valid)
        self.assertFalse(
            self.validate(
                stance="no_response", include_in_reply=False
            ).valid
        )
        self.assertTrue(
            self.validate(
                stance="no_response",
                include_in_reply=False,
                no_response_confirmed=True,
            ).valid
        )

    def test_unable_to_confirm_does_not_require_date(self) -> None:
        self.assertTrue(
            self.validate(
                stance="unable_to_confirm",
                reason="Internal verification is pending.",
            ).valid
        )

    def test_custom_requires_instruction(self) -> None:
        self.assertFalse(self.validate(stance="custom").valid)
        self.assertTrue(
            self.validate(
                stance="custom",
                custom_instruction="Acknowledge without making a commitment.",
            ).valid
        )

    def test_optional_item_without_decision_is_valid_and_skipped(self) -> None:
        optional = ReplyItem(
            item_id="optional_1",
            item_type="question",
            description="Optional background question",
            deadline=None,
            required=False,
            source_request_id=None,
            source_question_ids=("optional_1",),
            uncertain=False,
        )
        self.assertTrue(validate_decision(optional, None).valid)
        summary = build_decision_summary((optional,), {})
        self.assertTrue(summary.ready)
        self.assertEqual(summary.skipped_optional, (optional,))

    def test_invalid_required_decision_blocks_readiness(self) -> None:
        raw = ReplyDecision(
            item_id=self.item.item_id,
            stance="partial",
            accepted_part="Only one half",
        ).to_dict()
        summary = build_decision_summary(
            (self.item,), {self.item.item_id: raw}
        )
        self.assertFalse(summary.ready)
        self.assertEqual(summary.undecided, (self.item,))

    def test_no_response_is_separated_from_decided_items(self) -> None:
        raw = ReplyDecision(
            item_id=self.item.item_id,
            stance="no_response",
            include_in_reply=False,
            no_response_confirmed=True,
        ).to_dict()
        summary = build_decision_summary(
            (self.item,), {self.item.item_id: raw}
        )
        self.assertTrue(summary.ready)
        self.assertEqual(summary.excluded, (self.item,))
        self.assertFalse(summary.decided)

    def test_publishable_text_excludes_internal_and_excluded_text(self) -> None:
        decisions = {
            "a": ReplyDecision(
                item_id="a",
                stance="accept",
                confirmed_facts="Public confirmed fact",
                user_notes="Internal approval secret",
            ).to_dict(),
            "b": ReplyDecision(
                item_id="b",
                stance="no_response",
                reason="Excluded reason",
                include_in_reply=False,
                no_response_confirmed=True,
            ).to_dict(),
        }
        content = decision_publishable_text(decisions)
        self.assertIn("Public confirmed fact", content)
        self.assertNotIn("Internal approval secret", content)
        self.assertNotIn("Excluded reason", content)

    def test_decision_edit_changes_digest(self) -> None:
        first = {
            "a": ReplyDecision(
                item_id="a",
                stance="accept",
                confirmed_facts="First",
            ).to_dict()
        }
        second = json.loads(json.dumps(first))
        second["a"]["confirmed_facts"] = "Second"
        self.assertNotEqual(decision_digest(first), decision_digest(second))

    def test_decision_round_trip_preserves_fields(self) -> None:
        original = ReplyDecision(
            item_id="request_1",
            stance="partial",
            accepted_part="Reason",
            declined_part="Date",
            alternative="Provide an update later",
        )
        self.assertEqual(
            ReplyDecision.from_dict(original.to_dict()),
            original,
        )

    def test_summary_can_include_all_four_groups(self) -> None:
        optional = ReplyItem(
            "optional",
            "question",
            "Optional",
            None,
            False,
            None,
            ("optional",),
            False,
        )
        excluded = ReplyItem(
            "excluded",
            "request",
            "Excluded",
            None,
            True,
            "excluded",
            (),
            False,
        )
        undecided = ReplyItem(
            "undecided",
            "request",
            "Undecided",
            None,
            True,
            "undecided",
            (),
            False,
        )
        decisions = {
            self.item.item_id: ReplyDecision(
                item_id=self.item.item_id,
                stance="accept",
                confirmed_facts="Confirmed",
            ).to_dict(),
            excluded.item_id: ReplyDecision(
                item_id=excluded.item_id,
                stance="no_response",
                include_in_reply=False,
                no_response_confirmed=True,
            ).to_dict(),
        }
        summary = build_decision_summary(
            (self.item, excluded, optional, undecided), decisions
        )
        self.assertEqual(len(summary.decided), 1)
        self.assertEqual(len(summary.excluded), 1)
        self.assertEqual(len(summary.skipped_optional), 1)
        self.assertEqual(len(summary.undecided), 1)
        self.assertFalse(summary.ready)

    def test_publishable_text_is_stable_by_item_id(self) -> None:
        a = ReplyDecision(
            item_id="a", stance="accept", confirmed_facts="Alpha"
        ).to_dict()
        b = ReplyDecision(
            item_id="b", stance="accept", confirmed_facts="Beta"
        ).to_dict()
        self.assertEqual(
            decision_publishable_text({"b": b, "a": a}),
            decision_publishable_text({"a": a, "b": b}),
        )

    def test_summary_and_digest_are_deterministic(self) -> None:
        decision = ReplyDecision(
            item_id=self.item.item_id,
            stance="accept",
            confirmed_facts="We will provide the explanation.",
        ).to_dict()
        decisions = {self.item.item_id: decision}
        summary = build_decision_summary((self.item,), decisions)
        self.assertTrue(summary.ready)
        self.assertEqual(summary.decided, (self.item,))
        self.assertEqual(
            decision_digest(decisions),
            decision_digest(dict(reversed(list(decisions.items())))),
        )


if __name__ == "__main__":
    unittest.main()
