"""Settings service for application configuration."""

from __future__ import annotations

import os
from typing import Any

from ..persistence.database import Database
from ..persistence.repositories import SettingRepository

# Default settings
_DEFAULT_SETTINGS = {
    "telemetry.enabled": "false",
    "llm.enabled": "false",
    "llm.provider": "none",
    "llm.model": "",
    "llm.base_url": "",
    "api.host": "127.0.0.1",
    "api.port": "8765",
    "report.disclaimer": "RESEARCH_BACKTEST_ONLY | NO_LIVE_TRADING | NOT_INVESTMENT_ADVICE",
    "ui.language": "zh-CN",
    "data.max_upload_mb": "500",
    "jobs.max_concurrent": "1",
}


class SettingsService:
    """Application service for settings management."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def get_all(self) -> dict[str, Any]:
        with self.db.session() as session:
            repo = SettingRepository(session)
            settings = repo.get_all()
            # Merge with defaults
            result = dict(_DEFAULT_SETTINGS)
            result.update(settings)
            return result

    def get(self, key: str, default: str = "") -> str:
        with self.db.session() as session:
            repo = SettingRepository(session)
            return repo.get(key, _DEFAULT_SETTINGS.get(key, default))

    def set(self, key: str, value: str) -> None:
        with self.db.session() as session:
            repo = SettingRepository(session)
            repo.set(key, value)

    def update(self, updates: dict[str, str]) -> dict[str, Any]:
        with self.db.session() as session:
            repo = SettingRepository(session)
            for key, value in updates.items():
                repo.set(key, value)
        return self.get_all()

    def get_llm_config(self) -> dict[str, Any]:
        """Get LLM configuration (never exposes API keys)."""
        settings = self.get_all()
        return {
            "enabled": settings.get("llm.enabled", "false") == "true",
            "provider": settings.get("llm.provider", "none"),
            "model": settings.get("llm.model", ""),
            "base_url": settings.get("llm.base_url", ""),
            "key_configured": bool(self._check_any_llm_key()),
        }

    @staticmethod
    def _check_any_llm_key() -> str | bool:
        """Check if any LLM API key is set in environment."""
        for key in [
            "IFLYTEK_SPARK_API_KEY",
            "MINIMAX_API_KEY",
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "DEEPSEEK_API_KEY",
            "DASHSCOPE_API_KEY",
        ]:
            if os.environ.get(key):
                return key
        return False

    def initialize_defaults(self) -> None:
        """Initialize default settings if not present."""
        with self.db.session() as session:
            repo = SettingRepository(session)
            for key, value in _DEFAULT_SETTINGS.items():
                current = repo.get(key, "")
                if not current:
                    repo.set(key, value)
