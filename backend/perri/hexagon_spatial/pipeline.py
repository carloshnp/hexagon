"""End-to-end spatial pipeline: load → H3 → cluster → score geral + score por instituição.

Aceita `days` ∈ {None, 1, 3, 7, ...} para restringir ocorrências e denúncias
aos últimos N dias relativos à data mais recente do próprio dataset.
"""
from __future__ import annotations

import time
from typing import Optional

import pandas as pd

from .clustering import cluster_hotspots
from .h3_indexer import aggregate_by_h3, encode_h3
from .institution_scorer import score_by_institution
from .loaders import (
    dataset_as_of,
    load_cameras,
    load_denuncias,
    load_fatores_urbanos,
    load_ocorrencias,
)
from .scorer import build_score_matrix, top_priority_areas


def run_pipeline(
    top_n: int = 5,
    days: Optional[int] = None,
    verbose: bool = True,
) -> dict:
    def log(msg: str):
        if verbose:
            print(f"  [{time.time() - t_start:.1f}s] {msg}")

    t_start = time.time()

    # 1. Load (com filtro de dias só onde faz sentido)
    gdf_ocorr   = load_ocorrencias(days=days)
    gdf_denunc  = load_denuncias(days=days)
    gdf_cameras = load_cameras()
    gdf_fatores = load_fatores_urbanos()
    log(f"Loaded — ocorr={len(gdf_ocorr):,}  denunc={len(gdf_denunc):,}  "
        f"cameras={len(gdf_cameras):,}  fatores={len(gdf_fatores):,}  "
        f"(days={days})")

    # 2. H3 encode
    gdf_ocorr   = encode_h3(gdf_ocorr)
    gdf_denunc  = encode_h3(gdf_denunc)
    gdf_cameras = encode_h3(gdf_cameras)
    gdf_fatores = encode_h3(gdf_fatores)
    log("H3 encoded")

    # 3. Aggregate by H3 cell
    h3_ocorr   = aggregate_by_h3(gdf_ocorr,   "count")
    h3_denunc  = aggregate_by_h3(gdf_denunc,  "count")
    h3_cameras = aggregate_by_h3(gdf_cameras, "count")
    h3_fatores = aggregate_by_h3(gdf_fatores, "count")

    # 4. DBSCAN hotspot clustering
    h3_ocorr_clustered = cluster_hotspots(h3_ocorr)
    n_clusters = h3_ocorr_clustered[h3_ocorr_clustered["cluster_id"] >= 0]["cluster_id"].nunique()
    log(f"DBSCAN: {n_clusters} hotspot clusters")

    # 5. Score geral (MCDA)
    score_df = build_score_matrix(h3_ocorr, h3_denunc, h3_fatores, h3_cameras)
    top_geral = top_priority_areas(score_df, n=top_n)

    # 6. Score por instituição
    scores_inst = score_by_institution(
        gdf_ocorrencias=gdf_ocorr,
        gdf_denuncias=gdf_denunc,
        gdf_fatores=gdf_fatores,
        gdf_cameras=gdf_cameras,
        top_n=top_n,
    )

    elapsed = time.time() - t_start
    log(f"TOTAL: {elapsed:.1f}s")

    # data mais recente usada para a janela
    as_of = dataset_as_of()
    as_of_used = as_of["ocorrencias_max"]   # fonte principal

    return {
        "elapsed_seconds": round(elapsed, 2),
        "filtro_dias": days,
        "as_of_date": as_of_used,
        "n_ocorrencias_usadas": int(len(gdf_ocorr)),
        "n_denuncias_usadas": int(len(gdf_denunc)),
        "total_cells_scored": len(score_df),
        "n_hotspot_clusters": int(n_clusters),
        "score_geral": {
            "descricao": "Fusão ponderada de todas as fontes (MCDA)",
            "top_areas": top_geral.to_dict(orient="records"),
        },
        "scores_por_instituicao": scores_inst,
        "_score_df": score_df,
        "_clustered_df": h3_ocorr_clustered,
    }


def _clean_for_json(result: dict) -> dict:
    output = {k: v for k, v in result.items() if not k.startswith("_")}

    def _round_area(area: dict) -> dict:
        return {k: round(v, 6) if isinstance(v, float) else v for k, v in area.items()}

    output["score_geral"]["top_areas"] = [_round_area(a) for a in output["score_geral"]["top_areas"]]
    for inst in output["scores_por_instituicao"].values():
        inst["top_areas"] = [_round_area(a) for a in inst["top_areas"]]
    return output


if __name__ == "__main__":
    import json
    import sys

    top_n = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    days  = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2] != "all" else None
    out_file = sys.argv[3] if len(sys.argv) > 3 else None

    result = run_pipeline(top_n=top_n, days=days)
    output = _clean_for_json(result)
    js = json.dumps(output, ensure_ascii=False, indent=4)
    if out_file:
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(js)
        print(f"Saved to {out_file}")
    else:
        print(js)
