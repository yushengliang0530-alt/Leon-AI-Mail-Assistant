import ast
import inspect
from pathlib import Path
import re
import unittest

from ui.pages.reply import _reply_workflow_steps, render_reply_workspace
from ui import components, styles


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ReplyWorkspaceContractTests(unittest.TestCase):
    def test_public_signature_has_explicit_service_dependencies(self) -> None:
        signature = inspect.signature(render_reply_workspace)
        self.assertEqual(
            tuple(signature.parameters),
            (
                "analysis_service",
                "generation_service",
                "preflight_service",
                "render_privacy_notice",
                "service_status",
            ),
        )
        for name in (
            "analysis_service",
            "generation_service",
            "preflight_service",
        ):
            parameter = signature.parameters[name]
            self.assertEqual(parameter.kind, inspect.Parameter.KEYWORD_ONLY)
            self.assertIs(parameter.default, inspect.Parameter.empty)
        self.assertIsNone(
            signature.parameters["render_privacy_notice"].default
        )
        self.assertEqual(signature.parameters["service_status"].default, "已配置")
        self.assertFalse(
            any(
                parameter.kind is inspect.Parameter.VAR_KEYWORD
                for parameter in signature.parameters.values()
            )
        )

    def test_app_injects_exact_reply_workspace_services(self) -> None:
        tree = ast.parse((PROJECT_ROOT / "app.py").read_text(encoding="utf-8"))
        calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "render_reply_workspace"
        ]
        self.assertEqual(len(calls), 1)
        self.assertEqual(
            {keyword.arg for keyword in calls[0].keywords},
            {
                "analysis_service",
                "generation_service",
                "preflight_service",
                "service_status",
            },
        )
        self.assertTrue(
            all(keyword.arg is not None for keyword in calls[0].keywords)
        )

    def test_reply_stepper_maps_existing_reply_state_without_mutating_it(self) -> None:
        steps = _reply_workflow_steps(3)
        self.assertEqual([step.label for step in steps], [
            "Email",
            "Analysis",
            "Decision",
            "Generate",
            "Check",
        ])
        self.assertEqual(
            [step.state for step in steps],
            ["complete", "complete", "current", "upcoming", "upcoming"],
        )

    def test_reply_workspace_uses_the_shared_responsive_shell(self) -> None:
        reply_source = (PROJECT_ROOT / "ui" / "pages" / "reply.py").read_text(
            encoding="utf-8"
        )
        styles_source = re.sub(r"\s+", " ", inspect.getsource(styles))
        self.assertIn("render_workspace_shell(", reply_source)
        self.assertIn(
            ".st-key-workspace__reply.la-workflow-nav{display:none}",
            re.sub(r"\s+", "", reply_source),
        )
        self.assertIn("@media (max-width: 768px)", styles_source)
        self.assertIn("flex-direction:column", styles_source)
        self.assertIn("overflow-x:clip", styles_source)

    def test_analysis_presentation_uses_shared_components_and_tokens(self) -> None:
        reply_source = (PROJECT_ROOT / "ui" / "pages" / "reply.py").read_text(
            encoding="utf-8"
        )
        styles_source = inspect.getsource(styles)
        for name in (
            "render_analysis_summary_panel",
            "render_analysis_action_cards",
            "render_analysis_date_cards",
            "render_analysis_notices",
            "render_strategy_list",
            "tertiary_action_button",
        ):
            self.assertTrue(callable(getattr(components, name)))
            self.assertIn(name, reply_source)
        for selector in (
            ".la-analysis-summary",
            ".la-analysis-item",
            ".la-analysis-date-grid",
            ".la-analysis-notice",
            ".la-strategy-list",
        ):
            self.assertIn(selector, styles_source)
        self.assertIn(".la-analysis-date-grid { grid-template-columns:1fr; }", styles_source)


if __name__ == "__main__":
    unittest.main()
