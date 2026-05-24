"""CameraCoverageAgent — narra lacunas de cobertura nos hotspots.

Só temos LOCALIZAÇÃO de câmera (sem imagem, placa, rosto, biometria). Para
cada hotspot com `camera.gap=True`, este agente escreve uma frase operacional
explicando a lacuna no contexto do horário/modalidade crítica e indicando o
acionamento (FM + COR/CET-Rio para realocação/expansão). Determinístico se
sem chave.
"""
from __future__ import annotations

from . import provider

_SYSTEM = (
    "Você é o analista de cobertura de monitoramento do COR/Força Municipal. "
    "Para cada hotspot com lacuna de cobertura de câmera, escreva 1 frase "
    "operacional indicando a distância à câmera mais próxima, horário do "
    "crime e o acionamento (FM no terreno + COR para reavaliar cobertura). "
    "Use SOMENTE LOCALIZAÇÃO de câmera. PROIBIDO discutir placa, rosto, "
    "biometria, reconhecimento facial ou imagem bruta."
)

_SCHEMA = {
    "type": "object",
    "properties": {
        "gaps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "hotspot_id": {"type": "string"},
                    "narrative": {"type": "string"},
                    "action": {"type": "string"},
                },
                "required": ["hotspot_id", "narrative"],
            },
        },
        "summary": {"type": "string"},
    },
    "required": ["gaps"],
}


def _fallback_gap_narrative(h: dict) -> dict:
    dist = h["camera"].get("distance_m")
    return {
        "hotspot_id": h["hotspot_id"],
        "narrative": (
            f"Lacuna de cobertura: câmera mais próxima a {dist:.0f} m. "
            f"Crime dominante ({h.get('dominant_modality') or 'n/d'}) em "
            f"{h.get('critical_hours_label') or 'horários variáveis'}."
        ) if dist is not None else
            "Lacuna de cobertura no ponto crítico (distância não disponível).",
        "action": "FM no terreno + COR reavaliar realocação/expansão.",
    }


def narrate(bingo_hotspots: list[dict]) -> dict:
    """Recebe hotspots do bingo, devolve {gaps, summary} só para os com gap=True."""
    gaps_in = [h for h in bingo_hotspots if h.get("camera", {}).get("gap")]
    if not gaps_in:
        return {"gaps": [], "summary": "Sem lacunas de cobertura nos hotspots prioritários."}

    fallback = {
        "gaps": [_fallback_gap_narrative(h) for h in gaps_in],
        "summary": f"{len(gaps_in)} hotspot(s) com lacuna de cobertura — acionar COR/FM.",
    }
    prov = provider.get_provider()
    context = {"gaps": [{
        "hotspot_id": h["hotspot_id"],
        "distance_m": h["camera"].get("distance_m"),
        "dominant_modality": h.get("dominant_modality"),
        "critical_hours": h.get("critical_hours_label"),
        "temporal_profile": h.get("temporal_profile"),
    } for h in gaps_in]}
    enriched = prov.generate_structured(
        system=_SYSTEM, context=provider.json_block(context),
        task=("Para cada item em gaps, escreva 1 frase operacional (com "
              "distância e janela horária) e o acionamento sugerido. "
              "Mantenha hotspot_id exato."),
        schema=_SCHEMA, fallback=fallback,
    )
    return {
        "gaps": enriched.get("gaps") or fallback["gaps"],
        "summary": enriched.get("summary") or fallback["summary"],
        "generated_by": "CameraCoverageAgent",
        "llm_mode": prov.mode,
    }
