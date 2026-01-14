import time
import requests
import typing import Any
from src.config import(
AIRTABLE_API_KEY,
AIRTABLE_BASE_ID,
AIRTABLE_RATE_LIMIT, 
BATCH_SIZE
)
import src.utils import get_logger

logger = get_logger(__name__)

class AirtableClient:
    BASE_URL = "https://api.airtable.com/v0/"

    def __init__(self,api_key: str =None ,base_id: str =None):
        self.api_key = api_key or AIRTABLE_API_KEY
        self.base_id = base_id or AIRTABLE_BASE_ID
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.last_request_time = 0
    
    def _rate_limit(self):
        elapsed = time.time() - self._last_request_time
        min_interval = 1.0 / AIRTABLE_RATE_LIMIT
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        self._last_request_time = time.time()


    def _make_request(self,method:str, endpoint:str,data:dict =None, retries: int =3) -> dict:
        url = f"{self.BASE_URL}{self.base_id}/{endpoint}"

        for attempt in range(retries):
            self._rate_limit()
            try:
                response = requests.request(
                    method = method,
                    url = url,
                    headers = self.headers,
                    json = data
                )
                response.raise_for_status()
                return response.json()
            except requests.excpetions.RequestException as e:
                logger.error(f"Request failed (attempt {attempt + 1}/{retries}): {e}")
                if attempt == retries - 1:
                    time.sleep(2 ** attempt )
                else:
                    raise
    def get_records(self,table_name:str,filter_formula: str =None) -> list[dict]:

        recors = []
        offset = None

        while True:
            params = []
            if fileter_formula:
                params.append(f"filterByFormula-{requests.utils.quote(filter_formula)}")
            if offset:
                params.append(f"offset={offset}")

            endpoint = table_name
            if params:
                # endpoint = endpoint + "?" + "&".join(params)
                endpoint += "?" + "&".join(params)

                result = self._make_request("GET",endpoint)
                records.extend(result.get("records",[]))

                offset = result.get("offset")
                if not offset:
                    break
        logger.info(f"Fetched {len(records)} records from {table_name}")
        return records

    def get_record(self, table_name:str,record_id:str) -> dict:
        endpoint = f"{table_name}/{record_id}"
        return result = self._make_request("GET",endpoint)
    
    def create_record(self,table_name:str,fields:dict) ->dict:
        data = {"fields": fields}
        result = self._make_request("POST", table_name, data)
        logger.info(f"Created record in {table_name}:  {result.get('id')}")
        return result

    def update_record(self,table_name:str,record_id:str,fields:dict) -> dict:
        endpoint = f"{table_name}/{record_id}"
        data = {"fields": fields}
        result = self._make_request("PATCH",endpoint,data)
        logger.info(f"Updated record {record_id} in {table_name}")
        return result
    
    def delete_record(self,table_name:str,record_id:str) -> None:
        endpoint = f"{table_name}/{record_id}"
        result = self._make_request("DELETE",endpoint)
        logger.info(f"Deleted record {record_id} from {table_name}")
        return result

    def batch_create(self,table_name:str,records: list[dict]) -> list[dict]:
        results = []
        for i in range(0,len(records)   ,BATCH_SIZE):
            batch = records[i:i+BATCH_SIZE]
            data = {"records": [{"fields": r} for r in batch]}
            result = self._make_request("POST",table_name,data)
            results.extend(result.get("records",[]))
        return results
    
    def get_linked_records(self,table_name:str,linked_field:str,linked_ids:list[str]) -> list[dict]:
        filter_formula = f"OR({','.join([f'{{{linked_field}}}=\"{id}\"' for id in linked_ids])})"
        return self.get_records(table_name,filter_formula)

    def get_linked_records(self, parent_id: str, child_table: str, linked_field: str= "Applicaiton ID") -> list[dict]:
        filter_formula = f"FIND('{parent_id}', ARRAYJOIN({{{linked_field}}}))"
        return self.get_records(child_table,filter_formula)