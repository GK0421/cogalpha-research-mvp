"""Settings endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..dependencies import get_settings_service
from ..schemas import SettingsUpdate

router = APIRouter()


@router.get("/settings")
async def get_settings(svc=Depends(get_settings_service)):
    return svc.get_all()


@router.patch("/settings")
async def update_settings(body: SettingsUpdate, svc=Depends(get_settings_service)):
    return svc.update(body.updates)


@router.get("/settings/llm")
async def get_llm_config(svc=Depends(get_settings_service)):
    return svc.get_llm_config()
