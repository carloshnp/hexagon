"""Exporta as agências + RELINTs em formato tabular (CSV) e JSON canônico.

Gera dois arquivos em `exports/`:
  - relints.json           : JSON estruturado completo (igual à resposta de /relints/)
  - areas_detalhadas.csv   : denormalizado (1 linha por agência × sub-área)

O CSV é o formato de consumo direto para o front-end / planilha.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from .agency_areas import agencies_full_index
from .relints_parser import FATORES, parse_all_relints

EXPORT_DIR = Path(__file__).parent / "exports"

CSV_COLUMNS = [
    # Identificação da agência (área da Força Municipal)
    "fid",
    "nome_area",
    "area_km2",
    "perimetro_m",
    "centroide_lat",
    "centroide_lon",
    "bbox_min_lat",
    "bbox_min_lon",
    "bbox_max_lat",
    "bbox_max_lon",
    # RELINT vinculado
    "codigo_relint",
    "titulo_relint",
    "match_score",
    # Sub-área
    "subarea_idx",
    "subarea_nome",
    "subarea_descricao",
    # Os 5 fatores padronizados
    "retencao_fluxo",
    "baixa_visibilidade",
    "obstaculos_urbanos",
    "motos_bicicletas",
    "rotas_dispersao",
    # Contexto extra
    "subarea_fechamento",
    "conclusao_necessidades",  # join '|'
]


def export_json(out_path: Path) -> int:
    """Escreve o JSON estruturado completo de todas as agências e RELINTs."""
    index = agencies_full_index()
    payload = {
        "agencias": list(index.values()),
        "relints": list(parse_all_relints()),
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(payload["agencias"])


def export_csv(out_path: Path) -> int:
    """Escreve uma linha por (agência × sub-área) no CSV denormalizado."""
    index = agencies_full_index()
    n_rows = 0
    with out_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        w.writeheader()
        for fid in sorted(index.keys()):
            ag = index[fid]
            relint = ag.get("relint") or {}
            necessidades = "|".join(relint.get("conclusao", {}).get("necessidades", []))

            subareas = relint.get("subareas") or [{
                "nome": "", "descricao": "", "fatores": {f: None for f in FATORES}, "fechamento": "",
            }]
            for idx, sub in enumerate(subareas):
                fatores = sub.get("fatores", {})
                w.writerow({
                    "fid": ag["fid"],
                    "nome_area": ag["nome_area"],
                    "area_km2": ag["area_km2"],
                    "perimetro_m": ag["perimetro_m"],
                    "centroide_lat": ag["centroide"]["lat"],
                    "centroide_lon": ag["centroide"]["lon"],
                    "bbox_min_lat": ag["bbox"]["min_lat"],
                    "bbox_min_lon": ag["bbox"]["min_lon"],
                    "bbox_max_lat": ag["bbox"]["max_lat"],
                    "bbox_max_lon": ag["bbox"]["max_lon"],
                    "codigo_relint": relint.get("codigo", ""),
                    "titulo_relint": relint.get("titulo", ""),
                    "match_score": (ag.get("relint_match") or {}).get("score", 0),
                    "subarea_idx": idx,
                    "subarea_nome": sub.get("nome", ""),
                    "subarea_descricao": sub.get("descricao", ""),
                    "retencao_fluxo":     fatores.get("retencao_fluxo")     or "",
                    "baixa_visibilidade": fatores.get("baixa_visibilidade") or "",
                    "obstaculos_urbanos": fatores.get("obstaculos_urbanos") or "",
                    "motos_bicicletas":   fatores.get("motos_bicicletas")   or "",
                    "rotas_dispersao":    fatores.get("rotas_dispersao")    or "",
                    "subarea_fechamento": sub.get("fechamento", ""),
                    "conclusao_necessidades": necessidades,
                })
                n_rows += 1
    return n_rows


def export_all(export_dir: Path = EXPORT_DIR) -> dict:
    export_dir.mkdir(parents=True, exist_ok=True)
    json_path = export_dir / "relints.json"
    csv_path  = export_dir / "areas_detalhadas.csv"
    n_ag = export_json(json_path)
    n_rows = export_csv(csv_path)
    return {
        "json_path": str(json_path),
        "csv_path":  str(csv_path),
        "n_agencias": n_ag,
        "n_csv_rows": n_rows,
    }


if __name__ == "__main__":
    info = export_all()
    print(json.dumps(info, ensure_ascii=False, indent=2))
