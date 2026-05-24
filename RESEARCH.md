# Deep Research — CompStat Rio / Inteligência Territorial
**Hackathon Claude Impact Lab Rio — 2026-05-24**
*5 agentes de pesquisa paralelos | ~150 fontes consultadas*

---

## 1. Stack de Processamento Rápido de Dados (< 2h de implementação)

### Pipeline completo com benchmarks reais

```
CSV de ocorrências (100k linhas) → GeoDataFrame → H3 indexing → Spatial join → Score
Tempo total: < 3 minutos de processamento
```

| Etapa | Biblioteca | Tempo (100k registros) | Complexidade |
|---|---|---|---|
| Leitura CSV | pandas | ~1s | trivial |
| Conversão GeoDataFrame | geopandas | <1s | trivial |
| Hash H3 hexagonal | h3-py | 5-10s | baixa |
| Spatial join polígonos | geopandas.sjoin() | 30-90s | baixa |
| Clustering DBSCAN | scikit-learn | 10-30s | baixa |
| KDE heat map | scipy.stats | 30-60s | baixa |
| Multi-source fusion (5 fontes) | pandas + geopandas | 60-180s | média |

### H3 Hexagonal Indexing — o atalho mais importante
- Uber H3 converte lat/lon em IDs hexagonais em **milissegundos**
- Qualquer dataset com coordenadas pode ser "joinado" por ID de célula — sem spatial join custoso
- Resolução configurável: res 8 = ~460m² por célula (ideal para áreas da FM)
- **Implementação**: `h3.geo_to_h3(lat, lon, resolution=8)` → instant join cross-dataset

### Leitura de PDFs (RELINTs)
- **PyMuPDF**: ~5.5s para 1000 páginas → **250x mais barato** que Azure Document Intelligence
- Estratégia: PyMuPDF para texto corrido, pdfplumber para tabelas
- Para hackathon: PyMuPDF sozinho é suficiente

### Algoritmo recomendado para o Bingo Espacial
```
1. H3-encode todos os datasets (ocorrências, câmeras, fatores urbanos, pop. de rua)
2. GroupBy por H3 cell → agregação instantânea
3. Spatial join H3 cells → polígonos FM (point-in-polygon uma vez só)
4. Score MCDA por polígono: soma ponderada dos fatores
5. Rank descendente → top 5 áreas prioritárias
```
Tempo estimado: **< 5 minutos end-to-end** para o volume do hackathon

---

## 2. Pipeline LLM para Documentos Não Estruturados (RELINTs + Disque Denúncia)

### Padrão recomendado: Claude Structured Outputs + PyMuPDF

```
PDF/TXT (RELINT)
  ↓ PyMuPDF (< 10ms/página)
  ↓ Claude API com JSON schema obrigatório
  ↓ Output estruturado garantido (token-level enforcement)
  ↓ Entidades: localização, modus operandi, facção, rota de fuga, horário
```

**Vantagem do Claude vs outros LLMs**: structured outputs com enforcement em nível de token — o modelo fisicamente não pode gerar JSON inválido. OpenAI e outros têm garantias "soft". Para pipeline de inteligência crítica, isso importa.

### Entidades a extrair por documento
```json
{
  "area_fm": "string",
  "modalidade": "roubo_celular | roubo_onibus | ...",
  "modus_operandi": ["string"],
  "horarios_pico": ["HH:MM-HH:MM"],
  "rotas_fuga": ["string"],
  "pontos_receptacao": ["string"],
  "faccao_dominante": "string | null",
  "fatores_urbanos_mencionados": ["string"],
  "nivel_confianca": 0.0-1.0
}
```

### Modus Operandi — técnica adicional
- Algoritmo Apriori para detecção de padrões: tempo + lugar + MO → associações recorrentes
- Dynamic Time Warping para similaridade entre MOs → linkagem de crimes seriais
- Biblioteca: `zeyalt/Crime-Script-Analysis-NLP` (open source, referência acadêmica)

