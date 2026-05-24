# Arquitetura Técnica Completa — Radar de Ações Prioritárias

> Documento gerado para orientar qualquer LLM ou desenvolvedor externo sobre a arquitetura, produto, dados, agentes e contratos do sistema. Leia-o integralmente antes de qualquer alteração.

---

## 1. Visão do Produto

O **Radar de Ações Prioritárias** é um sistema de apoio à decisão operacional para segurança pública. Ele ingere eventos de múltiplas fontes heterogêneas (APIs, datasets CSV, briefings), normaliza tudo em um contrato comum, calcula um score de prioridade deterministico e auditável, e gera recomendações operacionais com rastreabilidade de provenance.

**A decisão é sempre humana.** O sistema nunca emite ordens automáticas. A linguagem de toda recomendação gerada é explicitamente "recomendação para validação humana" — nunca imperativa.

### Formulação obrigatória (não negociável)

- Recomendação operacional, não ordem automática.
- Humano aprova, rejeita, encaminha ou conclui via feedback.
- Score deterministico e auditável (sem LLM como fonte única de decisão).
- Provenance obrigatória por recomendação.
- **Proibido:** reconhecimento facial, pessoa-alvo, perfilamento individual, policiamento preditivo opaco.

---

## 2. Stack Tecnológica

| Camada | Tecnologia |
|---|---|
| Backend runtime | Python 3.11, `uv` como gerenciador de pacotes |
| API | FastAPI 0.115+ |
| Modelos de dados | Pydantic v2 + SQLModel |
| Banco de dados | SQLite (`backend/data/radar.db`, ignorado no git) |
| HTTP client | httpx (assíncrono) |
| Testes | pytest |
| Frontend | TypeScript + React 18 + Vite + Leaflet (react-leaflet) |
| Estilos | Tailwind CSS |

### Comandos principais

```powershell
# Todos os testes
uv run --python 3.11 pytest backend/tests -q

# Teste específico
uv run --python 3.11 pytest backend/tests/test_pipeline.py::test_score_is_deterministic_for_same_events -q

# Servidor de desenvolvimento
uv run --python 3.11 uvicorn app.main:app --app-dir backend --reload --port 8000

# Frontend
cd frontend && npm run dev  # porta 5173 por padrão
```

---

## 3. Arquitetura Geral

```
Fonte (Adapter) → CommonEvent → AgentPipeline → OperationalRecommendation → Feedback humano
                                     ↓
              SchemaInference → EntityExtraction → Enrichment → Recommendation → Audit
```

### Fluxo de dados passo a passo

1. **Ingestão:** Adapters lêem dados de fontes externas (APIs, CSV, endpoints privados) e normalizam cada registro em um `CommonEvent`.
2. **Inspeção opcional:** `SchemaInferenceAgent` detecta mapeamento de campos em datasets desconhecidos, PII e chaves de join.
3. **Extração de entidades:** `EntityExtractionAgent` aplica regex determinístico sobre `raw_text` para extrair horários, modus operandi, termos de risco, etc.
4. **Enriquecimento:** `EnrichmentAgent` agrupa eventos por `micro_area` e calcula contexto de grupo (mix de fontes, contagem de evidências, flag context-only).
5. **Recomendação:** `RecommendationAgent` constrói `OperationalRecommendation` com score, briefings por órgão e trace auditável.
6. **Auditoria:** `AuditAgent` é sempre o último trace. Bloqueia recomendações sem provenance, com linguagem proibida, ou baseadas apenas em fontes contextuais (GENI).
7. **Persistência:** `StorageService` persiste runs, eventos e recomendações em SQLite.
8. **Feedback humano:** Operador registra aprovação, rejeição, encaminhamento ou conclusão via POST `/feedback`.

---

## 4. Estrutura de Diretórios

