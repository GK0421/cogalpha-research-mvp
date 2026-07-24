"""Pydantic schemas for API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    market: str = "A_STOCK"
    default_config: dict[str, Any] = {}


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    market: str | None = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str
    market: str
    status: str
    default_config: dict[str, Any] = {}
    created_at: str | None = None
    updated_at: str | None = None


class DatasetResponse(BaseModel):
    id: str
    project_id: str
    name: str
    source_type: str
    original_filename: str
    stored_path: str
    sha256: str
    row_count: int
    symbol_count: int
    start_date: str
    end_date: str
    schema_version: str
    quality_status: str
    quality_report: dict[str, Any] = {}
    created_at: str | None = None


class FactorCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    expression: str = Field(..., min_length=1)
    agent_id: str = ""
    level: int = Field(1, ge=1, le=7)
    direction: int = Field(1, ge=-1, le=1)
    description: str = ""
    origin: str = "custom"


class FactorUpdate(BaseModel):
    name: str | None = None
    expression: str | None = None
    direction: int | None = None
    description: str | None = None


class FactorResponse(BaseModel):
    id: str
    project_id: str
    name: str
    agent_id: str
    level: int
    expression: str
    direction: int
    description: str
    origin: str
    expression_hash: str
    validation_status: str
    created_at: str | None = None


class FactorValidateRequest(BaseModel):
    expression: str


class FactorValidateResponse(BaseModel):
    valid: bool
    hash: str = ""
    error: str | None = None


class RunCreate(BaseModel):
    dataset_id: str | None = None
    run_type: str = "full"
    config: dict[str, Any] = {}


class RunResponse(BaseModel):
    id: str
    project_id: str
    dataset_id: str | None = None
    run_type: str
    status: str
    progress: float
    current_stage: str
    config_snapshot: dict[str, Any] = {}
    started_at: str | None = None
    finished_at: str | None = None
    error_code: str
    error_message: str
    result_path: str
    created_at: str | None = None


class SettingsUpdate(BaseModel):
    updates: dict[str, str]


class ErrorResponse(BaseModel):
    error: dict[str, Any]
