# Mercor Tooling - Architecture Documentation

## System Overview

This system automates contractor application processing using Airtable as the data source and Python scripts for data transformation, evaluation, and LLM-powered enrichment.

## High-Level Data Flow

```
Airtable tables
   ↓
compress.py
   ↓
ONE canonical JSON per applicant
   ↓
shortlist.py     llm_eval.py
   ↓                ↓
Shortlisted Leads   LLM fields
   ↓
(optional)
decompress.py → back to tables
```

---

## 1. Airtable Schema Design

### 1.1 Tables Overview

| Table | Key Fields | Notes |
|-------|------------|-------|
| Applicants (parent) | Applicant ID (primary), Compressed JSON, Shortlist Status, LLM Summary, LLM Score, LLM Follow-Ups | Stores one row per applicant and holds the compressed JSON + LLM outputs |
| Personal Details | Full Name, Email, Location, LinkedIn, (linked to Applicant ID) | One-to-one with the parent |
| Work Experience | Company, Title, Start, End, Technologies, (linked to Applicant ID) | One-to-many |
| Salary Preferences | Preferred Rate, Minimum Rate, Currency, Availability (hrs/wk), (linked to Applicant ID) | One-to-one |
| Shortlisted Leads | Applicant (link to Applicants), Compressed JSON, Score Reason, Created At | Auto-populated when rules are met |

### 1.2 Detailed Field Specifications

#### Applicants Table (Parent)
**Purpose**: Stores one row per applicant and holds the compressed JSON + LLM outputs

| Field Name | Type | Description |
|------------|------|-------------|
| Applicant ID | Primary Key (Text) | Unique identifier for each applicant |
| Compressed JSON | Long Text | Single JSON object containing all applicant data |
| Shortlist Status | Single Select | Values: Pending, Shortlisted, Rejected |
| LLM Summary | Long Text | AI-generated 75-word summary |
| LLM Score | Number | Quality score from 1-10 |
| LLM Follow-Ups | Long Text | AI-suggested follow-up questions |

#### Personal Details Table (Child - One-to-One)
**Purpose**: Stores personal information for each applicant

| Field Name | Type | Description |
|------------|------|-------------|
| Full Name | Single Line Text | Applicant's full name |
| Email | Email | Contact email address |
| Location | Single Line Text | City, Country format |
| LinkedIn | URL | LinkedIn profile URL |
| Applicant ID | Linked Record | Link to Applicants table |

#### Work Experience Table (Child - One-to-Many)
**Purpose**: Stores employment history, multiple records per applicant

| Field Name | Type | Description |
|------------|------|-------------|
| Company | Single Line Text | Company name |
| Title | Single Line Text | Job title/role |
| Start | Date | Employment start date |
| End | Date | Employment end date (blank if current) |
| Technologies | Multiple Select | Tech stack used |
| Applicant ID | Linked Record | Link to Applicants table |

#### Salary Preferences Table (Child - One-to-One)
**Purpose**: Stores compensation and availability preferences

| Field Name | Type | Description |
|------------|------|-------------|
| Preferred Rate | Number | Preferred hourly rate |
| Minimum Rate | Number | Minimum acceptable rate |
| Currency | Single Select | USD, EUR, GBP, INR, etc. |
| Availability | Number | Hours per week (hrs/wk) |
| Applicant ID | Linked Record | Link to Applicants table |

#### Shortlisted Leads Table (Auto-Populated)
**Purpose**: Auto-populated when shortlist rules are met

| Field Name | Type | Description |
|------------|------|-------------|
| Applicant | Linked Record | Link to Applicants table |
| Compressed JSON | Long Text | Copy of applicant JSON |
| Score Reason | Long Text | Explanation of why shortlisted |
| Created At | Created Time | Auto-populated timestamp |

### 1.3 Table Relationships

```
Applicants (1) ←→ (1) Personal Details
Applicants (1) ←→ (N) Work Experience
Applicants (1) ←→ (1) Salary Preferences
Applicants (1) ←→ (0..1) Shortlisted Leads
```

All child tables are linked back to Applicants by Applicant ID.

---

## 2. Python Module Architecture

### 2.1 Module Overview

