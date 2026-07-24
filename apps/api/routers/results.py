"""Results endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_report_service, get_workspace

router = APIRouter()


@router.get("/runs/{run_id}/summary")
async def get_summary(
    run_id: str,
    svc=Depends(get_report_service),
    workspace=Depends(get_workspace),
):
    summary = svc.get_summary(run_id, workspace.runs_dir)
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    return summary


@router.get("/runs/{run_id}/factor-metrics")
async def get_factor_metrics(
    run_id: str,
    svc=Depends(get_report_service),
    workspace=Depends(get_workspace),
):
    metrics = svc.get_factor_metrics(run_id, workspace.runs_dir)
    if not metrics:
        raise HTTPException(status_code=404, detail="Factor metrics not found")
    return metrics


@router.get("/runs/{run_id}/portfolio-results")
async def get_portfolio_results(
    run_id: str,
    svc=Depends(get_report_service),
    workspace=Depends(get_workspace),
):
    results = svc.get_portfolio_results(run_id, workspace.runs_dir)
    if not results:
        raise HTTPException(status_code=404, detail="Portfolio results not found")
    return results
