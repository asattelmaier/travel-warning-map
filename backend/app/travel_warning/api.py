from typing import Optional
from fastapi import APIRouter, HTTPException
from app.core.config import settings
from app.travel_warning.google_drive_repository import GoogleDriveTravelWarningRepository
from app.travel_warning.service import TravelWarningService
from app.travel_warning.models_travel_warnings import TravelWarningsResponse
from app.travel_warning.models_travel_warning import TravelWarningResponse

router = APIRouter()
repository = GoogleDriveTravelWarningRepository(drive_folder_id=settings.DRIVE_FOLDER_ID)
service = TravelWarningService(repository=repository)

@router.get("", response_model=TravelWarningsResponse)
async def get_travel_warnings(language: Optional[str] = "en"):
    """
    Fetch all travel warnings from Google Drive.
    """
    try:
        warnings = service.get_all_travel_warnings(language=language)
        return warnings
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch travel warnings")

@router.get("/{warning_id}", response_model=TravelWarningResponse)
async def get_travel_warning(warning_id: str, language: Optional[str] = "en"):
    """
    Fetch a specific travel warning by ID from Google Drive.
    """
    try:
        warning = service.get_travel_warning_by_id(warning_id, language=language)
        if not warning:
            raise HTTPException(status_code=404, detail="Travel warning not found")
        return warning
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch travel warning details")

@router.get("/status/progress")
async def get_cache_status():
    """
    Get the current progress of the cache prefill.
    """
    return service.get_cache_status() 