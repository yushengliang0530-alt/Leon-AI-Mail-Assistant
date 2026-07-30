import unittest

from localization_service import (
    COUNTRY_REGION_OPTIONS,
    build_localization_guidance,
)


class LocalizationServiceTests(unittest.TestCase):
    def test_country_region_options_are_complete(self) -> None:
        self.assertEqual(COUNTRY_REGION_OPTIONS[0], "未指定 / Not Specified")
        self.assertIn("印度尼西亚 / Indonesia", COUNTRY_REGION_OPTIONS)
        self.assertIn("马来西亚 / Malaysia", COUNTRY_REGION_OPTIONS)
        self.assertEqual(len(COUNTRY_REGION_OPTIONS), 11)

    def test_unspecified_region_is_safe(self) -> None:
        result = build_localization_guidance(
            recipient="Alex Tan",
            country_region="未指定 / Not Specified",
            tone="Formal",
        )
        self.assertIn("Dear Alex Tan", result.recommended_salutation)
        self.assertIn("不要自动添加", result.salutation_risk)

    def test_indonesia_guidance_does_not_add_title(self) -> None:
        result = build_localization_guidance(
            recipient="Alex Tan",
            country_region="印度尼西亚 / Indonesia",
            tone="Formal",
        )
        self.assertIn("不要未经确认自动添加", result.cross_cultural_note)
        self.assertNotIn("Mr. Alex", result.recommended_salutation)
        self.assertNotIn("Ms. Alex", result.recommended_salutation)

    def test_indonesia_existing_pak_is_recognized(self) -> None:
        result = build_localization_guidance(
            recipient="Pak Budi",
            country_region="印度尼西亚 / Indonesia",
            tone="Formal",
        )
        self.assertIn("检测到 Pak 或 Bu", result.cross_cultural_note)

    def test_malaysia_formal_title_is_preserved(self) -> None:
        result = build_localization_guidance(
            recipient="Datuk Amir",
            country_region="马来西亚 / Malaysia",
            tone="Executive",
        )
        self.assertIn("准确保留", result.cross_cultural_note)


if __name__ == "__main__":
    unittest.main()
