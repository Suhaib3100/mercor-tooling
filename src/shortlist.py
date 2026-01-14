"""
Lead Shortlist Automation - Evaluate candidates based on multi-factor rules.
"""
import json
from datetime import datetime
from src.airtable_client import AirtableClient
from src.config import (
    TABLE_APPLICANTS,
    TABLE_SHORTLISTED,
    TIER_1_COMPANIES,
    MIN_EXPERIENCE_YEARS,
    MAX_PREFERRED_RATE,
    MIN_AVAILABILITY_HOURS,
    APPROVED_LOCATIONS
)
from src.utils import get_logger, calculate_years_between, normalize_location

logger = get_logger(__name__)


def calculate_total_experience(experience_list: list) -> float:
    """Calculate total years from experience entries."""
    total_years = 0.0

    for exp in experience_list:
        start = exp.get("start")
        end = exp.get("end")
        years = calculate_years_between(start, end)
        total_years += years

    return round(total_years, 2)


def worked_at_tier1(experience_list: list) -> tuple[bool, str | None]:
    """Check if any company is in Tier-1 list."""
    for exp in experience_list:
        company = exp.get("company", "").strip()
        for tier1 in TIER_1_COMPANIES:
            if tier1.lower() in company.lower():
                return True, company
    return False, None


def meets_experience_criteria(experience_list: list) -> tuple[bool, list[str]]:
    """Evaluate experience criterion."""
    reasons = []

    total_years = calculate_total_experience(experience_list)
    has_min_experience = total_years >= MIN_EXPERIENCE_YEARS

    if has_min_experience:
        reasons.append(f"{total_years} years total experience (exceeds {MIN_EXPERIENCE_YEARS}-year minimum)")

    is_tier1, company = worked_at_tier1(experience_list)
    if is_tier1:
        reasons.append(f"Worked at {company} (Tier-1 company)")

    passed = has_min_experience or is_tier1
    return passed, reasons


def meets_compensation_criteria(salary_data: dict) -> tuple[bool, list[str]]:
    """Evaluate rate and availability."""
    reasons = []

    preferred_rate = salary_data.get("preferred_rate", 0)
    availability = salary_data.get("availability", 0)
    currency = salary_data.get("currency", "USD")

    # Check rate (assumes USD for simplicity)
    rate_ok = preferred_rate <= MAX_PREFERRED_RATE and preferred_rate > 0
    availability_ok = availability >= MIN_AVAILABILITY_HOURS

    if rate_ok:
        reasons.append(f"Preferred rate: ${preferred_rate}/hour {currency} (under ${MAX_PREFERRED_RATE} threshold)")

    if availability_ok:
        reasons.append(f"Availability: {availability} hours/week (exceeds {MIN_AVAILABILITY_HOURS}-hour minimum)")

    passed = rate_ok and availability_ok
    return passed, reasons


def meets_location_criteria(personal_data: dict) -> tuple[bool, list[str]]:
    """Normalize and check location."""
    reasons = []

    location = personal_data.get("location", "")
    country = normalize_location(location)

    if country and country in APPROVED_LOCATIONS:
        reasons.append(f"Location: {location} (approved location)")
        return True, reasons

    return False, reasons


def evaluate_applicant(applicant_json: dict) -> tuple[bool, list[str]]:
    """Run all criteria checks, return (passed, reasons)."""
    all_reasons = []

    # Experience criteria
    exp_passed, exp_reasons = meets_experience_criteria(applicant_json.get("experience", []))
    all_reasons.extend(exp_reasons)

    # Compensation criteria
    comp_passed, comp_reasons = meets_compensation_criteria(applicant_json.get("salary", {}))
    all_reasons.extend(comp_reasons)

    # Location criteria
    loc_passed, loc_reasons = meets_location_criteria(applicant_json.get("personal", {}))
    all_reasons.extend(loc_reasons)

    # All criteria must be met
    passed = exp_passed and comp_passed and loc_passed

    return passed, all_reasons


def create_shortlisted_lead(client: AirtableClient, applicant_record_id: str, json_data: dict, reasons: list) -> bool:
    """Create Shortlisted Leads record."""
    try:
        # Check if already shortlisted
        existing = client.get_linked_records(applicant_record_id, TABLE_SHORTLISTED, "Applicants")
        if existing:
            logger.info(f"Applicant {applicant_record_id} already shortlisted, skipping")
            return True

        fields = {
            "Applicants": [applicant_record_id],
            "Compressed JSON": json.dumps(json_data, indent=2),
            "Score Reason": "\n".join(f"- {r}" for r in reasons)
        }

        client.create_record(TABLE_SHORTLISTED, fields)

        # Update shortlist status on Applicants table
        client.update_record(TABLE_APPLICANTS, applicant_record_id, {
            "Shortlist Status": "Shortlisted"
        })

        logger.info(f"Created Shortlisted Lead for {applicant_record_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to create Shortlisted Lead: {e}")
        return False


def shortlist_applicant(client: AirtableClient, applicant_record: dict) -> bool:
    """Evaluate and shortlist a single applicant."""
    record_id = applicant_record.get("id")
    fields = applicant_record.get("fields", {})
    json_string = fields.get("Compressed JSON")

    if not json_string:
        logger.warning(f"Record {record_id} has no Compressed JSON, skipping")
        return False

    try:
        json_data = json.loads(json_string)
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON for record {record_id}")
        return False

    passed, reasons = evaluate_applicant(json_data)

    if passed:
        return create_shortlisted_lead(client, record_id, json_data, reasons)
    else:
        # Update status to Rejected
        client.update_record(TABLE_APPLICANTS, record_id, {
            "Shortlist Status": "Rejected"
        })
        logger.info(f"Applicant {record_id} did not meet criteria")
        return False


def shortlist_all_applicants():
    """Main function: evaluate all applicants."""
    client = AirtableClient()

    # Fetch applicants with Compressed JSON
    applicants = client.get_records(TABLE_APPLICANTS)
    logger.info(f"Found {len(applicants)} applicants to evaluate")

    shortlisted_count = 0
    rejected_count = 0

    for applicant in applicants:
        if shortlist_applicant(client, applicant):
            shortlisted_count += 1
        else:
            rejected_count += 1

    logger.info(f"Shortlist complete: {shortlisted_count} shortlisted, {rejected_count} rejected/skipped")
    return shortlisted_count, rejected_count


if __name__ == "__main__":
    shortlist_all_applicants()
