import inspect
import re
import unittest
from unittest.mock import Mock, patch

from ui.pages import home


EXPECTED_ACTIONS = {
    "reply",
    "supplier",
    "meeting",
    "progress",
    "approval",
    "schedule",
    "improve",
    "preflight",
    "scenarios",
}


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
            self.assertRegex(card.icon, r"^[a-z][a-z0-9_]*$")

    def test_high_frequency_cards_share_one_configuration_shape(self) -> None:
        actions = tuple(
            action
            for row in home.HIGH_FREQUENCY_ROWS
            for action in row
        )
        self.assertEqual(
            actions,
            ("supplier", "meeting", "progress", "approval"),
        )
        for action in actions:
            card = home.HOME_TASK_CARDS[action]
            self.assertIsInstance(card, home.TaskCard)
            self.assertFalse(card.primary)
            self.assertIsNone(card.status)

    def test_render_task_card_passes_material_icon_and_stable_key(self) -> None:
        card = home.HOME_TASK_CARDS["supplier"]
        with patch.object(home.st, "button") as button:
            home.render_task_card(card=card)
        button.assert_called_once()
        kwargs = button.call_args.kwargs
        self.assertEqual(kwargs["key"], "home__action__supplier")
        self.assertEqual(kwargs["icon"], ":material/local_shipping:")
        self.assertTrue(kwargs["use_container_width"])
        self.assertEqual(kwargs["args"], ("supplier",))

    def test_reply_card_preserves_primary_click_callback(self) -> None:
        card = home.HOME_TASK_CARDS["reply"]
        callback = Mock()
        with patch.object(home.st, "button") as button:
            home.render_task_card(card=card, on_click=callback)
        kwargs = button.call_args.kwargs
        self.assertEqual(kwargs["type"], "primary")
        self.assertIs(kwargs["on_click"], callback)
        self.assertEqual(kwargs["args"], ())

    def test_home_cards_use_only_the_shared_renderer(self) -> None:
        source = inspect.getsource(home.render_home)
        self.assertNotIn("st.button(", source)
        self.assertIn("render_task_card(", source)
        self.assertNotIn("_action_button", inspect.getsource(home))

    def test_css_defines_fixed_icon_column_and_mobile_single_column(self) -> None:
        source = inspect.getsource(home.render_home)
        compact = re.sub(r"\s+", " ", source)
        self.assertIn(
            "button > div > span { display:grid; "
            "grid-template-columns:3.25rem minmax(0,1fr)",
            compact,
        )
        self.assertIn('[data-testid="stIconMaterial"]', source)
        self.assertIn("@media (max-width:640px)", source)
        self.assertIn("flex-direction:column", compact)
        self.assertIn("overflow-x:hidden", compact)


if __name__ == "__main__":
    unittest.main()
