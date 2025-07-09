import unittest
from unittest.mock import MagicMock, patch
from tap_mailgun.streams import MailgunUsageMetricsStream
from tap_mailgun.tap import TapMailgun

class TestMailgunUsageMetricsStream(unittest.TestCase):
    def setUp(self):
        self.config = {
            "api_key": "test_api_key",
            "base_url": "https://api.mailgun.net",
            "start_date": "2023-01-01T00:00:00Z",
            "end_date": "2023-01-02T00:00:00Z",
            "analytics_resolution": "day",
            "analytics_dimensions": ["time"],
            "analytics_metrics": ["delivered_count"],
            "analytics_usage_metrics": ["processed_count"],
            "analytics_filters": [],
            "analytics_include_subaccounts": False,
            "analytics_include_aggregates": False
        }
        self.tap = TapMailgun(config=self.config)
        self.stream = MailgunUsageMetricsStream(tap=self.tap)

    def test_prepare_request_payload(self):
        context = {}
        next_page_token = None
        payload = self.stream.prepare_request_payload(context, next_page_token)
        self.assertEqual(payload["metrics"], ["processed_count"])

if __name__ == "__main__":
    unittest.main()