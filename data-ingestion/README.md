# Data Ingestion for Auswärtiges Amt Open Data

This project automates fetching travel warnings and related data from the German Federal Foreign Office’s Open Data API and uploads the results to Google Drive. It’s containerized for easy deployment.

## Features

- **Fetch endpoints**: `travelwarning`, details per warning ID, and additional endpoints (`representativesInGermany`, `representativesInCountry`, `stateNames`, `healthcare`).
- **Retry logic** with exponential backoff and respect for `Retry-After` headers.
- **In-memory processing**: no local files; all data is uploaded directly to Google Drive.
- **Structured Drive folders**:
  - `<DRIVE_ROOT>/<API_BASE_URL>/<YYYY-MM-DD>/travelwarning/<id>.json`
  - Other endpoints and `report.json` under the date folder.
- **Progress logging**: shows success/skips/errors with a simple progress counter and elapsed time.
- **Report.json** tracks start/end timestamps and individual endpoint statuses.

## Prerequisites

- Python **3.12**
- Docker (optional, for container deployment)
- Google Service Account with **Drive API** access

## Environment Variables

| Variable          | Description                                            | Example                 |
|-------------------|--------------------------------------------------------|-------------------------|
| `DRIVE_FOLDER_ID` | ID of the root folder in Google Drive                  | `1a2B3cD...`            |
| `GOOGLE_CRED_B64` | Base64‑encoded JSON key of your Google service account | output of `cat key.json | base64` |

## Usage

### Local

1. Install dependencies:
   ```bash
   pip install requests google-api-python-client google-auth
   ```
2. Set environment variables:
   ```bash
   export DRIVE_FOLDER_ID="<YOUR_FOLDER_ID>"
   export GOOGLE_CRED_B64="$(cat credentials.json | base64)"
   ```
3. Run the ingestion:
   ```bash
   python data_ingestion.py
   ```

### Docker

1. Build the image:
   ```bash
   docker build -t data-ingestion .
   ```
2. Run the container:
   ```bash
   docker run --rm \
     -e DRIVE_FOLDER_ID="<YOUR_FOLDER_ID>" \
     -e GOOGLE_CRED_B64="<BASE64_JSON>" \
     data-ingestion
   ```

## Project Structure

```
├── data_ingestion.py      # Main ingestion script
├── Dockerfile             # Container definition (Python 3.12-slim)
├── README.md              # Project overview and usage instructions
└── requirements.txt?      # (optional) pinned dependencies
```

## Report.json Format

```json
{
  "date": "YYYY-MM-DD",
  "start": "2025-04-25T10:00:00",
  "end": "2025-04-25T10:05:30",
  "results": [
    {
      "path": "travelwarning",
      "status": "success"
    },
    {
      "path": "travelwarning/199124",
      "status": "success"
    },
    {
      "path": "stateNames",
      "status": "failure"
    }
  ]
}
```
