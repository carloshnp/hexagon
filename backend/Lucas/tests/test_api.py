"""Smoke tests da frente Lucas (modo estático + provider fake)."""
import pytest
from fastapi.testclient import TestClient

from app import app
from compstat.agents import audit

client = TestClient(app)

WIN = "?time_window=all"
VALID_REGION = "regiao_020"


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    body = r.json()
    assert body["data_mode"] in ("live", "static")
    assert body["llm_mode"] == "fake"


def test_map_regions_has_8_features():
    r = client.get("/map/regions" + WIN)
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 8
    for f in data["features"]:
        p = f["properties"]
        assert {"region_id", "fid", "region_name", "risk_score",
                "risk_level", "primary_agency"} <= p.keys()
        assert 0 <= p["risk_score"] <= 100
        assert p["risk_level"] in ("high", "medium", "low")
    # ordenado por risco desc
    scores = [f["properties"]["risk_score"] for f in data["features"]]
    assert scores == sorted(scores, reverse=True)


def test_map_region_detail():
    r = client.get(f"/map/regions/{VALID_REGION}" + WIN)
    assert r.status_code == 200
    d = r.json()
    assert d["region"]["region_id"] == VALID_REGION
    assert "polygon" in d["map_layers"]
    assert len(d["score_components"]) == 4
    assert isinstance(d["hourly_histogram"], list)


def test_map_region_404():
    assert client.get("/map/regions/regiao_999" + WIN).status_code == 404


def test_region_report_and_cache():
    r = client.get(f"/reports/regions/{VALID_REGION}" + WIN)
    assert r.status_code == 200
    d = r.json()
    assert d["llm_mode"] == "fake"
    assert d["score"]["final"] >= 0
    assert len(d["occurrences"]) > 0
    for g in d["occurrences"]:
        assert g["action_plan"]["responsible_agency"]
        assert g["action_plan"]["recommended_action"]
    assert d["guardrails"]
    # 2ª chamada deve vir do cache
    assert client.get(f"/reports/regions/{VALID_REGION}" + WIN).json()["cached"] is True
    # nunca vaza o campo interno de relatos
    assert "_relatos_sample" not in r.text


def test_region_report_404():
    assert client.get("/reports/regions/regiao_999" + WIN).status_code == 404


def test_weekly_report():
    r = client.get("/reports/weekly-strategic" + WIN)
    assert r.status_code == 200
    d = r.json()
    assert len(d["ranked_regions"]) == 8
    assert d["map_references"]
    assert d["agency_matrix"]


def test_chat_region():
    r = client.post("/reports/chat", json={
        "question": "Por que esta região está com risco alto?",
        "region_id": VALID_REGION,
        "filters": {"time_window": "all"},
    })
    assert r.status_code == 200
    d = r.json()
    assert d["answer"]
    assert VALID_REGION in d["region_refs"]
    assert d["evidence_refs"]


def test_chat_overview():
    r = client.post("/reports/chat", json={"question": "Quais regiões priorizar?",
                                           "filters": {"time_window": "all"}})
    assert r.status_code == 200
    assert len(r.json()["region_refs"]) >= 1


def test_audit_flags_forbidden_and_pii():
    a = audit.audit({"rec": "usar reconhecimento facial", "doc": "CPF 123.456.789-00"})
    assert a["passed"] is False
    assert any("proibido" in i.lower() for i in a["issues"])
    assert any("cpf" in i.lower() for i in a["issues"])


def test_audit_clean_passes():
    a = audit.audit({"rec": "Reforçar patrulhamento orientado por dados no horário crítico."})
    assert a["passed"] is True
