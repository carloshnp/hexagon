"""Configuração central da frente Lucas: paths, modo de dados (híbrido) e env.

Detecção de modo:
- `live`   → o submódulo `claude_impact_lab_compstat_rio/dados` existe localmente;
             usamos os CSVs brutos via os loaders do Perri (spatial join real).
- `static` → submódulo ausente; caímos para os exports estáticos do Perri
             (`exports/relints.json`, `spatial_priority_areas*.json`) + o
             `disk_denuncia.csv` do Arick (que está sempre presente no repo).
"""
from __future__ import annotations

import os
from pathlib import Path

# ── Paths ───────────────────────────────────────────────────────────────────
COMPSTAT_DIR = Path(__file__).resolve().parent
LUCAS_DIR = COMPSTAT_DIR.parent
BACKEND_DIR = LUCAS_DIR.parent

PERRI_DIR = BACKEND_DIR / "perri"
HEXAGON_SPATIAL_DIR = PERRI_DIR / "hexagon_spatial"
EXPORTS_DIR = HEXAGON_SPATIAL_DIR / "exports"
SUBMODULE_DIR = HEXAGON_SPATIAL_DIR / "claude_impact_lab_compstat_rio"
DADOS_DIR = SUBMODULE_DIR / "dados"

ARICK_DIR = BACKEND_DIR / "Arick"
DISK_DENUNCIA_CSV = ARICK_DIR / "disk_denuncia.csv"

# Exports estáticos do Perri
RELINTS_JSON = EXPORTS_DIR / "relints.json"
SPATIAL_JSON = {
    None: EXPORTS_DIR / "spatial_priority_areas.json",
    1: EXPORTS_DIR / "spatial_priority_areas_1d.json",
    3: EXPORTS_DIR / "spatial_priority_areas_3d.json",
    7: EXPORTS_DIR / "spatial_priority_areas_7d.json",
}

# ── Modo de dados ────────────────────────────────────────────────────────────
def detect_mode() -> str:
    """`live` se o submódulo de dados existir, senão `static`."""
    if DADOS_DIR.exists() and any(DADOS_DIR.glob("df_ocorrencias_tratado*.csv")):
        return "live"
    return "static"


DATA_MODE = os.getenv("LUCAS_DATA_MODE", detect_mode())

# ── Mapeamento region_id ↔ fid ───────────────────────────────────────────────
def fid_to_region_id(fid: int) -> str:
    return f"regiao_{int(fid):03d}"


def region_id_to_fid(region_id: str) -> int | None:
    try:
        return int(str(region_id).split("_")[-1])
    except (ValueError, IndexError):
        return None


# ── Score: limiares de nível de risco ────────────────────────────────────────
RISK_LEVEL_THRESHOLDS = {"high": 66.0, "medium": 33.0}  # senão: low


def risk_level(score: float) -> str:
    if score >= RISK_LEVEL_THRESHOLDS["high"]:
        return "high"
    if score >= RISK_LEVEL_THRESHOLDS["medium"]:
        return "medium"
    return "low"


# ── Recortes temporais ───────────────────────────────────────────────────────
DEFAULT_TIME_WINDOW = "last_30_days"
TIME_WINDOW_DAYS = {
    "last_30_days": 30,
    "last_7_days": 7,
    "1d": 1,
    "3d": 3,
    "7d": 7,
    "all": None,
}


def window_to_days(preset: str | None) -> int | None:
    if not preset:
        return TIME_WINDOW_DAYS[DEFAULT_TIME_WINDOW]
    return TIME_WINDOW_DAYS.get(preset, TIME_WINDOW_DAYS[DEFAULT_TIME_WINDOW])


# ── LLM ───────────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
LLM_MAX_TOKENS = int(os.getenv("LUCAS_LLM_MAX_TOKENS", "4096"))


def llm_available() -> bool:
    return bool(ANTHROPIC_API_KEY)
