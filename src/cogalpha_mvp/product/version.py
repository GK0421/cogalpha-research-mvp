"""Product version information."""

from __future__ import annotations

import pathlib


def get_version() -> str:
    """Get product version from VERSION file."""
    version_file = pathlib.Path(__file__).parent.parent.parent.parent / "VERSION"
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip()
    return "0.0.0"


PRODUCT_NAME = "CogAlpha Studio"
PRODUCT_VERSION = get_version()
PRODUCT_SUBTITLE_EN = "Local-first quantitative factor research workspace"
PRODUCT_SUBTITLE_CN = "本地优先的量化因子研究工作台"
