"""MapRegionOrchestrator — monta o diagnóstico da região e o trace de decisão.

Junta score (region_scoring) + overlay temporal (bingo) + competência, derivando
as ações recomendadas (fator→órgão→ação, priorizadas) e registrando quais
evidências entraram e quais foram descartadas (e por quê). Determinístico.
"""
from __future__ import annotations

from . import bingo, competence, data_source, region_scoring


def _priority(severity: float | None) -> str:
    s = severity or 0
    return "high" if s >= 66 else "medium" if s >= 33 else "low"


def recommended_actions(bz: dict) -> list[dict]:
    """Agrega ações por (órgão, problema) a partir dos drivers/social/câmera dos hotspots."""
    actions: dict[tuple, dict] = {}
    for h in bz.get("hotspots", []):
        prio = _priority(h.get("severity"))
        for f in h.get("driver_factors", []):
            key = (f["orgao"], f["tipo"])
            cur = actions.get(key)
            if cur is None or _rank(prio) < _rank(cur["priority"]):
                actions[key] = {
                    "problem": f["tipo"],
                    "responsible_agency": f["orgao"],
                    "esfera": f["esfera"],
                    "recommended_action": competence.recommended_action(f["orgao"]),
                    "priority": prio,
                    "evidence": f"co-ocorrência temporal {f['overlap_temporal']} no hotspot {h['hotspot_id']}",
                    "hotspot_id": h["hotspot_id"],
                    "time_window": h["critical_hours_label"],
                }
        for f in h.get("social_factors", []):
            key = (f["orgao"], f["tipo"])
            actions.setdefault(key, {
                "problem": f["tipo"],
                "responsible_agency": f["orgao"],
                "esfera": f["esfera"],
                "recommended_action": competence.recommended_action(f["orgao"]),
                "priority": "medium",
                "evidence": f"fator social presente no hotspot {h['hotspot_id']} (articulação, não repressão)",
                "hotspot_id": h["hotspot_id"],
                "time_window": h["critical_hours_label"],
            })
        if h["camera"].get("gap"):
            key = ("FM", f"lacuna_camera_{h['hotspot_id']}")
            actions[key] = {
                "problem": "Lacuna de cobertura de câmera no ponto crítico",
                "responsible_agency": "FM",
                "esfera": "municipal",
                "recommended_action": competence.recommended_action("FM"),
                "priority": prio,
                "evidence": f"câmera mais próxima a {h['camera'].get('distance_m')} m",
                "hotspot_id": h["hotspot_id"],
                "time_window": h["critical_hours_label"],
            }
    return sorted(actions.values(), key=lambda a: _rank(a["priority"]))


def _rank(p: str) -> int:
    return {"high": 0, "medium": 1, "low": 2}.get(p, 3)


def decision_trace(region_id: str, days: int | None, sc: dict, bz: dict) -> dict:
    fid = data_source.region_by_id(region_id)["fid"]
    occ = data_source.occurrences(days, fid)
    den = data_source.denuncias(days, fid)
    fat = data_source.fatores(fid)
    cam = data_source.cameras(fid)
    n_drivers = sum(len(h["driver_factors"]) for h in bz["hotspots"])
    n_factors_total = sum(len(h["matched_factors"]) for h in bz["hotspots"])
    considered = [
        f"Ocorrências (ISP-RJ): {0 if occ is None else len(occ)} pontos.",
        f"Denúncias (Disque): {0 if den is None else len(den)} pontos (eixo temporal).",
        f"Fatores urbanos: {0 if fat is None else len(fat)} na região.",
        f"Câmeras: {0 if cam is None else len(cam)} (cobertura por distância).",
        f"Hotspots H3: {bz['n_hotspots']}; fatores casados temporalmente (drivers): {n_drivers}.",
    ]
    discarded = [
        f"{n_factors_total - n_drivers} fatores presentes mas descartados como driver "
        "(overlap temporal baixo ou estruturais).",
        "Domínio territorial (CV/ADA/TCP) não usado como fonte de ação (apenas contexto).",
    ]
    return {"considered": considered, "discarded": discarded}


def region_diagnosis(region_id: str, days: int | None) -> dict:
    sc = region_scoring.compute_region_scores(days)[data_source.region_by_id(region_id)["fid"]]
    bz = bingo.region_bingo(region_id, days)
    return {
        "bingo": bz,
        "recommended_actions": recommended_actions(bz),
        "decision_trace": decision_trace(region_id, days, sc, bz),
    }
