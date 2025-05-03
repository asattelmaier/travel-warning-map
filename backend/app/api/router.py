from fastapi import APIRouter

from app.api.endpoints import travel_warnings

api_router = APIRouter()

api_router.include_router(
    travel_warnings.router,
    prefix="/travel-warnings",
    tags=["travel-warnings"],
) 