"""
LLM Evaluation and Enrichment - Use LLM to analyze and score applicants.
"""
import json
import time
import re
import hashlib
from src.airtable_client import AirtableClient
from src.config import (
    TABLE_APPLICANTS,
    LLM_API_KEY,
    LLM_PROVIDER,
    LLM_MODEL,
    LLM_MAX_TOKENS,
    LLM_MAX_RETRIES,
    LLM_TIMEOUT
)
from src.utils import get_logger

logger = get_logger(__name__)


def build_llm_prompt(applicant_json: dict) -> str:
    """Construct prompt with JSON data."""
    json_string = json.dumps(applicant_json, indent=2)

    prompt = f"""You are a recruiting analyst reviewing contractor applications. Given this JSON applicant profile, perform four tasks:

1. Provide a concise 75-word summary highlighting key qualifications and experience.
2. Rate overall candidate quality from 1-10 (10 = exceptional, 1 = unsuitable).
3. List any data gaps or inconsistencies you notice.
4. Suggest up to three follow-up questions to clarify gaps or strengthen the application.

Applicant JSON:
{json_string}

Return your response in exactly this format:
Summary: <your 75-word summary>
Score: <integer 1-10>
Issues: <comma-separated list or 'None'>
Follow-Ups:
- <question 1>
- <question 2>
- <question 3>"""

    return prompt


def call_openai_api(prompt: str) -> str:
    """Call OpenAI API."""
    import openai

    client = openai.OpenAI(api_key=LLM_API_KEY)
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=LLM_MAX_TOKENS
    )
    return response.choices[0].message.content


def call_anthropic_api(prompt: str) -> str:
    """Call Anthropic API."""
    import anthropic

    client = anthropic.Anthropic(api_key=LLM_API_KEY)
    response = client.messages.create(
        model=LLM_MODEL,
        max_tokens=LLM_MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text


def call_gemini_api(prompt: str) -> str:
    """Call Google Gemini API."""
    import google.generativeai as genai

    genai.configure(api_key=LLM_API_KEY)
    model = genai.GenerativeModel(LLM_MODEL)
    response = model.generate_content(prompt)
    return response.text


def call_llm_api(prompt: str) -> str | None:
    """Call LLM API with retry logic."""
    api_functions = {
        "openai": call_openai_api,
        "anthropic": call_anthropic_api,
        "gemini": call_gemini_api
    }

    api_func = api_functions.get(LLM_PROVIDER)
    if not api_func:
        logger.error(f"Unknown LLM provider: {LLM_PROVIDER}")
        return None

    for attempt in range(LLM_MAX_RETRIES):
        try:
            return api_func(prompt)
        except Exception as e:
            logger.warning(f"LLM API call failed (attempt {attempt + 1}/{LLM_MAX_RETRIES}): {e}")
            if attempt < LLM_MAX_RETRIES - 1:
                delay = LLM_TIMEOUT * (2 ** attempt)  # Exponential backoff
                time.sleep(delay)

    logger.error("LLM API call failed after all retries")
    return None


def parse_llm_response(response_text: str) -> dict:
    """Extract summary, score, issues, follow-ups from response."""
    result = {
        "summary": "",
        "score": 0,
        "issues": "",
        "follow_ups": ""
    }

    if not response_text:
        return result

    # Extract Summary
    summary_match = re.search(r"Summary:\s*(.+?)(?=\nScore:|$)", response_text, re.DOTALL)
    if summary_match:
        result["summary"] = summary_match.group(1).strip()

    # Extract Score
    score_match = re.search(r"Score:\s*(\d+)", response_text)
    if score_match:
        result["score"] = int(score_match.group(1))

    # Extract Issues
    issues_match = re.search(r"Issues:\s*(.+?)(?=\nFollow-Ups:|$)", response_text, re.DOTALL)
    if issues_match:
        result["issues"] = issues_match.group(1).strip()

    # Extract Follow-Ups
    followups_match = re.search(r"Follow-Ups:\s*(.+?)$", response_text, re.DOTALL)
    if followups_match:
        result["follow_ups"] = followups_match.group(1).strip()

    return result


def get_json_hash(json_string: str) -> str:
    """Generate hash of JSON for change detection."""
    return hashlib.md5(json_string.encode()).hexdigest()


def evaluate_applicant(client: AirtableClient, applicant_record: dict) -> bool:
    """Run LLM evaluation for a single applicant."""
    record_id = applicant_record.get("id")
    fields = applicant_record.get("fields", {})
    json_string = fields.get("Compressed JSON")

    if not json_string:
        logger.warning(f"Record {record_id} has no Compressed JSON, skipping")
        return False

    # Check if JSON has changed (budget guardrail)
    current_hash = get_json_hash(json_string)
    stored_summary = fields.get("LLM Summary", "")

    # Skip if already evaluated and JSON unchanged
    if stored_summary and f"[hash:{current_hash[:8]}]" in stored_summary:
        logger.info(f"Skipping {record_id} - JSON unchanged")
        return True

    try:
        json_data = json.loads(json_string)
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON for record {record_id}")
        return False

    # Build prompt and call LLM
    prompt = build_llm_prompt(json_data)
    response = call_llm_api(prompt)

    if not response:
        return False

    # Parse response
    parsed = parse_llm_response(response)

    # Add hash to summary for change detection
    summary_with_hash = f"{parsed['summary']} [hash:{current_hash[:8]}]"

    # Update Applicants table
    try:
        client.update_record(TABLE_APPLICANTS, record_id, {
            "LLM Summary": summary_with_hash,
            "LLM Score": parsed["score"],
            "LLM Follow-Ups": parsed["follow_ups"]
        })
        logger.info(f"Updated LLM fields for {record_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to update LLM fields: {e}")
        return False


def evaluate_all_applicants():
    """Main function: evaluate all applicants with LLM."""
    client = AirtableClient()

    applicants = client.get_records(TABLE_APPLICANTS)
    logger.info(f"Found {len(applicants)} applicants to evaluate")

    success_count = 0
    failure_count = 0

    for applicant in applicants:
        if evaluate_applicant(client, applicant):
            success_count += 1
        else:
            failure_count += 1

    logger.info(f"LLM evaluation complete: {success_count} succeeded, {failure_count} failed")
    return success_count, failure_count


if __name__ == "__main__":
    evaluate_all_applicants()
