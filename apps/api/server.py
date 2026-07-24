"""API server entry point for uvicorn."""

from __future__ import annotations

import logging
import os

from .main import create_app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = create_app()

# Default: localhost-only binding for security
DEFAULT_HOST = os.environ.get("COGALPHA_HOST", "127.0.0.1")
DEFAULT_PORT = int(os.environ.get("COGALPHA_PORT", "8765"))


def run() -> None:
    """Run the API server."""
    import uvicorn

    host = DEFAULT_HOST
    port = DEFAULT_PORT

    logger.info("Starting %s on %s:%d", "CogAlpha Studio API", host, port)
    if host == "127.0.0.1":
        logger.info("Localhost-only binding (secure default)")

    uvicorn.run(
        "apps.api.server:app",
        host=host,
        port=port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    run()
