import threading
import logging
from datetime import datetime
from typing import Dict
from app.travel_warning.repository import TravelWarningRepository
from app.core.config import settings

logger = logging.getLogger(__name__)

class TravelWarningCache:
    def __init__(self, repository: TravelWarningRepository):
        self.repository = repository
        self._cache_warnings = {}
        self._cache_details = {}
        self._lock = threading.Lock()
        if settings.TRAVEL_WARNING_PREFILL:
            self.prefill_for_today()

    def _get_today(self) -> str:
        return datetime.now().strftime('%Y-%m-%d')

    def prefill_for_today(self):
        today = self._get_today()
        logger.info("Prefilling travel warning cache for today (%s)...", today)
        with self._lock:
            if today not in self._cache_warnings:
                self._cache_warnings[today] = self.repository.get_travel_warnings(today)
            warnings = self._cache_warnings[today].get("response", {})
            content_list = warnings.get("contentList", [])
            logger.info("Found %d warning ids in contentList.", len(content_list))
            if today not in self._cache_details:
                self._cache_details[today] = {}
            for i, warning_id in enumerate(content_list, 1):
                if warning_id not in self._cache_details[today]:
                    self._cache_details[today][warning_id] = self.repository.get_travel_warning(warning_id, today)
                    logger.info("Loaded warning %s (%d/%d)", warning_id, i, len(content_list))
        logger.info("Cache prefill for today complete. %d warnings loaded.", len(content_list))

    def get_all_travel_warnings(self, date: str = None, language: str = "en") -> Dict:
        if date is None:
            date = self._get_today()
        with self._lock:
            if date not in self._cache_warnings:
                self._cache_warnings[date] = self.repository.get_travel_warnings(date, language=language)
            return self._cache_warnings[date]

    def get_travel_warning_by_id(self, warning_id: str, date: str = None, language: str = "en") -> Dict:
        if date is None:
            date = self._get_today()
        with self._lock:
            if date not in self._cache_details:
                self._cache_details[date] = {}
            if warning_id not in self._cache_details[date]:
                self._cache_details[date][warning_id] = self.repository.get_travel_warning(warning_id, date, language=language)
            return self._cache_details[date][warning_id]

    def clear_cache(self):
        with self._lock:
            self._cache_warnings.clear()
            self._cache_details.clear() 