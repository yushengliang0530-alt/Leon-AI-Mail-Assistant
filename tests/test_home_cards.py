import inspect
import re
import unittest
from unittest.mock import Mock, patch

from ui import components, styles
from ui.pages import compose_supplier, explore, home, improve


EXPECTED_ACTIONS = {"reply", "create", "improve"}


class HomeTaskCardTests(unittest.TestCase):
    def test_home_has_exactly_three_core_task_entries(self) -> None:
        cards = tuple(home.HOME_TASK_CARDS.values())
        self.assertEqual({card.action for card in cards}, EXPECTED_ACTIONS)
        self.assertEqual(len(cards), 3)
        self.assertNotIn("supplier", home.HOME_TASK_CARDS)
        self.assertTrue(home.HOME_TASK_CARDS["reply"].primary)
        self.assertEqual(home.WORKSPACE_ACTIONS, ("create", "improve"))

    def test_all_home_entries_have_unique_keys_icons_and_action_labels(self) -> None:
        cards = tuple(home.HOME_TASK_CARDS.values())
        keys = tuple(f"home__action__{card.action}" for card in cards)
        self.assertEqual(len(keys), len(set(keys)))
        for card in cards:
            self.assertTrue(card.title)
            self.assertTrue(card.description)
            self.assertTrue(card.action_label)
            self.assertRegex(card.icon, r"^[a-z][a-z0-9_]*$")

    def test_task_cards_use_shared_renderer_with_stable_callbacks(self) -> None:
        callback = Mock()
        card = home.HOME_TASK_CARDS["create"]
        with patch.object(components.st, "button") as button:
            components.render_task_card(card=card, on_click=callback)
        kwargs = button.call_args.kwargs
        self.assertEqual(kwargs["key"], "home__action__create")
        self.assertEqual(kwargs["icon"], ":material/edit_note:")
        self.assertTrue(kwargs["use_container_width"])
        self.assertIs(kwargs["on_click"], callback)

    def test_primary_reply_card_uses_primary_style(self) -> None:
        callback = Mock()
        with patch.object(components.st, "button") as button:
            components.render_task_card(
                card=home.HOME_TASK_CARDS["reply"],
                on_click=callback,
            )
        self.assertEqual(button.call_args.kwargs["type"], "primary")

    def test_home_routes_core_tasks_and_explore_without_expanding_content(self) -> None:
        source = inspect.getsource(home.render_home)
        self.assertIn("render_task_card(", source)
        self.assertIn("open_reply_workspace", source)
        self.assertIn("open_create_workspace", source)
        self.assertIn("open_improve_workspace", source)
        self.assertIn("open_explore_more", source)
        self.assertIn('key="home__explore_more"', source)
        self.assertNotIn("open_supplier_workflow", source)
        self.assertNotIn("_render_selected_action", inspect.getsource(home))

    def test_home_uses_copilot_information_hierarchy(self) -> None:
        source = inspect.getsource(home.render_home)
        self.assertIn("今天需要完成什么商务沟通？", source)
        self.assertIn("选择任务，Leon AI会一步步帮助你完成。", source)
        self.assertIn("核心任务", source)
        self.assertIn("CORE TASKS", source)
        self.assertIn("常用任务", source)
        self.assertIn("EVERYDAY TASKS", source)
        self.assertIn("探索更多工作流 · Explore More", source)

    def test_explore_catalog_only_exposes_supplier_as_available(self) -> None:
        items = {item["key"]: item for item in explore.CATALOG_ITEMS}
        self.assertEqual(set(items), {"supplier", "meeting", "report", "approval"})
        self.assertTrue(items["supplier"]["available"])
        self.assertTrue(
            all(not item["available"] for key, item in items.items() if key != "supplier")
        )

    def test_workspaces_use_single_shell_without_improve_placeholder(self) -> None:
        source = inspect.getsource(compose_supplier.render_create_workspace)
        improve_source = inspect.getsource(improve.render_improve_workspace)
        self.assertIn("render_workspace_shell", source)
        self.assertIn("_workflow_steps", source)
        self.assertIn("_render_step_one", source)
        self.assertIn("_render_step_four", source)
        self.assertIn("render_workspace_shell", improve_source)
        self.assertIn("_render_draft_step", improve_source)
        self.assertIn("_render_target_step", improve_source)
        self.assertIn("_render_result_step", improve_source)
        self.assertEqual(len(compose_supplier.CREATE_WORKFLOW_STEPS), 4)
        self.assertEqual(len(improve.IMPROVE_WORKFLOW_STEPS), 3)

    def test_design_tokens_cover_required_status_and_spacing_values(self) -> None:
        source = inspect.getsource(styles)
        for token in (
            "--la-primary",
            "--la-canvas",
            "--la-surface",
            "--la-border",
            "--la-ink",
            "--la-text",
            "--la-muted",
            "--la-success",
            "--la-warning",
            "--la-risk",
            "--la-info",
        ):
            self.assertIn(token, source)
        for spacing in (".25rem", ".5rem", ".75rem", "1rem", "1.5rem", "2rem", "3rem", "4rem"):
            self.assertIn(spacing, source)

    def test_workspace_css_uses_shared_shell_and_mobile_stack(self) -> None:
        source = inspect.getsource(styles)
        compact = re.sub(r"\s+", " ", source)
        self.assertIn(".la-workspace-header", source)
        self.assertIn(".la-workflow-nav", source)
        self.assertIn(".la-action-bar", source)
        self.assertIn(".la-workspace-empty-state", source)
        self.assertIn('@media (max-width: 768px)', source)
        self.assertIn("flex-direction:column", compact)
        self.assertIn("overflow-x:clip", compact)

    def test_workspace_headers_share_icons_and_mobile_stepper_is_compact(self) -> None:
        source = inspect.getsource(components)
        style_source = inspect.getsource(styles)
        self.assertIn("_HEADER_ICON_PATHS", source)
        self.assertIn("la-workspace-header__icon", source)
        self.assertIn("icon: str = \"spark\"", source)
        self.assertIn(".la-workflow-nav { display:none; }", style_source)

    def test_create_completed_steps_use_the_shared_complete_state(self) -> None:
        states = [step.state for step in compose_supplier._workflow_steps(3)]
        self.assertEqual(states, ["complete", "complete", "current", "upcoming"])

    def test_improve_comparison_uses_shared_panels_and_mobile_safe_styles(self) -> None:
        page_source = inspect.getsource(improve)
        style_source = inspect.getsource(styles)
        self.assertIn("render_before_after_panel", page_source)
        self.assertIn("render_copy_button", page_source)
        self.assertIn("st-key-workspace__improve", style_source)
        self.assertIn("@media (max-width:768px)", style_source)

    def test_common_workspace_components_are_available(self) -> None:
        for name in (
            "render_global_header",
            "render_workspace_header",
            "render_workspace_shell",
            "render_workflow_nav",
            "render_action_bar",
            "render_workspace_empty_state",
            "render_scenario_cards",
            "render_guided_question_header",
            "render_review_items",
            "render_optimization_option_cards",
            "render_before_after_panel",
        ):
            self.assertTrue(callable(getattr(components, name)))


if __name__ == "__main__":
    unittest.main()
