"""Carrega o shapefile de áreas da Força Municipal e casa cada polígono ao
RELINT correspondente por similaridade de nome.

Cada agência (na verdade, sub-área operacional da Força Municipal) recebe:
- delimitação geométrica (polígono em EPSG:4326)
- o RELINT associado, com seus parâmetros estruturados
"""
from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from pathlib import Path

import geopandas as gpd
from shapely.geometry import mapping

from .relints_parser import parse_all_relints

SHAPEFILE = (
    Path(__file__).parent
    / "claude_impact_lab_compstat_rio"
    / "sh_area_forca"
    / "areas_forca_municipal.shp"
)

_STOPWORDS = {
    "de", "da", "do", "das", "dos", "e", "a", "o", "as", "os",
    "rua", "av", "avenida", "estacao", "estacoes", "estação", "estações",
    "trem", "metro", "metrô",
    # tokens muito frequentes nos nomes que não ajudam a discriminar
}


def _norm(s: str) -> set[str]:
    """Normaliza string para set de tokens (sem acento, lower, sem stopwords)."""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    tokens = re.findall(r"[a-z0-9]+", s)
    return {t for t in tokens if t not in _STOPWORDS and len(t) > 1}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


@lru_cache(maxsize=1)
def load_agency_areas() -> gpd.GeoDataFrame:
    """Carrega o shapefile e devolve GeoDataFrame em EPSG:4326."""
    gdf = gpd.read_file(SHAPEFILE)
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    elif str(gdf.crs).upper() != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")
    return gdf


def match_relints_to_areas() -> list[dict]:
    """Para cada polígono do shapefile, encontra o RELINT de melhor Jaccard.

    Devolve uma lista de dicts com fid, nome_subar, geometry (GeoJSON), bbox,
    centroide, área aproximada (km²), e o RELINT inteiro associado.
    """
    gdf = load_agency_areas()
    relints = parse_all_relints()

    # Pré-computa tokens dos títulos dos RELINTs
    relint_tokens = [(r, _norm(r["titulo"])) for r in relints]

    # Para cálculo de área em km², projeta para SIRGAS 2000 / UTM 23S (Rio).
    gdf_m = gdf.to_crs("EPSG:31983")

    out = []
    for idx, row in gdf.iterrows():
        nome = str(row["nome_subar"])
        a_tokens = _norm(nome)

        best, best_score = None, 0.0
        for r, b_tokens in relint_tokens:
            score = _jaccard(a_tokens, b_tokens)
            if score > best_score:
                best, best_score = r, score

        geom = row.geometry
        geom_m = gdf_m.loc[idx].geometry
        centroid = geom.centroid
        minx, miny, maxx, maxy = geom.bounds

        out.append({
            "fid": int(row["fid"]),
            "nome_area": nome,
            "centroide": {"lat": float(centroid.y), "lon": float(centroid.x)},
            "bbox": {
                "min_lat": float(miny), "min_lon": float(minx),
                "max_lat": float(maxy), "max_lon": float(maxx),
            },
            "area_km2": round(geom_m.area / 1e6, 4),
            "perimetro_m": round(geom_m.length, 1),
            "geometry": mapping(geom),
            "relint_match": {
                "codigo": best["codigo"] if best else None,
                "titulo": best["titulo"] if best else None,
                "score": round(best_score, 3),
            } if best else None,
        })

    return out


@lru_cache(maxsize=1)
def agencies_full_index() -> dict[int, dict]:
    """Mapeia fid → agência + RELINT completo (todos os parâmetros embutidos)."""
    relints_by_code = {r["codigo"]: r for r in parse_all_relints()}
    agencies = match_relints_to_areas()
    index: dict[int, dict] = {}
    for ag in agencies:
        relint = None
        match = ag.get("relint_match")
        if match and match["codigo"]:
            relint = relints_by_code.get(match["codigo"])
        index[ag["fid"]] = {**ag, "relint": relint}
    return index


if __name__ == "__main__":
    import json
    for ag in match_relints_to_areas():
        rm = ag["relint_match"] or {}
        print(f"fid {ag['fid']:>3}  area_km2={ag['area_km2']:6.3f}  "
              f"-> {rm.get('codigo','?')}  score={rm.get('score',0):.2f}  "
              f"| {ag['nome_area'][:55]}")
