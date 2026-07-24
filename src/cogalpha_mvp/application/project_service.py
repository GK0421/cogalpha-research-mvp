"""Project management service."""

from __future__ import annotations

import json
from typing import Any

from ..persistence.database import Database
from ..persistence.repositories import ProjectRepository


class ProjectService:
    """Application service for project management."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def create_project(
        self,
        name: str,
        description: str = "",
        market: str = "A_STOCK",
        default_config: dict | None = None,
    ) -> dict[str, Any]:
        with self.db.session() as session:
            repo = ProjectRepository(session)
            project = repo.create(
                name=name,
                description=description,
                market=market,
                default_config=default_config,
            )
            return self._to_dict(project)

    def get_project(self, project_id: str) -> dict[str, Any] | None:
        with self.db.session() as session:
            repo = ProjectRepository(session)
            project = repo.get(project_id)
            return self._to_dict(project) if project else None

    def list_projects(self) -> list[dict[str, Any]]:
        with self.db.session() as session:
            repo = ProjectRepository(session)
            return [self._to_dict(p) for p in repo.list_all()]

    def update_project(self, project_id: str, **kwargs: Any) -> dict[str, Any] | None:
        with self.db.session() as session:
            repo = ProjectRepository(session)
            project = repo.update(project_id, **kwargs)
            return self._to_dict(project) if project else None

    def delete_project(self, project_id: str, permanent: bool = False) -> bool:
        with self.db.session() as session:
            repo = ProjectRepository(session)
            return repo.delete(project_id, permanent=permanent)

    @staticmethod
    def _to_dict(project: Any) -> dict[str, Any]:
        return {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "market": project.market,
            "status": project.status.value
            if hasattr(project.status, "value")
            else str(project.status),
            "default_config": json.loads(project.default_config) if project.default_config else {},
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "updated_at": project.updated_at.isoformat() if project.updated_at else None,
        }
