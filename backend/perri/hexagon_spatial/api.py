"""FastAPI router expondo resultados do pipeline espacial.

Aceita filtro temporal `days` ∈ {1, 3, 7}. Quando omitido, considera todo o
histórico disponível no submódulo de dados.
"""
from functools import lru_cache
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .pipeline import run_pipeline

router = APIRouter(prefix="/spatial", tags=["spatial"])

ALLOWED_DAYS = {1, 3, 7}


def _validate_days(days: Optional[int]) -> Optional[int]:
    if days is not None and days not in ALLOWED_DAYS:
        raise HTTPException(
            status_code=422,
            detail=f"days deve ser um de {sorted(ALLOWED_DAYS)} ou omitido (todo histórico)",
        )
    return days

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class GeneralPriorityArea(BaseModel):
    h3_cell: str
    lat: float
    lon: float
    score: float
    cnt_ocorrencias: float
    cnt_denuncias: float
    cnt_fatores: float
    cnt_cameras: float


class InstitutionPriorityArea(BaseModel):
    h3_cell: str
    lat: float
    lon: float
    score: float
    cnt_ocorr: float
    cnt_den: float
    cnt_fat: float
    cnt_cameras: float


class ScoreGeral(BaseModel):
    descricao: str
    top_areas: List[GeneralPriorityArea]


class InstitutionScore(BaseModel):
    instituicao: str
    mandato: str
    pesos: dict[str, float]
    total_celulas: int
    top_areas: List[InstitutionPriorityArea]


class PipelineResult(BaseModel):
    elapsed_seconds: float
    filtro_dias: Optional[int] = None
    as_of_date: Optional[str] = None
    n_ocorrencias_usadas: int
    n_denuncias_usadas: int
    total_cells_scored: int
    n_hotspot_clusters: int
    score_geral: ScoreGeral
    scores_por_instituicao: dict[str, InstitutionScore]


# ---------------------------------------------------------------------------
# Cache + endpoints
# ---------------------------------------------------------------------------

@lru_cache(maxsize=16)
def _cached_pipeline(top_n: int, days: Optional[int]) -> dict:
    result = run_pipeline(top_n=top_n, days=days, verbose=False)
    result.pop("_score_df", None)
    result.pop("_clustered_df", None)
    return result


@router.get("/priority-areas", response_model=PipelineResult)
def get_priority_areas(
    top_n: int = Query(default=5, ge=1, le=50, description="Quantas células por ranking"),
    days: Optional[int] = Query(
        default=None,
        description="Janela temporal em dias: 1, 3 ou 7 (a partir da data mais recente do dataset). Omita para usar todo o histórico.",
    ),
):
    """Top-N áreas prioritárias. Cacheado por (top_n, days)."""
    return _cached_pipeline(top_n, _validate_days(days))


@router.post("/priority-areas/refresh", response_model=PipelineResult)
def refresh_priority_areas(
    top_n: int = Query(default=5, ge=1, le=50),
    days: Optional[int] = Query(default=None),
):
    """Limpa o cache e recomputa."""
    _cached_pipeline.cache_clear()
    return _cached_pipeline(top_n, _validate_days(days))
