from singer_sdk import Tap
from singer_sdk.typing import (
    PropertiesList,
    Property,
    StringType,
    ArrayType,
    BooleanType,
    ObjectType,
)

from tap_mailgun import streams

class TapMailgun(Tap):
    """Mailgun tap class."""
    name = "tap-mailgun"

    config_jsonschema = PropertiesList(
        Property("api_key", StringType, required=True),
        Property("base_url", StringType, required=True),
        Property("start_date", StringType, required=False),
        Property("end_date", StringType, required=False),
        Property("analytics_resolution", StringType, required=True),
        Property("analytics_duration", StringType, required=False),
        Property("analytics_dimensions", ArrayType(wrapped_type=StringType), required=True),
        Property("analytics_metrics", ArrayType(wrapped_type=StringType), required=True),
        Property(
            "analytics_filters",
            ArrayType(ObjectType(
                Property("attribute", StringType, required=True),
                Property("comparator", StringType, required=True),
                Property("value", StringType, required=True),
                additional_properties=False,
            )),
            required=True
        ),
        Property("analytics_include_subaccounts", BooleanType, required=True),
        Property("analytics_include_aggregates", BooleanType, required=True)
    ).to_dict()

    def discover_streams(self) -> list:
        """Return a list of discovered streams."""
        return [
            streams.MailgunMetricsStream(self)
        ]

if __name__ == "__main__":
    TapMailgun.cli()
