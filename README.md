# CIVITAS — Claude Impact Lab Rio

Sistema de segurança pública para o Rio de Janeiro, desenvolvido no Claude Impact Lab Hackathon.

## Overview

CIVITAS integra múltiplas abordagens técnicas para análise de segurança pública:

- **FAISS** — busca por similaridade em ocorrências criminais
- **Graph (NetworkX)** — grafo de movimento e conexões entre eventos
- **Vision (OpenCV)** — visão computacional com anonimização de PII
- **Headless SDK** — orquestração de multi-agentes Claude

## Stack

- **Backend**: Python 3.12 + FastAPI + FAISS + NetworkX
- **Frontend**: React + Vite + TypeScript
- **Data**: ISP-RJ (Instituto de Segurança Pública), dados.rio

## Team

| Role | Focus |
|------|-------|
| Tech Lead | Full-stack, arquitetura geral |
| Backend | FastAPI, FAISS, data pipeline |
| Frontend / Data | React, visualizações |
| Research + Pitch | Contexto do problema, apresentação |

## Docs

- [Guide](docs/index.html) — Guia completo bilíngue (PT-BR/EN)
- [Prototype](docs/prototype/) — Arquitetura técnica, features avançadas
- [Research](docs/research/) — Plano de pesquisa, contexto COMPSTAT Rio
- [Hackathon Info](docs/hackathon-info/) — Guia de agentes, identidade, perfil do time

## Setup

```bash
cp .env.example .env
pip install -r requirements.txt
```

See workspace-specific `CLAUDE.md` files in `backend/`, `frontend/`, and `pitch-research/` for detailed setup.

## Rules

- NEVER expose PII (names, CPF, unblurred faces) in APIs or logs
- Commit messages in English
- Use environment variables for all credentials
