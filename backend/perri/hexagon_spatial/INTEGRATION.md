# CIVITAS — Integração Front-end · Agências & RELINTs

Este documento descreve, para o time de front-end, como consumir o módulo
`hexagon_spatial`: a API FastAPI, o pipeline `.docx → JSON`, e o CSV
denormalizado pronto para tabela/planilha.

> **TL;DR**
> 1. Suba a API com `uvicorn hexagon_spatial.app:app --reload` (porta 8000).
> 2. Para listar áreas: `GET /relints/agencias`.
> 3. Para detalhar 1 área (com polígono e RELINT inteiro): `GET /relints/agencias/{fid}`.
> 4. Se preferir consumir tudo estático, use os arquivos em `hexagon_spatial/exports/`:
>    `relints.json` (estruturado) e `areas_detalhadas.csv` (achatado).

---

## 1. Visão geral

Existem **8 sub-áreas operacionais da Força Municipal** delimitadas em
`sh_area_forca/areas_forca_municipal.shp`. Para cada uma há um **Relatório de
Inteligência de Área (RELINT)** em `.docx`, contendo descrições por sub-local
e os **5 parâmetros padronizados de vulnerabilidade urbana**.

O módulo:

1. Parseia os 8 `.docx` em JSON estruturado (sem dependência de `python-docx`).
2. Carrega o shapefile, projeta para EPSG:31983 (SIRGAS UTM 23S) para medir
   área/perímetro, e devolve em EPSG:4326 (lat/lon).
3. Casa cada polígono ao seu RELINT por similaridade de nome (Jaccard).
4. Expõe tudo via FastAPI.
5. Permite exportar `relints.json` + `areas_detalhadas.csv` estáticos.

## 2. Os 5 parâmetros estruturados

Toda sub-área de todo RELINT tem os mesmos 5 campos (chave canônica → rótulo):

| chave                  | rótulo |
|------------------------|--------|
| `retencao_fluxo`       | Retenção de fluxo em horários de pico |
| `baixa_visibilidade`   | Áreas com baixa visibilidade |
| `obstaculos_urbanos`   | Obstáculos urbanos dificultando vigilância |
| `motos_bicicletas`     | Circulação intensa de motocicletas e bicicletas |
| `rotas_dispersao`      | Múltiplas rotas de dispersão após a prática criminosa |

O valor associado a cada chave é a **string de contexto** extraída do bullet
do RELINT (texto após o travessão). Exemplo:

```json
"retencao_fluxo": "acessos, embarque, desembarque e passarelas de circulação"
```

## 3. Endpoints

Todos servidos sob o app `hexagon_spatial.app:app`.

### 3.1 `GET /relints/parametros`

Dicionário canônico de fatores. Útil para o front-end montar a UI com os
mesmos rótulos da API.

```json
{
  "retencao_fluxo": "Retenção de fluxo em horários de pico",
  "baixa_visibilidade": "Áreas com baixa visibilidade",
  "obstaculos_urbanos": "Obstáculos urbanos dificultando vigilância",
  "motos_bicicletas": "Circulação intensa de motocicletas e bicicletas",
  "rotas_dispersao": "Múltiplas rotas de dispersão após a prática criminosa"
}
```

### 3.2 `GET /relints/agencias`

Lista as 8 áreas (sem geometria — payload leve, ideal para a tela de lista/mapa
de pontos).

