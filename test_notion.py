import os, requests
from dotenv import load_dotenv
load_dotenv(".env")
url = f"https://api.notion.com/v1/databases/{os.getenv('NOTION_DATABASE_ID')}/query"
headers = {
    "Authorization": f"Bearer {os.getenv('NOTION_TOKEN')}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}
r = requests.post(url, headers=headers, json={"page_size": 1}, timeout=15)
print(r.status_code, r.text[:300])
