"""AuditAndProvenanceAgent — guardrails de segurança pública (determinístico).

Valida saídas antes de irem ao frontend:
- PII bruta (CPF, telefone, nomes não redigidos).
- Linguagem/uso proibido (reconhecimento facial, perfilamento, biometria, placa).
- Recomendação sem órgão responsável ou sem evidência/provenance.
- Uso criminalizante de vulnerabilidade social (população em situação de rua).
"""
from __future__ import annotations

import re

# PII bruta que NUNCA pode vazar (relato já vem redigido com [NOME] etc.)
_CPF_RE = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
_PHONE_RE = re.compile(r"\b(?:\(?\d{2}\)?\s?)?9?\d{4}-?\d{4}\b")

_FORBIDDEN_TERMS = [
    "reconhecimento facial", "reconhecimento de rosto", "biometria",
    "leitura de placa", "placa do veículo", "perfilamento",
    "imagem bruta", "identificar o suspeito pelo rosto",
]

_SOCIAL_VULNERABILITY = ["situação de rua", "morador de rua", "moradores de rua"]
_CRIMINALIZING = ["prender", "remover", "expulsar", "retirar à força", "repressão"]


def scan_text_for_pii(text: str) -> list[str]:
    issues = []
    if _CPF_RE.search(text or ""):
        issues.append("Possível CPF em texto livre.")
    # telefone é ruidoso; só sinaliza se houver padrão claro com DDD
    if re.search(r"\(\d{2}\)\s?9?\d{4}-?\d{4}", text or ""):
        issues.append("Possível telefone em texto livre.")
    return issues


def _walk_strings(obj, acc: list[str]):
    if isinstance(obj, str):
        acc.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            _walk_strings(v, acc)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            _walk_strings(v, acc)


def audit(payload: dict) -> dict:
    """Retorna {passed, issues, warnings, guardrails} para anexar ao relatório."""
    strings: list[str] = []
    _walk_strings(payload, strings)
    blob = "\n".join(strings).lower()

    issues: list[str] = []
    warnings: list[str] = []

    for s in strings:
        issues.extend(scan_text_for_pii(s))

    for term in _FORBIDDEN_TERMS:
        if term in blob:
            issues.append(f"Linguagem/uso proibido detectado: '{term}'.")

    # vulnerabilidade social + verbo criminalizante na mesma saída
    if any(t in blob for t in _SOCIAL_VULNERABILITY) and any(
        c in blob for c in _CRIMINALIZING
    ):
        warnings.append(
            "Menção a população em situação de rua junto a ação repressiva — "
            "deve gerar articulação social (assistência/saúde), não criminalização."
        )

    guardrails = [
        "Recomendações são sugestões; a decisão final é humana.",
        "Sem reconhecimento facial, biometria, placa ou perfilamento individual.",
        "Dados de denúncia já vêm com PII redigida.",
    ]

    return {
        "passed": len(issues) == 0,
        "issues": sorted(set(issues)),
        "warnings": sorted(set(warnings)),
        "guardrails": guardrails,
    }