```json
[
  {
    "fid": 2,
    "nome_area": "Rodoviária - Terminal Gentileza - Estação Leopoldina",
    "centroide": { "lat": -22.9072, "lon": -43.2061 },
    "bbox": { "min_lat": -22.9169, "min_lon": -43.2155,
              "max_lat": -22.8943, "max_lon": -43.1953 },
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

### 3.3 `GET /relints/agencias/{fid}`

Detalhe completo de uma área: polígono GeoJSON + RELINT parseado inteiro.
Aceita `?include_geometry=false` se você só quer o RELINT.

```json
{
  "fid": 10,
  "nome_area": "Jardim de Alah",
  "centroide": { "lat": -22.98, "lon": -43.21 },
  "bbox": { "min_lat": -22.98, "min_lon": -43.21,
            "max_lat": -22.97, "max_lon": -43.21 },
  "area_km2": 0.3338,
  "perimetro_m": 3186.5,
  "geometry": { "type": "Polygon", "coordinates": [[[ -43.218, -22.980 ], ...]] },
  "relint_match": { "codigo": "RI_012_2026", "titulo": "JARDIM DE ALAH", "score": 1.0 },
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
        "fechamento": "A dinâmica criminal observada indica..."
      }
    ],
    "conclusao": {
      "texto": "A área analisada apresenta fatores urbanos...",
      "necessidades": [
        "reforço do patrulhamento preventivo — com foco nos fins de semana...",
        "melhoria da iluminação pública — especialmente nas passagens internas..."
      ],
      "fechamento": "Os delitos tendem a ocorrer principalmente..."
    }
  }
}
```

**404** se o `fid` não existir.

### 3.4 `GET /relints/`

Devolve a lista dos 8 RELINTs no formato estruturado acima. Útil quando o
front-end precisa só dos relatórios (sem geometrias).

### 3.5 `GET /relints/{codigo}`

Devolve um RELINT por código (ex.: `RI_010_2026`). **404** se inexistente.

### 3.6 Outros endpoints do módulo

Não fazem parte deste fluxo mas estão no mesmo app:

- `GET /spatial/priority-areas?top_n=5` — top-N de células H3 priorizadas
  por MCDA (cache em memória).
- `POST /spatial/priority-areas/refresh?top_n=5` — recomputa o pipeline.

## 4. Como rodar a API

```bash
# da pasta /home/juan/hexagon/perri/
uvicorn hexagon_spatial.app:app --reload --port 8000
```

- Docs Swagger: `http://localhost:8000/docs`
- Redoc:        `http://localhost:8000/redoc`

## 5. Como o JSON é construído

### 5.1 Mapeamento polígono ↔ RELINT

Arquivo: `hexagon_spatial/agency_areas.py`

1. `load_agency_areas()` lê o shapefile em EPSG:4326.
2. `match_relints_to_areas()`:
   - Para cada polígono, normaliza o `nome_subar` (sem acento, lower, sem
     stopwords como "de", "rua", "av") em um set de tokens.
   - Faz o mesmo com o `titulo` de cada RELINT.
   - Calcula Jaccard `|A ∩ B| / |A ∪ B|` e fica com o melhor.
   - Mede área/perímetro em EPSG:31983 (SIRGAS UTM 23S).
3. `agencies_full_index()` devolve `fid → agência + relint completo` com cache.

Resultado atual do casamento:

```
fid  2  ← RI_010_2026  Rodoviária–Gentileza–Leopoldina      score=1.00
fid  9  ← RI_011_2026  Metrô Botafogo–São Clemente           score=1.00
fid 10  ← RI_012_2026  Jardim de Alah                        score=1.00
fid 11  ← RI_013_2026  Campo Grande Estação–Calçadão         score=1.00
fid 12  ← RI_014_2026  Rio Sul                               score=1.00
fid 14  ← RI_015_2026  Praia Botafogo–Marquês de Abrantes    score=1.00
fid 19  ← RI_016_2026  SFX–Afonso Pena                       score=1.00
fid 20  ← RI_017_2026  Pres. Vargas–Campo Santana–Cinelândia score=0.86
```

### 5.2 Pipeline `.docx → JSON` dos RELINTs

Arquivo: `hexagon_spatial/relints_parser.py`

O `.docx` é apenas um `.zip` contendo `word/document.xml`. O parser:

1. Descompacta com `zipfile` e lê o XML — **sem dependência de `python-docx`**.
2. Quebra o XML em parágrafos `<w:p>...</w:p>` (preserva a ordem do documento).
3. Classifica cada parágrafo por heurística:
   - **Heading**: texto curto, todo em CAIXA-ALTA, sem ponto final.
   - **Boilerplate**: contém "RELATÓRIO" + ("INTELIGÊNCIA" ou "COMPSTAT") —
     ignorado.
   - **Título da área**: primeiro heading válido.
   - **Sub-área**: cada heading subsequente até `CONCLUSÃO`.
