# Airtable Setup Guide

Complete step-by-step guide for setting up tables, automations, and scripts in Airtable.

---

## 📊 Part 1: Create Tables

### Table 1: Applications (Main Table)

1. Create new table named **"Applications"**
2. Add these fields:

| Field Name | Field Type | Notes |
|------------|------------|-------|
| Application ID | Single line text | Primary field |
| Compressed JSON | Long text | Stores aggregated JSON |
| Shortlist Status | Single select | Options: "Shortlisted", "Rejected" |
| LLM Score | Number | 1-10 rating |
| LLM Summary | Long text | AI-generated summary |
| LLM Follow-Ups | Long text | Interview questions |
| Personal Details | Link to another record | Link to Personal Details table |
| Work Experience | Link to another record | Link to Work Experience table |
| Salary Preferences | Link to another record | Link to Salary Preferences table |
| Shortlisted Leads | Link to another record | Link to Shortlisted Leads table |

---

### Table 2: Personal Details

1. Create new table named **"Personal Details"**
2. Add these fields:

| Field Name | Field Type |
|------------|------------|
| Full Name | Single line text |
| Email | Email |
| Location | Single line text |
| LinkedIn URL | URL |
| Application ID | Link to Applications |

---

### Table 3: Work Experience

1. Create new table named **"Work Experience"**
2. Add these fields:

| Field Name | Field Type | Notes |
|------------|------------|-------|
| Company Name | Single line text | |
| Job Title | Single line text | |
| Start Date | Date | |
| End Date | Date | Leave empty if current |
| Technologies | Multiple select | Add options: Python, JavaScript, React, etc. |
| Application ID | Link to Applications | |

---

### Table 4: Salary Preferences

1. Create new table named **"Salary Preferences"**
2. Add these fields:

| Field Name | Field Type | Notes |
|------------|------------|-------|
| Preferred Hourly Rate | Number | |
| Minimum Hourly Rate | Number | |
| Currency | Single select | Options: USD, EUR, GBP, INR, CAD |
| Weekly Availability | Number | Hours per week |
| Application ID | Link to Applications | |

---

### Table 5: Shortlisted Leads

1. Create new table named **"Shortlisted Leads"**
2. Add these fields:

| Field Name | Field Type | Notes |
|------------|------------|-------|
| Lead Name | Single line text | |
| Source | Single select | Options: Mercor Platform, Referral, Direct |
| Shortlist Reason | Long text | Why they were shortlisted |
| Applicants | Link to Applications | |

---

## 🔄 Part 2: Create Automation

### Step-by-Step: Auto-Process New Applications

#### Step 1: Open Automations
1. Click **"Automations"** tab at top of Airtable
2. Click **"+ Create automation"**

#### Step 2: Set Trigger
1. Click **"+ Add trigger"**
2. Select **"When record created"**
3. Configure:
   - **Table:** Applications
4. Click **"Done"**

