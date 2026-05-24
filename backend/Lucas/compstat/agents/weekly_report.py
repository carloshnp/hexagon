"""StrategicWeeklyReportAgent — relatório estratégico semanal para a reunião.

Consolida os scores das 8 regiões em ranking, prioridades, matriz de órgãos e
referências de mapa. Determinístico + enriquecimento LLM (resumo, justificativas).
"""
from __future__ import annotations

import datetime as dt

from .. import config, data_source, region_scoring
from . import provider

_SYSTEM = (
    "Você é o relator da reunião semanal CompStat de segurança pública do Rio. "
    "Escreva em português para gestores municipais, de forma executiva e "
    "acionável. Use SOMENTE os dados fornecidos; não invente números nem scores. "
    "Para cada região priorizada, justifique com base nos componentes do score e "
    "no órgão responsável. PROIBIDO reconhecimento facial, biometria, placa, "
    "perfilamento ou ações criminalizantes. Aponte limitações dos dados."
)

_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "strategic_priorities": {"type": "array", "items": {"type": "string"}},
        "ranked_rationales": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "region_id": {"type": "string"},
                    "rationale": {"type": "string"},
                },
                "required": ["region_id"],
            },
        },
    },
    "required": ["summary"],
}


def _agency_matrix(regions, scores) -> list[dict]:
    by_agency: dict[str, list[str]] = {}
    for reg in regions:
        ag = scores[reg["fid"]]["primary_agency"]
        by_agency.setdefault(ag, []).append(reg["region_id"])
    return [
        {"agency": ag, "regions": regs, "n_regions": len(regs)}
        for ag, regs in sorted(by_agency.items(), key=lambda kv: len(kv[1]), reverse=True)
    ]


def build_weekly_report(days: int | None) -> dict:
    regions = data_source.regions()
    scores = region_scoring.compute_region_scores(days)
    ranked = sorted(regions, key=lambda r: scores[r["fid"]]["risk_score"], reverse=True)

    ranked_regions = []
    for reg in ranked:
        sc = scores[reg["fid"]]
        ranked_regions.append({
            "region_id": reg["region_id"],
            "region_name": reg["region_name"],
            "risk_score": sc["risk_score"],
            "risk_level": sc["risk_level"],
            "primary_agency": sc["primary_agency"],
            "rationale": (
                f"{sc['counts']['ocorrencias']} ocorrências e "
                f"{sc['counts']['denuncias']} denúncias; órgão {sc['primary_agency']}."
            ),
        })

    top = ranked_regions[0] if ranked_regions else None
    janela = f"últimos {days} dias" if days else "todo o histórico"
    det_summary = (
        f"{len(regions)} regiões analisadas ({janela}). "
        + (f"Maior prioridade: {top['region_name']} "
           f"(score {top['risk_score']:.0f}, órgão {top['primary_agency']}). "
           if top else "")
        + "Ranking e matriz de responsabilidade no corpo do relatório."
    )
    det_priorities = [
        f"{r['region_name']}: nível {r['risk_level']} (score {r['risk_score']:.0f}) — órgão {r['primary_agency']}."
        for r in ranked_regions[:3]
    ]

    context = {
        "time_window_days": days,
        "data_mode": config.DATA_MODE,
        "ranked_regions": ranked_regions,
        "agency_matrix": _agency_matrix(regions, scores),
    }
    fallback = {
        "summary": det_summary,
        "strategic_priorities": det_priorities,
        "ranked_rationales": [
            {"region_id": r["region_id"], "rationale": r["rationale"]} for r in ranked_regions
        ],
    }

    prov = provider.get_provider()
    enriched = prov.generate_structured(
        system=_SYSTEM,
        context=provider.json_block(context),
        task=("Gere o relatório semanal: summary executivo, strategic_priorities "
              "(lista) e ranked_rationales (justificativa por region_id)."),
        schema=_SCHEMA,
        fallback=fallback,
    )

    rationale_by_id = {r.get("region_id"): r.get("rationale")
                       for r in (enriched.get("ranked_rationales") or [])}
    for r in ranked_regions:
        if rationale_by_id.get(r["region_id"]):
            r["rationale"] = rationale_by_id[r["region_id"]]

    week_id = dt.date.today().strftime("%Y_%m_%d")
    return {
        "report_id": f"weekly_{week_id}",
        "title": "Relatório Estratégico Semanal — CompStat Rio",
        "summary": enriched.get("summary") or det_summary,
        "ranked_regions": ranked_regions,
        "strategic_priorities": enriched.get("strategic_priorities") or det_priorities,
        "agency_matrix": context["agency_matrix"],
        "map_references": [r["region_id"] for r in ranked_regions],
        "provenance": [{
            "source": "CompStat Rio (Lucas)",
            "description": f"Consolidação determinística dos scores das {len(regions)} regiões; modo {config.DATA_MODE}.",
        }],
        "generated_by": "StrategicWeeklyReportAgent",
        "llm_mode": prov.mode,
    }
