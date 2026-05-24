# CompStat Rio — Contrato Backend → Frontend (frente Lucas)

Mapa estratégico das **8 regiões oficiais da Força Municipal** com score de risco
por região, recorte granular, relatórios (semanal + por região) e chat com agente
LLM. Integra os scores do Perri (MCDA/H3) e os relatos do Disque Denúncia (Arick).

> **TL;DR**
> 1. Suba: de `backend/Lucas/` → `uvicorn app:app --reload --port 8000`
>    (ou de `backend/` → `uvicorn app:app --app-dir Lucas --port 8000`).
> 2. Mapa: `GET /map/regions` → 8 polígonos com score.
> 3. Clique na região: `GET /map/regions/{region_id}` → camadas + agregações.
> 4. Relatório da região (lazy, LLM): `GET /reports/regions/{region_id}`.
> 5. Relatório semanal: `GET /reports/weekly-strategic`.
> 6. Chat: `POST /reports/chat`.
> 7. Swagger: `http://localhost:8000/docs`.

O mesmo servidor também serve os endpoints do Perri (`/relints/*`, `/spatial/*`)
— ver `perri/hexagon_spatial/API.md`.

---

## 1. Modos de dados (importante para o frontend)

O backend detecta automaticamente o modo em `GET /` (`data_mode`):

| Modo | Quando | O que muda |
|---|---|---|
| `live` | Submódulo `claude_impact_lab_compstat_rio/dados` presente | Ocorrências, câmeras e fatores urbanos **reais** (join ponto-em-polígono). |
| `static` | Submódulo ausente (padrão deste repo hoje) | Denúncias **reais** (Arick); ocorrências/câmeras/fatores **aproximados** via células H3 do Perri. |

Cada região reporta `properties.data_quality` por fonte: `"real"`, `"aproximado"`
ou `"indisponivel"`. **Mostre isso na UI** (ex. badge "aprox.") para não induzir o
gestor a erro. O campo `llm_mode` (`anthropic`|`fake`) indica se a narrativa veio
de LLM ou do fallback determinístico.

`region_id` ↔ `fid`: `region_id = "regiao_{fid:03d}"` (fids válidos: 2, 9, 10, 11,
12, 14, 19, 20 → `regiao_002` … `regiao_020`). Ambos vêm nas properties.

---

## 2. Recortes temporais (`time_window`)

Query param aceito por `/map/*` e `/reports/*` (e em `filters.time_window` do chat):

| valor | significado |
|---|---|
| `last_30_days` (padrão) | últimos 30 dias **a partir da data mais recente do dataset** |
| `7d` / `3d` / `1d` | últimos N dias do dataset |
| `last_7_days` | idem 7d |
| `all` | todo o histórico |

A janela é relativa ao `max(data)` das fontes, não à data de hoje (o dataset é
histórico). `time_window.end` na resposta é essa data de referência.

---

## 3. Endpoints

### 3.1 `GET /map/regions`

Query: `time_window` (ver §2). Retorna um **FeatureCollection** (GeoJSON) das 8
regiões, já ordenado por `risk_score` desc.

```json
{
  "type": "FeatureCollection",
  "generated_at": "2026-05-24T00:00:00Z",
  "data_mode": "static",
  "time_window": { "preset": "all", "start": null, "end": "2026-05-08", "historical_available": false },
  "features": [
    {
      "type": "Feature",
      "id": "regiao_020",
      "properties": {
        "region_id": "regiao_020",
        "fid": 20,
        "region_name": "Presidente Vargas - Campo de Santana - Central do Brasil - Cinelândia",
        "risk_score": 85.0,
        "risk_level": "high",
        "primary_agency": "PM-RJ",
        "secondary_agencies": ["SEOP", "GM-Rio"],
        "summary": "Risco high (score 85/100) em todo o histórico: 4558 ocorrências e 231 denúncias. Órgão municipal sugerido: PM-RJ.",
        "occurrence_count": 4558,
        "denuncia_count": 231,
        "camera_count": 153,
        "urban_factor_count": 56,
        "critical_area_count": 2,
        "data_quality": { "ocorrencias": "aproximado", "denuncias": "real", "fatores": "aproximado", "cameras": "aproximado" }
      },
      "geometry": { "type": "Polygon", "coordinates": [[[ -43.19, -22.90 ], ...]] }
    }
  ]
}
```

### 3.2 `GET /map/regions/{region_id}`

Query: `time_window`. Recorte granular determinístico (sem LLM). **404** se o
`region_id` não existir.

