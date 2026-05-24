"""Smoke tests do router de RELINTs/agências.

Roda standalone via: `python -m hexagon_spatial.test_relints_api`
Cobre:
- /relints/parametros            → 5 fatores canônicos
- /relints/agencias              → 8 áreas, todas com RELINT casado
- /relints/agencias/{fid}        → detalhe com geometria + RELINT completo
- /relints/                      → lista de 8 RELINTs com 3 sub-áreas cada
- /relints/{codigo}              → RELINT específico
- /relints/{codigo} inexistente  → 404
"""
from __future__ import annotations

import sys

from fastapi.testclient import TestClient

from .app import app
from .relints_parser import FATORES

client = TestClient(app)

FAILED: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    status = "PASS" if cond else "FAIL"
    print(f"  [{status}] {name}{(' — ' + detail) if detail else ''}")
    if not cond:
        FAILED.append(name)


def test_root():
    print("\n== / ==")
    r = client.get("/")
    check("root 200", r.status_code == 200)
    check("root has endpoints", "endpoints" in r.json())


def test_parametros():
    print("\n== /relints/parametros ==")
    r = client.get("/relints/parametros")
    check("200", r.status_code == 200)
    data = r.json()
    check("5 fatores", set(data.keys()) == set(FATORES), f"keys={list(data.keys())}")
    check(
        "rótulo Retenção de fluxo",
        "Retenção de fluxo" in data["retencao_fluxo"],
        data["retencao_fluxo"],
    )


def test_list_agencias():
    print("\n== /relints/agencias ==")
    r = client.get("/relints/agencias")
    check("200", r.status_code == 200)
    rows = r.json()
    check("8 agências", len(rows) == 8, f"got {len(rows)}")
    check(
        "todas têm RELINT",
        all(x.get("relint_match") and x["relint_match"]["codigo"] for x in rows),
    )
    check(
        "fids esperados",
        {x["fid"] for x in rows} == {2, 9, 10, 11, 12, 14, 19, 20},
    )
    check(
        "score >= 0.85 em todas",
        all(x["relint_match"]["score"] >= 0.85 for x in rows),
        f"min={min(x['relint_match']['score'] for x in rows)}",
    )


def test_get_agencia_detalhe():
    print("\n== /relints/agencias/10 (Jardim de Alah) ==")
    r = client.get("/relints/agencias/10")
    check("200", r.status_code == 200)
    ag = r.json()
    check("nome contém 'Jardim'", "Jardim" in ag["nome_area"], ag["nome_area"])
    check("centróide RJ (Rio Sul)",
          -23.1 < ag["centroide"]["lat"] < -22.7 and -43.9 < ag["centroide"]["lon"] < -43.0)
    check("area_km2 > 0", ag["area_km2"] > 0)
    check("geometry é GeoJSON", ag["geometry"]["type"] in ("Polygon", "MultiPolygon"))
    check("relint embutido", ag["relint"] is not None)
    check("relint codigo == RI_012_2026", ag["relint"]["codigo"] == "RI_012_2026")
    check("3 sub-áreas", ag["relint"]["n_subareas"] == 3)


def test_get_agencia_404():
    print("\n== /relints/agencias/999 ==")
    r = client.get("/relints/agencias/999")
    check("404", r.status_code == 404)


def test_list_relints():
    print("\n== /relints/ ==")
    r = client.get("/relints/")
    check("200", r.status_code == 200)
    rows = r.json()
    check("8 RELINTs", len(rows) == 8)
    check("todos com 3 sub-áreas", all(x["n_subareas"] == 3 for x in rows))
    check(
        "todos com 5 fatores * 3 = 15 preenchidos",
        all(
            sum(1 for s in x["subareas"] for v in s["fatores"].values() if v) == 15
            for x in rows
        ),
    )
    check(
        "todos com 5 necessidades",
        all(len(x["conclusao"]["necessidades"]) == 5 for x in rows),
    )


def test_get_relint_codigo():
    print("\n== /relints/RI_010_2026 ==")
    r = client.get("/relints/RI_010_2026")
    check("200", r.status_code == 200)
    rel = r.json()
    check(
        "titulo Rodoviária",
        "RODOVIÁRIA" in rel["titulo"],
        rel["titulo"],
    )
    s0 = rel["subareas"][0]
    check(
        "sub-área 0 tem retencao_fluxo",
        s0["fatores"]["retencao_fluxo"] is not None,
        s0["fatores"]["retencao_fluxo"] or "",
    )
    check(
        "sub-área 0 tem rotas_dispersao",
        s0["fatores"]["rotas_dispersao"] is not None,
    )


def test_get_relint_404():
    print("\n== /relints/RI_999_9999 ==")
    r = client.get("/relints/RI_999_9999")
    check("404", r.status_code == 404)


def test_spatial_priority_areas():
    print("\n== /spatial/priority-areas?top_n=3 ==")
    r = client.get("/spatial/priority-areas?top_n=3")
    check("200", r.status_code == 200)
    d = r.json()
    check("score_geral 3 top_areas", len(d["score_geral"]["top_areas"]) == 3)
    check("6 instituicoes", set(d["scores_por_instituicao"].keys()) ==
          {"PM-RJ", "GM-Rio", "RioLuz", "COMLURB", "SEOP", "CET-Rio"})
    check("PM-RJ tem pesos somando ~1",
          abs(sum(d["scores_por_instituicao"]["PM-RJ"]["pesos"].values()) - 1.0) < 0.01)
    check("PM-RJ top1 score > 0",
          d["scores_por_instituicao"]["PM-RJ"]["top_areas"][0]["score"] > 0)


def main() -> int:
    test_root()
    test_parametros()
    test_list_agencias()
    test_get_agencia_detalhe()
    test_get_agencia_404()
    test_list_relints()
    test_get_relint_codigo()
    test_get_relint_404()
    test_spatial_priority_areas()

    print(f"\n=== {len(FAILED)} falhas ===")
    for f in FAILED:
        print(f"  - {f}")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
