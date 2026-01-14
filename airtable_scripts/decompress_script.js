// Airtable Script: Decompress JSON to Tables
// Restores data from Compressed JSON back to linked tables

const applicationsTable = base.getTable('Applications');
const personalTable = base.getTable('Personal Details');
const experienceTable = base.getTable('Work Experience');
const salaryTable = base.getTable('Salary Preferences');

const applications = await applicationsTable.selectRecordsAsync();

// Ask user which application to decompress
const appChoices = applications.records
    .filter(r => r.getCellValue('Compressed JSON'))
    .map(r => ({
        label: `${r.getCellValue('Application ID')}`,
        value: r.id
    }));

if (appChoices.length === 0) {
    output.text('No applications with Compressed JSON found!');
    return;
}

const selectedApp = await input.buttonsAsync('Select application to decompress:', appChoices);
const app = applications.getRecord(selectedApp);
const compressedJson = app.getCellValue('Compressed JSON');

if (!compressedJson) {
    output.text('No compressed JSON found for this application!');
    return;
}

const data = JSON.parse(compressedJson);
output.markdown(`## Decompressing: ${data.applicant_id}`);

// Create/Update Personal Details
if (data.personal) {
    const existingPersonal = app.getCellValue('Personal Details');
    
    if (existingPersonal && existingPersonal.length > 0) {
        // Update existing
        await personalTable.updateRecordAsync(existingPersonal[0].id, {
            'Full Name': data.personal.name,
            'Email': data.personal.email,
            'Location': data.personal.location,
            'LinkedIn URL': data.personal.linkedin
        });
        output.text(`✓ Updated Personal Details: ${data.personal.name}`);
    } else {
        // Create new
        const newPersonalId = await personalTable.createRecordAsync({
            'Full Name': data.personal.name,
            'Email': data.personal.email,
            'Location': data.personal.location,
            'LinkedIn URL': data.personal.linkedin,
            'Application ID': [{ id: app.id }]
        });
        output.text(`✓ Created Personal Details: ${data.personal.name}`);
    }
}

// Create Work Experience records
if (data.experience && data.experience.length > 0) {
    for (let exp of data.experience) {
        // Check if record exists by record_id
        const existingExp = app.getCellValue('Work Experience') || [];
        const exists = exp.record_id && existingExp.some(e => e.id === exp.record_id);
        
        if (exists) {
            await experienceTable.updateRecordAsync(exp.record_id, {
                'Company Name': exp.company,
                'Job Title': exp.title,
                'Start Date': exp.start,
                'End Date': exp.end
            });
            output.text(`✓ Updated Experience: ${exp.company}`);
        } else {
            await experienceTable.createRecordAsync({
                'Company Name': exp.company,
                'Job Title': exp.title,
                'Start Date': exp.start,
                'End Date': exp.end || null,
                'Application ID': [{ id: app.id }]
            });
            output.text(`✓ Created Experience: ${exp.company}`);
        }
    }
}

// Create/Update Salary Preferences
if (data.salary) {
    const existingSalary = app.getCellValue('Salary Preferences');
    
    const salaryFields = {
        'Preferred Hourly Rate': data.salary.preferred_rate,
        'Minimum Hourly Rate': data.salary.minimum_rate,
        'Currency': { name: data.salary.currency || 'USD' },
        'Weekly Availability': data.salary.availability
    };
    
    if (existingSalary && existingSalary.length > 0) {
        await salaryTable.updateRecordAsync(existingSalary[0].id, salaryFields);
        output.text(`✓ Updated Salary Preferences`);
    } else {
        salaryFields['Application ID'] = [{ id: app.id }];
        await salaryTable.createRecordAsync(salaryFields);
        output.text(`✓ Created Salary Preferences`);
    }
}

output.markdown('---');
output.text('Decompression complete!');
