"""MapRegionOrchestratorAgent — narra o trace de decisão da região.

`diagnosis.decision_trace` produz `considered/discarded` cruas. Este agente
adiciona a narrativa (por que essas camadas, com que peso qualitativo) que vai
ao painel "Por que esta região está nesta posição?". Determinístico se sem chave.
"""
from __future__ import annotations

from . import provider

_SYSTEM = (
    "Você é o coordenador de inteligência da reunião CompStat MUNICIPAL do Rio. "
    "Explique, em 1-2 parágrafos curtos, POR QUE as camadas listadas entraram "
    "na análise desta região e quais ficaram de fora — sem inventar números. "
    "Use os valores fornecidos (componentes do score, hotspots, qualidade dos "
    "dados). Termine recomendando UMA camada-chave a observar na semana. "
    "PROIBIDO reconhecimento facial, biometria, placa, perfilamento."
)

_SCHEMA = {
    "type": "object",
    "properties": {
        "narrative": {"type": "string"},
        "layer_weights": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "layer": {"type": "string"},
                    "weight": {"type": "string", "enum": ["alto", "medio", "baixo"]},
                    "rationale": {"type": "string"},
                },
                "required": ["layer", "weight"],
            },
        },
        "key_layer_to_watch": {"type": "string"},
    },
    "required": ["narrative"],
}


def _deterministic(region_name: str, sc: dict, bz: dict, trace: dict) -> dict:
    top = sorted(sc["components"], key=lambda c: c["contribution"], reverse=True)
    parts = [c["label"] for c in top[:2]]
    narrative = (
        f"A posição de {region_name} no ranking é puxada por "
        f"{parts[0]} e {parts[1]} (maiores contribuições no score). "
        f"Foram identificados {bz['n_hotspots']} pontos críticos no recorte; "
        f"{len(trace['considered'])} camadas consideradas, "
        f"{len(trace['discarded'])} sinais descartados (overlap temporal baixo "
        "ou estruturais)."
    )
    weights = []
    for c in sc["components"]:
        w = "alto" if c["contribution"] >= 25 else "medio" if c["contribution"] >= 10 else "baixo"
        weights.append({
            "layer": c["label"],
            "weight": w,
            "rationale": f"contribuição {c['contribution']:.0f} ao score final.",
        })
    return {
        "narrative": narrative,
        "layer_weights": weights,
        "key_layer_to_watch": top[0]["label"] if top else "denúncias",
    }


def narrate(region_name: str, sc: dict, bz: dict, trace: dict) -> dict:
    """Recebe score (sc), bingo (bz) e decision_trace cru; devolve trace enriquecido."""
    prov = provider.get_provider()
    fallback = _deterministic(region_name, sc, bz, trace)
    context = {
        "region_name": region_name,
        "score_components": sc["components"],
        "counts": sc["counts"],
        "data_quality": sc["data_quality"],
        "n_hotspots": bz["n_hotspots"],
        "considered": trace["considered"],
        "discarded": trace["discarded"],
        "signals": bz.get("signals", []),
    }
    enriched = prov.generate_structured(
        system=_SYSTEM, context=provider.json_block(context),
        task=("Narre, em 1-2 parágrafos, por que estas camadas entraram na "
              "análise e quais ficaram de fora. Liste o peso qualitativo de "
              "cada camada e recomende UMA para observar na próxima semana."),
        schema=_SCHEMA, fallback=fallback,
    )
    return {
        "considered": trace["considered"],
        "discarded": trace["discarded"],
        "narrative": enriched.get("narrative") or fallback["narrative"],
        "layer_weights": enriched.get("layer_weights") or fallback["layer_weights"],
        "key_layer_to_watch": enriched.get("key_layer_to_watch") or fallback["key_layer_to_watch"],
        "generated_by": "MapRegionOrchestratorAgent",
        "llm_mode": prov.mode,
    }
