"""UrbanFactorActionAgent — narra cada fator urbano → órgão → ação concreta.

`competence.RECOMMENDED_ACTION` tem templates fixos ("Vistoria e reparo de
iluminação..."). Este agente contextualiza pelo horário do crime, modalidade
dominante e cobertura de câmera no hotspot, gerando uma ação operacional
acionável (sem perder a ressalva social do SMAS). Fallback: o template.
"""
from __future__ import annotations

from .. import competence
from . import provider

_SYSTEM = (
    "Você é o oficial de articulação intersetorial da Força Municipal do Rio. "
    "Para cada fator urbano com co-ocorrência TEMPORAL no hotspot, escreva uma "
    "ação curta (1 frase) que o órgão competente deve executar — citando "
    "horário do crime e modalidade. Em fatores sociais (SMAS), articulação com "
    "assistência/saúde, NUNCA repressão. Em órgão estadual (PM-RJ), articulação. "
    "Use SOMENTE o que está no contexto; não invente endereço, placa ou pessoa. "
    "PROIBIDO reconhecimento facial, biometria, placa, perfilamento."
)

_SCHEMA = {
    "type": "object",
    "properties": {
        "actions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "key": {"type": "string"},
                    "agency": {"type": "string"},
                    "narrative": {"type": "string"},
                    "ressalva": {"type": "string"},
                },
                "required": ["key", "narrative"],
            },
        },
    },
    "required": ["actions"],
}


def _key(action: dict) -> str:
    return f"{action['responsible_agency']}|{action['problem']}|{action.get('hotspot_id','')}"


def _fallback_narrative(action: dict) -> str:
    base = competence.recommended_action(action["responsible_agency"])
    win = action.get("time_window")
    return f"{base} Janela: {win}." if win else base


def narrate(actions: list[dict], bingo_hotspots: list[dict]) -> list[dict]:
    """Enriquece recommended_actions in place com narrativa e ressalva."""
    if not actions:
        return actions
    hs_by_id = {h["hotspot_id"]: h for h in bingo_hotspots}
    prov = provider.get_provider()
    fallback = {"actions": [{"key": _key(a),
                             "agency": a["responsible_agency"],
                             "narrative": _fallback_narrative(a),
                             "ressalva": "Articulação social — sem ação repressiva."
                                         if competence.is_social_agency(a["responsible_agency"])
                                         else ""}
                            for a in actions]}
    context = {
        "actions": [{
            "key": _key(a),
            "problem": a["problem"],
            "agency": a["responsible_agency"],
            "esfera": a["esfera"],
            "priority": a["priority"],
            "time_window": a.get("time_window"),
            "hotspot_id": a.get("hotspot_id"),
            "hotspot": {
                "dominant_modality": hs_by_id.get(a.get("hotspot_id"), {}).get("dominant_modality"),
                "temporal_profile": hs_by_id.get(a.get("hotspot_id"), {}).get("temporal_profile"),
                "camera_gap": hs_by_id.get(a.get("hotspot_id"), {}).get("camera", {}).get("gap"),
            },
        } for a in actions],
    }
    enriched = prov.generate_structured(
        system=_SYSTEM, context=provider.json_block(context),
        task=("Para cada item em actions, gere uma narrativa operacional curta "
              "(1 frase) citando órgão, problema, horário e modalidade. "
              "Mantenha a `key` exatamente como recebida."),
        schema=_SCHEMA, fallback=fallback,
    )
    by_key = {a.get("key"): a for a in (enriched.get("actions") or [])}
    out = []
    for a in actions:
        eg = by_key.get(_key(a), {})
        merged = dict(a)
        merged["narrative"] = eg.get("narrative") or _fallback_narrative(a)
        ressalva = eg.get("ressalva") or (
            "Articulação social — sem ação repressiva."
            if competence.is_social_agency(a["responsible_agency"]) else ""
        )
        if ressalva:
            merged["ressalva"] = ressalva
        out.append(merged)
    return out
