# CIVITAS — Frontend Workspace

## Contexto / Context
Frontend para o sistema CIVITAS de análise de segurança pública do Rio.
Integra com FastAPI backend em localhost:8000.

## Stack
- React 18 + Vite
- Tailwind CSS (styling — sem inline styles)
- Leaflet (mapas interativos)
- Recharts (gráficos/charts)
- PyVis HTML export (visualização de grafos de NetworkX)

## Comandos / Commands
```bash
npm install
npm run dev        # dev server (localhost:5173)
npm run build      # build de produção
```

## Componentes Planejados / Planned Components
- `MapView` — mapa de calor com Leaflet + filtros
- `FilterPanel` — date range, tipo de crime, bairro
- `StatsChart` — gráfico de tendência mensal (Recharts)
- `GraphView` — embed do PyVis HTML ou D3.js
- `OccurrenceTable` — tabela paginada de ocorrências

## Regras / Rules
- Sem inline styles — sempre Tailwind
- Sem bibliotecas UI externas pesadas (sem MUI, sem Ant Design)
- API base URL: `http://localhost:8000`
- Dados agregados apenas — sem PII visível na UI

## Skills Disponíveis (deste workspace)
Workspace mais leve — sem skills de análise de dados.
Use `/feynman` para pesquisar documentação de bibliotecas.
