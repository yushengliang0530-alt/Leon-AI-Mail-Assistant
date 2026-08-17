import inspect
import re
import unittest
from unittest.mock import Mock, patch

from ui import components, styles
from ui.pages import home


EXPECTED_ACTIONS = {"reply", "supplier", "improve"}


class HomeTaskCardTests(unittest.TestCase):
    def test_all_home_entries_have_unique_keys_and_icons(self) -> None:
        cards = tuple(home.HOME_TASK_CARDS.values())
        self.assertEqual({card.action for card in cards}, EXPECTED_ACTIONS)
        self.assertEqual(len(cards), len(EXPECTED_ACTIONS))
        keys = tuple(f"home__action__{card.action}" for card in cards)
        self.assertEqual(len(keys), len(set(keys)))
        for card in cards:
            self.assertTrue(card.title)
            self.assertTrue(card.description)
            self.assertTrue(card.action_label)
            self.assertRegex(card.icon, r"^[a-z][a-z0-9_]*$")

    def test_production_workspace_cards_share_one_configuration_shape(
        self,
    ) -> None:
        self.assertEqual(home.WORKSPACE_ACTIONS, ("supplier", "improve"))
        for card in home.HOME_TASK_CARDS.values():
            self.assertIsInstance(card, components.TaskCard)
        self.assertTrue(home.HOME_TASK_CARDS["reply"].primary)
        self.assertFalse(home.HOME_TASK_CARDS["supplier"].primary)
        self.assertFalse(home.HOME_TASK_CARDS["improve"].primary)

    def test_render_task_card_passes_material_icon_stable_key_and_callback(
        self,
    ) -> None:
        callback = Mock()
        card = home.HOME_TASK_CARDS["supplier"]
        with patch.object(components.st, "button") as button:
            components.render_task_card(card=card, on_click=callback)
        button.assert_called_once()
        kwargs = button.call_args.kwargs
        self.assertEqual(kwargs["key"], "home__action__supplier")
        self.assertEqual(kwargs["icon"], ":material/local_shipping:")
        self.assertTrue(kwargs["use_container_width"])
        self.assertIs(kwargs["on_click"], callback)

    def test_reply_card_preserves_primary_click_callback(self) -> None:
        callback = Mock()
        card = home.HOME_TASK_CARDS["reply"]
        with patch.object(components.st, "button") as button:
            components.render_task_card(card=card, on_click=callback)
        kwargs = button.call_args.kwargs
        self.assertEqual(kwargs["type"], "primary")
        self.assertIs(kwargs["on_click"], callback)

    def test_home_cards_use_only_the_shared_renderer(self) -> None:
        source = inspect.getsource(home.render_home)
        self.assertNotIn("st.button(", source)
        self.assertIn("render_task_card(", source)
        self.assertIn("render_global_header(", source)
        self.assertNotIn("set_selected_home_action", source)
        self.assertNotIn("_render_selected_action", inspect.getsource(home))

    def test_home_has_direct_routes_for_all_available_workflows(self) -> None:
        source = inspect.getsource(home.render_home)
        self.assertIn("open_reply_workspace", source)
        self.assertIn("open_supplier_workflow", source)
        self.assertIn("open_legacy_improve", source)
        self.assertNotIn("home__open_supplier_workflow", source)
        self.assertNotIn("home__open_legacy_improve", source)

    def test_home_uses_approved_brand_and_information_hierarchy(self) -> None:
        source = inspect.getsource(home.render_home)
        self.assertIn("今天需要完成什么商务沟通？", source)
        self.assertIn("选择任务，Leon AI会一步步帮助你完成。", source)
        self.assertIn("主要工作流", source)
        self.assertIn("PRIMARY WORKFLOW", source)
        self.assertIn("常用任务", source)
        self.assertIn("EVERYDAY TASKS", source)
        self.assertIn("安全提醒", source)

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

    def test_home_cards_use_shared_layout_with_primary_variant(self) -> None:
        source = inspect.getsource(styles.inject_workspace_home_styles)
        compact = re.sub(r"\s+", " ", source)
        self.assertIn('[class*="st-key-home__action__"]', source)
        self.assertIn("grid-template-columns:3.25rem minmax(0,1fr) 2.5rem", compact)
        self.assertIn('content:"→"', compact)
        self.assertIn(".st-key-home__action__reply", source)
        self.assertNotIn("!important", source)

    def test_mobile_styles_make_cards_single_column_without_horizontal_scroll(
        self,
    ) -> None:
        source = inspect.getsource(styles)
        compact = re.sub(r"\s+", " ", source)
        self.assertIn("@media (max-width: 640px)", source)
        self.assertIn("flex-direction:column", compact)
        self.assertIn("overflow-x:clip", compact)
        self.assertIn("min-height:6.5rem", compact)

    def test_common_presentation_components_are_available(self) -> None:
        for name in (
            "render_global_header",
            "render_page_header",
            "render_task_card",
            "render_section_header",
            "render_status_badge",
            "render_summary_card",
            "render_notice_bar",
            "render_empty_state",
            "render_loading_state",
            "primary_action_button",
            "secondary_action_button",
        ):
            self.assertTrue(callable(getattr(components, name)))


if __name__ == "__main__":
    unittest.main()
