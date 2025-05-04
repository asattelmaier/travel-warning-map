from typing import Dict
from app.travel_warning.cache import TravelWarningCache
from app.travel_warning.repository import TravelWarningRepository

class TravelWarningService:
    def __init__(self, repository: TravelWarningRepository):
        self.cache = TravelWarningCache(repository)

    def get_all_travel_warnings(self, language: str = "en", date: str = None) -> Dict:
        return self.cache.get_all_travel_warnings(date=date, language=language)

    def get_travel_warning_by_id(self, warning_id: str, language: str = "en", date: str = None) -> Dict:
        return self.cache.get_travel_warning_by_id(warning_id, date=date, language=language)

    def clear_cache(self):
        self.cache.clear_cache() 