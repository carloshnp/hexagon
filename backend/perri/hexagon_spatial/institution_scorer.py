"""Score por instituição — cada órgão recebe um ranking das células H3 mais relevantes para seu mandato."""
import pandas as pd
import numpy as np
import geopandas as gpd

from .h3_indexer import encode_h3, aggregate_by_h3

# ---------------------------------------------------------------------------
# Perfis de instituição: filtros sobre os datasets brutos + pesos
# ---------------------------------------------------------------------------

INSTITUTIONS = {
    "PM-RJ": {
        "nome": "Polícia Militar do Rio de Janeiro",
        "mandato": "Policiamento ostensivo, crimes contra patrimônio e pessoa, armas e drogas",
        "ocorrencias_tipos": None,          # todas as ocorrências são relevantes para PM
        "denuncias_classes": [
            "CRIMES CONTRA O PATRIMÔNIO",
            "ARMAS DE FOGO E ARTEFATOS EXPLOSIVOS",
            "SUBSTÂNCIAS ENTORPECENTES",
            "CRIMES CONTRA A PESSOA",
            "CRIMES CONTRA A LIBERDADE SEXUAL",
        ],
        "fatores_tipos": [
            "Cena de uso de drogas",
            "Vãos ou cavidades usados como esconderijo",
            "Mobiliário/estrutura servindo de esconderijo",
            "Mobiliário abandonado servindo de esconderijo",
            "Ponto de ônibus com histórico de vandalismo",
        ],
        "weights": {
            "ocorrencias": 0.50,
            "denuncias":   0.30,
            "fatores":     0.10,
            "cameras_inv": 0.10,
        },
    },
    "GM-Rio": {
        "nome": "Guarda Municipal do Rio de Janeiro",
        "mandato": "Ordem pública, proteção do patrimônio municipal, fiscalização urbana",
        "ocorrencias_tipos": None,
        "denuncias_classes": [
            "PERTURBAÇÃO DA ORDEM PÚBLICA",
            "CRIMES CONTRA A ADMINISTRAÇÃO PÚBLICA",
            "CRIMES DE TRÂNSITO",
            "DEFESA DO CIDADÃO",
        ],
        "fatores_tipos": [
            "Comércio irregular obstruindo a visibilidade do passeio",
            "Estacionamento irregular forçando pedestres à pista",
            "Motocicletas trafegando no passeio",
            "Pessoas em situação de rua",
            "Veículos de grande porte obstruindo a visibilidade",
            "Ponto de retenção do tráfego",
        ],
        "weights": {
            "ocorrencias": 0.20,
            "denuncias":   0.35,
            "fatores":     0.45,
            "cameras_inv": 0.00,
        },
    },
    "RioLuz": {
        "nome": "Rio Luz (Iluminação Pública)",
        "mandato": "Manutenção e expansão da rede de iluminação pública",
        "ocorrencias_tipos": None,
        "denuncias_classes": [],
        "fatores_tipos": [
            "Vegetação encobrindo iluminação pública",
            "Área mal iluminada com circulação de pedestres",
            "Área mal iluminada com parada de veículos",
        ],
        "weights": {
            "ocorrencias": 0.30,
            "denuncias":   0.00,
            "fatores":     0.70,
            "cameras_inv": 0.00,
        },
    },
    "COMLURB": {
        "nome": "Companhia Municipal de Limpeza Urbana",
        "mandato": "Limpeza urbana, coleta de lixo, poda de vegetação",
        "ocorrencias_tipos": None,
        "denuncias_classes": [
            "CRIMES CONTRA O MEIO AMBIENTE",
        ],
        "fatores_tipos": [
            "Vegetação obstruindo a visibilidade do passeio",
            "Vegetação encobrindo iluminação pública",
            "Lixo/entulho forçando pedestres à pista",
            "Calçada estreita forçando pedestres à pista",
        ],
        "weights": {
            "ocorrencias": 0.20,
            "denuncias":   0.10,
            "fatores":     0.70,
            "cameras_inv": 0.00,
        },
    },
    "SEOP": {
        "nome": "Secretaria de Ordem Pública",
        "mandato": "Fiscalização de ocupação irregular, ambulantes, posturas municipais",
        "ocorrencias_tipos": None,
        "denuncias_classes": [
            "PERTURBAÇÃO DA ORDEM PÚBLICA",
            "CRIMES CONTRA A ADMINISTRAÇÃO PÚBLICA",
        ],
        "fatores_tipos": [
            "Comércio irregular obstruindo a visibilidade do passeio",
            "Estacionamento irregular forçando pedestres à pista",
            "Motocicletas trafegando no passeio",
            "Praças e Parques",
        ],
        "weights": {
            "ocorrencias": 0.15,
            "denuncias":   0.40,
            "fatores":     0.45,
            "cameras_inv": 0.00,
        },
    },
    "CET-Rio": {
        "nome": "Companhia de Engenharia de Tráfego do Rio",
        "mandato": "Fluidez do tráfego, sinalização, gestão de vias",
        "ocorrencias_tipos": None,
        "denuncias_classes": [
            "CRIMES DE TRÂNSITO",
            "PERTURBAÇÃO DA ORDEM PÚBLICA",
        ],
        "fatores_tipos": [
            "Ponto de retenção do tráfego",
            "Estacionamento irregular forçando pedestres à pista",
            "Veículos de grande porte obstruindo a visibilidade",
            "Motocicletas trafegando no passeio",
            "Calçada estreita forçando pedestres à pista",
            "Mobiliário urbano desviando pedestres para a pista",
        ],
        "weights": {
            "ocorrencias": 0.10,
            "denuncias":   0.25,
            "fatores":     0.65,
            "cameras_inv": 0.00,
        },
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _minmax(s: pd.Series) -> pd.Series:
    lo, hi = s.min(), s.max()
    if hi == lo:
        return pd.Series(np.zeros(len(s)), index=s.index)
    return (s - lo) / (hi - lo)


def _filter_denuncias(gdf_denuncias: gpd.GeoDataFrame, classes: list) -> gpd.GeoDataFrame:
    if not classes:
        return gdf_denuncias.iloc[:0]   # empty
    mask = gdf_denuncias["assuntos.classe"].isin(classes)
    return gdf_denuncias[mask]


def _filter_fatores(gdf_fatores: gpd.GeoDataFrame, tipos: list) -> gpd.GeoDataFrame:
    if not tipos:
        return gdf_fatores.iloc[:0]     # empty
    mask = gdf_fatores["tipo_ocorrencia_descricao"].isin(tipos)
    return gdf_fatores[mask]


# ---------------------------------------------------------------------------
# Main scorer
# ---------------------------------------------------------------------------

def score_by_institution(
    gdf_ocorrencias: gpd.GeoDataFrame,
    gdf_denuncias: gpd.GeoDataFrame,
    gdf_fatores: gpd.GeoDataFrame,
    gdf_cameras: gpd.GeoDataFrame,
    top_n: int = 5,
) -> dict:
    """
    Retorna um dict institution_id → {meta, top_areas, all_cells_count}.
    Os GeoDataFrames já devem ter a coluna h3_cell (pós encode_h3).
    """
    h3_ocorr   = aggregate_by_h3(gdf_ocorrencias, "cnt_ocorr")
    h3_cameras = aggregate_by_h3(gdf_cameras,     "cnt_cameras")

    results = {}

    for inst_id, profile in INSTITUTIONS.items():
        weights = profile["weights"]

        # Denúncias filtradas por relevância da instituição
        den_filtered = _filter_denuncias(gdf_denuncias, profile["denuncias_classes"])
        h3_den = aggregate_by_h3(den_filtered, "cnt_den") if len(den_filtered) else pd.DataFrame(columns=["h3_cell", "cnt_den"])

        # Fatores filtrados por relevância da instituição
        fat_filtered = _filter_fatores(gdf_fatores, profile["fatores_tipos"])
        h3_fat = aggregate_by_h3(fat_filtered, "cnt_fat") if len(fat_filtered) else pd.DataFrame(columns=["h3_cell", "cnt_fat"])

        # Merge
        base = (
            h3_ocorr
            .merge(h3_den,     on="h3_cell", how="outer", suffixes=("", "_d"))
            .merge(h3_fat,     on="h3_cell", how="outer", suffixes=("", "_f"))
            .merge(h3_cameras, on="h3_cell", how="outer", suffixes=("", "_c"))
        )

        for col in ["cnt_ocorr", "cnt_den", "cnt_fat", "cnt_cameras"]:
            base[col] = base.get(col, pd.Series(0, index=base.index)).fillna(0)

        # Consolidar lat/lon
        lat_cols = [c for c in base.columns if c.startswith("lat")]
        lon_cols = [c for c in base.columns if c.startswith("lon")]
        base["lat"] = base[lat_cols].bfill(axis=1).iloc[:, 0]
        base["lon"] = base[lon_cols].bfill(axis=1).iloc[:, 0]
        base = base.drop(columns=[c for c in lat_cols + lon_cols if c not in ("lat", "lon")])

        # Normalizar + score
        base["n_ocorr"]    = _minmax(base["cnt_ocorr"])
        base["n_den"]      = _minmax(base["cnt_den"])
        base["n_fat"]      = _minmax(base["cnt_fat"])
        base["n_cam_inv"]  = 1 - _minmax(base["cnt_cameras"])

        base["score"] = (
            weights["ocorrencias"] * base["n_ocorr"]
            + weights["denuncias"] * base["n_den"]
            + weights["fatores"]   * base["n_fat"]
            + weights["cameras_inv"] * base["n_cam_inv"]
        ) * 100

        base = base.sort_values("score", ascending=False).reset_index(drop=True)

        top = base[["h3_cell", "lat", "lon", "score",
                    "cnt_ocorr", "cnt_den", "cnt_fat", "cnt_cameras"]].head(top_n)

        results[inst_id] = {
            "instituicao": profile["nome"],
            "mandato": profile["mandato"],
            "pesos": weights,
            "total_celulas": len(base),
            "top_areas": top.to_dict(orient="records"),
        }

    return results
