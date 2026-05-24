"""OperationDraftAgent — narra o rascunho operacional (alocação dos 600 agentes).

Os números vêm determinísticos de `operations.py`; a LLM só produz o resumo
executivo e a justificativa por região (com OK humano). Fallback determinístico.
"""
from __future__ import annotations

from . import provider

_SYSTEM = (
    "Você é o oficial de planejamento da Força Municipal do Rio na reunião CompStat. "
    "Escreva em português, objetivo e operacional. Use SOMENTE os números fornecidos "
    "(efetivo, turnos, hotspots) — não invente. A alocação é SUGERIDA e depende de "
    "aprovação humana. Enquadre pelos 4 pilares do CompStat (inteligência → deployment "
    "rápido → táticas → follow-up). PROIBIDO reconhecimento facial, biometria, placa, "
    "perfilamento; população vulnerável → articulação SMAS/saúde, nunca repressão."
)

_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "region_rationales": {
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


def _deterministic(draft: dict) -> dict:
    allocs = draft["allocations"]
    top = allocs[0] if allocs else None
    summary = (
        f"Rascunho operacional: {draft['allocated']} de {draft['total_agents']} agentes "
        f"alocados em {len(allocs)} polígonos, proporcional ao risco e concentrados nos "
        f"hotspots de cada área (alocação cirúrgica). "
        + (f"Maior prioridade: {top['region_name']} com {top['agents']} agentes em "
           f"{top['n_hotspots']} pontos críticos. " if top else "")
        + "Predomínio de turno noturno nos pontos de roubo a transeunte. Sugerido — requer OK humano."
    )
    rationales = [{
        "region_id": a["region_id"],
        "rationale": (f"{a['agents']} agentes ({a['n_hotspots']} hotspots); "
                      f"score {a['risk_score']:.0f}."),
    } for a in allocs]
    return {"summary": summary, "region_rationales": rationales}


def narrate(draft: dict) -> dict:
    prov = provider.get_provider()
    fallback = _deterministic(draft)
    context = {
        "total_agents": draft["total_agents"],
        "allocations": [{
            "region_id": a["region_id"], "region_name": a["region_name"],
            "risk_score": a["risk_score"], "agents": a["agents"],
            "n_hotspots": a["n_hotspots"],
            "hotspots": [{"shift": h["shift"], "agents": h["agents"],
                         "modality": h["dominant_modality"],
                         "employment_model": h["employment_model"],
                         "support_agencies": h["support_agencies"]}
                        for h in a["hotspots"][:3]],
        } for a in draft["allocations"]],
    }
    enriched = prov.generate_structured(
        system=_SYSTEM, context=provider.json_block(context),
        task=("Gere o resumo executivo do rascunho operacional e uma justificativa "
              "curta por região (region_id exato), enquadrando pelos 4 pilares CompStat."),
        schema=_SCHEMA, fallback=fallback,
    )
    rat = {r.get("region_id"): r.get("rationale") for r in (enriched.get("region_rationales") or [])}
    for a in draft["allocations"]:
        if rat.get(a["region_id"]):
            a["rationale"] = rat[a["region_id"]]
    return {
        **draft,
        "summary": enriched.get("summary") or fallback["summary"],
        "generated_by": "OperationDraftAgent",
        "llm_mode": prov.mode,
        "status": "sugerido",   # requer OK humano (pilar follow-up no próximo ciclo)
    }
