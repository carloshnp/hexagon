"""Cache em memória para saídas caras (relatórios LLM lazy).

Simples e por processo — suficiente para a reunião/demonstração. Chave textual
que inclui região + janela + modo, para não misturar recortes.
"""
from __future__ import annotations

from typing import Any, Callable

_STORE: dict[str, Any] = {}


def make_key(*parts: Any) -> str:
    return "|".join(str(p) for p in parts)


def get(key: str) -> Any | None:
    return _STORE.get(key)


def set(key: str, value: Any) -> Any:
    _STORE[key] = value
    return value


def get_or_compute(key: str, compute: Callable[[], Any]) -> tuple[Any, bool]:
    """Retorna (valor, cached?). Computa e armazena se ausente."""
    if key in _STORE:
        return _STORE[key], True
    value = compute()
    _STORE[key] = value
    return value, False


def clear() -> None:
    _STORE.clear()
