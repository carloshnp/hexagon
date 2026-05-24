"""Router de operações: GET /operations/draft — rascunho de emprego dos agentes."""
from __future__ import annotations

from fastapi import APIRouter, Query

from .. import cache, config, operations
from ..agents import operation_draft, provider

router = APIRouter(prefix="/operations", tags=["operations"])


@router.get("/draft", summary="Rascunho operacional: alocação dos agentes da FM por polígono/hotspot")
def get_draft(
    time_window: str = Query(default=config.DEFAULT_TIME_WINDOW),
    total_agents: int = Query(default=operations.DEFAULT_TOTAL_AGENTS, ge=1, le=5000),
):
    days = config.window_to_days(time_window)
    key = cache.make_key("operation_draft", days, total_agents, provider.get_provider().mode)

    def _compute():
        draft = operations.operation_draft(days, total_agents)
        return operation_draft.narrate(draft)

    result, cached = cache.get_or_compute(key, _compute)
    return {**result, "time_window": time_window, "cached": cached}
