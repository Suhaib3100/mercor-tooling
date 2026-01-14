// Airtable Script: LLM Evaluation (Manual Trigger)
// Note: Airtable scripts cannot call external APIs directly
// This script prepares the prompt for manual LLM evaluation

const applicationsTable = base.getTable('Applications');
const applications = await applicationsTable.selectRecordsAsync();

output.markdown('# LLM Evaluation Prompts');
output.markdown('Copy these prompts to ChatGPT/Claude for evaluation:\n');

for (let app of applications.records) {
    const appId = app.getCellValue('Application ID');
    const status = app.getCellValue('Shortlist Status');
    const compressedJson = app.getCellValue('Compressed JSON');
    
    // Only evaluate shortlisted candidates without LLM scores
    if (status !== 'Shortlisted' || !compressedJson) continue;
    if (app.getCellValue('LLM Score')) {
        console.log(`Skipping ${appId} - already has LLM evaluation`);
        continue;
    }
    
    const data = JSON.parse(compressedJson);
    
    const prompt = `You are evaluating a contractor candidate for a software engineering role.

Candidate Profile:
${JSON.stringify(data, null, 2)}

Please provide:
1. **Score** (1-10): Overall fit score
2. **Summary** (2-3 sentences): Brief assessment of the candidate
3. **Follow-up Questions** (3 bullet points): Questions to ask in interview

Format your response exactly as:
SCORE: [number]
SUMMARY: [text]
FOLLOW_UPS:
- [question 1]
- [question 2]
- [question 3]`;

    output.markdown(`## ${appId}: ${data.personal?.name || 'Unknown'}`);
    output.markdown('```');
    output.text(prompt);
    output.markdown('```\n');
}

output.markdown('---');
output.markdown('After getting LLM responses, update the Applications table with:');
output.markdown('- **LLM Score**: The score (1-10)');
output.markdown('- **LLM Summary**: The summary text');
output.markdown('- **LLM Follow-Ups**: The follow-up questions');
