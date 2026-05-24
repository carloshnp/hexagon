#!/usr/bin/env python3
"""
Pipeline Completo — Obliteratus + Claude Vision.

Processa evidências visuais com redação de privacidade e prepara payload
para análise via Claude Vision (Anthropic API).

Fluxo:
  1. Carrega imagem → 2. Aplica Obliteratus (blur facial + redação de metadados)
  → 3. Prepara payload para Claude Vision → 4. Retorna resultado estruturado
"""

import base64
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Adiciona o diretório atual para importar obliteratus
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from obliteratus import obliteratus, redacted_image_to_pil, save_redacted_image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("civitas.pipeline")


# ---------------------------------------------------------------------------
# Modelos de Dados
# ---------------------------------------------------------------------------


@dataclass
class PipelineResult:
    """Resultado estruturado do pipeline completo."""

    analise: str = ""
    """Resposta textual da análise (Claude ou fallback)."""

    redacted_image_base64: str = ""
    """Imagem redigida em base64 (PNG)."""

    redacted_metadata: Dict[str, Any] = field(default_factory=dict)
    """Metadados sanitizados (sem PII)."""

    audit_log: List[Dict[str, Any]] = field(default_factory=list)
    """Log de auditoria do Obliteratus."""

    claude_payload: Optional[Dict[str, Any]] = None
    """Payload preparado para Claude Vision (se query fornecida)."""

    error: Optional[str] = None
    """Mensagem de erro, se houver."""

    elapsed_seconds: float = 0.0
    """Tempo total de processamento."""

    success: bool = False
    """Indicador de sucesso."""


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


