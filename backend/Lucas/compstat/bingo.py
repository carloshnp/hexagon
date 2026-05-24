"""O "Bingo" — overlay espaço-temporal de dinâmica criminal × fatores urbanos.

Para cada micro-área (hotspot DBSCAN dentro de um polígono FM):
  ONDE (centróide) × QUANDO (horas dominantes do crime) × POR QUE (fatores que
  co-ocorrem NO TEMPO) × QUEM (órgão competente) × cobertura de câmera.

O casamento temporal evita a armadilha do briefing: um fator noturno (iluminação)
não é apontado como motivo de um crime que ocorre às 12h — `temporal_overlap` ≈ 0.
DBSCAN haversine espelha a config do Perri (`clustering.py`).
"""
from __future__ import annotations

from functools import lru_cache

import geopandas as gpd
import h3
import pandas as pd
from shapely.geometry import Point

from . import camera_coverage, competence, data_source, temporal

H3_RES = 9             # ~175 m de aresta → micro-área urbana
MIN_CRIMES = 8         # mínimo de crimes p/ a célula virar hotspot
MAX_HOTSPOTS = 6
FACTOR_RADIUS_M = 200  # fatores dentro deste raio do centróide entram no overlay
DRIVER_OVERLAP = 0.35  # overlap temporal mínimo p/ um fator ser "driver"


def _crime_points(days: int | None, fid: int) -> pd.DataFrame:
    rows = []
    occ = data_source.occurrences(days, fid)
    if occ is not None and len(occ):
        for geom, hora, mod in zip(occ.geometry, occ["hora"], occ["modalidade"]):
            rows.append((geom.y, geom.x, hora, mod, "ocorrencia"))
    den = data_source.denuncias(days, fid)
    if den is not None and len(den):
        for geom, hora, classe in zip(den.geometry, den["hora"], den["classe"]):
            rows.append((geom.y, geom.x, hora, classe, "denuncia"))
    return pd.DataFrame(rows, columns=["lat", "lon", "hora", "modalidade", "fonte"])


def _hotspot_cells(points: pd.DataFrame) -> pd.DataFrame:
    """Micro-áreas = células H3 (res 9) mais densas. Estável e dinâmico por dado/janela."""
    if len(points) == 0:
        points = points.copy()
        points["h3"] = pd.Series(dtype=str)
        return points
    points = points.copy()
    points["h3"] = [h3.latlng_to_cell(lat, lon, H3_RES)
                    for lat, lon in zip(points["lat"], points["lon"])]
    return points


def _factors_near(fid: int, lat: float, lon: float, crime_hist: dict) -> list[dict]:
    fat = data_source.fatores(fid)
    if fat is None or len(fat) == 0:
        return []
    fat_m = fat.to_crs(camera_coverage.CRS_M)
    pt = gpd.GeoSeries([Point(lon, lat)], crs="EPSG:4326").to_crs(camera_coverage.CRS_M).iloc[0]
    near = fat[fat_m.geometry.distance(pt) <= FACTOR_RADIUS_M]
    if len(near) == 0 or "tipo_ocorrencia_descricao" not in near.columns:
        return []
    out = []
    for tipo, grp in near.groupby("tipo_ocorrencia_descricao"):
        if str(tipo).strip().lower() == "sem ocorrência":
            continue
        label, hours = temporal.factor_time_profile(str(tipo))
        overlap = temporal.temporal_overlap(crime_hist, hours)
        agency = competence.agency_for_factor(str(tipo))
        time_specific = bool(hours) and hours != temporal.ALL_HOURS
        if competence.is_social_agency(agency):
            relevance = "social"               # articulação, nunca driver criminal
        elif time_specific and overlap >= DRIVER_OVERLAP:
            relevance = "driver"               # casa no TEMPO com o crime → insight do bingo
        elif not hours or hours == temporal.ALL_HOURS:
            relevance = "estrutural"           # sempre presente (esconderijo, calçada)
        else:
            relevance = "contexto"             # presente mas temporalmente descasado
        out.append({
            "tipo": str(tipo),
            "n": int(len(grp)),
            "orgao": agency,
            "esfera": competence.agency_meta(agency)["esfera"],
            "perfil_temporal": label,
            "overlap_temporal": overlap,
            "relevancia": relevance,
        })
    # drivers temporais primeiro, depois estruturais, social, contexto
    rank = {"driver": 0, "estrutural": 1, "social": 2, "contexto": 3}
    out.sort(key=lambda f: (rank[f["relevancia"]], -f["overlap_temporal"]))
    return out