```
claude-impact/
├── backend/
│   ├── app/
│   │   ├── main.py                  # Factory da app FastAPI + lifespan
│   │   ├── config.py                # Settings (dataclass frozen)
│   │   ├── domain/
│   │   │   ├── models.py            # Todos os contratos Pydantic
│   │   │   └── scoring.py           # Score deterministico (WEIGHTS fixos)
│   │   ├── adapters/
│   │   │   ├── base.py              # SourceAdapter ABC
│   │   │   ├── isp_dados.py         # ISP/CISP dados públicos
│   │   │   ├── fogo_cruzado.py      # API Fogo Cruzado (requer JWT)
│   │   │   ├── private_ready.py     # Adapter genérico para fontes restritas
│   │   │   └── official_dataset.py  # Inspeção e normalização de datasets
│   │   ├── agents/
│   │   │   ├── schema_inference.py  # Mapeamento de campos desconhecidos
│   │   │   ├── extraction.py        # Extração de entidades via regex
│   │   │   ├── enrichment.py        # Agrupamento por micro_area
│   │   │   ├── recommendation.py    # Construção da recomendação
│   │   │   ├── briefing.py          # Briefings por órgão
│   │   │   └── audit.py             # Guardrails e provenance
│   │   ├── api/
│   │   │   ├── errors.py            # OperationalAPIError + handler
│   │   │   ├── dependencies.py      # Singletons (DI)
│   │   │   └── routers/
│   │   │       ├── health.py        # GET /health, GET /
│   │   │       ├── sources.py       # GET /sources, /sources/catalog, /sources/*
│   │   │       ├── datasets.py      # POST /datasets/inspect*, /datasets/normalize*
│   │   │       ├── recommendations.py # POST/GET /recommendations, POST /feedback
│   │   │       └── agents.py        # GET /agents/capabilities
│   │   ├── services/
│   │   │   ├── orchestrator.py      # RadarOrchestrator (ponto central)
│   │   │   ├── storage.py           # StorageService (SQLite)
│   │   │   ├── source_registry.py   # Instancia todos os adapters
│   │   │   ├── source_catalog.py    # Metadados estáticos por fonte
│   │   │   └── agent_catalog.py     # Capabilities declaradas por agente
│   │   ├── persistence/
│   │   │   ├── database.py          # Engine SQLModel + init_db + get_session
│   │   │   └── tables.py            # ORM rows: AnalysisRunRow, EventRow, RecommendationRow, FeedbackRow
│   │   ├── utils/
│   │   │   └── privacy.py           # Redação de PII (regex + field-name detection)
│   │   └── data/
│   │       └── demo_events.json     # Eventos sintéticos para demo
│   └── tests/
│       └── test_pipeline.py         # 19 testes de integração
├── frontend/
│   ├── src/
│   │   ├── App.tsx                  # Componente raiz
│   │   ├── types.ts                 # Tipos TypeScript (espelham contratos backend)
│   │   ├── api/
│   │   │   ├── recommendations.ts   # getDemo(), postFeedback()
│   │   │   └── sources.ts           # getSources()
│   │   ├── hooks/
│   │   │   ├── useRecommendations.ts
│   │   │   └── useSources.ts
│   │   └── components/              # (provisório, não alterar)
│   └── package.json
├── pyproject.toml
├── CLAUDE.md
├── AGENTS.md
├── METHODOLOGY.md
└── LIMITATIONS.md
```

---

## 5. Contrato Central: `CommonEvent`

Todo evento normalizado deve satisfazer este modelo. **Campos obrigatórios:**

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | `str` | Identificador único do evento |
| `source` | `SourceName` | Fonte original (enum) |
| `kind` | `EventKind` | Tipo do evento (enum) |
| `access_level` | `AccessLevel` | Nível de acesso (enum) |
| `observed_at` | `datetime` | Quando o evento foi observado |
| `micro_area` | `str` | Área geográfica normalizada (chave de agrupamento) |
| `raw_text` | `str` | Texto bruto, sempre redatado de PII |
| `severity` | `float [0-1]` | Gravidade do evento |
| `confidence` | `float [0-1]` | Confiança na informação |
| `data_quality` | `float [0-1]` | Qualidade do dado da fonte |
| `references` | `list[ProvenanceItem]` | Provenance obrigatória |
| `coordinates` | `Coordinate` | Lat/lng (pode ser None) |
| `attributes` | `dict[str, Any]` | Dados extras da fonte |

**Regra crítica:** Evento sem `references` não pode virar recomendação sem que o `AuditAgent` bloqueie.

