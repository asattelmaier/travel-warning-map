# Data Ingestion

This service fetches travel warning data from the German Foreign Office API and stores it in Google Drive.

## Prerequisites

- Python 3.12+
- Docker
- Google Cloud SDK
- Access to Google Drive API

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DRIVE_FOLDER_ID` | ID of the root folder in Google Drive | `1zF9mGo4x_j-WPyLWMI-RHbmeAx_oG_oA` |

## Local Development

1. Set up Google Cloud credentials:
```bash
gcloud auth application-default login --scopes='https://www.googleapis.com/auth/drive.file,https://www.googleapis.com/auth/cloud-platform'
```

2. Set environment variables:
```bash
export DRIVE_FOLDER_ID="your_folder_id"
```

3. Run the script:
```bash
python src/data_ingestion.py
```

## Docker

Build and run with Docker:

```bash
# Build the image
docker build -t travel-warning-data-ingestion .

# Run the container
docker run -v ~/.config/gcloud/application_default_credentials.json:/app/credentials.json \
  -e DRIVE_FOLDER_ID="your_folder_id" \
  travel-warning-data-ingestion
```

## Deployment

The service is deployed as a Cloud Run job and triggered by a Cloud Scheduler job daily at midnight (CET).
