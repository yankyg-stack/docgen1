# N8N + Document Generation: Integration Guide

## Overview

This system generates **training logs** (DOCX) and **completion certificates** (PDF) for each staff member based on their employment dates, then uploads everything to Google Drive.

---

## What Gets Generated Per Staff Member

For a staff member hired `2021-06-15` who is still employed:

| File | Description |
|------|-------------|
| `Jane_Doe_Training_Log.docx` | Single log with one row per training year |
| `Jane_Doe_Certificate_06-17-2021.pdf` | Certificate for initial orientation (start + 2 days) |
| `Jane_Doe_Certificate_06-10-2022.pdf` | Certificate for year 2 (start + 1yr - 1wk + 2 days) |
| `Jane_Doe_Certificate_06-10-2023.pdf` | Certificate for year 3 |
| ... | Continues until today (or end date) |

### Logic Summary

| Field | Year 1 (hire date) | Year 2+ (anniversary - 1 week) |
|-------|--------------------|---------------------------------|
| **Training Date** | Start date | Start + N years - 7 days |
| **Trainer** | Joel Posen BS/SC Supervisor | Same |
| **Goals** | Basic and Service Specific Orientation | Annual Training |
| **Evaluation** | Pre & Post written evaluation | Basic and Service Specific Orientation Review |
| **Cert Issued** | Training date + 2 days | Training date + 2 days |

---

## Architecture Options for N8N Cloud

Since **N8N Cloud** cannot run shell commands or install npm packages, you need an external service to generate the documents. Here are your options:

### Option A: Webhook API on a VPS or Cloud Function (Recommended)

```
N8N Cloud                          Your Server / Cloud Function
┌──────────────┐    HTTP POST     ┌──────────────────────────┐
│ Webhook      │ ──────────────>  │ Express.js API           │
│ Trigger      │    staff JSON    │   - generate_log.js      │
│              │                  │   - generate_certs.py    │
│ Loop items   │  <──────────── │   Returns ZIP of files   │
│              │   ZIP (base64)   │                          │
│ Google Drive │                  └──────────────────────────┘
│   - Create   │
│     folder   │
│   - Upload   │
│     files    │
└──────────────┘
```

**Deploy the API** (see `server.js` in this package) to any of:
- **Railway.app** (free tier) — easiest
- **Render.com** (free tier)
- **AWS Lambda** + API Gateway
- **Google Cloud Run**
- Any VPS with Node.js + Python3

### Option B: Self-Hosted N8N (Docker)

If you switch to self-hosted N8N, you can use the **Execute Command** node directly:

```bash
python3 /path/to/process_all_staff.py '{{ JSON.stringify($json.staffList) }}'
```

### Option C: Run Locally + N8N Just for Google Drive

1. Run `process_all_staff.py` on your machine with the staff JSON
2. Use N8N workflow to read the `manifest.json` and upload to Google Drive

---

## Setup Instructions (Option A — Recommended)

### Step 1: Deploy the API Server

1. Copy the entire `doc-generator/` folder to your server
2. Install dependencies:
   ```bash
   npm install express multer
   pip3 install pypdf reportlab
   ```
3. Place your certificate template PDF at `./templates/CERTIFICATE-_Attentive_JP.pdf`
4. Start the server:
   ```bash
   node server.js
   ```
5. The API will be available at `http://your-server:3000/generate`

### Step 2: Import the N8N Workflow

1. In N8N Cloud, go to **Workflows** → **Import from file**
2. Import `n8n_workflow.json` (included in this package)
3. Configure:
   - Update the HTTP Request node URL to point to your deployed API
   - Connect your Google Drive credentials
   - Set the parent folder ID where staff folders should be created

### Step 3: Provide Staff Data

The workflow expects a JSON array as input (via webhook or manual trigger):

```json
[
  {
    "name": "Jane Doe",
    "startDate": "2021-06-15"
  },
  {
    "name": "John Smith",
    "startDate": "2019-01-10",
    "endDate": "2023-05-01"
  }
]
```

- `name` — Full name (used in documents and folder name)
- `startDate` — YYYY-MM-DD format
- `endDate` — Optional. If omitted, generates up to today's date

---

## N8N Workflow Structure

```
1. Manual Trigger / Webhook
   │  (receives staff list JSON)
   │
2. Split In Batches (loop through each staff)
   │
   ├─ 3. HTTP Request → POST to your API
   │     Body: { name, startDate, endDate }
   │     Response: { files: [{name, content_base64, type}] }
   │
   ├─ 4. Google Drive: Create Folder
   │     Folder name: {{ $json.name }}
   │     Parent: your chosen folder ID
   │
   ├─ 5. Split In Batches (loop through files)
   │     │
   │     └─ 6. Google Drive: Upload File
   │           File name: {{ $json.fileName }}
   │           File content: {{ $json.content }}
   │           Parent folder: folder from step 4
   │
   └─ (next staff member)
```

---

## API Endpoint Specification

### POST /generate

**Request:**
```json
{
  "name": "Jane Doe",
  "startDate": "2021-06-15",
  "endDate": ""
}
```

**Response:**
```json
{
  "staffName": "Jane Doe",
  "fileCount": 6,
  "files": [
    {
      "fileName": "Jane_Doe_Training_Log.docx",
      "type": "docx",
      "content": "<base64 encoded file>"
    },
    {
      "fileName": "Jane_Doe_Certificate_06-17-2021.pdf",
      "type": "pdf",
      "content": "<base64 encoded file>"
    }
  ]
}
```

---

## File Inventory

```
doc-generator/
├── README.md                    ← This file
├── generate_log.js              ← Training log DOCX generator
├── generate_certs.py            ← Certificate PDF generator
├── process_all_staff.py         ← Master batch processor (CLI)
├── server.js                    ← Express API server (for N8N)
├── n8n_workflow.json            ← Importable N8N workflow
├── package.json                 ← Node dependencies
└── templates/
    └── CERTIFICATE-_Attentive_JP.pdf  ← Certificate template
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Dates look wrong | Ensure `startDate` is YYYY-MM-DD format |
| Certificate text misaligned | Adjust `pw * X` and `ph * Y` multipliers in `generate_certs.py` |
| N8N can't reach API | Check firewall rules, ensure HTTPS if N8N Cloud |
| Google Drive upload fails | Verify OAuth2 credentials and folder permissions |
| Large staff lists timeout | Increase N8N HTTP Request timeout to 120s |
