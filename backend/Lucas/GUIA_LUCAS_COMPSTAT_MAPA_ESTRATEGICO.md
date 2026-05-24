# Guia Lucas - CompStat Mapa Estrategico

## Objetivo

Este documento e um guia para a IA/desenvolvedor responsavel pela frente **Lucas** no repositorio `hexagon`.

O produto mudou. A solucao agora deve ser orientada por um **mapa estrategico interativo com as 8 regioes oficiais delimitadas pela Prefeitura**, usando analise granular por regiao para apoiar a **reuniao semanal de seguranca** com os orgaos competentes.

A missao da frente Lucas e orquestrar backend, IA, dados e contrato frontend para transformar as bases oficiais e fontes complementares em:

- Mapa com score de risco por regiao.
- Relatorio estrategico semanal.
- Relatorios individuais por regiao.
- Planos de acao por grupo/tipo de ocorrencia.
- Chat com agente LLM que responde com base nos dados e referencia regiao, evidencias e camadas do mapa.
- Contrato backend -> frontend para o time consumir.

## Regra de Escopo

Antes de modificar qualquer coisa, leia o repositorio inteiro o suficiente para entender a arquitetura atual.

Prioridade de leitura:

1. `README.md`
2. `CLAUDE.md`
3. `backend/Lucas/`
4. `backend/`
5. `frontend/`
6. `docs/`
7. Quaisquer contratos, scores ou endpoints ja existentes

Se for criar ou alterar documentacao desta frente, mexer somente em `backend/Lucas/`.

Se for implementar backend em etapa posterior, primeiro confirmar o contrato e evitar quebrar codigo existente.

## Produto Atual

Nome de trabalho:

**CompStat Rio - Mapa Estrategico de Apoio a Decisao**

O produto deve apoiar decisoes estrategicas da reuniao semanal de seguranca. Ele nao e um dashboard generico. Ele deve ajudar os orgaos competentes a responder:

- Qual regiao deve ser priorizada?
- Por que?
- Quais ocorrencias explicam o risco?
- Quais horarios concentram eventos?
- Quais pontos criticos aparecem no mapa?
- Ha cameras CIVITAS proximas aos pontos sensiveis?
- Quais fatores urbanos ajudam a explicar o problema?
- Qual orgao municipal deve agir?
- Qual plano de acao e recomendado?
- Quais evidencias sustentam essa recomendacao?

## Fonte Principal

Usar como fonte oficial do desafio:

[CompStat-Rio/claude_impact_lab_compstat_rio](https://github.com/CompStat-Rio/claude_impact_lab_compstat_rio)

Dados esperados:

- `dados/cameras_areas_fm.csv`
- `dados/df_ocorrencias_tratado - Extracao 1.csv`
- `dados/disk_denuncia.csv`
- `dados/fatores_urbanos.csv`
- `dados/Dicionario de dados.xlsx`
- `dados/outros dados/CPSR_2020_2022_2024.xlsx`
- `dados/outros dados/dominio_territorial - Extracao 1.csv`
- `relints/*.docx`
- `sh_area_forca/areas_forca_municipal.shp`

O shapefile publico atual representa as **8 regioes oficiais** usadas nesta versao do produto.

## Fontes Publicas Complementares

Podem ser usadas para enriquecer analise, desde que nao substituam a base oficial do desafio:

- ISPDados, para baseline historico agregado de seguranca publica:
  https://www.ispdados.rj.gov.br/estatistica.html

- Dados.Rio e APIs municipais:
  https://docs.dados.rio/api-reference/overview

- 1746, quando fizer sentido como camada de zeladoria/ordem urbana:
  https://docs.dados.rio/api-reference/citizen/obter-chamados-do-1746-do-cidad%C3%A3o

- Fogo Cruzado, para violencia armada, se houver acesso e pertinencia:
  https://fogocruzado.org.br/

- GENI/Fogo Cruzado - Mapa de Grupos Armados, apenas como contexto territorial:
  https://geni.uff.br/2022/09/13/mapa-historico-dos-grupos-armados-no-rio-de-janeiro/

## Guardrails

Nao implementar nem sugerir:

- Reconhecimento facial.
- Identificacao de pessoa-alvo.
- Perfilamento individual.
- Uso de placa, imagem bruta ou biometria.
- Decisao automatica sem validacao humana.
- Policiamento preditivo opaco.
- Criminalizacao de populacao em situacao de rua.
- Uso de dominio territorial como fonte unica para acao.

Toda recomendacao precisa ter:

- Evidencia.
- Fonte/provenance.
- Grau de confianca ou incerteza.
- Orgao competente.
- Status humano: sugerido, aprovado, rejeitado, encaminhado ou concluido.

## Funcionalidades Principais

### 1. Mapa Interativo das 8 Regioes

O mapa deve exibir as 8 regioes oficiais do GitHub, com:

- Poligono da regiao.
- Score de risco geral.
- Nivel de risco.
- Orgao municipal principal sugerido.
- Camadas de ocorrencias.
- Camadas de cameras CIVITAS.
- Camadas de fatores urbanos.
- Areas criticas.
- Filtros por periodo, tipo de ocorrencia, horario e orgao.

Ao clicar em uma regiao, o frontend deve receber um recorte granular daquela area.

### 2. Recorte Granular por Regiao

Para cada regiao, retornar:

- Resumo executivo da regiao.
- Score de risco.
- Ocorrencias localizadas.
- Agrupamentos de ocorrencias por tipo/padrao.
- Pontos de maior concentracao.
- Horarios criticos.
- Cameras proximas aos pontos sensiveis.
- Fatores urbanos relevantes.
- Orgao competente para cada risco.
- Plano de acao por grupo de ocorrencia.
- Relatorio individual gerado por agente LLM.

### 3. Relatorio Estrategico Semanal

Relatorio para reuniao semanal dos orgaos de seguranca.

Deve conter:

- Ranking das 8 regioes.
- Justificativa da priorizacao.
- Principais padroes do mes.
- Mudancas em relacao ao historico.
- Alertas por horario.
- Riscos por orgao responsavel.
- Recomendacoes estrategicas.
- Matriz de responsabilidade.
- Pendencias e proximos passos.

O relatorio deve ser interativo: ao falar de uma regiao ou ocorrencia, o frontend precisa conseguir referenciar o item no mapa.

### 4. Relatorios Individuais por Area

Cada area deve ter um relatorio proprio, gerado por agente LLM, com:

- Resumo.
- Explicacao completa.
- Score e seus componentes.
- Descricao das ocorrencias.
- Pontos de maior ocorrencia.
- Janelas horarias criticas.
- Relacao com fatores urbanos.
- Cobertura/lacunas de cameras.
- Plano de acao por tipo de ocorrencia.
- Dados estruturados para renderizacao no mapa.

### 5. Chat com Agente LLM

O usuario deve poder conversar com o plano e com o mapa.

Exemplos de perguntas:

- "Por que esta regiao esta com risco alto?"
- "Quais ocorrencias acontecem mais a noite?"
- "Tem camera perto dos pontos criticos?"
- "Qual orgao deve resolver o fator urbano mais relevante?"
- "O que muda se eu olhar os ultimos 6 meses?"
- "Quais acoes a SEOP deveria priorizar?"
- "Explique a diferenca entre essa regiao e a regiao X."

A resposta deve citar:

- Regiao.
- Dados usados.
- Evidencias.
- Recorte temporal.
- Limitacoes.
- Camadas do mapa relacionadas.

## Recortes Temporais

Padrao:

- Ultimos 30 dias de ocorrencias.

Tambem deve permitir:

- Historico ampliado da regiao.
- Comparacao mes atual vs historico.
- Filtro por faixa horaria.
- Filtro por periodo diurno/noturno.
- Filtro por tipo de ocorrencia.
- Filtro por orgao responsavel.

A analise horaria e importante especialmente quando combinada com fatores urbanos, por exemplo iluminacao precaria em areas com ocorrencias noturnas.

## Papel dos Scores

Um colega da pasta `Perri` ja fez scores e contrato para frontend. Outro colega esta fazendo score granular so de ocorrencias.

A frente Lucas nao deve reimplementar tudo do zero.

A missao e:

- Ler e entender os scores existentes.
- Integrar esses scores ao pipeline do backend.
- Criar orquestracao com IA.
- Gerar relatorios estruturados.
- Gerar contrato final para frontend.
- Garantir que o mapa e relatorios falem a mesma lingua.

Se houver divergencia entre scores:

- Preservar score granular de ocorrencias como insumo especifico.
- Usar score integrado/orquestrado como score final da regiao.
- Explicar os componentes no relatorio.
- Nunca deixar a LLM inventar score sem formula ou evidencia.

## Agentes Claude Code/API

Os agentes devem ser consumidos via Claude Code/API, com saida estruturada e validada.

### MapRegionOrchestratorAgent

Responsavel por decidir quais camadas e evidencias entram na analise de cada regiao.

Entradas:

- Regiao.
- Ocorrencias.
- Cameras.
- Fatores urbanos.
- RELINTs.
- Denuncias.
- Scores existentes.
- Filtros temporais.

Saidas:

- Lista de evidencias consideradas.
- Evidencias descartadas e motivo.
- Peso qualitativo de cada camada.
- Trace de decisao.

### RegionalRiskNarrativeAgent

Gera relatorio individual por regiao.

Saidas:

- Resumo executivo.
- Explicacao completa.
- Principais padroes.
- Incertezas.
- Recomendacoes.
- Evidencias citadas.

### OccurrenceGroupAgent

Agrupa ocorrencias por:

- Tipo.
- Localizacao.
- Horario.
- Padrao.
- Intensidade.
- Recorrencia.

Saidas:

- Grupos de ocorrencia.
- Resumo por grupo.
- Plano de acao por grupo.
- Dados para renderizar no mapa.

### UrbanFactorActionAgent

Conecta fatores urbanos a orgaos competentes.

Exemplos:

- Iluminacao: RioLuz.
- Ordenamento urbano: SEOP.
- Lixo/limpeza: Comlurb.
- Transito/fluxo: CET-Rio.
- Vulnerabilidade social: assistencia/saude, sem criminalizacao.
- Presenca operacional: Forca Municipal.

### CameraCoverageAgent

Avalia se ha cameras proximas aos pontos sensiveis.

Nao usar:

- Imagem bruta.
- Placa.
- Rosto.
- Biometria.

Usar apenas:

- Localizacao da camera.
- Cobertura aproximada.
- Lacuna de cobertura.
- Relacao com ponto critico.

### StrategicWeeklyReportAgent

Gera relatorio semanal para reuniao.

Deve consolidar:

- Ranking das regioes.
- Prioridades.
- Matriz de responsabilidade.
- Planos de acao.
- Alertas.
- Evidencias.
- Limitacoes.

### ReportChatAgent

Responde perguntas do usuario sobre mapa, relatorio e dados.

Deve:

- Usar retrieval otimizado.
- Responder com base nos dados.
- Citar regiao e evidencia.
- Indicar quando nao houver evidencia suficiente.
- Nunca inventar dados.

### AuditAndProvenanceAgent

Valida:

- PII.
- Fonte unica contextual.
- Linguagem proibida.
- Falta de evidencia.
- Uso indevido de vulnerabilidade social.
- Ausencia de orgao responsavel.
- Plano de acao sem justificativa.

## Contrato Backend -> Frontend

### GET `/map/regions`

Retorna GeoJSON das 8 regioes com resumo de risco.

Formato esperado:

```json
{
  "type": "FeatureCollection",
  "generated_at": "2026-05-24T00:00:00Z",
  "time_window": {
    "preset": "last_30_days",
    "start": "2026-04-24",
    "end": "2026-05-24"
  },
  "features": [
    {
      "type": "Feature",
      "id": "regiao_001",
      "properties": {
        "region_id": "regiao_001",
        "region_name": "Rodoviaria - Terminal Gentileza - Estacao Leopoldina",
        "risk_score": 82,
        "risk_level": "high",
        "primary_agency": "FM",
        "secondary_agencies": ["SEOP", "Comlurb"],
        "summary": "Alta concentracao de furtos em horarios de pico e lacunas de cobertura em pontos sensiveis.",
        "occurrence_count": 128,
        "camera_count": 12,
        "critical_area_count": 4
      },
      "geometry": {}
    }
  ]
}
```

### GET `/map/regions/{region_id}`

Retorna analise granular da regiao.

Formato esperado:

```json
{
  "region": {
    "region_id": "regiao_001",
    "region_name": "Rodoviaria - Terminal Gentileza - Estacao Leopoldina",
    "risk_score": 82,
    "risk_level": "high",
    "primary_agency": "FM"
  },
  "time_window": {
    "preset": "last_30_days",
    "start": "2026-04-24",
    "end": "2026-05-24",
    "historical_available": true
  },
  "map_layers": {
    "polygon": {},
    "occurrences": [],
    "cameras": [],
    "urban_factors": [],
    "critical_areas": []
  },
  "occurrence_groups": [],
  "regional_report": {},
  "recommended_actions": [],
  "provenance": []
}
```

### GET `/reports/weekly-strategic`

Retorna relatorio estrategico semanal.

Formato esperado:

```json
{
  "report_id": "weekly_2026_05_24",
  "title": "Relatorio Estrategico Semanal - CompStat Rio",
  "summary": "Resumo para reuniao semanal.",
  "ranked_regions": [],
  "strategic_priorities": [],
  "agency_matrix": [],
  "map_references": [],
  "provenance": [],
  "generated_by": "StrategicWeeklyReportAgent"
}
```

### GET `/reports/regions/{region_id}`

Retorna relatorio individual da area.

Formato esperado:

```json
{
  "region_id": "regiao_001",
  "summary": "Resumo da regiao.",
  "full_explanation": "Explicacao detalhada.",
  "score": {
    "final": 82,
    "components": []
  },
  "occurrences": [
    {
      "group_id": "furto_celular_pico_tarde",
      "summary": "Resumo da ocorrencia/grupo.",
      "detailed_explanation": "Explicacao completa.",
      "action_plan": {
        "responsible_agency": "FM",
        "supporting_agencies": ["SEOP"],
        "action": "Acao recomendada.",
        "priority": "high",
        "time_window": "17h-20h"
      },
      "map_data": {
        "points": [],
        "hotspots": [],
        "related_cameras": [],
        "related_urban_factors": []
      },
      "provenance": []
    }
  ],
  "uncertainties": [],
  "guardrails": []
}
```

### POST `/reports/chat`

Entrada:

```json
{
  "question": "Por que esta regiao esta com risco alto?",
  "region_id": "regiao_001",
  "filters": {
    "time_window": "last_30_days",
    "occurrence_type": null,
    "hour_range": null
  }
}
```

Saida:

```json
{
  "answer": "Resposta baseada nos dados.",
  "region_refs": ["regiao_001"],
  "map_refs": [],
  "evidence_refs": [],
  "limitations": [],
  "agent_trace": []
}
```

## JSON do Relatorio Individual

O relatorio em JSON deve conter obrigatoriamente uma lista de ocorrencias ou grupos de ocorrencias.

Cada item deve ter:

- `summary`
- `detailed_explanation`
- `score`
- `action_plan`
- `map_data`
- `provenance`

Exemplo minimo:

```json
{
  "occurrences": [
    {
      "summary": "Furtos de celular concentrados no entorno do terminal.",
      "detailed_explanation": "Nos ultimos 30 dias, os registros indicam concentracao no fim da tarde, com recorrencia em acessos de alto fluxo.",
      "score": {
        "risk": 82,
        "confidence": 0.76
      },
      "action_plan": {
        "responsible_agency": "FM",
        "supporting_agencies": ["SEOP", "RioLuz"],
        "recommended_action": "Reforcar presenca orientada por dados no horario critico e solicitar verificacao de iluminacao nos pontos com maior concentracao.",
        "priority": "high"
      },
      "map_data": {
        "points": [],
        "hotspots": [],
        "critical_hours": ["17h", "18h", "19h"],
        "related_cameras": [],
        "related_urban_factors": []
      },
      "provenance": []
    }
  ]
}
```

## Criterios de Aceite

A entrega da frente Lucas deve ser considerada boa se:

- As 8 regioes aparecem no contrato de mapa.
- Cada regiao tem score, resumo e orgao responsavel.
- Clicar em uma regiao permite carregar recorte granular.
- O relatorio semanal referencia regioes do mapa.
- O relatorio individual explica score, ocorrencias, pontos criticos e plano de acao.
- Cada grupo de ocorrencia tem plano de acao.
- O chat responde com base nos dados e cita evidencias.
- O frontend recebe JSON previsivel e suficiente para renderizar mapa, painel lateral e relatorios.
- A IA nao inventa dados sem provenance.
- Os guardrails de seguranca publica sao respeitados.

## Prioridade de Implementacao

1. Ler o repo `hexagon` e identificar endpoints/contratos ja existentes.
2. Ler o que existe em `backend/Lucas`.
3. Ler scores/contratos de colegas se existirem no repo.
4. Criar ou atualizar contrato backend -> frontend para o mapa.
5. Implementar pipeline de regioes.
6. Integrar scores existentes.
7. Implementar relatorios individuais por regiao.
8. Implementar relatorio estrategico semanal.
9. Implementar chat com agente LLM.
10. Implementar auditoria/provenance.
11. Testar com as 8 regioes oficiais.

## Observacao Final

A solucao vencedora deve parecer uma ferramenta real para reuniao CompStat: mapa, evidencia, decisao, orgao responsavel e plano de acao. O frontend nao deve receber apenas texto bonito. Ele precisa receber dados estruturados suficientes para mostrar exatamente onde, por que e como agir.
