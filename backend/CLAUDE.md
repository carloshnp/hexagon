# CIVITAS — Backend Workspace

## Contexto / Context
Backend FastAPI + FAISS + NetworkX para análise de segurança pública do Rio.
Dados do ISP-RJ (Instituto de Segurança Pública). Sistema CIVITAS.

## Stack
- Python 3.12 + FastAPI + Uvicorn
- FAISS (busca por similaridade / similarity search)
- NetworkX + PyVis (análise e visualização de grafos)
- OpenCV + Pillow (visão computacional, detecção/anonimização de rostos)
- Pandas + GeoPandas (análise de dados geoespaciais)
- Pytest (testes)

## Estrutura / Structure
- `research/backend/` — código exploratório do backend
- `research/faiss/` — índice FAISS (civitas_hnsw.index)
- `research/graph/` — análise de grafos (movement_graph.py, advanced_graph.py)
- `research/vision/` — módulo de visão computacional

## Comandos / Commands
```bash
source .venv/bin/activate
uvicorn research.backend.main:app --reload --port 8000
pytest research/
```

## Variáveis de Ambiente / Environment Variables
Ver `.env.example`. Copiar para `.env` e preencher:
- `ANTHROPIC_API_KEY` — para geração de relatórios com Claude
- `ISP_DATA_PATH` — caminho para CSV de dados do ISP-RJ
- `FAISS_INDEX_PATH` — `research/faiss/civitas_hnsw.index`

## Regras / Rules
- NUNCA expor PII (nomes, rostos não anonimizados, CPF) em APIs ou logs
- Borrar rostos (blur) antes de qualquer output de visão computacional
- Usar dados agregados por bairro, não individuais
- Testes para todos os endpoints da API

## Skills Disponíveis (deste workspace)
- `/networkx` — análise de grafos
- `/geopandas` — dados geoespaciais
- `/matplotlib` — visualizações
- `/seaborn` — visualizações estatísticas
- `/statistical-analysis` — análise de dados ISP-RJ
- `/exploratory-data-analysis` — EDA inicial
- `/scikit-learn` — anomaly detection
