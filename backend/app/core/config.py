from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Travel Warning Map Backend"
    VERSION: str = "1.0.0"
    
    # CORS settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:4200",
        "https://storage.googleapis.com"
    ]
    
    # Google Drive settings
    DRIVE_FOLDER_ID: str
    DRIVE_ORIGIN_FOLDER: str = "https://www.auswaertiges-amt.de/opendata"
    DRIVE_TRAVELWARNING_FOLDER: str = "travelwarning"
    DRIVE_TRAVELWARNING_FILE: str = "travelwarning.json"

    # Prefill cache on startup (default: True)
    TRAVEL_WARNING_PREFILL: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings() 