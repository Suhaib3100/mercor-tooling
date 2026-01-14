"""
Compression Pipeline - Gather data from linked tables and create canonical JSON per applicant.
"""
import json
from src.airtable_client import AirtableClient
from src.config import (
    TABLE_APPLICANTS,
    TABLE_PERSONAL,
    TABLE_EXPERIENCE,
    TABLE_SALARY
)
from src.utils import get_logger

logger = get_logger(__name__)


def fetch_applicant_data(client: AirtableClient, applicant_id: str, applicant_record_id: str) -> dict:
    """Fetch all related data for one applicant."""
    data = {
        "applicant_id": applicant_id,
        "record_id": applicant_record_id,
        "personal": {},
        "experience": [],
        "salary": {}
    }

    # Fetch Personal Details
    personal_records = client.get_linked_records(applicant_record_id, TABLE_PERSONAL)
    if personal_records:
        fields = personal_records[0].get("fields", {})
        data["personal"] = {
            "name": fields.get("Full Name", ""),
            "email": fields.get("Email", ""),
            "location": fields.get("Location", ""),
            "linkedin": fields.get("LinkedIn", "")
        }

    # Fetch Work Experience
    experience_records = client.get_linked_records(applicant_record_id, TABLE_EXPERIENCE)
    for record in experience_records:
        fields = record.get("fields", {})
        data["experience"].append({
            "record_id": record.get("id"),
            "company": fields.get("Company", ""),
            "title": fields.get("Title", ""),
            "start": fields.get("Start", ""),
            "end": fields.get("End", ""),
            "technologies": fields.get("Technologies", [])
        })

    # Fetch Salary Preferences
    salary_records = client.get_linked_records(applicant_record_id, TABLE_SALARY)
    if salary_records:
        fields = salary_records[0].get("fields", {})
        data["salary"] = {
            "preferred_rate": fields.get("Preferred Rate", 0),
            "minimum_rate": fields.get("Minimum Rate", 0),
            "currency": fields.get("Currency", "USD"),
            "availability": fields.get("Availability", 0)
        }

    return data


def build_json_object(applicant_data: dict) -> str:
    """Convert applicant data to JSON string."""
    return json.dumps(applicant_data, indent=2)


def compress_single_applicant(client: AirtableClient, applicant_record: dict) -> bool:
    """Compress data for a single applicant."""
    record_id = applicant_record.get("id")
    fields = applicant_record.get("fields", {})
    applicant_id = fields.get("Applicant ID")

    if not applicant_id:
        logger.warning(f"Record {record_id} has no Applicant ID, skipping")
        return False

    try:
        # Fetch all related data
        data = fetch_applicant_data(client, applicant_id, record_id)

        # Build JSON
        json_string = build_json_object(data)

        # Update Applicants table with Compressed JSON
        client.update_record(TABLE_APPLICANTS, record_id, {
            "Compressed JSON": json_string
        })

        logger.info(f"Compressed applicant {applicant_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to compress applicant {applicant_id}: {e}")
        return False


def compress_all_applicants():
    """Main function: compress all applicants in batch."""
    client = AirtableClient()

    # Fetch all applicants
    applicants = client.get_records(TABLE_APPLICANTS)
    logger.info(f"Found {len(applicants)} applicants to compress")

    success_count = 0
    failure_count = 0

    for applicant in applicants:
        if compress_single_applicant(client, applicant):
            success_count += 1
        else:
            failure_count += 1

    logger.info(f"Compression complete: {success_count} succeeded, {failure_count} failed")
    return success_count, failure_count


if __name__ == "__main__":
    compress_all_applicants()
