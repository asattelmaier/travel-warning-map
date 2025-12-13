import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.travel_warning.repository import TravelWarningRepository
from app.core.config import settings

logger = logging.getLogger(__name__)

class TravelWarningCache:
    # For I/O-bound tasks, a higher thread count can help; adjust as needed
    MAX_WORKER_THREADS: int = 20

    def __init__(self, repository: TravelWarningRepository):
        self.repository = repository
        self._cache_warnings: Dict[str, dict] = {}
        self._cache_details: Dict[str, Dict[str, dict]] = {}
        self._date_aliases: Dict[str, str] = {}
        self._lock = threading.RLock()
        
        self._progress: Dict[str, object] = {"total": 0, "loaded": 0, "active": False}
        
        logger.info("TravelWarningCache initialized (prefill=%s)", settings.TRAVEL_WARNING_PREFILL)
        if settings.TRAVEL_WARNING_PREFILL:
            self._progress["active"] = True
            threading.Thread(target=self.prefill_for_today, daemon=True).start()

    def get_progress(self) -> Dict[str, object]:
        return self._progress

    def _today(self) -> str:
        return datetime.now().strftime('%Y-%m-%d')

    def _fallback_date(self, date: str) -> str:
        return (datetime.strptime(date, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')

    def _load_summary(self, date: str, language: str = 'en') -> Optional[str]:
        """
        Try to load summary for `date`, falling back one day if empty.
        Caches the result and returns the actual date used or None.
        """
        data = self.repository.get_travel_warnings(date, language=language)
        if data.get('response'):
            data['effectiveDate'] = date
            with self._lock:
                self._cache_warnings[date] = data
                self._date_aliases[date] = date
            return date

        fb = self._fallback_date(date)
        logger.warning("No summary for %s, falling back to %s", date, fb)
        data = self.repository.get_travel_warnings(fb, language=language)
        if data.get('response'):
            data['effectiveDate'] = fb
            with self._lock:
                self._cache_warnings[fb] = data
                # Optimization: Cache the fallback result under the requested date too
                # to prevent repeated lookups/roundtrips for a missing date.
                self._cache_warnings[date] = data
                self._date_aliases[date] = fb
            return fb

        logger.error("No summary found for %s or %s", date, fb)
        return None

    def prefill_for_today(self):
        today = self._today()
        logger.info("Starting prefill for %s", today)

        used_date = self._load_summary(today)
        if not used_date:
            self._progress["active"] = False
            return

        ids = self._cache_warnings[used_date]['response'].get('contentList', [])
        total = len(ids)
        logger.info("Found %d warnings to load for %s", total, used_date)

        self._progress.update({"total": total, "loaded": 0})

        self._cache_details.setdefault(used_date, {})
        missing = [wid for wid in ids if wid not in self._cache_details[used_date]]

        with ThreadPoolExecutor(max_workers=self.MAX_WORKER_THREADS) as executor:
            futures = {executor.submit(self.repository.get_travel_warning, wid, used_date): wid for wid in missing}
            for i, future in enumerate(as_completed(futures), start=1):
                wid = futures[future]
                try:
                    detail = future.result()
                except Exception:
                    logger.exception("Failed to load detail for %s", wid)
                else:
                    with self._lock:
                        self._cache_details[used_date][wid] = detail
                    logger.info("Loaded %s (%d/%d)", wid, i, total)
                
                # Update progress
                current_loaded = self._progress["loaded"]
                if isinstance(current_loaded, int):
                    self._progress["loaded"] = current_loaded + 1

        loaded = len(self._cache_details[used_date])
        logger.info("Prefill complete: %d/%d warnings loaded for %s", loaded, total, used_date)
        self._progress["active"] = False

    def get_all_travel_warnings(self, date: Optional[str] = None, language: str = 'en') -> dict:
        date = date or self._today()
        logger.info("get_all_travel_warnings for %s", date)

        with self._lock:
            if date in self._cache_warnings:
                logger.info("Cache hit for %s", date)
                return self._cache_warnings[date]

        used_date = self._load_summary(date, language)
        if not used_date:
            return {'response': {}}

        logger.info("Loaded summary for %s (cache miss)", used_date)
        return self._cache_warnings[used_date]

    def get_travel_warning_by_id(self, warning_id: str, date: Optional[str] = None, language: str = 'en') -> dict:
        date_requested = date or self._today()
        logger.info("get_travel_warning_by_id %s on %s", warning_id, date_requested)

        # Ensure summary is loaded (this sets up aliases)
        with self._lock:
            if date_requested not in self._cache_warnings:
                # Release lock to load
                pass
            else:
                # Fast path
                effective_date = self._date_aliases.get(date_requested, date_requested)
                if effective_date in self._cache_details and warning_id in self._cache_details[effective_date]:
                    logger.info("Cache hit for %s on %s (aliased to %s)", warning_id, date_requested, effective_date)
                    return self._cache_details[effective_date][warning_id]

        # Load summary via helper if not present
        if date_requested not in self._cache_warnings:
            used_date = self._load_summary(date_requested, language)
            if not used_date:
                return {'response': {}}
        
        # Now resolve effective date from alias
        with self._lock:
            effective_date = self._date_aliases.get(date_requested, date_requested)

        self._cache_details.setdefault(effective_date, {})
        if warning_id not in self._cache_details[effective_date]:
            try:
                detail = self.repository.get_travel_warning(warning_id, effective_date, language=language)
                with self._lock:
                    self._cache_details[effective_date][warning_id] = detail
                logger.info("Loaded detail for %s on %s", warning_id, effective_date)
            except Exception:
                logger.exception("Failed to load detail for %s on %s", warning_id, effective_date)
                return {'response': {}}

        return self._cache_details[effective_date][warning_id]

    def clear_cache(self):
        logger.info("Clearing all caches")
        with self._lock:
            self._cache_warnings.clear()
            self._cache_details.clear()
