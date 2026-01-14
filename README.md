# Mercor Application Pipeline

An automated system for managing contractor applications with Airtable integration, intelligent shortlisting, and LLM-powered candidate evaluation.

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Airtable      │────▶│  Webhook Server  │────▶│   OpenAI API    │
│   (5 Tables)    │◀────│  (Flask/Python)  │◀────│   (GPT-4o)      │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

### Pipeline Flow
1. **New Application** → Airtable triggers webhook
2. **Compress** → Aggregates data from linked tables into JSON
3. **Shortlist** → Evaluates against criteria (experience, rate, location)
4. **LLM Eval** → GPT-4o scores and summarizes candidate

---

## 📊 Airtable Schema

### Tables

| Table | Purpose |
|-------|---------|
| **Applications** | Main applicant records with compressed JSON, LLM results |
| **Personal Details** | Name, email, location, LinkedIn (linked to Applications) |
| **Work Experience** | Job history with technologies (linked to Applications) |
| **Salary Preferences** | Hourly rates, currency, availability (linked to Applications) |
| **Shortlisted Leads** | Approved candidates with reasons (linked to Applications) |

### Key Fields in Applications Table
- `Application ID` - Unique identifier
- `Compressed JSON` - All applicant data as JSON blob
- `Shortlist Status` - "Shortlisted" or "Rejected"
- `LLM Score` - 1-10 rating from GPT-4o
- `LLM Summary` - AI-generated candidate summary
- `LLM Follow-Ups` - Suggested interview questions

---

## 🚀 Webhook API

**Base URL:** `http://136.111.17.248`

### Endpoints

#### `POST /webhook/new-application`
Full pipeline - compress, shortlist, and LLM evaluate.

```bash
curl -X POST http://136.111.17.248/webhook/new-application \
  -H "Content-Type: application/json" \
  -d '{"record_id": "recXXXXXXXXX"}'
```

**Response:**
```json
{
  "status": "processing",
  "record_id": "recXXXXXXXXX",
  "message": "Pipeline started in background"
}
```

---

#### `POST /webhook/compress`
Compress applicant data only.

```bash
curl -X POST http://136.111.17.248/webhook/compress \
  -H "Content-Type: application/json" \
  -d '{"record_id": "recXXXXXXXXX"}'
```

**Response:**
```json
{"status": "compressed", "record_id": "recXXXXXXXXX"}
```

---

#### `POST /webhook/shortlist`
Run shortlist evaluation only.

```bash
curl -X POST http://136.111.17.248/webhook/shortlist \
  -H "Content-Type: application/json" \
  -d '{"record_id": "recXXXXXXXXX"}'
```

**Response:**
```json
{"status": "shortlisted", "record_id": "recXXXXXXXXX"}
```

---

#### `POST /webhook/llm-eval`
Run LLM evaluation only.

```bash
curl -X POST http://136.111.17.248/webhook/llm-eval \
  -H "Content-Type: application/json" \
  -d '{"record_id": "recXXXXXXXXX"}'
```

**Response:**
```json
{"status": "evaluated", "record_id": "recXXXXXXXXX"}
```

---

#### `GET /health`
Health check endpoint.

```bash
curl http://136.111.17.248/health
```

**Response:**
```json
{"status": "ok", "service": "mercor-pipeline"}
```

---

#### `GET /`
API documentation.

```bash
curl http://136.111.17.248/
```

---

## ⚙️ Shortlist Criteria

Candidates are automatically shortlisted if they meet ALL criteria:

| Criteria | Requirement |
|----------|-------------|
| Experience | ≥ 3 years total |
| Hourly Rate | ≤ $150 USD equivalent |
| Location | USA, Canada, UK, Germany, or India |

**Bonus:** Candidates from Tier-1 companies (Google, Apple, Microsoft, Amazon, Meta, Netflix, Tesla, SpaceX, IBM, Intel) get highlighted.

---

## 🤖 LLM Evaluation

GPT-4o evaluates shortlisted candidates and provides:
- **Score (1-10):** Overall fit rating
- **Summary:** 2-3 sentence assessment
- **Follow-up Questions:** 3 suggested interview questions

---

## 📁 Project Structure

```
mercor-tooling/
├── src/
│   ├── __init__.py
│   ├── config.py           # API keys, table names, criteria
│   ├── utils.py            # Logging, date parsing, validation
│   ├── airtable_client.py  # Airtable API wrapper
│   ├── compress.py         # Data compression logic
│   ├── decompress.py       # JSON to tables restoration
│   ├── shortlist.py        # Shortlisting criteria evaluation
│   └── llm_eval.py         # OpenAI integration
├── airtable_scripts/       # Scripts for Airtable Scripting Extension
├── tests/                  # Unit tests
├── webhook_server.py       # Flask webhook server
├── reset_data.py           # Test data population script
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (not in git)
├── mercor-pipeline.service # Systemd service file
├── nginx.conf              # Nginx reverse proxy config
└── README.md
```

---

## 🛠️ Local Development

### Setup

```bash
# Clone repository
git clone https://github.com/Suhaib3100/mercor-tooling.git
cd mercor-tooling

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your API keys
```

### Environment Variables

```env
AIRTABLE_API_KEY=pat...
AIRTABLE_BASE_ID=app...
LLM_API_KEY=sk-proj-...
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
```

### Run Pipeline Manually

```bash
# Compress all applicants
python3 -m src.compress

# Shortlist candidates
python3 -m src.shortlist

# LLM evaluation
python3 -m src.llm_eval
```

### Run Webhook Server Locally

```bash
python3 webhook_server.py
# Server runs on http://localhost:8080
```

---

## 🌐 Production Deployment (GCP VM)

### Quick Setup

```bash
# SSH into VM
ssh user@your-vm-ip

# Clone and setup
git clone https://github.com/Suhaib3100/mercor-tooling.git
cd mercor-tooling
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env with your keys
nano .env

# Setup systemd service
sudo cp mercor-pipeline.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mercor-pipeline
sudo systemctl start mercor-pipeline

# Setup Nginx
sudo cp nginx.conf /etc/nginx/sites-available/mercor-pipeline
sudo ln -sf /etc/nginx/sites-available/mercor-pipeline /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo systemctl restart nginx
```

### Useful Commands

```bash
# Check status
sudo systemctl status mercor-pipeline

# View logs
sudo journalctl -u mercor-pipeline -f

# Restart service
sudo systemctl restart mercor-pipeline
```

---

## 🔗 Airtable Automation Setup

1. Go to Airtable → **Automations** tab
2. Create new automation:
   - **Trigger:** When record created in "Applications"
   - **Action:** Send webhook
3. Configure webhook:
   - **URL:** `http://YOUR-SERVER-IP/webhook/new-application`
   - **Method:** POST
   - **Body:** `{"record_id": "{{Record ID}}"}`
4. Turn on automation

---

## 📝 API Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 202 | Accepted (processing in background) |
| 400 | Bad request (missing record_id) |
| 404 | Record not found |
| 500 | Server error |

---

## 🧪 Testing

### Test Webhook Endpoints

```bash
# Health check
curl http://136.111.17.248/health

# Test with a real record ID from Airtable
curl -X POST http://136.111.17.248/webhook/new-application \
  -H "Content-Type: application/json" \
  -d '{"record_id": "recANTrJO2vkL5tol"}'
```

### Reset Test Data

```bash
python3 reset_data.py
```

---

## 📄 License

MIT License

---

## 👤 Author

Suhaib SZ - [GitHub](https://github.com/Suhaib3100)
