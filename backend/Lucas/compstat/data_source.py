"""Camada de dados híbrida da frente Lucas.

Une as fontes já produzidas pelos colegas e entrega tudo recortado pelas 8
regiões oficiais:

- Geometria + RELINT das 8 regiões  → Perri (`relints.json` estático ou shapefile live)
- Ocorrências (ISP-RJ)              → Perri loaders (modo live) / proxy H3 (estático)
- Denúncias + relatos (Disque)      → Arick `disk_denuncia.csv` (sempre presente)
- Câmeras / fatores urbanos         → Perri loaders (modo live)
- Células H3 priorizadas (MCDA)     → exports do Perri (sempre)

Tudo é cacheado em memória. O join ponto-em-polígono usa geopandas.
"""
from __future__ import annotations

import json
from functools import lru_cache

import geopandas as gpd
import pandas as pd
from shapely.geometry import shape

from . import config, perri_bridge

CRS = "EPSG:4326"


# ── Regiões (geometria + RELINT) ─────────────────────────────────────────────
@lru_cache(maxsize=1)
def _regions_raw() -> list[dict]:
    """Lista bruta de agências (geometria + RELINT) — live (shapefile) ou estático."""
    if config.DATA_MODE == "live":
        try:
            idx = perri_bridge.get_agencies_full_index()
            return [dict(v) for v in idx.values()]
        except Exception:
            pass  # cai para estático se o shapefile/deps falharem
    with open(config.RELINTS_JSON, encoding="utf-8") as f:
        return json.load(f)["agencias"]


@lru_cache(maxsize=1)
def regions() -> list[dict]:
    """Regiões enriquecidas com region_id e polígono shapely.

    Cada item: fid, region_id, region_name, geometry (GeoJSON dict),
    centroide, bbox, area_km2, perimetro_m, relint, _polygon (shapely).
    """
    out = []
    for ag in _regions_raw():
        fid = int(ag["fid"])
        geom = ag.get("geometry")
        polygon = shape(geom) if geom and geom.get("coordinates") else None
        out.append({
            "fid": fid,
            "region_id": config.fid_to_region_id(fid),
            "region_name": ag.get("nome_area", ""),
            "geometry": geom,
            "centroide": ag.get("centroide"),
            "bbox": ag.get("bbox"),
            "area_km2": ag.get("area_km2"),
            "perimetro_m": ag.get("perimetro_m"),
            "relint": ag.get("relint"),
            "relint_match": ag.get("relint_match"),
            "_polygon": polygon,
        })
    return out


def region_by_id(region_id: str) -> dict | None:
    for r in regions():
        if r["region_id"] == region_id:
            return r
    return None


@lru_cache(maxsize=1)
def _regions_gdf() -> gpd.GeoDataFrame:
    rows = [{"fid": r["fid"], "geometry": r["_polygon"]}
            for r in regions() if r["_polygon"] is not None]
    return gpd.GeoDataFrame(rows, geometry="geometry", crs=CRS)


