"""REST client handling, including MailgunStream base class."""

from __future__ import annotations

from importlib import resources
from requests import Response
from typing import Any, Optional, Any, Dict, Iterable

from singer_sdk.authenticators import BasicAuthenticator
from singer_sdk.streams import RESTStream

SCHEMAS_DIR = resources.files(__package__) / "schemas"


class MailgunStream(RESTStream):
    """Mailgun stream class."""

    @property
    def url_base(self) -> str:
        """Return the API URL root, configurable via tap settings."""
        return self.config.get("base_url", "https://api.mailgun.net")


    @property
    def authenticator(self) -> BasicAuthenticator:
        """Return a basic authenticator."""
        return BasicAuthenticator(
            stream=self,
            username="api",
            password=self.config.get("api_key")
        )

    def prepare_request_payload(
        self, context: Optional[dict], next_page_token: Optional[Any]
    ) -> Optional[dict]:
        """Prepare the data payload for the API request.

        Args:
            context: Stream partition or context dictionary.
            next_page_token: Token for the next page of results.

        Returns:
            A dictionary with the body payload, or None if no data needs to be sent.
        """
        payload: dict = {}
        payload["start"] = self.config.get("start_date")
        payload["end"] = self.config.get("end_date")
        payload["resolution"] = self.config.get("analytics_resolution")
        
        if self.config.get("analytics_duration"):
            payload["duration"] = self.config.get("analytics_duration")
            # Note: If 'duration' is provided, Mailgun API calculates 'start' based on 'end' and 'duration'.
            # The tap does not need to pre-calculate 'start' in this case.

        payload["dimensions"] = self.config.get("analytics_dimensions")
        payload["metrics"] = self.config.get("analytics_metrics")
        payload["filter"] = self.config.get("analytics_filters")
        payload["include_subaccounts"] = self.config.get("analytics_include_subaccounts")
        payload["include_aggregates"] = self.config.get("analytics_include_aggregates")
        
        # Pagination handling
        pagination = {
            "skip": next_page_token if next_page_token is not None else 0,
            "limit": 300,  # Default limit, can be adjusted
        }
        payload["pagination"] = pagination
        return payload

    def get_next_page_token(
        self, response: Response, previous_token: t.Optional[t.Any]
    ) -> t.Optional[t.Any]:
        """Return a token for identifying next page or None if no more pages."""
        data = response.json()
        pagination_info = data.get("pagination", {})
        current_skip = pagination_info.get("skip", 0)
        limit = pagination_info.get("limit", 0) # Use the limit from the response
        total = pagination_info.get("total", 0)

        if (current_skip + limit) < total:
            return current_skip + limit
        return None

    def parse_response(self, response: Response) -> Iterable[dict]:
        """Parse the response and extract records."""
        data = response.json()
        yield from data.get("items", [])

    def post_process(self, row: dict, context: Optional[dict] = None) -> Optional[dict]:
        """Transform raw data in each record.
        
        Flattens dimensions and metrics into a single record.
        Extracts 'time_value' from the 'time' dimension for replication.
        """
        processed_record: Dict[str, Any] = {}
        time_dim_value: Optional[str] = None

        # Extract dimensions
        for dim_obj in row.get("dimensions", []):
            dim_name = dim_obj.get("dimension")
            dim_value = dim_obj.get("value")
            if dim_name:
                processed_record[str(dim_name)] = dim_value
                if dim_name == "time":
                    time_dim_value = dim_value
        
        if time_dim_value:
            processed_record["time_value"] = time_dim_value
        else:
            # If 'time' dimension is crucial for replication and is missing,
            # it might be an issue. For now, we log a warning.
            # Ensure 'time' is always requested in 'analytics_dimensions' config.
            self.logger.warning(
                f"Record missing 'time' dimension or its value, "
                f"which is used for replication_key 'time_value'. Record: {row}"
            )
            # Depending on requirements, could return None to skip record or raise an error.

        # Extract metrics
        metrics_data = row.get("metrics", {})
        for metric_name, metric_value in metrics_data.items():
            processed_record[str(metric_name)] = metric_value
        
        return processed_record