| Module | Purpose | Key Functions |
|--------|---------|---------------|
| airtable_client.py | Airtable API wrapper | get_records, create_record, update_record, batch_operations |
| config.py | Configuration management | Load env vars, API keys, constants |
| compress.py | Data compression | Fetch linked records, build JSON, update Applicants |
| decompress.py | Data decompression | Parse JSON, upsert child records, maintain links |
| shortlist.py | Candidate evaluation | Apply rules, create Shortlisted Leads |
| llm_eval.py | LLM evaluation | Call LLM API, parse response, update fields |
| utils.py | Shared utilities | Date parsing, validation, error handling |

### 2.2 Configuration (config.py)

**Environment Variables Required**:
- `AIRTABLE_API_KEY` - Airtable personal access token
- `AIRTABLE_BASE_ID` - Base identifier
- `LLM_API_KEY` - OpenAI/Anthropic/Gemini API key
- `LLM_PROVIDER` - Options: openai, anthropic, gemini
- `LLM_MODEL` - Model name (e.g., gpt-4, claude-3-sonnet)

**Configuration Constants**:
```python
# Table names
TABLE_APPLICANTS = "Applicants"
TABLE_PERSONAL = "Personal Details"
TABLE_EXPERIENCE = "Work Experience"
TABLE_SALARY = "Salary Preferences"
TABLE_SHORTLISTED = "Shortlisted Leads"

# Shortlist criteria
TIER_1_COMPANIES = ["Google", "Meta", "OpenAI", "Amazon", "Microsoft", ...]
MIN_EXPERIENCE_YEARS = 4
MAX_PREFERRED_RATE = 100
MIN_AVAILABILITY_HOURS = 20
APPROVED_LOCATIONS = ["US", "Canada", "UK", "Germany", "India"]

# LLM settings
LLM_MAX_TOKENS = 500
LLM_MAX_RETRIES = 3
LLM_RETRY_DELAY = 2  # seconds, exponential backoff
```

### 2.3 Airtable Client (airtable_client.py)

**Class Structure**:
```python
class AirtableClient:
    def __init__(self, api_key, base_id)
    def get_all_records(self, table_name, filter_formula=None)
    def get_record(self, table_name, record_id)
    def create_record(self, table_name, fields)
    def update_record(self, table_name, record_id, fields)
    def batch_create(self, table_name, records_list)
    def batch_update(self, table_name, records_list)
    def batch_delete(self, table_name, record_ids)
    def get_linked_records(self, parent_id, child_table)
```

**Features**:
- Rate limiting (5 requests/second)
- Automatic retry with exponential backoff
- Batch operation support (max 10 records per batch)
- Error handling and logging

---

## 3. Compression Pipeline (compress.py)

### 3.1 Purpose
Gather data from all linked child tables and create a single canonical JSON object per applicant.

### 3.2 Process Flow

```
1. Fetch all applicants from Applicants table
2. For each applicant:
   a. Fetch Personal Details (linked record)
   b. Fetch Work Experience (all linked records)
   c. Fetch Salary Preferences (linked record)
3. Build JSON structure
4. Update Compressed JSON field in Applicants table
5. Log success/failures
```

### 3.3 JSON Structure

```json
{
  "applicant_id": "rec123456",
  "personal": {
    "full_name": "Jane Doe",
    "email": "jane@example.com",
    "location": "New York, US",
    "linkedin": "https://linkedin.com/in/janedoe"
  },
  "experience": [
    {
      "company": "Google",
      "title": "Senior Software Engineer",
      "start": "2020-01-15",
      "end": "2023-06-30",
      "technologies": ["Python", "Go", "Kubernetes"]
    },
    {
      "company": "Meta",
      "title": "Software Engineer",
      "start": "2018-06-01",
      "end": "2019-12-31",
      "technologies": ["React", "GraphQL", "Python"]
    }
  ],
  "salary": {
    "preferred_rate": 95,
    "minimum_rate": 80,
    "currency": "USD",
    "availability": 25
  },
  "metadata": {
    "compressed_at": "2026-01-15T10:30:00Z",
    "version": "1.0"
  }
}
```

### 3.4 Key Functions

```python
def fetch_applicant_data(client, applicant_id):
    """Fetch all related data for one applicant"""

def build_json_object(applicant_data, personal, experience_list, salary):
    """Construct canonical JSON from raw data"""

def compress_all_applicants():
    """Main function: compress all applicants in batch"""

def compress_single_applicant(applicant_id):
    """Compress data for a single applicant (for updates)"""
```

### 3.5 Error Handling
- Missing child records: Use empty objects/arrays
- Invalid data: Log warnings, use null values
- API failures: Retry with exponential backoff
- Maintain compression log with timestamps