def _assign_region(gdf_points: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Anexa a coluna `fid` a cada ponto via join espacial (within)."""
    if gdf_points.empty:
        gdf_points = gdf_points.copy()
        gdf_points["fid"] = pd.Series(dtype="Int64")
        return gdf_points
    joined = gpd.sjoin(
        gdf_points, _regions_gdf(), how="left", predicate="within"
    )
    # sjoin pode duplicar se polígonos se sobrepõem; mantém a 1ª atribuição
    joined = joined[~joined.index.duplicated(keep="first")]
    return joined.drop(columns=[c for c in ("index_right",) if c in joined.columns])


# ── Denúncias + relatos (Arick, sempre presente) ─────────────────────────────
@lru_cache(maxsize=1)
def _denuncias_all() -> gpd.GeoDataFrame:
    df = pd.read_csv(
        config.DISK_DENUNCIA_CSV,
        sep=";",
        encoding="latin-1",
        low_memory=False,
        usecols=[
            "numero_denuncia", "data_denuncia", "bairro_logradouro",
            "latitude", "longitude", "assuntos.classe",
            "assuntos.tipos.tipo", "relato_redacted",
        ],
    )
    for col in ["latitude", "longitude"]:
        df[col] = (
            df[col].astype(str).str.replace(",", ".", regex=False)
            .pipe(pd.to_numeric, errors="coerce")
        )
    df = df.dropna(subset=["latitude", "longitude"])
    df["data_denuncia"] = pd.to_datetime(df["data_denuncia"], errors="coerce")
    df = df.rename(columns={
        "assuntos.classe": "classe",
        "assuntos.tipos.tipo": "tipo",
        "relato_redacted": "relato",
        "bairro_logradouro": "bairro",
        "data_denuncia": "data",
    })
    df["hora"] = df["data"].dt.hour
    gdf = gpd.GeoDataFrame(
        df, geometry=gpd.points_from_xy(df["longitude"], df["latitude"]), crs=CRS
    )
    return _assign_region(gdf)


def _apply_days(gdf: gpd.GeoDataFrame, date_col: str, days: int | None) -> gpd.GeoDataFrame:
    if not days:
        return gdf
    valid = gdf[gdf[date_col].notna()]
    if valid.empty:
        return gdf.iloc[0:0]
    cutoff = valid[date_col].max() - pd.Timedelta(days=days)
    return gdf[gdf[date_col].notna() & (gdf[date_col] > cutoff)]


def denuncias(days: int | None = None, fid: int | None = None) -> gpd.GeoDataFrame:
    gdf = _apply_days(_denuncias_all(), "data", days)
    if fid is not None:
        gdf = gdf[gdf["fid"] == fid]
    return gdf


# ── Ocorrências (ISP-RJ) — só no modo live ───────────────────────────────────
# Loader próprio (o do Perri não traz `hora`/`dia_semana`, essenciais p/ o bingo).
# A coluna `hora` vem como "HH:MM:SS"; `data` tem outliers, mas serve p/ a janela.
@lru_cache(maxsize=1)
def _occurrences_full() -> gpd.GeoDataFrame | None:
    if config.DATA_MODE != "live":
        return None
    try:
        path = next(config.DADOS_DIR.glob("df_ocorrencias_tratado*.csv"))
        df = pd.read_csv(
            path, low_memory=False,
            usecols=["data", "hora", "dia_semana", "delito", "desc_delito",
                     "longitude", "latitude"],
        )
        df = df.dropna(subset=["latitude", "longitude"])
        df["data"] = pd.to_datetime(df["data"], dayfirst=True, errors="coerce")
        df["hora"] = pd.to_numeric(
            df["hora"].astype(str).str.slice(0, 2), errors="coerce"
        )
        df = df.rename(columns={"desc_delito": "modalidade"})
        gdf = gpd.GeoDataFrame(
            df, geometry=gpd.points_from_xy(df["longitude"], df["latitude"]), crs=CRS
        )
        return _assign_region(gdf)
    except Exception:
        return None


def occurrences(days: int | None = None, fid: int | None = None) -> gpd.GeoDataFrame | None:
    gdf = _occurrences_full()
    if gdf is None:
        return None
    if days:
        gdf = _apply_days(gdf, "data", days)
    if fid is not None:
        gdf = gdf[gdf["fid"] == fid]
    return gdf


# ── Câmeras e fatores urbanos — só no modo live ──────────────────────────────
@lru_cache(maxsize=1)
def _cameras_all() -> gpd.GeoDataFrame | None:
    if config.DATA_MODE != "live":
        return None
    try:
        gdf = perri_bridge.get_loaders().load_cameras().copy()
        # se vierem como polígonos/áreas, usa centróide (projetando p/ evitar erro de CRS)
        if not (gdf.geom_type == "Point").all():
            gdf["geometry"] = gdf.to_crs("EPSG:31983").geometry.centroid.to_crs(CRS)
        return _assign_region(gdf)
    except Exception:
        return None


@lru_cache(maxsize=1)
def _fatores_all() -> gpd.GeoDataFrame | None:
    if config.DATA_MODE != "live":
        return None
    try:
        gdf = perri_bridge.get_loaders().load_fatores_urbanos()
        return _assign_region(gdf)
    except Exception:
        return None


def cameras(fid: int | None = None) -> gpd.GeoDataFrame | None:
    gdf = _cameras_all()
    if gdf is None:
        return None
    return gdf[gdf["fid"] == fid] if fid is not None else gdf


def fatores(fid: int | None = None) -> gpd.GeoDataFrame | None:
    gdf = _fatores_all()
    if gdf is None:
        return None
    return gdf[gdf["fid"] == fid] if fid is not None else gdf


# ── Células H3 priorizadas (exports do Perri, sempre) ────────────────────────
@lru_cache(maxsize=8)
def h3_cells(days: int | None = None) -> list[dict]:
    """Top-N células H3 do score geral MCDA (do export estático do Perri)."""
    path = config.SPATIAL_JSON.get(days, config.SPATIAL_JSON[None])
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("score_geral", {}).get("top_areas", [])


@lru_cache(maxsize=8)
def h3_cells_by_region(days: int | None = None) -> dict[int, list[dict]]:
    """Agrupa as células H3 por região (ponto-em-polígono do centróide)."""
    cells = h3_cells(days)
    if not cells:
        return {}
    gdf = gpd.GeoDataFrame(
        cells,
        geometry=gpd.points_from_xy([c["lon"] for c in cells],
                                    [c["lat"] for c in cells]),
        crs=CRS,
    )
    gdf = _assign_region(gdf)
    out: dict[int, list[dict]] = {}
    for _, row in gdf.iterrows():
        if pd.isna(row.get("fid")):
            continue
        out.setdefault(int(row["fid"]), []).append({
            k: row[k] for k in
            ("h3_cell", "lat", "lon", "score", "cnt_ocorrencias",
             "cnt_denuncias", "cnt_fatores", "cnt_cameras") if k in row
        })
    return out


@lru_cache(maxsize=1)
def dataset_as_of() -> str | None:
    """Data mais recente das denúncias (sempre disponível via Arick)."""
    gdf = _denuncias_all()
    mx = gdf["data"].max()
    return str(mx.date()) if pd.notna(mx) else None
