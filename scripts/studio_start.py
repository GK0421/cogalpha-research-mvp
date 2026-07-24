# -*- coding: utf-8 -*-
"""
CogAlpha Studio - Quick Start Script

Usage:
    python scripts/studio_start.py [--host HOST] [--port PORT] [--dev]

Options:
    --host HOST     API host (default: 127.0.0.1, localhost-only)
    --port PORT     API port (default: 8765)
    --dev           Start in development mode (also starts frontend dev server)
"""

from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys
import webbrowser
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description="Start CogAlpha Studio")
    parser.add_argument("--host", default="127.0.0.1", help="API host")
    parser.add_argument("--port", type=int, default=8765, help="API port")
    parser.add_argument("--dev", action="store_true", help="Development mode")
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    # Set environment
    os.environ["COGALPHA_HOST"] = args.host
    os.environ["COGALPHA_PORT"] = str(args.port)

    logger.info("=" * 60)
    logger.info("  CogAlpha Studio v0.2.0")
    logger.info("  Local-first quantitative factor research workspace")
    logger.info("  RESEARCH_BACKTEST_ONLY | NO_LIVE_TRADING")
    logger.info("=" * 60)

    if args.dev:
        logger.info("Starting in DEVELOPMENT mode...")
        logger.info("  Backend:  http://%s:%d/api/docs", args.host, args.port)
        logger.info("  Frontend: http://127.0.0.1:5173")

        # Start backend
        backend_proc = subprocess.Popen(
            [sys.executable, "-m", "apps.api.server"],
            cwd=project_root,
            env=os.environ.copy(),
        )

        # Start frontend dev server
        frontend_dir = project_root / "apps" / "web"
        if (frontend_dir / "node_modules").exists():
            frontend_proc = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=frontend_dir,
                env=os.environ.copy(),
            )
        else:
            logger.warning("Frontend node_modules not found. Run: cd apps/web && npm install")
            frontend_proc = None

        try:
            logger.info("Press Ctrl+C to stop...")
            backend_proc.wait()
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            backend_proc.terminate()
            if frontend_proc:
                frontend_proc.terminate()
    else:
        logger.info("Starting in PRODUCTION mode...")
        logger.info("  API:  http://%s:%d/api/docs", args.host, args.port)
        logger.info("  Host: %s", args.host)
        if args.host == "127.0.0.1":
            logger.info("  (localhost-only binding - secure default)")

        # Try to open browser
        url = f"http://{args.host}:{args.port}/api/docs"
        try:
            webbrowser.open(url)
            logger.info("Browser opened to %s", url)
        except Exception:
            logger.info("Open browser to %s", url)

        # Run uvicorn directly
        import uvicorn
        uvicorn.run(
            "apps.api.server:app",
            host=args.host,
            port=args.port,
            log_level="info",
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