### Enumerações

```
AccessLevel:    public | authenticated | restricted | synthetic
SourceName:     fogo_cruzado | isp_dados | disque_denuncia | central_1746 |
                civitas | forca_municipal | geni | official_dataset | camera_metadata
EventKind:      roubo_furto | tiroteio_disparo | denuncia_textual | camera_lpr |
                ordem_publica | abordagem_resultado | territorio_contexto | unknown
Agency:         segur_forca_municipal | civitas | seop | guarda_municipal |
                pmerj | pcerj | multiagencia
SourceStatus:   ready | needs_credentials | unavailable | dataset_only
FeedbackStatus: approved | rejected | forwarded | completed
```

---

## 6. Fontes de Dados

### 6.1 Fogo Cruzado (`fogo_cruzado`)
- **Tipo:** API REST autenticada (JWT)
- **Access level:** `authenticated`
- **Status:** `needs_credentials` (requer email + password ou access_token)
- **O que provê:** Ocorrências de tiroteios no RJ com coordenadas, número de vítimas, envolvimento policial
- **Credenciais (env vars):** `FOGO_CRUZADO_EMAIL`, `FOGO_CRUZADO_PASSWORD` ou `FOGO_CRUZADO_ACCESS_TOKEN`
- **Endpoint base:** `FOGO_CRUZADO_BASE_URL`
- **Severity calculada:** `min(1.0, 0.55 + deaths*0.2 + wounded*0.1 + 0.08*police_action)`
- **Confidence:** 0.78 | **Data quality:** 0.84 (com coords) / 0.68 (sem coords)

### 6.2 ISP Dados (`isp_dados`)
- **Tipo:** CSV público via HTTP
- **Access level:** `public`
- **Status:** `ready`
- **O que provê:** Estatísticas mensais por CISP (roubo de rua, letalidade violenta, apreensão de armas)
- **Env var:** `ISP_BASE_CISP_URL` (tem default)
- **Normalização:** Um evento por linha CSV → `roubo_furto`, `tiroteio_disparo` ou `unknown`
- **Severity:** `min(1.0, 0.35 + value/250)`
- **Confidence:** 0.86 | **Data quality:** 0.9

### 6.3 Central 1746 (`central_1746`)
- **Tipo:** API REST municipal (OAuth)
- **Access level:** `authenticated`
- **Status:** `needs_credentials` (requer `MUNICIPAL_OAUTH_TOKEN`)
- **O que provê:** Denúncias e chamados da prefeitura via RMI
- **Env vars:** `RMI_1746_ENDPOINT`, `MUNICIPAL_OAUTH_TOKEN`

### 6.4 Disque Denúncia (`disque_denuncia`)
- **Tipo:** Dataset restrito
- **Access level:** `restricted`
- **Status:** `dataset_only` (sem endpoint configurado)
- **O que provê:** Denúncias anônimas textuais

### 6.5 Civitas (`civitas`)
- **Tipo:** API restrita (sinais de campo)
- **Access level:** `restricted`
- **Status:** `needs_credentials`
- **Env var:** `CIVITAS_SIGNAL_ENDPOINT`

### 6.6 Força Municipal (`forca_municipal`)
- **Tipo:** API restrita (eventos de campo)
- **Access level:** `restricted`
- **Status:** `needs_credentials`
- **Env var:** `FORCA_MUNICIPAL_EVENTS_ENDPOINT`

### 6.7 GENI (`geni`)
- **Tipo:** Dataset público contextual de grupos armados
- **Access level:** `public`
- **Status:** `dataset_only`
- **Regra crítica:** GENI sozinho **bloqueia** a recomendação no AuditAgent (fonte contextual não pode ser única evidência operacional)

### 6.8 Camera Metadata (`camera_metadata`)
- **Tipo:** Metadados de câmera (sem imagem, sem biometria)
- **Access level:** `restricted`
- **Guardrail hardcoded:** `privacy_mode = "metadata_only_no_biometric_identification"` em todos os eventos
- **raw_text sempre inclui:** "sem imagem bruta, sem reconhecimento facial"

