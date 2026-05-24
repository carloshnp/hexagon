"""MCDA scorer — fuses multiple H3-aggregated sources into a priority score."""
import pandas as pd
import numpy as np

# Weights for each data source (must sum to 1.0)
WEIGHTS = {
    "ocorrencias": 0.40,
    "denuncias":   0.25,
    "fatores":     0.20,
    "cameras_inv": 0.15,  # inverse camera coverage → more cameras = lower score
}


def _minmax(s: pd.Series) -> pd.Series:
    lo, hi = s.min(), s.max()
    if hi == lo:
        return pd.Series(np.zeros(len(s)), index=s.index)
    return (s - lo) / (hi - lo)


def build_score_matrix(
    h3_ocorrencias: pd.DataFrame,
    h3_denuncias: pd.DataFrame,
    h3_fatores: pd.DataFrame,
    h3_cameras: pd.DataFrame,
) -> pd.DataFrame:
    """
    Merge all H3 aggregations on h3_cell, normalize, apply weights.
    Returns a DataFrame with one row per H3 cell and a 0-100 priority score.
    """
    base = (
        h3_ocorrencias.rename(columns={"count": "cnt_ocorrencias"})
        .merge(h3_denuncias.rename(columns={"count": "cnt_denuncias"}), on="h3_cell", how="outer", suffixes=("", "_d"))
        .merge(h3_fatores.rename(columns={"count": "cnt_fatores"}),     on="h3_cell", how="outer", suffixes=("", "_f"))
        .merge(h3_cameras.rename(columns={"count": "cnt_cameras"}),     on="h3_cell", how="outer", suffixes=("", "_c"))
    )

    for col in ["cnt_ocorrencias", "cnt_denuncias", "cnt_fatores", "cnt_cameras"]:
        base[col] = base[col].fillna(0)

    # Keep lat/lon from first non-null source
    for coord in ["lat", "lon"]:
        cols = [c for c in base.columns if c.startswith(coord)]
        base[coord] = base[cols].bfill(axis=1).iloc[:, 0]
        base = base.drop(columns=[c for c in cols if c != coord])

    base["norm_ocorrencias"] = _minmax(base["cnt_ocorrencias"])
    base["norm_denuncias"]   = _minmax(base["cnt_denuncias"])
    base["norm_fatores"]     = _minmax(base["cnt_fatores"])
    base["norm_cameras_inv"] = 1 - _minmax(base["cnt_cameras"])  # inverse

    base["score"] = (
        WEIGHTS["ocorrencias"] * base["norm_ocorrencias"]
        + WEIGHTS["denuncias"]   * base["norm_denuncias"]
        + WEIGHTS["fatores"]     * base["norm_fatores"]
        + WEIGHTS["cameras_inv"] * base["norm_cameras_inv"]
    ) * 100

    return base.sort_values("score", ascending=False).reset_index(drop=True)


def top_priority_areas(score_df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    cols = ["h3_cell", "lat", "lon", "score",
            "cnt_ocorrencias", "cnt_denuncias", "cnt_fatores", "cnt_cameras"]
    return score_df[cols].head(n)
