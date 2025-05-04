import logging
logger = logging.getLogger(__name__)
logger.info("GoogleDriveTravelWarningRepository module loaded.")

from datetime import datetime, timedelta
import json
import io
from typing import Dict, Optional
from google.auth import default
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError
from app.core.config import settings
from app.travel_warning.repository import TravelWarningRepository

SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/drive.metadata.readonly'
]

class GoogleDriveTravelWarningRepository(TravelWarningRepository):
    def __init__(self, drive_folder_id: str):
        logger.info("Instantiating GoogleDriveTravelWarningRepository...")
        self.drive_folder_id = drive_folder_id
        self.credentials = self._get_credentials()
        self.drive_service = build('drive', 'v3', credentials=self.credentials)
        self._cache_warnings = None
        self._cache_details = {}
        self._verify_folder_access()
        self._load_cache()

    def _get_credentials(self):
        creds, _ = default(scopes=SCOPES)
        if not creds.valid:
            creds.refresh(Request())
        return creds

    def _verify_folder_access(self) -> None:
        try:
            result = self.drive_service.files().get(
                fileId=self.drive_folder_id,
                fields='id, name, mimeType'
            ).execute()
            if result.get('mimeType') != 'application/vnd.google-apps.folder':
                raise ValueError(f"ID {self.drive_folder_id} is not a folder")
        except HttpError as e:
            if e.resp.status == 404:
                raise ValueError(f"Folder with ID {self.drive_folder_id} not found")
            elif e.resp.status == 403:
                error_details = json.loads(e.content.decode())
                error_message = error_details.get('error', {}).get('message', 'Unknown error')
                raise PermissionError(
                    f"No access to folder with ID {self.drive_folder_id}. Error: {error_message}"
                )
            else:
                raise

    def _load_cache(self):
        logger.info("Prefilling travel warning cache from Google Drive...")
        today_folder_id = self._get_today_folder_id()
        if not today_folder_id:
            today_folder_id = self._get_yesterday_folder_id()
        if not today_folder_id:
            logger.warning("No folder found for today or yesterday. Cache will be empty.")
            self._cache_warnings = {"response": {}}
            self._cache_details = {}
            return
        # Load travelwarning.json
        logger.info("Loading travelwarning.json...")
        query = f"name = '{settings.DRIVE_TRAVELWARNING_FILE}' and '{today_folder_id}' in parents"
        results = self.drive_service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name, size, mimeType)'
        ).execute()
        files = results.get('files', [])
        if files and files[0].get('mimeType') == 'application/json':
            file_id = files[0]['id']
            request = self.drive_service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            fh.seek(0)
            content = fh.read().decode()
            try:
                self._cache_warnings = json.loads(content)
                logger.info("Loaded travelwarning.json (%d bytes)", len(content))
            except Exception as e:
                logger.error("Failed to parse travelwarning.json: %s", e)
                self._cache_warnings = {"response": {}}
        else:
            logger.warning("No travelwarning.json found.")
            self._cache_warnings = {"response": {}}
        # Load all individual warning files
        logger.info("Loading individual warning files...")
        warning_ids = []
        # Try to use contentList from travelwarning.json if available
        content_list = None
        if self._cache_warnings and isinstance(self._cache_warnings, dict):
            content_list = self._cache_warnings.get("response", {}).get("contentList")
        if isinstance(content_list, list) and all(isinstance(x, str) for x in content_list):
            warning_ids = content_list
            logger.info("Using contentList from travelwarning.json (%d ids)", len(warning_ids))
        else:
            # Fallback: list all .json files in the folder (with pagination)
            logger.info("No valid contentList found, listing all .json files in folder (with pagination)...")
            travel_query = f"name = '{settings.DRIVE_TRAVELWARNING_FOLDER}' and '{today_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder'"
            travel_results = self.drive_service.files().list(
                q=travel_query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            travel_folders = travel_results.get('files', [])
            if not travel_folders:
                logger.warning("No travelwarning folder found.")
                self._cache_details = {}
                return
            travel_folder_id = travel_folders[0]['id']
            warning_files = []
            page_token = None
            while True:
                warning_files_results = self.drive_service.files().list(
                    q=f"'{travel_folder_id}' in parents and name contains '.json'",
                    spaces='drive',
                    fields='nextPageToken, files(id, name, mimeType)',
                    pageToken=page_token
                ).execute()
                warning_files.extend(warning_files_results.get('files', []))
                page_token = warning_files_results.get('nextPageToken')
                if not page_token:
                    break
            logger.info("Found %d .json files in folder.", len(warning_files))
            for file in warning_files:
                name = file.get('name')
                if name and name.endswith('.json'):
                    warning_ids.append(name[:-5])
        # Now load all warning files by id
        travel_query = f"name = '{settings.DRIVE_TRAVELWARNING_FOLDER}' and '{today_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder'"
        travel_results = self.drive_service.files().list(
            q=travel_query,
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        travel_folders = travel_results.get('files', [])
        if not travel_folders:
            logger.warning("No travelwarning folder found.")
            self._cache_details = {}
            return
        travel_folder_id = travel_folders[0]['id']
        loaded_count = 0
        for i, warning_id in enumerate(warning_ids, 1):
            file_query = f"name = '{warning_id}.json' and '{travel_folder_id}' in parents"
            file_results = self.drive_service.files().list(
                q=file_query,
                spaces='drive',
                fields='files(id, name, mimeType)'
            ).execute()
            files = file_results.get('files', [])
            if not files:
                logger.warning("Warning file %s.json not found in folder.", warning_id)
                continue
            file = files[0]
            try:
                request = self.drive_service.files().get_media(fileId=file['id'])
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()
                fh.seek(0)
                content = fh.read().decode()
                self._cache_details[warning_id] = json.loads(content)
                loaded_count += 1
                logger.info("Loaded warning file %s.json (%d/%d)", warning_id, i, len(warning_ids))
            except Exception as e:
                logger.error("Failed to load warning file %s.json: %s", warning_id, e)
                self._cache_details[warning_id] = {}
        logger.info("Cache prefill complete. %d warnings loaded.", loaded_count)

    def _validate_folder_structure(self, folder_id: str, expected_name: str) -> None:
        try:
            result = self.drive_service.files().get(
                fileId=folder_id,
                fields='id, name, mimeType'
            ).execute()
            if result.get('mimeType') != 'application/vnd.google-apps.folder':
                raise ValueError(f"ID {folder_id} is not a folder")
            if result.get('name') != expected_name:
                raise ValueError(f"Folder name mismatch: expected {expected_name}, got {result.get('name')}")
        except HttpError as e:
            if e.resp.status == 404:
                raise ValueError(f"Folder with ID {folder_id} not found")
            elif e.resp.status == 403:
                raise PermissionError(f"No access to folder with ID {folder_id}")
            raise

    def _get_today_folder_id(self) -> Optional[str]:
        today = datetime.now().strftime('%Y-%m-%d')
        origin_query = f"name = '{settings.DRIVE_ORIGIN_FOLDER}' and '{self.drive_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder'"
        try:
            origin_results = self.drive_service.files().list(
                q=origin_query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            origin_folders = origin_results.get('files', [])
            if not origin_folders:
                return None
            origin_id = origin_folders[0]['id']
            self._validate_folder_structure(origin_id, settings.DRIVE_ORIGIN_FOLDER)
            date_query = f"name = '{today}' and '{origin_id}' in parents and mimeType = 'application/vnd.google-apps.folder'"
            date_results = self.drive_service.files().list(
                q=date_query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            date_folders = date_results.get('files', [])
            if not date_folders:
                return None
            date_id = date_folders[0]['id']
            self._validate_folder_structure(date_id, today)
            return date_id
        except HttpError as e:
            if e.resp.status == 403:
                raise PermissionError(f"No access to list contents of folder {self.drive_folder_id}")
            raise

    def _get_yesterday_folder_id(self) -> Optional[str]:
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        origin_query = f"name = '{settings.DRIVE_ORIGIN_FOLDER}' and '{self.drive_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder'"
        try:
            origin_results = self.drive_service.files().list(
                q=origin_query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            origin_folders = origin_results.get('files', [])
            if not origin_folders:
                return None
            origin_id = origin_folders[0]['id']
            self._validate_folder_structure(origin_id, settings.DRIVE_ORIGIN_FOLDER)
            date_query = f"name = '{yesterday}' and '{origin_id}' in parents and mimeType = 'application/vnd.google-apps.folder'"
            date_results = self.drive_service.files().list(
                q=date_query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            date_folders = date_results.get('files', [])
            if not date_folders:
                return None
            date_id = date_folders[0]['id']
            self._validate_folder_structure(date_id, yesterday)
            return date_id
        except HttpError as e:
            if e.resp.status == 403:
                raise PermissionError(f"No access to list contents of folder {self.drive_folder_id}")
            raise

    def _validate_warning_id(self, warning_id: str) -> None:
        if not warning_id.isdigit():
            raise ValueError("Invalid warning ID format: must be a number")
        if len(warning_id) > 6:
            raise ValueError("Warning ID must not be longer than 6 digits")

    def get_travel_warnings(self, language: str = "en") -> Dict:
        return self._cache_warnings or {"response": {}}

    def get_travel_warning(self, warning_id: str, language: str = "en") -> Dict:
        self._validate_warning_id(warning_id)
        return self._cache_details.get(warning_id, {"response": {}}) 