### 6.9 Official Dataset (`official_dataset`)
- **Tipo:** CSV ou JSON arbitrário (upload manual)
- **Função:** `SchemaInferenceAgent` detecta mapeamento de campos automaticamente
- **Uso:** `/datasets/inspect`, `/datasets/normalize`, `/datasets/inspect-csv`, `/datasets/normalize-csv`

---

## 7. Score Deterministico

**Arquivo:** `backend/app/domain/scoring.py`

### Pesos (imutáveis para reprodutibilidade)

```python
WEIGHTS = {
    "delta_vs_baseline": 0.22,
    "recency":           0.16,
    "convergence":       0.18,
    "severity":          0.15,
    "confidence":        0.10,
    "data_quality":      0.09,
    "operational_viability": 0.10,
}
```

### Como cada componente é calculado

| Componente | Cálculo |
|---|---|
| `delta_vs_baseline` | `0.25 + 0.12*recent_count + 0.18*(se ISP presente) + 0.07*textual_signals` (clamped 0-1) |
| `recency` | `1 - (horas_desde_evento_mais_recente / 72)` (clamped 0-1) |
| `convergence` | `source_count / 5` (número de fontes distintas dividido por 5) |
| `severity` | Média de `event.severity` de todos os eventos do grupo |
| `confidence` | Média de `event.confidence` |
| `data_quality` | Média de `event.data_quality` |
| `operational_viability` | `0.46 + 0.24*(se campo/câmera presente) + 0.20*(se todos com coords precisas)` |

### Score final

```python
raw = sum(getattr(breakdown, key) * weight for key, weight in WEIGHTS.items())
score = round(clamp(raw) * 100)  # inteiro 0-100
```

**Garantia de teste:** `test_score_is_deterministic_for_same_events` verifica que o score é idêntico em execuções múltiplas com os mesmos eventos.

---

## 8. Pipeline de Agentes

### 8.1 `SchemaInferenceAgent`

**Arquivo:** `backend/app/agents/schema_inference.py`

**Função:** Inspeciona datasets desconhecidos e mapeia campos para o schema `CommonEvent`.

**Campos obrigatórios que tenta mapear:** `observed_at`, `micro_area`, `raw_text` (mais ~15 opcionais).

**Método principal:**
```python
inspect(request: DatasetInspectionRequest) -> DatasetInspection
```

- Para cada campo-alvo, busca o melhor match entre os aliases conhecidos (ex: `observed_at` aceita `timestamp`, `data_hora`, `data`, `hora`, `captured_at`, etc.)
- Calcula `field_coverage` (% de valores não-vazios por campo)
- Detecta campos com PII potencial via `potential_pii_fields()`
- Sugere `recommended_actions`
- `confidence = max(0.2, min(1.0, 0.35 + len(mapped)/12 - len(missing)*0.12))`

**Saída:** `DatasetInspection` com `mappings`, `missing_required_fields`, `potential_pii_fields`, `join_keys`, `recommended_adapter`, `confidence`.

---

### 8.2 `EntityExtractionAgent`

**Arquivo:** `backend/app/agents/extraction.py`

**Função:** Extrai entidades de `raw_text` com regex determinístico, sem LLM.

**Padrões regex:**
| Entidade | Exemplos detectados |
|---|---|
| `time_mentions` | "14h30", "14:30" |
| `route_mentions` | "fuga", "acesso", "rota", "sentido", "entorno", "saída" |
| `modus_operandi_terms` | "moto", "dupla", "celular", "roubo", "tiro", etc. |
| `risk_terms` | "arma", "tiroteio", "confronto", "ameaça", "tráfico", "milícia", etc. |
| `operational_objects` | "veículo", "câmera", "radar", "ônibus", "estação", etc. |

**Método:**
```python
enrich(events: list[CommonEvent]) -> tuple[list[CommonEvent], AgentTrace]
```

Popula `event.attributes["extracted_entities"]` e `event.attributes["extraction_confidence"]`.

**Confidence da extração:** `max(0.25, min(0.9, 0.35 + total_entidades*0.08))`

---

### 8.3 `EnrichmentAgent`

**Arquivo:** `backend/app/agents/enrichment.py`

