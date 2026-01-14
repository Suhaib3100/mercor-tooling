"""Reset and populate test data for Mercor pipeline demo."""
from src.airtable_client import AirtableClient

def clear_data():
    """Clear all existing test data."""
    client = AirtableClient()
    
    print('Clearing existing data...')
    
    # Delete Shortlisted Leads
    leads = client.get_records('Shortlisted Leads')
    for r in leads:
        try:
            client.delete_record('Shortlisted Leads', r['id'])
        except:
            pass
    print(f'Deleted {len(leads)} shortlisted leads')
    
    # Delete Salary Preferences
    salary = client.get_records('Salary Preferences')
    for r in salary:
        try:
            client.delete_record('Salary Preferences', r['id'])
        except:
            pass
    print(f'Deleted {len(salary)} salary records')
    
    # Delete Work Experience
    exp = client.get_records('Work Experience')
    for r in exp:
        try:
            client.delete_record('Work Experience', r['id'])
        except:
            pass
    print(f'Deleted {len(exp)} experience records')
    
    # Delete Personal Details
    personal = client.get_records('Personal Details')
    for r in personal:
        try:
            client.delete_record('Personal Details', r['id'])
        except:
            pass
    print(f'Deleted {len(personal)} personal records')
    
    # Reset Applications
    apps = client.get_records('Applications')
    for r in apps:
        try:
            client.update_record('Applications', r['id'], {
                'Application ID': r['fields'].get('Application ID', ''),
                'Compressed JSON': '',
                'Shortlist Status': None,
                'LLM Summary': '',
                'LLM Score': None,
                'LLM Follow-Ups': ''
            })
        except:
            pass
    print(f'Reset {len(apps)} applications')
    
    print('Data cleared!')


def populate_test_data():
    """Populate fresh test data with Siresh and Suhaib."""
    client = AirtableClient()
    
    # Get the application record IDs
    apps = client.get_records('Applications')
    app_map = {r['fields'].get('Application ID'): r['id'] for r in apps}
    
    print('Adding test data...')
    
    # Personal Details - Siresh, Suhaib, and one more
    personal_data = [
        {
            'Full Name': 'Siresh Reddy',
            'Email': 'sireesh@pronexus.in',
            'Location': 'Bangalore, India',
            'LinkedIn': 'https://linkedin.com/in/sireshkumar',
            'Application ID': [app_map['APP001']]
        },
        {
            'Full Name': 'Suhaib SZ',
            'Email': 'ceo@pronexus.in',
            'Location': 'Bangalore,India',
            'LinkedIn': 'https://linkedin.com/in/suhaib-sz',
            'Application ID': [app_map['APP002']]
        },
        {
            'Full Name': 'Alex Chen',
            'Email': 'alex@example.com',
            'Location': 'Toronto, Canada',
            'LinkedIn': 'https://linkedin.com/in/alexchen',
            'Application ID': [app_map['APP003']]
        }
    ]
    
    for p in personal_data:
        client.create_record('Personal Details', p)
        print(f"Created Personal: {p['Full Name']}")
    
    # Work Experience
    experience_data = [
        # Siresh - Google (Tier 1, 5 years)
        {
            'Company': 'Google',
            'Title': 'Senior Software Engineer',
            'Start': '2019-03-01',
            'End': '2024-06-01',
            'Application ID': [app_map['APP001']]
        },
        {
            'Company': 'Infosys',
            'Title': 'Software Developer',
            'Start': '2017-01-01',
            'End': '2019-02-28',
            'Application ID': [app_map['APP001']]
        },
        # Suhaib - Meta + OpenAI (Tier 1, 6 years)
        {
            'Company': 'Meta',
            'Title': 'Staff Engineer',
            'Start': '2020-01-01',
            'End': '2023-12-31',
            'Application ID': [app_map['APP002']]
        },
        {
            'Company': 'OpenAI',
            'Title': 'Machine Learning Engineer',
            'Start': '2024-01-01',
            'End': '2025-12-31',
            'Application ID': [app_map['APP002']]
        },
        # Alex - Startups (4 years, no Tier-1)
        {
            'Company': 'TechStartup Inc',
            'Title': 'Full Stack Developer',
            'Start': '2020-06-01',
            'End': '2022-12-31',
            'Application ID': [app_map['APP003']]
        },
        {
            'Company': 'DataLabs',
            'Title': 'Backend Engineer',
            'Start': '2023-01-01',
            'End': '2025-01-01',
            'Application ID': [app_map['APP003']]
        }
    ]
    
    for e in experience_data:
        client.create_record('Work Experience', e)
        print(f"Created Experience: {e['Company']} - {e['Title']}")
    
    # Salary Preferences - Using both USD and INR
    salary_data = [
        {
            'Preferred Rate': 75,
            'Minimum Rate': 60,
            'Currency': 'INR',  # INR - will be converted
            'Availability': 40,
            'Application ID': [app_map['APP001']]
        },
        {
            'Preferred Rate': 95,
            'Minimum Rate': 80,
            'Currency': 'USD',
            'Availability': 35,
            'Application ID': [app_map['APP002']]
        },
        {
            'Preferred Rate': 85,
            'Minimum Rate': 70,
            'Currency': 'USD',
            'Availability': 25,
            'Application ID': [app_map['APP003']]
        }
    ]
    
    for s in salary_data:
        try:
            client.create_record('Salary Preferences', s)
            print(f"Created Salary: {s['Preferred Rate']} {s['Currency']}, {s['Availability']} hrs/wk")
        except Exception as ex:
            # Try with USD if INR fails
            if s['Currency'] == 'INR':
                s['Currency'] = 'USD'
                client.create_record('Salary Preferences', s)
                print(f"Created Salary (fallback USD): {s['Preferred Rate']} USD, {s['Availability']} hrs/wk")
            else:
                print(f"Failed: {ex}")
    
    print('\nTest data populated!')


if __name__ == '__main__':
    clear_data()
    populate_test_data()
