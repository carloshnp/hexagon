"""Router do mapa estratégico: GET /map/regions e GET /map/regions/{region_id}."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from .. import config, data_source, region_scoring, region_view
from ..schemas import RegionDetail, RegionsFeatureCollection

router = APIRouter(prefix="/map", tags=["map"])


@router.get("/regions", response_model=RegionsFeatureCollection,
            summary="GeoJSON das 8 regiões com resumo de risco")
def get_regions(time_window: str = Query(default=config.DEFAULT_TIME_WINDOW)):
    days = config.window_to_days(time_window)
    scores = region_scoring.compute_region_scores(days)
    features = []
    for reg in data_source.regions():
        sc = scores[reg["fid"]]
        features.append({
            "type": "Feature",
            "id": reg["region_id"],
            "properties": region_view.region_properties(reg, sc, days),
            "geometry": reg["geometry"] or {},
        })
    # ordena por risco desc para conveniência do frontend
    features.sort(key=lambda f: f["properties"]["risk_score"], reverse=True)
    return {
        "type": "FeatureCollection",
        "generated_at": region_view.now_iso(),
        "data_mode": config.DATA_MODE,
        "time_window": region_view.time_window(time_window),
        "features": features,
    }


@router.get("/regions/{region_id}", response_model=RegionDetail,
            summary="Recorte granular de uma região (camadas, tipos, horários)")
def get_region(region_id: str,
               time_window: str = Query(default=config.DEFAULT_TIME_WINDOW)):
    detail = region_view.build_region_detail(region_id, time_window)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"region_id {region_id} não encontrado")
    return detail
