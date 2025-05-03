from typing import Optional
from fastapi import APIRouter, HTTPException
import httpx
from app.core.config import settings
from app.models.travel_warnings import TravelWarningsResponse
from app.models.travel_warning import TravelWarningResponse

router = APIRouter()

@router.get("", response_model=TravelWarningsResponse)
async def get_travel_warnings(language: Optional[str] = "en"):
    """
    Fetch all travel warnings from the Auswärtiges Amt API.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                settings.AUSWAERTIGES_AMT_URL,
                params={"language": language}
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail="Failed to fetch travel warnings")

@router.get("/{warning_id}", response_model=TravelWarningResponse)
async def get_travel_warning(warning_id: str, language: Optional[str] = "en"):
    """
    Fetch a specific travel warning by ID.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.AUSWAERTIGES_AMT_URL}/{warning_id}",
                params={"language": language}
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail="Failed to fetch travel warning details") 