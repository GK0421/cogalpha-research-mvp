"""Report endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from ..dependencies import get_report_service, get_workspace

router = APIRouter()


@router.get("/runs/{run_id}/report")
async def get_report(
    run_id: str,
    svc=Depends(get_report_service),
    workspace=Depends(get_workspace),
):
    report_path = svc.get_report_path(run_id, workspace.reports_dir)
    if not report_path:
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(report_path, media_type="text/html")


@router.get("/runs/{run_id}/artifacts")
async def list_artifacts(
    run_id: str,
    svc=Depends(get_report_service),
):
    return svc.list_artifacts(run_id)
