import unittest

from content_risk_service import analyze_content_risk


class ContentRiskServiceTests(unittest.TestCase):
    def test_risk_analysis_does_not_log_full_input(self) -> None:
        sensitive_input = "password: unique-never-log-this-value-78421"
        with self.assertNoLogs(level="DEBUG"):
            analyze_content_risk(sensitive_input)

    def test_api_key_and_token_are_high_risk(self) -> None:
        assessment = analyze_content_risk(
            "API Key: sk-testplaceholder123456 and access_token=tokenvalue123"
        )
        self.assertEqual(assessment.risk_level, "high")
        self.assertTrue(assessment.requires_confirmation)
        rendered = repr(assessment)
        self.assertNotIn("sk-testplaceholder123456", rendered)
        self.assertNotIn("tokenvalue123", rendered)

    def test_long_number_is_masked(self) -> None:
        assessment = analyze_content_risk("Account number: 1234567890123456")
        self.assertEqual(assessment.risk_level, "high")
        self.assertNotIn("1234567890123456", repr(assessment))
        self.assertIn("****", repr(assessment))

    def test_normal_business_content_is_not_high_risk(self) -> None:
        assessment = analyze_content_risk(
            "Please invite the project team to a coordination meeting next Tuesday."
        )
        self.assertEqual(assessment.risk_level, "low")
        self.assertFalse(assessment.requires_confirmation)


if __name__ == "__main__":
    unittest.main()
