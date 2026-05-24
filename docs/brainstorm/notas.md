# Ações Habituais da Prefeitura do Rio (CompStat Rio)

> Baseado em docs/research/COMPSTAT_RIO.md e docs/research/RESEARCH.md
> Data: 2026-05-24

---

## Diário

| Ação | Agência | Base documental |
|---|---|---|
| Rondas FM pelas 22 áreas prioritárias | Força Municipal | FM faz patrulhas em tempo real (COMPSTAT_RIO §1) |
| Monitoramento ao vivo de câmeras | CIVITAS / COR | 10.000+ câmeras CIVITAS, 5.000 COR (§1) |
| Leitura de placas em circulação | COR | 800+ leitores de placa (§1) |
| Despacho e resposta SAMU | SAMU/Saúde | Tempos de resposta como dado de entrada (§1) |
| Atendimento chamados 1746 | SEOP / RioLuz | Iluminação deficiente, ruído, desordem (§2) |

---

## Semanal

| Ação | Agência | Base documental |
|---|---|---|
| Briefing operacional de área (analistas) | FM / CIVITAS | "Ciclos regulares de análise → ação → avaliação" (§1) |
| Análise de ocorrências recentes (roubo celular + ônibus) | ISP / FM | Dataset de roubo = insumo semanal (§2) |
| Fiscalização de comércio irregular | SEOP | Autos de infração, SEOP como dado de entrada (§2) |
| Revisão de score por polígono | Múltiplas | "Ciclos regulares" + modelo CompStat |

---

## Mensal

| Ação | Agência | Base documental |
|---|---|---|
| **Reunião CompStat** com Prefeito + Casa Civil | Multi-agência | "Reuniões periódicas (prefeito + casa civil): prestação de contas, principais problemas, plano de ação" (§1) |
| Prestação de contas por área — responsável identificado por fator urbano | FM / SEOP / RioLuz | "Governança — responsabilização por área" (§1) |
| Atualização do plano de emprego da FM | Força Municipal | Ciclos do CompStat + doc §5 |
| Relatório executivo consolidado das 22 áreas | CIVITAS / COR | "Relatório automatizado: resumo executivo, mapa de calor…" (§4) |
| Revisão dos 20 fatores urbanos por área | SEOP / SMU / RioLuz | Lista de 20 fatores (§2) |

---

## Semestral

| Ação | Agência | Base documental |
|---|---|---|
| Revisão dos polígonos FM (22 áreas — limites e prioridades) | FM / CIVITAS | Implícito no modelo territorial (§1) |
| Análise de tendências criminais de médio prazo | ISP / FM | Dado histórico como insumo do Bingo Engine (§3) |
| Revisão de domínio territorial por facção | Inteligência | "Dado de facção = camada qualitativa crítica" (§2) |

---

## Anual

| Ação | Agência | Base documental |
|---|---|---|
| Revisão estratégica do CompStat Rio | Prefeitura / Casa Civil | Modelo NYPD CompStat: revisão anual de metas |
| Auditoria de cobertura de câmeras por área | CIVITAS / COR | Câmeras como fator de deterrência — gap analysis |
| Planejamento de bases FM para o ano seguinte | FM | Modelo operacional do CompStat |
| Licenciamento e mapeamento de obras (tapumes) | SMU | Tapumes como fator urbano (§2) |

---

## Bienal

| Ação | Agência | Base documental |
|---|---|---|
| **Censo de população de rua** | Prefeitura (survey) | "Censo bienal de entrevistas → índice de vulnerabilidade social por área" (COMPSTAT_RIO §2) |

---

## O que o CompStat Rio já produz vs. o que falta

> "Eles têm o **diagnóstico**. Precisam da **prescrição**." — COMPSTAT_RIO §4

| Já existe (diagnóstico) | Falta (prescrição) |
|---|---|
| Relatório automatizado + mapa de calor | Rota FM calculada + horário de patrulha |
| Análise temporal e criminal | Score de prioridade com raciocínio explicado (SHAP) |
| Painel de coincidências por área | LLM pipeline de RELINTs e Disque Denúncia |
| Mapa com polígonos FM | Responsável identificado por cada fator urbano |

---

## Implicação para o produto

A **reunião mensal com o prefeito** é o ritmo central — é o deadline real que o CompStat briefing precisa alimentar.

As ações diárias/semanais (rondas, chamados 1746, fiscalização SEOP) são os **insumos** que o score do Bingo Engine precisa consumir.