---

## 4. Decompression Pipeline (decompress.py)

### 4.1 Purpose
Read Compressed JSON and upsert child table records to reflect exact JSON state.

### 4.2 Process Flow

```
1. Fetch applicant record with Compressed JSON
2. Parse JSON into components
3. Upsert Personal Details:
   - Find existing record by Applicant ID link
   - Update if exists, create if not
4. Upsert Work Experience:
   - Find all existing records by Applicant ID link
   - Match by company+title+dates
   - Update matches, create new, delete orphans
5. Upsert Salary Preferences:
   - Find existing record by Applicant ID link
   - Update if exists, create if not
6. Verify all links are maintained
7. Log changes
```

### 4.3 Key Functions

```python
def parse_compressed_json(json_string):
    """Parse and validate JSON structure"""

def upsert_personal_details(client, applicant_id, personal_data):
    """Create or update Personal Details record"""

def upsert_work_experience(client, applicant_id, experience_list):
    """Sync Work Experience records (create/update/delete)"""

def upsert_salary_preferences(client, applicant_id, salary_data):
    """Create or update Salary Preferences record"""

def decompress_applicant(applicant_id):
    """Main function: decompress one applicant"""

def decompress_all():
    """Decompress all applicants with valid JSON"""
```

### 4.4 Sync Strategy for One-to-Many (Work Experience)

**Matching Logic**:
1. Fetch all existing Work Experience records for applicant
2. For each JSON experience entry:
   - Try to match by company + title + start_date
   - If match found: update the record
   - If no match: create new record
3. Delete existing records not matched in JSON (orphans)

**Ensures**: Child tables always mirror JSON state exactly

---

## 5. Shortlist Pipeline (shortlist.py)

### 5.1 Purpose
Automatically identify and flag promising candidates based on multi-factor rules.

### 5.2 Shortlist Criteria

| Criterion | Rule |
|-----------|------|
| Experience | >= 4 years total OR worked at Tier-1 company |
| Compensation | Preferred Rate <= $100 USD/hour AND Availability >= 20 hrs/week |
| Location | In US, Canada, UK, Germany, or India |

**All criteria must be met** to be shortlisted.

### 5.3 Process Flow

```
1. Fetch all applicants with Compressed JSON
2. For each applicant:
   a. Parse JSON
   b. Calculate total years of experience
   c. Check if worked at Tier-1 company
   d. Evaluate experience criterion
   e. Check rate and availability
   f. Normalize and check location
   g. If ALL criteria met:
      - Set Shortlist Status = "Shortlisted"
      - Create Shortlisted Leads record
      - Copy Compressed JSON
      - Generate Score Reason
3. Log shortlist results
```

### 5.4 Key Functions

```python
def calculate_total_experience(experience_list):
    """Calculate total years from experience entries"""

def worked_at_tier1(experience_list, tier1_companies):
    """Check if any company is in Tier-1 list"""

def meets_experience_criteria(experience_list):
    """Evaluate experience criterion"""

def meets_compensation_criteria(salary_data):
    """Evaluate rate and availability"""

def meets_location_criteria(personal_data):
    """Normalize and check location"""

def evaluate_applicant(applicant_json):
    """Run all criteria checks, return (passed, reasons)"""

def create_shortlisted_lead(client, applicant_id, json_data, reasons):
    """Create Shortlisted Leads record"""

def shortlist_all_applicants():
    """Main function: evaluate all applicants"""
```

### 5.5 Score Reason Examples

```
Shortlisted:
- 5.5 years total experience (exceeds 4-year minimum)
- Worked at Google (Tier-1 company)
- Preferred rate: $95/hour (under $100 threshold)
- Availability: 25 hours/week (exceeds 20-hour minimum)
- Location: New York, US (approved location)
```

---

## 6. LLM Evaluation Pipeline (llm_eval.py)

### 6.1 Purpose
Use LLM to automate qualitative review, generate summaries, assign scores, and identify gaps.

### 6.2 LLM Providers Support

| Provider | Model Options | Key Length |
|----------|---------------|------------|
| OpenAI | gpt-4-turbo, gpt-4, gpt-3.5-turbo | OPENAI_API_KEY |
| Anthropic | claude-3-opus, claude-3-sonnet | ANTHROPIC_API_KEY |
| Google | gemini-pro | GOOGLE_API_KEY |

### 6.3 Process Flow