**Função:** Agrupa eventos por micro_area para formar grupos de recomendação.

**Método:**
```python
group_for_recommendations(events: list[CommonEvent]) -> tuple[dict[str, list[CommonEvent]], AgentTrace]
```

**Chave de agrupamento (prioridade):** `micro_area` → `cisp` → `neighborhood` → fallback `"area_desconhecida"`

**Contexto de grupo calculado (`event.attributes["group_context"]`):**
- `source_mix`: contador de fontes
- `kind_mix`: contador de tipos de evento
- `evidence_count`: total de items de provenance
- `restricted_count`: eventos com access_level restricted
- `precise_location_count`: eventos com coordenadas precisas
- `latest`: timestamp do evento mais recente
- `context_only`: `True` se **todos** os eventos são `geni` ou `territorio_contexto`

---

### 8.4 `RecommendationAgent`

**Arquivo:** `backend/app/agents/recommendation.py`

**Função:** Constrói `OperationalRecommendation` completa a partir de um grupo de eventos.

**Método:**
```python
build(micro_area: str, events: list[CommonEvent], trace: list[AgentTrace]) -> OperationalRecommendation
```

**Passos internos:**
1. Calcula `ScoreBreakdown` e `priority_score`
2. Escolhe `primary_agency` via heurística de fontes/tipos
3. Extrai evidence única (dedup por id)
4. Detecta `context_only` (bloqueia ação operacional)
5. Gera `action` específica por agency e contexto
6. Gera `rationale` explicando o score
7. Gera `uncertainties` operacionais
8. Calcula janela temporal (2h a partir de menção de hora ou evento mais recente)
9. Constrói briefings com `BriefingAgent`
10. Executa `AuditAgent.audit()` — sempre o último trace

**Heurística de agency:**
- Maioria fogo_cruzado/tiroteio → `pmerj`
- Maioria civitas/forca_municipal → `segur_forca_municipal`
- Camera presente → `civitas`
- SEOP/ordem_publica → `seop`
- Default → `multiagencia`

---

### 8.5 `BriefingAgent`

**Arquivo:** `backend/app/agents/briefing.py`

**Função:** Gera briefing textual formatado por órgão.

**Método:**
```python
build(*, micro_area, score, primary_agency, action, rationale, events, evidence, uncertainties) -> BriefingSet
```

Produz 4 briefings (forca_municipal, civitas, pm_pc, seop), cada um com:
- Título de órgão
- Score e área
- Ação recomendada
- Racional
- Primeiras 5 evidências com source, excerpt e reliability
- Lista de incertezas
- Mix de fontes/tipos

---

### 8.6 `AuditAgent`

**Arquivo:** `backend/app/agents/audit.py`

**Função:** Guardrail final. Bloqueia ou avisa sobre problemas de compliance.

**Termos proibidos** (causam bloqueio se encontrados em `action` ou `rationale`):
```
"perfil racial", "pessoa-alvo", "mandar a policia", "prever crime",
"reconhecimento facial positivo", "identificar rosto"
```

**Safeguards sempre incluídos em toda recomendação:**
```
"Sem reconhecimento facial."
"Sem pessoa-alvo."
"Sem ranqueamento estigmatizante de comunidade."
"Sem decisão automática: recomendação exige validação humana."
"Toda afirmação operacional deve ter fonte rastreável."
```

**Causas de bloqueio (`status: "blocked"`):**
| Condição | Descrição |
|---|---|
| `missing_provenance` | `evidence` vazia |
| `event_without_reference` | Algum evento sem `references` |
| `forbidden_operational_language` | Termo proibido detectado |
| `possible_unredacted_pii` | PII detectada em texto |
| `context_only_source` | Apenas fontes GENI/territorio_contexto |

**Causas de aviso (`status: "warning"`):**
| Condição | Descrição |
|---|---|
| `high_score_single_source` | Score > 70 com apenas 1 fonte |
| `imprecise_location` | Nenhum evento com coords precisas |
| `restricted_source_governance_required` | Fontes restritas presentes |

---

## 9. API REST

Base URL: `http://localhost:8000`

### Health

