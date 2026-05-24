# CIVITAS — Instruções para o Frontend (atualizações do backend Lucas)

Este documento descreve **o que mudou no backend** e **o que o frontend precisa
mudar** para aproveitar tudo. Está dividido em três partes:

1. **Status atual** — o que já existe no `frontend/src/store/data.jsx` e como
   está sendo usado hoje.
2. **Melhorias em endpoints já consumidos** — campos que o backend devolve mas
   o frontend descarta (especialmente do `/reports/weekly-strategic`).
3. **Novos campos e endpoints** — `/operations/draft`, `recommended_actions`,
   `camera_coverage`, `decision_trace`, `bingo`, `operation_summary`.

> Resumo:
> - O **weekly report ESTÁ sendo gerado por IA** (LLM enriquece `summary`,
>   `strategic_priorities`, `ranked_rationales` quando há `ANTHROPIC_API_KEY`).
>   O frontend hoje só usa `ranked_regions[]`. Há ~6 campos prontos para exibir.
> - Cada região agora tem 3 narrativas adicionais geradas por agentes
>   especializados: **fator urbano → ação**, **lacuna de câmera**, **trace de
>   decisão**. Tudo com fallback determinístico (nunca quebra).
> - Novo endpoint `/operations/draft` devolve a **alocação dos 600 agentes**
>   por região e hotspot, com narrativa por região.

---

## 1. Status atual

Hoje o `data.jsx` chama:

| Endpoint | Chamado em | O que é usado | O que é descartado |
|---|---|---|---|
| `GET /map/regions?time_window=...` | `loadSummary()` | features → `areas[]` | nada |
| `GET /reports/weekly-strategic?time_window=...` | `loadSummary()` | `ranked_regions[].rationale` | **summary, strategic_priorities, agency_matrix, operation_allocation, operation_summary, total_agents, llm_mode, provenance** |
| `GET /reports/regions/{region_id}?time_window=...` | `loadReport(fid)` | `full_explanation`, `occurrences[]`, `score`, `uncertainties`, `guardrails`, `llm_mode` | (e agora 4 campos novos — ver §3) |
| `POST /reports/chat` | `chat()` | resposta completa | — |

Endpoints **nunca chamados**:
- `GET /operations/draft` — alocação dos 600 agentes (novo, ver §3.4)
- `GET /map/regions/{region_id}` — recorte granular para o mapa (camadas:
  occurrences, denuncias, cameras, urban_factors, critical_areas). Hoje o
  frontend só usa as 8 regiões em bloco; ao clicar em uma região, este endpoint
  já traz pontos prontos para o MapLibre.

---

## 2. Melhorias em endpoints já consumidos

### 2.1 `/reports/weekly-strategic` — o relatório semanal completo

Hoje só `ranked_regions[]` é consumido. O backend devolve mais 6 campos
prontos para a UI da reunião CompStat. **Sugestão de tela:** painel
"**Briefing semanal**" (botão no topo do app ou modal/overlay), com a estrutura
abaixo.

Schema completo:
```ts
interface WeeklyReport {
  report_id: string;                // "weekly_2026_05_24"
  title: string;                    // "Relatório Estratégico Semanal — CompStat Rio"
  summary: string;                  // ★ resumo executivo gerado pela LLM
  ranked_regions: RankedRegion[];   // ★ já consumido
  strategic_priorities: string[];   // ★ 3-5 bullets gerados pela LLM
  agency_matrix: AgencyMatrixRow[]; // ★ matriz órgão → regiões responsáveis
  operation_allocation: AllocRow[]; // ★ NOVO: 600 agentes por região
  operation_summary: string|null;   // ★ NOVO: narrativa LLM da alocação
  total_agents: number|null;        // ★ NOVO: 600
  map_references: string[];         // region_ids — destacar no mapa ao clicar
  provenance: Provenance[];
  generated_by: "StrategicWeeklyReportAgent";
  llm_mode: "anthropic" | "fake";
}
interface AgencyMatrixRow { agency: string; regions: string[]; n_regions: number }
interface AllocRow { region_id: string; region_name: string; agents: number; n_hotspots: number; rationale?: string }
```

