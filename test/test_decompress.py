"""Tests for decompress module."""
import pytest
import json
from unittest.mock import Mock, patch
from src.decompress import (
    parse_compressed_json,
    upsert_personal_details,
    upsert_salary_preferences,
    decompress_applicant
)


class TestParseCompressedJson:
    """Tests for parse_compressed_json function."""

    def test_parses_valid_json(self):
        json_string = '{"applicant_id": "123", "personal": {"name": "Jane", "email": "j@t.com", "location": "NYC"}, "experience": [], "salary": {"preferred_rate": 100, "availability": 20}}'
        result = parse_compressed_json(json_string)
        assert result is not None
        assert result["applicant_id"] == "123"

    def test_returns_none_for_empty_string(self):
        assert parse_compressed_json("") is None

    def test_returns_none_for_invalid_json(self):
        assert parse_compressed_json("not valid json") is None

    def test_handles_missing_fields(self):
        json_string = '{"applicant_id": "123"}'
        result = parse_compressed_json(json_string)
        # Should still return data even with validation warnings
        assert result is not None


class TestUpsertPersonalDetails:
    """Tests for upsert_personal_details function."""

    def test_creates_new_record_when_none_exists(self):
        mock_client = Mock()
        mock_client.get_linked_records.return_value = []
        
        personal_data = {"name": "Jane", "email": "jane@test.com", "location": "NYC"}
        
        result = upsert_personal_details(mock_client, "rec123", personal_data)
        
        assert result is True
        mock_client.create_record.assert_called_once()

    def test_updates_existing_record(self):
        mock_client = Mock()
        mock_client.get_linked_records.return_value = [{"id": "personal_rec1"}]
        
        personal_data = {"name": "Jane Updated", "email": "jane@test.com", "location": "NYC"}
        
        result = upsert_personal_details(mock_client, "rec123", personal_data)
        
        assert result is True
        mock_client.update_record.assert_called_once()
        mock_client.create_record.assert_not_called()


class TestUpsertSalaryPreferences:
    """Tests for upsert_salary_preferences function."""

    def test_creates_new_record(self):
        mock_client = Mock()
        mock_client.get_linked_records.return_value = []
        
        salary_data = {"preferred_rate": 100, "minimum_rate": 80, "currency": "USD", "availability": 40}
        
        result = upsert_salary_preferences(mock_client, "rec123", salary_data)
        
        assert result is True
        mock_client.create_record.assert_called_once()


class TestDecompressApplicant:
    """Tests for decompress_applicant function."""

    @patch('src.decompress.upsert_personal_details')
    @patch('src.decompress.upsert_work_experience')
    @patch('src.decompress.upsert_salary_preferences')
    def test_skips_record_without_json(self, mock_salary, mock_exp, mock_personal):
        mock_client = Mock()
        applicant_record = {"id": "rec123", "fields": {}}
        
        result = decompress_applicant(mock_client, applicant_record)
        
        assert result is False
        mock_personal.assert_not_called()

    @patch('src.decompress.upsert_personal_details', return_value=True)
    @patch('src.decompress.upsert_work_experience', return_value=True)
    @patch('src.decompress.upsert_salary_preferences', return_value=True)
    def test_decompresses_valid_record(self, mock_salary, mock_exp, mock_personal):
        mock_client = Mock()
        json_data = {
            "applicant_id": "APP001",
            "personal": {"name": "Jane", "email": "j@t.com", "location": "NYC"},
            "experience": [],
            "salary": {"preferred_rate": 100, "availability": 20}
        }
        applicant_record = {
            "id": "rec123",
            "fields": {"Compressed JSON": json.dumps(json_data)}
        }
        
        result = decompress_applicant(mock_client, applicant_record)
        
        assert result is True
        mock_personal.assert_called_once()
        mock_exp.assert_called_once()
        mock_salary.assert_called_once()
