"""Health and system info endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from cogalpha_mvp.product.version import PRODUCT_NAME, PRODUCT_SUBTITLE_EN, PRODUCT_VERSION

from ..dependencies import get_workspace

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok", "product": PRODUCT_NAME, "version": PRODUCT_VERSION}


@router.get("/version")
async def version():
    return {
        "product": PRODUCT_NAME,
        "version": PRODUCT_VERSION,
        "subtitle": PRODUCT_SUBTITLE_EN,
    }


@router.get("/capabilities")
async def capabilities():
    return {
        "product": PRODUCT_NAME,
        "version": PRODUCT_VERSION,
        "features": [
            "project_management",
            "data_import",
            "data_quality",
            "factor_lab",
            "safe_dsl",
            "seed_factors",
            "quality_pipeline",
            "factor_evaluation",
            "deduplication",
            "oos_validation",
            "backtest",
            "reporting",
            "optional_llm",
        ],
        "seed_factors_count": 21,
        "llm_required": False,
        "trading_enabled": False,
        "research_only": True,
    }


@router.get("/workspace-info")
async def workspace_info(workspace=Depends(get_workspace)):
    return workspace.get_info()
