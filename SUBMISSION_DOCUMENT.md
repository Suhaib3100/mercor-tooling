# Mercor Mini-Interview Task - Submission Document

---

## 📋 Project Overview

**Task:** Build an Airtable-based data model and automation system for managing contractor applications with intelligent shortlisting and LLM-powered evaluation.

**Submitted by:** Suhaib SZ  
**Date:** January 15, 2026

---

## ✅ Requirements Completed

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Multi-table Airtable schema | ✅ Done | 5 linked tables created |
| Data compression to JSON | ✅ Done | Python script + API endpoint |
| Data decompression from JSON | ✅ Done | Python script |
| Auto-shortlisting rules | ✅ Done | Experience, rate, location criteria |
| LLM evaluation & enrichment | ✅ Done | GPT-4o integration |
| Webhook automation server | ✅ Done | Flask server on GCP VM |

---

## 🔗 Submission Links

### 1. Airtable Base (Share Link)
```
[PASTE YOUR AIRTABLE SHARE LINK HERE]
```

### 2. GitHub Repository
```
https://github.com/Suhaib3100/mercor-tooling
```

### 3. Webhook Server (Live)
```
http://[YOUR-SERVER-IP]/webhook/new-application
```

**Health Check:** `http://[YOUR-SERVER-IP]/health`

---

## 📊 Airtable Schema

### Tables Created

#### 1. Applications (Main Table)
| Field | Type | Purpose |
|-------|------|---------|
| Application ID | Text | Unique identifier |
| Compressed JSON | Long Text | Aggregated applicant data |
| Shortlist Status | Single Select | "Shortlisted" / "Rejected" |
| LLM Score | Number | AI rating (1-10) |
| LLM Summary | Long Text | AI-generated assessment |
| LLM Follow-Ups | Long Text | Suggested interview questions |
| Personal Details | Link | → Personal Details table |
| Work Experience | Link | → Work Experience table |
| Salary Preferences | Link | → Salary Preferences table |

#### 2. Personal Details
| Field | Type |
|-------|------|
| Full Name | Text |
| Email | Email |
| Location | Text |
| LinkedIn URL | URL |

#### 3. Work Experience
| Field | Type |
|-------|------|
| Company Name | Text |
| Job Title | Text |
| Start Date | Date |
| End Date | Date |
| Technologies | Multiple Select |

#### 4. Salary Preferences
| Field | Type |
|-------|------|
| Preferred Hourly Rate | Number |
| Minimum Hourly Rate | Number |
| Currency | Single Select (USD, EUR, GBP, INR, CAD) |
| Weekly Availability | Number |

#### 5. Shortlisted Leads
| Field | Type |
|-------|------|
| Lead Name | Text |
| Source | Single Select |
| Shortlist Reason | Long Text |
| Applicants | Link → Applications |

**📸 Screenshot - Airtable Tables:**
```
[INSERT SCREENSHOT OF AIRTABLE BASE WITH ALL TABLES]
```

---

## ⚙️ Automation Pipeline

### Pipeline Flow
```
New Application → Compress Data → Shortlist Evaluation → LLM Analysis → Update Airtable
```

### Shortlist Criteria
| Criteria | Requirement |
|----------|-------------|
| Experience | ≥ 3 years total |
| Hourly Rate | ≤ $150 USD equivalent |
| Location | USA, Canada, UK, Germany, or India |

### LLM Evaluation (GPT-4o)
- **Score:** 1-10 overall fit rating
- **Summary:** 2-3 sentence candidate assessment
- **Follow-ups:** 3 suggested interview questions

---

## 🌐 Webhook API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/webhook/new-application` | POST | Full pipeline (compress → shortlist → LLM) |
| `/webhook/compress` | POST | Compress data only |
| `/webhook/shortlist` | POST | Shortlist evaluation only |
| `/webhook/llm-eval` | POST | LLM evaluation only |
| `/health` | GET | Health check |

### Example API Call
```bash
curl -X POST http://[YOUR-SERVER-IP]/webhook/new-application \
  -H "Content-Type: application/json" \
  -d '{"record_id": "recXXXXXXXXX"}'
```

### Response
```json
{
  "status": "processing",
  "record_id": "recXXXXXXXXX",
  "message": "Pipeline started in background"
}
```

**📸 Screenshot - Webhook Health Check:**
```
[INSERT SCREENSHOT OF curl http://[YOUR-SERVER-IP]/health RESPONSE]
```