#### Onde colocar na tela

```
┌──────────────────── Briefing Semanal (modal/drawer) ────────────────────┐
│  [Header]       weekly_report.title                                     │
│  [Badge LLM]    weekly_report.llm_mode === "anthropic" ? "✨ IA" : "—" │
│                                                                          │
│  [Resumo]       weekly_report.summary               ← LLM, 2-3 frases    │
│                                                                          │
│  [Prioridades]  weekly_report.strategic_priorities  ← lista bulletada    │
│                                                                          │
│  [Ranking]      weekly_report.ranked_regions        ← já existe          │
│                                                                          │
│  [Matriz]       weekly_report.agency_matrix         ← tabela órgão×regs  │
│                                                                          │
│  [Operação]     weekly_report.operation_summary     ← LLM, parágrafo     │
│                 weekly_report.total_agents          ← "600 agentes"      │
│                 weekly_report.operation_allocation  ← tabela por região  │
│                                                                          │
│  [Provenance]   weekly_report.provenance            ← rodapé sutil       │
└──────────────────────────────────────────────────────────────────────────┘
```

#### Patch sugerido em `data.jsx`

```js
// Mantenha o objeto completo, não só ranked_regions
this.state.summary = {
  period: periodKey,
  areas,
  integrated_occurrences,
  weekly_report: weeklyReport,           // ← NOVO: preservar tudo
  data_mode: featureCollection.data_mode,
  time_window: featureCollection.time_window,
};
```

E adicione um componente `<WeeklyBriefing />` que lê `summary.weekly_report`.
Atalho no topo do app: botão "📋 Briefing semanal".

---

### 2.2 `/reports/regions/{region_id}` — o relatório por região

Já consumido em `loadReport(fid)`. **3 novos campos** foram adicionados (ver
§3.1–§3.3) e o `mapRegionReport` atual descarta-os.

**Patch em `data.jsx`**, função `mapRegionReport`:

```js
function mapRegionReport(regionReport) {
  // ... código existente ...
  return {
    occurrences: [topEntry, ...groupEntries],
    summary: regionReport.summary,
    full_explanation: regionReport.full_explanation,
    score: regionReport.score,
    uncertainties: regionReport.uncertainties || [],
    guardrails: regionReport.guardrails || [],
    llm_mode: regionReport.llm_mode,
    generated_by: regionReport.generated_by,
    // ── NOVOS ──────────────────────────────────────────────
    recommended_actions: regionReport.recommended_actions || [], // §3.1
    camera_coverage:    regionReport.camera_coverage || null,    // §3.2
    decision_trace:     regionReport.decision_trace || null,     // §3.3
    bingo:              regionReport.bingo || null,              // §3.5
  };
}
```

---

## 3. Novos campos e endpoints

### 3.1 `recommended_actions[]` — UrbanFactorActionAgent

**O que é:** lista de ações por (órgão municipal × problema × hotspot), já
enriquecida com narrativa LLM contextual (cita horário do crime, modalidade
dominante e janela). Cada item é uma sugestão para a Casa Civil/Prefeitura
acionar o órgão competente.

**Schema:**
```ts
interface RecommendedAction {
  problem: string;              // ex.: "Vegetação encobrindo iluminação pública"
  responsible_agency: string;   // ex.: "Rio Luz"
  esfera: "municipal" | "estadual";
  recommended_action: string;   // template determinístico (fallback)
  narrative: string;            // ★ LLM contextual ("Pico de roubo às 22h coincide...")
  ressalva?: string;            // ★ presente se órgão social (SMAS) — não criminalizar
  priority: "high" | "medium" | "low";
  evidence: string;             // ex.: "co-ocorrência temporal 0.71 no hotspot ..."
  hotspot_id: string;
  time_window: string;          // ex.: "22h, 23h, 00h"
}
```

**Onde colocar na tela:** dentro do painel da região (sidebar ou bottom),
seção **"Ações recomendadas (sugeridas — OK humano)"**.

