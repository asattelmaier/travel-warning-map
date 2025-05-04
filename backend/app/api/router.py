from fastapi import APIRouter

from app.travel_warning import api as travel_warnings

api_router = APIRouter()

api_router.include_router(
    travel_warnings.router,
    prefix="/travel-warnings",
    tags=["travel-warnings"],
) 