| Método | Rota | Resposta |
|---|---|---|
| GET | `/health` | `{"status": "ok", "service": "radar-acoes-prioritarias"}` |
| GET | `/` | `{"service": "...", "docs": "/docs"}` |

### Fontes

| Método | Rota | Descrição |
|---|---|---|
| GET | `/sources` | Health de todas as fontes |
| GET | `/sources/catalog` | Catálogo completo com metadados |
| GET | `/sources/fogo-cruzado/occurrences` | Eventos do Fogo Cruzado (requer credenciais) |
| GET | `/sources/isp/baseline?limit=500` | Eventos ISP/CISP |
| POST | `/sources/{source}/normalize` | Normaliza linhas brutas de uma fonte |

### Datasets (upload manual)

| Método | Rota | Body | Descrição |
|---|---|---|---|
| POST | `/datasets/inspect` | `DatasetInspectionRequest` | Inspeciona JSON rows |
| POST | `/datasets/inspect-csv` | `DatasetTextRequest` | Inspeciona CSV texto |
| POST | `/datasets/normalize` | `DatasetInspectionRequest` | Normaliza JSON rows |
| POST | `/datasets/normalize-csv` | `DatasetTextRequest` | Normaliza CSV texto |

### Recomendações

| Método | Rota | Descrição |
|---|---|---|
| POST | `/recommendations?persist=bool` | Pipeline completo a partir de `EventBatch` |
| GET | `/recommendations/demo?persist=bool` | Demo com dados sintéticos |
| GET | `/events/demo` | Apenas os eventos demo (sem pipeline) |
| POST | `/feedback` | Registra feedback humano (`FeedbackRequest`) |

### Agentes

| Método | Rota | Descrição |
|---|---|---|
| GET | `/agents/capabilities` | Capabilities declaradas de todos os agentes |

### Erros operacionais

Todos os erros seguem `OperationalErrorResponse`:
```json
{
  "error": "missing_credentials",
  "detail": "Fogo Cruzado requer credenciais...",
  "source": "fogo_cruzado",
  "retryable": false
}
```

HTTP 424 → credenciais ausentes | HTTP 502 → erro upstream | HTTP 400 → payload inválido | HTTP 404 → fonte não registrada

---

## 10. Persistência SQLite

**Tabelas:**

### `analysis_runs`
| Coluna | Tipo | Índice |
|---|---|---|
| `id` | TEXT PK | sim |
| `kind` | TEXT | sim |
| `created_at` | DATETIME | sim |
| `event_count` | INT | — |
| `recommendation_count` | INT | — |
| `agent_trace_json` | TEXT | — |

### `events`
| Coluna | Tipo | Índice |
|---|---|---|
| `storage_id` | TEXT PK | sim |
| `run_id` | TEXT FK→analysis_runs | sim |
| `event_id` | TEXT | sim |
| `source` | TEXT | sim |
| `access_level` | TEXT | sim |
| `micro_area` | TEXT | sim |
| `observed_at` | DATETIME | sim |
| `payload_json` | TEXT | — |

### `recommendations`
| Coluna | Tipo | Índice |
|---|---|---|
| `storage_id` | TEXT PK | sim |
| `run_id` | TEXT FK→analysis_runs | sim |
| `recommendation_id` | TEXT | sim |
| `micro_area` | TEXT | sim |
| `primary_agency` | TEXT | sim |
| `score` | INT | sim |
| `payload_json` | TEXT | — |

### `feedback`
| Coluna | Tipo | Índice |
|---|---|---|
| `id` | TEXT PK | sim |
| `recommendation_id` | TEXT | sim |
| `run_id` | TEXT | sim |
| `status` | TEXT | sim |
| `reviewer` | TEXT | — |
| `note` | TEXT | — |
| `result_summary` | TEXT | — |
| `metadata_json` | TEXT | — |
| `created_at` | DATETIME | sim |

---

## 11. Privacidade e Redação de PII

**Arquivo:** `backend/app/utils/privacy.py`

### Campos sensíveis detectados automaticamente
Keywords: `cpf`, `rg`, `nome`, `phone`, `telefone`, `celular`, `email`, `placa`, `biometric`, `facial`, `face`, `iris`, `fingerprint`, `dna`, `cnh`

