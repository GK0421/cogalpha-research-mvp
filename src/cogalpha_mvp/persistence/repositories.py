"""Repository pattern for database access."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import (
    AppSetting,
    Artifact,
    Dataset,
    DatasetQualityStatus,
    FactorDefinition,
    FactorOrigin,
    FactorValidationStatus,
    Project,
    ProjectStatus,
    ResearchRun,
    RunStatus,
    RunType,
)


def _new_id() -> str:
    return str(uuid.uuid4())


class ProjectRepository:
    """CRUD operations for projects."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        name: str,
        description: str = "",
        market: str = "A_STOCK",
        default_config: dict | None = None,
    ) -> Project:
        project = Project(
            id=_new_id(),
            name=name,
            description=description,
            market=market,
            status=ProjectStatus.ACTIVE,
            default_config=json.dumps(default_config or {}),
        )
        self.session.add(project)
        self.session.flush()
        return project

    def get(self, project_id: str) -> Project | None:
        return self.session.get(Project, project_id)

    def list_all(self) -> list[Project]:
        return list(
            self.session.scalars(
                select(Project)
                .where(Project.status != ProjectStatus.DELETED)
                .order_by(Project.updated_at.desc())
            )
        )

    def update(self, project_id: str, **kwargs: Any) -> Project | None:
        project = self.get(project_id)
        if project is None:
            return None
        for key, value in kwargs.items():
            if hasattr(project, key):
                setattr(project, key, value)
        project.updated_at = datetime.utcnow()
        self.session.flush()
        return project

    def delete(self, project_id: str, permanent: bool = False) -> bool:
        project = self.get(project_id)
        if project is None:
            return False
        if permanent:
            self.session.delete(project)
        else:
            project.status = ProjectStatus.DELETED
            project.updated_at = datetime.utcnow()
        self.session.flush()
        return True


class DatasetRepository:
    """CRUD operations for datasets."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        project_id: str,
        name: str,
        source_type: str = "csv",
        original_filename: str = "",
        stored_path: str = "",
        sha256: str = "",
        row_count: int = 0,
        symbol_count: int = 0,
        start_date: str = "",
        end_date: str = "",
    ) -> Dataset:
        ds = Dataset(
            id=_new_id(),
            project_id=project_id,
            name=name,
            source_type=source_type,
            original_filename=original_filename,
            stored_path=stored_path,
            sha256=sha256,
            row_count=row_count,
            symbol_count=symbol_count,
            start_date=start_date,
            end_date=end_date,
            quality_status=DatasetQualityStatus.PENDING,
        )
        self.session.add(ds)
        self.session.flush()
        return ds

    def get(self, dataset_id: str) -> Dataset | None:
        return self.session.get(Dataset, dataset_id)

    def list_by_project(self, project_id: str) -> list[Dataset]:
        return list(
            self.session.scalars(
                select(Dataset)
                .where(Dataset.project_id == project_id)
                .order_by(Dataset.created_at.desc())
            )
        )

    def update(self, dataset_id: str, **kwargs: Any) -> Dataset | None:
        ds = self.get(dataset_id)
        if ds is None:
            return None
        for key, value in kwargs.items():
            if hasattr(ds, key):
                setattr(ds, key, value)
        self.session.flush()
        return ds

    def delete(self, dataset_id: str) -> bool:
        ds = self.get(dataset_id)
        if ds is None:
            return False
        self.session.delete(ds)
        self.session.flush()
        return True


class FactorRepository:
    """CRUD operations for factor definitions."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        project_id: str,
        name: str,
        expression: str,
        agent_id: str = "",
        level: int = 1,
        direction: int = 1,
        description: str = "",
        origin: FactorOrigin = FactorOrigin.SEED,
        expression_hash: str = "",
    ) -> FactorDefinition:
        factor = FactorDefinition(
            id=_new_id(),
            project_id=project_id,
            name=name,
            agent_id=agent_id,
            level=level,
            expression=expression,
            direction=direction,
            description=description,
            origin=origin,
            expression_hash=expression_hash,
            validation_status=FactorValidationStatus.PENDING,
        )
        self.session.add(factor)
        self.session.flush()
        return factor

    def get(self, factor_id: str) -> FactorDefinition | None:
        return self.session.get(FactorDefinition, factor_id)

    def list_by_project(self, project_id: str) -> list[FactorDefinition]:
        return list(
            self.session.scalars(
                select(FactorDefinition)
                .where(FactorDefinition.project_id == project_id)
                .order_by(FactorDefinition.level, FactorDefinition.name)
            )
        )

    def update(self, factor_id: str, **kwargs: Any) -> FactorDefinition | None:
        factor = self.get(factor_id)
        if factor is None:
            return None
        for key, value in kwargs.items():
            if hasattr(factor, key):
                setattr(factor, key, value)
        self.session.flush()
        return factor

    def delete(self, factor_id: str) -> bool:
        factor = self.get(factor_id)
        if factor is None:
            return False
        self.session.delete(factor)
        self.session.flush()
        return True


