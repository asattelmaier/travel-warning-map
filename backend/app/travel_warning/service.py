from typing import Dict
from app.travel_warning.repository import TravelWarningRepository

class TravelWarningService:
    def __init__(self, repository: TravelWarningRepository):
        self.repository = repository

    def get_all_travel_warnings(self, language: str = "en") -> Dict:
        return self.repository.get_travel_warnings(language=language)

    def get_travel_warning_by_id(self, warning_id: str, language: str = "en") -> Dict:
        return self.repository.get_travel_warning(warning_id=warning_id, language=language) 