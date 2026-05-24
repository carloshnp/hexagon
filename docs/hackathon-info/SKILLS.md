# Available Skills — CIVITAS

## Skills Nativas / Built-in Claude Code
| Skill           | Comando          | Quando usar                              |
|-----------------|------------------|------------------------------------------|
| verify          | /verify          | Após implementar uma feature             |
| run             | /run             | Screenshot/teste do app em execução      |
| code-review     | /code-review     | Antes de commitar código crítico         |
| security-review | /security-review | Antes da demo final — checar PII leaks   |
| init            | /init            | Criar CLAUDE.md para sub-workspace       |
| byterover       | brv              | Armazenar decisões e contexto do projeto |

## Skills Instaladas / Installed (em .claude/commands/)
| Skill                    | Comando                    | Descrição                                        |
|--------------------------|----------------------------|--------------------------------------------------|
| networkx                 | /networkx                  | Análise de grafos — movimento, conexões (CIVITAS)|
| geopandas                | /geopandas                 | Dados geoespaciais do Rio                        |
| matplotlib               | /matplotlib                | Visualizações de dados                           |
| seaborn                  | /seaborn                   | Visualizações estatísticas                       |
| statistical-analysis     | /statistical-analysis      | Análise estatística dos dados ISP-RJ             |
| exploratory-data-analysis| /exploratory-data-analysis | EDA inicial dos datasets                         |
| scikit-learn             | /scikit-learn              | ML para detecção de anomalias                    |
| feynman                  | /feynman                   | Pesquisa web aprofundada                         |

## Todas as Skills Disponíveis (.agents/skills/)
Skills adicionais disponíveis mas não carregadas por padrão para economizar tokens.
Para instalar: `cp .agents/skills/<nome>/SKILL.md .claude/commands/<nome>.md`

Incluem: bgpt-paper-search, detect-objects, exa-search, geomaster, hugging-science,
inspect-geo, install-geoai, literature-review, markitdown, market-research-reports,
markdown-mermaid-writing, optimize-for-gpu, overture-data, paper-lookup, pdf,
process-raster, read-memories, scientific-brainstorming, scientific-critical-thinking,
shap, statsmodels, timesfm-forecasting, torch-geometric, vaex, xlsx, zarr-python