```
┌── Ações recomendadas ──────────────────────────────────────┐
│  🟥 [high]  Rio Luz                                         │
│  Vegetação encobrindo iluminação pública                    │
│  "Pico de roubo a transeunte às 22h-00h coincide com        │
│   trecho de poste obstruído; programar poda + vistoria."    │
│  📍 hotspot_XYZ  ⏰ 22h, 23h, 00h                            │
│                                                              │
│  🟧 [medium]  SMAS                                          │
│  Pessoas em situação de rua                                 │
│  "Articulação com SMAS/saúde no entorno do terminal."       │
│  ⚠ Articulação social — sem ação repressiva.                │
└─────────────────────────────────────────────────────────────┘
```

Estilo: cor pela `priority` (high→vermelho, medium→laranja, low→amarelo).
Sempre mostrar `ressalva` quando presente (cor diferente, ícone ⚠).

---

### 3.2 `camera_coverage` — CameraCoverageAgent

**O que é:** análise das **lacunas de cobertura** de câmera nos hotspots. Sem
imagem/placa/rosto/biometria — só localização.

**Schema:**
```ts
interface CameraCoverage {
  gaps: Array<{
    hotspot_id: string;
    narrative: string;   // ★ LLM ("Lacuna a 240m; crime dominante em 22h-00h...")
    action: string;      // "FM no terreno + COR reavaliar realocação"
  }>;
  summary: string;       // resumo geral da cobertura
  generated_by?: "CameraCoverageAgent";
  llm_mode?: "anthropic" | "fake";
}
```

**Onde colocar na tela:** dentro do painel da região, seção
**"📷 Cobertura de câmera"**, abaixo de "Ações recomendadas". Se
`gaps.length === 0`, mostrar só o `summary` ("Sem lacunas de cobertura.").

```
┌── 📷 Cobertura de câmera ───────────────────────────────────┐
│  3 hotspots com lacuna de cobertura — acionar COR/FM.       │
│                                                              │
│  • hotspot_XYZ                                              │
│    "Câmera mais próxima a 240m; crime dominante (roubo a    │
│     transeunte) em 22h-00h. Acionar FM no terreno; COR      │
│     reavaliar realocação."                                  │
│    Ação: FM no terreno + COR reavaliar realocação           │
└─────────────────────────────────────────────────────────────┘
```

**Mapa:** desenhar marcador especial nos hotspots com `gap=true` (ícone
câmera tachada). Em hover/click, mostrar o `narrative` deste gap.

---

### 3.3 `decision_trace` — MapRegionOrchestratorAgent

**O que é:** explicação narrativa de **por que** a região está nesta posição
do ranking. Resolve a pergunta da reunião: "por que estou tendo essa
recomendação?"

**Schema:**
```ts
interface DecisionTrace {
  considered: string[];     // ex.: ["Ocorrências: 4558 pontos.", ...]
  discarded: string[];      // sinais descartados e por quê
  narrative: string;        // ★ LLM, 1-2 parágrafos
  layer_weights: Array<{
    layer: string;          // "Ocorrências (ISP-RJ)"
    weight: "alto" | "medio" | "baixo";
    rationale: string;      // "contribuição 40 ao score final."
  }>;
  key_layer_to_watch: string;   // ★ ex.: "Denúncias (Disque Denúncia)"
  generated_by: "MapRegionOrchestratorAgent";
  llm_mode: "anthropic" | "fake";
}
```

**Onde colocar na tela:** topo do painel da região, expandível (accordion)
**"🧠 Por que esta região? (trace de decisão)"**.

