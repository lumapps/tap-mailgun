import typing as t
from importlib import resources


from tap_mailgun.client import MailgunStream

SCHEMAS_DIR = resources.files(__package__) / "schemas"

class MailgunMetricsStream(MailgunStream):
    name = "analytics_metrics"
    path = "/v1/analytics/metrics?limit=300"
    primary_keys = ["time_value"]  # Based on transformed record
    replication_key = "time_value" # Based on transformed record
    schema_filepath = SCHEMAS_DIR / "analytics_metrics.json"
    rest_method = "POST"


class MailgunUsageMetricsStream(MailgunStream):
    name = "analytics_usage_metrics"
    path = "/v1/analytics/usage/metrics?limit=300"
    primary_keys = ["time_value"]
    replication_key = "time_value"
    schema_filepath = SCHEMAS_DIR / "analytics_usage_metrics.json"
    rest_method = "POST"
