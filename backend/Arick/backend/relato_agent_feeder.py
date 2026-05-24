"""
relato_agent_feeder.py

Monta o payload (system prompt + user message + contexto estruturado) que o
backend envia ao agente Claude para interpretar o `relato_redacted` de uma
denúncia do disk-denúncia.

O payload já está no formato esperado pela Anthropic Messages API
(anthropic.messages.create(**payload)). Os campos com prefixo `_` são
metadados do nosso sistema e devem ser removidos antes de enviar à API.

Uso programático:
    from backend.relato_agent_feeder import build_agent_request, run_agent

    payload = build_agent_request('1024.6.2020')
    # ou, se ANTHROPIC_API_KEY estiver no env:
    resposta = run_agent('1024.6.2020')

Uso CLI:
    python backend/relato_agent_feeder.py 1024.6.2020
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd


MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 1024

SYSTEM_PROMPT = """Você é um analista da Central de Inteligência de Segurança Pública do Rio de Janeiro.
Sua tarefa é interpretar relatos de denúncias anônimas (Disk-Denúncia) e produzir um resumo
estruturado que ajude as forças de segurança a priorizar e investigar a ocorrência.

Para cada relato, devolva UM ÚNICO JSON com a estrutura:

{
  "resumo": "1-2 frases descrevendo o que está acontecendo no relato",
  "urgencia": "BAIXA" | "MEDIA" | "ALTA" | "CRITICA",
  "elementos_identificados": {
    "pessoas": ["descrições físicas, apelidos, papéis (chefe, vigia, etc.)"],
    "veiculos": ["modelo, cor, placa parcial, etc."],
    "locais": ["referências como esquinas, comércios, pontos de acesso"],
    "modus_operandi": ["padrões de atuação, horários, frequência"]
  },
  "crimes_inferidos": [
    {"classe": "...", "tipo": "...", "confianca": 0.0}
  ],
  "risco_iminente": true | false,
  "recomendacao_acao": "uma frase com a ação prioritária",
  "confianca_relato": 0.0
}

Regras importantes:
- O relato JÁ foi redacted: tokens como [NOME], [TELEFONE], [NUMERO], [ENDERECO]
  substituem PII. Não tente recuperar ou inventar essas informações.
- Use o contexto estruturado (classificação oficial, localização, órgãos notificados,
  envolvidos) como apoio à interpretação — mas a primazia é o que está no RELATO.
- Se o relato é vago, marque confianca_relato baixa e seja explícito no resumo.
- Responda APENAS com o JSON. Sem texto antes ou depois, sem markdown fences.
"""


def load_dataframes(csv_path: str | Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Reproduz a normalização do notebook disk_denuncia_transform.ipynb."""
    raw = pd.read_csv(csv_path, encoding="latin-1", sep=";", low_memory=False)
    raw["numero_denuncia"] = raw["numero_denuncia"].ffill()

    for col in ["latitude", "longitude"]:
        raw[col] = (
            raw[col].astype(str).str.replace(",", ".", regex=False).replace("nan", np.nan)
        )
        raw[col] = pd.to_numeric(raw[col], errors="coerce")

    denuncia_cols = [
        "numero_denuncia", "id_denuncia", "data_denuncia", "data_difusao",
        "status_denuncia", "tipo_logradouro", "logradouro", "numero_logradouro",
        "complemento_logradouro", "bairro_logradouro", "subbairro_logradouro",
        "referencia_logradouro", "municipio", "estado",
        "latitude", "longitude",
        "id_classe", "classe", "id_tipo", "tipo", "assunto_principal",
        "relato_redacted",
    ]
    df_denuncias = (
        raw[raw["id_denuncia"].notna()][denuncia_cols]
        .drop_duplicates(subset="numero_denuncia")
        .reset_index(drop=True)
    )
    for col in ["data_denuncia", "data_difusao"]:
        df_denuncias[col] = pd.to_datetime(df_denuncias[col], errors="coerce")

    df_orgaos = (
        raw[raw["orgaos.id"].notna()]
        [["numero_denuncia", "orgaos.id", "orgaos.nome", "orgaos.tipo"]]
        .drop_duplicates()
        .rename(columns={"orgaos.id": "orgao_id", "orgaos.nome": "orgao_nome", "orgaos.tipo": "orgao_tipo"})
        .reset_index(drop=True)
    )

    assuntos_a = (
        raw[raw["assuntos.id_classe"].notna()]
        [["numero_denuncia", "assuntos.id_classe", "assuntos.classe",
          "assuntos.tipos.id_tipo", "assuntos.tipos.tipo", "assuntos.tipos.assunto_principal"]]
        .rename(columns={
            "assuntos.id_classe": "id_classe", "assuntos.classe": "classe",
            "assuntos.tipos.id_tipo": "id_tipo", "assuntos.tipos.tipo": "tipo",
            "assuntos.tipos.assunto_principal": "assunto_principal",
        })
    )
    assuntos_b = (
        raw[raw["tipos.id_tipo"].notna()]
        [["numero_denuncia", "id_classe", "classe",
          "tipos.id_tipo", "tipos.tipo", "tipos.assunto_principal"]]
        .rename(columns={
            "tipos.id_tipo": "id_tipo", "tipos.tipo": "tipo",
            "tipos.assunto_principal": "assunto_principal",
        })
    )
    df_assuntos = (
        pd.concat([assuntos_a, assuntos_b], ignore_index=True)
        .drop_duplicates(subset=["numero_denuncia", "id_tipo"])
        .reset_index(drop=True)
    )

    df_envolvidos = (
        raw[raw["envolvidos.id"].notna()]
        [["numero_denuncia", "envolvidos.id", "envolvidos.sexo",
          "envolvidos.idade", "envolvidos.pele", "envolvidos.estatura",
          "envolvidos.porte", "envolvidos.cabelos", "envolvidos.olhos",
          "envolvidos.outras_caracteristicas"]]
        .drop_duplicates()
        .rename(columns=lambda c: c.replace("envolvidos.", ""))
        .reset_index(drop=True)
    )

    return df_denuncias, df_orgaos, df_assuntos, df_envolvidos


