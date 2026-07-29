import unittest

from access_control import (
    configured_access_code,
    runtime_environment,
    verify_access_code,
)


class AccessControlTests(unittest.TestCase):
    def test_unconfigured_access_code_allows_local_development(self) -> None:
        self.assertEqual(configured_access_code({}), "")
        self.assertTrue(verify_access_code("", ""))

    def test_wrong_and_correct_access_codes(self) -> None:
        self.assertFalse(verify_access_code("invite-123", "wrong"))
        self.assertTrue(verify_access_code("invite-123", "invite-123"))

    def test_runtime_environment_returns_safe_labels(self) -> None:
        self.assertEqual(
            runtime_environment("http://127.0.0.1:8501", {}),
            "本地开发",
        )
        self.assertEqual(
            runtime_environment("https://example.streamlit.app", {}),
            "云端部署",
        )
        self.assertEqual(
            runtime_environment("", {"STREAMLIT_SHARING_MODE": "true"}),
            "云端部署",
        )


if __name__ == "__main__":
    unittest.main()