```
1. Trigger: After Compressed JSON is written/updated
2. Load applicant with Compressed JSON
3. Build LLM prompt with full JSON
4. Call LLM API with retry logic:
   - Initial attempt
   - Retry up to 3 times with exponential backoff if fails
   - Log all errors
5. Parse LLM response:
   - Extract Summary (75 words max)
   - Extract Score (1-10)
   - Extract Issues list
   - Extract Follow-Ups list
6. Update Applicants table:
   - LLM Summary
   - LLM Score
   - LLM Follow-Ups
7. Log evaluation results
```

### 6.4 Prompt Template

```
You are a recruiting analyst reviewing contractor applications. Given this JSON applicant profile, perform four tasks:

1. Provide a concise 75-word summary highlighting key qualifications and experience.
2. Rate overall candidate quality from 1-10 (10 = exceptional, 1 = unsuitable).
3. List any data gaps or inconsistencies you notice.
4. Suggest up to three follow-up questions to clarify gaps or strengthen the application.

Applicant JSON:
{json_data}

Return your response in exactly this format:
Summary: <your 75-word summary>
Score: <integer 1-10>
Issues: <comma-separated list or 'None'>
Follow-Ups:
- <question 1>
- <question 2>
- <question 3>
```

### 6.5 Response Parsing

**Expected Output Format**:
```
Summary: Full-stack SWE with 5 years experience at Google and Meta. Strong background in Python, Go, React. Led backend infrastructure team. Currently seeking 25 hrs/week at $95/hour. Based in NYC. LinkedIn profile provided.

Score: 8

Issues: Missing end date for Google role (may still be employed), No specific production metrics or impact quantified

Follow-Ups:
- Can you confirm your current employment status at Google?
- What was the scale/impact of projects you led at Google?
- Are you available to start immediately or is there a notice period?
```

### 6.6 Key Functions

```python
def build_llm_prompt(applicant_json):
    """Construct prompt with JSON data"""

def call_llm_api(prompt, provider, model, api_key):
    """Call LLM API with retry logic"""

def parse_llm_response(response_text):
    """Extract summary, score, issues, follow-ups"""

def validate_llm_output(parsed_output):
    """Ensure all required fields present and valid"""

def evaluate_applicant_with_llm(applicant_id):
    """Main function: evaluate one applicant"""

def evaluate_all_applicants():
    """Batch evaluate all applicants with JSON"""
```

### 6.7 Budget Guardrails

**Token Management**:
- Max input tokens: ~2000 (compressed JSON + prompt)
- Max output tokens: 500
- Total cost per call: ~$0.01-0.05 depending on model

**Caching Strategy**:
- Hash Compressed JSON
- Store hash in metadata
- Skip LLM call if hash unchanged since last evaluation
- Force re-evaluation with command-line flag

**Rate Limiting**:
- Max 10 requests per minute
- Batch processing with delays
- Queue system for large batches

### 6.8 Error Handling

**Retry Logic**:
```python
max_retries = 3
base_delay = 2  # seconds

for attempt in range(max_retries):
    try:
        response = call_api()
        break
    except APIError as e:
        if attempt < max_retries - 1:
            delay = base_delay * (2 ** attempt)  # exponential backoff
            time.sleep(delay)
        else:
            log_error(e)
            return None
```

**Failure Modes**:
- API timeout: Retry with longer timeout
- Rate limit: Wait and retry
- Invalid response: Log and mark for manual review
- Parsing error: Log raw response and skip

---

## 7. Utility Functions (utils.py)

### 7.1 Date Utilities

```python
def parse_date(date_string):
    """Parse various date formats to datetime"""

def calculate_duration(start_date, end_date):
    """Calculate duration in years between dates"""

def is_current_role(end_date):
    """Check if end_date is null/empty (current role)"""
```

### 7.2 Validation

```python
def validate_email(email):
    """Validate email format"""

def validate_url(url):
    """Validate URL format"""

def validate_currency(currency):
    """Check if currency code is valid"""

def normalize_location(location_string):
    """Extract country from location string"""
```

### 7.3 Logging

```python
def setup_logger(name, log_file):
    """Configure logging with file and console handlers"""

def log_operation(operation, applicant_id, status, details):
    """Structured logging for all operations"""
```

---

## 8. Execution Workflow

### 8.1 Initial Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with API keys and configuration

# 3. Verify Airtable connection
python -c "from airtable_client import AirtableClient; client = AirtableClient(); print('Connected')"
```

### 8.2 Daily Processing Workflow

```bash
# Step 1: Compress new/updated applicants
python compress.py --mode=incremental

# Step 2: Run shortlist evaluation
python shortlist.py

# Step 3: Run LLM evaluation
python llm_eval.py --batch-size=10

# Step 4 (Optional): Decompress for edits
python decompress.py --applicant-id=rec123456
```

### 8.3 Full Reprocessing

```bash
# Reprocess all applicants from scratch
python compress.py --mode=full
python shortlist.py --reprocess
python llm_eval.py --force-reevaluate
```

---

## 9. Command-Line Interface Design

### 9.1 compress.py

```bash
# Compress all applicants (full mode)
python compress.py --mode=full

# Compress only new/updated (incremental)
python compress.py --mode=incremental

# Compress specific applicant
python compress.py --applicant-id=rec123456

# Dry run (no updates)
python compress.py --mode=full --dry-run
```

### 9.2 decompress.py

```bash
# Decompress specific applicant
python decompress.py --applicant-id=rec123456

# Decompress all applicants
python decompress.py --all

# Dry run
python decompress.py --applicant-id=rec123456 --dry-run
```

### 9.3 shortlist.py

```bash
# Shortlist all applicants
python shortlist.py

# Reprocess all (clear existing shortlist)
python shortlist.py --reprocess

# Shortlist specific applicant
python shortlist.py --applicant-id=rec123456

# Dry run (show who would be shortlisted)
python shortlist.py --dry-run
```

### 9.4 llm_eval.py

```bash
# Evaluate all applicants
python llm_eval.py

# Force re-evaluation (ignore cache)
python llm_eval.py --force-reevaluate

# Evaluate specific applicant
python llm_eval.py --applicant-id=rec123456

# Batch processing with custom size
python llm_eval.py --batch-size=5

# Dry run
python llm_eval.py --dry-run
```

---

## 10. Security Considerations

### 10.1 API Key Management

- Store all API keys in environment variables
- Never commit .env file to version control
- Use .env.example as template
- Rotate keys periodically
- Use Airtable personal access tokens (not deprecated API keys)

### 10.2 Data Privacy

- All PII (email, name, LinkedIn) stored in Airtable (secure)
- Compressed JSON contains full applicant data - protect accordingly
- LLM API calls send full applicant data - ensure provider compliance
- Log files may contain sensitive data - restrict access

### 10.3 Rate Limiting

- Airtable: 5 requests/second
- OpenAI: 10,000 requests/minute (tier-dependent)
- Implement exponential backoff
- Queue system for large batches

---

## 11. Testing Strategy

### 11.1 Unit Tests

- Test each utility function independently
- Mock Airtable API responses
- Mock LLM API responses
- Test date calculations
- Test validation functions

### 11.2 Integration Tests

- Test full compress → shortlist → LLM → decompress flow
- Test error recovery
- Test retry logic
- Test batch operations

### 11.3 Test Data

Create test applicants with edge cases:
- Minimal data (only required fields)
- Maximal data (all fields populated)
- Edge case: exactly 4 years experience
- Edge case: exactly $100/hour rate
- Edge case: exactly 20 hours/week
- Invalid data (missing required fields)
- Multiple work experiences
- Current role (no end date)

---

## 12. Monitoring and Logging

### 12.1 Log Files

- `compress.log` - Compression operations
- `decompress.log` - Decompression operations
- `shortlist.log` - Shortlist evaluations
- `llm_eval.log` - LLM API calls and responses
- `errors.log` - All errors across modules

### 12.2 Metrics to Track

- Number of applicants processed
- Compression success rate
- Shortlist rate (% of applicants shortlisted)
- Average LLM score
- LLM API costs
- Processing time per applicant
- Error rates by type

### 12.3 Monitoring Dashboard

Optional: Create simple dashboard showing:
- Total applicants
- Shortlisted count
- Average LLM score
- Today's processing stats
- Recent errors

---

## 13. Future Enhancements

### 13.1 Automation

- Airtable automation to trigger Python scripts
- Webhook-based real-time processing
- Scheduled batch jobs (cron/GitHub Actions)

### 13.2 Advanced Features

- Multi-stage shortlisting (Bronze/Silver/Gold tiers)
- Skills matching against job requirements
- Duplicate detection (same email/LinkedIn)
- Automated email notifications to shortlisted candidates

### 13.3 Analytics

- Shortlist criteria optimization
- LLM score correlation with hire rate
- Geographic distribution analysis
- Salary trends by role/location

---

## 14. Dependencies

### 14.1 Python Packages (requirements.txt)

```
pyairtable>=2.1.0
python-dotenv>=1.0.0
openai>=1.0.0
anthropic>=0.8.0
google-generativeai>=0.3.0
requests>=2.31.0
python-dateutil>=2.8.0
pydantic>=2.0.0
pytest>=7.4.0
```

### 14.2 Python Version

- Minimum: Python 3.9
- Recommended: Python 3.11+

---

## 15. File Structure Summary

```
mercor-tooling/
├── README.md                  # Project overview and setup instructions
├── architechture.md           # This file - detailed architecture
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variable template
├── .env                      # Actual config (gitignored)
├── .gitignore               # Git ignore rules
│
├── config.py                # Configuration constants
├── airtable_client.py       # Airtable API wrapper
├── utils.py                 # Shared utilities
│
├── compress.py              # JSON compression script
├── decompress.py            # JSON decompression script
├── shortlist.py             # Shortlist evaluation script
├── llm_eval.py              # LLM evaluation script
│
├── logs/                    # Log files directory
│   ├── compress.log
│   ├── decompress.log
│   ├── shortlist.log
│   ├── llm_eval.log
│   └── errors.log
│
└── tests/                   # Test suite
    ├── test_compress.py
    ├── test_decompress.py
    ├── test_shortlist.py
    ├── test_llm_eval.py
    └── test_utils.py
