"""Background market scan manager handling concurrency, execution, and state reporting."""

import threading
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from run_all import run_pipeline
from src.screening.main import run_screening
from src.api.services.history_service import save_analysis

logger = logging.getLogger(__name__)


class ScanManager:
    """Singleton scan coordinator ensuring non-blocking, concurrency-safe market analysis."""

    def __init__(self):
        self._lock = threading.Lock()
        self.status: str = "idle"  # idle, running, completed, error
        self.progress_msg: str = "System ready."
        self.start_time: Optional[str] = None
        self.finish_time: Optional[str] = None
        self.last_results: Optional[Dict[str, Any]] = None
        self.last_error: Optional[str] = None

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "status": self.status,
                "progress": self.progress_msg,
                "start_time": self.start_time,
                "finish_time": self.finish_time,
                "has_results": self.last_results is not None,
                "error": self.last_error
            }

    def get_results(self) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self.last_results

    def start_scan(
        self,
        universe: str = "broad_market",
        max_symbols: int = 10,
        refresh_universe: bool = False,
        offline: bool = False,
        symbols: Optional[List[str]] = None
    ) -> bool:
        """
        Initiates a background market scan if one is not already running.
        Returns True if started, False if busy.
        """
        with self._lock:
            if self.status == "running":
                return False
            self.status = "running"
            self.progress_msg = f"Initiating NSE market scan ({'offline' if offline else 'live'})..."
            self.start_time = datetime.now().isoformat()
            self.finish_time = None
            self.last_error = None

        thread = threading.Thread(
            target=self._run_scan_worker,
            kwargs={
                "universe": universe,
                "max_symbols": max_symbols,
                "refresh_universe": refresh_universe,
                "offline": offline,
                "symbols": symbols
            },
            daemon=True
        )
        thread.start()
        return True

    def _run_scan_worker(
        self,
        universe: str,
        max_symbols: int,
        refresh_universe: bool,
        offline: bool,
        symbols: Optional[List[str]]
    ) -> None:
        try:
            with self._lock:
                self.progress_msg = "Discovering eligible ordinary equities across the NSE..."

            # Step 1: Run full pipeline (Discovery -> Tech -> Fund -> Decision Engine)
            results = run_pipeline(
                universe=universe,
                symbols=symbols,
                max_symbols=max_symbols,
                refresh_universe=refresh_universe,
                offline=offline
            )

            # Step 2: Persist individual completed analyses to local history
            pipeline_items = results.get("multi_agent_pipeline", [])
            for item in pipeline_items:
                try:
                    formatted_record = {
                        "symbol": item.get("symbol"),
                        "timestamp": datetime.now().isoformat(),
                        "mode": "offline" if offline else "live",
                        "composite_score": item.get("composite_score"),
                        "composite_verdict": item.get("composite_verdict"),
                        "verdict_reason": item.get("verdict_reason"),
                        "screening": {"eligible": True, "status": "discovered"},
                        "technical": item.get("agent_2_technical", {}),
                        "fundamental": item.get("agent_3_fundamental", {})
                    }
                    save_analysis(formatted_record)
                except Exception as e:
                    logger.warning(f"Failed to record history for {item.get('symbol')}: {e}")

            with self._lock:
                self.status = "completed"
                self.progress_msg = f"Scan complete. Discovered {len(results.get('screening', {}).get('symbols', []))} equities, analyzed {len(pipeline_items)} candidates."
                self.finish_time = datetime.now().isoformat()
                self.last_results = results

        except Exception as e:
            logger.error(f"Error during market scan: {e}", exc_info=True)
            with self._lock:
                self.status = "error"
                self.last_error = str(e)
                self.progress_msg = f"Scan encountered an error: {e}"
                self.finish_time = datetime.now().isoformat()


# Global singleton instance
scan_manager = ScanManager()
