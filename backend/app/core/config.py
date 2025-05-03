from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Travel Warning Map API"
    VERSION: str = "1.0.0"
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]
    
    # External API settings
    AUSWAERTIGES_AMT_URL: str = "https://www.auswaertiges-amt.de/opendata/travelwarning"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings() 