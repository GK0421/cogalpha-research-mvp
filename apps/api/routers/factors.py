"""Factor endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_factor_service
from ..schemas import (
    FactorCreate,
    FactorResponse,
    FactorUpdate,
    FactorValidateRequest,
    FactorValidateResponse,
)

router = APIRouter()


@router.get("/projects/{project_id}/factors", response_model=list[FactorResponse])
async def list_factors(project_id: str, svc=Depends(get_factor_service)):
    return svc.list_factors(project_id)


@router.post("/projects/{project_id}/factors", response_model=FactorResponse, status_code=201)
async def create_factor(project_id: str, body: FactorCreate, svc=Depends(get_factor_service)):
    try:
        return svc.create_factor(
            project_id=project_id,
            name=body.name,
            expression=body.expression,
            agent_id=body.agent_id,
            level=body.level,
            direction=body.direction,
            description=body.description,
            origin=body.origin,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/projects/{project_id}/factors/validate", response_model=FactorValidateResponse)
async def validate_factor(
    project_id: str, body: FactorValidateRequest, svc=Depends(get_factor_service)
):
    return svc.validate_expression(body.expression)


@router.post("/projects/{project_id}/factors/seed", response_model=list[FactorResponse])
async def seed_factors(project_id: str, svc=Depends(get_factor_service)):
    """Register all 21 seed factors for a project."""
    return svc.seed_project_factors(project_id)


@router.post("/projects/{project_id}/factors/generate")
async def generate_factors(
    project_id: str,
    provider: str = "",
    model: str = "",
    prompt: str = "",
    svc=Depends(get_factor_service),
):
    import os

    api_key = ""
    for key in [
        "IFLYTEK_SPARK_API_KEY",
        "MINIMAX_API_KEY",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "DEEPSEEK_API_KEY",
        "DASHSCOPE_API_KEY",
    ]:
        if os.environ.get(key):
            api_key = os.environ[key]
            if not provider:
                provider = key.replace("_API_KEY", "").lower()
            break
    return svc.generate_with_llm(
        project_id=project_id,
        provider=provider,
        api_key=api_key,
        model=model,
        prompt=prompt,
    )


@router.get("/factors/{factor_id}", response_model=FactorResponse)
async def get_factor(factor_id: str, svc=Depends(get_factor_service)):
    f = svc.get_factor(factor_id)
    if not f:
        raise HTTPException(status_code=404, detail="Factor not found")
    return f


@router.patch("/factors/{factor_id}", response_model=FactorResponse)
async def update_factor(factor_id: str, body: FactorUpdate, svc=Depends(get_factor_service)):
    try:
        updates = body.model_dump(exclude_none=True)
        f = svc.update_factor(factor_id, **updates)
        if not f:
            raise HTTPException(status_code=404, detail="Factor not found")
        return f
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.delete("/factors/{factor_id}")
async def delete_factor(factor_id: str, svc=Depends(get_factor_service)):
    success = svc.delete_factor(factor_id)
    if not success:
        raise HTTPException(status_code=404, detail="Factor not found")
    return {"deleted": True}
