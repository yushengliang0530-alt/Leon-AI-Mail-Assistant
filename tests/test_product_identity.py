import unittest


class ProductIdentityTests(unittest.TestCase):
    def test_v2_identity_is_available_without_config_runtime_state(
        self,
    ) -> None:
        from product_identity import (
            APP_BRAND,
            APP_NAME_EN,
            APP_NAME_ZH,
            APP_VERSION,
            APP_VERSION_LABEL,
            PRODUCT_NAME_EN,
            PRODUCT_NAME_ZH,
        )

        self.assertEqual(APP_BRAND, "Leon AI")
        self.assertEqual(APP_NAME_ZH, "AI商务邮件工作台")
        self.assertEqual(APP_NAME_EN, "AI Business Email Workspace")
        self.assertEqual(APP_VERSION, "2.1")
        self.assertEqual(APP_VERSION_LABEL, "V2.1 Development")
        self.assertEqual(PRODUCT_NAME_ZH, APP_NAME_ZH)
        self.assertEqual(PRODUCT_NAME_EN, APP_NAME_EN)


if __name__ == "__main__":
    unittest.main()
