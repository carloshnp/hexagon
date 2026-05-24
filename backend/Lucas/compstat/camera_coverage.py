"""Cobertura de câmeras (CIVITAS/COR) por proximidade — só temos a LOCALIZAÇÃO.

Para cada ponto crítico (hotspot), calcula a distância à câmera mais próxima e
sinaliza lacuna de cobertura quando acima do limiar. Sem metadados, sem imagem.
"""
from __future__ import annotations

from functools import lru_cache

import geopandas as gpd
from shapely.geometry import Point

from . import data_source

CRS_M = "EPSG:31983"   # SIRGAS 2000 / UTM 23S (metros, Rio)
GAP_THRESHOLD_M = 150.0


@lru_cache(maxsize=1)
def _cameras_projected() -> gpd.GeoDataFrame | None:
    cam = data_source.cameras()
    if cam is None or len(cam) == 0:
        return None
    return cam.to_crs(CRS_M)


def nearest_camera(lat: float, lon: float) -> dict:
    """Distância (m) à câmera mais próxima + se há lacuna de cobertura."""
    cams = _cameras_projected()
    if cams is None:
        return {"distance_m": None, "gap": None, "camera": None,
                "note": "Sem dados de câmera (modo estático)."}
    pt = gpd.GeoSeries([Point(lon, lat)], crs="EPSG:4326").to_crs(CRS_M).iloc[0]
    dists = cams.geometry.distance(pt)
    idx = dists.idxmin()
    dist_m = float(dists.loc[idx])
    nearest = data_source.cameras().loc[idx].geometry
    return {
        "distance_m": round(dist_m, 1),
        "gap": dist_m > GAP_THRESHOLD_M,
        "camera": {"lat": float(nearest.y), "lon": float(nearest.x)},
    }


def coverage_for_region(fid: int) -> dict:
    """Resumo de cobertura na região: nº de câmeras + densidade aproximada."""
    cam = data_source.cameras(fid)
    n = 0 if cam is None else len(cam)
    return {"n_cameras": int(n)}