```
┌── 🧠 Por que esta região está nesta posição? ──────────────┐
│  decision_trace.narrative                                   │
│  (1-2 parágrafos da LLM)                                    │
│                                                              │
│  ▼ Detalhes                                                 │
│    Pesos por camada                                         │
│      • Ocorrências (ISP-RJ)         [alto]  40 ao score    │
│      • Denúncias (Disque)           [alto]  25 ao score    │
│      • Fatores urbanos              [medio] 20 ao score    │
│      • Cobertura inversa de câmeras [baixo]  0 ao score    │
│                                                              │
│    Considerados (5)                                         │
│      • Ocorrências: 4558 pontos.                            │
│      • Denúncias: 231 pontos.                               │
│      • ...                                                  │
│                                                              │
│    Descartados (2)                                          │
│      • 12 fatores temporalmente descasados.                 │
│      • Domínio territorial: apenas contexto.                │
│                                                              │
│  💡 Observar na próxima semana: Denúncias                   │
└─────────────────────────────────────────────────────────────┘
```

---

### 3.4 `GET /operations/draft` — alocação dos 600 agentes

**Quando chamar:** sob demanda (botão "📋 Plano operacional" no Briefing
Semanal **ou** quando o gestor abre uma região individual).

**Query params:** `time_window` (padrão `last_30_days`), `total_agents`
(padrão 600, mín 1, máx 5000).

**Schema completo:**
```ts
interface OperationDraft {
  total_agents: number;
  allocated: number;
  data_mode: "live" | "static";
  time_window: string;
  cached: boolean;
  summary: string;                // ★ LLM: resumo executivo da alocação
  status: "sugerido";             // sempre — requer OK humano
  generated_by: "OperationDraftAgent";
  llm_mode: "anthropic" | "fake";
  allocations: Array<{
    region_id: string;
    region_name: string;
    risk_score: number;
    agents: number;               // efetivo nesta região
    n_hotspots: number;
    rationale?: string;           // ★ LLM: justificativa por região
    hotspots: Array<{
      hotspot_id: string;
      centroid: { lat: number; lon: number };
      agents: number;             // efetivo neste hotspot
      severity: number;           // 0-100
      dominant_modality: string;
      shift: string;              // "turno noturno (18h–00h)" etc.
      critical_hours_label: string;
      employment_model: string;   // tática operacional
      support_agencies: string[];
      camera_gap: boolean | null;
    }>;
    route: string[];              // ordem sugerida dos hotspots
  }>;
}
```

**Onde colocar na tela:**
1. **No mapa:** ícone de "agentes" em cada hotspot com badge do nº de agentes;
   linhas conectando os hotspots na ordem de `route`.
2. **Painel lateral "Plano operacional":**
   ```
   ┌── 📋 Plano operacional (sugerido) ──────────────────────┐
   │  600 / 600 agentes alocados                              │
   │  [Badge IA] gerado por OperationDraftAgent              │
   │  ⚠ Sugerido — requer OK humano                          │
   │                                                          │
   │  summary (LLM, parágrafo)                                │
   │                                                          │
   │  Por região:                                             │
   │  ▼ Presidente Vargas — 145 agentes (4 hotspots)         │
   │      rationale (LLM)                                    │
   │      Hotspots (severidade ↓):                            │
   │        • hot_001  82 agentes  🌙 turno noturno          │
   │          modalidade: roubo a transeunte                 │
   │          "Patrulhamento noturno a pé; Rio Luz no ponto." │
   │          Apoio: Rio Luz, COMLURB                        │
   │          ⚠ lacuna de câmera                              │
   │        • hot_002  40 agentes  ⏰ pico                   │
   │          ...                                             │
   ```
3. **Botões de ação por hotspot:** "✓ Aprovar alocação" (placeholder — o
   sistema é sugestão; a decisão é humana).

**Patch em `data.jsx`:** adicionar método `loadOperationDraft(periodKey)`:
```js
async loadOperationDraft(periodKey) {
  const tw = twForPeriod(periodKey || this.state.period);
  const draft = await apiFetch(`/operations/draft?time_window=${tw}`);
  this.state.operationDraft = draft;
  this.notify();
  return draft;
}
```

---

### 3.5 `bingo` — overlay espaço-temporal

**O que é:** **estrutura existente** que agora vem dentro do `RegionReport`.
São os hotspots H3 (~175m de aresta) com `centroid`, `n_crimes`,
`dominant_modality`, `critical_hours`, `driver_factors`, `camera`,
`severity`.

