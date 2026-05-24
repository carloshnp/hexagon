"""Mapeamento ocorrência/classe → órgão competente e modelos de ação.

Deriva o órgão primário de cada classe de denúncia a partir dos perfis das
instituições do Perri (`INSTITUTIONS`), e fornece modelos de ação por órgão.
"""
from __future__ import annotations

from functools import lru_cache

from .. import perri_bridge

# Modelos de ação recomendada por órgão (ponto de partida; a LLM refina).
ACTION_TEMPLATES = {
    "PM-RJ": "Reforçar policiamento ostensivo orientado por dados no horário crítico.",
    "GM-Rio": "Acionar a Guarda Municipal para ordenamento e proteção do patrimônio público.",
    "RioLuz": "Solicitar vistoria/reparo de iluminação pública nos pontos de maior concentração.",
    "COMLURB": "Programar limpeza, poda e remoção de entulho que reduzem visibilidade.",
    "SEOP": "Realizar fiscalização de ordem pública (ambulantes, ocupação irregular).",
    "CET-Rio": "Revisar sinalização e fluxo viário nos pontos de retenção de tráfego.",
    "FM": "Acionar a Força Municipal para presença operacional orientada por evidência.",
}

# Prioridade entre instituições quando uma classe é coberta por mais de uma.
_PRIORITY = ["PM-RJ", "GM-Rio", "SEOP", "CET-Rio", "COMLURB", "RioLuz"]


@lru_cache(maxsize=1)
def _classe_to_agencies() -> dict[str, list[str]]:
    institutions = perri_bridge.get_institutions()
    rev: dict[str, list[str]] = {}
    for inst_id, prof in institutions.items():
        for classe in prof.get("denuncias_classes") or []:
            rev.setdefault(classe, []).append(inst_id)
    # ordena cada lista pela prioridade definida
    for classe, lst in rev.items():
        lst.sort(key=lambda i: _PRIORITY.index(i) if i in _PRIORITY else 99)
    return rev


def agency_for_classe(classe: str) -> tuple[str, list[str]]:
    """Retorna (órgão_primário, órgãos_de_apoio) para uma classe de denúncia."""
    lst = _classe_to_agencies().get(classe, [])
    if not lst:
        return "PM-RJ", []
    return lst[0], lst[1:3]


def action_for_agency(agency: str) -> str:
    return ACTION_TEMPLATES.get(agency, ACTION_TEMPLATES["FM"])
