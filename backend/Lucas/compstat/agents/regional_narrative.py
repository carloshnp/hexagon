"""RegionalRiskNarrativeAgent — relatório individual por região (lazy + LLM).

Monta o esqueleto determinístico (score, grupos de ocorrência, provenance) e
faz UMA chamada estruturada à LLM para enriquecer narrativa + recomendações,
consumindo os relatos granulares. Sem chave, o esqueleto determinístico é a
resposta. O score nunca é inventado pela LLM.
"""
from __future__ import annotations

import pandas as pd

from .. import config, data_source, region_scoring, region_view
from . import camera as camera_agent
from . import factor as factor_agent
from . import occurrence_group, orchestrator, provider

_SYSTEM = (
    "Você é um analista de segurança pública MUNICIPAL apoiando a reunião semanal "
    "CompStat do Rio (com prefeito/Casa Civil). Enquadre pelos 4 pilares do CompStat: "
    "(1) inteligência precisa, (2) deployment rápido, (3) táticas eficazes, (4) follow-up. "
    "Escreva em português, objetivo e acionável. Baseie-se SOMENTE nos dados fornecidos. "
    "Nunca invente números nem o score (calculado por fórmula). Respeite o casamento "
    "TEMPORAL: só trate um fator urbano como causa quando ele coincide no horário com o "
    "crime (campo overlap_temporal/relevancia=driver). Cada recomendação indica o órgão "
    "MUNICIPAL competente (a FM é a força de emprego; PM-RJ é estadual = articulação). "
    "PROIBIDO reconhecimento facial, biometria, placa, perfilamento; população em situação "
    "de rua → articulação SMAS/saúde, nunca repressão. Aponte incertezas."
)

_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "full_explanation": {"type": "string"},
        "uncertainties": {"type": "array", "items": {"type": "string"}},
        "groups": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "group_id": {"type": "string"},
                    "summary": {"type": "string"},
                    "detailed_explanation": {"type": "string"},
                    "recommended_action": {"type": "string"},
                    "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                },
                "required": ["group_id"],
            },
        },
    },
    "required": ["summary", "full_explanation"],
}


def _relint_factors(reg: dict) -> list[dict]:
    relint = reg.get("relint") or {}
    out = []
    for sub in (relint.get("subareas") or [])[:3]:
        out.append({"subarea": sub.get("nome"), "fatores": sub.get("fatores")})
    return out


def _bingo_summary(region_id, days) -> dict:
    from .. import diagnosis  # import tardio (evita ciclo)
    diag = diagnosis.region_diagnosis(region_id, days)
    bz = diag["bingo"]
    return {
        "n_hotspots": bz["n_hotspots"],
        "hotspots": [{
            "centroid": h["centroid"],
            "n_crimes": h["n_crimes"],
            "dominant_modality": h["dominant_modality"],
            "critical_hours": h["critical_hours_label"],
            "temporal_profile": h["temporal_profile"],
            "driver_factors": [{"tipo": f["tipo"], "orgao": f["orgao"],
                                "overlap_temporal": f["overlap_temporal"]}
                               for f in h["driver_factors"]],
            "camera_gap": h["camera"].get("gap"),
        } for h in bz["hotspots"]],
        "signals": bz["signals"],
        "recommended_actions": diag["recommended_actions"],
    }


def _build_context(reg, sc, groups, days) -> dict:
    return {
        "region_name": reg["region_name"],
        "risk_score": sc["risk_score"],
        "risk_level": sc["risk_level"],
        "primary_agency": sc["primary_agency"],
        "secondary_agencies": sc["secondary_agencies"],
        "score_components": sc["components"],
        "counts": sc["counts"],
        "data_quality": sc["data_quality"],
        "time_window_days": days,
        "occurrence_types": region_view.occurrence_types(reg, days),
        "hourly_peaks": [h for h in region_view.hourly_histogram(reg, days) if h["count"] > 0][-6:],
        "relint_factors": _relint_factors(reg),
        "bingo": _bingo_summary(reg["region_id"], days),
        "occurrence_groups": [
            {
                "group_id": g["group_id"],
                "classe": g["classe"],
                "count": g["count"],
                "critical_hours": g["map_data"]["critical_hours"],
                "responsible_agency": g["action_plan"]["responsible_agency"],
                "relatos_amostra": g["_relatos_sample"],
            }
            for g in groups
        ],
    }


