"""
score_service.py

Calcula um score de prioridade/risco para cada denúncia do disk-denúncia e
devolve o resultado em JSON, pronto para ser consumido por um backend HTTP.

Uso programático:
    from backend.score_service import score_denuncia, score_lote
    payload = score_denuncia('1024.6.2020', csv_path='dados/disk_denuncia.csv')

Uso CLI:
    python backend/score_service.py 1024.6.2020
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


SEVERITY_WEIGHTS: dict[str, float] = {
    "ARMAS DE FOGO E ARTEFATOS EXPLOSIVOS": 1.00,
    "CRIMES CONTRA A PESSOA": 0.95,
    "CRIMES CONTRA CRIANÇA E O ADOLESCENTE": 0.90,
    "CRIMES CONTRA A LIBERDADE INDIVIDUAL": 0.85,
    "SUBSTÂNCIAS ENTORPECENTES": 0.70,
    "CRIMES CONTRA O PATRIMÔNIO": 0.65,
    "CRIMES CONTRA A FÉ PÚBLICA": 0.45,
    "CRIMES CONTRA A ADMINISTRAÇÃO PÚBLICA": 0.40,
    "PERTURBAÇÃO DA ORDEM PÚBLICA": 0.30,
    "CRIMES AMBIENTAIS": 0.30,
}
DEFAULT_SEVERITY = 0.50


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
        "bairro_logradouro", "subbairro_logradouro", "municipio", "estado",
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
    df_denuncias["assunto_principal"] = (
        pd.to_numeric(df_denuncias["assunto_principal"], errors="coerce").astype("Int64")
    )

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
          "envolvidos.idade", "envolvidos.pele"]]
        .drop_duplicates()
        .rename(columns=lambda c: c.replace("envolvidos.", ""))
        .reset_index(drop=True)
    )

    return df_denuncias, df_orgaos, df_assuntos, df_envolvidos


def _classe_severity(classe) -> float:
    if classe is None or (isinstance(classe, float) and np.isnan(classe)):
        return DEFAULT_SEVERITY
    return SEVERITY_WEIGHTS.get(str(classe).strip().upper(), DEFAULT_SEVERITY)


def _risk_level(score: float) -> str:
    if score >= 0.85:
        return "CRITICO"
    if score >= 0.65:
        return "ALTO"
    if score >= 0.45:
        return "MEDIO"
    return "BAIXO"


def _safe(value):
    if isinstance(value, float) and np.isnan(value):
        return None
    if value is pd.NaT or (hasattr(pd, "isna") and not isinstance(value, (str, bytes)) and pd.isna(value)):
        return None
    return value


def compute_score(
    numero_denuncia: str,
    df_denuncias: pd.DataFrame,
    df_orgaos: pd.DataFrame,
    df_assuntos: pd.DataFrame,
    df_envolvidos: pd.DataFrame,
) -> dict | None:
    den = df_denuncias[df_denuncias["numero_denuncia"] == numero_denuncia]
    if den.empty:
        return None
    row = den.iloc[0]

    rel_assuntos = df_assuntos[df_assuntos["numero_denuncia"] == numero_denuncia]
    rel_orgaos = df_orgaos[df_orgaos["numero_denuncia"] == numero_denuncia]
    rel_envolvidos = df_envolvidos[df_envolvidos["numero_denuncia"] == numero_denuncia]

    severities = (
        [_classe_severity(c) for c in rel_assuntos["classe"].tolist()]
        or [_classe_severity(row.get("classe"))]
    )
    base_severity = max(severities)

    multi_crime_bonus = min(0.15, 0.05 * max(0, len(rel_assuntos) - 1))
    envolvidos_factor = min(0.15, 0.05 * len(rel_envolvidos))
    orgaos_factor = min(0.10, 0.02 * len(rel_orgaos))
    assunto_principal_boost = (
        0.10 if pd.notna(row.get("assunto_principal")) and int(row["assunto_principal"]) == 1 else 0.0
    )

    score = base_severity + multi_crime_bonus + envolvidos_factor + orgaos_factor + assunto_principal_boost
    score = round(min(1.0, score), 4)

    return {
        "numero_denuncia": str(numero_denuncia),
        "score": score,
        "risk_level": _risk_level(score),
        "breakdown": {
            "base_severity": round(base_severity, 4),
            "multi_crime_bonus": round(multi_crime_bonus, 4),
            "envolvidos_factor": round(envolvidos_factor, 4),
            "orgaos_factor": round(orgaos_factor, 4),
            "assunto_principal_boost": round(assunto_principal_boost, 4),
        },
        "context": {
            "classe_principal": _safe(row.get("classe")),
            "tipo_principal": _safe(row.get("tipo")),
            "data_denuncia": row["data_denuncia"].isoformat() if pd.notna(row.get("data_denuncia")) else None,
            "bairro": _safe(row.get("bairro_logradouro")),
            "municipio": _safe(row.get("municipio")),
            "estado": _safe(row.get("estado")),
            "latitude": float(row["latitude"]) if pd.notna(row.get("latitude")) else None,
            "longitude": float(row["longitude"]) if pd.notna(row.get("longitude")) else None,
            "n_assuntos": int(len(rel_assuntos)),
            "n_envolvidos": int(len(rel_envolvidos)),
            "n_orgaos": int(len(rel_orgaos)),
        },
    }


def score_denuncia(numero_denuncia: str, csv_path: str | Path = "dados/disk_denuncia.csv") -> str:
    """Endpoint-style: recebe um numero_denuncia, devolve string JSON."""
    dfs = load_dataframes(csv_path)
    result = compute_score(numero_denuncia, *dfs)
    return json.dumps(result, ensure_ascii=False, default=str)


def score_lote(
    numeros: Iterable[str] | None = None,
    csv_path: str | Path = "dados/disk_denuncia.csv",
    top_n: int | None = None,
) -> str:
    """Endpoint-style: devolve JSON com a lista ordenada de scores.

    Se `numeros` é None, calcula para todas as denúncias.
    Se `top_n` é dado, devolve só as N denúncias com maior score.
    """
    df_denuncias, df_orgaos, df_assuntos, df_envolvidos = load_dataframes(csv_path)

    if numeros is None:
        numeros = df_denuncias["numero_denuncia"].tolist()

    results = []
    for nd in numeros:
        r = compute_score(nd, df_denuncias, df_orgaos, df_assuntos, df_envolvidos)
        if r is not None:
            results.append(r)

    results.sort(key=lambda r: r["score"], reverse=True)
    if top_n is not None:
        results = results[:top_n]

    payload = {
        "total": len(results),
        "items": results,
    }
    return json.dumps(payload, ensure_ascii=False, default=str)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(score_denuncia(sys.argv[1]))
    else:
        print(score_lote(top_n=10))