def _clean(value):
    """Converte NaN/NaT em None para serialização JSON limpa."""
    if value is None:
        return None
    if isinstance(value, float) and np.isnan(value):
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value


def _build_contexto(row, rel_assuntos, rel_orgaos, rel_envolvidos) -> dict:
    logradouro_partes = [_clean(row.get("tipo_logradouro")), _clean(row.get("logradouro"))]
    logradouro = " ".join(p for p in logradouro_partes if p) or None

    return {
        "numero_denuncia": str(row["numero_denuncia"]),
        "data_denuncia": row["data_denuncia"].isoformat() if pd.notna(row.get("data_denuncia")) else None,
        "classificacao_oficial": {
            "classe": _clean(row.get("classe")),
            "tipo": _clean(row.get("tipo")),
            "assunto_principal": bool(row.get("assunto_principal") == 1) if pd.notna(row.get("assunto_principal")) else None,
        },
        "localizacao": {
            "logradouro": logradouro,
            "numero": _clean(row.get("numero_logradouro")),
            "complemento": _clean(row.get("complemento_logradouro")),
            "referencia": _clean(row.get("referencia_logradouro")),
            "bairro": _clean(row.get("bairro_logradouro")),
            "subbairro": _clean(row.get("subbairro_logradouro")),
            "municipio": _clean(row.get("municipio")),
            "estado": _clean(row.get("estado")),
            "latitude": float(row["latitude"]) if pd.notna(row.get("latitude")) else None,
            "longitude": float(row["longitude"]) if pd.notna(row.get("longitude")) else None,
        },
        "assuntos_relacionados": [
            {
                "classe": _clean(r["classe"]),
                "tipo": _clean(r["tipo"]),
                "principal": bool(r["assunto_principal"] == 1) if pd.notna(r["assunto_principal"]) else None,
            }
            for _, r in rel_assuntos.iterrows()
        ],
        "orgaos_notificados": [
            {"nome": _clean(r["orgao_nome"]), "tipo": _clean(r["orgao_tipo"])}
            for _, r in rel_orgaos.iterrows()
        ],
        "envolvidos": [
            {k: _clean(v) for k, v in r.to_dict().items() if k != "numero_denuncia"}
            for _, r in rel_envolvidos.iterrows()
        ],
    }


def build_agent_request(
    numero_denuncia: str,
    csv_path: str | Path = "dados/disk_denuncia.csv",
) -> dict | None:
    """Constrói o payload da Messages API para interpretar um relato.

    O dict devolvido pode ser passado direto:
        client.messages.create(**{k: v for k, v in payload.items() if not k.startswith('_')})
    """
    df_denuncias, df_orgaos, df_assuntos, df_envolvidos = load_dataframes(csv_path)

    den = df_denuncias[df_denuncias["numero_denuncia"] == numero_denuncia]
    if den.empty:
        return None
    row = den.iloc[0]

    rel_assuntos = df_assuntos[df_assuntos["numero_denuncia"] == numero_denuncia]
    rel_orgaos = df_orgaos[df_orgaos["numero_denuncia"] == numero_denuncia]
    rel_envolvidos = df_envolvidos[df_envolvidos["numero_denuncia"] == numero_denuncia]

    contexto = _build_contexto(row, rel_assuntos, rel_orgaos, rel_envolvidos)
    relato = _clean(row.get("relato_redacted")) or ""

    user_message = (
        "RELATO (com PII removida — tokens entre colchetes substituem dados pessoais):\n"
        f'"""\n{relato}\n"""\n\n'
        "CONTEXTO ESTRUTURADO DA DENÚNCIA:\n"
        f"{json.dumps(contexto, ensure_ascii=False, indent=2, default=str)}\n\n"
        "Produza o JSON conforme as instruções do sistema."
    )

    return {
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user_message}],
        "_meta": {
            "numero_denuncia": str(numero_denuncia),
            "relato_length": len(relato),
            "n_assuntos": int(len(rel_assuntos)),
            "n_envolvidos": int(len(rel_envolvidos)),
            "n_orgaos": int(len(rel_orgaos)),
        },
    }


def run_agent(
    numero_denuncia: str,
    csv_path: str | Path = "dados/disk_denuncia.csv",
) -> dict | None:
    """Constrói o payload, chama a Anthropic Messages API e devolve a resposta parseada.

    Requer:
        - pacote `anthropic` instalado (`pip install anthropic`)
        - variável de ambiente ANTHROPIC_API_KEY
    """
    from anthropic import Anthropic

    payload = build_agent_request(numero_denuncia, csv_path=csv_path)
    if payload is None:
        return None

    meta = payload.pop("_meta")
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    response = client.messages.create(**payload)

    text = "".join(block.text for block in response.content if getattr(block, "type", None) == "text")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = {"raw_text": text, "parse_error": True}

    return {
        "meta": meta,
        "model": response.model,
        "usage": {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        },
        "analise": parsed,
    }


if __name__ == "__main__":
    numero = sys.argv[1] if len(sys.argv) > 1 else "1024.6.2020"
    payload = build_agent_request(numero)
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
