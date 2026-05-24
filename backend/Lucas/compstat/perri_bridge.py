"""Ponte para o pacote `hexagon_spatial` do colega Perri (somente leitura/import).

Adiciona `backend/perri` ao sys.path e expõe imports *lazy* dos artefatos que
reusamos: pesos do MCDA (`scorer.WEIGHTS`), perfis de instituição
(`institution_scorer.INSTITUTIONS`), loaders dos CSVs brutos e o índice de
agências (geometria + RELINT). Nunca modificamos nada do Perri.
"""
from __future__ import annotations

import sys
from functools import lru_cache

from . import config

if str(config.PERRI_DIR) not in sys.path:
    sys.path.insert(0, str(config.PERRI_DIR))


@lru_cache(maxsize=1)
def get_weights() -> dict[str, float]:
    """Pesos do MCDA geral do Perri (pandas/numpy apenas — sempre disponível)."""
    from hexagon_spatial.scorer import WEIGHTS  # type: ignore

    return dict(WEIGHTS)


@lru_cache(maxsize=1)
def get_institutions() -> dict[str, dict]:
    """Perfis das 6 instituições (mandato, filtros, pesos).

    `institution_scorer` importa `h3_indexer` (depende de `h3`). Se `h3` não
    estiver instalado, caímos para um espelho mínimo dos pesos para não quebrar
    o modo estático.
    """
    try:
        from hexagon_spatial.institution_scorer import INSTITUTIONS  # type: ignore

        return INSTITUTIONS
    except Exception:  # pragma: no cover - fallback raro
        return _INSTITUTIONS_FALLBACK


@lru_cache(maxsize=1)
def get_loaders():
    """Módulo de loaders do Perri (lê os CSVs do submódulo). Só no modo live."""
    from hexagon_spatial import loaders  # type: ignore

    return loaders


@lru_cache(maxsize=1)
def get_agencies_full_index() -> dict[int, dict]:
    """fid → agência + RELINT completo, lido do shapefile (modo live)."""
    from hexagon_spatial.agency_areas import agencies_full_index  # type: ignore

    return agencies_full_index()


# Espelho mínimo dos pesos por instituição (usado só se `h3` faltar no modo
# estático). Mantém as mesmas chaves do INSTITUTIONS do Perri.
_INSTITUTIONS_FALLBACK: dict[str, dict] = {
    "PM-RJ": {"nome": "Polícia Militar do Rio de Janeiro",
              "mandato": "Policiamento ostensivo, crimes contra patrimônio e pessoa",
              "denuncias_classes": ["CRIMES CONTRA O PATRIMÔNIO",
                                     "ARMAS DE FOGO E ARTEFATOS EXPLOSIVOS",
                                     "SUBSTÂNCIAS ENTORPECENTES",
                                     "CRIMES CONTRA A PESSOA",
                                     "CRIMES CONTRA A LIBERDADE SEXUAL"],
              "fatores_tipos": [],
              "weights": {"ocorrencias": 0.50, "denuncias": 0.30, "fatores": 0.10, "cameras_inv": 0.10}},
    "GM-Rio": {"nome": "Guarda Municipal do Rio de Janeiro",
               "mandato": "Ordem pública, proteção do patrimônio municipal",
               "denuncias_classes": ["PERTURBAÇÃO DA ORDEM PÚBLICA",
                                     "CRIMES CONTRA A ADMINISTRAÇÃO PÚBLICA",
                                     "CRIMES DE TRÂNSITO", "DEFESA DO CIDADÃO"],
               "fatores_tipos": [],
               "weights": {"ocorrencias": 0.20, "denuncias": 0.35, "fatores": 0.45, "cameras_inv": 0.00}},
    "RioLuz": {"nome": "Rio Luz (Iluminação Pública)",
               "mandato": "Manutenção e expansão da rede de iluminação pública",
               "denuncias_classes": [],
               "fatores_tipos": [],
               "weights": {"ocorrencias": 0.30, "denuncias": 0.00, "fatores": 0.70, "cameras_inv": 0.00}},
    "COMLURB": {"nome": "Companhia Municipal de Limpeza Urbana",
                "mandato": "Limpeza urbana, coleta de lixo, poda de vegetação",
                "denuncias_classes": ["CRIMES CONTRA O MEIO AMBIENTE"],
                "fatores_tipos": [],
                "weights": {"ocorrencias": 0.20, "denuncias": 0.10, "fatores": 0.70, "cameras_inv": 0.00}},
    "SEOP": {"nome": "Secretaria de Ordem Pública",
             "mandato": "Fiscalização de ocupação irregular, ambulantes, posturas",
             "denuncias_classes": ["PERTURBAÇÃO DA ORDEM PÚBLICA",
                                   "CRIMES CONTRA A ADMINISTRAÇÃO PÚBLICA"],
             "fatores_tipos": [],
             "weights": {"ocorrencias": 0.15, "denuncias": 0.40, "fatores": 0.45, "cameras_inv": 0.00}},
    "CET-Rio": {"nome": "Companhia de Engenharia de Tráfego do Rio",
                "mandato": "Fluidez do tráfego, sinalização, gestão de vias",
                "denuncias_classes": ["CRIMES DE TRÂNSITO", "PERTURBAÇÃO DA ORDEM PÚBLICA"],
                "fatores_tipos": [],
                "weights": {"ocorrencias": 0.10, "denuncias": 0.25, "fatores": 0.65, "cameras_inv": 0.00}},
}
