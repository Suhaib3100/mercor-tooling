"""
Decompression Pipeline - Read Compressed JSON and upsert child table records.
"""
import json
from src.airtable_client import AirtableClient
from src.config import (
    TABLE_APPLICANTS,
    TABLE_PERSONAL,
    TABLE_EXPERIENCE,
    TABLE_SALARY
)
from src.utils import get_logger, validate_json_structure

logger = get_logger(__name__)


def parse_compressed_json(json_string: str) -> dict | None:
    """Parse and validate JSON structure."""
    if not json_string:
        return None

    try:
        data = json.loads(json_string)
        is_valid, errors = validate_json_structure(data)
        if not is_valid:
            logger.warning(f"JSON validation errors: {errors}")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        return None


def upsert_personal_details(client: AirtableClient, applicant_record_id: str, personal_data: dict) -> bool:
    """Create or update Personal Details record."""
    try:
        existing = client.get_linked_records(applicant_record_id, TABLE_PERSONAL)

        fields = {
            "Full Name": personal_data.get("name", ""),
            "Email": personal_data.get("email", ""),
            "Location": personal_data.get("location", ""),
            "LinkedIn": personal_data.get("linkedin", ""),
            "Application ID": [applicant_record_id]
        }

        if existing:
            # Update existing record
            client.update_record(TABLE_PERSONAL, existing[0]["id"], fields)
            logger.info(f"Updated Personal Details for {applicant_record_id}")
        else:
            # Create new record
            client.create_record(TABLE_PERSONAL, fields)
            logger.info(f"Created Personal Details for {applicant_record_id}")

        return True
    except Exception as e:
        logger.error(f"Failed to upsert Personal Details: {e}")
        return False


def upsert_work_experience(client: AirtableClient, applicant_record_id: str, experience_list: list) -> bool:
    """Sync Work Experience records (create/update/delete)."""
    try:
        existing = client.get_linked_records(applicant_record_id, TABLE_EXPERIENCE)
        existing_map = {r["id"]: r for r in existing}

        processed_ids = set()

        for exp in experience_list:
            fields = {
                "Company": exp.get("company", ""),
                "Title": exp.get("title", ""),
                "Start": exp.get("start", ""),
                "End": exp.get("end", ""),
                "Technologies": exp.get("technologies", []),
                "Application ID": [applicant_record_id]
            }

            # Try to match by record_id if available
            record_id = exp.get("record_id")
            if record_id and record_id in existing_map:
                client.update_record(TABLE_EXPERIENCE, record_id, fields)
                processed_ids.add(record_id)
                logger.info(f"Updated Work Experience {record_id}")
            else:
                # Try to match by company + title + start
                matched = False
                for existing_id, existing_record in existing_map.items():
                    if existing_id in processed_ids:
                        continue
                    ef = existing_record.get("fields", {})
                    if (ef.get("Company") == fields["Company"] and
                        ef.get("Title") == fields["Title"] and
                        ef.get("Start") == fields["Start"]):
                        client.update_record(TABLE_EXPERIENCE, existing_id, fields)
                        processed_ids.add(existing_id)
                        matched = True
                        logger.info(f"Updated Work Experience {existing_id} (matched)")
                        break

                if not matched:
                    result = client.create_record(TABLE_EXPERIENCE, fields)
                    logger.info(f"Created Work Experience {result.get('id')}")

        # Delete orphan records
        for existing_id in existing_map:
            if existing_id not in processed_ids:
                client.delete_record(TABLE_EXPERIENCE, existing_id)
                logger.info(f"Deleted orphan Work Experience {existing_id}")

        return True
    except Exception as e:
        logger.error(f"Failed to upsert Work Experience: {e}")
        return False


def upsert_salary_preferences(client: AirtableClient, applicant_record_id: str, salary_data: dict) -> bool:
    """Create or update Salary Preferences record."""
    try:
        existing = client.get_linked_records(applicant_record_id, TABLE_SALARY)

        fields = {
            "Preferred Rate": salary_data.get("preferred_rate", 0),
            "Minimum Rate": salary_data.get("minimum_rate", 0),
            "Currency": salary_data.get("currency", "USD"),
            "Availability": salary_data.get("availability", 0),
            "Application ID": [applicant_record_id]
        }

        if existing:
            client.update_record(TABLE_SALARY, existing[0]["id"], fields)
            logger.info(f"Updated Salary Preferences for {applicant_record_id}")
        else:
            client.create_record(TABLE_SALARY, fields)
            logger.info(f"Created Salary Preferences for {applicant_record_id}")

        return True
    except Exception as e:
        logger.error(f"Failed to upsert Salary Preferences: {e}")
        return False


def decompress_applicant(client: AirtableClient, applicant_record: dict) -> bool:
    """Decompress one applicant's JSON to child tables."""
    record_id = applicant_record.get("id")
    fields = applicant_record.get("fields", {})
    json_string = fields.get("Compressed JSON")

    if not json_string:
        logger.warning(f"Record {record_id} has no Compressed JSON, skipping")
        return False

    data = parse_compressed_json(json_string)
    if not data:
        return False

    success = True
    success = upsert_personal_details(client, record_id, data.get("personal", {})) and success
    success = upsert_work_experience(client, record_id, data.get("experience", [])) and success
    success = upsert_salary_preferences(client, record_id, data.get("salary", {})) and success

    return success


def decompress_all():
    """Decompress all applicants with valid JSON."""
    client = AirtableClient()

    applicants = client.get_records(TABLE_APPLICANTS)
    logger.info(f"Found {len(applicants)} applicants to decompress")

    success_count = 0
    failure_count = 0

    for applicant in applicants:
        if decompress_applicant(client, applicant):
            success_count += 1
        else:
            failure_count += 1

    logger.info(f"Decompression complete: {success_count} succeeded, {failure_count} failed")
    return success_count, failure_count


if __name__ == "__main__":
    decompress_all()
