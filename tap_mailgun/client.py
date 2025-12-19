"""REST client handling, including MailgunStream base class."""

from __future__ import annotations

from datetime import datetime
from email.utils import formatdate
from importlib import resources
from typing import Any, Optional, Any, Dict, Iterable

from requests import Response
from singer_sdk.authenticators import BasicAuthenticator
from singer_sdk.streams import RESTStream

SCHEMAS_DIR = resources.files(__package__) / "schemas"


class MailgunStream(RESTStream):
    """Mailgun stream class."""

    @property
    def url_base(self) -> str:
        """Return the API URL root, configurable via tap settings."""
        return self.config.get("base_url", "https://api.mailgun.net")

    def _format_datetime_to_rfc2822(self, date_str: str) -> str:
        """Convert ISO format to RFC 2822 format required by Mailgun API.
        
        Args:
            date_str: Date string in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
            
        Returns:
            RFC 2822 formatted date string
        """
        if not date_str:
            return date_str
            
        try:
            # Parse ISO format datetime
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            
            # Convert to RFC 2822 format
            return formatdate(dt.timestamp(), usegmt=True)
                
        except (ValueError, TypeError) as e:
            # If parsing fails, log error and return original string
            self.logger.error(f"Could not parse ISO date format: {date_str}, error: {e}")
            raise ValueError(f"Invalid ISO date format: {date_str}. Expected format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS")


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
        
        # Format dates to RFC 2822 format required by Mailgun API
        start_date = self.config.get("start_date")
        end_date = self.config.get("end_date")
        
        if start_date:
            payload["start"] = self._format_datetime_to_rfc2822(start_date)
        if end_date:
            payload["end"] = self._format_datetime_to_rfc2822(end_date)
        payload["resolution"] = self.config.get("analytics_resolution")
        
        if self.config.get("analytics_duration"):
            payload["duration"] = self.config.get("analytics_duration")
            # Note: If 'duration' is provided, Mailgun API calculates 'start' based on 'end' and 'duration'.
            # The tap does not need to pre-calculate 'start' in this case.

        payload["dimensions"] = self.config.get("analytics_dimensions")
        if self.name == "analytics_usage_metrics":
            payload["metrics"] = self.config.get("analytics_usage_metrics")
        else:
            payload["metrics"] = self.config.get("analytics_metrics")
        
        # Transform analytics_filters to the correct Mailgun API format
        # Only apply filters to regular analytics metrics, not usage metrics
        if self.name != "analytics_usage_metrics":
            analytics_filters = self.config.get("analytics_filters", [])
            if analytics_filters:
                filter_conditions = []
                for filter_item in analytics_filters:
                    filter_condition = {
                        "attribute": filter_item.get("attribute"),
                        "comparator": filter_item.get("comparator"),
                        "values": [
                            {
                                "label": filter_item.get("value"),
                                "value": filter_item.get("value")
                            }
                        ]
                    }
                    filter_conditions.append(filter_condition)
                payload["filter"] = {"AND": filter_conditions}
        
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
        items = data.get("items", [])
        
        yield from items

    def post_process(self, row: dict, context: Optional[dict] = None) -> Optional[dict]:
        """Transform raw data in each record.
        
        Flattens dimensions and metrics into a single record.
        Extracts 'time_value' from the 'time' dimension for replication.
        """
        processed_record: Dict[str, Any] = {}
        time_dim_value: Optional[str] = None

        # Extract dimensions
        dimensions = row.get("dimensions", [])
        
        for dim_obj in dimensions:
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
