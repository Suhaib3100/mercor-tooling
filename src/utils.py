import os
import logging
from datetime import datetime
from dateutil import parser as date_parser

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# Basic logic for logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "app.log")),
        logging.StreamHandler()
    ]
)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def parse_date(date_string: str) -> datetime | None:
    if not date_string:
        return None
    try:
        return date_parser.parse(date_string)
    except (ValueError, TypeError):
        return None


def calculate_years_between(start_date: str, end_date: str = None) -> float:
    start = parse_date(start_date)
    if not start:
        return 0.0
    end = parse_date(end_date) if end_date else datetime.now()
    delta = end - start
    return round(delta.days / 365.25, 2)


def normalize_location(location: str) -> str | None:
    if not location:
        return None
    location = location.strip().upper()

    country_mappings = {
        "US": "USA",
        "UNITED STATES": "USA",
        "UK": "UNITED KINGDOM",
        "U.K.": "UNITED KINGDOM",
        "GERMANY": "GERMANY",
        "INDIA": "INDIA",
        "CANADA": "CANADA"
    }

    parts = location.replace(",", " ").split()
    if parts:
        last_part = parts[-1]
        return country_mappings.get(last_part, last_part)
    return None


def validate_json_structure(data: dict) -> tuple[bool, list[str]]:
    errors = []
    required_keys = ["applicant_id", "personal", "experience", "salary"]
    for key in required_keys:
        if key not in data:
            errors.append(f"Missing required field: {key}")

    if "personal" in data:
        personal_fields = ["name", "email", "location"]
        for field in personal_fields:
            if field not in data["personal"]:
                errors.append(f"Missing personal field: {field}")

    if "experience" in data and not isinstance(data["experience"], list):
        errors.append("Experience must be a list.")

    if "salary" in data:
        salary_fields = ["preferred_rate", "availability"]
        for field in salary_fields:
            if field not in data["salary"]:
                errors.append(f"Missing salary field: {field}")

    return len(errors) == 0, errors
