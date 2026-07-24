"""Dataset endpoints."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from ..dependencies import get_dataset_service, get_workspace
from ..schemas import DatasetResponse

router = APIRouter()


@router.get("/projects/{project_id}/datasets", response_model=list[DatasetResponse])
async def list_datasets(project_id: str, svc=Depends(get_dataset_service)):
    return svc.list_datasets(project_id)


@router.post(
    "/projects/{project_id}/datasets/upload", response_model=DatasetResponse, status_code=201
)
async def upload_dataset(
    project_id: str,
    file: UploadFile = File(...),
    svc=Depends(get_dataset_service),
    workspace=Depends(get_workspace),
):
    # Security: validate filename
    filename = file.filename or "upload.csv"
    ext = Path(filename).suffix.lower()
    if ext not in (".csv", ".parquet"):
        raise HTTPException(status_code=400, detail="Only CSV and Parquet files are supported")

    file_data = await file.read()
    storage_dir = workspace.datasets_dir / project_id
    try:
        return svc.upload_dataset(project_id, filename, file_data, storage_dir)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Upload failed") from e


@router.post(
    "/projects/{project_id}/datasets/register-local",
    response_model=DatasetResponse,
    status_code=201,
)
async def register_local(
    project_id: str,
    name: str,
    file_path: str,
    svc=Depends(get_dataset_service),
):
    try:
        return svc.register_local(project_id, name, file_path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/datasets/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(dataset_id: str, svc=Depends(get_dataset_service)):
    ds = svc.get_dataset(dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return ds


@router.post("/datasets/{dataset_id}/validate")
async def validate_dataset(dataset_id: str, svc=Depends(get_dataset_service)):
    try:
        return svc.validate_dataset(dataset_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/datasets/{dataset_id}/quality-report")
async def get_quality_report(dataset_id: str, svc=Depends(get_dataset_service)):
    ds = svc.get_dataset(dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return ds.get("quality_report", {})


@router.get("/datasets/{dataset_id}/preview")
async def preview_dataset(
    dataset_id: str,
    n_rows: int = 50,
    svc=Depends(get_dataset_service),
):
    try:
        return svc.preview_dataset(dataset_id, n_rows)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.delete("/datasets/{dataset_id}")
async def delete_dataset(
    dataset_id: str,
    delete_file: bool = False,
    confirm: bool = False,
    svc=Depends(get_dataset_service),
):
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Confirmation required: pass confirm=true",
        )
    success = svc.delete_dataset(dataset_id, delete_file=delete_file)
    if not success:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return {"deleted": True, "file_deleted": delete_file}
