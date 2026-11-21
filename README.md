# Airtable to Notion Job Tracker Sync

An automated Python sync script hosted on an Oracle Cloud Free Tier Ubuntu VM (`VM.Standard.E2.1.Micro`) and administered from a mobile device via Termux over SSH.

## Architecture & Workflow
- **Source:** Airtable (`Companies` table)
- **Destination:** Notion (`Applications` database)
- **Automation:** Scheduled hourly via `cron` (`0 * * * *`), writing output to `sync.log`
- **Deduplication & Write-Back:** Stores `Notion Page ID`, `Notion URL`, and `Synced to Notion` back in Airtable so existing records are not duplicated

## Field Mappings
- `Job Title` / `Name` / `Company` -> Notion `Job Title` (title)
- Airtable Record ID -> Notion `Airtable Record ID` (rich text)
- `Company` -> Notion `Company` (rich text)
- `Location` -> Notion `Location` (rich text)
- `Salary` -> Notion `Salary` (rich text)
- `Status` -> Notion `Status` (select)
- `Job URL` -> Notion `Job URL` (url)
- `Date Applied` -> Notion `Date Applied ` (date; matches trailing space in Notion schema)

## Notes, Testing & Limitations
- Built iteratively with AI assistance and validated on a small job-search dataset.
- Notion property names must match the target database schema character-for-character.
- Designed for creating new Notion pages and backfilling `Notion URL` / `Date Applied` rather than full two-way edit conflict resolution.
