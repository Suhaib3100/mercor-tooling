"""Tests for compress module."""
import pytest
import json
from unittest.mock import Mock, patch
from src.compress import (
    fetch_applicant_data,
    build_json_object,
    compress_single_applicant
)


class TestBuildJsonObject:
    """Tests for build_json_object function."""

    def test_builds_valid_json(self):
        data = {
            "applicant_id": "123",
            "personal": {"name": "Jane Doe", "email": "jane@test.com"},
            "experience": [{"company": "Google", "title": "SWE"}],
            "salary": {"preferred_rate": 100}
        }
        result = build_json_object(data)
        parsed = json.loads(result)
        assert parsed["applicant_id"] == "123"
        assert parsed["personal"]["name"] == "Jane Doe"

    def test_empty_data(self):
        data = {}
        result = build_json_object(data)
        assert result == "{}"


class TestFetchApplicantData:
    """Tests for fetch_applicant_data function."""

    @patch('src.compress.AirtableClient')
    def test_fetches_all_linked_records(self, mock_client_class):
        mock_client = Mock()
        
        # Mock personal details response
        mock_client.get_linked_records.side_effect = [
            [{"fields": {"Full Name": "Jane", "Email": "jane@test.com", "Location": "NYC", "LinkedIn": ""}}],
            [{"id": "exp1", "fields": {"Company": "Google", "Title": "SWE", "Start": "2020-01-01", "End": "2023-01-01", "Technologies": ["Python"]}}],
            [{"fields": {"Preferred Rate": 100, "Minimum Rate": 80, "Currency": "USD", "Availability": 40}}]
        ]

        result = fetch_applicant_data(mock_client, "APP001", "rec123")

        assert result["applicant_id"] == "APP001"
        assert result["personal"]["name"] == "Jane"
        assert len(result["experience"]) == 1
        assert result["experience"][0]["company"] == "Google"
        assert result["salary"]["preferred_rate"] == 100


class TestCompressSingleApplicant:
    """Tests for compress_single_applicant function."""

    @patch('src.compress.fetch_applicant_data')
    def test_skips_record_without_applicant_id(self, mock_fetch):
        mock_client = Mock()
        applicant_record = {"id": "rec123", "fields": {}}
        
        result = compress_single_applicant(mock_client, applicant_record)
        
        assert result is False
        mock_fetch.assert_not_called()

    @patch('src.compress.fetch_applicant_data')
    def test_compresses_valid_applicant(self, mock_fetch):
        mock_client = Mock()
        mock_fetch.return_value = {
            "applicant_id": "APP001",
            "personal": {"name": "Jane"},
            "experience": [],
            "salary": {}
        }
        
        applicant_record = {"id": "rec123", "fields": {"Applicant ID": "APP001"}}
        
        result = compress_single_applicant(mock_client, applicant_record)
        
        assert result is True
        mock_client.update_record.assert_called_once()
