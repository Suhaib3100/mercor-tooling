# Render.com Deployment Guide

## Step 1: Push Code to GitHub

```bash
# Initialize git if not already
git init
git add .
git commit -m "Add webhook server for Airtable automation"

# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/mercor-tooling.git
git push -u origin main
```

## Step 2: Deploy on Render

1. Go to **https://render.com** and sign up/login
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub account
4. Select the **mercor-tooling** repository
5. Configure:
   - **Name**: `mercor-pipeline`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn webhook_server:app`
   - **Instance Type**: Free

## Step 3: Add Environment Variables

In Render dashboard, go to **Environment** tab and add:

| Key | Value |
|-----|-------|
| `AIRTABLE_API_KEY` | `patfOYUrcaU5O6ZId.1bc...` (your token) |
| `AIRTABLE_BASE_ID` | `appjkWw6Z1fgtGTgi` |
| `LLM_API_KEY` | `sk-proj-...` (your OpenAI key) |
| `LLM_PROVIDER` | `openai` |
| `LLM_MODEL` | `gpt-4o` |

## Step 4: Get Your Webhook URL

After deploy, Render gives you a URL like:
```
https://mercor-pipeline.onrender.com
```

Your webhook endpoints will be:
- `https://mercor-pipeline.onrender.com/webhook/new-application`
- `https://mercor-pipeline.onrender.com/webhook/compress`
- `https://mercor-pipeline.onrender.com/webhook/shortlist`
- `https://mercor-pipeline.onrender.com/webhook/llm-eval`

## Step 5: Configure Airtable Automation

1. Go to Airtable → **Automations** tab
2. Create new automation:
   - **Trigger**: "When record created" → Select "Applications" table
3. Add action: **"Send webhook request"** (under Integrations)
4. Configure:
   - **URL**: `https://mercor-pipeline.onrender.com/webhook/new-application`
   - **Method**: POST
   - **Headers**: `Content-Type: application/json`
   - **Body**: 
     ```json
     {
       "record_id": "{{Record ID}}"
     }
     ```
5. Turn on the automation!

## Testing

After deployment, test with:
```bash
curl https://mercor-pipeline.onrender.com/health
```

Should return:
```json
{"status": "ok", "service": "mercor-pipeline"}
```

## Notes

- Free tier may have cold starts (first request takes ~30s)
- Logs available in Render dashboard
- Auto-deploys when you push to GitHub
