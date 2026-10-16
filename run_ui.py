"""CLI runner for the Swing-AI Web Research Interface."""

import sys
import argparse
from pathlib import Path
import uvicorn

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Safe Windows UTF-8 stdout
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="Swing-AI: Minimal Desktop Financial Research Interface")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host interface to bind to (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable automatic code reloading during development")
    args = parser.parse_args()

    banner = f"""
==========================================================================================
                     SWING-AI -- FINANCIAL RESEARCH & TRADING UI                         
              Agent 1 (Discovery) | Agent 2 (Technical) | Agent 3 (Fundamental)          
==========================================================================================
  * Local URL: http://{args.host}:{args.port}
  * API Docs : http://{args.host}:{args.port}/docs
  * Market   : NSE (India)
==========================================================================================
"""
    print(banner.strip())
    print("\nStarting Swing-AI server... Press CTRL+C to stop.\n")

    uvicorn.run(
        "src.api.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )


if __name__ == "__main__":
    main()
