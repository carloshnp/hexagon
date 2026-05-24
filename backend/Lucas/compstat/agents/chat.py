"""ReportChatAgent — responde perguntas sobre o mapa, regiões e dados.

Retrieval determinístico do contexto da região (ou ranking geral), resposta via
LLM quando há chave, senão um resumo determinístico. Sempre cita região e
evidência e aponta limitações; nunca inventa dados.
"""
from __future__ import annotations

from .. import config, data_source, region_scoring, region_view
from . import occurrence_group, provider

_SYSTEM = (
    "Você é um assistente da reunião CompStat de segurança pública do Rio. "
    "Responda em português, com base EXCLUSIVA no contexto fornecido. Cite a "
    "região e as evidências (denúncias, ocorrências, fatores urbanos, RELINT). "
    "Se o contexto não tiver a resposta, diga explicitamente que não há evidência "
    "suficiente. Nunca invente números nem o score. PROIBIDO sugerir "
    "reconhecimento facial, biometria, placa, perfilamento ou ações "
    "criminalizantes contra população em situação de rua."
)


def _region_context(region_id: str, days: int | None) -> tuple[dict, dict, dict]:
    reg = data_source.region_by_id(region_id)
    sc = region_scoring.compute_region_scores(days)[reg["fid"]]
    groups = occurrence_group.build_groups(region_id, days)
    from .. import diagnosis  # import tardio (evita ciclo)
    diag = diagnosis.region_diagnosis(region_id, days)
    bz = diag["bingo"]
    ctx = {
        "region_name": reg["region_name"],
        "risk_score": sc["risk_score"],
        "risk_level": sc["risk_level"],
        "primary_agency": sc["primary_agency"],
        "secondary_agencies": sc["secondary_agencies"],
        "counts": sc["counts"],
        "data_quality": sc["data_quality"],
        "occurrence_types": region_view.occurrence_types(reg, days),
        "hourly_peaks": [h for h in region_view.hourly_histogram(reg, days) if h["count"] > 0],
        "bingo_hotspots": [{
            "critical_hours": h["critical_hours_label"],
            "temporal_profile": h["temporal_profile"],
            "dominant_modality": h["dominant_modality"],
            "driver_factors": [{"tipo": f["tipo"], "orgao": f["orgao"]} for f in h["driver_factors"]],
            "camera_gap": h["camera"].get("gap"),
            "camera_distance_m": h["camera"].get("distance_m"),
        } for h in bz["hotspots"]],
        "bingo_signals": bz["signals"],
        "recommended_actions": diag["recommended_actions"],
        "occurrence_groups": [
            {"classe": g["classe"], "count": g["count"],
             "critical_hours": g["map_data"]["critical_hours"],
             "responsible_agency": g["action_plan"]["responsible_agency"],
             "relatos_amostra": g["_relatos_sample"][:4]}
            for g in groups
        ],
    }
    return reg, ctx, sc


def _overview_context(days: int | None) -> dict:
    regions = data_source.regions()
    scores = region_scoring.compute_region_scores(days)
    ranked = sorted(regions, key=lambda r: scores[r["fid"]]["risk_score"], reverse=True)
    return {
        "ranked_regions": [
            {"region_id": r["region_id"], "region_name": r["region_name"],
             "risk_score": scores[r["fid"]]["risk_score"],
             "risk_level": scores[r["fid"]]["risk_level"],
             "primary_agency": scores[r["fid"]]["primary_agency"]}
            for r in ranked
        ]
    }


def _deterministic_region_answer(ctx: dict) -> str:
    types = ", ".join(f"{t['tipo']} ({t['count']})" for t in ctx["occurrence_types"][:3])
    peaks = sorted({h["hour"] for h in ctx["hourly_peaks"]},
                   key=lambda x: -[hh["count"] for hh in ctx["hourly_peaks"] if hh["hour"] == x][0])[:3]
    peak_str = ", ".join(f"{h:02d}h" for h in sorted(peaks)) if peaks else "sem padrão claro"
    return (
        f"A região {ctx['region_name']} está com risco {ctx['risk_level']} "
        f"(score {ctx['risk_score']:.0f}/100). Principais tipos de denúncia: "
        f"{types or 'sem dados suficientes'}. Horários de maior concentração: "
        f"{peak_str}. Órgão municipal sugerido: {ctx['primary_agency']}. "
        f"Baseado em {ctx['counts']['denuncias']} denúncias e "
        f"{ctx['counts']['ocorrencias']} ocorrências no recorte."
    )


def _deterministic_overview_answer(ctx: dict) -> str:
    top = ctx["ranked_regions"][:3]
    linhas = "; ".join(
        f"{r['region_name']} (score {r['risk_score']:.0f}, {r['risk_level']}, órgão {r['primary_agency']})"
        for r in top
    )
    return f"As regiões com maior risco no recorte são: {linhas}."


def build_chat_response(question: str, region_id: str | None, filters: dict) -> dict:
    days = config.window_to_days((filters or {}).get("time_window"))
    prov = provider.get_provider()
    trace = [f"retrieval: modo={config.DATA_MODE}, janela_dias={days}"]
    limitations: list[str] = []
    evidence_refs: list[dict] = []
    map_refs: list[str] = []

    if region_id and data_source.region_by_id(region_id):
        reg, ctx, sc = _region_context(region_id, days)
        trace.append(f"contexto da região {region_id} ({reg['region_name']})")
        fallback = _deterministic_region_answer(ctx)
        region_refs = [region_id]
        map_refs = ["occurrences", "denuncias", "critical_areas"]
        evidence_refs = region_view.provenance(reg, sc, days)
        for src, q in sc["data_quality"].items():
            if q == "aproximado":
                limitations.append(f"Contagem de {src} é aproximada (modo estático).")
        context_obj = ctx
    else:
        ctx = _overview_context(days)
        trace.append("contexto: ranking geral das 8 regiões")
        fallback = _deterministic_overview_answer(ctx)
        region_refs = [r["region_id"] for r in ctx["ranked_regions"][:3]]
        evidence_refs = [{"source": "CompStat Rio (Lucas)",
                          "description": "Ranking determinístico das 8 regiões."}]
        context_obj = ctx

    if prov.mode == "fake":
        limitations.append("Resposta determinística (sem LLM); defina ANTHROPIC_API_KEY para narrativa.")

    answer = prov.generate_text(
        system=_SYSTEM,
        context=provider.json_block(context_obj),
        task=question,
        fallback=fallback,
    )
    trace.append(f"geração: {prov.mode}")

    return {
        "answer": answer,
        "region_refs": region_refs,
        "map_refs": map_refs,
        "evidence_refs": evidence_refs,
        "limitations": limitations,
        "agent_trace": trace,
        "llm_mode": prov.mode,
    }