@lru_cache(maxsize=32)
def region_bingo(region_id: str, days: int | None) -> dict:
    reg = data_source.region_by_id(region_id)
    if reg is None:
        return {}
    fid = reg["fid"]
    pts = _crime_points(days, fid)
    celled = _hotspot_cells(pts)
    sizes = celled["h3"].value_counts() if "h3" in celled.columns else pd.Series(dtype=int)
    sizes = sizes[sizes >= MIN_CRIMES]

    hotspots = []
    for rank_i, (cell, _) in enumerate(sizes.head(MAX_HOTSPOTS).items()):
        grp = celled[celled["h3"] == cell]
        lat, lon = h3.cell_to_latlng(cell)
        hist = temporal.hour_histogram(grp["hora"])
        dom_hours = temporal.dominant_hours(hist)
        modality = grp["modalidade"].dropna().value_counts()
        factors = _factors_near(fid, lat, lon, hist)
        drivers = [f for f in factors if f["relevancia"] == "driver"]
        social = [f for f in factors if f["relevancia"] == "social"]
        hotspots.append({
            "hotspot_id": f"{region_id}__{cell}",
            "h3_cell": cell,
            "centroid": {"lat": round(lat, 6), "lon": round(lon, 6)},
            "n_crimes": int(len(grp)),
            "dominant_modality": modality.index[0] if len(modality) else None,
            "modality_breakdown": {str(k): int(v) for k, v in modality.head(4).items()},
            "critical_hours": dom_hours,
            "critical_hours_label": temporal.fmt_hours(dom_hours),
            "temporal_profile": temporal.window_label(hist),
            "matched_factors": factors,
            "driver_factors": drivers,
            "social_factors": social,
            "camera": camera_coverage.nearest_camera(lat, lon),
        })

    # severidade relativa entre hotspots da região
    if hotspots:
        mx = max(h["n_crimes"] for h in hotspots)
        for h in hotspots:
            h["severity"] = round(h["n_crimes"] / mx * 100, 1) if mx else 0.0

    return {
        "region_id": region_id,
        "n_hotspots": len(hotspots),
        "n_crime_points": int(len(pts)),
        "hotspots": hotspots,
        "signals": _region_signals(hotspots),
    }


def _region_signals(hotspots: list[dict]) -> list[dict]:
    """Sinais cruzados de alto nível p/ a reunião (o 'bingo' resumido)."""
    signals = []
    for h in hotspots:
        gap = h["camera"].get("gap")
        if h["temporal_profile"].startswith("predominantemente noturno"):
            lighting = [f for f in h["driver_factors"]
                        if f["orgao"] in ("Rio Luz", "COMLURB")]
            if lighting:
                signals.append({
                    "hotspot_id": h["hotspot_id"],
                    "tipo": "crime_noturno_iluminacao",
                    "descricao": (f"Crime noturno ({h['critical_hours_label']}) coincide com "
                                  f"{lighting[0]['tipo']} → {lighting[0]['orgao']}."),
                    "orgao": lighting[0]["orgao"],
                })
        if gap:
            signals.append({
                "hotspot_id": h["hotspot_id"],
                "tipo": "lacuna_camera",
                "descricao": (f"Ponto crítico a {h['camera']['distance_m']:.0f} m da câmera "
                              "mais próxima — lacuna de cobertura."),
                "orgao": "FM",
            })
    return signals