def _deterministic(reg, sc, groups, days) -> dict:
    c = sc["counts"]
    janela = f"últimos {days} dias" if days else "todo o histórico"
    expl_parts = [
        f"A região '{reg['region_name']}' tem score {sc['risk_score']:.0f}/100 "
        f"(nível {sc['risk_level']}) considerando {janela}.",
        "Componentes do score: " + "; ".join(
            f"{comp['label']} = {comp['raw_count']:.0f} (contribuição {comp['contribution']:.0f})"
            for comp in sc["components"]
        ) + ".",
    ]
    factors = _relint_factors(reg)
    if factors and factors[0].get("fatores"):
        f0 = factors[0]["fatores"]
        expl_parts.append(
            "Fatores urbanos (RELINT): " +
            "; ".join(f"{k}: {v}" for k, v in f0.items() if v)[:600] + "."
        )
    uncertainties = []
    for src, q in sc["data_quality"].items():
        if q == "aproximado":
            uncertainties.append(
                f"Contagem de {src} é aproximada (modo estático, proxy H3); "
                "ative o modo live para precisão."
            )
    return {
        "summary": region_view.region_summary(reg, sc, days),
        "full_explanation": " ".join(expl_parts),
        "uncertainties": uncertainties,
    }


def build_region_report(region_id: str, days: int | None) -> dict:
    reg = data_source.region_by_id(region_id)
    if reg is None:
        return {}
    sc = region_scoring.compute_region_scores(days)[reg["fid"]]
    groups = occurrence_group.build_groups(region_id, days)

    det = _deterministic(reg, sc, groups, days)
    context = _build_context(reg, sc, groups, days)

    prov = provider.get_provider()
    fallback = {**det, "groups": [
        {"group_id": g["group_id"], "summary": g["summary"],
         "detailed_explanation": g["detailed_explanation"],
         "recommended_action": g["action_plan"]["recommended_action"],
         "priority": g["action_plan"]["priority"]}
        for g in groups
    ]}
    enriched = prov.generate_structured(
        system=_SYSTEM,
        context=provider.json_block(context),
        task=("Gere o relatório estratégico desta região: summary, "
              "full_explanation, uncertainties e, para cada grupo de ocorrência "
              "(use o group_id exato), summary/detailed_explanation/"
              "recommended_action/priority com base nos relatos."),
        schema=_SCHEMA,
        fallback=fallback,
    )

    # Merge narrativa da LLM no esqueleto determinístico (preservando dados duros)
    llm_groups = {g.get("group_id"): g for g in (enriched.get("groups") or [])}
    occurrences = []
    for g in groups:
        gid = g["group_id"]
        eg = llm_groups.get(gid, {})
        ap = dict(g["action_plan"])
        if eg.get("recommended_action"):
            ap["recommended_action"] = eg["recommended_action"]
        if eg.get("priority"):
            ap["priority"] = eg["priority"]
        occurrences.append({
            "group_id": gid,
            "summary": eg.get("summary") or g["summary"],
            "detailed_explanation": eg.get("detailed_explanation") or g["detailed_explanation"],
            "score": g["score"],
            "action_plan": ap,
            "map_data": g["map_data"],
            "provenance": g["provenance"],
        })

    # Agentes especializados (1 chamada cada — ou fallback determinístico).
    from .. import diagnosis  # tardio: evita ciclo
    diag = diagnosis.region_diagnosis(region_id, days)
    bz = diag["bingo"]
    decision_trace = orchestrator.narrate(reg["region_name"], sc, bz, diag["decision_trace"])
    recommended_actions = factor_agent.narrate(diag["recommended_actions"], bz["hotspots"])
    camera_coverage = camera_agent.narrate(bz["hotspots"])

    return {
        "region_id": region_id,
        "region_name": reg["region_name"],
        "summary": enriched.get("summary") or det["summary"],
        "full_explanation": enriched.get("full_explanation") or det["full_explanation"],
        "score": {"final": sc["risk_score"], "level": sc["risk_level"],
                  "components": sc["components"]},
        "occurrences": occurrences,
        "uncertainties": enriched.get("uncertainties") or det["uncertainties"],
        "recommended_actions": recommended_actions,
        "camera_coverage": camera_coverage,
        "decision_trace": decision_trace,
        "bingo": bz,
        "provenance": region_view.provenance(reg, sc, days),
        "generated_by": "RegionalRiskNarrativeAgent",
        "llm_mode": prov.mode,
    }
