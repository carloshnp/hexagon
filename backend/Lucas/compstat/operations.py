"""Rascunho operacional — alocação dos ~600 agentes da Força Municipal.

Etapa 2 do ciclo CompStat (matriz de responsabilidade + plano de ação), na forma
de um rascunho de emprego: quantos agentes por polígono e por hotspot, em qual
turno, com qual modelo de emprego e quais órgãos municipais de apoio. Tudo
determinístico e SUGERIDO (OK humano). A LLM narra; os números saem daqui.
"""
from __future__ import annotations

from . import bingo, competence, config, data_source, region_scoring, temporal

DEFAULT_TOTAL_AGENTS = 600


def _largest_remainder(weights: dict, total: int) -> dict:
    ids = list(weights)
    s = sum(max(w, 0) for w in weights.values())
    if s <= 0:
        base, extra = divmod(total, len(ids))
        return {i: base + (1 if k < extra else 0) for k, i in enumerate(ids)}
    exact = {i: total * max(weights[i], 0) / s for i in ids}
    alloc = {i: int(v) for i, v in exact.items()}
    rem = total - sum(alloc.values())
    for i in sorted(ids, key=lambda i: exact[i] - alloc[i], reverse=True)[:rem]:
        alloc[i] += 1
    return alloc


def _shift_label(critical_hours: list[int]) -> str:
    if not critical_hours:
        return "turno a definir"
    night = sum(1 for h in critical_hours if h in temporal.NIGHT)
    if night >= len(critical_hours) / 2:
        return "turno noturno (18h–00h)"
    if any(h in temporal.PEAK for h in critical_hours):
        return "turno de pico (priorizar horários de fluxo)"
    return "turno diurno (06h–18h)"


def _tactic(hotspot: dict) -> tuple[str, list[str]]:
    """Modelo de emprego a partir de modalidade + fatores temporalmente casados."""
    drivers = hotspot.get("driver_factors", [])
    social = hotspot.get("social_factors", [])
    support = sorted({f["orgao"] for f in drivers if not competence.is_state_agency(f["orgao"])})
    noturno = hotspot["temporal_profile"].startswith("predominantemente noturno")
    lighting = [f for f in drivers if f["orgao"] in ("Rio Luz", "COMLURB")]

    if noturno and lighting:
        tactic = ("Patrulhamento noturno a pé orientado por dados; acionar "
                  f"{lighting[0]['orgao']} para corrigir iluminação/poda no ponto.")
    elif any(f["orgao"] == "SEOP" for f in drivers):
        tactic = ("Patrulha no horário de pico com ordenamento da SEOP "
                  "(comércio/estacionamento irregular).")
    elif any(f["orgao"] == "CET-Rio" for f in drivers):
        tactic = "Presença no pico viário; CET-Rio para retenção de tráfego."
    else:
        tactic = "Presença ostensiva da FM orientada por dados no horário crítico."

    if social:
        tactic += (" Articulação com SMAS/saúde para população vulnerável "
                   "(sem ação repressiva).")
    return tactic, support


def operation_draft(days: int | None, total_agents: int = DEFAULT_TOTAL_AGENTS) -> dict:
    regions = data_source.regions()
    scores = region_scoring.compute_region_scores(days)

    region_weights = {r["fid"]: scores[r["fid"]]["risk_score"] for r in regions}
    region_alloc = _largest_remainder(region_weights, total_agents)

    allocations = []
    for reg in sorted(regions, key=lambda r: scores[r["fid"]]["risk_score"], reverse=True):
        fid = reg["fid"]
        agents = region_alloc[fid]
        bz = bingo.region_bingo(reg["region_id"], days)
        hotspots = bz["hotspots"]

        # divide o efetivo da região entre hotspots por severidade
        hs_weights = {h["hotspot_id"]: h["n_crimes"] for h in hotspots}
        hs_alloc = _largest_remainder(hs_weights, agents) if hotspots else {}

        hs_out = []
        for h in hotspots:
            tactic, support = _tactic(h)
            hs_out.append({
                "hotspot_id": h["hotspot_id"],
                "centroid": h["centroid"],
                "agents": hs_alloc.get(h["hotspot_id"], 0),
                "severity": h.get("severity"),
                "dominant_modality": h["dominant_modality"],
                "shift": _shift_label(h["critical_hours"]),
                "critical_hours_label": h["critical_hours_label"],
                "employment_model": tactic,
                "support_agencies": support,
                "camera_gap": h["camera"].get("gap"),
            })
        # rota: hotspots por severidade decrescente
        route = [h["hotspot_id"] for h in sorted(hs_out, key=lambda x: x["agents"], reverse=True)]

        allocations.append({
            "region_id": reg["region_id"],
            "region_name": reg["region_name"],
            "risk_score": scores[fid]["risk_score"],
            "agents": agents,
            "n_hotspots": len(hotspots),
            "hotspots": hs_out,
            "route": route,
        })

    return {
        "total_agents": total_agents,
        "allocated": sum(region_alloc.values()),
        "data_mode": config.DATA_MODE,
        "allocations": allocations,
    }
