"""Tests for llm_eval module."""
import pytest
from unittest.mock import Mock, patch
from src.llm_eval import (
    build_llm_prompt,
    parse_llm_response,
    get_json_hash,
    evaluate_applicant
)


class TestBuildLlmPrompt:
    """Tests for build_llm_prompt function."""

    def test_includes_json_data(self):
        applicant = {"applicant_id": "123", "personal": {"name": "Jane"}}
        prompt = build_llm_prompt(applicant)
        assert '"applicant_id": "123"' in prompt
        assert "Jane" in prompt

    def test_includes_instructions(self):
        applicant = {"applicant_id": "123"}
        prompt = build_llm_prompt(applicant)
        assert "75-word summary" in prompt
        assert "1-10" in prompt
        assert "follow-up questions" in prompt.lower()


class TestParseLlmResponse:
    """Tests for parse_llm_response function."""

    def test_parses_complete_response(self):
        response = """Summary: This is a great candidate with strong experience.
Score: 8
Issues: Missing end date for current role
Follow-Ups:
- What is your availability starting date?
- Can you share portfolio links?"""

        result = parse_llm_response(response)
        
        assert "great candidate" in result["summary"]
        assert result["score"] == 8
        assert "Missing end date" in result["issues"]
        assert "availability" in result["follow_ups"]

    def test_handles_empty_response(self):
        result = parse_llm_response("")
        assert result["summary"] == ""
        assert result["score"] == 0

    def test_handles_none_response(self):
        result = parse_llm_response(None)
        assert result["summary"] == ""
        assert result["score"] == 0

    def test_extracts_score_correctly(self):
        response = "Summary: Test\nScore: 7\nIssues: None"
        result = parse_llm_response(response)
        assert result["score"] == 7


class TestGetJsonHash:
    """Tests for get_json_hash function."""

    def test_same_input_same_hash(self):
        json_str = '{"name": "Jane"}'
        hash1 = get_json_hash(json_str)
        hash2 = get_json_hash(json_str)
        assert hash1 == hash2

    def test_different_input_different_hash(self):
        hash1 = get_json_hash('{"name": "Jane"}')
        hash2 = get_json_hash('{"name": "John"}')
        assert hash1 != hash2


class TestEvaluateApplicant:
    """Tests for evaluate_applicant function."""

    def test_skips_record_without_json(self):
        mock_client = Mock()
        applicant_record = {"id": "rec123", "fields": {}}
        
        result = evaluate_applicant(mock_client, applicant_record)
        
        assert result is False

    def test_skips_unchanged_json(self):
        mock_client = Mock()
        json_data = '{"applicant_id": "123"}'
        json_hash = get_json_hash(json_data)[:8]
        
        applicant_record = {
            "id": "rec123",
            "fields": {
                "Compressed JSON": json_data,
                "LLM Summary": f"Previous summary [hash:{json_hash}]"
            }
        }
        
        result = evaluate_applicant(mock_client, applicant_record)
        
        assert result is True
        mock_client.update_record.assert_not_called()

    @patch('src.llm_eval.call_llm_api')
    def test_calls_llm_for_new_json(self, mock_llm):
        mock_client = Mock()
        mock_llm.return_value = "Summary: Test summary\nScore: 8\nIssues: None\nFollow-Ups:\n- Question 1"
        
        json_data = '{"applicant_id": "123", "personal": {"name": "Jane"}}'
        applicant_record = {
            "id": "rec123",
            "fields": {"Compressed JSON": json_data}
        }
        
        result = evaluate_applicant(mock_client, applicant_record)
        
        assert result is True
        mock_llm.assert_called_once()
        mock_client.update_record.assert_called_once()
