"""Parser dos Relatórios de Inteligência (RELINTs) em .docx.

Extrai, para cada RI, parâmetros estruturados que se repetem em todo relatório:
título, sub-locais, descrição, e os 5 fatores de vulnerabilidade urbana com
seu contexto, mais o bloco de conclusão com as necessidades de ação.

Não depende de python-docx — usa apenas zipfile + regex sobre o XML.
"""
from __future__ import annotations

import re
import zipfile
from functools import lru_cache
from pathlib import Path
from typing import Optional

RELINTS_DIR = Path(__file__).parent / "claude_impact_lab_compstat_rio" / "relints"

# Os 5 fatores padronizados que aparecem em toda sub-área.
FATORES = [
    "retencao_fluxo",
    "baixa_visibilidade",
    "obstaculos_urbanos",
    "motos_bicicletas",
    "rotas_dispersao",
]

FATOR_LABELS = {
    "retencao_fluxo":     "Retenção de fluxo em horários de pico",
    "baixa_visibilidade": "Áreas com baixa visibilidade",
    "obstaculos_urbanos": "Obstáculos urbanos dificultando vigilância",
    "motos_bicicletas":   "Circulação intensa de motocicletas e bicicletas",
    "rotas_dispersao":    "Múltiplas rotas de dispersão após a prática criminosa",
}

FATOR_PATTERNS = {
    "retencao_fluxo":     r"retenção de fluxo em horários de pico",
    "baixa_visibilidade": r"áreas com baixa visibilidade",
    "obstaculos_urbanos": r"obstáculos urbanos dificultando vigilância",
    "motos_bicicletas":   r"circulação intensa de motocicletas e bicicletas",
    "rotas_dispersao":    r"múltiplas rotas de dispersão após a prática criminosa",
}

def _is_boilerplate_head(p: str) -> bool:
    """Cabeçalhos institucionais que não são título de área."""
    up = p.upper()
    if up == "CONCLUSÃO":
        return True
    return "RELATÓRIO" in up and ("INTELIGÊNCIA" in up or "COMPSTAT" in up)

_CODE_RE = re.compile(r"RI_(\d+)_(\d+)")


def _read_paragraphs(fp: Path) -> list[str]:
    """Lê um .docx e devolve a lista de parágrafos (texto plano)."""
    with zipfile.ZipFile(fp) as z:
        with z.open("word/document.xml") as f:
            xml = f.read().decode("utf-8")

    paragraphs: list[str] = []
    for m in re.finditer(r"<w:p\b[^>]*>(.*?)</w:p>", xml, re.DOTALL):
        text = re.sub(r"<[^>]+>", "", m.group(1))
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            paragraphs.append(text)
    return paragraphs


def _is_caps_heading(p: str) -> bool:
    """Detecta um cabeçalho em caixa-alta (curto, sem pontuação de frase)."""
    if not p or len(p) > 120:
        return False
    letters = [c for c in p if c.isalpha()]
    if not letters:
        return False
    if not all(c.isupper() for c in letters):
        return False
    if "." in p:  # cabeçalhos não terminam em ponto
        return False
    return True


def _extract_fatores(bullets: list[str]) -> dict[str, Optional[str]]:
    """Mapeia cada um dos 5 fatores ao seu contexto (texto após o travessão)."""
    out: dict[str, Optional[str]] = {f: None for f in FATORES}
    for b in bullets:
        b = b.lstrip("•").strip()
        for key, prefix in FATOR_PATTERNS.items():
            m = re.match(prefix + r"\s+[—–-]\s+(.+)", b, re.IGNORECASE)
            if m:
                out[key] = m.group(1).strip().rstrip(".;,")
                break
    return out


def _bullets_from(p: str) -> list[str]:
    """Quebra um parágrafo em bullets quando vêm concatenados ('• a; • b;')."""
    parts = re.split(r"\s*•\s*", p)
    return [x.strip().rstrip(".;") for x in parts if x.strip()]


