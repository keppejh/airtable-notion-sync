import os, requests
from dotenv import load_dotenv
load_dotenv(".env")
url = f"https://api.airtable.com/v0/{os.getenv('AIRTABLE_BASE_ID')}/{os.getenv('AIRTABLE_TABLE_NAME')}"
r = requests.get(url, headers={"Authorization": f"Bearer {os.getenv('AIRTABLE_TOKEN')}"}, params={"maxRecords": 1}, timeout=15)
print(r.status_code, r.text[:300])
