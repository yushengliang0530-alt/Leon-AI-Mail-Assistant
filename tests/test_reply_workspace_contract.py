import ast
import inspect
from pathlib import Path
import unittest

from ui.pages.reply import render_reply_workspace


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
            },
        )
        self.assertTrue(
            all(keyword.arg is not None for keyword in calls[0].keywords)
        )


if __name__ == "__main__":
    unittest.main()
