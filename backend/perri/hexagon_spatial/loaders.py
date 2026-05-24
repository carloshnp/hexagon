"""Loaders das fontes CIVITAS → GeoDataFrame.

Cada loader aceita um filtro opcional `days` (1, 3, 7 …) que restringe os
registros aos últimos N dias relativos à data mais recente presente no
dataset (semântica operacional: "últimas 24 h de dados disponíveis", etc.).
Câmeras e fatores urbanos não são filtrados — são infraestrutura.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import geopandas as gpd
import pandas as pd
from shapely import wkt

DATA_DIR = Path(__file__).parent / "claude_impact_lab_compstat_rio" / "dados"

CRS = "EPSG:4326"


def _apply_days_window(df: pd.DataFrame, date_col: str, days: Optional[int]) -> pd.DataFrame:
    """Mantém apenas linhas cujo `date_col` está dentro dos últimos `days` dias
    contados a partir do `max(date_col)` do próprio dataset.

    Linhas com data nula são descartadas quando `days` é fornecido.
    """
    if not days:
        return df
    max_dt = df[date_col].max()
    if pd.isna(max_dt):
        return df.iloc[0:0]
    cutoff = max_dt - pd.Timedelta(days=days)
    return df[df[date_col].notna() & (df[date_col] > cutoff)]


def load_ocorrencias(days: Optional[int] = None) -> gpd.GeoDataFrame:
    df = pd.read_csv(
        DATA_DIR / "df_ocorrencias_tratado - Extração 1 .csv",
        usecols=["id_criptografado", "ano", "mes", "data", "delito",
                 "longitude", "latitude", "desc_delito", "aisp", "risp"],
        low_memory=False,
    )
    df = df.dropna(subset=["latitude", "longitude"])
    df["data"] = pd.to_datetime(df["data"], dayfirst=True, errors="coerce")
    df = _apply_days_window(df, "data", days)
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
        crs=CRS,
    )
    return gdf


def load_denuncias(days: Optional[int] = None) -> gpd.GeoDataFrame:
    df = pd.read_csv(
        DATA_DIR / "disk_denuncia.csv",
        sep=";",
        usecols=["numero_denuncia", "data_denuncia", "bairro_logradouro",
                 "municipio", "latitude", "longitude",
                 "assuntos.classe", "assuntos.tipos.tipo"],
        encoding="latin-1",
        low_memory=False,
    )
    for col in ["latitude", "longitude"]:
        df[col] = (
            df[col].astype(str)
            .str.replace(",", ".", regex=False)
            .pipe(pd.to_numeric, errors="coerce")
        )
    df = df.dropna(subset=["latitude", "longitude"])
    df["data_denuncia"] = pd.to_datetime(df["data_denuncia"], errors="coerce")
    df = _apply_days_window(df, "data_denuncia", days)
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
        crs=CRS,
    )
    return gdf


def load_cameras() -> gpd.GeoDataFrame:
    df = pd.read_csv(DATA_DIR / "cameras_areas_fm.csv")
    df["geometry"] = df["geometry"].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs=CRS)
    return gdf


def load_fatores_urbanos() -> gpd.GeoDataFrame:
    df = pd.read_csv(DATA_DIR / "fatores_urbanos.csv", low_memory=False)
    df = df.dropna(subset=["coordenada_x", "coordenada_y"])
    # coordenada_x = latitude, coordenada_y = longitude (convenção GIS brasileira invertida)
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["coordenada_y"], df["coordenada_x"]),
        crs=CRS,
    )
    return gdf


def dataset_as_of() -> dict[str, str]:
    """Devolve a data mais recente disponível em cada fonte com data."""
    o = pd.read_csv(DATA_DIR / "df_ocorrencias_tratado - Extração 1 .csv",
                    usecols=["data"], low_memory=False)
    o_dt = pd.to_datetime(o["data"], dayfirst=True, errors="coerce")
    d = pd.read_csv(DATA_DIR / "disk_denuncia.csv", sep=";", encoding="latin-1",
                    usecols=["data_denuncia"], low_memory=False)
    d_dt = pd.to_datetime(d["data_denuncia"], errors="coerce")
    return {
        "ocorrencias_max": str(o_dt.max().date()) if pd.notna(o_dt.max()) else None,
        "denuncias_max":   str(d_dt.max().date()) if pd.notna(d_dt.max()) else None,
    }
