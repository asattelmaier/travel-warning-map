from typing import Optional, List
from fastapi import APIRouter, HTTPException
from app.core.config import settings
from app.core.drive_service import DriveService
from app.models.travel_warnings import TravelWarningsResponse
from app.models.travel_warning import TravelWarningResponse

router = APIRouter()
drive_service = DriveService(drive_folder_id=settings.DRIVE_FOLDER_ID)

@router.get("", response_model=TravelWarningsResponse)
async def get_travel_warnings(language: Optional[str] = "en"):
    """
    Fetch all travel warnings from Google Drive.
    """
    try:
        warnings = drive_service.get_travel_warnings(language=language)
        return warnings
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch travel warnings")

@router.get("/{warning_id}", response_model=TravelWarningResponse)
async def get_travel_warning(warning_id: str, language: Optional[str] = "en"):
    """
    Fetch a specific travel warning by ID from Google Drive.
    """
    try:
        warning = drive_service.get_travel_warning(warning_id, language=language)
        if not warning:
            raise HTTPException(status_code=404, detail="Travel warning not found")
        return warning
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch travel warning details") 