```

---

## 16. Quick Start Guide

### Step 1: Airtable Setup
1. Create new Airtable base
2. Create all 5 tables with specified fields
3. Set up table links (Applicant ID relationships)
4. Generate personal access token
5. Copy base ID from URL

### Step 2: Environment Setup
```bash
git clone <repo>
cd mercor-tooling
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
```

### Step 3: Initial Data Load
1. Manually enter test applicant data or import CSV
2. Ensure all three child tables have linked records

### Step 4: Run Pipeline
```bash
# Compress applicants
python compress.py --mode=full

# Shortlist candidates
python shortlist.py

# Run LLM evaluation
python llm_eval.py
```

### Step 5: Verify Results
1. Check Applicants table for Compressed JSON
2. Check Shortlisted Leads table for new entries
3. Check LLM Summary, LLM Score, LLM Follow-Ups fields

---

## 17. Troubleshooting

### Common Issues

**Issue**: `pyairtable.api.retrying.RateLimitError`
**Solution**: Reduce batch size, add delays between requests

**Issue**: LLM API timeout
**Solution**: Increase timeout, reduce token limit, check network

**Issue**: JSON parsing errors in decompress
**Solution**: Validate Compressed JSON format, check for corrupted data

**Issue**: Missing linked records
**Solution**: Verify Applicant ID links are correct, re-run compress

**Issue**: Shortlist criteria not working
**Solution**: Check date parsing, verify currency normalization, review logs

---

## Appendix: Sample Data

### Sample Applicant JSON
```json
{
  "applicant_id": "recABC123",
  "personal": {
    "full_name": "John Smith",
    "email": "john.smith@email.com",
    "location": "San Francisco, US",
    "linkedin": "https://linkedin.com/in/johnsmith"
  },
  "experience": [
    {
      "company": "Google",
      "title": "Senior Software Engineer",
      "start": "2019-03-01",
      "end": null,
      "technologies": ["Python", "Kubernetes", "TensorFlow"]
    },
    {
      "company": "Startup Inc",
      "title": "Full Stack Developer",
      "start": "2017-06-15",
      "end": "2019-02-28",
      "technologies": ["React", "Node.js", "PostgreSQL"]
    }
  ],
  "salary": {
    "preferred_rate": 90,
    "minimum_rate": 75,
    "currency": "USD",
    "availability": 30
  },
  "metadata": {
    "compressed_at": "2026-01-15T14:22:33Z",
    "version": "1.0"
  }
}
```

### Sample LLM Output
```
Summary: Senior SWE with 7 total years experience including 5 years at Google leading ML infrastructure. Expert in Python, Kubernetes, TensorFlow. Seeks 30 hrs/week at $90/hour. San Francisco-based. Strong technical profile with Tier-1 company background.

Score: 9

Issues: Current role end date is null - confirm if still employed at Google and availability timeline

Follow-Ups:
- Are you currently employed at Google or available immediately?
- What is the team size you currently lead at Google?
- Can you provide examples of ML systems you have built at scale?
```
