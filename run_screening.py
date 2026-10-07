"""Top-level CLI runner for Agent 1 — Screening Agent."""

import sys
from pathlib import Path

# Ensure root is in sys.path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Configure safe UTF-8 output with replacement on Windows consoles if supported
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from src.screening.main import main

if __name__ == "__main__":
    main()