![Trigger Setup](https://i.imgur.com/placeholder.png)

#### Step 3: Add Webhook Action
1. Click **"+ Add action"**
2. Scroll down to **"Integrations"** section
3. Select **"Send webhook"**

#### Step 4: Configure Webhook
Fill in these fields:

| Setting | Value |
|---------|-------|
| **URL** | `http://YOUR-SERVER-IP/webhook/new-application` |
| **Method** | POST |
| **Content type** | application/json |

#### Step 5: Set Request Body
1. Click on **"Body"** field
2. Click **"+ Insert"** button (blue plus icon)
3. Type this JSON, inserting the Record ID:

```json
{"record_id": "CLICK_PLUS_AND_SELECT_RECORD_ID"}
```

**How to insert Record ID:**
1. Delete the placeholder text
2. Type: `{"record_id": "`
3. Click the blue **+** button
4. Select **"Record ID"** from the trigger
5. Type: `"}`

Final result should look like:
```
{"record_id": "rec..."}  (with dynamic value)
```

#### Step 6: Test the Automation
1. Click **"Test action"**
2. Should see: `{"status": "processing", "record_id": "...", "message": "Pipeline started in background"}`

#### Step 7: Turn On
1. Click **"Turn on automation"** (top right, toggle switch)
2. Name it: "Auto-Process New Applications"

---

## 📜 Part 3: Add Scripts (Optional - Free Tier)

Scripts run manually, not automatically (automations with scripts need paid plan).

### Step 1: Add Scripting Extension
1. Go to **Data** tab
2. Look for **Extensions** panel on right side
3. If not visible, click the **puzzle icon** or **"Extensions"** in toolbar
4. Click **"+ Add an extension"**
5. Search **"Scripting"**
6. Click **"Add"**

### Step 2: Add Compress Script

1. In Scripting extension, click **"Add a script"**
2. Name it: **"Compress All Applicants"**
3. Paste this code:

```javascript
// Compress All Applicants Script
const applicationsTable = base.getTable('Applications');
const personalTable = base.getTable('Personal Details');
const experienceTable = base.getTable('Work Experience');
const salaryTable = base.getTable('Salary Preferences');

const applications = await applicationsTable.selectRecordsAsync();
const personalRecords = await personalTable.selectRecordsAsync();
const experienceRecords = await experienceTable.selectRecordsAsync();
const salaryRecords = await salaryTable.selectRecordsAsync();

let compressed = 0;

for (let app of applications.records) {
    const appId = app.getCellValue('Application ID');
    
    // Skip if already compressed
    if (app.getCellValue('Compressed JSON')) {
        console.log(`Skipping ${appId} - already compressed`);
        continue;
    }
    
    // Get Personal Details
    const personalLinks = app.getCellValue('Personal Details') || [];
    let personalData = null;
    if (personalLinks.length > 0) {
        const rec = personalRecords.getRecord(personalLinks[0].id);
        personalData = {
            name: rec.getCellValue('Full Name'),
            email: rec.getCellValue('Email'),
            location: rec.getCellValue('Location'),
            linkedin: rec.getCellValue('LinkedIn URL')
        };
    }
    
    // Get Work Experience
    const expLinks = app.getCellValue('Work Experience') || [];
    const experienceData = expLinks.map(link => {
        const rec = experienceRecords.getRecord(link.id);
        const techs = rec.getCellValue('Technologies') || [];
        return {
            company: rec.getCellValue('Company Name'),
            title: rec.getCellValue('Job Title'),
            start: rec.getCellValue('Start Date'),
            end: rec.getCellValue('End Date'),
            technologies: techs.map(t => t.name)
        };
    });
    
    // Get Salary
    const salaryLinks = app.getCellValue('Salary Preferences') || [];
    let salaryData = null;
    if (salaryLinks.length > 0) {
        const rec = salaryRecords.getRecord(salaryLinks[0].id);
        salaryData = {
            preferred_rate: rec.getCellValue('Preferred Hourly Rate'),
            minimum_rate: rec.getCellValue('Minimum Hourly Rate'),
            currency: rec.getCellValue('Currency')?.name || 'USD',
            availability: rec.getCellValue('Weekly Availability')
        };
    }
    
    // Build JSON
    const data = {
        applicant_id: appId,
        record_id: app.id,
        personal: personalData,
        experience: experienceData,
        salary: salaryData
    };
    
    // Update record
    await applicationsTable.updateRecordAsync(app.id, {
        'Compressed JSON': JSON.stringify(data, null, 2)
    });
    
    compressed++;
    console.log(`✓ Compressed ${appId}`);
}

output.text(`Done! Compressed ${compressed} applicants.`);
```

4. Click **"Run"** to test

---

### Step 3: Add Shortlist Script

1. Click **"Add a script"**
2. Name it: **"Shortlist Candidates"**
3. Paste this code:

```javascript
// Shortlist Candidates Script
const CRITERIA = {
    minExperience: 3,
    maxRateUSD: 150,
    approvedLocations: ['USA', 'CANADA', 'UK', 'GERMANY', 'INDIA']
};

const applicationsTable = base.getTable('Applications');
const shortlistedTable = base.getTable('Shortlisted Leads');
const applications = await applicationsTable.selectRecordsAsync();

function calcExperience(experiences) {
    let months = 0;
    for (let exp of experiences) {
        if (exp.start) {
            const start = new Date(exp.start);
            const end = exp.end ? new Date(exp.end) : new Date();
            months += (end - start) / (1000 * 60 * 60 * 24 * 30);
        }
    }
    return months / 12;
}

function normalizeLocation(loc) {
    if (!loc) return '';
    loc = loc.toUpperCase();
    if (loc.includes('USA') || loc.includes('UNITED STATES')) return 'USA';
    if (loc.includes('CANADA')) return 'CANADA';
    if (loc.includes('UK') || loc.includes('UNITED KINGDOM')) return 'UK';
    if (loc.includes('GERMANY')) return 'GERMANY';
    if (loc.includes('INDIA')) return 'INDIA';
    return loc;
}

function toUSD(rate, currency) {
    const rates = { USD: 1, EUR: 1.1, GBP: 1.25, INR: 0.012, CAD: 0.75 };
    return rate * (rates[currency] || 1);
}

let shortlisted = 0, rejected = 0;

for (let app of applications.records) {
    const json = app.getCellValue('Compressed JSON');
    if (!json) continue;
    if (app.getCellValue('Shortlist Status')) continue;
    
    const data = JSON.parse(json);
    const years = calcExperience(data.experience || []);
    const location = normalizeLocation(data.personal?.location);
    const rateUSD = toUSD(data.salary?.preferred_rate || 0, data.salary?.currency);
    
    const passExp = years >= CRITERIA.minExperience;
    const passRate = rateUSD <= CRITERIA.maxRateUSD;
    const passLoc = CRITERIA.approvedLocations.includes(location);
    
    const pass = passExp && passRate && passLoc;
    
    if (pass) {
        await shortlistedTable.createRecordAsync({
            'Lead Name': data.personal?.name || data.applicant_id,
            'Source': { name: 'Mercor Platform' },
            'Shortlist Reason': `Experience: ${years.toFixed(1)}y, Rate: $${rateUSD.toFixed(0)}/hr, Location: ${location}`,
            'Applicants': [{ id: app.id }]
        });
        shortlisted++;
    } else {
        rejected++;
    }
    
    await applicationsTable.updateRecordAsync(app.id, {
        'Shortlist Status': pass ? 'Shortlisted' : 'Rejected'
    });
    
    console.log(`${data.applicant_id}: ${pass ? 'SHORTLISTED' : 'REJECTED'}`);
}

output.text(`Done! ${shortlisted} shortlisted, ${rejected} rejected.`);
```

4. Click **"Run"** to test

---

## ✅ Part 4: Test Everything

### Test 1: Create a New Application Manually
1. Go to **Applications** table
2. Add new record with Application ID: "TEST001"
3. Add linked Personal Details, Work Experience, Salary Preferences
4. If automation is on, webhook triggers automatically

### Test 2: Check Webhook Received
SSH into your server and check logs:
```bash
sudo journalctl -u mercor-pipeline -f
```

### Test 3: Verify Results
After processing, check:
- ✅ Compressed JSON field is populated
- ✅ Shortlist Status is set
- ✅ LLM Score/Summary filled (if shortlisted)
- ✅ New record in Shortlisted Leads (if shortlisted)

---

## 🔧 Troubleshooting

### Automation not triggering?
- Check automation is **turned on** (toggle in top right)
- Check trigger is set to correct table

### Webhook failing?
- Test URL manually: `curl http://YOUR-SERVER-IP/health`
- Check server logs: `sudo journalctl -u mercor-pipeline -f`

### Script errors?
- Check field names match exactly (case-sensitive)
- Make sure all tables have correct linked fields

---

## 📋 Summary

| Component | Purpose | How it Works |
|-----------|---------|--------------|
| **Webhook Automation** | Auto-process new apps | Triggers on new record → calls your server |
| **Compress Script** | Manual compress | Run in Scripting extension |
| **Shortlist Script** | Manual shortlist | Run in Scripting extension |
| **Python Server** | Full pipeline | Handles webhook, runs compress+shortlist+LLM |

---

Your webhook URL: **`http://YOUR-SERVER-IP/webhook/new-application`**