---

## 🖥️ Server Deployment

**Platform:** Google Cloud Platform (Compute Engine)  
**Stack:** Python 3.11, Flask, Gunicorn, Nginx  
**Service:** Running as systemd service (auto-restart enabled)

### Server Commands
```bash
# Check service status
sudo systemctl status mercor-pipeline

# View logs
sudo journalctl -u mercor-pipeline -f

# Restart service
sudo systemctl restart mercor-pipeline
```

**📸 Screenshot - Server Running:**
```
[INSERT SCREENSHOT OF sudo systemctl status mercor-pipeline]
```

**📸 Screenshot - Pipeline Logs:**
```
[INSERT SCREENSHOT OF sudo journalctl -u mercor-pipeline SHOWING SUCCESSFUL PROCESSING]
```

---

## 📁 Code Structure

```
mercor-tooling/
├── src/
│   ├── config.py           # API keys, table names, criteria
│   ├── utils.py            # Helper functions
│   ├── airtable_client.py  # Airtable API wrapper
│   ├── compress.py         # Data compression logic
│   ├── decompress.py       # JSON to tables restoration
│   ├── shortlist.py        # Shortlisting evaluation
│   └── llm_eval.py         # OpenAI GPT-4o integration
├── webhook_server.py       # Flask webhook server
├── reset_data.py           # Test data population
├── requirements.txt        # Python dependencies
├── mercor-pipeline.service # Systemd service config
├── nginx.conf              # Nginx reverse proxy config
├── README.md               # Project documentation
└── AIRTABLE_SETUP.md       # Airtable setup guide
```

---

## 🧪 Test Results

### Sample Data
| Applicant | Location | Experience | Rate | Status | LLM Score |
|-----------|----------|------------|------|--------|-----------|
| Siresh Reddy | India | 7+ years | ₹75/hr | Shortlisted | 8/10 |
| Suhaib SZ | USA | 8+ years | $95/hr | Shortlisted | 8/10 |
| Alex Chen | Canada | 5+ years | $85/hr | Shortlisted | 8/10 |

**📸 Screenshot - Applications Table with Results:**
```
[INSERT SCREENSHOT OF APPLICATIONS TABLE SHOWING COMPRESSED JSON, STATUS, LLM FIELDS]
```

**📸 Screenshot - Shortlisted Leads Table:**
```
[INSERT SCREENSHOT OF SHORTLISTED LEADS TABLE]
```

---

## ⚠️ Note on Airtable Automations

> **Airtable's free plan does not support:**
> - Webhook actions in automations
> - Custom scripts in automations (requires Team/Business plan)
>
> **Solution implemented:**  
> The automation runs via an **external Python webhook server** hosted on GCP. The pipeline can be triggered via:
> 1. Direct API call to the webhook endpoint
> 2. Manual command-line execution
>
> For production use with Airtable Team/Business plan, the webhook can be called directly from Airtable's "When record created" automation.

---

## 🎥 Demo

### Running the Pipeline

**Step 1:** Trigger webhook for a record
```bash
curl -X POST http://[YOUR-SERVER-IP]/webhook/new-application \
  -H "Content-Type: application/json" \
  -d '{"record_id": "recANTrJO2vkL5tol"}'
```

**Step 2:** Check server logs
```bash
sudo journalctl -u mercor-pipeline -f
```

**Step 3:** Verify in Airtable
- Compressed JSON populated ✅
- Shortlist Status set ✅
- LLM Score/Summary filled ✅
- Shortlisted Leads record created ✅

**📸 Screenshot - Complete Pipeline Execution:**
```
[INSERT SCREENSHOT OF TERMINAL SHOWING FULL PIPELINE RUN]
```

---

## 📝 Summary

| Component | Description |
|-----------|-------------|
| **Data Model** | 5 linked Airtable tables with proper relationships |
| **Compression** | Aggregates all linked data into JSON blob |
| **Decompression** | Restores JSON data back to linked tables |
| **Shortlisting** | Rule-based evaluation (experience, rate, location) |
| **LLM Enrichment** | GPT-4o scoring, summary, and follow-up questions |
| **Automation** | Webhook server with REST API endpoints |
| **Deployment** | Production-ready on GCP with Nginx + Gunicorn |

---

**Thank you for reviewing my submission!**

---