---

## 3. Soluções de Hackathons — O Que Venceu / Impressionou

### Características dos projetos que ganharam
1. **Deployable em 48-72h** — Streamlit, APIs simples, ML direto
2. **Ângulo claro de segurança pública** — não ML por ML
3. **Dados reais e abertos** — ISP Rio, SINESP, FBI UCR
4. **Resolve um gargalo específico** — reconhecimento de padrão, entity matching, detecção em tempo real
5. **Privacy-aware** — de-identificação, privacidade diferencial incorporada
6. **Combina modalidades** — localização + social media + sensores
7. **Profundidade técnica não-óbvia** — grafos, aprendizado federado, IA agêntica
8. **Vantagem comparativa clara** — "mais barato que X, mais rápido que análise manual"

### Projetos notáveis (referência)
- **Rakshekanetra** (Karnataka Police Hackathon): dashboard Streamlit + Google Maps + ML, R²=0.936 para previsão de crimes
- **IndySafetyAssist**: bot Telegram para denúncias de risco + alertas em tempo real
- **Anomaly Detection Model**: localização + boletins de ocorrência + sinais de social media

---

## 4. As 15 Soluções Não-Triviais — Rankeadas por Impacto × Viabilidade em 6h

### TIER 1 — Fazer (alto impacto, rápido de construir)

#### #1 — Multi-Agent LLM Debate para Análise Criminal
**O que faz**: 3-4 agentes Claude com papéis distintos (Analista Criminal, Avaliador Crítico, Especialista em Fatores Urbanos, Forecaster) debatem em rodadas sobre os dados de cada área. Output: consenso com raciocínio explicitado.

**Por que não-trivial**: reasoning emergente multi-turno com perspectivas genuinamente distintas. Produz análises que nenhum agente único produziria.

**Por que 6h é suficiente**: apenas Claude API + prompt engineering + estrutura de turnos. Zero infraestrutura.

**Stack**: Claude API (tool_use para passar JSON entre agentes), structured outputs

**Demo factor**: muito alto — juízes veem "IA pensando em voz alta" sobre um crime real

---

#### #2 — Text-to-SQL / Natural Language Interface ao Banco de Crimes
**O que faz**: analista digita em português → Claude gera SQL → executa na base → resposta em prosa. "Quais são as 3 áreas com mais roubo de celular nas últimas 4 semanas?" → resposta instantânea.

**Por que não-trivial**: schema linking, geração de JOINs complexos, tratamento de ambiguidade, prevenção de SQL injection, graceful error handling.

**Por que 6h é suficiente**: Claude API + schema da base como contexto + whitelist de operações permitidas.

**Stack**: Claude API, SQLAlchemy, SQLite/PostgreSQL

**Demo factor**: alto — democratiza acesso a dados para não-técnicos (o perfil exato dos usuários da prefeitura)

---

#### #3 — Score de Risco Explicável com SHAP Values
**O que faz**: XGBoost treinado nos fatores urbanos + dados históricos → SHAP explica cada predição: "nesta área, iluminação deficiente contribuiu +23pts, população de rua +15pts, tapumes +12pts."

**Por que não-trivial**: balanceia precisão preditiva com interpretabilidade. SHAP force plots visualizam localmente quais fatores pesaram mais por área.

**Por que 6h é suficiente**: XGBoost + SHAP library. Treinar offline em dados sintéticos, demo em dados reais.

**Stack**: XGBoost, shap, matplotlib/plotly

**Demo factor**: muito alto — mostra RACIOCÍNIO do algoritmo, não black box

---

#### #4 — Otimizador de Rota de Patrulha FM (VRP)
**O que faz**: hotspots priorizados → resolve Vehicle Routing Problem → rota ótima de patrulha para cada base (litorânea, oeste, norte), minimizando tempo de deslocamento e maximizando cobertura de risco.