def process_evidence(
    image_path: str,
    metadata: Optional[Dict[str, Any]] = None,
    query: Optional[str] = None,
    blur_ksize: tuple = (99, 99),
    blur_sigma: float = 30.0,
    save_redacted: Optional[str] = None,
) -> PipelineResult:
    """
    Pipeline completo de processamento de evidência.

    Args:
        image_path: Caminho para a imagem de evidência.
        metadata: Metadados da ocorrência (opcional).
        query: Pergunta textual para Claude Vision (opcional).
        blur_ksize: Kernel do desfoque gaussiano.
        blur_sigma: Sigma do desfoque.
        save_redacted: Caminho opcional para salvar a imagem redigida.

    Returns:
        PipelineResult com análise, imagem redigida e auditoria.
    """
    start = time.time()
    result = PipelineResult()
    metadata = metadata or {}

    try:
        # ── Passo 1: Validar entrada ──
        if not os.path.isfile(image_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {image_path}")

        logger.info("Processando evidência: %s", image_path)
        logger.info("Metadados: %d campos | Query: %s",
                    len(metadata), query[:80] + "..." if query else "N/A")

        # ── Passo 2: Aplicar Obliteratus ──
        logger.info("Aplicando Obliteratus (blur facial + redação de metadados)...")
        ob_result = obliteratus(
            image_path=image_path,
            metadata=metadata,
            blur_ksize=blur_ksize,
            blur_sigma=blur_sigma,
        )

        result.redacted_image_base64 = ob_result["redacted_image"]
        result.redacted_metadata = ob_result["redacted_metadata"]
        result.audit_log = ob_result["audit_log"]

        # Opcional: salvar imagem redigida em disco
        if save_redacted:
            save_redacted_image(ob_result["redacted_image"], save_redacted)

        # ── Passo 3: Preparar payload para Claude Vision ──
        if query:
            result.claude_payload = _build_claude_payload(
                image_base64=ob_result["redacted_image"],
                metadata=ob_result["redacted_metadata"],
                query=query,
            )
            logger.info("Payload Claude Vision preparado (%d caracteres de base64)",
                        len(ob_result["redacted_image"]))

            # ── Passo 4: Análise simulada (fallback) ──
            # Em produção, aqui seria feita a chamada à API Anthropic.
            # Mantemos uma análise simulada para validação do pipeline.
            result.analise = _simulate_analysis(
                query=query,
                metadata=ob_result["redacted_metadata"],
            )
        else:
            result.analise = "Nenhuma query fornecida para análise."
            logger.info("Nenhuma query — apenas redação aplicada.")

        # ── Finalizar ──
        result.elapsed_seconds = round(time.time() - start, 4)
        result.success = True

        logger.info("Pipeline concluído em %.2fs", result.elapsed_seconds)

    except Exception as e:
        result.error = f"[{type(e).__name__}] {str(e)}"
        result.elapsed_seconds = round(time.time() - start, 4)
        logger.error("Pipeline falhou: %s", result.error)

    return result


# ---------------------------------------------------------------------------
# Auxiliares
# ---------------------------------------------------------------------------


def _build_claude_payload(
    image_base64: str,
    metadata: Dict[str, Any],
    query: str,
    system_prompt: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Constrói o payload para a API Claude Vision (messages API).

    O payload segue o formato:
    {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1024,
        "messages": [
            {"role": "user", "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                              "data": "..."}},
                {"type": "text", "text": "..."}
            ]}
        ],
        "system": "..."
    }
    """
    if system_prompt is None:
        system_prompt = (
            "Você é um analista forense do sistema CIVITAS. "
            "A imagem foi redigida pelo sistema Obliteratus para remover PII. "
            "Analise a evidência visual com base nos metadados fornecidos. "
            "Seja objetivo, técnico e cite elementos visuais relevantes. "
            "Nunca peça ou sugira que dados de PII sejam fornecidos."
        )

    # Montar contexto textual com metadados
    meta_lines = "\n".join(f"  - {k}: {v}" for k, v in sorted(metadata.items()))
    text_content = (
        f"[Contexto da Evidência]\n"
        f"Metadados:\n{meta_lines}\n\n"
        f"[Análise Solicitada]\n{query}\n\n"
        f"[Instruções]\n"
        f"Descreva objetivamente o que a imagem mostra. "
        f"Relacione com os metadados fornecidos. "
        f"Não mencione PII (nomes, CPFs, placas)."
    )

    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1024,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_base64,
                        },
                    },
                    {
                        "type": "text",
                        "text": text_content,
                    },
                ],
            }
        ],
        "system": system_prompt,
    }

    return payload


def _simulate_analysis(query: str, metadata: Dict[str, Any]) -> str:
    """Análise simulada para validação do pipeline (sem chamada real à API)."""
    return (
        "--- ANÁLISE SIMULADA (Claude Vision não configurada) ---\n\n"
        f"Query: {query}\n\n"
        "Metadados disponíveis:\n"
        + "\n".join(f"  • {k}: {v}" for k, v in sorted(metadata.items()))
        + "\n\n"
        + "AVALIAÇÃO TÉCNICA:\n"
        + "A imagem foi processada com sucesso pelo sistema Obliteratus. "
        + "A redação facial foi aplicada, removendo qualquer PII visual. "
        + "Os metadados foram sanitizados, mantendo apenas dados de "
        + "localização e classificação do crime.\n"
        + "Para habilitar a análise real, configure a chave ANTHROPIC_API_KEY "
        + "e utilize o payload gerado em 'claude_payload'."
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="CIVITAS Pipeline — Processa evidência com Obliteratus."
    )
    parser.add_argument("image", help="Caminho da imagem de evidência")
    parser.add_argument("--metadata", "-m", default=None,
                        help="Metadados em JSON (string ou arquivo .json)")
    parser.add_argument("--query", "-q", default=None,
                        help="Query para análise")
    parser.add_argument("--output", "-o", default=None,
                        help="Salvar imagem redigida neste caminho")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Log detalhado")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Parse metadata
    meta: Dict[str, Any] = {}
    if args.metadata:
        md_raw = args.metadata
        if os.path.isfile(md_raw):
            with open(md_raw, "r") as f:
                meta = json.load(f)
        else:
            try:
                meta = json.loads(md_raw)
            except json.JSONDecodeError:
                logger.error("Metadados inválidos: %s", md_raw)
                return

    # Executa pipeline
    result = process_evidence(
        image_path=args.image,
        metadata=meta,
        query=args.query,
        save_redacted=args.output,
    )

    # Saída
    print(json.dumps({
        "success": result.success,
        "error": result.error,
        "elapsed_seconds": result.elapsed_seconds,
        "analise": result.analise[:500] + "..." if len(result.analise) > 500 else result.analise,
        "redacted_metadata": result.redacted_metadata,
        "audit_summary": [
            e["evento"] for e in result.audit_log
        ],
        "has_claude_payload": result.claude_payload is not None,
        "redacted_image_length": len(result.redacted_image_base64),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
