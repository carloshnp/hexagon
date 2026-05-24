"""Exporta os dados processados em `exports/`:

  - relints.json                          : agências + RELINTs estruturados
  - areas_detalhadas.csv                  : denormalizado (1 linha por agência × sub-área)
  - spatial_priority_areas.json           : pipeline completo, todo o histórico
  - spatial_priority_areas_{1,3,7}d.json  : mesmo pipeline com janela de N dias
  - spatial_top_areas.csv                 : ranking global + por instituição, denormalizado

Tudo aqui é consumível direto pelo front-end (drop em CDN, abrir no Power BI,
ou carregar como fixture nos testes).
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Optional

from .agency_areas import agencies_full_index
from .pipeline import _clean_for_json, run_pipeline
from .relints_parser import FATORES, parse_all_relints

EXPORT_DIR = Path(__file__).parent / "exports"
DAY_WINDOWS = [1, 3, 7]
SPATIAL_TOP_N = 10

# ─── RELINTs / Agências ────────────────────────────────────────────────────

CSV_COLUMNS = [
    "fid", "nome_area", "area_km2", "perimetro_m",
    "centroide_lat", "centroide_lon",
    "bbox_min_lat", "bbox_min_lon", "bbox_max_lat", "bbox_max_lon",
    "codigo_relint", "titulo_relint", "match_score",
    "subarea_idx", "subarea_nome", "subarea_descricao",
    "retencao_fluxo", "baixa_visibilidade", "obstaculos_urbanos",
    "motos_bicicletas", "rotas_dispersao",
    "subarea_fechamento", "conclusao_necessidades",
]


def export_relints_json(out_path: Path) -> int:
    index = agencies_full_index()
    payload = {
        "agencias": list(index.values()),
        "relints": list(parse_all_relints()),
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(payload["agencias"])


def export_relints_csv(out_path: Path) -> int:
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


# ─── Spatial pipeline (MCDA) ───────────────────────────────────────────────

SPATIAL_CSV_COLUMNS = [
    "janela_dias",          # "" | "1" | "3" | "7"
    "ranking_tipo",         # "geral" | "PM-RJ" | "GM-Rio" | ...
    "instituicao",          # texto longo, vazio se ranking_tipo=geral
    "pos",                  # 1..N
    "h3_cell",
    "lat", "lon",
    "score",
    "cnt_ocorrencias", "cnt_denuncias", "cnt_fatores", "cnt_cameras",
]


def _spatial_rows_from(result: dict, days_label: str):
    """Itera (janela, ranking_tipo, pos, ...) para o CSV."""
    for pos, area in enumerate(result["score_geral"]["top_areas"], start=1):
        yield {
            "janela_dias": days_label,
            "ranking_tipo": "geral",
            "instituicao": "",
            "pos": pos,
            "h3_cell": area["h3_cell"],
            "lat": area["lat"],
            "lon": area["lon"],
            "score": area["score"],
            "cnt_ocorrencias": area["cnt_ocorrencias"],
            "cnt_denuncias":   area["cnt_denuncias"],
            "cnt_fatores":     area["cnt_fatores"],
            "cnt_cameras":     area["cnt_cameras"],
        }
    for inst_id, inst in result["scores_por_instituicao"].items():
        for pos, area in enumerate(inst["top_areas"], start=1):
            yield {
                "janela_dias": days_label,
                "ranking_tipo": inst_id,
                "instituicao": inst["instituicao"],
                "pos": pos,
                "h3_cell": area["h3_cell"],
                "lat": area["lat"],
                "lon": area["lon"],
                "score": area["score"],
                # nomes abreviados → mapeia para colunas canônicas do CSV
                "cnt_ocorrencias": area["cnt_ocorr"],
                "cnt_denuncias":   area["cnt_den"],
                "cnt_fatores":     area["cnt_fat"],
                "cnt_cameras":     area["cnt_cameras"],
            }


def export_spatial(out_dir: Path, top_n: int = SPATIAL_TOP_N) -> dict:
    """Roda o pipeline pra cada janela e escreve 4 JSONs + 1 CSV consolidado."""
    files = []
    csv_path = out_dir / "spatial_top_areas.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=SPATIAL_CSV_COLUMNS)
        w.writeheader()

        for days in [None, *DAY_WINDOWS]:
            label = "" if days is None else str(days)
            tag   = "" if days is None else f"_{days}d"
            result = run_pipeline(top_n=top_n, days=days, verbose=False)
            clean = _clean_for_json(result)
            out_json = out_dir / f"spatial_priority_areas{tag}.json"
            out_json.write_text(json.dumps(clean, ensure_ascii=False, indent=2), encoding="utf-8")
            files.append({
                "file": out_json.name,
                "janela_dias": days,
                "n_ocorrencias_usadas": clean["n_ocorrencias_usadas"],
                "n_denuncias_usadas":   clean["n_denuncias_usadas"],
                "elapsed_s": clean["elapsed_seconds"],
            })
            for row in _spatial_rows_from(clean, label):
                w.writerow(row)

    return {"csv": str(csv_path), "json_files": files}


# ─── Orquestração ──────────────────────────────────────────────────────────

def export_all(export_dir: Path = EXPORT_DIR, with_spatial: bool = True) -> dict:
    export_dir.mkdir(parents=True, exist_ok=True)

    relints_json = export_dir / "relints.json"
    relints_csv  = export_dir / "areas_detalhadas.csv"
    n_ag    = export_relints_json(relints_json)
    n_rows  = export_relints_csv(relints_csv)

    out = {
        "relints_json": str(relints_json),
        "relints_csv":  str(relints_csv),
        "n_agencias":   n_ag,
        "n_csv_rows":   n_rows,
    }
    if with_spatial:
        spatial = export_spatial(export_dir)
        out["spatial_csv"]   = spatial["csv"]
        out["spatial_files"] = spatial["json_files"]
    return out


if __name__ == "__main__":
    import sys
    with_spatial = "--no-spatial" not in sys.argv
    info = export_all(with_spatial=with_spatial)
    print(json.dumps(info, ensure_ascii=False, indent=2))
