# CIVITAS — Planejamento de Produto
**Hackathon Claude Impact Lab Rio — 24/05/2026**

> Status: **ABERTO** — arquitetura será ajustada conforme exploração dos dados reais.

---

## Visão Geral

Sistema de inteligência territorial para segurança pública do Rio de Janeiro. O objetivo central é transformar dados de ocorrências (ISP-RJ, RELINTs, Disque Denúncia) em **relatórios acionáveis para reuniões da prefeitura**, com alta usabilidade e decisão sempre humana.

**Princípio de design:** Tudo deve ser óbvio de usar. Sem jargão técnico na interface. O gestor abre, enxerga, decide.

---

## Contexto Operacional — A Reunião da Prefeitura

Entender como a reunião funciona é o que define o produto. Não estamos fazendo um dashboard genérico — estamos fazendo uma ferramenta para esse momento específico.

### Estrutura da reunião (2h)

| Parte | Duração | Características |
|-------|---------|-----------------|
| **Abertura** | ~30 min | Pública — notícias relevantes, presença da imprensa. **Sem dados sensíveis.** |
| **Parte fechada** | ~90 min | Confidencial — transcrição, encaminhamentos, análise operacional |

### Dois tipos de reunião (modos distintos)

**Reunião A — Planejamento (presente → futuro)**
- Anúncio de nova área de atuação
- Apresentação da operação planejada
- Pergunta central: *"Onde devemos entrar a seguir e por quê?"*

**Reunião B — Avaliação (passado → presente)**
- Avaliação das áreas onde a Força já entrou
- Verificação de patrulhamento efetivo, CEOP
- Pergunta central: *"As ações estão sendo efetivas? O que explica os resultados?"*
- Responder: quem está alocado, quais índices, se estão diminuindo

### Lógica de escolha de área
- 22 áreas priorizadas no total, 9 operando atualmente
- Escolha tem componente política: maior incidência criminal, ordenamento, contexto da área
- Não há sobreposição de dados ainda entre as fontes — RELINTs são a fonte principal hoje
- O sistema precisa dar suporte a essa escolha, não substituí-la

### O que o sistema precisa entregar na reunião
1. **Dashboard ao vivo** — para visualizar dados durante a reunião (parte fechada)
2. **Relatório estático** — gerado antes, levado impresso ou em PDF, consultado durante abertura e fechada
3. **Resposta à pergunta de efetividade** — dados para Reunião B: alocação, índices, tendência

---

## Dados Disponíveis

```
dados/
├── df_ocorrencias_tratado.csv       # Ocorrências criminais (input principal)
├── cameras_areas_fm.csv             # Câmeras nas áreas da Força Municipal
├── disk_denuncia.csv                # Disk Denúncia
├── fatores_urbanos.csv              # Fatores ambientais/urbanos
├── Dicionário de dados.xlsx         # Schema de todos os datasets
└── outros dados/
    ├── CPSR_2020_2022_2024.xlsx     # Censo de Pessoas em Situação de Rua
    └── dominio_territorial.csv      # Domínio territorial (facções)

relints/                             # 8 RELINTs disponíveis (DOCX)
└── RI_010 a RI_017 — áreas específicas: Rodoviária, Botafogo, Campo Grande, etc.

sh_area_forca/
└── areas_forca_municipal.shp        # Polígonos das áreas FM (shapefile pronto)
```

> **Próximo passo crítico:** explorar o `Dicionário de dados.xlsx` e amostrar o `df_ocorrencias_tratado.csv` antes de iniciar qualquer implementação.

---

## Os Três Pilares do MVP

> Estes três pilares formam o núcleo da demo. Tudo o que não está aqui é stretch goal.

### Pilar 1 — H3 Hexagonal Indexing (Bingo Espacial)

Conversão de ocorrências em IDs hexagonais (Uber H3) para análise espacial rápida e cruzamento de datasets sem spatial join custoso.

**O que entrega:**
- Mapa de calor hexagonal por área da cidade
- Score de prioridade por célula H3 (soma ponderada de fatores: volume, tipo, horário, histórico)
- Ranking das top N áreas que precisam de atenção
- Cruzamento com câmeras, iluminação, população em situação de rua (quando disponível)

**Pipeline:**
```
CSVs ISP-RJ → GeoDataFrame → H3 encode (res=8) → GroupBy célula → Score MCDA → Ranking
```