4. Para cada sub-área, capta a descrição (parágrafos até "Também foram
   identificados:") e os 5 bullets de fatores, casando cada bullet aos
   5 padrões regex em `FATOR_PATTERNS`.
5. Em `CONCLUSÃO`, separa o texto narrativo dos bullets de
   "Observa-se necessidade de:" e da frase final "Os delitos tendem a...".

Estrutura final de cada RELINT (Pydantic `Relint` em `relints_api.py`):

```
codigo      str          # ex. "RI_010_2026"
arquivo     str          # nome original do .docx
titulo      str          # heading principal em CAPS
introducao  str          # parágrafo "A presente análise..."
n_subareas  int
subareas    list[{
    nome        str,
    descricao   str,
    fatores     dict[chave → string ou null],
    fechamento  str
}]
conclusao   {
    texto         str,
    necessidades  list[str],
    fechamento    str
}
```

### 5.3 Estado validado

Os 8 RELINTs estão sendo parseados com **3 sub-áreas × 5 fatores = 15
fatores** preenchidos cada, e 5 itens em `necessidades`. Os testes em
`test_relints_api.py` cobrem isso.

## 6. CSV denormalizado — `exports/areas_detalhadas.csv`

Gerado por `hexagon_spatial/export_csv.py`:

```bash
cd /home/juan/hexagon/perri
python -m hexagon_spatial.export_csv
```

Saída em `hexagon_spatial/exports/`:
- `relints.json` — payload combinado `{agencias, relints}` (mesma estrutura
  da API, em arquivo).
- `areas_detalhadas.csv` — uma linha por **agência × sub-área**
  (8 × 3 = **24 linhas**).

### 6.1 Schema do CSV

| coluna | tipo | descrição |
|---|---|---|
| `fid` | int | ID do polígono no shapefile |
| `nome_area` | str | Nome legível da sub-área da Força Municipal |
| `area_km2` | float | Área do polígono (SIRGAS UTM 23S) |
| `perimetro_m` | float | Perímetro em metros |
| `centroide_lat` / `centroide_lon` | float | Centróide (EPSG:4326) |
| `bbox_min_lat` / `bbox_min_lon` / `bbox_max_lat` / `bbox_max_lon` | float | Bounding box |
| `codigo_relint` | str | Ex. `RI_010_2026` |
| `titulo_relint` | str | Título em CAPS do RELINT |
| `match_score` | float | Jaccard polígono↔RELINT (0–1) |
| `subarea_idx` | int | 0..2 |
| `subarea_nome` | str | Heading da sub-área (ex. "ESTAÇÃO LEOPOLDINA") |
| `subarea_descricao` | str | Parágrafo narrativo |
| `retencao_fluxo` | str | Contexto do fator 1 |
| `baixa_visibilidade` | str | Contexto do fator 2 |
| `obstaculos_urbanos` | str | Contexto do fator 3 |
| `motos_bicicletas` | str | Contexto do fator 4 |
| `rotas_dispersao` | str | Contexto do fator 5 |
| `subarea_fechamento` | str | Frase "A dinâmica criminal observada..." |
| `conclusao_necessidades` | str | Bullets da conclusão **separados por `\|`** |

### 6.2 Consumo no front-end

- Para uma **tabela** com filtros por fator: parseie o CSV (PapaParse, etc.)
  e exponha as 5 colunas de fatores como facetas.
- Para um **mapa**: prefira a API (`GET /relints/agencias/{fid}`) — o
  GeoJSON do polígono não cabe bem no CSV. O CSV traz só centróide+bbox.
- `conclusao_necessidades` se quebra com `split('|')`.

## 7. Stack & dependências

Já presentes em `requirements.txt`:
- `fastapi`, `pydantic` — API e schemas.
- `geopandas`, `shapely` — shapefile + geometria.
- (zero dependência nova para parsear `.docx` — só `zipfile` + `re` da stdlib.)

## 8. Como testar

```bash
cd /home/juan/hexagon/perri
python -m hexagon_spatial.test_relints_api
```

Roda 23 asserções com `fastapi.testclient` (sem precisar de servidor). Saída
esperada: `=== 0 falhas ===`.

## 9. Estrutura de arquivos relevante

```
hexagon_spatial/
├── app.py                  # FastAPI app principal
├── api.py                  # /spatial (módulo H3/MCDA já existente)
├── relints_api.py          # /relints — router novo
├── relints_parser.py       # .docx → JSON estruturado
├── agency_areas.py         # shapefile + matching polígono↔RELINT
├── export_csv.py           # gera exports/*.json e *.csv
├── test_relints_api.py     # smoke tests via TestClient
├── exports/
│   ├── relints.json
│   └── areas_detalhadas.csv
└── claude_impact_lab_compstat_rio/
    ├── relints/            # 8 arquivos .docx originais
    └── sh_area_forca/      # shapefile das 8 áreas
```
