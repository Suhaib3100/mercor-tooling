// Airtable Script: Auto-Shortlist Candidates
// Add this to Airtable's Scripting Extension

// Configuration - matching your Python config
const SHORTLIST_CRITERIA = {
    min_experience_years: 3,
    max_hourly_rate_usd: 150,
    approved_locations: ['USA', 'CANADA', 'UK', 'GERMANY', 'INDIA']
};

// Get tables
const applicationsTable = base.getTable('Applications');
const shortlistedTable = base.getTable('Shortlisted Leads');

// Get all records
const applications = await applicationsTable.selectRecordsAsync();
const shortlistedRecords = await shortlistedTable.selectRecordsAsync();

// Helper: Calculate years of experience
function calculateExperienceYears(experiences) {
    let totalMonths = 0;
    for (let exp of experiences) {
        if (exp.start) {
            const start = new Date(exp.start);
            const end = exp.end ? new Date(exp.end) : new Date();
            const months = (end - start) / (1000 * 60 * 60 * 24 * 30);
            totalMonths += months;
        }
    }
    return totalMonths / 12;
}

// Helper: Normalize location
function normalizeLocation(location) {
    if (!location) return '';
    const loc = location.toUpperCase();
    if (loc.includes('USA') || loc.includes('UNITED STATES') || loc.includes('US')) return 'USA';
    if (loc.includes('CANADA')) return 'CANADA';
    if (loc.includes('UK') || loc.includes('UNITED KINGDOM') || loc.includes('BRITAIN')) return 'UK';
    if (loc.includes('GERMANY') || loc.includes('DEUTSCHLAND')) return 'GERMANY';
    if (loc.includes('INDIA')) return 'INDIA';
    return loc;
}

// Helper: Convert rate to USD
function convertToUSD(rate, currency) {
    const rates = { 'USD': 1, 'EUR': 1.1, 'GBP': 1.25, 'INR': 0.012, 'CAD': 0.75 };
    return rate * (rates[currency] || 1);
}

// Process each application
let shortlisted = 0;
let rejected = 0;

for (let app of applications.records) {
    const appId = app.getCellValue('Application ID');
    const compressedJson = app.getCellValue('Compressed JSON');
    
    // Skip if no compressed data
    if (!compressedJson) {
        console.log(`Skipping ${appId} - no compressed JSON`);
        continue;
    }
    
    // Skip if already processed
    const currentStatus = app.getCellValue('Shortlist Status');
    if (currentStatus) {
        console.log(`Skipping ${appId} - already processed: ${currentStatus}`);
        continue;
    }
    
    const data = JSON.parse(compressedJson);
    
    // Check criteria
    const experienceYears = calculateExperienceYears(data.experience || []);
    const location = normalizeLocation(data.personal?.location);
    const rateUSD = convertToUSD(
        data.salary?.preferred_rate || 0, 
        data.salary?.currency || 'USD'
    );
    
    const meetsExperience = experienceYears >= SHORTLIST_CRITERIA.min_experience_years;
    const meetsRate = rateUSD <= SHORTLIST_CRITERIA.max_hourly_rate_usd;
    const meetsLocation = SHORTLIST_CRITERIA.approved_locations.includes(location);
    
    const isShortlisted = meetsExperience && meetsRate && meetsLocation;
    
    let reason = '';
    if (!meetsExperience) reason += `Experience: ${experienceYears.toFixed(1)} years (need ${SHORTLIST_CRITERIA.min_experience_years}). `;
    if (!meetsRate) reason += `Rate: $${rateUSD.toFixed(0)}/hr USD (max $${SHORTLIST_CRITERIA.max_hourly_rate_usd}). `;
    if (!meetsLocation) reason += `Location: ${location} not in approved list. `;
    
    if (isShortlisted) {
        reason = `✓ Experience: ${experienceYears.toFixed(1)} years. Rate: $${rateUSD.toFixed(0)}/hr. Location: ${location}`;
        
        // Create Shortlisted Lead record
        await shortlistedTable.createRecordAsync({
            'Lead Name': data.personal?.name || appId,
            'Source': { name: 'Mercor Platform' },
            'Shortlist Reason': reason,
            'Applicants': [{ id: app.id }]
        });
        
        shortlisted++;
    } else {
        rejected++;
    }
    
    // Update application status
    await applicationsTable.updateRecordAsync(app.id, {
        'Shortlist Status': isShortlisted ? 'Shortlisted' : 'Rejected'
    });
    
    console.log(`${appId}: ${isShortlisted ? 'SHORTLISTED' : 'REJECTED'} - ${reason}`);
}

output.text(`Shortlist complete! ${shortlisted} shortlisted, ${rejected} rejected`);
