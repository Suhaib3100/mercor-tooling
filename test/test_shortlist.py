"""Tests for shortlist module."""
import pytest
from unittest.mock import Mock, patch
from src.shortlist import (
    calculate_total_experience,
    worked_at_tier1,
    meets_experience_criteria,
    meets_compensation_criteria,
    meets_location_criteria,
    evaluate_applicant
)


class TestCalculateTotalExperience:
    """Tests for calculate_total_experience function."""

    def test_single_job(self):
        experience = [{"start": "2020-01-01", "end": "2023-01-01"}]
        result = calculate_total_experience(experience)
        assert result >= 2.9 and result <= 3.1

    def test_multiple_jobs(self):
        experience = [
            {"start": "2018-01-01", "end": "2020-01-01"},
            {"start": "2020-01-01", "end": "2023-01-01"}
        ]
        result = calculate_total_experience(experience)
        assert result >= 4.9 and result <= 5.1

    def test_empty_experience(self):
        result = calculate_total_experience([])
        assert result == 0.0


class TestWorkedAtTier1:
    """Tests for worked_at_tier1 function."""

    def test_google_is_tier1(self):
        experience = [{"company": "Google Inc"}]
        is_tier1, company = worked_at_tier1(experience)
        assert is_tier1 is True
        assert "Google" in company

    def test_meta_is_tier1(self):
        experience = [{"company": "Meta Platforms"}]
        is_tier1, company = worked_at_tier1(experience)
        assert is_tier1 is True

    def test_unknown_company(self):
        experience = [{"company": "Random Startup LLC"}]
        is_tier1, company = worked_at_tier1(experience)
        assert is_tier1 is False
        assert company is None


class TestMeetsExperienceCriteria:
    """Tests for meets_experience_criteria function."""

    def test_meets_with_years(self):
        experience = [
            {"start": "2015-01-01", "end": "2020-01-01"},
            {"start": "2020-01-01", "end": "2023-01-01"}
        ]
        passed, reasons = meets_experience_criteria(experience)
        assert passed is True
        assert len(reasons) > 0

    def test_meets_with_tier1(self):
        experience = [{"company": "Google", "start": "2022-01-01", "end": "2023-01-01"}]
        passed, reasons = meets_experience_criteria(experience)
        assert passed is True
        assert any("Tier-1" in r for r in reasons)

    def test_fails_no_experience(self):
        passed, reasons = meets_experience_criteria([])
        assert passed is False


class TestMeetsCompensationCriteria:
    """Tests for meets_compensation_criteria function."""

    def test_meets_criteria(self):
        salary = {"preferred_rate": 80, "availability": 30, "currency": "USD"}
        passed, reasons = meets_compensation_criteria(salary)
        assert passed is True
        assert len(reasons) == 2

    def test_fails_rate_too_high(self):
        salary = {"preferred_rate": 150, "availability": 30}
        passed, reasons = meets_compensation_criteria(salary)
        assert passed is False

    def test_fails_low_availability(self):
        salary = {"preferred_rate": 80, "availability": 10}
        passed, reasons = meets_compensation_criteria(salary)
        assert passed is False


class TestMeetsLocationCriteria:
    """Tests for meets_location_criteria function."""

    def test_approved_location_usa(self):
        personal = {"location": "New York, US"}
        passed, reasons = meets_location_criteria(personal)
        assert passed is True

    def test_approved_location_india(self):
        personal = {"location": "Bangalore, India"}
        passed, reasons = meets_location_criteria(personal)
        assert passed is True

    def test_unapproved_location(self):
        personal = {"location": "Tokyo, Japan"}
        passed, reasons = meets_location_criteria(personal)
        assert passed is False


class TestEvaluateApplicant:
    """Tests for evaluate_applicant function."""

    def test_fully_qualified_applicant(self):
        applicant = {
            "personal": {"location": "San Francisco, US"},
            "experience": [
                {"company": "Google", "start": "2015-01-01", "end": "2020-01-01"}
            ],
            "salary": {"preferred_rate": 90, "availability": 40, "currency": "USD"}
        }
        passed, reasons = evaluate_applicant(applicant)
        assert passed is True
        assert len(reasons) >= 3

    def test_unqualified_applicant(self):
        applicant = {
            "personal": {"location": "Tokyo, Japan"},
            "experience": [],
            "salary": {"preferred_rate": 200, "availability": 5}
        }
        passed, reasons = evaluate_applicant(applicant)
        assert passed is False
