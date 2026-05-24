"""Eixo temporal do bingo: perfis hora × modalidade e relevância horária dos fatores.

Resolve a armadilha do briefing ("o furto é às 12h, mas o mapa de iluminação é
problema noturno"): um fator só "explica" o crime nas horas em que AMBOS estão
ativos. `temporal_overlap` mede a fração da atividade criminal que coincide com a
janela de relevância do fator — overlap baixo = fator não é o motivo daquele crime.
"""
from __future__ import annotations

import unicodedata

import pandas as pd

# ── Janelas horárias canônicas ───────────────────────────────────────────────
# Roubo a transeunte/celular no Rio concentra no fim de tarde/noite → 18h conta como noturno.
NIGHT = set(range(18, 24)) | set(range(0, 6))          # 18h–05h
DAY = set(range(6, 18))                                 # 06h–17h
PEAK = {7, 8, 9, 12, 13, 17, 18, 19}                    # picos de fluxo (manhã/almoço/tarde)
ALL_HOURS = set(range(24))


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return s.lower()


# Perfil de relevância temporal por palavra-chave do tipo de fator.
# (label, conjunto de horas em que o fator é plausivelmente um driver de crime)
_FACTOR_RULES: list[tuple[tuple[str, ...], str, set]] = [
    (("mal iluminada", "iluminacao", "iluminação"), "noturno", NIGHT),
    (("vegetacao encobrindo ilumina",), "noturno", NIGHT),
    (("uso de drogas", "drogas"), "noturno/sempre", NIGHT | {14, 15, 16}),
    (("retencao do trafego", "trafego", "transito"), "pico", PEAK),
    (("comercio irregular", "comercio"), "diurno/pico", DAY & (PEAK | set(range(9, 19)))),
    (("estacionamento irregular",), "diurno/pico", PEAK | set(range(9, 19))),
    (("motocicletas", "motos"), "diurno/pico", PEAK | set(range(9, 19))),
    (("veiculos de grande porte",), "diurno", DAY),
    (("vegetacao obstruindo a visibilidade", "visibilidade do passeio"), "diurno", DAY),
    (("calcada estreita",), "sempre", ALL_HOURS),
    (("mobiliario", "mobiliario urbano"), "sempre", ALL_HOURS),
    (("lixo", "entulho"), "sempre", ALL_HOURS),
    (("esconderijo", "vaos", "cavidades"), "sempre", ALL_HOURS),
    (("onibus", "vandalismo"), "sempre", ALL_HOURS),
    (("situacao de rua", "morador"), "social", set()),     # NÃO é driver criminal
    (("praca", "parque"), "contexto", DAY),
]

_DEFAULT_PROFILE = ("sempre", ALL_HOURS)


def factor_time_profile(tipo: str) -> tuple[str, set]:
    """Retorna (rótulo, horas relevantes) para um tipo de fator urbano."""
    t = _norm(tipo)
    for keys, label, hours in _FACTOR_RULES:
        if any(k in t for k in keys):
            return label, hours
    return _DEFAULT_PROFILE


def is_social_factor(tipo: str) -> bool:
    return factor_time_profile(tipo)[0] == "social"


# ── Histogramas de crime ─────────────────────────────────────────────────────
def hour_histogram(*series: pd.Series) -> dict[int, int]:
    """Conta crimes por hora (0–23) combinando várias séries de `hora`."""
    hist = {h: 0 for h in range(24)}
    for s in series:
        if s is None or len(s) == 0:
            continue
        for h, c in s.dropna().astype(int).value_counts().items():
            if 0 <= int(h) <= 23:
                hist[int(h)] += int(c)
    return hist


def dominant_hours(hist: dict[int, int], top: int = 3) -> list[int]:
    nonzero = {h: c for h, c in hist.items() if c > 0}
    if not nonzero:
        return []
    return sorted(sorted(nonzero, key=nonzero.get, reverse=True)[:top])


def window_label(hist: dict[int, int]) -> str:
    """Classifica o perfil temporal dominante do crime."""
    total = sum(hist.values())
    if total == 0:
        return "sem dados"
    night = sum(hist[h] for h in NIGHT) / total
    peak = sum(hist[h] for h in PEAK) / total
    if night >= 0.5:
        return "predominantemente noturno"
    if peak >= 0.5:
        return "concentrado em horários de pico"
    return "predominantemente diurno"


def temporal_overlap(crime_hist: dict[int, int], factor_hours: set) -> float:
    """Fração da atividade criminal que coincide com as horas relevantes do fator (0–1)."""
    total = sum(crime_hist.values())
    if total == 0 or not factor_hours:
        return 0.0
    return round(sum(crime_hist[h] for h in factor_hours if h in crime_hist) / total, 3)


def fmt_hours(hours: list[int]) -> str:
    return ", ".join(f"{h:02d}h" for h in sorted(hours)) if hours else "sem padrão claro"
