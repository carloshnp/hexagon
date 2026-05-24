# CIVITAS — API & Coleta de Dados

Documento de referência para o front-end e para qualquer integração com o
módulo `hexagon_spatial`.

Conteúdo:
1. [Setup e nova forma de coleta de dados](#1-setup-e-coleta-de-dados)
2. [Como os pipelines interagem](#2-pipelines-internos)
3. [API — Todos os endpoints com I/O](#3-api--endpoints)
4. [Tipos TypeScript prontos](#4-tipos-typescript)
5. [Arquivos estáticos exportados](#5-arquivos-estáticos)
6. [Testes](#6-testes)
7. [Árvore de arquivos](#7-árvore-de-arquivos)

---

## 1. Setup e coleta de dados

### 1.1 Submódulo de dados

Os dados (CSVs, RELINTs `.docx`, shapefile da Força Municipal) vivem em um
repo público separado e entram no projeto como **git submodule**:

```
.gitmodules
  path = perri/hexagon_spatial/claude_impact_lab_compstat_rio
  url  = https://github.com/CompStat-Rio/claude_impact_lab_compstat_rio.git
```

### 1.2 Clone inicial

```bash
git clone https://github.com/carloshnp/hexagon.git
cd hexagon
git submodule update --init --recursive
```

### 1.3 Atualizar os dados

Quando o repo de dados recebe um push novo:

```bash
git submodule update --remote perri/hexagon_spatial/claude_impact_lab_compstat_rio
git add perri/hexagon_spatial/claude_impact_lab_compstat_rio   # fixa o novo commit
git commit -m "data: bump submodule"
```

### 1.4 Estrutura do submódulo

```
claude_impact_lab_compstat_rio/
├── dados/
│   ├── df_ocorrencias_tratado - Extração 1 .csv   # 115.354 ocorrências (ISP-RJ)
│   ├── disk_denuncia.csv                          #  17.850 denúncias (Disque Denúncia)
│   ├── cameras_areas_fm.csv                       #     985 câmeras municipais
│   ├── fatores_urbanos.csv                        #   2.085 fatores urbanos
│   └── Dicionário de dados.xlsx
├── relints/                                       # 8 .docx (Relatórios de Inteligência)
└── sh_area_forca/                                 # shapefile com 8 polígonos
```

### 1.5 Instalar e rodar (manual)

```bash
pip install -r /home/juan/hexagon/requirements.txt
cd /home/juan/hexagon/perri
uvicorn hexagon_spatial.app:app --reload --port 8000
```

- Swagger interativo: `http://localhost:8000/docs`
- ReDoc:               `http://localhost:8000/redoc`

### 1.5.1 Bootstrap automatizado (recomendado)

Para clonar, baixar dados, processar pipelines, gerar todos os JSON/CSV
estáticos e testar — tudo num comando:

```bash
git clone --recurse-submodules https://github.com/carloshnp/hexagon.git
cd hexagon
bash perri/scripts/setup_data.sh --install
```

O script faz 5 etapas (idempotentes):

| Etapa | Ação |
|---|---|
| 1 | `git submodule update --init` (`--pull-latest` puxa HEAD remoto do repo de dados) |
| 2 | Verifica os 7 arquivos críticos + 8 `.docx` |
| 3 | Confere/instala dependências Python (`--install`) |
| 4 | Roda o pipeline para todas as janelas (`null`, `1d`, `3d`, `7d`) → JSON + CSV |
| 5 | Smoke tests (34 asserções via `TestClient`) |

Flags: `--install`, `--pull-latest`, `--skip-tests`, `--skip-spatial`. Detalhes em
[SETUP.md](./SETUP.md).

### 1.6 Onde o código aponta pros dados

Todos os caminhos são relativos ao próprio módulo `hexagon_spatial/`:

| Arquivo Python | Constante | Resolve em |
|---|---|---|
| `loaders.py` | `DATA_DIR` | `claude_impact_lab_compstat_rio/dados/` |
| `relints_parser.py` | `RELINTS_DIR` | `claude_impact_lab_compstat_rio/relints/` |
| `agency_areas.py` | `SHAPEFILE` | `claude_impact_lab_compstat_rio/sh_area_forca/areas_forca_municipal.shp` |

Trocar a fonte de dados = atualizar o submódulo. Não há paths absolutos.

---

## 2. Pipelines internos

```
                          ┌──────────────────────┐
   submódulo de dados ───►│ loaders.py           │──► GeoDataFrames lat/lon
                          │ (4 CSVs)             │
                          └──────────┬───────────┘
                                     │
                                     ▼
                        ┌────────────────────────────┐
                        │ pipeline.py                │
                        │  H3 encode  → agregação    │
                        │  DBSCAN     → hotspots     │
                        │  MCDA       → score_geral  │
                        │  por inst.  → 6 rankings   │
                        └────────────┬───────────────┘
                                     │
                                     ▼
                              GET /spatial/priority-areas

                          ┌──────────────────────┐
   submódulo de dados ───►│ relints_parser.py    │──► dict estruturado
                          │ (8 .docx)            │     por sub-área
                          └──────────┬───────────┘
                                     │
                          ┌──────────▼───────────┐
                          │ agency_areas.py      │
                          │  shapefile           │
                          │  Jaccard match       │
                          └──────────┬───────────┘
                                     │
                                     ▼
                              GET /relints/*

                          ┌──────────────────────┐
                          │ export_csv.py        │──► exports/relints.json
                          │ (gera estáticos)     │──► exports/areas_detalhadas.csv
                          └──────────────────────┘
```

### 2.1 Pipeline espacial (CSVs → MCDA)

`hexagon_spatial/pipeline.py · run_pipeline(top_n, verbose)`

1. **Load** — 4 CSVs viram `GeoDataFrame` em EPSG:4326.
2. **H3 encode** — cada ponto recebe `h3_cell` (resolução 8).
3. **Agregação** — contagem por célula H3.
4. **DBSCAN** — clusteriza hotspots de ocorrências.
5. **Score geral (MCDA)** — fusão ponderada via `scorer.build_score_matrix`.
6. **Score por instituição** — 6 órgãos (PM-RJ, GM-Rio, RioLuz, COMLURB,
   SEOP, CET-Rio), cada um com filtros + pesos próprios.

Tempo médio: **~5,7 s** para 115k ocorrências. Resultado cacheado em memória
(`lru_cache(maxsize=1)`) por valor de `top_n`.

### 2.2 Pipeline RELINTs (DOCX → JSON estruturado)

`hexagon_spatial/relints_parser.py · parse_all_relints()`

1. Lê o `.docx` como zip e extrai `word/document.xml`.
2. Quebra em parágrafos `<w:p>`.
3. Classifica cada parágrafo:
   - **Heading** em CAIXA-ALTA, sem ponto final.
   - **Boilerplate** (contém "RELATÓRIO" + "INTELIGÊNCIA"/"COMPSTAT") → ignora.
   - Primeiro heading válido = título da área.
   - Headings subsequentes (até `CONCLUSÃO`) = sub-áreas.
4. Para cada sub-área, captura descrição + 5 bullets de fatores casados via
   regex contra `FATOR_PATTERNS`.
5. Em `CONCLUSÃO`, separa texto narrativo de bullets "Observa-se necessidade
   de:" e da frase final "Os delitos tendem a...".

**Estado atual:** 8 RELINTs, cada um com 3 sub-áreas × 5 fatores = **15
fatores preenchidos** + 5 necessidades.

### 2.3 Matching agência ↔ RELINT

`hexagon_spatial/agency_areas.py · match_relints_to_areas()`

- Normaliza nomes (sem acento, lower, sem stopwords) em set de tokens.
- Calcula Jaccard `|A ∩ B| / |A ∪ B|`.
- Mede área/perímetro projetando para EPSG:31983 (SIRGAS UTM 23S).

Casamento atual: 7 áreas com score 1.0, 1 com 0.86 (Presidente Vargas).

### 2.4 Export estático

`hexagon_spatial/export_csv.py`

Gera `exports/relints.json` (mesma estrutura da API) e
`exports/areas_detalhadas.csv` (24 linhas, denormalizado).

---

## 3. API — Endpoints

Servidor: `uvicorn hexagon_spatial.app:app`. Base URL local: `http://localhost:8000`.

| Método | Path | Descrição | Cache |
|---|---|---|---|
| GET  | `/`                              | Lista de endpoints              | — |
| GET  | `/spatial/priority-areas`        | Top-N áreas (MCDA + por inst.)  | ✓ em memória |
| POST | `/spatial/priority-areas/refresh`| Limpa cache e recomputa         | — |
| GET  | `/relints/parametros`            | 5 fatores canônicos             | — |
| GET  | `/relints/agencias`              | 8 áreas (sem geometria)         | ✓ (1ª chamada) |
| GET  | `/relints/agencias/{fid}`        | 1 área + GeoJSON + RELINT       | ✓ |
| GET  | `/relints/`                      | 8 RELINTs estruturados          | ✓ |
| GET  | `/relints/{codigo}`              | 1 RELINT por código             | ✓ |

### 3.1 Convenções

- Sempre `application/json; charset=utf-8`.
- Coordenadas em **EPSG:4326** (`lat`/`lon` em graus).
- Erros seguem padrão FastAPI: `{ "detail": "mensagem" }` com HTTP apropriado.
- O cache de pipelines pode levar 5–7 s na 1ª chamada após o boot.

---

### 3.2 `GET /`

Sem parâmetros.

**Resposta 200**
```json
{
  "name": "CIVITAS Spatial API",
  "endpoints": [
    "/spatial/priority-areas",
    "/relints/parametros",
    "/relints/agencias",
    "/relints/agencias/{fid}",
    "/relints/",
    "/relints/{codigo}",
    "/docs"
  ]
}
```

---

### 3.3 `GET /spatial/priority-areas`

**Query params**

| param   | tipo | default | range / valores | descrição |
|---------|------|---------|------------------|-----------|
| `top_n` | int  | 5       | 1–50            | quantas células por ranking |
| `days`  | int  | _omitir_ | **1, 3 ou 7**   | janela temporal a partir da data mais recente do dataset; omita para usar todo o histórico |

Valores inválidos de `days` retornam **422** com mensagem `days deve ser um de [1, 3, 7] ou omitido (todo histórico)`.

A janela é calculada a partir do `max(data)` do próprio dataset de ocorrências
(ver `as_of_date` na resposta) — não a partir de "hoje". Linhas sem data
parseável são descartadas quando o filtro está ativo. Câmeras e fatores
urbanos são infraestrutura e não são filtrados por tempo.

**Resposta 200** — `PipelineResult`:

```json
{
  "elapsed_seconds": 2.04,
  "filtro_dias": 7,
  "as_of_date": "2025-01-02",
  "n_ocorrencias_usadas": 328,
  "n_denuncias_usadas": 71,
  "total_cells_scored": 266,
  "n_hotspot_clusters": 4,
  "score_geral": {
    "descricao": "Fusão ponderada de todas as fontes (MCDA)",
    "top_areas": [
      {
        "h3_cell": "88a8a06a55fffff",
        "lat": -22.911448,
        "lon": -43.186833,
        "score": 57.50,
        "cnt_ocorrencias": 9.0,
        "cnt_denuncias": 1.0,
        "cnt_fatores": 6.0,
        "cnt_cameras": 11.0
      }
    ]
  },
  "scores_por_instituicao": {
    "PM-RJ": {
      "instituicao": "Polícia Militar do Rio de Janeiro",
      "mandato": "Policiamento ostensivo, crimes contra patrimônio e pessoa, armas e drogas",
      "pesos": {
        "ocorrencias": 0.5,
        "denuncias":   0.3,
        "fatores":     0.1,
        "cameras_inv": 0.1
      },
      "total_celulas": 250,
      "top_areas": [
        {
          "h3_cell": "88a8a06a55fffff",
          "lat": -22.911448,
          "lon": -43.186833,
          "score": 71.42,
          "cnt_ocorr": 9.0,
          "cnt_den": 1.0,
          "cnt_fat": 0.0,
          "cnt_cameras": 11.0
        }
      ]
    },
    "GM-Rio":  { ... },
    "RioLuz":  { ... },
    "COMLURB": { ... },
    "SEOP":    { ... },
    "CET-Rio": { ... }
  }
}
```

**Volumes observados por janela** (top_n=10, dataset atual):

| `days` | ocorrências | denúncias | células | clusters | tempo |
|---|---|---|---|---|---|
| _omitir_ | 115.354 | 17.850 | 1.222 | 832 | ~7 s |
| 7 |   328 | 71 | 266 |  4 | ~2 s |
| 3 |    44 | 31 | 151 | _0_ | ~2 s |
| 1 |     1 | 10 | 115 | _0_ | ~2 s |

Janelas pequenas (1d/3d) produzem rankings instáveis — use só para
operações táticas com dados frescos. Para análise estratégica use `days`
omitido ou `days=7`.

**Atenção:** `score_geral.top_areas[].cnt_*` usa nomes longos
(`cnt_ocorrencias`, `cnt_denuncias`, ...). `scores_por_instituicao[].top_areas[].cnt_*`
usa nomes abreviados (`cnt_ocorr`, `cnt_den`, `cnt_fat`, `cnt_cameras`).

**Cache:** a resposta é cacheada por par `(top_n, days)` em memória
(`lru_cache` capacidade 16). Use `POST /spatial/priority-areas/refresh` para
limpar.

---

### 3.4 `POST /spatial/priority-areas/refresh`

Mesmos query params `top_n` e `days` (com mesma validação). Limpa o cache
antes de recomputar.

---

### 3.5 `GET /relints/parametros`

Sem parâmetros.

**Resposta 200** — `Record<FatorKey, string>`:

```json
{
  "retencao_fluxo": "Retenção de fluxo em horários de pico",
  "baixa_visibilidade": "Áreas com baixa visibilidade",
  "obstaculos_urbanos": "Obstáculos urbanos dificultando vigilância",
  "motos_bicicletas": "Circulação intensa de motocicletas e bicicletas",
  "rotas_dispersao": "Múltiplas rotas de dispersão após a prática criminosa"
}
```

---

### 3.6 `GET /relints/agencias`

Sem parâmetros. Resposta enxuta — sem geometria.

**Resposta 200** — `AgencyArea[]` (8 itens):

```json
[
  {
    "fid": 2,
    "nome_area": "Rodoviária - Terminal Gentileza - Estação Leopoldina",
    "centroide": { "lat": -22.9072, "lon": -43.2061 },
    "bbox": {
      "min_lat": -22.9169, "min_lon": -43.2155,
      "max_lat": -22.8943, "max_lon": -43.1953
    },
    "area_km2": 1.4649,
    "perimetro_m": 10994.3,
    "relint_match": {
      "codigo": "RI_010_2026",
      "titulo": "RODOVIÁRIA – TERMINAL GENTILEZA – ESTAÇÃO LEOPOLDINA",
      "score": 1.0
    }
  }
]
```

Fids existentes: **2, 9, 10, 11, 12, 14, 19, 20**.

---

### 3.7 `GET /relints/agencias/{fid}`

**Path param**

| param | tipo | descrição |
|---|---|---|
| `fid` | int | um dos 8 valores válidos |

**Query params**

| param | tipo | default | descrição |
|---|---|---|---|
| `include_geometry` | bool | true | se false, `geometry` vem `{ type: "Polygon", coordinates: [] }` |

**Resposta 200** — `AgencyFull` (estende `AgencyArea`):

```json
{
  "fid": 10,
  "nome_area": "Jardim de Alah",
  "centroide": { "lat": -22.9824, "lon": -22.9824 },
  "bbox": { "min_lat": ..., "min_lon": ..., "max_lat": ..., "max_lon": ... },
  "area_km2": 0.3338,
  "perimetro_m": 3186.5,
  "relint_match": { "codigo": "RI_012_2026", "titulo": "JARDIM DE ALAH", "score": 1.0 },
  "geometry": {
    "type": "Polygon",
    "coordinates": [[[-43.218, -22.980], [-43.218, -22.979], ...]]
  },
  "relint": {
    "codigo": "RI_012_2026",
    "arquivo": "Cópia de RI_012_2026_Jardim_de_Alah.docx",
    "titulo": "JARDIM DE ALAH",
    "introducao": "A presente análise territorial visa identificar fatores urbanos...",
    "n_subareas": 3,
    "subareas": [
      {
        "nome": "PARQUE E ACESSOS INTERNOS",
        "descricao": "A área do Jardim de Alah apresenta grande circulação...",
        "fatores": {
          "retencao_fluxo": "concentração de pedestres e ciclistas nos acessos à orla",
          "baixa_visibilidade": "vegetação densa e nichos formados por tapumes de obras",
          "obstaculos_urbanos": "estruturas de obras criando pontos cegos nos acessos internos",
          "motos_bicicletas": "ciclovia utilizada como rota de fuga após delitos",
          "rotas_dispersao": "saídas para Av. Epitácio Pessoa e Av. Delfim Moreira"
        },
        "fechamento": "A dinâmica criminal observada indica predominância..."
      }
    ],
    "conclusao": {
      "texto": "A área analisada apresenta fatores urbanos...",
      "necessidades": [
        "reforço do patrulhamento preventivo — ...",
        "melhoria da iluminação pública — ..."
      ],
      "fechamento": "Os delitos tendem a ocorrer principalmente..."
    }
  }
}
```

**Resposta 404**
```json
{ "detail": "fid 999 não encontrado" }
```

---

### 3.8 `GET /relints/`

Sem parâmetros.

**Resposta 200** — `Relint[]` (8 itens, mesmo schema de `AgencyFull.relint`).

---

### 3.9 `GET /relints/{codigo}`

**Path param**

| param | tipo | descrição |
|---|---|---|
| `codigo` | string | ex. `RI_010_2026`, `RI_012_2026` |

**Resposta 200** — `Relint` (mesmo schema).

**Resposta 404**
```json
{ "detail": "RELINT RI_999_9999 não encontrado" }
```

---

## 4. Tipos TypeScript

Cole esses tipos no front-end (todos os endpoints estão cobertos):

```ts
// ─── Geometria & metadados de área ─────────────────────────────────────────
export interface Centroide { lat: number; lon: number; }
export interface BBox {
  min_lat: number; min_lon: number;
  max_lat: number; max_lon: number;
}
export interface GeoJSONPolygon {
  type: "Polygon" | "MultiPolygon";
  coordinates: number[][][] | number[][][][];
}

// ─── RELINTs ───────────────────────────────────────────────────────────────
export type FatorKey =
  | "retencao_fluxo"
  | "baixa_visibilidade"
  | "obstaculos_urbanos"
  | "motos_bicicletas"
  | "rotas_dispersao";

export type Fatores = Record<FatorKey, string | null>;

export interface Subarea {
  nome: string;
  descricao: string;
  fatores: Fatores;
  fechamento: string;
}

export interface Conclusao {
  texto: string;
  necessidades: string[];
  fechamento: string;
}

export interface Relint {
  codigo: string;          // ex. "RI_010_2026"
  arquivo: string;
  titulo: string;
  introducao: string;
  n_subareas: number;
  subareas: Subarea[];
  conclusao: Conclusao;
}

export interface RelintMatch {
  codigo: string | null;
  titulo: string | null;
  score: number;           // Jaccard 0–1
}

export interface AgencyArea {
  fid: number;
  nome_area: string;
  centroide: Centroide;
  bbox: BBox;
  area_km2: number;
  perimetro_m: number;
  relint_match: RelintMatch | null;
}

export interface AgencyFull extends AgencyArea {
  geometry: GeoJSONPolygon;
  relint: Relint | null;
}

// ─── Pipeline espacial ─────────────────────────────────────────────────────
export interface GeneralPriorityArea {
  h3_cell: string;
  lat: number;
  lon: number;
  score: number;            // 0–100
  cnt_ocorrencias: number;
  cnt_denuncias: number;
  cnt_fatores: number;
  cnt_cameras: number;
}

export interface InstitutionPriorityArea {
  h3_cell: string;
  lat: number;
  lon: number;
  score: number;            // 0–100
  cnt_ocorr: number;        // nomes abreviados
  cnt_den: number;
  cnt_fat: number;
  cnt_cameras: number;
}

export interface ScoreGeral {
  descricao: string;
  top_areas: GeneralPriorityArea[];
}

export interface InstitutionScore {
  instituicao: string;
  mandato: string;
  pesos: {
    ocorrencias: number;
    denuncias: number;
    fatores: number;
    cameras_inv: number;
  };
  total_celulas: number;
  top_areas: InstitutionPriorityArea[];
}

export type InstitutionId =
  | "PM-RJ" | "GM-Rio" | "RioLuz" | "COMLURB" | "SEOP" | "CET-Rio";

export type DaysWindow = 1 | 3 | 7;

export interface PipelineResult {
  elapsed_seconds: number;
  filtro_dias: DaysWindow | null;        // null = todo histórico
  as_of_date: string | null;             // "YYYY-MM-DD"
  n_ocorrencias_usadas: number;
  n_denuncias_usadas: number;
  total_cells_scored: number;
  n_hotspot_clusters: number;
  score_geral: ScoreGeral;
  scores_por_instituicao: Record<InstitutionId, InstitutionScore>;
}

// ─── Helpers de fetch ──────────────────────────────────────────────────────
const BASE = "http://localhost:8000";

export const api = {
  parametros:    () => fetch(`${BASE}/relints/parametros`).then(r => r.json() as Promise<Record<FatorKey,string>>),
  agencias:      () => fetch(`${BASE}/relints/agencias`).then(r => r.json() as Promise<AgencyArea[]>),
  agencia:       (fid: number, withGeom = true) =>
    fetch(`${BASE}/relints/agencias/${fid}?include_geometry=${withGeom}`).then(r => r.json() as Promise<AgencyFull>),
  relints:       () => fetch(`${BASE}/relints/`).then(r => r.json() as Promise<Relint[]>),
  relint:        (codigo: string) => fetch(`${BASE}/relints/${codigo}`).then(r => r.json() as Promise<Relint>),
  priorityAreas: (topN = 5, days?: DaysWindow) => {
    const qs = new URLSearchParams({ top_n: String(topN) });
    if (days) qs.set("days", String(days));
    return fetch(`${BASE}/spatial/priority-areas?${qs}`).then(r => r.json() as Promise<PipelineResult>);
  },
  refreshPriority: (topN = 5, days?: DaysWindow) => {
    const qs = new URLSearchParams({ top_n: String(topN) });
    if (days) qs.set("days", String(days));
    return fetch(`${BASE}/spatial/priority-areas/refresh?${qs}`, { method: "POST" })
      .then(r => r.json() as Promise<PipelineResult>);
  },
};
```

### Exemplos de uso

```ts
// 1. Pintar mapa com as 8 áreas (sem buscar geometria detalhada)
const areas = await api.agencias();

// 2. Abrir o polígono + RELINT de uma área específica
const ag = await api.agencia(10);          // Jardim de Alah
const fator = ag.relint!.subareas[0].fatores.retencao_fluxo;

// 3. Renderizar hexágonos H3 da PM-RJ — histórico completo
const result = await api.priorityAreas(10);
const pm = result.scores_por_instituicao["PM-RJ"];
pm.top_areas.forEach(a => drawHex(a.h3_cell, a.score));

// 4. Toggle entre janelas 1d/3d/7d
const recente = await api.priorityAreas(10, 7);   // últimos 7 dias
console.log(`as_of=${recente.as_of_date}  usadas=${recente.n_ocorrencias_usadas}`);
```

---

## 5. Arquivos estáticos

Gerados por `python -m hexagon_spatial.export_csv` (ou pelo script de
bootstrap `scripts/setup_data.sh`) em `hexagon_spatial/exports/`:

| Arquivo | Conteúdo | Equivalente API |
|---|---|---|
| `relints.json` | `{ agencias, relints }` | `/relints/` + `/relints/agencias/*` |
| `areas_detalhadas.csv` | 24 linhas (1 por agência × sub-área) | RELINTs achatados |
| `spatial_priority_areas.json` | `PipelineResult` sem filtro | `GET /spatial/priority-areas` |
| `spatial_priority_areas_1d.json` | `PipelineResult` filtrado por 1 dia | `?days=1` |
| `spatial_priority_areas_3d.json` | `PipelineResult` filtrado por 3 dias | `?days=3` |
| `spatial_priority_areas_7d.json` | `PipelineResult` filtrado por 7 dias | `?days=7` |
| `spatial_top_areas.csv` | top-N geral + por instituição, 4 janelas, 1 linha por ranking-posição | — |
| `api_samples/*.json` | payload exato de cada endpoint (gerados para QA do front) | snapshot |

### 5.1 `relints.json`

`{ agencias: AgencyFull[], relints: Relint[] }` — mesmo schema da API,
útil para hospedar estático/CDN.

### 5.2 `areas_detalhadas.csv` — 24 linhas (8 agências × 3 sub-áreas)

| coluna | tipo | descrição |
|---|---|---|
| `fid` | int | id do polígono |
| `nome_area` | string | nome legível da área |
| `area_km2` | float | área (SIRGAS UTM 23S) |
| `perimetro_m` | float | perímetro em metros |
| `centroide_lat`, `centroide_lon` | float | centróide EPSG:4326 |
| `bbox_min_lat`, `bbox_min_lon`, `bbox_max_lat`, `bbox_max_lon` | float | bounding box |
| `codigo_relint` | string | ex. `RI_010_2026` |
| `titulo_relint` | string | título em CAPS |
| `match_score` | float | Jaccard 0–1 |
| `subarea_idx` | int | 0..2 |
| `subarea_nome` | string | ex. `ESTAÇÃO LEOPOLDINA` |
| `subarea_descricao` | string | parágrafo narrativo |
| `retencao_fluxo` | string | contexto do fator |
| `baixa_visibilidade` | string | contexto do fator |
| `obstaculos_urbanos` | string | contexto do fator |
| `motos_bicicletas` | string | contexto do fator |
| `rotas_dispersao` | string | contexto do fator |
| `subarea_fechamento` | string | frase "A dinâmica criminal observada..." |
| `conclusao_necessidades` | string | bullets separados por `\|` |

### 5.3 `spatial_top_areas.csv` — 280 linhas (4 janelas × 70 rankings)

| coluna | tipo | descrição |
|---|---|---|
| `janela_dias` | string | `""` (sem filtro), `"1"`, `"3"`, `"7"` |
| `ranking_tipo` | string | `"geral"` ou ID de instituição (`PM-RJ`, `GM-Rio`, etc.) |
| `instituicao` | string | nome longo da instituição (vazio quando `geral`) |
| `pos` | int | 1..N (top_n usado no export = 10) |
| `h3_cell` | string | id da célula H3 (resolução 8) |
| `lat`, `lon` | float | centróide da célula |
| `score` | float | 0–100 |
| `cnt_ocorrencias`, `cnt_denuncias`, `cnt_fatores`, `cnt_cameras` | float | contagens |

> No CSV os nomes de contagem são sempre os longos. Para o ranking geral
> vêm direto do pipeline; para os rankings por instituição os nomes abreviados
> (`cnt_ocorr`, `cnt_den`, `cnt_fat`) são remapeados antes de gravar.

---

## 6. Testes

Rodar todos os endpoints com `fastapi.testclient` (sem subir uvicorn):

```bash
cd /home/juan/hexagon/perri
python -m hexagon_spatial.test_relints_api
```

Cobre 28 asserções em 9 cenários:

- `GET /`
- `GET /relints/parametros`
- `GET /relints/agencias`
- `GET /relints/agencias/{fid}` (sucesso)
- `GET /relints/agencias/999` (404)
- `GET /relints/`
- `GET /relints/{codigo}` (sucesso)
- `GET /relints/RI_999_9999` (404)
- `GET /spatial/priority-areas?top_n=3` (todas as 6 instituições, pesos válidos)

Saída esperada: `=== 0 falhas ===`.

---

## 7. Árvore de arquivos

```
perri/
├── scripts/
│   └── setup_data.sh                    ← bootstrap completo (5 etapas)
└── hexagon_spatial/
    ├── API.md                           ← este documento
    ├── SETUP.md                         ← guia front-end do bootstrap
    ├── INTEGRATION.md                   ← guia inicial (histórico)
    ├── app.py                           ← FastAPI app principal
    ├── api.py                           ← router /spatial (MCDA + days filter)
    ├── relints_api.py                   ← router /relints
    ├── pipeline.py                      ← run_pipeline(top_n, days)
    ├── loaders.py                       ← CSVs do submódulo, filtro por dias
    ├── h3_indexer.py                    ← encode_h3 / aggregate_by_h3
    ├── clustering.py                    ← DBSCAN nas células
    ├── scorer.py                        ← MCDA geral
    ├── institution_scorer.py            ← rankings por mandato
    ├── relints_parser.py                ← .docx → JSON estruturado
    ├── agency_areas.py                  ← shapefile + matching polígono↔RELINT
    ├── export_csv.py                    ← gera todos os arquivos em exports/
    ├── test_relints_api.py              ← 34 asserções via TestClient
    ├── exports/
    │   ├── relints.json
    │   ├── areas_detalhadas.csv
    │   ├── spatial_priority_areas.json          (todo histórico)
    │   ├── spatial_priority_areas_1d.json       (janela 1 dia)
    │   ├── spatial_priority_areas_3d.json       (janela 3 dias)
    │   ├── spatial_priority_areas_7d.json       (janela 7 dias)
    │   ├── spatial_top_areas.csv                (4 janelas × rankings)
    │   └── api_samples/                         (payloads por endpoint)
    └── claude_impact_lab_compstat_rio/  ← git submodule (dados públicos)
        ├── dados/
        ├── relints/
        └── sh_area_forca/
```
