// Airtable Script: Compress Applicant Data
// Add this to Airtable's Scripting Extension

// Get tables
const applicationsTable = base.getTable('Applications');
const personalTable = base.getTable('Personal Details');
const experienceTable = base.getTable('Work Experience');
const salaryTable = base.getTable('Salary Preferences');

// Get all records
const applications = await applicationsTable.selectRecordsAsync();
const personalRecords = await personalTable.selectRecordsAsync();
const experienceRecords = await experienceTable.selectRecordsAsync();
const salaryRecords = await salaryTable.selectRecordsAsync();

// Process each application
for (let app of applications.records) {
    const appId = app.getCellValue('Application ID');
    
    // Skip if already has compressed JSON
    if (app.getCellValue('Compressed JSON')) {
        console.log(`Skipping ${appId} - already compressed`);
        continue;
    }
    
    // Get linked Personal Details
    const personalLinks = app.getCellValue('Personal Details') || [];
    let personalData = null;
    if (personalLinks.length > 0) {
        const personalRecord = personalRecords.getRecord(personalLinks[0].id);
        personalData = {
            name: personalRecord.getCellValue('Full Name'),
            email: personalRecord.getCellValue('Email'),
            location: personalRecord.getCellValue('Location'),
            linkedin: personalRecord.getCellValue('LinkedIn URL')
        };
    }
    
    // Get linked Work Experience
    const expLinks = app.getCellValue('Work Experience') || [];
    const experienceData = expLinks.map(link => {
        const expRecord = experienceRecords.getRecord(link.id);
        const techs = expRecord.getCellValue('Technologies') || [];
        return {
            company: expRecord.getCellValue('Company Name'),
            title: expRecord.getCellValue('Job Title'),
            start: expRecord.getCellValue('Start Date'),
            end: expRecord.getCellValue('End Date'),
            technologies: techs.map(t => t.name || t)
        };
    });
    
    // Get linked Salary Preferences
    const salaryLinks = app.getCellValue('Salary Preferences') || [];
    let salaryData = null;
    if (salaryLinks.length > 0) {
        const salaryRecord = salaryRecords.getRecord(salaryLinks[0].id);
        salaryData = {
            preferred_rate: salaryRecord.getCellValue('Preferred Hourly Rate'),
            minimum_rate: salaryRecord.getCellValue('Minimum Hourly Rate'),
            currency: salaryRecord.getCellValue('Currency')?.name || 'USD',
            availability: salaryRecord.getCellValue('Weekly Availability')
        };
    }
    
    // Build compressed JSON
    const compressed = {
        applicant_id: appId,
        record_id: app.id,
        personal: personalData,
        experience: experienceData,
        salary: salaryData
    };
    
    // Update the application with compressed JSON
    await applicationsTable.updateRecordAsync(app.id, {
        'Compressed JSON': JSON.stringify(compressed, null, 2)
    });
    
    console.log(`Compressed ${appId}`);
}

output.text('Compression complete!');
