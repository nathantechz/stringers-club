"""Apply schema.sql to Supabase using the Management API."""
import os, requests
from dotenv import load_dotenv

load_dotenv()

URL = os.environ["SUPABASE_URL"]
KEY = os.environ["SUPABASE_KEY"]
PROJECT_REF = URL.replace("https://", "").split(".")[0]

sql = open("schema.sql").read()

# Supabase Management API — run arbitrary SQL (works with service_role key)
endpoint = f"https://api.supabase.com/v1/projects/{PROJECT_REF}/database/query"
headers = {
    "Authorization": f"Bearer {KEY}",
    "Content-Type": "application/json",
}

resp = requests.post(endpoint, json={"query": sql}, headers=headers)
print("Status:", resp.status_code)
print(resp.text[:2000])