**Por que não-trivial**: VRP com constraints reais (janelas de horário por turno, capacidade por equipe, revisitas obrigatórias a áreas críticas).

**Por que 6h é suficiente**: Google OR-Tools ou PyVRP resolvem VRP em segundos para <100 pontos.

**Stack**: Google OR-Tools, scipy.spatial, folium para visualização da rota

**Demo factor**: alto — saída é mapa com rota traçada e horários. Muito concreto.

---

#### #5 — Interface de Briefing por Voz (Voice-to-Intelligence)
**O que faz**: comandante fala → Whisper transcreve → Claude consulta base + gera análise → resposta em áudio. "Qual a situação da área 7 nesta semana?" → briefing completo em 10 segundos.

**Por que não-trivial**: latência end-to-end, geração segura de SQL a partir de voz (não toda query é válida), integração speech + NLP + dados estruturados + TTS.

**Por que 6h é suficiente**: OpenAI Whisper (gratuito/local), Claude API, ElevenLabs TTS.

**Demo factor**: altíssimo — é o que mais impressiona juízes. "Falar com os dados."

---

### TIER 2 — Considerar (alto impacto, complexidade média)

#### #6 — Síntese de Narrativa Criminal por Área
**O que faz**: dados estruturados de incidentes (quem, o quê, onde, como, horário) → Claude gera narrativa coesa em linguagem natural, pronta para briefing executivo ou relatório técnico.

**Por que não-trivial**: manter precisão factual com dados esparsos/contraditórios, consistência temporal, linguagem adequada ao público.

**Stack**: Claude API + templates Jinja2

**Variação**: adicionar SHAP-style explainability → cada frase do relatório cita qual dado a embasou.

---

#### #7 — Análise de Rede Criminal (Grafo)
**O que faz**: dados de co-ocorrência criminal (mesma área + período + MO similar) → grafo onde nós são incidentes/padrões, arestas são similaridade. Detecta comunidades (organizações) via Louvain clustering. Identifica "hubs" de atividade.

**Por que não-trivial**: dados incompletos/ruidosos, dinâmica temporal (grupos se formam e dissolvem), distinguir colaboração real de coincidência.

**Stack**: NetworkX, community-detection (python-louvain), Pyvis para visualização interativa

---

#### #8 — Detecção de Anomalias em Padrões Criminais
**O que faz**: Isolation Forest ou autoencoder treinado em padrões "normais" de crime por área → detecta desvios súbitos (novo MO, mudança de horário, área nova). Gera alerta automático.

**Por que não-trivial**: crime é inerentemente esparso e desbalanceado. Requer feature engineering cuidadoso.

**Stack**: scikit-learn (IsolationForest), PyTorch (autoencoder simples)

---

#### #9 — Score MCDA Multi-Critério com AHP
**O que faz**: Analytic Hierarchy Process para ponderar os ~20 fatores urbanos com julgamento de especialistas → score de prioridade 0-100 por polígono FM, com justificativa explícita de cada componente.

**Por que não-trivial**: transparente e auditável (importante para accountability do CompStat), permite que gestores ajustem pesos.

**Stack**: numpy/pandas (puro), sem ML necessário

---

#### #10 — Previsão Temporal de Crimes (LSTM/Prophet)
**O que faz**: histórico de roubos por área/hora/dia → prediz próximas 24-72h por área. Modela sazonalidade (feriados, eventos, chuva).

**Por que não-trivial**: crime é esparso → LSTM pode overfitar. Prophet do Facebook é mais robusto para séries esparsas.

**Stack**: Prophet (Facebook, 2h de implementação) ou PyTorch LSTM

---

### TIER 3 — Evitar em 6h (muito complexo ou dados insuficientes)

