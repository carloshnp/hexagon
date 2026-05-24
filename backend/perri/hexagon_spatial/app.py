"""Aplicação FastAPI agregando os routers do CIVITAS Spatial."""
from fastapi import FastAPI

from . import api as spatial_api
from . import relints_api

app = FastAPI(
    title="CIVITAS — Spatial & RELINTs API",
    description=(
        "Endpoints para áreas prioritárias (MCDA/H3) e para as 8 sub-áreas da "
        "Força Municipal com seus Relatórios de Inteligência (RELINTs)."
    ),
    version="0.2.0",
)


@app.get("/", tags=["meta"])
def root():
    return {
        "name": "CIVITAS Spatial API",
        "endpoints": [
            "/spatial/priority-areas",
            "/relints/parametros",
            "/relints/agencias",
            "/relints/agencias/{fid}",
            "/relints/",
            "/relints/{codigo}",
            "/docs",
        ],
    }


app.include_router(spatial_api.router)
app.include_router(relints_api.router)
