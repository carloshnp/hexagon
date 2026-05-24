"""Router de relatórios e chat (Passos 4–6)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .. import config, reports_service
from ..schemas import ChatRequest, ChatResponse, RegionReport, WeeklyReport

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/weekly-strategic", response_model=WeeklyReport,
            summary="Relatório estratégico semanal (ranking das 8 regiões)")
def weekly_strategic(time_window: str = config.DEFAULT_TIME_WINDOW):
    return reports_service.weekly_report(time_window)


@router.get("/regions/{region_id}", response_model=RegionReport,
            summary="Relatório individual da região (lazy, gerado por agente LLM)")
def region_report(region_id: str, time_window: str = config.DEFAULT_TIME_WINDOW):
    report = reports_service.region_report(region_id, time_window)
    if report is None:
        raise HTTPException(status_code=404, detail=f"region_id {region_id} não encontrado")
    return report


@router.post("/chat", response_model=ChatResponse,
             summary="Chat com o agente sobre mapa, regiões e dados")
def chat(req: ChatRequest):
    return reports_service.chat(req.question, req.region_id, req.filters.model_dump())
