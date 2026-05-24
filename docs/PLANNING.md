# CIVITAS — Planejamento de Produto
**Hackathon Claude Impact Lab Rio — 24/05/2026**

> Status: **ABERTO** — arquitetura será ajustada conforme exploração dos dados reais.

---

## Visão Geral

Sistema de inteligência territorial para segurança pública do Rio de Janeiro. O objetivo central é transformar dados de ocorrências (ISP-RJ, RELINTs, Disque Denúncia) em **relatórios acionáveis para reuniões da prefeitura**, com alta usabilidade e decisão sempre humana.

**Princípio de design:** Tudo deve ser óbvio de usar. Sem jargão técnico na interface. O gestor abre, enxerga, decide.

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

**Fontes de dados disponíveis:**
- `df_ocorrencias_tratado.csv` — ocorrências criminais (input principal)
- `cameras_areas_fm.csv` — câmeras nas áreas da Força Municipal
- `fatores_urbanos.csv` — fatores ambientais/urbanos
- `disk_denuncia.csv` — Disk Denúncia
- `CPSR_2020_2022_2024.xlsx` — Censo de Pessoas em Situação de Rua
- `dominio_territorial.csv` — domínio territorial (facções)
- `sh_area_forca/areas_forca_municipal.shp` — **polígonos das áreas FM** (disponível)

**Decisões em aberto:**
- [ ] Resolução H3 a definir após explorar os dados (res 7 ou 8?)
- [ ] Quais fatores entram no score e com qual peso? (ver Dicionário de dados.xlsx)
- [ ] Polígonos de referência: **áreas da Força Municipal** (shapefile disponível — usar esse)

---

### Pilar 2 — Pipeline de Relatórios Automáticos

Claude gerando relatórios estruturados a partir dos dados processados. Três tipos de relatório, todos prontos para reunião da prefeitura.

**Tipos de relatório:**

| Tipo | Gatilho | Conteúdo |
|------|---------|----------|
| **Relatório de Ocorrência Individual** | Upload de boletim / registro | Resumo, entidades extraídas, área H3, similaridade com casos anteriores |
| **Relatório Integrado (Diário/Semanal/Mensal)** | Agendado ou on-demand | Panorama por área, tendências, variações vs período anterior |
| **Plano de Ação** | A partir do score de áreas | Sugestão de alocação de recursos com rastreabilidade de provenance |

**Fontes de entrada para os relatórios:**
- Ocorrências: `df_ocorrencias_tratado.csv`
- Inteligência textual: `relints/RI_*.docx` (8 RELINTs disponíveis — áreas específicas do Rio)
- Denúncias: `disk_denuncia.csv`

**Decisões em aberto:**
- [ ] Formato de saída: PDF, HTML, ou Markdown exportável?
- [ ] Relatório de plano de ação depende da previsão temporal — avaliar após explorar dados
- [ ] Como integrar RELINTs (texto livre) com dados tabulares no mesmo relatório?

---

### Pilar 3 — Síntese de Narrativa Criminal por Área

Claude lendo os dados de uma área e gerando uma narrativa textual coerente para briefing — o "resumo executivo" de cada zona prioritária.

**O que entrega:**
- Parágrafo de 3-5 linhas por área: "A Zona Sul concentrou X ocorrências de tipo Y nos últimos 7 dias, com pico às HH:MM. Modus operandi predominante: ..."
- Extração de entidades estruturadas: MO, horários, rotas, fações (quando presente)
- Nível de confiança explícito por claim

**Pipeline:**
```
Dados da área (H3 cells) → Claude API (structured output) → Narrativa + JSON de entidades
```

**Decisões em aberto:**
- [ ] Prompt a calibrar após ver os dados reais
- [ ] Quais entidades são relevantes nos nossos dados concretos?
- [ ] Como lidar com áreas com poucos dados (confiança baixa)?

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

## Fluxo de Dados (Visão Geral)

```
Dados Brutos
  ├── CSVs ISP-RJ (ocorrências)
  ├── RELINTs (PDFs de inteligência)
  └── Outros (câmeras, Disque Denúncia)
        │
        ▼
  Ingestão + Normalização
  (Pandas, GeoPandas, PyMuPDF)
        │
        ▼
  H3 Indexing + Score
  (Pilar 1)
        │
        ├──▶ Síntese Narrativa (Claude API)   ← Pilar 3
        │
        └──▶ Pipeline de Relatórios (Claude Code Headless)   ← Pilar 2
                  │
                  ▼
            Output Final
            (PDF / HTML para reunião da prefeitura)
```

---

## Princípios Não-Negociáveis

- **Decisão sempre humana** — o sistema recomenda, o gestor decide
- **Zero PII exposto** — sem nomes, CPF, rostos não anonimizados em APIs ou logs
- **Provenance obrigatória** — toda recomendação tem rastreabilidade de fonte
- **Linguagem não-imperativa** — "recomendação para validação" nunca "ordem"

---

## Próximos Passos Imediatos

1. **Explorar os dados reais** — entender schema, volume, qualidade, campos disponíveis
2. **Definir resolução H3 e polígonos de referência** (depende dos dados)
3. **Prototipar pipeline H3 → Score** (Pilar 1, bloqueia os outros dois)
4. **Calibrar prompt de síntese narrativa** com amostra dos dados reais
5. **Definir formato de output dos relatórios** com o time de frontend

---

## Referências Internas

- `docs/research/RESEARCH.md` — pesquisa técnica: H3, FAISS, pipeline LLM, benchmarks
- `docs/prototype/ARQUITETURA_TECNICA_DASHBOARD.md` — arquitetura do Radar de Ações Prioritárias
- `docs/research/COMPSTAT_RIO.md` — contexto do problema: CompStat Rio, segurança pública RJ
