import time
import requests
from typing import Any
from src.config import (
    AIRTABLE_API_KEY,
    AIRTABLE_BASE_ID,
    AIRTABLE_RATE_LIMIT,
    BATCH_SIZE
)
from src.utils import get_logger

logger = get_logger(__name__)


class AirtableClient:
    """Client for interacting with Airtable API."""

    BASE_URL = "https://api.airtable.com/v0"

    def __init__(self, api_key: str = None, base_id: str = None):
        self.api_key = api_key or AIRTABLE_API_KEY
        self.base_id = base_id or AIRTABLE_BASE_ID
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self._last_request_time = 0

    def _rate_limit(self):
        """Enforce rate limiting."""
        elapsed = time.time() - self._last_request_time
        min_interval = 1.0 / AIRTABLE_RATE_LIMIT
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        self._last_request_time = time.time()

    def _make_request(self, method: str, endpoint: str, data: dict = None, retries: int = 3) -> dict:
        """Make an API request with retry logic."""
        url = f"{self.BASE_URL}/{self.base_id}/{endpoint}"

        for attempt in range(retries):
            self._rate_limit()
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=data
                )
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise

    def get_records(self, table_name: str, filter_formula: str = None) -> list[dict]:
        """Fetch all records from a table."""
        records = []
        offset = None

        while True:
            params = []
            if filter_formula:
                params.append(f"filterByFormula={requests.utils.quote(filter_formula)}")
            if offset:
                params.append(f"offset={offset}")

            endpoint = table_name
            if params:
                endpoint += "?" + "&".join(params)

            result = self._make_request("GET", endpoint)
            records.extend(result.get("records", []))

            offset = result.get("offset")
            if not offset:
                break

        logger.info(f"Fetched {len(records)} records from {table_name}")
        return records

    def get_record(self, table_name: str, record_id: str) -> dict:
        """Fetch a single record by ID."""
        endpoint = f"{table_name}/{record_id}"
        return self._make_request("GET", endpoint)

    def create_record(self, table_name: str, fields: dict) -> dict:
        """Create a new record."""
        data = {"fields": fields}
        result = self._make_request("POST", table_name, data)
        logger.info(f"Created record in {table_name}: {result.get('id')}")
        return result

    def update_record(self, table_name: str, record_id: str, fields: dict) -> dict:
        """Update an existing record."""
        endpoint = f"{table_name}/{record_id}"
        data = {"fields": fields}
        result = self._make_request("PATCH", endpoint, data)
        logger.info(f"Updated record {record_id} in {table_name}")
        return result

    def delete_record(self, table_name: str, record_id: str) -> dict:
        """Delete a record."""
        endpoint = f"{table_name}/{record_id}"
        result = self._make_request("DELETE", endpoint)
        logger.info(f"Deleted record {record_id} from {table_name}")
        return result

    def batch_create(self, table_name: str, records: list[dict]) -> list[dict]:
        """Create multiple records in batches."""
        results = []
        for i in range(0, len(records), BATCH_SIZE):
            batch = records[i:i + BATCH_SIZE]
            data = {"records": [{"fields": r} for r in batch]}
            result = self._make_request("POST", table_name, data)
            results.extend(result.get("records", []))
        return results

    def batch_update(self, table_name: str, records: list[dict]) -> list[dict]:
        """Update multiple records in batches."""
        results = []
        for i in range(0, len(records), BATCH_SIZE):
            batch = records[i:i + BATCH_SIZE]
            data = {"records": batch}
            result = self._make_request("PATCH", table_name, data)
            results.extend(result.get("records", []))
        return results

    def get_linked_records(self, parent_id: str, child_table: str, link_field: str = "Applicant ID") -> list[dict]:
        """Fetch all child records linked to a parent."""
        filter_formula = f"FIND('{parent_id}', ARRAYJOIN({{{link_field}}}))"
        return self.get_records(child_table, filter_formula)