### Padrões regex redatados em texto livre
| Padrão | Exemplo |
|---|---|
| CPF | `123.456.789-00` → `[redacted]` |
| Email | `user@example.com` → `[redacted]` |
| Telefone | `(21) 99999-9999` → `[redacted]` |
| Placa veicular | `ABC-1234` → `[redacted]` |

### Uso
- `PrivateReadyAdapter.normalize_record()` chama `redact_record(record)` antes de qualquer outra operação
- `AuditAgent` verifica `contains_sensitive_pattern()` em action/rationale e bloqueia se positivo
- Logs nunca devem conter payload completo (guardrail arquitetural)

---

## 12. Configuração (env vars)

**Arquivo:** `backend/app/config.py` — `Settings` dataclass frozen

| Env var | Default | Uso |
|---|---|---|
| `RADAR_ENV` | `development` | Ambiente |
| `RADAR_DATABASE_URL` | `sqlite:///backend/data/radar.db` | Banco de dados |
| `RADAR_CORS_ORIGINS` | `http://localhost:5173,...` | CORS (CSV) |
| `FOGO_CRUZADO_BASE_URL` | — | API Fogo Cruzado |
| `FOGO_CRUZADO_EMAIL` | — | Login |
| `FOGO_CRUZADO_PASSWORD` | — | Login |
| `FOGO_CRUZADO_ACCESS_TOKEN` | — | Alternativa a email/password |
| `ISP_BASE_CISP_URL` | (padrão ISP) | Dados CISP |
| `MUNICIPAL_API_BASE_URL` | — | Prefeitura RJ |
| `MUNICIPAL_OAUTH_TOKEN` | — | Token OAuth municipal |
| `RMI_1746_ENDPOINT` | — | Central 1746 |
| `DISQUE_DENUNCIA_DATASET` | — | Dataset Disque Denúncia |
| `CIVITAS_SIGNAL_ENDPOINT` | — | API Civitas |
| `FORCA_MUNICIPAL_EVENTS_ENDPOINT` | — | API Força Municipal |
| `GENI_ARMED_GROUPS_ENDPOINT` | — | API GENI |
| `ANTHROPIC_API_KEY` | — | LLM (reservado, não em uso no score) |
| `RADAR_REQUEST_TIMEOUT` | `20` | Timeout HTTP (segundos) |

Todas as credenciais ficam em `.env` (ignorado no git). Ver `.env.example` para template.

---

## 13. Frontend

**Localização:** `frontend/` — **não alterar neste sprint.**

### Componentes principais

| Componente | Função |
|---|---|
| `App.tsx` | Raiz: estado global, handlers de refresh e feedback |
| `TopBar` | Barra superior com status de fontes |
| `RecommendationQueue` | Lista lateral de recomendações ordenadas por score |
| `RadarMap` | Mapa Leaflet central com pins de eventos |
| `RecommendationDetail` | Painel direito com detalhes da recomendação selecionada |

### Hooks

| Hook | Estado | Ações |
|---|---|---|
| `useRecommendations` | `run`, `loading`, `error`, `selectedId`, `feedbackMap` | `load()`, `select(id)`, `submitFeedback(rec, status, runId)` |
| `useSources` | `sources`, `loading` | `load()` |

### API client

- `GET /recommendations/demo` → `getDemo(): Promise<RecommendationRun>`
- `POST /feedback` → `postFeedback(body): Promise<FeedbackRecord>`
- `GET /sources` → `getSources(): Promise<SourceHealth[]>`

---

## 14. Testes

**Arquivo:** `backend/tests/test_pipeline.py` — **19 testes de integração.**

