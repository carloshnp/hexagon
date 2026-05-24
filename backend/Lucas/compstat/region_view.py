"""Montagem das views de região (properties, camadas de mapa, recorte granular).

Compartilhado entre o router de mapa e o de relatórios. Tudo determinístico.
"""
from __future__ import annotations

import datetime as dt

import pandas as pd

from . import config, data_source, region_scoring

_MAX_POINTS = 800   # teto de pontos por camada para o payload do mapa


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def time_window(preset: str | None) -> dict:
    days = config.window_to_days(preset)
    end = data_source.dataset_as_of()
    start = None
    if end and days:
        start = str((pd.Timestamp(end) - pd.Timedelta(days=days)).date())
    return {
        "preset": preset or config.DEFAULT_TIME_WINDOW,
        "start": start,
        "end": end,
        "historical_available": config.DATA_MODE == "live",
    }


def region_summary(reg: dict, sc: dict, days: int | None) -> str:
    c = sc["counts"]
    janela = f"últimos {days} dias" if days else "todo o histórico"
    return (
        f"Risco {sc['risk_level']} (score {sc['risk_score']:.0f}/100) em "
        f"{janela}: {c['ocorrencias']} ocorrências e {c['denuncias']} denúncias. "
        f"Órgão municipal sugerido: {sc['primary_agency']}."
    )


def region_properties(reg: dict, sc: dict, days: int | None) -> dict:
    c = sc["counts"]
    n_critical = len(data_source.h3_cells_by_region(days).get(reg["fid"], []))
    return {
        "region_id": reg["region_id"],
        "fid": reg["fid"],
        "region_name": reg["region_name"],
        "risk_score": sc["risk_score"],
        "risk_level": sc["risk_level"],
        "primary_agency": sc["primary_agency"],
        "secondary_agencies": sc["secondary_agencies"],
        "summary": region_summary(reg, sc, days),
        "occurrence_count": c["ocorrencias"],
        "denuncia_count": c["denuncias"],
        "camera_count": c["cameras"],
        "urban_factor_count": c["fatores"],
        "critical_area_count": n_critical,
        "data_quality": sc["data_quality"],
    }


def _points_from_gdf(gdf, cols: list[str]) -> list[dict]:
    if gdf is None or len(gdf) == 0:
        return []
    gdf = gdf.head(_MAX_POINTS)
    out = []
    for _, row in gdf.iterrows():
        item = {"lat": float(row.geometry.y), "lon": float(row.geometry.x)}
        for col in cols:
            if col in row and pd.notna(row[col]):
                val = row[col]
                item[col] = val.isoformat() if hasattr(val, "isoformat") else val
        out.append(item)
    return out


def map_layers(reg: dict, days: int | None) -> dict:
    fid = reg["fid"]
    occ = data_source.occurrences(days, fid)
    den = data_source.denuncias(days, fid)
    cam = data_source.cameras(fid)
    fat = data_source.fatores(fid)
    critical = data_source.h3_cells_by_region(days).get(fid, [])
    return {
        "polygon": reg["geometry"] or {},
        "occurrences": _points_from_gdf(occ, ["delito", "desc_delito", "data", "hora"]),
        "denuncias": _points_from_gdf(den, ["classe", "tipo", "bairro", "hora"]),
        "cameras": _points_from_gdf(cam, []),
        "urban_factors": _points_from_gdf(fat, ["tipo_ocorrencia_descricao"]),
        "critical_areas": critical,
    }


def occurrence_types(reg: dict, days: int | None, top: int = 12) -> list[dict]:
    fid = reg["fid"]
    occ = data_source.occurrences(days, fid)
    if occ is not None and len(occ):
        col = "desc_delito" if "desc_delito" in occ.columns else "delito"
        counts = occ[col].dropna().value_counts().head(top)
    else:
        den = data_source.denuncias(days, fid)
        counts = den["classe"].dropna().value_counts().head(top) if len(den) else pd.Series(dtype=int)
    return [{"tipo": str(k), "count": int(v)} for k, v in counts.items()]


def hourly_histogram(reg: dict, days: int | None) -> list[dict]:
    fid = reg["fid"]
    hours = pd.Series(dtype=float)
    occ = data_source.occurrences(days, fid)
    if occ is not None and "hora" in occ.columns:
        hours = pd.concat([hours, occ["hora"].dropna()])
    den = data_source.denuncias(days, fid)
    if len(den) and "hora" in den.columns:
        hours = pd.concat([hours, den["hora"].dropna()])
    if hours.empty:
        return []
    counts = hours.astype(int).value_counts().sort_index()
    return [{"hour": int(h), "count": int(counts.get(h, 0))} for h in range(24)]


def provenance(reg: dict, sc: dict, days: int | None) -> list[dict]:
    prov = []
    q = sc["data_quality"]
    if q.get("denuncias") == "real":
        prov.append({"source": "Disque Denúncia",
                     "description": "Denúncias georreferenciadas com relato redigido (PII removida).",
                     "n_records": sc["counts"]["denuncias"]})
    if q.get("ocorrencias") == "real":
        prov.append({"source": "ISP-RJ",
                     "description": "Ocorrências tratadas (Extração 1).",
                     "n_records": sc["counts"]["ocorrencias"]})
    elif q.get("ocorrencias") == "aproximado":
        prov.append({"source": "ISP-RJ (proxy H3)",
                     "description": "Modo estático: contagem aproximada pelas células H3 priorizadas do Perri."})
    if reg.get("relint_match") and reg["relint_match"].get("codigo"):
        prov.append({"source": f"RELINT {reg['relint_match']['codigo']}",
                     "description": "Relatório de Inteligência de Área (fatores urbanos estruturados).",
                     "confidence": reg["relint_match"].get("score")})
    return prov


def build_region_detail(region_id: str, preset: str | None) -> dict | None:
    reg = data_source.region_by_id(region_id)
    if reg is None:
        return None
    days = config.window_to_days(preset)
    scores = region_scoring.compute_region_scores(days)
    sc = scores[reg["fid"]]
    return {
        "region": region_properties(reg, sc, days),
        "time_window": time_window(preset),
        "score_components": sc["components"],
        "map_layers": map_layers(reg, days),
        "occurrence_types": occurrence_types(reg, days),
        "hourly_histogram": hourly_histogram(reg, days),
        "occurrence_groups": [],      # preenchido pelo relatório (lazy, Passo 4)
        "regional_report": None,      # idem
        "recommended_actions": [],
        "provenance": provenance(reg, sc, days),
    }
