"""App FastAPI da frente Lucas — CompStat Rio (mapa estratégico das 8 regiões).

Sobe um único servidor que serve:
- Os routers do colega Perri (`/spatial/*`, `/relints/*`) — funcionam no modo live.
- Os routers da frente Lucas (`/map/*`, `/reports/*`).

Rodar (de backend/):       uvicorn app:app --app-dir Lucas --reload --port 8000
ou (de backend/Lucas/):    uvicorn app:app --reload --port 8000
"""
from __future__ import annotations

import pathlib
import sys

# Garante que `compstat` seja importável como pacote top-level,
# independente de como o uvicorn for lançado.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from compstat import config, perri_bridge  # noqa: E402,F401  (perri_bridge ajusta sys.path)
from compstat.routers import map_router, operations_router, reports_router  # noqa: E402

app = FastAPI(
    title="CompStat Rio — Mapa Estratégico (frente Lucas)",
    description=(
        "Mapa das 8 regiões oficiais da Força Municipal com score de risco por "
        "região, relatórios estratégicos e chat com agente LLM. Integra os scores "
        "do Perri (MCDA/H3) e a análise granular de denúncias do Arick."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["meta"])
def root():
    return {
        "name": "CompStat Rio — Mapa Estratégico (Lucas)",
        "data_mode": config.DATA_MODE,
        "llm_mode": "anthropic" if config.llm_available() else "fake",
        "endpoints": [
            "/map/regions",
            "/map/regions/{region_id}",
            "/operations/draft",
            "/reports/weekly-strategic",
            "/reports/regions/{region_id}",
            "/reports/chat",
            "/relints/agencias",
            "/spatial/priority-areas",
            "/docs",
        ],
    }


app.include_router(map_router.router)
app.include_router(reports_router.router)
app.include_router(operations_router.router)

# Routers do Perri (mesmo servidor). Dependem do submódulo de dados (modo live).
try:
    from hexagon_spatial import api as spatial_api  # type: ignore
    from hexagon_spatial import relints_api  # type: ignore

    app.include_router(spatial_api.router)
    app.include_router(relints_api.router)
except Exception as exc:  # pragma: no cover
    import logging

    logging.getLogger("uvicorn.error").warning(
        "Routers do Perri não montados (%s). Provável submódulo de dados ausente.", exc
    )