```json
{
  "region": { /* mesmas properties de §3.1 */ },
  "time_window": { "preset": "all", "start": null, "end": "2026-05-08", "historical_available": false },
  "score_components": [
    { "key": "ocorrencias", "label": "Ocorrências (ISP-RJ)", "raw_count": 4558, "normalized": 1.0, "weight": 0.40, "contribution": 40.0 },
    { "key": "denuncias", "label": "Denúncias (Disque Denúncia)", "raw_count": 231, "normalized": 1.0, "weight": 0.25, "contribution": 25.0 },
    { "key": "fatores", "label": "Fatores urbanos", "raw_count": 56, "normalized": 1.0, "weight": 0.20, "contribution": 20.0 },
    { "key": "cameras_inv", "label": "Cobertura inversa de câmeras", "raw_count": 153, "normalized": 1.0, "weight": 0.15, "contribution": 0.0 }
  ],
  "map_layers": {
    "polygon": { "type": "Polygon", "coordinates": [ ... ] },
    "occurrences": [ { "lat": -22.9, "lon": -43.19, "delito": "...", "data": "...", "hora": 18 } ],
    "denuncias":   [ { "lat": -22.9, "lon": -43.19, "classe": "CRIMES CONTRA O PATRIMÔNIO", "tipo": "...", "bairro": "CENTRO", "hora": 14 } ],
    "cameras":     [ { "lat": -22.9, "lon": -43.19 } ],
    "urban_factors": [ { "lat": -22.9, "lon": -43.19, "tipo_ocorrencia_descricao": "..." } ],
    "critical_areas": [ { "h3_cell": "88a8a0...", "lat": -22.91, "lon": -43.18, "score": 57.5, "cnt_ocorrencias": 9 } ]
  },
  "occurrence_types": [ { "tipo": "CRIMES CONTRA O PATRIMÔNIO", "count": 126 } ],
  "hourly_histogram": [ { "hour": 0, "count": 1 }, ... { "hour": 23, "count": 4 } ],
  "occurrence_groups": [],
  "regional_report": null,
  "recommended_actions": [],
  "provenance": [ { "source": "Disque Denúncia", "description": "...", "n_records": 231 } ]
}
```

> `occurrence_groups`/`regional_report` aqui vêm vazios de propósito — eles são
> gerados sob demanda (LLM) no endpoint de relatório (§3.3), para economizar tokens.
> Pontos das camadas são limitados a 800 por camada (amostra para o mapa).

### 3.3 `GET /reports/regions/{region_id}`  — **lazy + cache + LLM**

Query: `time_window`. Gera o relatório individual da região (narrativa por agente
LLM quando há `ANTHROPIC_API_KEY`, senão fallback determinístico). A 1ª chamada
computa; as seguintes vêm do cache (`cached: true`). **404** se inexistente.

```json
{
  "region_id": "regiao_020",
  "region_name": "Presidente Vargas - ...",
  "summary": "Risco high (score 85/100) ...",
  "full_explanation": "A região '...' tem score 85/100 (nível high) ... Componentes do score: ...",
  "score": { "final": 85.0, "level": "high", "components": [ /* score_components */ ] },
  "occurrences": [
    {
      "group_id": "crimes_contra_o_patrimonio__regiao_020",
      "summary": "126 denúncias de CRIMES CONTRA O PATRIMÔNIO na região.",
      "detailed_explanation": "Concentração de 126 denúncias ... pico em 14h, 16h, 21h. Bairros: CENTRO, ...",
      "score": { "risk": 100.0, "confidence": 0.9 },
      "action_plan": {
        "responsible_agency": "PM-RJ",
        "supporting_agencies": [],
        "recommended_action": "Reforçar policiamento ostensivo orientado por dados no horário crítico.",
        "priority": "high",
        "time_window": "14h, 16h, 21h"
      },
      "map_data": { "points": [ {"lat":-22.9,"lon":-43.19} ], "hotspots": [], "critical_hours": ["14h","16h","21h"], "related_cameras": [], "related_urban_factors": [] },
      "provenance": [ { "source": "Disque Denúncia", "n_records": 126, "confidence": 0.9 } ]
    }
  ],
  "uncertainties": [ "Contagem de ocorrencias é aproximada (modo estático, proxy H3); ..." ],
  "guardrails": [ "Recomendações são sugestões; a decisão final é humana.", ... ],
  "provenance": [ ... ],
  "generated_by": "RegionalRiskNarrativeAgent",
  "llm_mode": "fake",
  "cached": false,
  "audit_flags": null
}
```

