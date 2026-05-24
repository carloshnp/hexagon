"""Loaders for all CIVITAS data sources → GeoDataFrame."""
import pandas as pd
import geopandas as gpd
from shapely import wkt
from pathlib import Path

DATA_DIR = Path(__file__).parents[2] / "dados"

CRS = "EPSG:4326"


def load_ocorrencias() -> gpd.GeoDataFrame:
    df = pd.read_csv(
        DATA_DIR / "df_ocorrencias_tratado - Extração 1 .csv",
        usecols=["id_criptografado", "ano", "mes", "delito", "longitude", "latitude",
                 "desc_delito", "aisp", "risp"],
        low_memory=False,
    )
    df = df.dropna(subset=["latitude", "longitude"])
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
        crs=CRS,
    )
    return gdf


def load_denuncias() -> gpd.GeoDataFrame:
    df = pd.read_csv(
        DATA_DIR / "disk_denuncia.csv",
        sep=";",
        usecols=["numero_denuncia", "data_denuncia", "bairro_logradouro",
                 "municipio", "latitude", "longitude",
                 "assuntos.classe", "assuntos.tipos.tipo"],
        encoding="latin-1",
        low_memory=False,
    )
    # Fix Brazilian decimal comma
    for col in ["latitude", "longitude"]:
        df[col] = (
            df[col].astype(str)
            .str.replace(",", ".", regex=False)
            .pipe(pd.to_numeric, errors="coerce")
        )
    df = df.dropna(subset=["latitude", "longitude"])
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
