"""FastAPI router exposing spatial pipeline results."""
from functools import lru_cache
from typing import List

from fastapi import APIRouter, Query
from pydantic import BaseModel

from .pipeline import run_pipeline

router = APIRouter(prefix="/spatial", tags=["spatial"])


class PriorityArea(BaseModel):
    h3_cell: str
    lat: float
    lon: float
    score: float
    cnt_ocorrencias: float
    cnt_denuncias: float
    cnt_fatores: float
    cnt_cameras: float


class PipelineResult(BaseModel):
    elapsed_seconds: float
    total_cells_scored: int
    n_hotspot_clusters: int
    top_areas: List[PriorityArea]


@lru_cache(maxsize=1)
def _cached_pipeline(top_n: int) -> dict:
    result = run_pipeline(top_n=top_n, verbose=False)
    result.pop("score_df", None)
    result.pop("clustered_df", None)
    return result


@router.get("/priority-areas", response_model=PipelineResult)
def get_priority_areas(top_n: int = Query(default=5, ge=1, le=50)):
    """Return top N priority areas by MCDA score."""
    return _cached_pipeline(top_n)


@router.post("/priority-areas/refresh", response_model=PipelineResult)
def refresh_priority_areas(top_n: int = Query(default=5, ge=1, le=50)):
    """Force pipeline recompute (clears cache)."""
    _cached_pipeline.cache_clear()
    return _cached_pipeline(top_n)