| Solução | Por que não |
|---|---|
| Graph Neural Network (GNN) | Requer PyTorch-Geometric + feature engineering pesado |
| Agent-Based Simulation (Mesa) | Síntese de população demora dias para calibrar |
| Satellite Change Detection | Precisa de dados pré-processados + GPU + dataset rotulado |
| MARL Patrol Optimization | Framework RL complexo, precisa de simulador de ambiente |
| Causal Inference Deployment Elasticity | Econometria pesada, causalml/DoWhy não trivial |

---

## 5. Algoritmos de Otimização de Patrulha FM

### Recomendação rápida para 6h

**Camada 1 (core)**: MCDA Priority Score → ranking das 22 áreas
- Complexidade: 2/5 — puro numpy/pandas
- Pesos sugeridos: ocorrências (40%) + fatores urbanos (30%) + pop. de rua (15%) + cobertura câmeras (15%)

**Camada 2 (rota)**: VRP estático com Google OR-Tools
- Complexidade: 3/5 — OR-Tools resolve em segundos
- Input: top N hotspots → Output: rota ótima por base FM

**Camada 3 (schedule)**: Prophet para previsão de horário
- Complexidade: 2/5 — treinamento rápido
- Output: "Área 7 tem pico de roubos de celular 18h-21h nas quartas-feiras"

### Algoritmos alternativos (referência)
- **RoSSO**: Python package para patrol optimization com JAX — bem documentado, para SF PD
- **Beat Workload Balancing**: redesign de beats por carga de 911 + densidade criminal
- **Getis-Ord Gi\*** (spatial autocorrelation): identifica clusters estatisticamente significativos

---

## 6. Recomendação para a Equipe de 4 Pessoas — 6h

### Divisão proposta

| Pessoa | Responsabilidade | H1 | H2 | H3 | H4 | H5 | H6 |
|---|---|---|---|---|---|---|---|
| **P1 — Data** | Pipeline + Bingo Engine | Setup dados + H3 | Spatial scoring MCDA | Score final + ranking | Suporte frontend | Integração | Demo |
| **P2 — IA** | Intel Extractor + Briefing | PyMuPDF + Claude extractor | Structured output RELINT | Multi-agent debate | Report generator | Integração | Demo |
| **P3 — Frontend** | Mapa + UI | Leaflet + polígonos FM | Layer toggles | Painel prioridades | Detalhes por área | Briefing view | Demo |
| **P4 — Ops/FM** | Patrol Optimizer + Pitch | OR-Tools VRP setup | Rota FM | Schedule temporal | Visualização rota | Pitch deck | Demo |

### Sequência crítica (dependências)

```
P1: dados normalizados → P2 pode extrair + P3 pode visualizar + P4 pode calcular rotas
P2: intel estruturada → alimenta score MCDA do P1 e relatório final
P3: mapa base → recebe scores do P1 e rotas do P4
P4: hotspots do P1 → calcula rota FM
```

O gargalo está em **P1 ter os dados prontos na H2** — prioridade máxima.

---

## 7. Stack Técnica Final Recomendada

### Backend
```python
# Processamento
pandas, geopandas, h3-py, shapely

# ML / Score
scikit-learn (IsolationForest, DBSCAN)
xgboost + shap
scipy.stats (KDE)

# Otimização
google-or-tools  # VRP patrulha

# LLM Pipeline
anthropic (claude-sonnet-4-6)
pymupdf  # leitura de PDFs (RELINTs)

# API
fastapi, uvicorn
```

### Frontend
```
React 18 + Vite + TypeScript + Tailwind
Leaflet.js  → mapa interativo com polígonos FM
react-leaflet  → componente React para Leaflet
plotly / recharts  → SHAP plots + temporal charts
```

### Dados
```
GeoJSON → polígonos FM (22 áreas)
CSV → ocorrências, fatores urbanos, câmeras
PDF/TXT → RELINTs, Disque Denúncia
```

---

## 8. Arquitetura Final — Síntese

