"""Abstração de provider LLM com fallback determinístico.

Contrato: todo agente calcula um `fallback` determinístico a partir dos dados e
chama o provider. Com `ANTHROPIC_API_KEY`, o `AnthropicProvider` enriquece/produz
a narrativa via tool-use (saída estruturada garantida) e usa prompt caching no
bloco de contexto pesado. Sem chave, o `FakeProvider` devolve o fallback. Assim os
endpoints SEMPRE retornam JSON válido — a LLM é aditiva, nunca um ponto de falha.
"""
from __future__ import annotations

import json
from typing import Any

from .. import config


class LLMProvider:
    mode = "fake"

    def generate_structured(self, *, system: str, context: str, task: str,
                            schema: dict, fallback: dict) -> dict:
        raise NotImplementedError

    def generate_text(self, *, system: str, context: str, task: str,
                      fallback: str) -> str:
        raise NotImplementedError


class FakeProvider(LLMProvider):
    """Sem LLM: devolve o fallback determinístico construído pelo agente."""

    mode = "fake"

    def generate_structured(self, *, system, context, task, schema, fallback):
        return fallback

    def generate_text(self, *, system, context, task, fallback):
        return fallback


class AnthropicProvider(LLMProvider):
    mode = "anthropic"

    def __init__(self):
        import anthropic  # import tardio: só quando há chave

        self._client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        self._model = config.ANTHROPIC_MODEL
        self._max_tokens = config.LLM_MAX_TOKENS

    def _system_blocks(self, system: str, context: str) -> list[dict]:
        # contexto pesado marcado para prompt caching (TTL ~5 min)
        return [
            {"type": "text", "text": system},
            {"type": "text", "text": context,
             "cache_control": {"type": "ephemeral"}},
        ]

    def generate_structured(self, *, system, context, task, schema, fallback):
        try:
            resp = self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                system=self._system_blocks(system, context),
                tools=[{
                    "name": "emit_report",
                    "description": "Emite o relatório estruturado conforme o schema.",
                    "input_schema": schema,
                }],
                tool_choice={"type": "tool", "name": "emit_report"},
                messages=[{"role": "user", "content": task}],
            )
            for block in resp.content:
                if getattr(block, "type", None) == "tool_use":
                    return block.input  # type: ignore[attr-defined]
            return fallback
        except Exception:
            return fallback

    def generate_text(self, *, system, context, task, fallback):
        try:
            resp = self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                system=self._system_blocks(system, context),
                messages=[{"role": "user", "content": task}],
            )
            parts = [b.text for b in resp.content if getattr(b, "type", None) == "text"]
            return "\n".join(parts).strip() or fallback
        except Exception:
            return fallback


_provider: LLMProvider | None = None


def get_provider() -> LLMProvider:
    """Factory cacheada: Anthropic se houver chave, senão Fake."""
    global _provider
    if _provider is None:
        _provider = AnthropicProvider() if config.llm_available() else FakeProvider()
    return _provider


def reset_provider() -> None:
    global _provider
    _provider = None


def json_block(data: Any) -> str:
    """Serializa dados para um bloco de contexto legível pela LLM."""
    return json.dumps(data, ensure_ascii=False, indent=2, default=str)
