"""OccurrenceGroupAgent — agrupa ocorrências/denúncias por tipo e gera plano de ação.

Produz o esqueleto DETERMINÍSTICO dos grupos (contagens, horários, pontos,
órgão responsável, provenance). A narrativa/ação refinada é preenchida depois
pela LLM em `regional_narrative` (1 chamada por região, lazy). Consome os
relatos redigidos do Disque Denúncia (insumo granular do Arick).
"""
from __future__ import annotations

import re
import unicodedata

import pandas as pd

from .. import data_source
from . import agencies

_MAX_GROUPS = 6
_MAX_RELATOS = 8
_RELATO_MAXLEN = 320
_MAX_POINTS = 200


def _slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")
    return s[:48] or "grupo"


def _peak_hours(hours: pd.Series) -> list[int]:
    h = hours.dropna()
    if h.empty:
        return []
    return [int(x) for x in h.astype(int).value_counts().head(3).sort_index().index]


def _fmt_window(hours: list[int]) -> str | None:
    if not hours:
        return None
    return ", ".join(f"{h:02d}h" for h in sorted(hours))


def build_groups(region_id: str, days: int | None) -> list[dict]:
    reg = data_source.region_by_id(region_id)
    if reg is None:
        return []
    fid = reg["fid"]
    den = data_source.denuncias(days, fid)
    if den is None or len(den) == 0:
        return []

    top_classes = den["classe"].dropna().value_counts().head(_MAX_GROUPS)
    region_max = int(top_classes.iloc[0]) if len(top_classes) else 1

    groups = []
    for classe, count in top_classes.items():
        sub = den[den["classe"] == classe]
        primary, supporting = agencies.agency_for_classe(str(classe))
        peak = _peak_hours(sub["hora"]) if "hora" in sub.columns else []
        relatos = [
            str(r)[:_RELATO_MAXLEN]
            for r in sub["relato"].dropna().head(_MAX_RELATOS).tolist()
            if str(r).strip() and str(r).strip().upper() != "NA"
        ]
        bairros = sub["bairro"].dropna().value_counts().head(3).index.tolist() \
            if "bairro" in sub.columns else []
        points = [
            {"lat": float(g.y), "lon": float(g.x)}
            for g in sub.geometry.head(_MAX_POINTS)
        ]
        risk = round(min(100.0, int(count) / region_max * 100), 1)
        confidence = round(min(0.9, 0.4 + int(count) / 80), 2)

        groups.append({
            "group_id": f"{_slug(str(classe))}__{region_id}",
            "classe": str(classe),
            "count": int(count),
            "summary": f"{int(count)} denúncias de {classe} na região.",
            "detailed_explanation": (
                f"Concentração de {int(count)} denúncias classificadas como "
                f"'{classe}'"
                + (f", com pico em {_fmt_window(peak)}" if peak else "")
                + (f". Bairros mais citados: {', '.join(map(str, bairros))}." if bairros else ".")
            ),
            "score": {"risk": risk, "confidence": confidence},
            "action_plan": {
                "responsible_agency": primary,
                "supporting_agencies": supporting,
                "recommended_action": agencies.action_for_agency(primary),
                "priority": "high" if risk >= 66 else "medium" if risk >= 33 else "low",
                "time_window": _fmt_window(peak),
            },
            "map_data": {
                "points": points,
                "hotspots": [],
                "critical_hours": [f"{h:02d}h" for h in peak],
                "related_cameras": [],
                "related_urban_factors": [],
            },
            "provenance": [{
                "source": "Disque Denúncia",
                "description": f"{int(count)} denúncias com relato redigido (PII removida).",
                "n_records": int(count),
                "confidence": confidence,
            }],
            "_relatos_sample": relatos,   # consumido pela LLM; removido na resposta final
        })
    return groups