**Schema:**
```ts
interface Bingo {
  region_id: string;
  n_hotspots: number;
  n_crime_points: number;
  hotspots: Array<{
    hotspot_id: string;
    h3_cell: string;
    centroid: { lat: number; lon: number };
    n_crimes: number;
    dominant_modality: string;
    modality_breakdown: Record<string, number>;
    critical_hours: number[];        // ex.: [22, 23, 0]
    critical_hours_label: string;    // "22h, 23h, 00h"
    temporal_profile: string;        // "predominantemente noturno"
    driver_factors: Array<{tipo, orgao, esfera, perfil_temporal, overlap_temporal, relevancia}>;
    social_factors: Array<{...}>;
    matched_factors: Array<{...}>;   // todos os fatores próximos, com `relevancia`
    camera: { distance_m: number|null; gap: boolean|null; camera: {lat,lon}|null };
    severity: number;                // 0-100, relativo aos hotspots da região
  }>;
  signals: Array<{ hotspot_id; tipo; descricao; orgao }>;
}
```

**Onde colocar na tela:**
1. **No mapa:** círculos/hexágonos H3 nos `centroid` de cada hotspot, raio
   proporcional a `n_crimes`, cor pela `severity`. Tooltip com
   `dominant_modality` + `critical_hours_label`.
2. **No painel da região:** seção **"🎯 Pontos críticos (hotspots)"**, lista
   ordenada por severidade. Cada card mostra:
   - centroid (lat/lon)
   - `n_crimes` e `dominant_modality`
   - `critical_hours_label` (chip horário)
   - `temporal_profile` (badge: "🌙 noturno" / "☀️ diurno" / "⏰ pico")
   - até 3 `driver_factors` com `overlap_temporal`
   - badge `camera.gap` se true

---

## 4. Tipos TypeScript atualizados (cole no contrato)

```ts
// — Já existentes em FRONTEND_CONTRACT.md —
export type RiskLevel = "high" | "medium" | "low";
export type LLMMode = "anthropic" | "fake";

// — Novos —
export interface RecommendedAction {
  problem: string; responsible_agency: string; esfera: "municipal"|"estadual";
  recommended_action: string; narrative: string; ressalva?: string;
  priority: RiskLevel; evidence: string; hotspot_id: string; time_window: string;
}

export interface CameraGap {
  hotspot_id: string; narrative: string; action: string;
}
export interface CameraCoverage {
  gaps: CameraGap[]; summary: string;
  generated_by?: string; llm_mode?: LLMMode;
}

export interface DecisionTrace {
  considered: string[]; discarded: string[];
  narrative: string;
  layer_weights: { layer: string; weight: "alto"|"medio"|"baixo"; rationale: string }[];
  key_layer_to_watch: string;
  generated_by: "MapRegionOrchestratorAgent"; llm_mode: LLMMode;
}

export interface BingoHotspot {
  hotspot_id: string; h3_cell: string;
  centroid: { lat: number; lon: number };
  n_crimes: number; dominant_modality: string;
  modality_breakdown: Record<string, number>;
  critical_hours: number[]; critical_hours_label: string;
  temporal_profile: string;
  driver_factors: { tipo: string; orgao: string; esfera: string;
                    perfil_temporal: string; overlap_temporal: number;
                    relevancia: "driver"|"estrutural"|"social"|"contexto" }[];
  social_factors: BingoHotspot["driver_factors"];
  camera: { distance_m: number|null; gap: boolean|null;
            camera: { lat: number; lon: number }|null };
  severity: number;
}
export interface Bingo {
  region_id: string; n_hotspots: number; n_crime_points: number;
  hotspots: BingoHotspot[];
  signals: { hotspot_id: string; tipo: string; descricao: string; orgao: string }[];
}

// — RegionReport agora carrega 4 campos novos —
export interface RegionReport {
  region_id: string; region_name: string; summary: string; full_explanation: string;
  score: { final: number; level: RiskLevel; components: ScoreComponent[] };
  occurrences: OccurrenceGroupReport[];
  uncertainties: string[]; guardrails: string[];
  recommended_actions: RecommendedAction[];   // ★ novo
  camera_coverage: CameraCoverage | null;     // ★ novo
  decision_trace: DecisionTrace | null;       // ★ novo
  bingo: Bingo | null;                        // ★ novo
  provenance: Provenance[]; generated_by: string; llm_mode: LLMMode; cached: boolean;
  audit_flags?: { issues: string[]; warnings: string[] } | null;
}

// — WeeklyReport com narrativa operacional —
export interface AllocationRow {
  region_id: string; region_name: string;
  agents: number; n_hotspots: number; rationale?: string;
}
export interface WeeklyReport {
  report_id: string; title: string; summary: string;
  ranked_regions: RankedRegion[]; strategic_priorities: string[];
  agency_matrix: { agency: string; regions: string[]; n_regions: number }[];
  operation_allocation: AllocationRow[];      // ★ novo: 600 agentes por região
  operation_summary: string | null;           // ★ novo: narrativa LLM
  total_agents: number | null;                // ★ novo
  map_references: string[]; provenance: Provenance[];
  generated_by: string; llm_mode: LLMMode;
}

// — OperationDraft (novo endpoint) —
export interface OperationHotspot {
  hotspot_id: string; centroid: { lat: number; lon: number };
  agents: number; severity: number; dominant_modality: string;
  shift: string; critical_hours_label: string;
  employment_model: string; support_agencies: string[];
  camera_gap: boolean | null;
}
export interface OperationRegion {
  region_id: string; region_name: string; risk_score: number;
  agents: number; n_hotspots: number; rationale?: string;
  hotspots: OperationHotspot[]; route: string[];
}
export interface OperationDraft {
  total_agents: number; allocated: number;
  data_mode: "live" | "static"; time_window: string; cached: boolean;
  summary: string; status: "sugerido";
  generated_by: "OperationDraftAgent"; llm_mode: LLMMode;
  allocations: OperationRegion[];
}
```

