"""Project management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_project_service
from ..schemas import ProjectCreate, ProjectResponse, ProjectUpdate

router = APIRouter()


@router.get("/projects", response_model=list[ProjectResponse])
async def list_projects(svc=Depends(get_project_service)):
    return svc.list_projects()


@router.post("/projects", response_model=ProjectResponse, status_code=201)
async def create_project(body: ProjectCreate, svc=Depends(get_project_service)):
    return svc.create_project(
        name=body.name,
        description=body.description,
        market=body.market,
        default_config=body.default_config,
    )


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, svc=Depends(get_project_service)):
    project = svc.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, body: ProjectUpdate, svc=Depends(get_project_service)):
    updates = body.model_dump(exclude_none=True)
    project = svc.update_project(project_id, **updates)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: str,
    permanent: bool = False,
    confirm: bool = False,
    svc=Depends(get_project_service),
):
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Confirmation required: pass confirm=true to delete",
        )
    success = svc.delete_project(project_id, permanent=permanent)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"deleted": True, "permanent": permanent}