class RunRepository:
    """CRUD operations for research runs."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        project_id: str,
        dataset_id: str | None = None,
        run_type: RunType = RunType.FULL,
        config_snapshot: dict | None = None,
    ) -> ResearchRun:
        run = ResearchRun(
            id=_new_id(),
            project_id=project_id,
            dataset_id=dataset_id,
            run_type=run_type,
            status=RunStatus.PENDING,
            progress=0.0,
            current_stage="INITIALIZING",
            config_snapshot=json.dumps(config_snapshot or {}),
        )
        self.session.add(run)
        self.session.flush()
        return run

    def get(self, run_id: str) -> ResearchRun | None:
        return self.session.get(ResearchRun, run_id)

    def list_by_project(self, project_id: str) -> list[ResearchRun]:
        return list(
            self.session.scalars(
                select(ResearchRun)
                .where(ResearchRun.project_id == project_id)
                .order_by(ResearchRun.created_at.desc())
            )
        )

    def update(self, run_id: str, **kwargs: Any) -> ResearchRun | None:
        run = self.get(run_id)
        if run is None:
            return None
        for key, value in kwargs.items():
            if hasattr(run, key):
                setattr(run, key, value)
        self.session.flush()
        return run

    def list_interrupted(self) -> list[ResearchRun]:
        """Find runs that were interrupted (running when process died)."""
        return list(
            self.session.scalars(
                select(ResearchRun).where(
                    ResearchRun.status.in_([RunStatus.RUNNING, RunStatus.QUEUED])
                )
            )
        )


class ArtifactRepository:
    """CRUD operations for artifacts."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        run_id: str,
        artifact_type: str,
        name: str = "",
        relative_path: str = "",
        sha256: str = "",
    ) -> Artifact:
        artifact = Artifact(
            id=_new_id(),
            run_id=run_id,
            artifact_type=artifact_type,
            name=name,
            relative_path=relative_path,
            sha256=sha256,
        )
        self.session.add(artifact)
        self.session.flush()
        return artifact

    def list_by_run(self, run_id: str) -> list[Artifact]:
        return list(
            self.session.scalars(
                select(Artifact).where(Artifact.run_id == run_id).order_by(Artifact.created_at)
            )
        )


class SettingRepository:
    """CRUD operations for app settings."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, key: str, default: str = "") -> str:
        setting = self.session.get(AppSetting, key)
        return setting.value if setting else default

    def set(self, key: str, value: str) -> AppSetting:
        setting = self.session.get(AppSetting, key)
        if setting:
            setting.value = value
            setting.updated_at = datetime.utcnow()
        else:
            setting = AppSetting(key=key, value=value)
            self.session.add(setting)
        self.session.flush()
        return setting

    def get_all(self) -> dict[str, str]:
        settings = list(self.session.scalars(select(AppSetting)))
        return {s.key: s.value for s in settings}

    def delete(self, key: str) -> bool:
        setting = self.session.get(AppSetting, key)
        if setting is None:
            return False
        self.session.delete(setting)
        self.session.flush()
        return True
