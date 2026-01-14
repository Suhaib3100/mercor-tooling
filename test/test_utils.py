"""Tests for utils module."""
import pytest
from datetime import datetime
from src.utils import (
    parse_date,
    calculate_years_between,
    normalize_location,
    validate_json_structure
)


class TestParseDate:
    """Tests for parse_date function."""

    def test_valid_date_string(self):
        result = parse_date("2023-01-15")
        assert result is not None
        assert result.year == 2023
        assert result.month == 1
        assert result.day == 15

    def test_empty_string(self):
        assert parse_date("") is None

    def test_none_input(self):
        assert parse_date(None) is None

    def test_invalid_date(self):
        assert parse_date("not-a-date") is None


class TestCalculateYearsBetween:
    """Tests for calculate_years_between function."""

    def test_full_year(self):
        result = calculate_years_between("2020-01-01", "2021-01-01")
        assert result >= 0.99 and result <= 1.01

    def test_multiple_years(self):
        result = calculate_years_between("2018-01-01", "2023-01-01")
        assert result >= 4.9 and result <= 5.1

    def test_no_start_date(self):
        result = calculate_years_between("", "2023-01-01")
        assert result == 0.0

    def test_no_end_date_uses_now(self):
        result = calculate_years_between("2020-01-01")
        assert result > 0


class TestNormalizeLocation:
    """Tests for normalize_location function."""

    def test_us_normalization(self):
        assert normalize_location("New York, US") == "USA"

    def test_full_country_name(self):
        assert normalize_location("California, United States") == "USA"

    def test_empty_location(self):
        assert normalize_location("") is None

    def test_none_location(self):
        assert normalize_location(None) is None

    def test_india(self):
        result = normalize_location("Bangalore, India")
        assert result == "INDIA"


class TestValidateJsonStructure:
    """Tests for validate_json_structure function."""

    def test_valid_structure(self):
        data = {
            "applicant_id": "123",
            "personal": {"name": "John", "email": "john@test.com", "location": "NYC"},
            "experience": [],
            "salary": {"preferred_rate": 100, "availability": 20}
        }
        is_valid, errors = validate_json_structure(data)
        assert is_valid is True
        assert len(errors) == 0

    def test_missing_applicant_id(self):
        data = {
            "personal": {"name": "John", "email": "john@test.com", "location": "NYC"},
            "experience": [],
            "salary": {"preferred_rate": 100, "availability": 20}
        }
        is_valid, errors = validate_json_structure(data)
        assert is_valid is False
        assert "Missing required field: applicant_id" in errors

    def test_missing_personal_fields(self):
        data = {
            "applicant_id": "123",
            "personal": {"name": "John"},
            "experience": [],
            "salary": {"preferred_rate": 100, "availability": 20}
        }
        is_valid, errors = validate_json_structure(data)
        assert is_valid is False
        assert any("email" in e for e in errors)

    def test_experience_not_list(self):
        data = {
            "applicant_id": "123",
            "personal": {"name": "John", "email": "john@test.com", "location": "NYC"},
            "experience": "not a list",
            "salary": {"preferred_rate": 100, "availability": 20}
        }
        is_valid, errors = validate_json_structure(data)
        assert is_valid is False
        assert "Experience must be a list." in errors
