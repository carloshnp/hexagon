"""FastAPI router para agências (áreas da Força Municipal) e seus RELINTs."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .agency_areas import agencies_full_index, match_relints_to_areas
from .relints_parser import FATOR_LABELS, FATORES, parse_all_relints

router = APIRouter(prefix="/relints", tags=["relints"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class Centroide(BaseModel):
    lat: float
    lon: float


class BBox(BaseModel):
    min_lat: float
    min_lon: float
    max_lat: float
    max_lon: float


class RelintMatch(BaseModel):
    codigo: Optional[str]
    titulo: Optional[str]
    score: float


class AgencyArea(BaseModel):
    fid: int
    nome_area: str
    centroide: Centroide
    bbox: BBox
    area_km2: float
    perimetro_m: float
    relint_match: Optional[RelintMatch] = None


class Subarea(BaseModel):
    nome: str
    descricao: str
    fatores: dict[str, Optional[str]]
    fechamento: str = ""


class Conclusao(BaseModel):
    texto: str
    necessidades: list[str]
    fechamento: str = ""


class Relint(BaseModel):
    codigo: str
    arquivo: str
    titulo: str
    introducao: str = ""
    n_subareas: int
    subareas: list[Subarea]
    conclusao: Conclusao


class AgencyFull(AgencyArea):
    geometry: dict  # GeoJSON Polygon/MultiPolygon
    relint: Optional[Relint] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/parametros", summary="Lista os 5 parâmetros padronizados dos RELINTs")
def get_parametros() -> dict[str, str]:
    """Devolve a chave canônica → rótulo legível dos fatores estruturados."""
    return {k: FATOR_LABELS[k] for k in FATORES}


@router.get(
    "/agencias",
    response_model=list[AgencyArea],
    summary="Lista todas as agências (áreas da Força Municipal) delimitadas",
)
def list_agencias():
    """Sem geometria — devolve metadados, bbox, centróide e RELINT associado."""
    rows = match_relints_to_areas()
    # remove geometry para resposta compacta
    return [{k: v for k, v in r.items() if k != "geometry"} for r in rows]


@router.get(
    "/agencias/{fid}",
    response_model=AgencyFull,
    summary="Detalha uma agência com geometria e RELINT estruturado completo",
)
def get_agencia(
    fid: int,
    include_geometry: bool = Query(default=True, description="Incluir o polígono GeoJSON"),
):
    index = agencies_full_index()
    if fid not in index:
        raise HTTPException(status_code=404, detail=f"fid {fid} não encontrado")
    ag = dict(index[fid])
    if not include_geometry:
        ag.pop("geometry", None)
        ag["geometry"] = {"type": "Polygon", "coordinates": []}
    return ag


@router.get(
    "/",
    response_model=list[Relint],
    summary="Lista todos os RELINTs parseados com parâmetros estruturados",
)
def list_relints():
    return list(parse_all_relints())


@router.get(
    "/{codigo}",
    response_model=Relint,
    summary="Devolve um RELINT pelo código (ex. RI_010_2026)",
)
def get_relint(codigo: str):
    for r in parse_all_relints():
        if r["codigo"] == codigo:
            return r
    raise HTTPException(status_code=404, detail=f"RELINT {codigo} não encontrado")