| Teste | O que valida |
|---|---|
| `test_schema_inference_maps_official_dataset_fields` | Mapeamento de campos, confidence, adapter recomendado |
| `test_schema_inference_flags_pii_and_field_coverage` | Detecção de PII, cobertura de campos |
| `test_camera_metadata_adapter_is_metadata_only` | privacy_mode, sem reconhecimento facial |
| `test_private_adapter_reads_endpoint_env_and_redacts_pii` | Env var de endpoint, redação de PII |
| `test_score_is_deterministic_for_same_events` | Score idêntico em execuções múltiplas |
| `test_entity_extraction_and_recommendation_trace_are_operational` | Entidades extraídas, trace operacional |
| `test_context_only_signal_is_blocked_by_audit` | GENI/territorio_contexto bloqueado pelo audit |
| `test_audit_blocks_missing_provenance` | Evento sem references é bloqueado |
| `test_demo_recommendations_have_provenance_and_audit_trace` | Demo tem provenance e audit trace |
| `test_common_event_contract_accepts_restricted_source_with_provenance` | Contrato CommonEvent válido |
| `test_fastapi_routers_expose_core_backend_contracts` | Rotas /health, /sources, /catalog, /agents, /datasets, /recommendations/demo, CORS |
| `test_recommendation_run_and_feedback_are_persisted` | Persiste AnalysisRunRow, RecommendationRow, FeedbackRow |
| `test_fogo_cruzado_route_returns_operational_error_without_credentials` | HTTP 424 sem credenciais |

---

## 15. Guardrails — Resumo Executivo

Estas regras **nunca podem ser violadas**, independentemente de qualquer alteração:

1. **Score deterministico:** `WEIGHTS` em `scoring.py` são fixos. LLM não pode ser fonte única do score. `test_score_is_deterministic_for_same_events` deve sempre passar.

2. **Provenance obrigatória:** Todo `CommonEvent` deve ter `references` preenchido. `AuditAgent` bloqueia qualquer recomendação sem evidência.

3. **Audit é sempre o último trace:** `RecommendationAgent.build()` sempre appenda o trace do `AuditAgent` por último.

4. **Sem PII em payloads:** `redact_record()` e `redact_text()` são chamados em `PrivateReadyAdapter` antes de qualquer outra operação. Nunca logar payload completo.

5. **Context-only bloqueia:** Fontes GENI ou `territorio_contexto` sozinhas resultam em `AuditAgent` retornando `status: "blocked"`.

6. **Sem linguagem proibida:** Termos como "perfil racial", "pessoa-alvo", "reconhecimento facial positivo" causam bloqueio automático.

7. **Human-in-the-loop:** Toda `action` gerada pelo `RecommendationAgent` é fraseada como recomendação para validação humana, nunca como ordem.

8. **Camera metadata:** `CameraMetadataAdapter` sempre sobrescreve `kind` para `camera_lpr` e inclui disclaimer anti-reconhecimento facial.

---

## 16. Limitações Conhecidas

- `/recommendations/demo` usa dados sintéticos (não refletem operações reais).
- Fogo Cruzado exige JWT; sem credencial, o status é `needs_credentials` e a rota retorna HTTP 424.
- ISP dados são mensais por CISP — sem granularidade de bairro ou horário.
- Recomendações precisam de validação humana antes de qualquer aprendizado institucional.
- Banco SQLite é local e não distribuído (artefato de desenvolvimento).
- GENI e `disque_denuncia` operam em modo `dataset_only` sem endpoint ativo.

---

## 17. Extensão do Sistema

### Adicionar nova fonte
1. Criar adapter em `backend/app/adapters/` herdando de `SourceAdapter`
2. Implementar `health()`, `fetch_events()`, `normalize_record()`
3. Registrar em `services/source_registry.py` com `build_source_registry()`
4. Adicionar entrada em `services/source_catalog.py` com metadados completos
5. Incluir status de health, normalização e ao menos um teste mínimo

### Adicionar nova rota
1. Criar/editar router em `backend/app/api/routers/`
2. Registrar em `backend/app/main.py` dentro de `create_app()`
3. Usar `get_orchestrator()`, `get_sources()` ou `get_storage()` como dependências (DI)

### Alterar pesos do score
- Editar `WEIGHTS` em `domain/scoring.py`
- Verificar que `test_score_is_deterministic_for_same_events` ainda passa
- Documentar a mudança (os pesos são auditáveis por design)

---

*Fim do relatório técnico. Toda alteração deve respeitar os guardrails da Seção 15 e rodar `uv run --python 3.11 pytest backend/tests -q` antes de ser encerrada.*
