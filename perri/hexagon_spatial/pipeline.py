"""End-to-end spatial pipeline: load → H3 → cluster → score geral + score por instituição."""
import time
import pandas as pd

from .loaders import load_ocorrencias, load_denuncias, load_cameras, load_fatores_urbanos
from .h3_indexer import encode_h3, aggregate_by_h3
from .clustering import cluster_hotspots
from .scorer import build_score_matrix, top_priority_areas
from .institution_scorer import score_by_institution


def run_pipeline(top_n: int = 5, verbose: bool = True) -> dict:
    def log(msg: str):
        if verbose:
            print(f"  [{time.time() - t_start:.1f}s] {msg}")

    t_start = time.time()

    # 1. Load
    gdf_ocorr   = load_ocorrencias()
    gdf_denunc  = load_denuncias()
    gdf_cameras = load_cameras()
    gdf_fatores = load_fatores_urbanos()
    log(f"Loaded — ocorrencias={len(gdf_ocorr):,}  denuncias={len(gdf_denunc):,}  "
        f"cameras={len(gdf_cameras):,}  fatores={len(gdf_fatores):,}")

    # 2. H3 encode (feito uma vez, reaproveitado em todos os scorers)
    gdf_ocorr   = encode_h3(gdf_ocorr)
    gdf_denunc  = encode_h3(gdf_denunc)
    gdf_cameras = encode_h3(gdf_cameras)
    gdf_fatores = encode_h3(gdf_fatores)
    log("H3 encoded all datasets")

    # 3. Aggregate by H3 cell
    h3_ocorr   = aggregate_by_h3(gdf_ocorr,   "count")
    h3_denunc  = aggregate_by_h3(gdf_denunc,  "count")
    h3_cameras = aggregate_by_h3(gdf_cameras, "count")
    h3_fatores = aggregate_by_h3(gdf_fatores, "count")
    log(f"Aggregated — cells: ocorr={len(h3_ocorr):,}  denunc={len(h3_denunc):,}  "
        f"cameras={len(h3_cameras):,}  fatores={len(h3_fatores):,}")

    # 4. DBSCAN hotspot clustering
    h3_ocorr_clustered = cluster_hotspots(h3_ocorr)
    n_clusters = h3_ocorr_clustered[h3_ocorr_clustered["cluster_id"] >= 0]["cluster_id"].nunique()
    log(f"DBSCAN: {n_clusters} hotspot clusters found")

    # 5. Score geral (MCDA fusão de todas as fontes)
    score_df = build_score_matrix(h3_ocorr, h3_denunc, h3_fatores, h3_cameras)
    top_geral = top_priority_areas(score_df, n=top_n)
    log(f"Score geral: {len(score_df):,} células H3 pontuadas")

    # 6. Score por instituição
    scores_inst = score_by_institution(
        gdf_ocorrencias=gdf_ocorr,
        gdf_denuncias=gdf_denunc,
        gdf_fatores=gdf_fatores,
        gdf_cameras=gdf_cameras,
        top_n=top_n,
    )
    log(f"Scores por instituição: {len(scores_inst)} órgãos calculados")

    elapsed = time.time() - t_start
    log(f"TOTAL: {elapsed:.1f}s")

    return {
        "elapsed_seconds": round(elapsed, 2),
        "total_cells_scored": len(score_df),
        "n_hotspot_clusters": n_clusters,
        "score_geral": {
            "descricao": "Fusão ponderada de todas as fontes (MCDA)",
            "top_areas": top_geral.to_dict(orient="records"),
        },
        "scores_por_instituicao": scores_inst,
        # internos, não vão para o JSON
        "_score_df": score_df,
        "_clustered_df": h3_ocorr_clustered,
    }


def _clean_for_json(result: dict) -> dict:
    """Remove chaves internas e arredonda floats para serialização JSON."""
    output = {k: v for k, v in result.items() if not k.startswith("_")}

    def _round_area(area: dict) -> dict:
        return {
            k: round(v, 6) if isinstance(v, float) else v
            for k, v in area.items()
        }

    output["score_geral"]["top_areas"] = [
        _round_area(a) for a in output["score_geral"]["top_areas"]
    ]
    for inst in output["scores_por_instituicao"].values():
        inst["top_areas"] = [_round_area(a) for a in inst["top_areas"]]

    return output


if __name__ == "__main__":
    import json
    import sys

    top_n    = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    out_file = sys.argv[2] if len(sys.argv) > 2 else None

    result = run_pipeline(top_n=top_n)
    output = _clean_for_json(result)

    json_str = json.dumps(output, ensure_ascii=False, indent=4, separators=(",", ": "))

    if out_file:
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(json_str)
        print(f"Saved to {out_file}")
    else:
        print(json_str)
