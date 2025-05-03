from datetime import datetime, timedelta
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from google.auth import default
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError
import io
from app.core.config import settings

# Define required scopes
SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/drive.metadata.readonly'
]

class DriveService:
    def __init__(self, drive_folder_id: str):
        self.drive_folder_id = drive_folder_id
        self.credentials = self._get_credentials()
        self.drive_service = build('drive', 'v3', credentials=self.credentials)
        # Verify folder access on initialization
        self._verify_folder_access()

    def _get_credentials(self):
        """Get credentials for Google Drive API access."""
        print("Using gcloud application default credentials...")
        creds, _ = default(scopes=SCOPES)
        if not creds.valid:
            creds.refresh(Request())
        return creds

    def _verify_folder_access(self) -> None:
        """Verify that we have access to the specified folder."""
        try:
            print(f"Verifying access to folder {self.drive_folder_id}...")
            result = self.drive_service.files().get(
                fileId=self.drive_folder_id,
                fields='id, name, mimeType'
            ).execute()
            
            # Verify that it's actually a folder
            if result.get('mimeType') != 'application/vnd.google-apps.folder':
                raise ValueError(f"ID {self.drive_folder_id} is not a folder")
                
            print(f"Successfully accessed folder: {result.get('name')}")
        except HttpError as e:
            if e.resp.status == 404:
                raise ValueError(f"Folder with ID {self.drive_folder_id} not found")
            elif e.resp.status == 403:
                error_details = json.loads(e.content.decode())
                error_message = error_details.get('error', {}).get('message', 'Unknown error')
                raise PermissionError(
                    f"No access to folder with ID {self.drive_folder_id}. "
                    f"Error: {error_message}. "
                    "Please ensure you have granted access to this specific folder in Google Drive."
                )
            else:
                raise

    def _validate_folder_structure(self, folder_id: str, expected_name: str) -> None:
        """Validate that a folder has the expected name and type."""
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
        """Get the folder ID for today's data."""
        today = datetime.now().strftime('%Y-%m-%d')
        
        # First get the origin folder
        origin_query = f"name = '{settings.DRIVE_ORIGIN_FOLDER}' and '{self.drive_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder'"
        print(f"Searching for origin folder with query: {origin_query}")
        try:
            origin_results = self.drive_service.files().list(
                q=origin_query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            origin_folders = origin_results.get('files', [])
            if not origin_folders:
                print("No origin folder found")
                return None
                
            origin_id = origin_folders[0]['id']
            # Validate origin folder
            self._validate_folder_structure(origin_id, settings.DRIVE_ORIGIN_FOLDER)
            print(f"Found origin folder: {origin_folders[0]['name']} (ID: {origin_id})")
            
            # Then get today's folder
            date_query = f"name = '{today}' and '{origin_id}' in parents and mimeType = 'application/vnd.google-apps.folder'"
            print(f"Searching for today's folder with query: {date_query}")
            date_results = self.drive_service.files().list(
                q=date_query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            date_folders = date_results.get('files', [])
            if not date_folders:
                print("No folder found for today's date")
                return None
                
            date_id = date_folders[0]['id']
            # Validate date folder
            self._validate_folder_structure(date_id, today)
            print(f"Found today's folder: {date_folders[0]['name']} (ID: {date_id})")
            return date_id
            
        except HttpError as e:
            if e.resp.status == 403:
                raise PermissionError(f"No access to list contents of folder {self.drive_folder_id}")
            raise

    def _get_yesterday_folder_id(self) -> Optional[str]:
        """Get the folder ID for yesterday's data."""
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # First get the origin folder
        origin_query = f"name = '{settings.DRIVE_ORIGIN_FOLDER}' and '{self.drive_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder'"
        print(f"Searching for origin folder with query: {origin_query}")
        try:
            origin_results = self.drive_service.files().list(
                q=origin_query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            origin_folders = origin_results.get('files', [])
            if not origin_folders:
                print("No origin folder found")
                return None
                
            origin_id = origin_folders[0]['id']
            # Validate origin folder
            self._validate_folder_structure(origin_id, settings.DRIVE_ORIGIN_FOLDER)
            print(f"Found origin folder: {origin_folders[0]['name']} (ID: {origin_id})")
            
            # Then get yesterday's folder
            date_query = f"name = '{yesterday}' and '{origin_id}' in parents and mimeType = 'application/vnd.google-apps.folder'"
            print(f"Searching for yesterday's folder with query: {date_query}")
            date_results = self.drive_service.files().list(
                q=date_query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            date_folders = date_results.get('files', [])
            if not date_folders:
                print("No folder found for yesterday's date")
                return None
                
            date_id = date_folders[0]['id']
            # Validate date folder
            self._validate_folder_structure(date_id, yesterday)
            print(f"Found yesterday's folder: {date_folders[0]['name']} (ID: {date_id})")
            return date_id
            
        except HttpError as e:
            if e.resp.status == 403:
                raise PermissionError(f"No access to list contents of folder {self.drive_folder_id}")
            raise

    def _validate_warning_id(self, warning_id: str) -> None:
        """Validate that the warning ID is a number with max 6 digits."""
        # Check if warning_id is a number
        if not warning_id.isdigit():
            raise ValueError("Invalid warning ID format: must be a number")
        
        # Check length (max 6 digits)
        if len(warning_id) > 6:
            raise ValueError("Warning ID must not be longer than 6 digits")

    def get_travel_warnings(self, language: str = "en") -> Dict:
        """Get all travel warnings for today, falling back to yesterday's data if today's data is not available."""
        today_folder_id = self._get_today_folder_id()
        if not today_folder_id:
            print("No folder found for today, trying yesterday's folder")
            today_folder_id = self._get_yesterday_folder_id()
            if not today_folder_id:
                print("No folder found for today or yesterday, returning empty list")
                return {"response": {}}

        # Get the travelwarning.json file
        query = f"name = '{settings.DRIVE_TRAVELWARNING_FILE}' and '{today_folder_id}' in parents"
        print(f"Searching for travelwarning.json with query: {query}")
        try:
            results = self.drive_service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, size, mimeType)'
            ).execute()

            files = results.get('files', [])
            if not files:
                print("No travelwarning.json found")
                return {"response": {}}
                
            # Validate file type
            if files[0].get('mimeType') != 'application/json':
                raise ValueError(f"File {files[0]['name']} is not a JSON file")
                
            print(f"Found travelwarning.json (size: {files[0].get('size', 'unknown')} bytes)")
            
            # Read the travelwarning.json file
            request = self.drive_service.files().get_media(fileId=files[0]['id'])
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            
            fh.seek(0)
            content = fh.read().decode()
            print(f"Raw content length: {len(content)} bytes")
            print(f"Raw content preview: {content[:200]}...")
            
            warning_data = json.loads(content)
            print(f"Parsed JSON keys: {list(warning_data.keys())}")
            
            if 'response' in warning_data:
                response = warning_data['response']
                print(f"Response keys: {list(response.keys())}")
                print(f"Number of warnings in contentList: {len(response.get('contentList', []))}")
                return warning_data
            
            print("No response found in data")
            return {"response": {}}

        except HttpError as e:
            if e.resp.status == 403:
                raise PermissionError(f"No access to read travelwarning.json")
            raise
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            print(f"Content that failed to parse: {content}")
            raise
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise

    def get_travel_warning(self, warning_id: str, language: str = "en") -> Dict:
        """Get a specific travel warning by ID, falling back to yesterday's data if today's data is not available."""
        # Validate warning_id before using it
        self._validate_warning_id(warning_id)
        
        today_folder_id = self._get_today_folder_id()
        if not today_folder_id:
            print("No folder found for today, trying yesterday's folder")
            today_folder_id = self._get_yesterday_folder_id()
            if not today_folder_id:
                print("No folder found for today or yesterday")
                return {"response": {}}

        # Get the travelwarning folder
        travel_query = f"name = '{settings.DRIVE_TRAVELWARNING_FOLDER}' and '{today_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder'"
        print(f"Searching for travelwarning folder with query: {travel_query}")
        try:
            travel_results = self.drive_service.files().list(
                q=travel_query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            travel_folders = travel_results.get('files', [])
            if not travel_folders:
                print("No travelwarning folder found")
                return {"response": {}}
                
            travel_folder_id = travel_folders[0]['id']
            # Validate travelwarning folder
            self._validate_folder_structure(travel_folder_id, settings.DRIVE_TRAVELWARNING_FOLDER)
            print(f"Found travelwarning folder: {travel_folders[0]['name']} (ID: {travel_folder_id})")

            # Get the specific warning file - using validated warning_id
            warning_query = f"name = '{warning_id}.json' and '{travel_folder_id}' in parents"
            print(f"Searching for warning file with query: {warning_query}")
            warning_results = self.drive_service.files().list(
                q=warning_query,
                spaces='drive',
                fields='files(id, name, mimeType)'
            ).execute()
            
            warning_files = warning_results.get('files', [])
            if not warning_files:
                print(f"No file found for warning {warning_id}")
                return {"response": {}}
                
            # Validate file type
            if warning_files[0].get('mimeType') != 'application/json':
                raise ValueError(f"File {warning_files[0]['name']} is not a JSON file")
                
            print(f"Found warning file: {warning_files[0]['name']}")
            
            # Read the warning file
            request = self.drive_service.files().get_media(fileId=warning_files[0]['id'])
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            
            fh.seek(0)
            content = fh.read().decode()
            print(f"Raw content length: {len(content)} bytes")
            print(f"Raw content preview: {content[:200]}...")
            
            warning_data = json.loads(content)
            print(f"Parsed JSON keys: {list(warning_data.keys())}")
            print(f"Successfully loaded warning file: {warning_files[0]['name']}")
            return warning_data
                
        except HttpError as e:
            if e.resp.status == 403:
                raise PermissionError(f"No access to read warning file {warning_id}.json")
            raise
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            print(f"Content that failed to parse: {content}")
            raise
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise 