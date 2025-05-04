import threading
import logging
from datetime import datetime, timedelta
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

    def _get_yesterday(self) -> str:
        return (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    def _load_with_fallback(self, date: str, language: str = "en") -> str:
        # Try today, then yesterday if today is empty
        data = self.repository.get_travel_warnings(date, language=language)
        if not data.get("response") or not data["response"]:
            fallback_date = (datetime.strptime(date, "%Y-%m-%d") - timedelta(days=1)).strftime('%Y-%m-%d')
            logger.warning("No data for %s, falling back to %s", date, fallback_date)
            data = self.repository.get_travel_warnings(fallback_date, language=language)
            if not data.get("response") or not data["response"]:
                logger.error("No data for fallback date %s either!", fallback_date)
                return None
            self._cache_warnings[fallback_date] = data
            return fallback_date
        self._cache_warnings[date] = data
        return date

    def prefill_for_today(self):
        today = self._get_today()
        with self._lock:
            used_date = self._load_with_fallback(today)
            if not used_date:
                logger.error("Prefill failed: no data for today or yesterday.")
                return
            logger.info("Prefilling travel warning cache for %s...", used_date)
            warnings = self._cache_warnings[used_date].get("response", {})
            content_list = warnings.get("contentList", [])
            logger.info("Found %d warning ids in contentList.", len(content_list))
            if used_date not in self._cache_details:
                self._cache_details[used_date] = {}
            for i, warning_id in enumerate(content_list, 1):
                if warning_id not in self._cache_details[used_date]:
                    self._cache_details[used_date][warning_id] = self.repository.get_travel_warning(warning_id, used_date)
                    logger.info("Loaded warning %s (%d/%d)", warning_id, i, len(content_list))
            logger.info("Cache prefill for %s complete. %d warnings loaded.", used_date, len(content_list))

    def get_all_travel_warnings(self, date: str = None, language: str = "en") -> Dict:
        if date is None:
            date = self._get_today()
        with self._lock:
            if date in self._cache_warnings:
                logger.info("Cache hit for travel warnings: %s", date)
                return self._cache_warnings[date]
            used_date = self._load_with_fallback(date, language=language)
            if not used_date:
                logger.error("No data for %s or fallback.", date)
                return {"response": {}}
            logger.info("Cache miss for %s, loaded %s", date, used_date)
            return self._cache_warnings[used_date]

    def get_travel_warning_by_id(self, warning_id: str, date: str = None, language: str = "en") -> Dict:
        if date is None:
            date = self._get_today()
        with self._lock:
            # Check if warning is already cached for date or fallback
            if date in self._cache_details and warning_id in self._cache_details[date]:
                logger.info("Cache hit for warning %s on %s", warning_id, date)
                return self._cache_details[date][warning_id]
            # If not, try fallback date if needed
            used_date = date
            if date not in self._cache_warnings:
                used_date = self._load_with_fallback(date, language=language)
                if not used_date:
                    logger.error("No data for %s or fallback.", date)
                    return {"response": {}}
            if used_date not in self._cache_details:
                self._cache_details[used_date] = {}
            if warning_id not in self._cache_details[used_date]:
                self._cache_details[used_date][warning_id] = self.repository.get_travel_warning(warning_id, used_date, language=language)
                logger.info("Loaded warning %s for %s (cache miss)", warning_id, used_date)
            return self._cache_details[used_date][warning_id]

    def clear_cache(self):
        with self._lock:
            self._cache_warnings.clear()
            self._cache_details.clear() 