**Fontes de dados:**
- `df_ocorrencias_tratado.csv` — ocorrências criminais (input principal)
- `cameras_areas_fm.csv` — câmeras nas áreas da Força Municipal
- `fatores_urbanos.csv` — fatores ambientais/urbanos
- `disk_denuncia.csv` — Disk Denúncia
- `CPSR_2020_2022_2024.xlsx` — Censo de Pessoas em Situação de Rua
- `dominio_territorial.csv` — domínio territorial (facções)
- `sh_area_forca/areas_forca_municipal.shp` — **polígonos das áreas FM** (shapefile pronto)

**Decisões em aberto:**
- [ ] Resolução H3 a definir após explorar os dados (res 7 ou 8?)
- [ ] Quais fatores entram no score e com qual peso? (ver Dicionário de dados.xlsx)
- [ ] Polígonos de referência: áreas da Força Municipal (shapefile disponível — usar esse)

---

### Pilar 2 — Pipeline de Relatórios Automáticos

Claude gerando relatórios estruturados a partir dos dados processados. O relatório é **estático** (gerado antes da reunião), complementando o dashboard ao vivo.

**Dois modos de relatório, alinhados com os dois tipos de reunião:**

| Relatório | Reunião | Pergunta que responde |
|-----------|---------|----------------------|
| **Relatório de Planejamento** | Reunião A | Onde entrar? Por quê esta área? Qual a operação sugerida? |
| **Relatório de Avaliação** | Reunião B | A ação está sendo efetiva? Quem está alocado? Os índices estão caindo? |

**Formato do output:**
- Claude gera **Markdown** com estrutura semântica (seções, parágrafos linkados)
- Markdown é convertido para **HTML interativo** (ver Pilar de Frontend)
- Claude também gera **JSON estruturado** para o dashboard consumir diretamente

**Fontes de entrada:**
- Ocorrências: `df_ocorrencias_tratado.csv`
- Inteligência textual: `relints/RI_*.docx` (8 RELINTs — áreas específicas do Rio)
- Denúncias: `disk_denuncia.csv`

**Decisões em aberto:**
- [ ] Quais campos do `df_ocorrencias_tratado.csv` mapeiam para cada seção do relatório?
- [ ] Como integrar RELINTs (texto livre) com dados tabulares no mesmo relatório?
- [ ] Relatório de Avaliação precisa de dado de alocação — esse dado existe nos CSVs?

---

### Pilar 3 — Síntese de Narrativa Criminal por Área

Claude lendo os dados de uma área e gerando uma narrativa textual coerente para briefing — o "resumo executivo" de cada zona prioritária. É o texto que aparece no relatório e que pode ser clicado para acionar o mapa.

**O que entrega:**
- Parágrafo de 3-5 linhas por área: *"A área X concentrou Y ocorrências de tipo Z nos últimos 7 dias, com pico às HH:MM. Modus operandi predominante: ..."*
- Extração de entidades estruturadas: MO, horários, rotas, facções (quando presente nos dados)
- Nível de confiança explícito por claim
- JSON de entidades para o frontend consumir nos cards e tooltips

**Pipeline:**
```
Dados da área (H3 cells + RELINT) → Claude API (structured output) → Narrativa (.md) + Entidades (JSON)
```

**Output duplo para o frontend:**
```json
{
  "narrativa_md": "A área da Rodoviária concentrou...",
  "entidades": {
    "area_fm": "FM-010",
    "modalidade_principal": "roubo_celular",
    "horarios_pico": ["07:00-09:00", "17:00-19:00"],
    "tendencia": "alta",
    "nivel_confianca": 0.87
  },
  "cards": {
    "card_1": { "titulo": "Ocorrências", "valor": 142, "variacao": "+18%" },
    "card_2": { "titulo": "Tipo Principal", "valor": "Roubo de Celular" },
    "card_3": { "titulo": "Horário de Pico", "valor": "07h–09h" },
    "detalhes": { ... }
  }
}
```

**Decisões em aberto:**
- [ ] Prompt a calibrar após ver os dados reais
- [ ] Quais entidades estão realmente presentes nos dados (não apenas no RELINT)?
- [ ] Como lidar com áreas com poucos dados (confiança baixa)?

---

## Frontend — Interface para a Reunião

