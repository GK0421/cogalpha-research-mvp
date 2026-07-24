"""Factor management service."""

from __future__ import annotations

import logging
from typing import Any

from ..factors.dsl import FactorParser
from ..factors.registry import FactorRegistry
from ..factors.seed_factors import register_seed_factors
from ..persistence.database import Database
from ..persistence.models import FactorOrigin
from ..persistence.repositories import FactorRepository

logger = logging.getLogger(__name__)


class FactorService:
    """Application service for factor management."""

    def __init__(self, db: Database) -> None:
        self.db = db
        self.parser = FactorParser()

    def list_factors(self, project_id: str) -> list[dict[str, Any]]:
        with self.db.session() as session:
            repo = FactorRepository(session)
            return [self._to_dict(f) for f in repo.list_by_project(project_id)]

    def get_factor(self, factor_id: str) -> dict[str, Any] | None:
        with self.db.session() as session:
            repo = FactorRepository(session)
            f = repo.get(factor_id)
            return self._to_dict(f) if f else None

    def create_factor(
        self,
        project_id: str,
        name: str,
        expression: str,
        agent_id: str = "",
        level: int = 1,
        direction: int = 1,
        description: str = "",
        origin: str = "custom",
    ) -> dict[str, Any]:
        # Validate expression with safe DSL
        validation = self.validate_expression(expression)
        if not validation["valid"]:
            raise ValueError(f"Invalid factor expression: {validation['error']}")

        with self.db.session() as session:
            repo = FactorRepository(session)
            factor = repo.create(
                project_id=project_id,
                name=name,
                expression=expression,
                agent_id=agent_id,
                level=level,
                direction=direction,
                description=description,
                origin=FactorOrigin(origin)
                if origin in [o.value for o in FactorOrigin]
                else FactorOrigin.CUSTOM,
                expression_hash=validation["hash"],
            )
            # Update validation status
            repo.update(factor.id, validation_status="valid")
            return self._to_dict(factor)

    def update_factor(self, factor_id: str, **kwargs: Any) -> dict[str, Any] | None:
        if "expression" in kwargs:
            validation = self.validate_expression(kwargs["expression"])
            if not validation["valid"]:
                raise ValueError(f"Invalid expression: {validation['error']}")
            kwargs["expression_hash"] = validation["hash"]

        with self.db.session() as session:
            repo = FactorRepository(session)
            f = repo.update(factor_id, **kwargs)
            return self._to_dict(f) if f else None

    def delete_factor(self, factor_id: str) -> bool:
        with self.db.session() as session:
            repo = FactorRepository(session)
            return repo.delete(factor_id)

    def validate_expression(self, expression: str) -> dict[str, Any]:
        """Validate a DSL factor expression."""
        import hashlib
        import re as re_mod

        try:
            # Compute hash from expression string directly
            normalized = re_mod.sub(r"\s+", "", expression.lower())
            expr_hash = hashlib.sha256(normalized.encode()).hexdigest()
            # Try parsing
            self.parser.parse(expression)
            return {
                "valid": True,
                "hash": expr_hash,
                "error": None,
            }
        except Exception as e:
            return {
                "valid": False,
                "hash": "",
                "error": str(e),
            }

    def seed_project_factors(self, project_id: str) -> list[dict[str, Any]]:
        """Register all 21 seed factors for a project."""
        registry = FactorRegistry()
        register_seed_factors(registry)

        results = []
        with self.db.session() as session:
            repo = FactorRepository(session)
            for factor in registry.all_factors():
                f = repo.create(
                    project_id=project_id,
                    name=factor.name,
                    expression=factor.expression,
                    agent_id=factor.agent_id,
                    level=factor.level,
                    direction=factor.direction,
                    description=factor.description,
                    origin=FactorOrigin.SEED,
                    expression_hash=factor.expression_hash,
                )
                repo.update(f.id, validation_status="valid")
                results.append(self._to_dict(f))
        return results

    def generate_with_llm(
        self,
        project_id: str,
        provider: str,
        api_key: str,
        base_url: str = "",
        model: str = "",
        prompt: str = "",
    ) -> dict[str, Any]:
        """Generate factors using LLM (optional feature)."""
        if not api_key:
            return {
                "status": "LLM_PROVIDER_NOT_CONFIGURED",
                "factors": [],
                "message": "No API key configured. LLM factor generation is optional.",
            }

        # This is a placeholder for LLM integration
        # Actual implementation would call the LLM API
        return {
            "status": "LLM_GENERATION_NOT_IMPLEMENTED",
            "factors": [],
            "message": "LLM factor generation will be available in a future update.",
        }

    @staticmethod
    def _to_dict(f: Any) -> dict[str, Any]:
        return {
            "id": f.id,
            "project_id": f.project_id,
            "name": f.name,
            "agent_id": f.agent_id,
            "level": f.level,
            "expression": f.expression,
            "direction": f.direction,
            "description": f.description,
            "origin": f.origin.value if hasattr(f.origin, "value") else str(f.origin),
            "expression_hash": f.expression_hash,
            "validation_status": f.validation_status.value
            if hasattr(f.validation_status, "value")
            else str(f.validation_status),
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