### 3.4 `GET /reports/weekly-strategic`

Query: `time_window`. Relatório consolidado para a reunião semanal.

```json
{
  "report_id": "weekly_2026_05_24",
  "title": "Relatório Estratégico Semanal — CompStat Rio",
  "summary": "8 regiões analisadas ... Maior prioridade: ...",
  "ranked_regions": [
    { "region_id": "regiao_020", "region_name": "...", "risk_score": 85.0, "risk_level": "high", "primary_agency": "PM-RJ", "rationale": "4558 ocorrências e 231 denúncias; órgão PM-RJ." }
  ],
  "strategic_priorities": [ "Presidente Vargas ...: nível high (score 85) — órgão PM-RJ." ],
  "agency_matrix": [ { "agency": "PM-RJ", "regions": ["regiao_009","regiao_020", ...], "n_regions": 5 } ],
  "map_references": [ "regiao_020", "regiao_019", ... ],
  "provenance": [ ... ],
  "generated_by": "StrategicWeeklyReportAgent",
  "llm_mode": "fake"
}
```

`map_references` e `ranked_regions[].region_id` casam com os `feature.id` de
§3.1 — use para destacar a região no mapa ao clicar no relatório.

### 3.5 `POST /reports/chat`

Body:

```json
{
  "question": "Por que esta região está com risco alto?",
  "region_id": "regiao_020",
  "filters": { "time_window": "all", "occurrence_type": null, "hour_range": null, "agency": null }
}
```

`region_id` é opcional (sem ele, responde sobre o ranking geral). Resposta:

```json
{
  "answer": "A região Presidente Vargas ... está com risco high (score 85/100). Principais tipos: ...",
  "region_refs": ["regiao_020"],
  "map_refs": ["occurrences", "denuncias", "critical_areas"],
  "evidence_refs": [ { "source": "Disque Denúncia", "description": "...", "n_records": 231 } ],
  "limitations": [ "Contagem de ocorrencias é aproximada (modo estático).", "Resposta determinística (sem LLM); ..." ],
  "agent_trace": [ "retrieval: modo=static, janela_dias=null", "contexto da região regiao_020 ...", "geração: fake" ],
  "llm_mode": "fake"
}
```

---

## 4. Tipos TypeScript

