# Airtable Automations & Scripts Setup

This folder contains JavaScript scripts to run inside Airtable's **Scripting Extension**.

## How to Add Scripts to Airtable

### Step 1: Install Scripting Extension
1. Open your Airtable base
2. Click **Extensions** (puzzle icon) in top-right
3. Click **+ Add an extension**
4. Search for **"Scripting"** and add it

### Step 2: Add Each Script
1. Click the Scripting extension
2. Click **"Add a script"** or paste into existing
3. Copy the content from each `.js` file below
4. Click **Run** to execute

---

## Scripts Included

### 1. `compress_script.js` - Compress Applicant Data
- **Purpose**: Aggregates data from Personal Details, Work Experience, and Salary Preferences into a JSON blob
- **When to run**: After adding new applicants or updating their data
- **Output**: Updates "Compressed JSON" field in Applications table

### 2. `shortlist_script.js` - Auto-Shortlist Candidates
- **Purpose**: Evaluates candidates against shortlist criteria
- **Criteria**:
  - Minimum 3 years experience
  - Max $150/hr USD rate
  - Location in: USA, Canada, UK, Germany, India
- **When to run**: After compression is complete
- **Output**: Updates "Shortlist Status" and creates records in Shortlisted Leads

### 3. `llm_eval_prompt_script.js` - Generate LLM Prompts
- **Purpose**: Creates prompts for ChatGPT/Claude to evaluate candidates
- **Note**: Airtable scripts cannot call external APIs, so this generates prompts for manual use
- **When to run**: After shortlisting
- **Output**: Displays prompts to copy/paste into LLM

### 4. `decompress_script.js` - Restore from JSON
- **Purpose**: Decompresses JSON back to linked table records
- **When to run**: If you need to restore/update data from compressed format
- **Output**: Creates/updates Personal Details, Work Experience, Salary Preferences

---

## Setting Up Automations

Go to **Automations** tab in Airtable to create these:

### Automation 1: Auto-Compress New Applications
```
Trigger: When record is created in "Applications"
Action: Run script → compress_script.js
```

### Automation 2: Auto-Shortlist After Compression
```
Trigger: When "Compressed JSON" field is updated in "Applications"
Condition: Compressed JSON is not empty
Action: Run script → shortlist_script.js
```

### Automation 3: Notify on Shortlist
```
Trigger: When "Shortlist Status" changes to "Shortlisted"
Action: Send email notification / Slack message
```

---

## Alternative: Python Scripts (External)

For full LLM integration with OpenAI API, use the Python scripts in `src/`:

```bash
# Activate virtual environment
source venv/bin/activate

# Run full pipeline
python3 -m src.compress      # Compress data
python3 -m src.shortlist     # Auto-shortlist
python3 -m src.llm_eval      # LLM evaluation (requires OpenAI API key)
```

The Python scripts provide more powerful automation including:
- Direct OpenAI API integration for LLM evaluation
- Rate limiting and retry logic
- Change detection to avoid re-processing
