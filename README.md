# CIVITAS — Inteligência de Segurança Pública para o Rio de Janeiro

**Equipe:** Analytica UFRJ

---

## Membros da Equipe

| Nome           | Papel                                                 |
| -------------- | ----------------------------------------------------- |
| Carlos Pereira | Tech Lead — Full-stack, arquitetura geral             |
| Arick Reis     | Backend — FastAPI, scoring de denúncias               |
| Juan Perri     | Backend — Análise espacial, indexação H3              |
| Lucas Passos   | Backend — CompStat, agentes Claude, pipeline de dados |
| Gabriel Feijão | Pesquisa & Pitch — contexto do problema, apresentação |

---

## Tema

Segurança Pública

---

## Resumo

FarolRio é um sistema de inteligência operacional para a Força Municipal do Rio de Janeiro. O sistema agrega dados oficiais de ocorrências (ISP-RJ), denúncias do Disque Denúncia e fatores urbanos para calcular scores de risco nas 8 áreas regionais da cidade. A partir desses scores, agentes Claude geram narrativas estratégicas e relatórios por região — no estilo da metodologia CompStat — auxiliando gestores a priorizar o emprego de força policial com base em evidências, não em intuição.

---

## Arquitetura e Uso do Claude

### Visão Geral

```
Frontend (React + MapLibre)
        │
        ▼
Backend FastAPI (Python 3.12)
        │
        ├── Pipeline de Dados
        │     ├── ISP-RJ (ocorrências)
        │     ├── Disque Denúncia (denúncias pontuadas)
        │     └── Fatores urbanos (densidade, câmeras, transporte)
        │
        ├── Scoring MCDA
        │     ├── Indexação H3 (células hexagonais ~460m²)
        │     ├── Clustering DBSCAN (detecção de hotspots)
        │     └── Normalização min-max por componente
        │
        └── Agentes Claude (Anthropic API)
              ├── Relatório Semanal Estratégico
              ├── Narrativa por Região
              ├── Chat (Q&A sobre o mapa)
              └── Explicação de Score (orchestrator)
```

### Como o Claude foi usado para construir

Claude Code (CLI) foi utilizado ao longo de todo o desenvolvimento do hackathon para:

- Gerar e iterar sobre os módulos de scoring espacial e pipeline de dados
- Escrever os prompts dos agentes
- Produzir os componentes React do dashboard (mapa, sidebar, painel de relatório)
- Depurar integrações entre H3, GeoPandas e a API FastAPI
- Gerar e transformar ipynb em modulos do backend

### Como o Claude atua dentro da aplicação

Cada endpoint de relatório invoca um agente Claude especializado via Anthropic API:

| Agente               | Função                                                                         |
| -------------------- | ------------------------------------------------------------------------------ |
| `weekly_report`      | Gera o resumo estratégico semanal das 8 regiões com priorização justificada    |
| `regional_narrative` | Produz narrativa profunda por região: contexto, incertezas, ações recomendadas |
| `chat`               | Responde perguntas em linguagem natural sobre dados do mapa                    |
| `orchestrator`       | Explica os fatores que determinaram o score de cada região                     |

**Padrão de fallback:** todos os agentes calculam uma resposta determinística a partir dos dados brutos antes de chamar a API. Se a chamada falhar ou a chave estiver ausente, a aplicação retorna JSON válido de qualquer forma. Claude é aditivo, nunca um ponto de falha.

**Restrições éticas incorporadas nos prompts:**

- Proibido reconhecimento facial, leitura de placas ou perfilamento individual
- Nunca inventar números ou scores
- Sempre citar região e evidências; admitir lacunas quando o contexto não permite resposta

---

## Links

- **Aplicação:** _em breve_
- **Vídeo demo:** _em breve_

---

## Como Rodar Localmente

```bash
# Backend
cd backend/Lucas
pip install -r ../../requirements.txt
uvicorn app:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev   # http://localhost:5173
```

Crie um arquivo `.env` na raiz com base em `.env.example` e adicione sua `ANTHROPIC_API_KEY`.

---

## Dados

https://github.com/CompStat-Rio/claude_impact_lab_compstat_rio