---

## 5. Resumo dos pontos de UI

| Onde | O que mostrar | Campo backend |
|---|---|---|
| Botão topo / drawer | Briefing Semanal completo | `weekly_report.*` |
| Painel da região — topo | "Por que esta região?" (accordion) | `region_report.decision_trace` |
| Painel da região — meio | Ações recomendadas (cards por prioridade) | `region_report.recommended_actions[]` |
| Painel da região — meio | Cobertura de câmera (lacunas) | `region_report.camera_coverage` |
| Painel da região — meio | Pontos críticos / hotspots | `region_report.bingo.hotspots[]` |
| Mapa — overlays | Círculos H3 por severidade + linhas de rota | `bingo.hotspots`, `operation_draft.allocations[].route` |
| Plano operacional (drawer) | 600 agentes por região/hotspot | `operation_draft.*` |
| Badge global | "✨ Gerado por IA" vs. "fallback" | `*.llm_mode` |
| Rodapé sutil | Limitações / provenance | `*.guardrails`, `*.provenance` |

---

## 6. Ordem sugerida de implementação

1. **Preservar o weekly report inteiro em `summary.weekly_report`** (1 linha
   no `data.jsx`). Liberar tudo que já vem do backend.
2. **Componente `<WeeklyBriefing />`** consumindo `summary`,
   `strategic_priorities`, `agency_matrix`, `operation_summary`,
   `operation_allocation`, `total_agents`. Atalho no topo do app.
3. **Atualizar `mapRegionReport`** para preservar `recommended_actions`,
   `camera_coverage`, `decision_trace`, `bingo` (4 linhas).
4. **Atualizar o painel da região** (sidebar/bottom) com as 4 novas seções.
5. **Novo método `loadOperationDraft()`** + painel "Plano operacional".
6. **Overlay no mapa**: hotspots (H3) + rota + ícones de câmera.

> Tudo tem fallback: o backend nunca devolve `null` para `summary`/`narrative`
> — se a LLM falhar, vem texto determinístico. O frontend nunca precisa tratar
> "LLM caiu"; só precisa lidar com `llm_mode === "fake"` se quiser mostrar um
> indicador.
