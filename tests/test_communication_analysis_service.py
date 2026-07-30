import unittest

from communication_analysis_service import (
    ANALYSIS_UNAVAILABLE,
    parse_communication_analysis,
)


class CommunicationAnalysisTests(unittest.TestCase):
    def test_complete_analysis_is_parsed(self) -> None:
        result = parse_communication_analysis(
            {
                "purpose": "良好：目的清晰",
                "action_required": "明确",
                "deadline": "未提供",
                "tone": "正式且适当",
                "commitment_risk": "未发现明显风险",
                "ambiguity_risk": "建议检查一个代词",
                "localization_note": "核对正式称谓",
                "improvement_suggestions": ["增加回复期限"],
            }
        )
        self.assertTrue(result.available)
        self.assertEqual(result.deadline, "未提供")
        self.assertEqual(result.improvement_suggestions, ("增加回复期限",))

    def test_missing_analysis_uses_safe_fallback(self) -> None:
        result = parse_communication_analysis(None)
        self.assertFalse(result.available)
        self.assertEqual(result.purpose, ANALYSIS_UNAVAILABLE)


if __name__ == "__main__":
    unittest.main()
