import os
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")

#here table names

TABLE_APPLICANTS =  "Applicants"
TABLE_PERSONAL = "Personal Details"
TABLE_EXPERIENCE = "Work Experience"
TABLE_SALARY = "Salary Expectations"
TABLE_SHORTLISTED = "Shortlisted Leads"

#LLM config heree
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-5-turbo")
LLM_MAX_TOKENS = 10000
LLM_MAX_RETRIES = 3
LLM_TIMEOUT = 2

TIER_1_COMPANIES = [
    "Google",
    "Apple",
    "Microsoft",
    "Amazon",
    "Facebook",
    "Netflix",
    "Tesla",
    "SpaceX",
    "IBM",
    "Intel"
]
MIN_EXPERIENCE_YEARS = 4
MAX_PREFERRED_RATE = 100
MIN_AVAILABILITY_HOURS = 20
APPROVED_LOCATIONS = ["USA", "Canada", "UK", "Germany", "India"]

AIRTABLE_RATE_LIMIT = 5  
BATCH_SIZE = 10