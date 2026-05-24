"""Schemas Pydantic do contrato backend → frontend (frente Lucas).

Seguem o formato definido em GUIA_LUCAS_COMPSTAT_MAPA_ESTRATEGICO.md.
Campos de geometria e camadas de mapa usam `dict`/`list` por serem GeoJSON
livres; o resto é tipado.
"""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Comuns ────────────────────────────────────────────────────────────────────
class TimeWindow(BaseModel):
    preset: str = "last_30_days"
    start: Optional[str] = None
    end: Optional[str] = None
    historical_available: bool = True


class Provenance(BaseModel):
    source: str                      # ex. "Disque Denúncia", "ISP-RJ", "RELINT RI_010_2026"
    description: str = ""
    n_records: Optional[int] = None
    confidence: Optional[float] = None


class ScoreComponent(BaseModel):
    key: str                         # ocorrencias | denuncias | fatores | cameras_inv
    label: str
    raw_count: float
    normalized: float                # 0–1 entre as 8 regiões
    weight: float
    contribution: float              # weight * normalized * 100


# ── /map/regions ──────────────────────────────────────────────────────────────
class RegionProperties(BaseModel):
    region_id: str
    fid: int
    region_name: str
    risk_score: float
    risk_level: str                  # high | medium | low
    primary_agency: str
    secondary_agencies: list[str] = []
    summary: str = ""
    occurrence_count: int = 0
    denuncia_count: int = 0
    camera_count: int = 0
    urban_factor_count: int = 0
    critical_area_count: int = 0
    data_quality: dict[str, str] = {}  # fonte → "real" | "aproximado" | "indisponivel"


class RegionFeature(BaseModel):
    type: str = "Feature"
    id: str
    properties: RegionProperties
    geometry: dict[str, Any]


class RegionsFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    generated_at: str
    data_mode: str                   # live | static
    time_window: TimeWindow
    features: list[RegionFeature]


# ── /map/regions/{region_id} ───────────────────────────────────────────────────
class MapLayers(BaseModel):
    polygon: dict[str, Any] = {}
    occurrences: list[dict[str, Any]] = []
    denuncias: list[dict[str, Any]] = []
    cameras: list[dict[str, Any]] = []
    urban_factors: list[dict[str, Any]] = []
    critical_areas: list[dict[str, Any]] = []   # hotspots/células H3


class HourlyBucket(BaseModel):
    hour: int
    count: int


class OccurrenceTypeCount(BaseModel):
    tipo: str
    count: int


class RegionDetail(BaseModel):
    region: RegionProperties
    time_window: TimeWindow
    score_components: list[ScoreComponent]
    map_layers: MapLayers
    occurrence_types: list[OccurrenceTypeCount] = []
    hourly_histogram: list[HourlyBucket] = []
    occurrence_groups: list[dict[str, Any]] = []     # preenchido pelo relatório (lazy)
    regional_report: Optional[dict[str, Any]] = None  # preenchido pelo relatório (lazy)
    recommended_actions: list[dict[str, Any]] = []
    provenance: list[Provenance] = []


# ── Relatórios ──────────────────────────────────────────────────────────────
class ActionPlan(BaseModel):
    responsible_agency: str
    supporting_agencies: list[str] = []
    recommended_action: str
    priority: str = "medium"          # high | medium | low
    time_window: Optional[str] = None


class OccurrenceGroupReport(BaseModel):
    group_id: str
    summary: str
    detailed_explanation: str = ""
    score: dict[str, float] = {}      # {risk, confidence}
    action_plan: ActionPlan
    map_data: dict[str, Any] = {}
    provenance: list[Provenance] = []


class RegionReport(BaseModel):
    region_id: str
    region_name: str
    summary: str
    full_explanation: str = ""
    score: dict[str, Any] = {}        # {final, components}
    occurrences: list[OccurrenceGroupReport] = []
    uncertainties: list[str] = []
    guardrails: list[str] = []
    provenance: list[Provenance] = []
    generated_by: str = "RegionalRiskNarrativeAgent"
    llm_mode: str = "fake"            # anthropic | fake
    cached: bool = False
    audit_flags: Optional[dict[str, Any]] = None


class RankedRegion(BaseModel):
    region_id: str
    region_name: str
    risk_score: float
    risk_level: str
    primary_agency: str
    rationale: str = ""


class WeeklyReport(BaseModel):
    report_id: str
    title: str
    summary: str
    ranked_regions: list[RankedRegion] = []
    strategic_priorities: list[str] = []
    agency_matrix: list[dict[str, Any]] = []
    map_references: list[str] = []
    provenance: list[Provenance] = []
    generated_by: str = "StrategicWeeklyReportAgent"
    llm_mode: str = "fake"


# ── Chat ──────────────────────────────────────────────────────────────────────
class ChatFilters(BaseModel):
    time_window: Optional[str] = "last_30_days"
    occurrence_type: Optional[str] = None
    hour_range: Optional[list[int]] = None
    agency: Optional[str] = None


class ChatRequest(BaseModel):
    question: str
    region_id: Optional[str] = None
    filters: ChatFilters = Field(default_factory=ChatFilters)


class ChatResponse(BaseModel):
    answer: str
    region_refs: list[str] = []
    map_refs: list[str] = []
    evidence_refs: list[Provenance] = []
    limitations: list[str] = []
    agent_trace: list[str] = []
    llm_mode: str = "fake"
