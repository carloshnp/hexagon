"""Score de risco POR REGIÃO (as 8 áreas oficiais).

Perri entrega score por célula H3; aqui agregamos as fontes dentro de cada
polígono e aplicamos o MESMO esquema de pesos do Perri
(`scorer.WEIGHTS` + `institution_scorer.INSTITUTIONS`), agora na granularidade
de região. O score é 100% determinístico — a LLM nunca o inventa, só o narra.

Componentes (min-max entre as 8 regiões, fundidos por peso):
  ocorrências · denúncias · fatores urbanos · cobertura inversa de câmeras
"""
from __future__ import annotations

from functools import lru_cache

import pandas as pd

from . import config, data_source, perri_bridge

_LABELS = {
    "ocorrencias": "Ocorrências (ISP-RJ)",
    "denuncias": "Denúncias (Disque Denúncia)",
    "fatores": "Fatores urbanos",
    "cameras_inv": "Cobertura inversa de câmeras",
}


def _minmax(s: pd.Series) -> pd.Series:
    lo, hi = s.min(), s.max()
    if hi == lo:
        return pd.Series(0.0, index=s.index)
    return (s - lo) / (hi - lo)


@lru_cache(maxsize=8)
def compute_region_scores(days: int | None = None) -> dict[int, dict]:
    """fid → dict com counts, componentes, risk_score/level, órgão e qualidade."""
    regs = data_source.regions()
    fids = [r["fid"] for r in regs]

    occ = data_source.occurrences(days)           # GeoDataFrame ou None
    den = data_source.denuncias(days)             # sempre real (Arick)
    fat = data_source.fatores()                   # GeoDataFrame ou None
    cam = data_source.cameras()                   # GeoDataFrame ou None
    h3_by_region = data_source.h3_cells_by_region(days)

    quality: dict[str, str] = {}

    def _counts_by_fid(gdf, real_label: str, h3_key: str) -> pd.Series:
        """Conta pontos por região; cai para proxy H3 se a fonte faltar."""
        if gdf is not None:
            quality[real_label] = "real"
            counts = gdf.dropna(subset=["fid"]).groupby("fid").size()
            return counts.reindex(fids, fill_value=0).astype(float)
        # proxy: soma dos cnt_* das células H3 do export que caem na região
        quality[real_label] = "aproximado"
        vals = {f: float(sum(c.get(h3_key, 0) for c in h3_by_region.get(f, [])))
                for f in fids}
        return pd.Series(vals).reindex(fids, fill_value=0.0)

    cnt = pd.DataFrame(index=fids)
    cnt["ocorrencias"] = _counts_by_fid(occ, "ocorrencias", "cnt_ocorrencias")
    cnt["denuncias"] = _counts_by_fid(den, "denuncias", "cnt_denuncias")
    cnt["fatores"] = _counts_by_fid(fat, "fatores", "cnt_fatores")
    cnt["cameras"] = _counts_by_fid(cam, "cameras", "cnt_cameras")

    # Normalização entre regiões
    norm = pd.DataFrame(index=fids)
    norm["ocorrencias"] = _minmax(cnt["ocorrencias"])
    norm["denuncias"] = _minmax(cnt["denuncias"])
    norm["fatores"] = _minmax(cnt["fatores"])
    norm["cameras_inv"] = 1 - _minmax(cnt["cameras"])

    weights = perri_bridge.get_weights()
    contrib = pd.DataFrame(index=fids)
    for k in ("ocorrencias", "denuncias", "fatores", "cameras_inv"):
        contrib[k] = weights[k] * norm[k] * 100
    score = contrib.sum(axis=1)

    agency = _primary_agency_by_region(days, cnt, norm, fids)

    out: dict[int, dict] = {}
    for f in fids:
        components = []
        for k in ("ocorrencias", "denuncias", "fatores", "cameras_inv"):
            raw_src = "cameras" if k == "cameras_inv" else k
            components.append({
                "key": k,
                "label": _LABELS[k],
                "raw_count": float(cnt[raw_src][f]),
                "normalized": round(float(norm[k][f]), 4),
                "weight": weights[k],
                "contribution": round(float(contrib[k][f]), 2),
            })
        out[f] = {
            "counts": {
                "ocorrencias": int(cnt["ocorrencias"][f]),
                "denuncias": int(cnt["denuncias"][f]),
                "fatores": int(cnt["fatores"][f]),
                "cameras": int(cnt["cameras"][f]),
            },
            "components": components,
            "risk_score": round(float(score[f]), 2),
            "risk_level": config.risk_level(float(score[f])),
            "primary_agency": agency[f]["primary"],
            "secondary_agencies": agency[f]["secondary"],
            "agency_scores": agency[f]["scores"],
            "data_quality": dict(quality),
        }
    return out


def _primary_agency_by_region(days, cnt, norm, fids) -> dict[int, dict]:
    """Para cada região, ranqueia as instituições reusando os perfis do Perri."""
    institutions = perri_bridge.get_institutions()
    den = data_source.denuncias(days)
    fat = data_source.fatores()

    # contagens por região filtradas por mandato da instituição
    inst_norm: dict[str, dict[str, pd.Series]] = {}
    for inst_id, prof in institutions.items():
        classes = prof.get("denuncias_classes") or []
        if den is not None and classes:
            sub = den[den["classe"].isin(classes)].dropna(subset=["fid"])
            den_c = sub.groupby("fid").size().reindex(fids, fill_value=0).astype(float)
        else:
            den_c = pd.Series(0.0, index=fids)

        tipos = prof.get("fatores_tipos") or []
        if fat is not None and tipos and "tipo_ocorrencia_descricao" in fat.columns:
            subf = fat[fat["tipo_ocorrencia_descricao"].isin(tipos)].dropna(subset=["fid"])
            fat_c = subf.groupby("fid").size().reindex(fids, fill_value=0).astype(float)
        else:
            fat_c = pd.Series(0.0, index=fids)

        inst_norm[inst_id] = {
            "den": _minmax(den_c),
            "fat": _minmax(fat_c),
        }

    # score por instituição por região
    scores_by_fid: dict[int, dict[str, float]] = {f: {} for f in fids}
    for inst_id, prof in institutions.items():
        w = prof["weights"]
        for f in fids:
            s = (
                w["ocorrencias"] * float(norm["ocorrencias"][f])
                + w["denuncias"] * float(inst_norm[inst_id]["den"][f])
                + w["fatores"] * float(inst_norm[inst_id]["fat"][f])
                + w["cameras_inv"] * float(norm["cameras_inv"][f])
            ) * 100
            scores_by_fid[f][inst_id] = round(s, 2)

    out: dict[int, dict] = {}
    for f in fids:
        ranked = sorted(scores_by_fid[f].items(), key=lambda kv: kv[1], reverse=True)
        out[f] = {
            "primary": ranked[0][0] if ranked else "FM",
            "secondary": [k for k, _ in ranked[1:3]],
            "scores": scores_by_fid[f],
        }
    return out
