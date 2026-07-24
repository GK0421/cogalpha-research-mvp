"""Research run endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_job_manager, get_run_service, get_workspace
from ..schemas import RunCreate, RunResponse

router = APIRouter()


@router.get("/projects/{project_id}/runs", response_model=list[RunResponse])
async def list_runs(project_id: str, svc=Depends(get_run_service)):
    return svc.list_runs(project_id)


@router.post("/projects/{project_id}/runs", response_model=RunResponse, status_code=201)
async def create_run(
    project_id: str,
    body: RunCreate,
    svc=Depends(get_run_service),
    job_mgr=Depends(get_job_manager),
    workspace=Depends(get_workspace),
):
    run = svc.create_run(
        project_id=project_id,
        dataset_id=body.dataset_id,
        run_type=body.run_type,
        config=body.config,
    )

    # For now, we don't auto-start the run
    # The client will call /runs/{run_id}/start to begin execution
    return run


@router.get("/runs/{run_id}", response_model=RunResponse)
async def get_run(run_id: str, svc=Depends(get_run_service)):
    run = svc.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.post("/runs/{run_id}/cancel")
async def cancel_run(run_id: str, svc=Depends(get_run_service), job_mgr=Depends(get_job_manager)):
    run = svc.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run["status"] not in ("running", "queued", "pending"):
        raise HTTPException(status_code=409, detail=f"Cannot cancel run in status: {run['status']}")
    job_mgr.cancel_run(run_id)
    return {"cancelled": True}


@router.post("/runs/{run_id}/rerun", response_model=RunResponse, status_code=201)
async def rerun(run_id: str, svc=Depends(get_run_service)):
    new_run = svc.rerun(run_id)
    if not new_run:
        raise HTTPException(status_code=404, detail="Original run not found")
    return new_run


@router.get("/runs/{run_id}/logs")
async def get_run_logs(run_id: str, svc=Depends(get_run_service), workspace=Depends(get_workspace)):
    run = svc.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    log_path = workspace.logs_dir / f"{run_id}.log"
    if log_path.exists():
        return {"logs": log_path.read_text(encoding="utf-8", errors="replace")}
    return {"logs": ""}
