#!/usr/bin/env python3
"""
Data Pipeline — Parse ISP RJ crime data and produce clean dataset.

Functions:
    load_real_data(path="/tmp/isp_data.csv") -> list[dict]
    aggregate_by_region(records, crime_type, year) -> dict
"""

import csv
import json
from pathlib import Path

# ── Known numeric (crime type / count) columns ──────────────────────────────
NUMERIC_FIELDS = {
    "hom_doloso", "lesao_corp_morte", "latrocinio", "cvli",
    "hom_por_interv_policial", "feminicidio", "letalidade_violenta",
    "tentat_hom", "tentativa_feminicidio", "lesao_corp_dolosa",
    "estupro", "hom_culposo", "lesao_corp_culposa",
    "roubo_transeunte", "roubo_celular", "roubo_em_coletivo",
    "roubo_rua", "roubo_veiculo", "roubo_carga", "roubo_comercio",
    "roubo_residencia", "roubo_banco", "roubo_cx_eletronico",
    "roubo_conducao_saque", "roubo_apos_saque", "roubo_bicicleta",
    "outros_roubos", "total_roubos",
    "furto_veiculos", "furto_transeunte", "furto_coletivo",
    "furto_celular", "furto_bicicleta", "outros_furtos",
    "total_furtos",
    "sequestro", "extorsao", "sequestro_relampago",
    "estelionato", "apreensao_drogas", "posse_drogas",
    "trafico_drogas", "apreensao_drogas_sem_autor",
    "recuperacao_veiculos", "apf", "aaapai", "cmp", "cmba",
    "ameaca", "pessoas_desaparecidas", "encontro_cadaver",
    "encontro_ossada", "pol_militares_mortos_serv",
    "pol_civis_mortos_serv", "registro_ocorrencias",
}


def _safe_int(val):
    """Convert a value to int, returning 0 for empty/missing values."""
    if val is None:
        return 0
    val = val.strip()
    if val == "":
        return 0
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


def load_real_data(path="/tmp/isp_data.csv") -> list[dict]:
    """
    Parse ISP RJ CSV, filter to Rio de Janeiro capital, 2024-2026 only.
    
    Returns a list of flat dict records with all crime type fields as integers.
    """
    csv_path = Path(path).resolve()
    if not csv_path.exists():
        raise FileNotFoundError(f"ISP data not found: {csv_path}")

    records = []

    with open(csv_path, encoding="latin-1", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        # Strip whitespace from fieldnames (the CSV may have \r chars)
        reader.fieldnames = [fn.strip() for fn in reader.fieldnames]

        for row in reader:
            # Strip values
            row = {k.strip(): v.strip() if v else "" for k, v in row.items()}

            mun = row.get("munic", "")
            if mun != "Rio de Janeiro":
                continue

            # Filter 2024-2026
            try:
                ano = int(row.get("ano", 0))
            except (ValueError, TypeError):
                continue
            if ano < 2024 or ano > 2026:
                continue

            # Build flat record
            record = {
                "cisp": _safe_int(row.get("cisp")),
                "mes": _safe_int(row.get("mes")),
                "ano": ano,
                "mes_ano": row.get("mes_ano", ""),
                "aisp": _safe_int(row.get("aisp")),
                "risp": _safe_int(row.get("risp")),
                "munic": row.get("munic", ""),
                "mcirc": _safe_int(row.get("mcirc")),
                "regiao": row.get("regiao", ""),
                "fase": _safe_int(row.get("fase")),
            }

            # Add all numeric crime fields
            for field_name in NUMERIC_FIELDS:
                record[field_name] = _safe_int(row.get(field_name))

            records.append(record)

    return records


def aggregate_by_region(records: list[dict], crime_type: str, year: int) -> dict:
    """
    Aggregate crime counts by region for a given crime type and year.
    
    Args:
        records: List of dicts from load_real_data()
        crime_type: Column name of the crime type (e.g. 'roubo_rua', 'hom_doloso')
        year: Filter to this year
    
    Returns:
        dict mapping region name -> total count
    """
    totals = {}
    for rec in records:
        if rec.get("ano") != year:
            continue
        region = rec.get("regiao", "Desconhecida")
        count = rec.get(crime_type, 0)
        if not isinstance(count, (int, float)):
            count = _safe_int(count)
        totals[region] = totals.get(region, 0) + count
    return dict(sorted(totals.items()))


def _save_dataset(records: list[dict], output_path: str = None):
    """Save filtered records as JSON."""
    if output_path is None:
        output_path = Path(__file__).resolve().parent.parent / "data" / "rio_crime_data.json"
    else:
        output_path = Path(output_path).resolve()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"[data_pipeline] Saved {len(records)} records to {output_path}")
    return output_path


# ── CLI usage ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    src = sys.argv[1] if len(sys.argv) > 1 else "/tmp/isp_data.csv"
    dst = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"[data_pipeline] Loading data from {src} ...")
    data = load_real_data(src)
    print(f"[data_pipeline] Loaded {len(data)} records (Rio de Janeiro, 2024-2026)")

    _save_dataset(data, dst)
