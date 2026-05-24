# Claude Code Agent Harness — Guia para o Claude Impact Lab Rio
# Claude Code Agent Harness — Guide for Claude Impact Lab Rio

> **Evento / Event:** Claude Impact Lab — Rio de Janeiro  
> **Tema / Theme:** Soluções de Segurança Pública com Claude AI / Public Safety Solutions with Claude AI  
> **Créditos API / API Credits:** $50 por participante / per participant  
> **Entregável / Deliverable:** Repositório GitHub + pitch de demonstração / GitHub repository + demo pitch

---

## Sumário / Table of Contents

1. [Conceitos Fundamentais / Core Concepts](#1-conceitos-fundamentais--core-concepts)
2. [Configurando o Claude Code / Setting Up Claude Code](#2-configurando-o-claude-code--setting-up-claude-code)
3. [Arquivos de Configuração / Configuration Files](#3-arquivos-de-configuração--configuration-files)
4. [Fluxo de Spec Doc / Spec Doc Workflow](#4-fluxo-de-spec-doc--spec-doc-workflow)
5. [Pesquisa com Claude Code / Research with Claude Code](#5-pesquisa-com-claude-code--research-with-claude-code)
6. [Skills, Plugins e MCP Servers](#6-skills-plugins-e-mcp-servers)
7. [Integração com GitHub / GitHub Integration](#7-integração-com-github--github-integration)
8. [Coordenação de Equipe / Team Coordination](#8-coordenação-de-equipe--team-coordination)
9. [Exemplos de Segurança Pública / Public Safety Examples](#9-exemplos-de-segurança-pública--public-safety-examples)

---

## 1. Conceitos Fundamentais / Core Concepts

### 1.1 Modelos / Models

Claude Code usa modelos de IA da Anthropic para processar suas instruções.
Claude Code uses Anthropic AI models to process your instructions.

| Modelo / Model | Velocidade / Speed | Custo / Cost | Melhor para / Best for |
|---|---|---|---|
| `claude-haiku-4-5` | Muito rápido / Very fast | Baixo / Low | Tarefas simples, pesquisa rápida / Simple tasks, quick lookups |
| `claude-sonnet-4-6` | Equilibrado / Balanced | Médio / Medium | Geração de código, análise / Code generation, analysis |
| `claude-opus-4-7` | Mais lento / Slower | Alto / High | Raciocínio complexo, arquitetura / Complex reasoning, architecture |

**Recomendação para o hackathon / Hackathon recommendation:**
- Use **Sonnet** para a maioria das tarefas de geração de código / for most code generation tasks
- Use **Haiku** para pesquisa e tarefas repetitivas / for research and repetitive tasks
- Reserve **Opus** para decisões de arquitetura críticas / for critical architecture decisions

Com $50 em créditos, você tem margem ampla para iterar bastante.
With $50 in credits, you have plenty of room to iterate extensively.

---

### 1.2 Harness

O **harness** é o ambiente de execução que orquestra o trabalho do Claude.
The **harness** is the runtime environment that orchestrates Claude's work.

**Claude Code é o harness.** Quando você executa `claude` no terminal, você está iniciando o harness.
**Claude Code IS the harness.** When you run `claude` in your terminal, you're starting the harness.

O harness gerencia / The harness manages:
- **Contexto de conversa / Conversation context** — mantém o histórico e o estado da sessão / keeps history and session state
- **Ferramentas / Tools** — controla quais ações Claude pode executar (ler arquivos, rodar código, buscar na web) / controls which actions Claude can take (read files, run code, web search)
- **Permissões / Permissions** — define o que é permitido sem aprovação manual / defines what's allowed without manual approval
- **Hooks** — comandos automáticos que rodam antes/depois de ações / automatic commands that run before/after actions
- **Memória / Memory** — persiste informações entre sessões / persists information across sessions
- **Agentes / Agents** — pode criar sub-agentes especializados para tarefas paralelas / can spawn specialized sub-agents for parallel tasks

---

### 1.3 Agentes / Agents

Um **agente** é uma instância do Claude com:
An **agent** is a Claude instance with:

- Um **papel** específico (o que ele faz) / A specific **role** (what it does)
- Um **contexto** (o que ele sabe) / A **context** (what it knows)
- **Ferramentas** (o que ele pode fazer) / **Tools** (what it can do)
- **Regras** (o que ele deve seguir) / **Rules** (what it must follow)

**Tipos de agentes / Agent types:**

```
Orchestrator (Orquestrador)
  └── Plana e delega tarefas / Plans and delegates tasks
  
Researcher (Pesquisador)
  └── Busca dados, APIs, documentação / Searches data, APIs, documentation

Coder (Programador)
  └── Escreve, testa e depura código / Writes, tests, and debugs code

Reviewer (Revisor)
  └── Revisa código e segurança / Reviews code and security

Data Scientist
  └── Analisa dados e gera visualizações / Analyzes data and generates visualizations

Presenter
  └── Gera pitch, slides e documentação / Generates pitch, slides, and documentation
```

Claude Code pode operar como um único agente ou criar múltiplos sub-agentes em paralelo para dividir o trabalho.
Claude Code can operate as a single agent or spawn multiple sub-agents in parallel to divide work.

---

## 2. Configurando o Claude Code / Setting Up Claude Code

> **Assumindo que o CLI já está instalado. / Assuming the CLI is already installed.**

### 2.1 Autenticação / Authentication

```bash
# Opção 1: Login via browser / Option 1: Login via browser
claude auth login

# Opção 2: Definir API key diretamente / Option 2: Set API key directly
export ANTHROPIC_API_KEY="sk-ant-api03-..."

# Persistir no perfil do shell / Persist to shell profile
echo 'export ANTHROPIC_API_KEY="sk-ant-api03-..."' >> ~/.bashrc
# ou para zsh / or for zsh:
echo 'export ANTHROPIC_API_KEY="sk-ant-api03-..."' >> ~/.zshrc

# Verificar se está funcionando / Verify it's working
claude --version
claude "Olá, você está funcionando? / Hello, are you working?"
```

### 2.2 Iniciando um Projeto / Starting a Project

```bash
# Criar e entrar no diretório do projeto / Create and enter project directory
mkdir rio-safety-dashboard && cd rio-safety-dashboard

# Inicializar git
git init

# Iniciar Claude Code (modo interativo) / Start Claude Code (interactive mode)
claude

# Ou enviar um comando diretamente / Or send a command directly
claude "Set up the initial project structure for a FastAPI + React Vite project"
```

### 2.3 Configurações do Projeto / Project Settings

Crie `.claude/settings.json` na raiz do projeto:
Create `.claude/settings.json` at the project root:

```json
{
  "permissions": {
    "allow": [
      "Bash(git *)",
      "Bash(python *)",
      "Bash(pip *)",
      "Bash(npm *)",
      "Bash(make *)",
      "Bash(docker *)",
      "Read(*)",
      "Write(*)",
      "Edit(*)"
    ]
  },
  "model": "claude-sonnet-4-6"
}
```

---

## 2.4 Isolamento de Workspaces / Workspace Isolation

> **Por que isso é crítico para um hackathon de um dia / Why this is critical for a one-day hackathon**

Cada skill, CLAUDE.md e arquivo de configuração que o Claude Code carrega consome **tokens de contexto**. Com apenas $50 em créditos, cada token desperdiçado é uma iteração a menos. Skills de geoespacial carregadas no workspace de pitch, ou contexto de backend aparecendo no workspace de dados, significam tokens queimados sem retorno.

Every skill, CLAUDE.md, and config file Claude Code loads consumes **context tokens**. With only $50 in credits, every wasted token is one fewer iteration. Geospatial skills loaded in the pitch workspace, or backend context appearing in the data workspace, means burned tokens with no return.

**Isolamento total = contexto menor = menos tokens por prompt = mais iterações com $50.**
**Full isolation = smaller context = fewer tokens per prompt = more iterations with $50.**

---

### Como o Claude Code Carrega Configurações / How Claude Code Loads Config

O Claude Code usa uma hierarquia de camadas que se **acumulam** — da mais geral para a mais específica:
Claude Code uses a layered hierarchy that **accumulates** — from most general to most specific:

```
Camada / Layer     Localização / Location             Escopo / Scope
─────────────────  ─────────────────────────────────  ──────────────────────────
Global (usuário)   ~/.claude/settings.json            Todos os projetos
                   ~/.claude/commands/*.md             Todas as sessões
                   ~/.claude/CLAUDE.md                Todas as sessões

Projeto (local)    .claude/settings.json              Este diretório apenas
                   .claude/commands/*.md              Este diretório apenas
                   CLAUDE.md (e pais até git root)    Este projeto
```

**Comportamento importante / Important behavior:**
- Skills em `~/.claude/commands/` são carregadas em TODOS os projetos automaticamente
- CLAUDE.md é lido do diretório atual **e de todas as pastas pai até o git root ou `~`**
- Settings do projeto **sobrescrevem** conflitos com o global (não substituem completamente)

---

### Estrutura de Pastas Recomendada / Recommended Directory Structure

```
hackathon-rio/                     ← Abrir aqui o terminal raiz / Root terminal
├── .claude/
│   ├── settings.json              ← Config mínima raiz (defaults do time)
│   └── commands/                  ← Skills compartilhadas (SOMENTE as essenciais)
│       └── byterover.md
├── CLAUDE.md                      ← Contexto raiz: MINIMAL (só o que todo workspace precisa)
│
├── backend/                       ← Workspace de Backend — rodar `claude` aqui
│   ├── .claude/
│   │   ├── settings.json          ← Config específica de backend
│   │   └── commands/              ← Skills APENAS do backend
│   │       ├── tdd-workflow.md
│   │       ├── data-scientist.md
│   │       └── geopandas-spatial-analysis.md
│   └── CLAUDE.md                  ← Contexto completo de backend + Python
│
├── frontend/                      ← Workspace de Frontend — rodar `claude` aqui
│   ├── .claude/
│   │   ├── settings.json
│   │   └── commands/
│   │       ├── gis-web-mapping.md
│   │       └── artifacts-builder.md
│   └── CLAUDE.md                  ← Contexto completo de frontend + React
│
└── pitch-research/                ← Workspace de Pitch/Pesquisa
    ├── .claude/
    │   ├── settings.json
    │   └── commands/
    │       ├── steve-jobs.md
    │       ├── data-storytelling.md
    │       └── research.md
    └── CLAUDE.md                  ← Contexto de pesquisa e apresentação
```

**Regra fundamental / Fundamental rule:** Cada pessoa do time abre o terminal **dentro do seu workspace** e roda `claude` de lá. Não do diretório raiz.
**Fundamental rule:** Each team member opens their terminal **inside their workspace** and runs `claude` from there. Not from the root directory.

---

### Prevenindo Herança de Configs Globais / Preventing Global Config Inheritance

#### 1. Estabeleça o Limite do Projeto com Git / Establish Project Boundary with Git

O Claude Code pára de ler CLAUDE.md nos diretórios pai quando encontra o **git root**. Inicializar git na raiz do projeto define o limite superior da busca.
Claude Code stops reading parent CLAUDE.md files when it finds the **git root**. Initializing git at the project root defines the upper boundary.

```bash
# Na raiz do hackathon / At the hackathon root
cd hackathon-rio
git init    # ← Isso define o limite para leitura de CLAUDE.md
            # This defines the boundary for CLAUDE.md reading
```

**Resultado / Result:** Quando você roda `claude` em `hackathon-rio/backend/`, ele lê:
- `backend/CLAUDE.md` ✅ (workspace específico)
- `hackathon-rio/CLAUDE.md` ✅ (raiz do projeto — por isso mantenha-o mínimo)
- Qualquer CLAUDE.md acima de `hackathon-rio/` ❌ (bloqueado pelo git root)

#### 2. Não Instale Skills Globalmente / Don't Install Skills Globally

```bash
# ❌ EVITE — skills globais aparecem em TODOS os workspaces
mkdir -p ~/.claude/commands
cp data-scientist.md ~/.claude/commands/    # Vai aparecer no workspace de pitch também!

# ✅ CORRETO — instale no workspace específico
mkdir -p backend/.claude/commands
cp data-scientist.md backend/.claude/commands/    # Só aparece no backend
```

#### 3. Mantenha o `~/.claude/settings.json` Global Mínimo / Keep Global Settings Minimal

O arquivo global deve conter **apenas autenticação**. Todo o resto vai nos workspaces.
The global file should contain **only authentication**. Everything else goes in workspaces.

```json
// ~/.claude/settings.json — MANTER MÍNIMO / KEEP MINIMAL
{
  "model": "claude-sonnet-4-6"
}
```

#### 4. Settings Completos por Workspace / Full Settings per Workspace

Cada workspace define **explicitamente** tudo que precisa — sem depender do global para preencher lacunas.
Each workspace explicitly defines everything it needs — no relying on global to fill gaps.

```json
// backend/.claude/settings.json
{
  "model": "claude-sonnet-4-6",
  "permissions": {
    "allow": [
      "Bash(git *)",
      "Bash(python *)",
      "Bash(pip *)",
      "Bash(pytest *)",
      "Bash(make *)",
      "Read(*)",
      "Write(*)",
      "Edit(*)"
    ],
    "deny": [
      "Bash(rm -rf *)"
    ]
  },
  "env": {
    "WORKSPACE": "backend",
    "PYTHONPATH": "./src"
  }
}
```

```json
// frontend/.claude/settings.json
{
  "model": "claude-sonnet-4-6",
  "permissions": {
    "allow": [
      "Bash(git *)",
      "Bash(npm *)",
      "Bash(npx *)",
      "Bash(node *)",
      "Read(*)",
      "Write(*)",
      "Edit(*)"
    ]
  },
  "env": {
    "WORKSPACE": "frontend"
  }
}
```

```json
// pitch-research/.claude/settings.json
{
  "model": "claude-haiku-4-5",
  "permissions": {
    "allow": [
      "Bash(git *)",
      "Read(*)",
      "Write(*)",
      "Edit(*)"
    ]
  },
  "env": {
    "WORKSPACE": "pitch-research"
  }
}
```

> **Dica de economia de tokens / Token saving tip:** O workspace de pesquisa e pitch pode usar **Haiku** em vez de Sonnet — é muito mais barato para tarefas de escrita e pesquisa.

---

### CLAUDE.md Raiz (Mínimo) / Root CLAUDE.md (Minimal)

O CLAUDE.md da raiz será lido por **todos** os workspaces (por ser o git root). Mantenha-o pequeno.
The root CLAUDE.md will be read by **all** workspaces (being the git root). Keep it small.

```markdown
# Hackathon: Claude Impact Lab Rio

## Projeto / Project
Sistema de análise de segurança pública para o Rio de Janeiro.
Public safety analytics system for Rio de Janeiro.

## Time / Team
- Carlos (Tech Lead), Ana (Backend), Bruno (Frontend), Lívia (Data), Rafael (Pitch)

## Regras Globais / Global Rules
- NUNCA expor PII em APIs, logs ou saídas
- Commit messages em Inglês, comentários em Português
- MVP primeiro — funcional antes de perfeito

## Workspaces
- backend/     → FastAPI + SQLite + análise de dados
- frontend/    → React + Vite + Leaflet
- pitch-research/ → Pesquisa, slides, pitch

## Atenção / Note
Cada workspace tem seu próprio CLAUDE.md com detalhes completos.
Each workspace has its own CLAUDE.md with full details. Use that, not this file.
```

---

### CLAUDE.md de Workspace (Completo) / Workspace CLAUDE.md (Full)

O CLAUDE.md dentro de cada workspace pode ter todo o detalhe necessário — sem medo de poluir outros contextos.

```markdown
# Workspace: Backend

## Contexto Completo
[Descrição detalhada: stack, arquitetura, decisões, endpoints, regras...]

## Stack
Python 3.12 + FastAPI + SQLite + Pandas + GeoPandas

## Comandos
- `make dev`  → uvicorn main:app --reload
- `make test` → pytest -v
- `make lint` → ruff check . && black --check .

## SPEC.md
[Ou inclua diretamente: "Ver SPEC.md para especificação completa."]

## Skills Disponíveis Neste Workspace
- /data-scientist    → análise de dados e ML
- /tdd-workflow     → ciclo RED-GREEN-REFACTOR
- /geopandas-spatial-analysis → análise espacial
```

---

### Regras Práticas do Hackathon / Practical Hackathon Rules

| Regra / Rule | ❌ Errado / Wrong | ✅ Certo / Right |
|---|---|---|
| Instalar skills | `~/.claude/commands/skill.md` | `workspace/.claude/commands/skill.md` |
| Abrir o Claude Code | Da pasta raiz | Do workspace específico |
| Config do modelo | Global para todos | Haiku para pitch, Sonnet para código |
| CLAUDE.md raiz | Detalhado e longo | Mínimo — apenas o essencial global |
| CLAUDE.md de workspace | Genérico | Completo e específico para o workspace |
| MCP servers | Configurados globalmente | Em `.claude/settings.json` do workspace |

---

## 3. Arquivos de Configuração / Configuration Files

> Esses arquivos formam o "DNA" do seu projeto para o Claude Code.
> These files form the "DNA" of your project for Claude Code.

### 3.1 CLAUDE.md — O Cérebro do Projeto / The Project Brain

**O único arquivo lido automaticamente pelo Claude Code. Coloque na raiz do projeto.**
**The ONLY file read automatically by Claude Code. Place at the project root.**

```markdown
# Projeto / Project: Rio Safety Dashboard

## Contexto / Context
Estamos construindo um painel de análise de segurança pública para o Rio de
Janeiro como parte do Claude Impact Lab. O sistema integra dados de ocorrências
policiais de múltiplas fontes para identificar padrões e apoiar decisões.

We are building a public safety analytics dashboard for Rio de Janeiro
as part of the Claude Impact Lab. The system integrates crime data from
multiple sources to identify patterns and support decisions.

## Stack
- Backend: Python 3.12 + FastAPI + PostgreSQL (ou SQLite para MVP)
- Frontend: React 18 + Vite + Tailwind CSS + Leaflet
- Data: Pandas + GeoPandas
- Deploy: Docker + docker-compose

## Comandos / Commands
- `make dev` — Inicia servidores de desenvolvimento / Start dev servers
- `make test` — Roda todos os testes / Run all tests
- `make lint` — Roda linters / Run linters
- `make build` — Build para produção / Build for production

## Time / Team
- 2 Desenvolvedores Backend (foco Python) / Backend Developers (Python focus)
- 1 Desenvolvedor Frontend (React) / Frontend Developer (React)
- 1 Cientista de Dados / Data Scientist
- 1 Pesquisador / UX (não técnico) / Researcher / UX (non-technical)

## Regras / Rules
- Textos para usuário em Português / User-facing text in Portuguese
- NUNCA expor dados pessoais (PII) nas APIs ou logs / NEVER expose PII in APIs or logs
- Usar variáveis de ambiente para credenciais / Use environment variables for credentials
- Escrever testes para todos os endpoints de API / Write tests for all API endpoints
- Hackathon MVP: preferir soluções que funcionem a soluções perfeitas
  Hackathon MVP: prefer working solutions over perfect solutions

## Arquivos Adicionais / Additional Files
- Ver AGENTS.md para definições de sub-agentes
- Ver SOUL.md para diretrizes de personalidade do agente
- Ver USER.md para preferências da equipe
- Ver SPEC.md para a especificação técnica completa
```

---

### 3.2 AGENTS.md — Definindo Especialistas / Defining Specialists

Define os sub-agentes especializados disponíveis no projeto. O orquestrador pode invocar qualquer um deles.
Defines the specialized sub-agents available in the project. The orchestrator can invoke any of them.

```markdown
# Agents

## Orchestrator (Orquestrador)
**Papel / Role:** Planeja a abordagem geral e coordena entre especialistas.
**Quando usar / When to use:** No início de uma nova feature ou tarefa complexa.
**Como invocar / How to invoke:**
"Act as the Orchestrator. Review SPEC.md and create a step-by-step
implementation plan. Break it into tasks for each specialist."

---

## Backend Engineer
**Papel / Role:** Especialista Python/FastAPI para APIs de dados e banco de dados.
**Stack:** FastAPI, SQLAlchemy, Alembic, PostgreSQL/SQLite, Pytest
**Quando usar / When to use:** Endpoints de API, modelos de dados, migrações, lógica de backend.
**Como invocar / How to invoke:**
"Act as the Backend Engineer. Implement the [feature] following the interfaces
in SPEC.md. Include Pytest tests for all endpoints."

---

## Frontend Engineer
**Papel / Role:** Especialista React + Vite para componentes de UI e visualização de dados.
**Stack:** React 18, Vite, Tailwind CSS, Recharts, Leaflet, Axios
**Quando usar / When to use:** Componentes UI, mapas, gráficos, estado da aplicação.
**Como invocar / How to invoke:**
"Act as the Frontend Engineer. Build the [component] per SPEC.md.
Use Tailwind for all styling. No inline styles."

---

## Data Scientist
**Papel / Role:** Análise de dados, visualização e modelagem estatística.
**Stack:** Pandas, GeoPandas, Matplotlib, Seaborn, Scikit-learn
**Quando usar / When to use:** Limpeza de dados, análise de padrões, geração de mapas, modelos preditivos.
**Como invocar / How to invoke:**
"Act as the Data Scientist. Analyze [dataset] and identify [pattern].
Generate a visualization and explain findings in Portuguese."

---

## Researcher
**Papel / Role:** Coleta informações externas, APIs e documentação.
**Quando usar / When to use:** Fontes de dados abertos, documentação de APIs, melhores práticas.
**Como invocar / How to invoke:**
"Act as the Researcher. Find all public APIs for Rio de Janeiro crime data.
For each: URL, format, authentication requirements, limitations, license."

---

## Presenter
**Papel / Role:** Gera pitch, slides e documentação para apresentação.
**Quando usar / When to use:** Preparação da demo, geração de README, slides.
**Como invocar / How to invoke:**
"Act as the Presenter. Generate a pitch outline for our Rio Safety Dashboard.
Audience: Rio city officials and hackathon judges. Include: Problem → Solution
→ Architecture → Demo → Impact → Next Steps."
```

---

### 3.3 SOUL.md — A Identidade do Agente / Agent Identity

Define a personalidade, valores e restrições que moldam como o agente se comporta.
Defines the personality, values, and constraints shaping how the agent behaves.

```markdown
# Agent Soul — Rio Safety Dashboard

## Identidade / Identity
Você é um engenheiro assistente de IA trabalhando numa solução crítica de
segurança pública para o Rio de Janeiro. Você prioriza precisão, transparência
e privacidade em todo o seu trabalho. Temos um prazo apertado — hackathon de
um dia — então você equilibra qualidade com velocidade de entrega.

You are an AI engineer assistant working on a critical public safety solution
for Rio de Janeiro. You prioritize accuracy, transparency, and privacy.
We have a tight deadline — one-day hackathon — so you balance quality with
delivery speed.

## Valores / Values
- **Precisão primeiro / Accuracy first:** Nunca invente dados. Cite todas as fontes.
- **Privacidade por padrão / Privacy by default:** Anonimize dados pessoais em todas as camadas.
- **Clareza / Clarity:** Explique seu raciocínio. Membros não técnicos do time revisarão seu trabalho.
- **Eficiência / Efficiency:** Prefira soluções funcionais a soluções perfeitas num contexto de hackathon.

## Restrições / Constraints
- NUNCA expor PII (nomes, CPF, endereços) em APIs, logs ou respostas
- Usar coordenadas geográficas reais do Rio de Janeiro (latitude: -23.0 a -23.1, longitude: -43.1 a -43.8)
- Atribuir todos os dados à sua fonte
- Se possível, fazer o código funcionar offline (usar dados em cache)

## Estilo de Comunicação / Communication Style
- Explicações em Português / Explanations in Portuguese
- Código em Inglês (variáveis, funções, comentários de código) / Code in English
- Ser conciso — estamos no prazo de um hackathon / Be concise — we're on a hackathon deadline
- Indicar claramente quando algo está fora do escopo do MVP
```

---

### 3.4 USER.md — Perfil do Time / Team Profile

Armazena as preferências do time para que o Claude não precise ser reinstruído a cada sessão.
Stores team preferences so Claude doesn't need to be re-instructed every session.

```markdown
# Team Profile

## Composição do Time / Team Composition
- **Carlos** (Tech Lead): Full-stack, Python + React
- **Ana** (Backend): Especialista Python, pipelines de dados
- **Bruno** (Frontend): React + Vite, UI/UX
- **Lívia** (Data Science): Pandas, GeoPandas, visualizações
- **Rafael** (Pesquisa + Pitch): Não técnico, pesquisa e apresentação

## Preferências / Preferences
- Backend: Python 3.12, FastAPI, SQLite para MVP (migrar para PostgreSQL depois)
- Frontend: React + Vite + Tailwind, sem bibliotecas UI pesadas
- Testes: Pytest para backend, Vitest para frontend
- Formatação: Black para Python, Prettier para JS/TS
- Git: Mensagens de commit em Inglês, nomes de branches em Inglês

## Não Fazer / Do Not
- Sugerir novas dependências sem perguntar primeiro
- Usar JavaScript onde TypeScript está disponível
- Escrever estilos inline (sempre usar classes Tailwind)
- Pular testes para endpoints de API
- Criar abstrações prematuras — estamos num hackathon

## Restrição de Tempo / Time Constraint
Este é um hackathon de um dia. Prefira implementações de MVP a código
perfeito para produção. MVP em 6 horas, polimento nas 2 últimas horas.
```

---

### 3.5 SKILLS.md — Capacidades Disponíveis / Available Capabilities

Documenta quais skills estão instaladas e como invocá-las.
Documents which skills are installed and how to invoke them.

```markdown
# Available Skills

## Skills Nativas / Built-in Skills
| Skill | Comando / Command | Quando usar / When to use |
|-------|-------------------|---------------------------|
| verify | `/verify` | Após implementar uma feature, verificar se funciona |
| run | `/run` | Iniciar o app e tirar screenshot para confirmação |
| code-review | `/code-review` | Revisar mudanças antes de commitar |
| security-review | `/security-review` | Auditoria de segurança antes da demo |
| init | `/init` | Criar CLAUDE.md para um novo projeto |

## Skills Instaladas / Installed Skills
| Skill | Comando / Command | Descrição |
|-------|-------------------|-----------|
| byterover | `brv` | Armazenar e recuperar decisões do projeto |
| data-science | `/data-science` | Análise Pandas + visualizações |
| web-search | `/research` | Pesquisa estilo Feynman na web |
| slides | `/slides` | Gerar outline de slides do pitch |

## Instalando Novas Skills / Installing New Skills
# Ver Seção 6 para instruções detalhadas / See Section 6 for detailed instructions
```

---

## 4. Fluxo de Spec Doc / Spec Doc Workflow

> **A regra de ouro:** Claude Code gera código MELHOR a partir de um spec detalhado do que de um prompt vago.
> **The golden rule:** Claude Code generates BETTER code from a detailed spec than from a vague prompt.

### O Fluxo Completo / The Full Flow

```
Ideia Bruta          Claude Refina       Você Aprova        Código Gerado
Rough Idea     →     Claude Refines  →   You Approve   →   Code Generated
(~10 min)            (SPEC.md draft)     (iterate)          (full project)
```

---

### 4.1 Passo 1: Escreva o Prompt Inicial / Write the Initial Prompt

Use este template para descrever o problema. Seja específico sobre o problema, não a solução.
Use this template to describe the problem. Be specific about the problem, not the solution.

**Template:**
```
Problema:
[Descreva o problema que você está resolvendo]

Usuários:
[Quem vai usar isso?]

Dados disponíveis:
[Que fontes de dados você tem?]

Resultado esperado:
[Como é o sucesso? O que o usuário consegue fazer?]

Stack:
[Tecnologias que você quer usar]

Restrições:
[Tempo, integração, requisitos especiais]
```

**Exemplo para segurança pública / Public safety example:**

```
Problema:
A Secretaria de Segurança Pública do Rio tem dados de ocorrências policiais
em múltiplos sistemas isolados. Analistas precisam integrar esses dados
manualmente, o que é lento e propenso a erros. Não há visibilidade
centralizada de padrões geográficos ou temporais de criminalidade.

Usuários:
Analistas de segurança pública, delegados, gestores municipais.

Dados disponíveis:
- CSVs mensais de ocorrências por delegacia (fornecidos no hackathon)
- Colunas: data, hora, tipo_crime, delegacia, bairro, latitude, longitude
- Dados geográficos de bairros do Rio (GeoJSON público do dados.rio)

Resultado esperado:
Dashboard que exibe mapa de calor de ocorrências por tipo e período,
com filtros por região e tipo de crime. Identifica automaticamente
padrões e anomalias (e.g., bairros com pico acima da média histórica).

Stack: Python + FastAPI (backend), React + Vite + Leaflet (frontend).
Banco: SQLite para MVP.

Restrições:
- Deve funcionar offline com os dados fornecidos no hackathon
- MVP em 6 horas
- Nenhum dado de PII nos dados — apenas dados agregados por bairro
```

---

### 4.2 Passo 2: Peça ao Claude para Gerar o SPEC.md / Ask Claude to Generate SPEC.md

```
Based on the problem description above, generate a comprehensive SPEC.md file.

Include the following sections:
1. Problem Statement (what problem we're solving and why it matters)
2. Solution Overview (what we're building, in plain language)
3. Architecture (ASCII diagram showing components and how they connect)
4. Data Models (schema for all entities)
5. API Interfaces (all endpoints with request/response schemas)
6. Frontend Components (list and describe each React component)
7. Data Pipeline (how CSV data gets loaded and processed)
8. Rules and Constraints (technical and business rules)
9. Out of Scope (what we're NOT building in this MVP)
10. Implementation Order (what to build first, second, third)

Be specific enough that a developer could implement any section
without asking clarifying questions.
```

---

### 4.3 Passo 3: Itere Até Aprovar / Iterate Until Approved

Revise o SPEC.md gerado e dê feedback específico:
Review the generated SPEC.md and give specific feedback:

```
# Feedback examples / Exemplos de feedback:

"Add an endpoint for filtering occurrences by date range."

"The Occurrence data model is missing the latitude and longitude fields."

"Simplify the architecture — we don't need Redis for this MVP.
Remove it and use in-memory caching."

"Add a section for the anomaly detection logic — how exactly does
it calculate 'above average' for an alert?"

"The frontend component list needs a <FilterPanel /> component with
date range picker, crime type selector, and neighborhood dropdown."
```

Continue iterando até o SPEC.md refletir exatamente o que você quer construir.
Keep iterating until the SPEC.md reflects exactly what you want to build.

---

### 4.4 Passo 4: Aprove e Gere o Código / Approve and Generate Code

Quando satisfeito com o SPEC.md:
When satisfied with the SPEC.md:

```
The SPEC.md looks good. I approve it.

Please now implement the full project based on this spec.
Build in this order:

1. Project structure and configuration (Makefile, docker-compose, .env.example)
2. Backend: data models and database initialization
3. Backend: CSV data ingestion pipeline
4. Backend: API endpoints
5. Backend: Pytest tests for all endpoints
6. Frontend: project setup with Vite + Tailwind
7. Frontend: components (MapView, FilterPanel, StatsChart, OccurrenceTable)
8. Frontend: API integration
9. README.md with setup instructions

Commit after completing each numbered step.
```

---

### 4.5 Estrutura do SPEC.md / SPEC.md Structure

Este é o template completo que o Claude deve gerar:
This is the complete template Claude should generate:

```markdown
# SPEC.md — [Project Name]

## 1. Problem Statement
[Clear description of the problem and why it matters]

## 2. Solution Overview
[Plain-language description of what we're building]

## 3. Architecture
[ASCII diagram]
```
Frontend (React + Vite)
    ↕ HTTP/REST
Backend (FastAPI)
    ↕ SQL
Database (SQLite)
    ↑
CSV Ingestion Pipeline
```

## 4. Data Models
```python
class Occurrence:
    id: int
    date: date
    time: time
    crime_type: str
    delegacia: str
    bairro: str
    latitude: float
    longitude: float
```

## 5. API Interfaces
### GET /api/occurrences
Query params: start_date?, end_date?, crime_type?, bairro?
Response: { total: int, data: Occurrence[] }

### GET /api/stats/by-type
Response: { [crime_type: string]: int }

### GET /api/stats/by-neighborhood
Response: { [bairro: string]: { count: int, lat: float, lon: float } }

### GET /api/alerts
Response: Alert[]  # neighborhoods significantly above historical average

## 6. Frontend Components
- <App /> — root component, global state
- <MapView /> — Leaflet map with heatmap layer
- <FilterPanel /> — date range, crime type, neighborhood filters
- <StatsChart /> — bar chart of crimes by type (Recharts)
- <OccurrenceTable /> — paginated data table
- <AlertBanner /> — shows active anomaly alerts

## 7. Data Pipeline
1. On startup, scan /data/*.csv
2. Parse each CSV with Pandas
3. Validate and clean (drop nulls, normalize crime_type strings)
4. Load into SQLite database
5. Build in-memory index for fast filter queries

## 8. Rules and Constraints
- No PII in any API response
- All amounts in metric units
- Dates in ISO 8601 format (YYYY-MM-DD)
- Crime type values normalized to a fixed enum list

## 9. Out of Scope (MVP)
- User authentication / login
- Real-time data feeds
- Mobile responsive design
- Export to PDF/Excel
- Machine learning predictions

## 10. Implementation Order
1. Project scaffolding + config
2. Database models + SQLite init
3. CSV ingestion pipeline
4. API endpoints (stats first, then filtered queries)
5. Frontend setup
6. Map component
7. Filter + chart components
8. Integration + tests
```

---

## 5. Pesquisa com Claude Code / Research with Claude Code

### 5.1 Claude Code como Agente de Pesquisa / Claude Code as Research Agent

Claude Code pode navegar na web, ler documentação e sintetizar informações automaticamente.
Claude Code can browse the web, read documentation, and synthesize information automatically.

**Template de pesquisa / Research prompt template:**
```
Research [topic] for our project. For each finding:
1. Provide the source URL
2. Summarize the key information in Portuguese
3. Note any limitations or caveats
4. Rate relevance to our project (High/Medium/Low)

Compile results in docs/RESEARCH.md.
```

---

### 5.2 Exemplos de Prompts de Pesquisa / Research Prompt Examples

**Encontrando fontes de dados / Finding data sources:**
```
Research all available open data sources for Rio de Janeiro public safety.
Check: dados.rio, data.rio, ISP-RJ (Instituto de Segurança Pública do Rio),
and any other official sources.

For each source, document:
- URL and access method (API, download, scraping)
- Data format and schema (if available)
- Time coverage (years available)
- Update frequency
- Geographic granularity (neighborhood, district, city)
- Authentication requirements
- License terms and any hackathon restrictions

Save to docs/DATA_SOURCES.md
```

**Pesquisa técnica / Technical research:**
```
Research best practices for building crime heatmaps with Leaflet and React.
Find: libraries for heatmap rendering, clustering markers, choropleth maps.
Compare leaflet-heat, react-leaflet, and deck.gl for our use case
(~10,000 data points, real-time filtering, no performance issues on laptop).
Recommend one approach with reasoning.
```

**Contexto do problema / Problem context:**
```
Research the Rio de Janeiro public safety landscape:
- Current crime statistics and trends (2022-2024)
- Key challenges for law enforcement data integration
- Existing government systems and why they fail to share data
- Success stories of data-driven policing in Brazil

This research will inform our pitch. Save to docs/PROBLEM_CONTEXT.md
```

---

### 5.3 Gerando Documentos de Pesquisa / Generating Research Documents

```
Based on your research in DATA_SOURCES.md and PROBLEM_CONTEXT.md,
generate an executive summary for our pitch deck that explains:
1. The scale of the problem (data points, affected population)
2. Why current systems fail
3. How our solution addresses the gap
4. Expected impact (time saved, decisions improved)

Write in Portuguese, max 300 words, suitable for a 2-minute verbal pitch.
Save to docs/PITCH_SUMMARY.md
```

---

## 6. Skills, Plugins e MCP Servers

### 6.1 O Que São Skills / What Are Skills

Skills são capacidades pré-configuradas que você pode invocar com um comando `/nome-da-skill`.
Podem ser nativas do Claude Code, instaladas de repositórios da comunidade, ou criadas por você.
Skills are pre-configured capabilities invoked with a `/skill-name` command.
They can be built into Claude Code, installed from community repos, or created by you.

---

### 6.2 Awesome Claude Code Skills

A comunidade mantém repositórios de skills prontas para instalar:
The community maintains repositories of ready-to-install skills:

- **Awesome Claude Code:** https://github.com/anthropics/awesome-claude-code
- Busque também no GitHub por: `awesome-claude-code-skills`, `claude-code-commands`

**Como instalar uma skill / How to install a skill:**

```bash
# Skills globais (disponíveis em todos os projetos) / Global skills (all projects)
mkdir -p ~/.claude/commands

# Baixar uma skill específica / Download a specific skill
curl -o ~/.claude/commands/research.md \
  https://raw.githubusercontent.com/anthropics/awesome-claude-code/main/skills/research.md

# Skills de projeto (apenas neste projeto) / Project skills (this project only)
mkdir -p .claude/commands
curl -o .claude/commands/data-science.md \
  https://raw.githubusercontent.com/anthropics/awesome-claude-code/main/skills/data-science.md
```

**Verificando skills instaladas / Verifying installed skills:**
```bash
# No terminal Claude Code, digite / In Claude Code terminal, type:
/   # Lista todos os comandos disponíveis / Lists all available commands
```

**Criando sua própria skill / Creating your own skill:**

```markdown
---
name: analyze-crime-data
description: Analyze a crime CSV dataset and generate statistical summary
---

Analyze the crime dataset at the given path using Python/Pandas.
Generate:
1. Summary statistics (total incidents, by type, by neighborhood)
2. Time series chart (incidents per month)
3. Top 10 neighborhoods by incident count
4. Anomaly detection (neighborhoods >2 std devs above mean)

Save analysis to docs/ANALYSIS.md and charts to docs/charts/.
```

Salve em `.claude/commands/analyze-crime-data.md` e invoque com `/analyze-crime-data`.
Save to `.claude/commands/analyze-crime-data.md` and invoke with `/analyze-crime-data`.

---

### 6.3 Skills Nativas / Built-in Skills

Disponíveis em toda instalação do Claude Code / Available in every Claude Code installation:

| Comando / Command | O Que Faz / What It Does | Quando Usar / When to Use |
|---|---|---|
| `/verify` | Roda o app e verifica se a mudança funciona / Runs app, verifies change works | Após implementar uma feature / After implementing a feature |
| `/run` | Inicia o app e tira screenshot / Starts app and screenshots it | Para confirmar UI / To confirm UI |
| `/code-review` | Revisa mudanças staged para bugs / Reviews staged changes for bugs | Antes de commitar / Before committing |
| `/security-review` | Auditoria de segurança das mudanças / Security audit of changes | Antes da demo final / Before final demo |
| `/init` | Gera CLAUDE.md para um novo projeto / Generates CLAUDE.md for a new project | Início de projeto / Project start |

---

### 6.4 MCP Servers

MCP (Model Context Protocol) servers adicionam acesso a ferramentas externas ao Claude Code.
MCP servers add external tool access to Claude Code.

**Configuração / Configuration** (em / in `.claude/settings.json`):

```json
{
  "mcpServers": {
    "google-drive": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/mcp-server-google-drive"]
    },
    "puppeteer": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/mcp-server-puppeteer"]
    }
  }
}
```

**Google Drive MCP — Útil para / Useful for:**
- Ler datasets compartilhados pelos organizadores do hackathon / Reading datasets shared by hackathon organizers
- Salvar relatórios e slides gerados / Saving generated reports and slides

**Puppeteer/Browser MCP — Útil para / Useful for:**
- Screenshot do app em execução / Screenshot of running app
- Web scraping para pesquisa / Web scraping for research
- Testar interações de UI / Testing UI interactions

**Autenticando o Google Drive MCP / Authenticating Google Drive MCP:**
```
# No Claude Code, execute: / In Claude Code, run:
"Please authenticate with Google Drive so we can access shared files."
# Siga o fluxo de autenticação / Follow the authentication flow
```

---

### 6.5 Skills Recomendadas para o Hackathon / Recommended Hackathon Skills

**byterover — Gestão de Conhecimento do Projeto / Project Knowledge Management:**
```bash
# Armazenar uma decisão técnica / Store a technical decision
brv store "Using SQLite instead of PostgreSQL for MVP — faster setup, no Docker needed"

# Armazenar um padrão descoberto / Store a discovered pattern
brv store "Crime data has inconsistent bairro names — normalize with fuzzy matching"

# Recuperar decisões relevantes / Retrieve relevant decisions
brv retrieve "database choice"
brv retrieve "data normalization"
```

**Workflow de Análise de Dados / Data Analysis Workflow:**
```
Analyze the crime dataset at data/ocorrencias.csv:
1. Load with Pandas, show dtypes and sample rows
2. Check for missing values and inconsistencies
3. Identify unique crime types and neighborhoods
4. Plot incident count by month (save to docs/charts/monthly.png)
5. Identify top 10 neighborhoods by total incidents
6. Flag any data quality issues for the team
Save full analysis to docs/ANALYSIS.md
```

**Geração de Pitch / Pitch Generation:**
```
Generate a structured pitch outline for our Rio Safety Dashboard.
Audience: Rio de Janeiro city officials and hackathon judges (mixed technical/non-technical).
Format: 5-minute verbal pitch.
Structure:
1. Hook — the human cost of disconnected data (30 sec)
2. Problem — manual integration, missed patterns (1 min)
3. Solution — our dashboard, live demo (2 min)
4. Impact — time saved, decisions improved (1 min)
5. Next steps — production path, data integration (30 sec)
Save to docs/PITCH.md
```

**Geração de Slides / Slide Generation:**
```
Based on docs/PITCH.md, generate a slide-by-slide outline with:
- Slide title
- 3-5 bullet points of content
- Suggested visual (chart, screenshot, icon)
- Speaker notes

Format as markdown that can be copy-pasted into Google Slides or Canva.
Save to docs/SLIDES.md
```

---

## 7. Integração com GitHub / GitHub Integration

### 7.1 Setup Inicial / Initial Setup

```bash
# Inicializar git no projeto / Initialize git in project
git init

# Criar repositório no GitHub via CLI / Create GitHub repo via CLI
gh repo create rio-safety-dashboard --public --source=. --remote=origin

# Ou conectar a um repo existente / Or connect to existing repo
git remote add origin https://github.com/your-team/rio-safety-dashboard.git
```

**Deixe o Claude Code fazer o scaffold / Let Claude Code scaffold:**
```
Set up the initial project structure for a Python FastAPI + React Vite project.
Include: .gitignore (Python + Node + .env), README.md (placeholder),
docker-compose.yml, Makefile with dev/test/build targets.
Create an initial commit with message "chore: initial project setup".
```

---

### 7.2 Git Workflow com Claude Code / Git Workflow with Claude Code

Claude Code pode executar todas as operações git para você:
Claude Code can handle all git operations for you:

```bash
# Commitar trabalho atual / Commit current work
"Commit all current changes. Write a descriptive commit message explaining
what was implemented (use conventional commits format: feat/fix/chore/docs)."

# Criar branch para uma feature / Create a branch for a feature
"Create a new branch called feature/crime-heatmap and switch to it."

# Criar PR no GitHub / Create a GitHub PR
"Push the current branch and create a GitHub PR.
Title: 'feat: interactive crime heatmap with filtering'
Include: what was implemented, how to test it, screenshots placeholder."

# Gerar README completo / Generate complete README
"Generate a comprehensive README.md including:
- Project overview and problem statement
- Architecture diagram (ASCII)
- Setup instructions (local dev + Docker)
- API documentation (all endpoints)
- Screenshots section (add placeholder text)
- Team credits
- Hackathon context"
```

---

### 7.3 Workflow de Git Recomendado para Times / Recommended Team Git Workflow

```
main (protegido / protected)
  └── develop (branch de integração / integration branch)
        ├── feature/backend-api          (Backend Dev)
        ├── feature/frontend-map         (Frontend Dev)
        ├── feature/data-pipeline        (Data Scientist)
        └── docs/pitch-and-research      (Researcher)
```

**Fluxo de integração / Integration flow:**
```bash
# Cada dev trabalha na sua branch / Each dev works on their branch
git checkout -b feature/backend-api

# Claude Code faz commits incrementais / Claude Code makes incremental commits
"Implement the /api/occurrences endpoint with filtering. Add Pytest tests. Commit."

# Quando pronto, abrir PR para develop / When ready, open PR to develop
"Push feature/backend-api and create a PR to develop branch.
Request review from the tech lead."

# Code review com Claude Code / Code review with Claude Code
"/code-review"  # Roda antes de aprovar o PR / Run before approving PR
```

---

### 7.4 Preparação Final do Repositório / Final Repository Preparation

Antes da demo / Before the demo:

```
1. "/security-review" — Auditar vulnerabilidades antes de tornar público
2. "Generate a comprehensive README.md with setup instructions and screenshots"
3. "Create a DEMO.md with step-by-step demo script for the judges"
4. "Tag the final version: git tag -a v1.0.0-hackathon -m 'Hackathon final submission'"
5. "Push all branches and tags to GitHub"
```

---

## 8. Coordenação de Equipe / Team Coordination

### 8.1 Papéis Recomendados / Recommended Roles

| Pessoa / Person | Papel / Role | Foco no Claude Code / Claude Code Focus |
|---|---|---|
| Tech Lead | Arquiteto / Architect | Escreve CLAUDE.md, SPEC.md, coordena agentes |
| Backend Dev 1 | API Engineer | Endpoints FastAPI, modelos de dados |
| Backend Dev 2 | Data Engineer | Pipeline CSV, análise de dados |
| Frontend Dev | UI Engineer | Componentes React, mapa Leaflet, gráficos |
| Researcher | Research + Pitch | DATA_SOURCES.md, PITCH.md, slides |

---

### 8.2 Agenda do Hackathon / Hackathon Agenda

**Manhã — Planejamento (Horas 1-2) / Morning — Planning (Hours 1-2):**
```
1. Tech Lead escreve o prompt inicial do problema
2. Todo o time junto com Claude itera no SPEC.md (30-45 min)
3. Time revisa e aprova o SPEC.md
4. Tech Lead cria CLAUDE.md, SOUL.md, USER.md com base no SPEC.md
5. Criar repositório GitHub, setup inicial
6. Dividir em workstreams paralelos
```

**Tarde — Construção (Horas 3-7) / Afternoon — Building (Hours 3-7):**
```
Cada pessoa roda sua própria sessão do Claude Code:

Backend Dev 1:
"Act as the Backend Engineer. Implement all API endpoints from SPEC.md.
Include Pytest tests. Commit each endpoint separately."

Backend Dev 2:
"Act as the Data Scientist. Build the CSV ingestion pipeline.
Analyze the data quality and document findings in docs/ANALYSIS.md."

Frontend Dev:
"Act as the Frontend Engineer. Build all components from SPEC.md.
Use Tailwind for all styling. Start with MapView and FilterPanel."

Researcher:
"Act as the Researcher. Research Rio crime data context for our pitch.
Then act as the Presenter and generate PITCH.md and SLIDES.md."
```

**Final — Integração e Demo (Horas 7-8) / End — Integration and Demo (Hours 7-8):**
```
1. Merge de todos os branches para develop
2. "/code-review" na integração
3. "/security-review" antes de tornar público
4. "/run" para screenshot do app funcionando
5. Finalizar PITCH.md e README.md
6. Push final para GitHub
7. "Tag the final submission: git tag v1.0.0-hackathon"
```

---

### 8.3 Dicas para Sessões Multi-Pessoa / Tips for Multi-Person Sessions

- Todos devem ter o mesmo CLAUDE.md, SPEC.md, SOUL.md na cópia local
- `git pull` antes de iniciar uma sessão de Claude Code
- Use byterover para registrar decisões tomadas: `brv store "API usa JWT para auth"`
- Se o SPEC.md mudar, atualize e avise o time via chat
- Cada pessoa pode ter um USER.md pessoal em `~/.claude/PERSONAL.md` para preferências individuais

---

## 9. Exemplos de Segurança Pública / Public Safety Examples

### 9.1 Sistema de Mapa de Calor de Crimes / Crime Heatmap System

**Prompt inicial completo / Complete initial prompt:**

```
Problema:
A Secretaria de Segurança Pública do Rio registra ocorrências em sistemas
isolados por delegacia. Analistas não têm visão consolidada de padrões
geográficos de criminalidade.

Usuários:
Analistas e gestores de segurança pública que precisam identificar padrões
e alocar recursos de policiamento.

Dados:
- CSV de ocorrências: data, hora, tipo_crime, delegacia, bairro, lat, lon
- GeoJSON de bairros do Rio (público, dados.rio)

Resultado esperado:
Painel web com:
- Mapa de calor interativo filtrável por tipo de crime e período
- Ranking dos 10 bairros com mais ocorrências
- Gráfico de tendência mensal
- Alertas automáticos para bairros com picos anômalos

Stack: FastAPI + React + Vite + Leaflet + SQLite
MVP em 6 horas.
```

---

### 9.2 Módulo de Detecção de Anomalias / Anomaly Detection Module

```
Generate an anomaly detection module for crime data.

Algorithm:
1. Load occurrence data for the past 90 days grouped by (bairro, crime_type)
2. For each (bairro, crime_type) pair, calculate:
   - Historical 30-day average (rolling, exclude current week)
   - Standard deviation
   - Current week count
   - Z-score: (current - mean) / std_dev
3. Flag as alert if z-score > 2.0 (significantly above average)
4. Return list of alerts sorted by severity (z-score descending)

Output schema:
{
  "bairro": string,
  "crime_type": string,
  "current_week_count": int,
  "historical_avg": float,
  "z_score": float,
  "severity": "high" | "medium",  # high: z>3, medium: z>2
  "lat": float,
  "lon": float
}

Implement as FastAPI endpoint GET /api/alerts
Include Pytest tests with mock data.
```

---

### 9.3 Pipeline de Dados de Fontes Abertas / Open Data Pipeline

```
Act as the Researcher. Find all public crime data sources for Rio de Janeiro.

Check these sources:
1. dados.rio — Plataforma de Dados Abertos da Prefeitura do Rio
2. isp.rj.gov.br — Instituto de Segurança Pública do Estado do RJ
3. data.rio — Portal de Dados da Cidade do Rio

For each source, document in docs/DATA_SOURCES.md:
- URL
- Available datasets (names and descriptions)
- Data format (CSV, JSON, API, etc.)
- Time coverage (date range of data)
- Update frequency
- Access method (direct download, API key required, etc.)
- License and usage rights
- Relevance to our hackathon project (High/Medium/Low)

Then recommend the best source for hackathon use.
```

---

### 9.4 Script de Demo para os Juízes / Demo Script for Judges

```
Generate a 5-minute demo script for our Rio Safety Dashboard presentation.

Context:
- Audience: Rio city officials and hackathon judges (mixed technical level)
- Our app: crime heatmap dashboard with anomaly alerts
- Time: 5 minutes total (2 min pitch + 3 min live demo)

Script structure:
1. Opening hook (30 sec) — the human cost of slow crime analysis
2. Problem statement (1 min) — manual, siloed, slow
3. Solution demo (3 min):
   - Show the heatmap with real data
   - Apply a filter (show specific crime type in a neighborhood)
   - Show an anomaly alert and explain the algorithm
   - Show the trend chart
4. Impact and closing (30 sec)

Include: what the presenter says AND what they click/show on screen.
Save to docs/DEMO_SCRIPT.md
```

---

## Referências Rápidas / Quick Reference

### Comandos Essenciais / Essential Commands

```bash
# Iniciar Claude Code / Start Claude Code
claude

# Enviar comando direto / Send direct command
claude "Your prompt here"

# Rodar skill nativa / Run built-in skill
# (dentro do Claude Code / inside Claude Code)
/verify
/code-review
/security-review
/run

# byterover
brv store "decision or pattern"
brv retrieve "query"

# Git com Claude Code / Git with Claude Code
"Commit all changes with a descriptive message"
"Create a PR to develop branch"
"Push and create GitHub release"
```

### Prompts de Emergência do Hackathon / Hackathon Emergency Prompts

```bash
# Quando travado num bug / When stuck on a bug
"I'm getting this error: [paste error]. Here's the relevant code: [paste code].
What's wrong and how do I fix it?"

# Quando o tempo está acabando / When running out of time
"We have 1 hour left. The working features are: [list].
What's the minimum I need to do to have a demo-able product?
Prioritize ruthlessly."

# Para gerar testes rapidamente / To generate tests quickly
"Generate Pytest tests for all API endpoints in [file].
Cover: happy path, empty results, invalid params."

# Para debug de dados / For data debugging
"Load data/ocorrencias.csv and show me:
1. First 5 rows
2. All column names and dtypes
3. Missing value counts
4. Unique values in 'tipo_crime' column"
```

---

## 10. Ecossistema Completo de Skills e Plugins / Full Skills & Plugin Ecosystem

> **Seção baseada em pesquisa web de maio de 2026. / Section based on May 2026 web research.**  
> Existem hoje mais de 6.700 skills, 2.500 marketplaces e 840+ MCP servers para o Claude Code.  
> There are currently 6,700+ skills, 2,500 marketplaces, and 840+ MCP servers for Claude Code.

---

### 10.1 Feynman CLI — Pesquisa com Verificação de Fontes / Research with Citation Verification

**Repositório / Repo:** `github.com/companion-inc/feynman`

O Feynman é um agente de pesquisa open-source que roda no terminal e usa 4 sub-agentes especializados para garantir que cada citação seja verificada contra a fonte real — sem links mortos, sem fontes inventadas.
Feynman is an open-source terminal research agent using 4 specialized subagents to ensure every citation is verified against its real source — no dead links, no fabricated sources.

#### O que o torna diferente / What makes it different

Enquanto outros agentes de pesquisa buscam informações e citam, o Feynman **verifica cada URL** contra sua fonte real. O `feynman audit` compara afirmações de papers contra código público real no GitHub — não tem equivalente em nenhuma outra ferramenta.
While other research agents find information and cite, Feynman **verifies every URL** against its real source. `feynman audit` compares paper claims against actual public code on GitHub — there's no equivalent in any other tool.

#### Os 4 Agentes / The 4 Agents

| Agente / Agent | Função / Function |
|---|---|
| **Researcher** | Busca papers (alphaXiv), web, GitHub, documentação. Nunca fabrica fontes. / Searches papers, web, GitHub, docs. Never fabricates sources. |
| **Reviewer** | Simula peer review — identifica afirmações fracas, contradições, lacunas / Simulates peer review — flags weak claims, contradictions, gaps |
| **Writer** | Estrutura os achados em formato de artigo com citações inline / Structures findings as a paper with inline citations |
| **Verifier** | Valida cada URL citada. Links mortos eliminados. Afirmações sem fonte flagadas. / Validates every cited URL. Dead links killed. Unsourced claims flagged. |

#### Comandos Principais / Key Commands

| Comando | O Que Faz / What It Does |
|---|---|
| `/deepresearch` | Investigação multi-agente com pesquisadores em paralelo |
| `/lit` | Revisão de literatura: consenso e discordâncias entre fontes |
| `/audit` | Compara afirmações de papers contra código real no GitHub |
| `/recipe` | Encontra receitas de ML implementáveis com datasets e código |
| `/watch` | Monitoramento recorrente de um tópico de pesquisa |

#### Integração com Claude Code / Claude Code Integration

```bash
# Instalar como skill do Claude Code / Install as Claude Code skill
npx feynman install --target claude-code
# Adiciona skills em .agents/skills/feynman — sem instalar o app completo

# Uso para o hackathon / Hackathon usage:
"Research all available open crime data APIs for Rio de Janeiro.
Verify every URL is live and accessible. Flag any dead links."
```

---

### 10.2 Plugins vs Skills — A Diferença / The Difference

| | Plugin | Skill |
|---|---|---|
| O que é / What | Pacote que distribui skills + hooks + MCPs | Capacidade específica invocável |
| Formato / Format | Pacote instalável (npm, git) | Arquivo `.md` ou `.js` |
| Analogia / Analogy | App da App Store | Feature dentro do app |
| Instala via / Install via | `/plugin install`, `ccpi install` | `/skill add`, copiar arquivo |
| Pode conter / Contains | Skills + hooks + MCP configs | Instruções + ferramentas |

**Resumo / Summary:** Você instala **plugins**; você usa **skills**.

---

### 10.3 Repositórios e Marketplaces Recomendados / Recommended Repos & Marketplaces

#### Marketplaces

| Site | Skills | Destaque / Highlight |
|---|---|---|
| **awesome-skills.com** | 153+ curadas | Interface web clara, atualizado maio 2026 |
| **tonsofskills.com** | 2.753 skills, 425 plugins | CLI próprio (ccpi), 53k downloads/mês |
| **claudemarketplaces.com** | 6.700+ skills, 840+ MCPs | Maior diretório, atualizado diariamente |
| **mcpmarket.com** | Skills + MCP servers | Foco em geoespacial e dados |
| **code.claude.ai/docs/discover-plugins** | Curado Anthropic | Validado e seguro |

#### Repositórios GitHub

| Repo | Conteúdo | Melhor para / Best for |
|---|---|---|
| `rohitg00/awesome-claude-code-toolkit` | 135 agentes, 35 skills, 176+ plugins, 42 comandos | Tudo em um, produção-grade |
| `affaan-m/everything-claude-code` (ECC) | 119 skills, 28 agentes, 60 comandos 🏆 | Metodologia completa, TDD, instincts |
| `ComposioHQ/awesome-claude-plugins` | Plugins com agents, hooks, MCPs | Automação e extensibilidade |
| `ComposioHQ/awesome-claude-skills` | 1000+ skills (Apache 2.0) | Variedade e licença aberta |
| `jeremylongshore/claude-code-plugins-plus-skills` | 425 plugins, 2.810 skills, 200 agentes | Maior coleção com ccpi CLI |
| `travisvn/awesome-claude-skills` | Curado, foco em qualidade | Ponto de entrada para iniciantes |
| `sickn33/antigravity-awesome-skills` | Catalog diverso, foco em produção | Skills especializadas por domínio |
| `companion-inc/feynman` | Agente de pesquisa com verificação de citações | Pesquisa acadêmica e web verificada |
| `opengeos/geoai-skills` | Skills GeoAI para dados espaciais | Mapas, satélite, análise geoespacial |

---

### 10.4 Antigravity Awesome Skills Catalog

**Repositório:** `github.com/sickn33/antigravity-awesome-skills/blob/main/CATALOG.md`

Coleção curada com foco em skills de produção para domínios específicos. Skills relevantes para o hackathon:
Curated collection focused on production-grade skills for specific domains. Hackathon-relevant skills:

#### Data Science & Análise / Data Science & Analysis

| Skill | Descrição / Description |
|---|---|
| `data-scientist` | Expert em analytics avançado, ML e modelagem estatística |
| `data-storytelling` | Transforma dados brutos em narrativas que guiam decisões |
| `business-analyst` | Dashboards em tempo real com AI-powered analytics |
| `data-quality-frameworks` | Validação com Great Expectations, dbt tests e contratos de dados |
| `analytics-product` | Analytics de produto: PostHog, Mixpanel, funnels, cohorts |

#### Pesquisa & Web / Research & Web

| Skill | Descrição / Description |
|---|---|
| `adhx` | Busca posts do X/Twitter como JSON limpo para LLMs |
| `apify-market-research` | Análise de mercado, oportunidades geográficas, comportamento |
| `helium-mcp` | Pesquisa de notícias com análise de viés de mídia |

#### Visualização / Visualization

| Skill | Descrição / Description |
|---|---|
| `claude-d3js-skill` | Visualizações interativas sofisticadas com D3.js |
| `kpi-dashboard-design` | Padrões para design de dashboards de KPIs eficazes |

#### Apresentação & Pitch / Presentation & Pitch

| Skill | Descrição / Description |
|---|---|
| `steve-jobs` | Abordagem Steve Jobs para apresentações de produto |
| `product-marketing-context` | Positioning, audiência, ICP, use cases e messaging |
| `launch-strategy` | Planejar lançamentos que criam momentum e capturam atenção |
| `startup-business-analyst-business-case` | Business case pronto para investidores/juízes |

#### Código / Code Generation

| Skill | Descrição / Description |
|---|---|
| `ai-engineer` | Aplicações LLM production-ready e sistemas RAG avançados |
| `fp-react` | Padrões funcionais com fp-ts e React: hooks, estado, formulários |
| `claude-code-guide` | Configuração e workflows do Claude Code |

---

### 10.5 Skills Geoespaciais / Geospatial Skills

> **Crítico para o hackathon:** Segurança pública exige mapas. Estas skills automatizam análise e visualização geográfica.

#### geoai-skills (`opengeos/geoai-skills`)

Plugin que adiciona 7 comandos para análise espacial com IA dentro do Claude Code:

| Comando / Command | O Que Faz / What It Does |
|---|---|
| `/inspect-geo` | Analisa arquivos raster/vector: coordenadas, limites, resolução |
| `/download-data` | Baixa imagens aéreas NAIP para área geográfica especificada |
| `/search-stac` | Busca imagens de satélite no Microsoft Planetary Computer |
| `/overture-data` | Dados OpenStreetMap derivados: edifícios, vias, uso do solo |
| `/process-raster` | Recorta, empilha, mosaica e converte raster/vector |
| `/detect-objects` | Detecta edifícios, veículos e features customizadas com IA |
| `/read-memories` | Recupera contexto de sessões anteriores do Claude Code |

```bash
# Instalar / Install
/plugin marketplace add opengeos/geoai-skills
/plugin install geoai-skills@geoai-skills
# Requer Python 3.10+ com geoai-py instalado
```

#### Skills Geoespaciais no MCPMarket

| Skill | O Que Faz |
|---|---|
| `geopandas-spatial-analysis` | Análise espacial com GeoPandas, operações vetoriais, joins espaciais |
| `gis-web-mapping` | Leaflet + vector tiles + GeoJSON overlays + clustering de pontos |
| `geospatial-visualization` | Mapas interativos: draw tools, area selection, isochrones |
| `geomaster` | Expert GIS completo: satélite multi-sensor, ML espacial, análise de terreno |

#### Agente Geoespacial do Toolkit

```bash
/plugin marketplace add rohitg00/awesome-claude-code-toolkit

# Invocar o agente geoespacial / Invoke geospatial agent:
"Act as the Geospatial Engineer from the toolkit.
Analyze crime occurrence data with lat/lon coordinates.
Generate a Leaflet heatmap component and a GeoPandas analysis pipeline."
```

---

### 10.6 ECC — Everything Claude Code (🏆 Vencedor do Hackathon Anthropic Feb/2026)

**Repositório:** `github.com/affaan-m/everything-claude-code` (68k+ stars)

O ECC ganhou o Cerebral Valley x Anthropic Hackathon em fevereiro de 2026. Não é uma coleção de skills — é uma metodologia completa chamada **Eval-Driven Development (EDD)**.

#### O Que Inclui / What It Contains

| Componente | Qtd | Destaque |
|---|---|---|
| Skills | 119 | TDD workflow, strategic-compact, verification-loop |
| Agentes | 28 | Backend, frontend, security, data, research |
| Slash Commands | 60 | Inclui shims de compatibilidade com ferramentas legadas |
| Instincts | Sistema | Aprendizado contínuo das suas sessões |

#### Skills Essenciais do ECC / Essential ECC Skills

**`tdd-workflow`** — O ciclo RED-GREEN-REFACTOR para IA:
```
Claude escreve o teste que FALHA primeiro → implementa → refatora
Garante código testável por design — crítico para sistemas de segurança pública
```

**`strategic-compact`** — Sessões 3x mais longas:
```
Resumo estruturado que preserva: decisões tomadas, restrições descobertas,
escolhas arquiteturais. Descarta histórico de baixo sinal.
Evita degradação de qualidade por overflow de contexto em sessões longas.
```

**`verification-loop`** — Validação contínua após cada mudança.

**`instincts`** — Aprendizado contínuo:
```
Extrai padrões das suas sessões em "instincts" reutilizáveis com score de confiança.
Eles evoluem automaticamente para skills completas.
```

#### Instalação / Installation

```bash
/plugin marketplace add affaan-m/everything-claude-code

# Ou manual / Or manual:
git clone https://github.com/affaan-m/everything-claude-code ~/.claude/plugins/ecc
```

**Resultado medido / Measured results:** 65% redução no tempo de desenvolvimento. Taxa de aprovação de PR na primeira revisão muito mais alta.

---

### 10.7 Outros Recursos Relevantes / Other Relevant Resources

| Site / Recurso | O Que É | Por Que Útil |
|---|---|---|
| **claudeskills.info** | Blog sobre skills e hackathons Claude Code | Análise profunda do ECC e metodologia EDD |
| **agensi.io/learn** | Guias de skills por linguagem/domínio | Tutoriais para Python, React, hackathons |
| **augmentcode.com/learn** | Análise técnica do ecossistema | Comparações, casos de uso, benchmarks |
| **levelup.gitconnected.com** | Artigos sobre mental models do ecossistema | Skills, subagents, plugins explicados |
| **scottspence.com** | Blog técnico sobre Claude Code | Posts práticos sobre organização de skills |
| **blog.geomusings.com** | Blog de análise espacial com Claude Code | Workflows geoespaciais em detalhe |
| **carto.com/blog** | IA geoespacial com Claude | Como transformar Claude em agente geoespacial |

---

### 10.8 Starter Pack para o Hackathon do Rio / Rio Hackathon Starter Pack

Instale antes do evento começar / Install before the event starts:

```bash
# 1. Gerenciador de plugins / Plugin manager
pnpm add -g @intentsolutionsio/ccpi

# 2. ECC — metodologia completa (instalar primeiro)
/plugin marketplace add affaan-m/everything-claude-code

# 3. Toolkit abrangente
/plugin marketplace add rohitg00/awesome-claude-code-toolkit

# 4. Skills geoespaciais (crítico para mapas!)
/plugin marketplace add opengeos/geoai-skills
/plugin install geoai-skills@geoai-skills

# 5. Feynman — pesquisa com verificação de fontes
npx feynman install --target claude-code

# 6. Skills do Antigravity Catalog — copiar manualmente:
#    sickn33/antigravity-awesome-skills/skills/
mkdir -p ~/.claude/commands
# data-scientist.md, claude-d3js-skill.md, steve-jobs.md, data-storytelling.md

# 7. Verificar todas as skills instaladas
/   # Lista todos os comandos disponíveis no Claude Code
```

#### Tabela de Uso por Fase do Hackathon / Usage by Phase

| Fase / Phase | Skill Recomendada | Como Usar |
|---|---|---|
| Pesquisa de dados | `feynman` + `/deepresearch` | Verificar fontes de dados do Rio com citações reais |
| Planejamento | `/plan` + `/architect` | Estruturar SPEC.md antes de codificar |
| Backend Python | `data-scientist` + `tdd-workflow` | Pipeline de dados + testes automáticos |
| Análise geoespacial | `/geopandas-spatial-analysis` + `/inspect-geo` | CSV com lat/lon → análise espacial |
| Frontend mapas | `/gis-web-mapping` + artifacts-builder | Leaflet + React components |
| Visualizações | `/claude-d3js-skill` + `kpi-dashboard-design` | Gráficos D3.js para crimes por tipo/período |
| Revisão de código | `/code-review` + `verification-loop` | Antes de cada commit |
| Segurança | `/security-review` + ECC security-review | Antes de publicar o repositório |
| Pitch | `steve-jobs` + `startup-business-analyst-business-case` | Roteiro e slides |
| Sessão longa | `strategic-compact` | Quando contexto estiver ficando longo |

---

## Fontes / Sources

- [Feynman AI Research Agent (2026) — Virtual Uncle](https://virtualuncle.com/feynman-ai-research-agent-2026/)
- [companion-inc/feynman — GitHub](https://github.com/companion-inc/feynman)
- [Awesome Claude Skills — awesome-skills.com](https://awesome-skills.com/)
- [ComposioHQ/awesome-claude-skills — GitHub](https://github.com/ComposioHQ/awesome-claude-skills)
- [jeremylongshore/claude-code-plugins-plus-skills — GitHub](https://github.com/jeremylongshore/claude-code-plugins-plus-skills)
- [rohitg00/awesome-claude-code-toolkit — GitHub](https://github.com/rohitg00/awesome-claude-code-toolkit)
- [affaan-m/everything-claude-code (ECC) — GitHub](https://github.com/affaan-m/everything-claude-code)
- [sickn33/antigravity-awesome-skills — GitHub](https://github.com/sickn33/antigravity-awesome-skills)
- [opengeos/geoai-skills — GitHub](https://github.com/opengeos/geoai-skills)
- [Claude Code Plugin Marketplace Guide (2026) — Agensi.io](https://www.agensi.io/learn/claude-code-plugin-marketplace-guide)
- [Best Claude Code Skills 2026 — Toolradar](https://toolradar.com/blog/best-claude-code-skills-2026)
- [Essential Claude Code Skills — Batsov](https://batsov.com/articles/2026/03/11/essential-claude-code-skills-and-commands/)
- [Everything Claude Code Hackathon Winner — Claude Skills Hub](https://claudeskills.info/blog/everything-claude-code-hackathon-eval-driven/)
- [GIS Web Mapping Skill — MCPMarket](https://mcpmarket.com/tools/skills/gis-web-mapping)
- [GeoPandas Spatial Analysis Skill — MCPMarket](https://mcpmarket.com/tools/skills/geopandas-spatial-analysis)
- [Spatial Analysis with Claude Code — GeoMusings](https://blog.geomusings.com/2026/01/14/spatial-analysis-with-claude-code/)
- [Turning Claude into Geospatial Agents — CARTO](https://carto.com/blog/turning-claude-chatgpt-into-geospatial-agents/)
- [Claude Code Hackathon Ultimate Guide — Medium](https://medium.com/@abandoned_train_station/claude-code-hackathon-the-ultimate-guide-to-winning-b06eaf84ee84)
- [Built with Opus 4.6 Hackathon Winners — Claude Blog](https://claude.com/blog/meet-the-winners-of-our-built-with-opus-4-6-claude-code-hackathon)

---

*Guia criado para o Claude Impact Lab — Rio de Janeiro*  
*Guide created for Claude Impact Lab — Rio de Janeiro*  
*Powered by Claude Code + claude-sonnet-4-6*
