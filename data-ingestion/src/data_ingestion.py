#!/usr/bin/env python3
"""
TODO: This is a proof of concept implementation and needs to be refactored:
1. Move to a proper Python package structure
2. Add proper error handling and logging
3. Add configuration management
4. Add tests
5. Add type hints
6. Add documentation
7. Add proper dependency management
8. Add proper exception handling for API calls
9. Add proper retry mechanism for API calls
10. Add proper validation for API responses
"""

import os
import sys
import time
import json
import base64
import requests
from datetime import datetime
from io import BytesIO
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

BASE_URL = "https://www.auswaertiges-amt.de/opendata"
MAX_ATTEMPTS = 5
BASE_DELAY = 1

# Environment
DRIVE_ROOT_ID = os.environ.get("DRIVE_FOLDER_ID")
if not DRIVE_ROOT_ID:
    print("❌ DRIVE_FOLDER_ID not set")
    sys.exit(1)
B64 = os.environ.get("GOOGLE_CRED_B64")
if not B64:
    print("❌ GOOGLE_CRED_B64 not set")
    sys.exit(1)
try:
    SA_INFO = json.loads(base64.b64decode(B64).decode())
except Exception as e:
    print(f"❌ Invalid GOOGLE_CRED_B64: {e}")
    sys.exit(1)
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

# Drive service singleton
SERVICE = None
def get_service():
    global SERVICE
    if SERVICE is None:
        creds = service_account.Credentials.from_service_account_info(SA_INFO, scopes=SCOPES)
        SERVICE = build('drive', 'v3', credentials=creds)
    return SERVICE

# Find or create folder
def get_or_create_folder(name, parent_id):
    svc = get_service()
    q = f"mimeType='application/vnd.google-apps.folder' and name='{name}' and '{parent_id}' in parents and trashed=false"
    files = svc.files().list(q=q, fields='files(id)').execute().get('files', [])
    if files:
        return files[0]['id']
    folder = svc.files().create(
        body={'name': name, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [parent_id]},
        fields='id'
    ).execute()
    return folder['id']

# Upload bytes without logging
def upload_bytes(data, filename, parent_id):
    svc = get_service()
    bio = BytesIO(data)
    media = MediaIoBaseUpload(bio, mimetype='application/json', resumable=True)
    q = f"name='{filename}' and '{parent_id}' in parents and trashed=false"
    existing = svc.files().list(q=q, fields='files(id)').execute().get('files', [])
    if existing:
        svc.files().update(fileId=existing[0]['id'], media_body=media).execute()
    else:
        svc.files().create(body={'name': filename, 'parents': [parent_id]}, media_body=media, fields='id').execute()

# Download or init report in memory
def download_report(date_str, date_id):
    svc = get_service()
    q = f"name='report.json' and '{date_id}' in parents and trashed=false"
    files = svc.files().list(q=q, fields='files(id)').execute().get('files', [])
    if not files:
        return {'date': date_str, 'start': datetime.now().isoformat(), 'results': []}
    data = svc.files().get_media(fileId=files[0]['id']).execute()
    return json.loads(data)

# Check if already succeeded
def should_skip(report, key):
    return any(r['path']==key and r['status']=='success' for r in report.get('results', []))

# Update and upload report
def update_report(report, key, status, date_id):
    report['results'] = [r for r in report.get('results', []) if r['path']!=key]
    report['results'].append({'path': key, 'status': status})
    report['end'] = datetime.now().isoformat()
    upload_bytes(json.dumps(report).encode(), 'report.json', date_id)

# Fetch a path and upload, return success
def fetch_and_upload(path, parent_id, filename):
    url = f"{BASE_URL}/{path}"
    for attempt in range(1, MAX_ATTEMPTS+1):
        resp = requests.get(url, allow_redirects=False)
        if resp.status_code == 200:
            upload_bytes(resp.content, filename, parent_id)
            return True
        ra = resp.headers.get('Retry-After')
        time.sleep(int(ra) if ra and ra.isdigit() else BASE_DELAY*(2**(attempt-1)))
    return False

# Main execution
if __name__=='__main__':
    svc = get_service()
    ORIGIN_ID = get_or_create_folder(BASE_URL, DRIVE_ROOT_ID)
    date_str = datetime.now().strftime('%Y-%m-%d')
    DATE_ID = get_or_create_folder(date_str, ORIGIN_ID)
    TRAVEL_ID = get_or_create_folder('travelwarning', DATE_ID)

    report = download_report(date_str, DATE_ID)

    # build tasks: (key, filename, parent_id)
    tasks = []
    tasks.append(('travelwarning', 'travelwarning.json', DATE_ID))
    master_data = fetch_and_upload('travelwarning', DATE_ID, 'travelwarning.json')  # ensure master present
    # load master content list
    master_bytes = svc.files().get_media(
        fileId=svc.files().list(q=f"name='travelwarning.json' and '{DATE_ID}' in parents").execute()['files'][0]['id']
    ).execute()
    ids = json.loads(master_bytes).get('response', {}).get('contentList', [])
    for id in ids:
        tasks.append((f'travelwarning/{id}', f"{id}.json", TRAVEL_ID))
    for ep in ['representativesInGermany','representativesInCountry','stateNames','healthcare']:
        tasks.append((ep, f"{ep}.json", DATE_ID))

    total = len(tasks)
    start_time = time.monotonic()  # track start time
    for idx, (key, fname, pid) in enumerate(tasks, start=1):
        if should_skip(report, key):
            elapsed = time.monotonic() - start_time
            fmt = time.strftime('%H:%M:%S', time.gmtime(elapsed))
            print(f"➖  Skipping {fname} ({idx}/{total}), elapsed {fmt}")
            continue
        ok = fetch_and_upload(key, pid, fname)
        status = 'success' if ok else 'failure'
        update_report(report, key, status, DATE_ID)
        if ok:
            elapsed = time.monotonic() - start_time
            fmt = time.strftime('%H:%M:%S', time.gmtime(elapsed))
            print(f"✔  [{fname}] ({idx}/{total}), elapsed {fmt}")
        else:
            elapsed = time.monotonic() - start_time
            fmt = time.strftime('%H:%M:%S', time.gmtime(elapsed))
            print(f"❌  [{fname}] ({idx}/{total}) failed, elapsed {fmt}")
            sys.exit(1)
    elapsed = time.monotonic() - start_time
    fmt = time.strftime('%H:%M:%S', time.gmtime(elapsed))
    print(f"🏁 Done in {fmt}")
