import os
import requests
from dotenv import load_dotenv

load_dotenv("/home/ubuntu/airtable-notion-sync/.env")

AIRTABLE_TOKEN = os.environ["AIRTABLE_TOKEN"]
AIRTABLE_BASE_ID = os.environ["AIRTABLE_BASE_ID"]
AIRTABLE_TABLE = os.environ.get("AIRTABLE_TABLE", "Companies")
NOTION_TOKEN = os.environ["NOTION_TOKEN"]
NOTION_DATABASE_ID = os.environ["NOTION_DATABASE_ID"]

NOTION_DATE_APPLIED_PROP = "Date Applied "

AIRTABLE_HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_TOKEN}",
    "Content-Type": "application/json",
}

NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}


def clean_str(val):
    if val is None:
        return ""
    if isinstance(val, list):
        return ", ".join(str(x) for x in val if x is not None)
    return str(val).strip()


def format_date_iso(val):
    s = clean_str(val)
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return s[:10]
    return ""


def list_airtable_records():
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE}"
    records = []
    params = {}
    while True:
        r = requests.get(url, headers=AIRTABLE_HEADERS, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        records.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            break
        params["offset"] = offset
    return records


def build_notion_properties(fields, rec_id=""):
    title_val = (
        clean_str(fields.get("Job Title"))
        or clean_str(fields.get("Name"))
        or clean_str(fields.get("Company"))
        or "Untitled Role"
    )
    props = {
        "Job Title": {
            "title": [{"text": {"content": title_val}}]
        }
    }

    if rec_id:
        props["Airtable Record ID"] = {
            "rich_text": [{"text": {"content": rec_id}}]
        }

    company_val = clean_str(fields.get("Company"))
    if company_val:
        props["Company"] = {"rich_text": [{"text": {"content": company_val}}]}

    location_val = clean_str(fields.get("Location"))
    if location_val:
        props["Location"] = {"rich_text": [{"text": {"content": location_val}}]}

    salary_val = clean_str(fields.get("Salary"))
    if salary_val:
        props["Salary"] = {"rich_text": [{"text": {"content": salary_val}}]}

    status_val = clean_str(fields.get("Status"))
    if status_val:
        props["Status"] = {"select": {"name": status_val}}

    job_url_val = clean_str(fields.get("Job URL"))
    if job_url_val:
        props["Job URL"] = {"url": job_url_val}

    date_applied = format_date_iso(fields.get("Date Applied"))
    if date_applied:
        props[NOTION_DATE_APPLIED_PROP] = {"date": {"start": date_applied}}

    return props


def create_notion_page(fields, rec_id=""):
    payload = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": build_notion_properties(fields, rec_id=rec_id),
    }
    r = requests.post(
        "https://api.notion.com/v1/pages",
        headers=NOTION_HEADERS,
        json=payload,
        timeout=30,
    )
    if r.status_code >= 400:
        raise RuntimeError(f"Notion error {r.status_code}: {r.text}")
    data = r.json()
    return data["id"], data.get("url", "")


def get_notion_page_url(page_id):
    clean_id = page_id.strip()
    r = requests.get(
        f"https://api.notion.com/v1/pages/{clean_id}",
        headers=NOTION_HEADERS,
        timeout=30,
    )
    if r.status_code >= 400:
        raise RuntimeError(f"Notion fetch error {r.status_code}: {r.text}")
    return r.json().get("url", "")


def patch_notion_date_applied(page_id, date_applied):
    clean_id = page_id.strip()
    payload = {
        "properties": {
            NOTION_DATE_APPLIED_PROP: {"date": {"start": date_applied}}
        }
    }
    r = requests.patch(
        f"https://api.notion.com/v1/pages/{clean_id}",
        headers=NOTION_HEADERS,
        json=payload,
        timeout=30,
    )
    if r.status_code >= 400:
        raise RuntimeError(f"Notion patch error {r.status_code}: {r.text}")


def update_airtable_record(record_id, fields_to_update):
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE}/{record_id}"
    r = requests.patch(
        url,
        headers=AIRTABLE_HEADERS,
        json={"fields": fields_to_update},
        timeout=30,
    )
    r.raise_for_status()


def main():
    records = list_airtable_records()
    print(f"Found {len(records)} Airtable record(s).")

    for rec in records:
        rec_id = rec["id"]
        fields = rec.get("fields", {})
        existing_page_id = clean_str(fields.get("Notion Page ID"))
        existing_notion_url = clean_str(fields.get("Notion URL"))
        date_applied = format_date_iso(fields.get("Date Applied"))

        if existing_page_id:
            if not existing_notion_url:
                notion_url = get_notion_page_url(existing_page_id)
                updates = {"Synced to Notion": True}
                if notion_url:
                    updates["Notion URL"] = notion_url
                update_airtable_record(rec_id, updates)
                print(f"Backfilled Notion URL for {rec_id}")
            if date_applied:
                patch_notion_date_applied(existing_page_id, date_applied)
                print(f"Updated Date Applied ({date_applied}) on Notion page {existing_page_id}")
            continue

        notion_page_id, notion_url = create_notion_page(fields, rec_id=rec_id)
        updates = {
            "Notion Page ID": notion_page_id,
            "Synced to Notion": True,
        }
        if notion_url:
            updates["Notion URL"] = notion_url
        update_airtable_record(rec_id, updates)
        print(f"Synced {rec_id} -> Notion page {notion_page_id}")


if __name__ == "__main__":
    main()
