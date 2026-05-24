"""Tabela de competência: fator urbano → órgão municipal responsável (data-driven).

A coluna `ocorrencia_orgao_nome`/`orgao_responsavel` do `fatores_urbanos.csv` JÁ diz
qual órgão é responsável por cada tipo de fator. Aqui derivamos o mapa do próprio
dado (modo live) com fallback embutido (modo estático), e anexamos metadados de
esfera (municipal × estadual) e mandato. Foco MUNICIPAL: a FM é a força de emprego;
PM-RJ é estadual e entra como articulação, não como alocação municipal.
"""
from __future__ import annotations

from functools import lru_cache

from . import data_source

# Metadados dos órgãos (esfera + mandato). Chaves batem com os nomes do dataset.
AGENCY_META: dict[str, dict] = {
    "FM":        {"esfera": "municipal", "mandato": "Força Municipal — emprego operacional orientado por dados", "social": False},
    "GM-Rio":    {"esfera": "municipal", "mandato": "Guarda Municipal — ordem pública e patrimônio", "social": False},
    "SEOP":      {"esfera": "municipal", "mandato": "Ordem Pública — fiscalização de comércio/ocupação irregular", "social": False},
    "COMLURB":   {"esfera": "municipal", "mandato": "Limpeza urbana, coleta, poda de vegetação", "social": False},
    "Rio Luz":   {"esfera": "municipal", "mandato": "Iluminação pública", "social": False},
    "SECONSERVA":{"esfera": "municipal", "mandato": "Conservação — calçadas, mobiliário urbano, tapumes", "social": False},
    "CET-Rio":   {"esfera": "municipal", "mandato": "Engenharia de tráfego e fluidez viária", "social": False},
    "SMTR":      {"esfera": "municipal", "mandato": "Transportes — pontos de ônibus e mobilidade", "social": False},
    "SMAS":      {"esfera": "municipal", "mandato": "Assistência Social — articulação para população vulnerável", "social": True},
    "Prefeitura":{"esfera": "municipal", "mandato": "Coordenação municipal geral", "social": False},
    "PM-RJ":     {"esfera": "estadual",  "mandato": "Polícia Militar (estadual) — articulação, não alocação municipal", "social": False},
}

# Fallback (modo estático): órgão dominante por tipo de fator, extraído do dataset oficial.
_FACTOR_AGENCY_FALLBACK: dict[str, str] = {
    "Calçada estreita forçando pedestres à pista": "SECONSERVA",
    "Cena de uso de drogas": "SMAS",
    "Comércio irregular obstruindo a visibilidade do passeio": "SEOP",
    "Estacionamento irregular forçando pedestres à pista": "SEOP",
    "Lixo/entulho forçando pedestres à pista": "COMLURB",
    "Lixo/entulho obstruindo a visibilidade": "COMLURB",
    "Mobiliário abandonado servindo de esconderijo": "SECONSERVA",
    "Mobiliário urbano desviando pedestres para a pista": "SECONSERVA",
    "Mobiliário/estrutura servindo de esconderijo": "SECONSERVA",
    "Motocicletas trafegando no passeio": "GM-Rio",
    "Pessoas em situação de rua": "SMAS",
    "Ponto de retenção do tráfego": "CET-Rio",
    "Ponto de ônibus com histórico de vandalismo": "SMTR",
    "Praças e Parques": "GM-Rio",
    "Tapumes servindo de esconderijo": "SECONSERVA",
    "Vegetação encobrindo iluminação pública": "COMLURB",
    "Vegetação obstruindo a visibilidade do passeio": "COMLURB",
    "Veículos de grande porte obstruindo a visibilidade": "SEOP",
    "Vãos ou cavidades usados como esconderijo": "SECONSERVA",
    "Área mal iluminada com circulação de pedestres": "Rio Luz",
    "Área mal iluminada com parada de veículos": "Rio Luz",
}


@lru_cache(maxsize=1)
def factor_agency_map() -> dict[str, str]:
    """tipo_fator → órgão. Deriva do dado em modo live; senão usa o fallback oficial."""
    fat = data_source.fatores()
    if fat is not None and "ocorrencia_orgao_nome" in fat.columns:
        try:
            g = (
                fat.dropna(subset=["tipo_ocorrencia_descricao", "ocorrencia_orgao_nome"])
                .groupby("tipo_ocorrencia_descricao")["ocorrencia_orgao_nome"]
                .agg(lambda s: s.value_counts().index[0])
            )
            mapping = {str(k): str(v) for k, v in g.items()}
            if mapping:
                return {**_FACTOR_AGENCY_FALLBACK, **mapping}
        except Exception:
            pass
    return dict(_FACTOR_AGENCY_FALLBACK)


def agency_for_factor(tipo: str) -> str:
    return factor_agency_map().get(str(tipo), "Prefeitura")


def agency_meta(agency: str) -> dict:
    return AGENCY_META.get(agency, {"esfera": "municipal", "mandato": agency, "social": False})


def is_state_agency(agency: str) -> bool:
    return agency_meta(agency)["esfera"] == "estadual"


def is_social_agency(agency: str) -> bool:
    return agency_meta(agency)["social"]


# Ação recomendada por órgão (ponto de partida; a LLM refina com o contexto).
RECOMMENDED_ACTION: dict[str, str] = {
    "FM": "Presença operacional da Força Municipal orientada por dados no horário crítico.",
    "GM-Rio": "Acionar a Guarda Municipal para ordenamento e proteção do patrimônio.",
    "SEOP": "Fiscalização de ordem pública: comércio/estacionamento irregular no ponto.",
    "COMLURB": "Poda da vegetação e remoção de entulho que reduzem visibilidade/iluminação.",
    "Rio Luz": "Vistoria e reparo de iluminação pública no ponto crítico.",
    "SECONSERVA": "Conservação: calçadas, mobiliário e tapumes que criam pontos cegos.",
    "CET-Rio": "Revisar sinalização e fluxo no ponto de retenção de tráfego.",
    "SMTR": "Manutenção/segurança no ponto de ônibus.",
    "SMAS": "Articulação social (SMAS/saúde) para população vulnerável — sem ação repressiva.",
    "Prefeitura": "Encaminhar à coordenação municipal competente.",
    "PM-RJ": "Articulação com a Polícia Militar (esfera estadual).",
}


def recommended_action(agency: str) -> str:
    return RECOMMENDED_ACTION.get(agency, RECOMMENDED_ACTION["FM"])