```
┌─────────────────────────────────────────────────────────────────┐
│  INPUT LAYER                                                     │
│  CSV ocorrências + GeoJSON polígonos + PDFs RELINTs             │
│  + Fatores municipais + Pop. rua + Domínio territorial          │
└──────────────────────────┬──────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────────┐
        │                  │                       │
┌───────▼────────┐  ┌──────▼───────┐  ┌──────────▼─────────────┐
│ H3 Spatial     │  │ LLM Intel    │  │ Multi-Agent Debate      │
│ Bingo Engine   │  │ Extractor    │  │ (3 agentes Claude)      │
│                │  │              │  │                         │
│ MCDA Score por │  │ MO, rotas,   │  │ Analista + Crítico +    │
│ polígono (0-100│  │ facção,      │  │ Forecaster → consenso   │
│ + SHAP explain │  │ horários     │  │ fundamentado            │
└───────┬────────┘  └──────┬───────┘  └──────────┬─────────────┘
        │                  │                       │
        └──────────────────┼───────────────────────┘
                           │
              ┌────────────▼──────────────┐
              │  FM PLANNER               │
              │  VRP Patrol Route         │
              │  + Schedule temporal      │
              │  + Responsável por fator  │
              └────────────┬──────────────┘
                           │
              ┌────────────▼──────────────┐
              │  COMPSTAT BRIEFING        │
              │  Relatório executivo      │
              │  pronto p/ reunião c/     │
              │  prefeito + casa civil    │
              └───────────────────────────┘
```

---

## 9. Fontes Principais

- RoSSO Patrol Optimization: arxiv.org/pdf/2309.08742
- VRP Police: mdpi.com/2220-9964/9/3/157
- MCDA Spatial Crime: sciencedirect.com/article/pii/S0143622822002119
- SHAP Crime Explainability: sciencedirect.com/article/abs/pii/S0198971522000333
- Multi-Agent Debate: mindstudio.ai/blog/agent-chat-rooms-multi-agent-debate-claude-code
- Crime NER: researchgate.net/publication/312774503
- H3 Indexing: h3geo.org | uber.github.io/h3-py
- DBSCAN Crime: researchgate.net/publication/347050982
- PyMuPDF benchmark: pymupdf.io
- Claude Structured Outputs: platform.claude.com/docs/en/build-with-claude/structured-outputs
- Rakshekanetra Hackathon: github.com/shreyas27092004/crime-rate-prediction
- ISP Dados Rio: ispdados.rj.gov.br

---

## 10. Rerankeamento pós-critérios (40% impacto real)

Com 40% do peso em impacto real ("a Prefeitura usaria amanhã?"), a ordem muda:

| # | Solução | Impacto | Produto | Eng | Total est. |
|---|---|---|---|---|---|
| 1 | **Bingo Engine + Score MCDA** | ★★★★★ | ★★★★ | ★★★★ | **melhor ROI** |
| 2 | **LLM Pipeline RELINTs** | ★★★★★ | ★★★ | ★★★★★ | diferencial técnico |
| 3 | **CompStat Briefing automático** | ★★★★★ | ★★★★★ | ★★★ | entrega concreta |
| 4 | **FM Patrol Route (VRP)** | ★★★★ | ★★★★ | ★★★★ | operacional |
| 5 | **Score SHAP explicável** | ★★★★ | ★★★★ | ★★★★ | auditável |
| 6 | Text-to-SQL português | ★★★ | ★★★★★ | ★★★ | nice-to-have |
| 7 | Multi-agent debate | ★★ | ★★★ | ★★★★★ | demo, pouco impacto real |
| 8 | Interface de voz | ★★ | ★★★★★ | ★★★ | WOW factor, não workflow |

**Conclusão**: foco total nos 5 primeiros. Voice e debate são enfeites se sobrar tempo.

---

*Documento gerado em 2026-05-24 via pesquisa paralela com 5 agentes especializados.*
