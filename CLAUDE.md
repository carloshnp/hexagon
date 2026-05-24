# CIVITAS — Claude Impact Lab Rio

## Projeto / Project
Sistema de segurança pública para o Rio de Janeiro — Claude Impact Lab Hackathon.
Múltiplas abordagens em exploração: dashboard de analytics, grafo de movimento (CIVITAS),
busca por similaridade (FAISS), e visão computacional.

## Stack
- Backend: Python 3.12 + FastAPI + FAISS + NetworkX
- Frontend: React + Vite (a definir)
- Data: ISP-RJ (Instituto de Segurança Pública), dados.rio
- CV: OpenCV + Pillow

## Time / Team (4 pessoas)
- Carlos (Tech Lead): Full-stack, arquitetura geral
- Membro 2 (Backend): FastAPI, FAISS, data pipeline
- Membro 3 (Frontend / Data): React, visualizações
- Membro 4 (Pesquisa + Pitch): Contexto do problema, apresentação

## Regras Globais / Global Rules
- NUNCA expor PII (nomes, CPF, rostos não anonimizados) em APIs ou logs
- Commit messages em Inglês
- Variáveis de ambiente para todas as credenciais — ver `.env.example`
- MVP: funcional > perfeito

## Workspaces
Cada workspace tem seu próprio CLAUDE.md com contexto completo.
Abra o terminal dentro do workspace específico para carregar apenas o contexto necessário.
- `backend/` — FastAPI, FAISS, NetworkX, testes
- `frontend/` — React, Vite, visualizações
- `pitch-research/` — pesquisa, pitch, documentação

## Arquivos Adicionais
- AGENTS.md: definições de sub-agentes especializados
- SOUL.md: identidade e valores do agente
- USER.md: perfil e preferências do time
- SKILLS.md: capacidades disponíveis e como invocar
