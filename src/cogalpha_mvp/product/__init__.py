"""Product module for CogAlpha Studio."""

from .paths import WorkspaceManager, get_default_home, get_workspace_root
from .version import PRODUCT_NAME, PRODUCT_VERSION, get_version

__all__ = [
    "PRODUCT_NAME",
    "PRODUCT_VERSION",
    "WorkspaceManager",
    "get_default_home",
    "get_version",
    "get_workspace_root",
]
