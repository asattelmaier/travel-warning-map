from typing import Dict

class TravelWarningRepository:
    def get_travel_warnings(self, language: str = "en") -> Dict:
        raise NotImplementedError

    def get_travel_warning(self, warning_id: str, language: str = "en") -> Dict:
        raise NotImplementedError 