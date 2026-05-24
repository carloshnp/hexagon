"""Orquestração de relatórios e chat: cache (lazy) + auditoria de guardrails.

Os routers chamam este serviço; ele decide o que recomputar, aplica o
AuditAndProvenanceAgent e anexa guardrails/avisos à resposta.
"""
from __future__ import annotations

from . import cache, config, data_source
from .agents import (
    audit,
    chat as chat_agent,
    provider,
    regional_narrative,
    weekly_report as weekly_agent,
)


def region_report(region_id: str, preset: str | None) -> dict | None:
    if data_source.region_by_id(region_id) is None:
        return None
    days = config.window_to_days(preset)
    prov = provider.get_provider()
    key = cache.make_key("region_report", region_id, days, prov.mode)

    def _compute() -> dict:
        report = regional_narrative.build_region_report(region_id, days)
        a = audit.audit(report)
        report["guardrails"] = a["guardrails"]
        if a["issues"] or a["warnings"]:
            report["audit_flags"] = {"issues": a["issues"], "warnings": a["warnings"]}
        return report

    report, was_cached = cache.get_or_compute(key, _compute)
    return {**report, "cached": was_cached}


def weekly_report(preset: str | None) -> dict:
    days = config.window_to_days(preset)
    prov = provider.get_provider()
    key = cache.make_key("weekly_report", days, prov.mode)

    def _compute() -> dict:
        report = weekly_agent.build_weekly_report(days)
        a = audit.audit(report)
        if a["issues"] or a["warnings"]:
            report["audit_flags"] = {"issues": a["issues"], "warnings": a["warnings"]}
        return report

    report, _ = cache.get_or_compute(key, _compute)
    return report


def chat(question: str, region_id: str | None, filters: dict) -> dict:
    """Chat não é cacheado (pergunta é variável); audita a resposta."""
    response = chat_agent.build_chat_response(question, region_id, filters)
    a = audit.audit(response)
    if a["issues"] or a["warnings"]:
        response.setdefault("limitations", []).extend(a["issues"] + a["warnings"])
    return response
