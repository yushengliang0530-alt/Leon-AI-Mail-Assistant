import unittest
from unittest.mock import Mock

from ai_service import EmailResult, SenderDetails
from data.email_scenarios import (
    SUPPLIER_SCENARIOS,
    get_supplier_scenario,
)
from prompts import scenario_generation_messages
from services.scenario_service import (
    ScenarioService,
    validate_scenario_facts,
)


class ScenarioEngineTests(unittest.TestCase):
    def test_supplier_scenarios_are_valid_and_readable(self) -> None:
        self.assertEqual(len(SUPPLIER_SCENARIOS), 4)
        self.assertEqual(
            get_supplier_scenario("supplier_plan_update").title_zh,
            "更新计划",
        )
        for scenario in SUPPLIER_SCENARIOS:
            field_keys = {field.key for field in scenario.fields}
            self.assertEqual(len(field_keys), len(scenario.fields))
            self.assertIn("supplier_name", field_keys)
            supplier = next(
                field
                for field in scenario.fields
                if field.key == "supplier_name"
            )
            self.assertTrue(supplier.required)

    def test_supplier_tasks_have_distinct_dynamic_fields(self) -> None:
        quotation = {
            field.key
            for field in get_supplier_scenario("supplier_quotation").fields
        }
        delivery = {
            field.key
            for field in get_supplier_scenario("supplier_delivery").fields
        }
        delay = {
            field.key
            for field in get_supplier_scenario(
                "supplier_delay_explanation"
            ).fields
        }
        self.assertIn("quotation_scope", quotation)
        self.assertNotIn("quotation_scope", delivery)
        self.assertIn("deliverable", delivery)
        self.assertIn("delayed_item", delay)

    def test_missing_required_facts_do_not_call_backend(self) -> None:
        backend = Mock()
        service = ScenarioService(backend)
        scenario = get_supplier_scenario("supplier_plan_update")

        with self.assertRaisesRegex(ValueError, "请填写供应商名称"):
            service.generate(
                scenario=scenario,
                facts={},
                tone="Formal",
                sender=SenderDetails(),
            )

        backend.generate_scenario_email.assert_not_called()

    def test_empty_optional_facts_are_removed_from_prompt_contract(self) -> None:
        scenario = get_supplier_scenario("supplier_plan_update")
        validation = validate_scenario_facts(
            scenario,
            {
                "supplier_name": "ABC Components",
                "project_name": "  ",
                "original_plan_date": "5 August 2026",
                "current_situation": "No updated plan received.",
                "requested_reply": "By Friday",
                "business_impact": "",
                "required_action": "Send the revised plan.",
            },
        )
        self.assertTrue(validation.is_valid)
        self.assertNotIn("project_name", validation.cleaned_facts)
        self.assertNotIn("business_impact", validation.cleaned_facts)

        messages = scenario_generation_messages(
            scenario_id=scenario.id,
            scenario_title=scenario.title_en,
            facts=validation.cleaned_facts,
            tone="Formal",
        )
        prompt = messages[1]["content"]
        self.assertNotIn('"project_name"', prompt)
        self.assertNotIn('"business_impact"', prompt)
        self.assertIn('"supplier_name": "ABC Components"', prompt)

    def test_valid_generation_calls_backend_once_with_clean_facts(self) -> None:
        backend = Mock()
        backend.generate_scenario_email.return_value = EmailResult(
            subject="Updated Plan Required",
            body="Please send the revised plan.\n\nBest regards,",
        )
        service = ScenarioService(backend)
        scenario = get_supplier_scenario("supplier_plan_update")
        result = service.generate(
            scenario=scenario,
            facts={
                "supplier_name": "ABC Components",
                "project_name": "",
                "original_plan_date": "5 August 2026",
                "current_situation": "No updated plan received.",
                "requested_reply": "By Friday",
                "required_action": "Send the revised plan.",
            },
            tone="Formal",
            sender=SenderDetails(),
        )
        self.assertEqual(result.subject, "Updated Plan Required")
        backend.generate_scenario_email.assert_called_once()
        sent_facts = backend.generate_scenario_email.call_args.kwargs["facts"]
        self.assertNotIn("project_name", sent_facts)