### Design
- **Paleta:** azul e branco da Prefeitura do Rio
- **Estilo:** flat + brutalista — sem gradientes decorativos, tipografia forte, hierarquia clara
- **Premissa:** funciona em projetor de sala de reunião

### Relatório Interativo (feature central)

O relatório não é um PDF estático. É um HTML onde cada seção/parágrafo é clicável e aciona o mapa e os cards ao lado.

**Fluxo de interação:**
```
Usuário clica em parágrafo do relatório
        │
        ▼
Polígono da área correspondente é destacado no mapa
Cards com dados daquela seção aparecem ao lado
Tooltips nos pontos do mapa mostram dados específicos
```

**Layout dos cards (por seção ativa):**
- 3 cards principais (ex: Ocorrências, Tipo Principal, Horário de Pico)
- 1 card de detalhes adicionais (entidades extras, nível de confiança)

**Geração do relatório na demo:**
- Relatórios já carregados (para a demo final — resposta imediata)
- Botão "Gerar novo relatório" como exemplo ao vivo
  - Claude gera o `.md` + JSON de entidades
  - Sistema converte para HTML interativo linkado
  - Dashboard integra automaticamente

**Decisões em aberto:**
- [ ] Qual biblioteca de mapa? (Leaflet já mencionado na arquitetura anterior — manter?)
- [ ] Como fazer o link semântico parágrafo → polígono no HTML gerado? (data attributes? IDs?)
- [ ] O botão de gerar relatório usa Claude Code headless ou API direta?

---

## Fluxo de Dados (Visão Geral)

```
Dados Brutos
  ├── df_ocorrencias_tratado.csv
  ├── relints/RI_*.docx
  ├── disk_denuncia.csv
  └── outros (câmeras, fatores urbanos, domínio territorial)
        │
        ▼
  Ingestão + Normalização
  (Pandas, GeoPandas, python-docx)
        │
        ▼
  H3 Indexing + Score por Área FM      ← Pilar 1
        │
        ├──▶ Claude API
        │      ├── Narrativa .md por área
        │      └── JSON de entidades + cards    ← Pilar 3
        │
        └──▶ Relatório Final (.md → HTML interativo)    ← Pilar 2
                  │
                  ▼
            Frontend (React + Leaflet)
              ├── Dashboard ao vivo (reunião)
              └── Relatório clicável (estático + geração on-demand)
```

---

## Stretch Goals (se sobrar tempo)

### Análise de Rede Criminal (Grafo)
- NetworkX para modelar relações entre ocorrências, locais, MOs
- Rodar em paralelo enquanto os outros pilares estão sendo implementados
- Entrega: visualização de grafo no frontend (opcional para demo)

### Previsão Temporal
- Série temporal simples por área/tipo de crime
- Só faz sentido se os dados tiverem volume e qualidade temporal suficientes
- **Avaliar após explorar os dados reais**

---

## Princípios Não-Negociáveis

- **Decisão sempre humana** — o sistema recomenda, o gestor decide
- **Zero PII exposto** — sem nomes, CPF, rostos não anonimizados em APIs ou logs
- **Provenance obrigatória** — toda recomendação tem rastreabilidade de fonte
- **Linguagem não-imperativa** — "recomendação para validação" nunca "ordem"
- **Parte aberta da reunião** — nenhum dado sensível exibido durante os 30 min de imprensa

---

## Próximos Passos Imediatos

1. **Explorar os dados reais** — schema, volume, qualidade, campos disponíveis (`Dicionário de dados.xlsx`)
2. **Definir resolução H3** e confirmar polígonos das áreas FM como referência
3. **Prototipar pipeline H3 → Score** (Pilar 1, bloqueia os outros dois)
4. **Calibrar prompt de síntese narrativa** com amostra dos dados reais e um RELINT
5. **Definir schema JSON** que o Claude gera e o frontend consome (cards + mapa)
6. **Prototipar relatório interativo** — HTML com data-attributes linkando parágrafo → polígono

---

## Referências Internas

- `docs/research/RESEARCH.md` — pesquisa técnica: H3, FAISS, pipeline LLM, benchmarks
- `docs/prototype/ARQUITETURA_TECNICA_DASHBOARD.md` — arquitetura do Radar de Ações Prioritárias
- `docs/research/COMPSTAT_RIO.md` — contexto do problema: CompStat Rio, segurança pública RJ