```ts
export type RiskLevel = "high" | "medium" | "low";
export type DataQuality = "real" | "aproximado" | "indisponivel";
export type LLMMode = "anthropic" | "fake";
export type AgencyId = "PM-RJ" | "GM-Rio" | "RioLuz" | "COMLURB" | "SEOP" | "CET-Rio";

export interface TimeWindow {
  preset: string; start: string | null; end: string | null; historical_available: boolean;
}
export interface Provenance {
  source: string; description?: string; n_records?: number | null; confidence?: number | null;
}
export interface ScoreComponent {
  key: "ocorrencias" | "denuncias" | "fatores" | "cameras_inv";
  label: string; raw_count: number; normalized: number; weight: number; contribution: number;
}

export interface RegionProperties {
  region_id: string; fid: number; region_name: string;
  risk_score: number; risk_level: RiskLevel;
  primary_agency: string; secondary_agencies: string[]; summary: string;
  occurrence_count: number; denuncia_count: number; camera_count: number;
  urban_factor_count: number; critical_area_count: number;
  data_quality: Record<string, DataQuality>;
}
export interface RegionFeature {
  type: "Feature"; id: string; properties: RegionProperties; geometry: GeoJSON.Polygon | GeoJSON.MultiPolygon;
}
export interface RegionsFeatureCollection {
  type: "FeatureCollection"; generated_at: string; data_mode: "live" | "static";
  time_window: TimeWindow; features: RegionFeature[];
}

export interface MapPoint { lat: number; lon: number; [k: string]: unknown; }
export interface CriticalArea { h3_cell: string; lat: number; lon: number; score: number; [k: string]: unknown; }
export interface MapLayers {
  polygon: GeoJSON.Polygon | {}; occurrences: MapPoint[]; denuncias: MapPoint[];
  cameras: MapPoint[]; urban_factors: MapPoint[]; critical_areas: CriticalArea[];
}
export interface RegionDetail {
  region: RegionProperties; time_window: TimeWindow; score_components: ScoreComponent[];
  map_layers: MapLayers;
  occurrence_types: { tipo: string; count: number }[];
  hourly_histogram: { hour: number; count: number }[];
  occurrence_groups: unknown[]; regional_report: unknown | null;
  recommended_actions: unknown[]; provenance: Provenance[];
}

export interface ActionPlan {
  responsible_agency: string; supporting_agencies: string[];
  recommended_action: string; priority: RiskLevel; time_window: string | null;
}
export interface OccurrenceGroupReport {
  group_id: string; summary: string; detailed_explanation: string;
  score: { risk: number; confidence: number };
  action_plan: ActionPlan; map_data: Record<string, unknown>; provenance: Provenance[];
}
export interface RegionReport {
  region_id: string; region_name: string; summary: string; full_explanation: string;
  score: { final: number; level: RiskLevel; components: ScoreComponent[] };
  occurrences: OccurrenceGroupReport[]; uncertainties: string[]; guardrails: string[];
  provenance: Provenance[]; generated_by: string; llm_mode: LLMMode; cached: boolean;
  audit_flags?: { issues: string[]; warnings: string[] } | null;
}

export interface RankedRegion {
  region_id: string; region_name: string; risk_score: number; risk_level: RiskLevel;
  primary_agency: string; rationale: string;
}
export interface WeeklyReport {
  report_id: string; title: string; summary: string;
  ranked_regions: RankedRegion[]; strategic_priorities: string[];
  agency_matrix: { agency: string; regions: string[]; n_regions: number }[];
  map_references: string[]; provenance: Provenance[]; generated_by: string; llm_mode: LLMMode;
}

export interface ChatRequest {
  question: string; region_id?: string | null;
  filters?: { time_window?: string; occurrence_type?: string | null; hour_range?: number[] | null; agency?: string | null };
}
export interface ChatResponse {
  answer: string; region_refs: string[]; map_refs: string[];
  evidence_refs: Provenance[]; limitations: string[]; agent_trace: string[]; llm_mode: LLMMode;
}

// ─── Helpers de fetch ────────────────────────────────────────────────────────
const BASE = "http://localhost:8000";
export const api = {
  regions: (tw = "last_30_days") =>
    fetch(`${BASE}/map/regions?time_window=${tw}`).then(r => r.json() as Promise<RegionsFeatureCollection>),
  region: (id: string, tw = "last_30_days") =>
    fetch(`${BASE}/map/regions/${id}?time_window=${tw}`).then(r => r.json() as Promise<RegionDetail>),
  regionReport: (id: string, tw = "last_30_days") =>
    fetch(`${BASE}/reports/regions/${id}?time_window=${tw}`).then(r => r.json() as Promise<RegionReport>),
  weekly: (tw = "last_30_days") =>
    fetch(`${BASE}/reports/weekly-strategic?time_window=${tw}`).then(r => r.json() as Promise<WeeklyReport>),
  chat: (body: ChatRequest) =>
    fetch(`${BASE}/reports/chat`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) })
      .then(r => r.json() as Promise<ChatResponse>),
};
```

---

## 5. Guardrails (mostre na UI)

Toda recomendação carrega `provenance`, órgão responsável e confiança. O backend
roda um `AuditAndProvenanceAgent` que bloqueia/sinaliza PII bruta, linguagem
proibida (reconhecimento facial, biometria, placa, perfilamento) e uso
criminalizante de vulnerabilidade social — eventuais alertas vêm em
`audit_flags`. **A decisão é sempre humana**; o produto recomenda, não decide.

---

## 6. Como rodar e testar

```bash
# de backend/ — instalar deps (a stack científica já costuma estar no ambiente)
pip install -r Lucas/requirements.txt

# (opcional) modo live: traz os CSVs brutos do Perri
git submodule update --init

# subir o servidor (de backend/Lucas/)
uvicorn app:app --reload --port 8000

# narrativa via LLM (opcional): exportar a chave antes de subir
#   PowerShell:  $env:ANTHROPIC_API_KEY = "sk-ant-..."
#   bash:        export ANTHROPIC_API_KEY=sk-ant-...

# testes (modo estático + provider fake; não precisa de submódulo nem chave)
pytest Lucas/tests -q
```

Verificações rápidas:

| Cenário | Como |
|---|---|
| API no ar + modo | `GET /` → `data_mode`, `llm_mode` |
| 8 regiões | `GET /map/regions` → `features.length === 8` |
| Recorte granular | `GET /map/regions/regiao_020` → `map_layers` preenchidas |
| Relatório lazy | `GET /reports/regions/regiao_020` (2ª vez `cached:true`) |
| Semanal | `GET /reports/weekly-strategic` → 8 em `ranked_regions` |
| Chat | `POST /reports/chat` |