def parse_relint(fp: Path) -> dict:
    """Parseia um RELINT (.docx) em dict estruturado."""
    paragraphs = _read_paragraphs(fp)

    codigo_m = _CODE_RE.search(fp.name)
    codigo = f"RI_{codigo_m.group(1)}_{codigo_m.group(2)}" if codigo_m else fp.stem

    # 1. Localiza o título: 1º heading CAPS que NÃO é boilerplate institucional.
    titulo = ""
    title_idx = -1
    for i, p in enumerate(paragraphs):
        if _is_caps_heading(p) and not _is_boilerplate_head(p):
            titulo = p
            title_idx = i
            break

    # 2. Localiza o índice da CONCLUSÃO.
    conc_idx = next(
        (i for i, p in enumerate(paragraphs) if p.strip() == "CONCLUSÃO"),
        len(paragraphs),
    )

    # 3. Itera entre title_idx+1 e conc_idx, agrupando sub-áreas.
    #    Texto que aparecer ANTES do primeiro sub-heading é a introdução do relatório.
    introducao_paragrafos: list[str] = []
    subareas: list[dict] = []
    cur: Optional[dict] = None
    i = title_idx + 1 if title_idx >= 0 else 0
    while i < conc_idx:
        p = paragraphs[i]
        if _is_caps_heading(p) and not _is_boilerplate_head(p):
            if cur:
                subareas.append(cur)
            cur = {
                "nome": p,
                "descricao_paragrafos": [],
                "bullets": [],
                "fechamento": "",
            }
        elif cur is None:
            introducao_paragrafos.append(p)
        elif p.startswith("Também foram identificados"):
            pass
        elif p.startswith("•"):
            cur["bullets"].extend(_bullets_from(p))
        elif p.startswith("A dinâmica criminal observada"):
            cur["fechamento"] = p
        else:
            cur["descricao_paragrafos"].append(p)
        i += 1

    if cur:
        subareas.append(cur)

    # Caso degenerado: relatório de área única sem sub-headings (não observado, mas defensivo).
    if not subareas and introducao_paragrafos:
        subareas.append({
            "nome": titulo or "ÁREA",
            "descricao_paragrafos": introducao_paragrafos,
            "bullets": [],
            "fechamento": "",
        })
        introducao_paragrafos = []

    # 4. Conclusão: descricao narrativa + bullets de "necessidade de:"
    conclusao_desc: list[str] = []
    necessidades: list[str] = []
    fechamento_geral = ""
    in_necessidades = False
    for p in paragraphs[conc_idx + 1:]:
        if p.startswith("•"):
            in_necessidades = True
            necessidades.extend(_bullets_from(p))
            continue
        if in_necessidades and p.startswith("Os delitos tendem"):
            fechamento_geral = p
            continue
        # Texto introdutório da conclusão (antes dos bullets)
        if not in_necessidades:
            # cortar trailing "Observa-se necessidade de:"
            txt = re.sub(r"\s*Observa-se necessidade de:\s*$", "", p).strip()
            if txt:
                conclusao_desc.append(txt)

    # 5. Estrutura cada sub-área no formato final
    out_subareas = []
    for s in subareas:
        out_subareas.append({
            "nome": s["nome"],
            "descricao": " ".join(s["descricao_paragrafos"]),
            "fatores": _extract_fatores(s["bullets"]),
            "fechamento": s["fechamento"],
        })

    return {
        "codigo": codigo,
        "arquivo": fp.name,
        "titulo": titulo,
        "introducao": " ".join(introducao_paragrafos),
        "n_subareas": len(out_subareas),
        "subareas": out_subareas,
        "conclusao": {
            "texto": " ".join(conclusao_desc),
            "necessidades": necessidades,
            "fechamento": fechamento_geral,
        },
    }


@lru_cache(maxsize=1)
def parse_all_relints(directory: Optional[str] = None) -> tuple[dict, ...]:
    dir_path = Path(directory) if directory else RELINTS_DIR
    files = sorted(dir_path.glob("*.docx"))
    relints = sorted((parse_relint(fp) for fp in files), key=lambda r: r["codigo"])
    return tuple(relints)


if __name__ == "__main__":
    import json, sys
    rel = parse_all_relints()
    print(f"Parseados {len(rel)} RELINTs")
    for r in rel:
        n_fat = sum(1 for s in r["subareas"] for v in s["fatores"].values() if v)
        total = len(r["subareas"]) * 5
        print(f"  {r['codigo']:12s} sub={r['n_subareas']}  fatores={n_fat}/{total}  "
              f"necessidades={len(r['conclusao']['necessidades']):2d}  "
              f"título='{r['titulo'][:55]}'")
    if "--json" in sys.argv:
        print(json.dumps(rel, ensure_ascii=False, indent=2))
