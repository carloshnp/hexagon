#!/usr/bin/env python3
"""
CIVITAS - Gerador de Relatórios Investigativos
===============================================
Gera relatórios estruturados a partir de evidências, análises de imagem,
dados de grafo e consulta do usuário.

Tenta usar Claude Haiku via API. Se offline, usa fallback baseado em templates.
"""

import json
import os
import sys
import copy
from datetime import date
from typing import Optional

# ─── Configuração ────────────────────────────────────────────────────────────

DEFAULT_MODEL = "claude-3-haiku-20240307"
MAX_RETRIES = 2
CONFIANCA_VALORES = ("ALTA", "MÉDIO", "BAIXO", "INDETERMINADO")
URGENCIA_VALORES = ("nenhuma", "baixa", "média", "alta")
FORCA_VALORES = ("FORTE", "MÉDIO", "FRACO")
AUTENTICIDADE_VALORES = ("ORIGINAL", "EDITADA", "INDETERMINADO")

# ─── Templates de Fallback ──────────────────────────────────────────────────

TEMPLATE_FALLBACK_SECTIONS = {
    "resumo_executivo": """
### Resumo Executivo
{user_query}

**Descobertas principais:**
{descobertas}

**Confiança global:** {confianca_global}
""",

    "evidencias": """
### Evidências Coletadas

**Documentais:**
{evidencias_doc}

**Digitais/Forenses:**
{evidencias_dig}
""",

    "analise_imagens": """
### Análise de Imagens
{imagens_texto}
""",

    "timeline": """
### Timeline
{timeline_texto}
""",

    "grafo": """
### Grafo de Relacionamentos

**Entidades:**
{entidades_texto}

**Relações:**
{relacoes_texto}
""",

    "recomendacoes": """
### Análise e Recomendações

**Síntese:**
{sintese}

**Recomendações:**
{recomendacoes}

**Lacunas:**
{lacunas}
""",
}


# ─── Schema do Relatório JSON ───────────────────────────────────────────────

RELATORIO_EMPTY = {
    "titulo": "",
    "data": str(date.today()),
    "caso": "NÃO INFORMADO",
    "classificacao": "INTERNO",
    "investigador": "CIVITAS IA - v1.0 (FALLBACK)",
    "confianca_global": "MÉDIO",
    "resumo_executivo": {
        "sintese": "",
        "descobertas_principais": [],
        "urgencia": "nenhuma",
    },
    "evidencias": {
        "documentais": [],
        "testemunhais": [],
        "digitais": [],
    },
    "analise_imagens": {"presente": False, "imagens": []},
    "timeline": {"presente": False, "titulo": "", "eventos": []},
    "grafo_relacionamentos": {
        "presente": False,
        "entidades": [],
        "relacoes": [],
        "metricas": {
            "nos": 0,
            "arestas": 0,
            "densidade": 0.0,
            "componentes_conectados": 0,
            "no_central": "",
        },
    },
    "analise_recomendacoes": {
        "sintese_analitica": "",
        "recomendacoes_imediatas": [],
        "recomendacoes_curto_prazo": [],
        "recomendacoes_medio_longo_prazo": [],
        "lacunas": [],
    },
    "fontes_citadas": [],
}


# ─── System Prompt (mesmo do investigator_prompt.md) ────────────────────────

SYSTEM_PROMPT = """
Você é um investigador forense digital sênior do sistema CIVITAS. Sua função é
GERAR RELATÓRIOS INVESTIGATIVOS ESTRUTURADOS a partir de evidências, análises
de imagem, dados de grafo e consultas do usuário.

## REGRAS FUNDAMENTAIS

1. IDIOMA: Responda SEMPRE em português brasileiro.
2. NÍVEIS DE CONFIANÇA: Toda evidência e conclusão DEVE ter nível de confiança:
   ALTA, MÉDIA, BAIXA ou INDETERMINADO.
3. SEÇÕES OBRIGATÓRIAS: Resumo Executivo, Evidências, Análise e Recomendações.
4. SEÇÕES CONDICIONAIS: Análise de Imagens, Timeline, Grafo.
5. CITAÇÃO: Use formato [F-NNN] para referenciar fontes.
6. OBJETIVIDADE: Baseie-se APENAS nos dados fornecidos.
7. Produza APENAS JSON válido. Sem markdown extra, sem comentários.

Calcule a confianca_global baseado na maioria das evidências. Se alguma
evidência crítica for BAIXA, o nível global não pode ser ALTO.
""".strip()


def _build_user_prompt(
    user_query: str,
    evidence: list,
    image_analysis: list,
    graph_data: dict,
) -> str:
    """Monta o user prompt com os slots preenchidos."""
    return f"""
## Dados para Investigação

### Consulta do Usuário
{user_query}

### Evidências Coletadas
{json.dumps(evidence, ensure_ascii=False, indent=2)}

### Análise de Imagens
{json.dumps(image_analysis, ensure_ascii=False, indent=2)}

### Dados do Grafo de Relacionamentos
{json.dumps(graph_data, ensure_ascii=False, indent=2)}

## Instrução

Com base nos dados acima, gere um relatório investigativo estruturado em JSON.
Preencha TODOS os campos. Use "presente": false para seções sem dados.
Siga exatamente o schema especificado no system prompt.
"""


# ─── Funções de Fallback ────────────────────────────────────────────────────

_CONFIANCA_MAP = {
    "alta": "ALTA",
    "alto": "ALTA",
    "média": "MÉDIO",
    "media": "MÉDIO",
    "medio": "MÉDIO",
    "médio": "MÉDIO",
    "baixa": "BAIXO",
    "baixo": "BAIXO",
    "indeterminado": "INDETERMINADO",
    None: "MÉDIO",
}


def _normalizar_confianca(valor) -> str:
    """Normaliza nível de confiança (ex: 'MÉDIA' → 'MÉDIO')."""
    if valor is None:
        return "MÉDIO"
    return _CONFIANCA_MAP.get(valor.strip().lower(), "MÉDIO")

def _calcular_confianca_global(evidencias: list) -> str:
    """Calcula confiança global com base nas evidências."""
    if not evidencias:
        return "INDETERMINADO"

    niveis = [_normalizar_confianca(e.get("confianca")) for e in evidencias]

    criticas_baixas = any(
        n == "BAIXO" and e.get("relevancia", 1) >= 4
        for n, e in zip(niveis, evidencias)
    )

    if criticas_baixas:
        return "MÉDIO"

    if all(n in ("ALTA", "MÉDIO") for n in niveis):
        if any(n == "MÉDIO" for n in niveis):
            return "MÉDIO"
        return "ALTO"

    if "BAIXO" in niveis:
        return "BAIXO"

    return "MÉDIO"


def _gerar_fallback_relatorio(
    user_query: str,
    evidence: list,
    image_analysis: list,
    graph_data: dict,
) -> dict:
    """Gera relatório usando fallback baseado em template."""
    relatorio = copy.deepcopy(RELATORIO_EMPTY)
    hoje = str(date.today())

    # Título
    titulo_base = user_query[:80] if user_query else "Investigação"
    relatorio["titulo"] = f"Relatório de Investigação: {titulo_base}"
    relatorio["data"] = hoje
    relatorio["caso"] = f"CASO-{hoje.replace('-', '')}"

    # Confiança global
    conf_global = _calcular_confianca_global(evidence)
    relatorio["confianca_global"] = conf_global
    relatorio["investigador"] = "CIVITAS IA - v1.0 (FALLBACK)"

    # Resumo Executivo
    n_evidencias = len(evidence)
    descobertas = []
    for i, e in enumerate(evidence[:5]):
        conf = _normalizar_confianca(e.get("confianca"))
        desc = e.get("descricao", e.get("conteudo", ""))[:100]
        descobertas.append({
            "descoberta": f"Evidência {i+1}: {desc}",
            "confianca": conf,
        })

    if not descobertas:
        descobertas.append({
            "descoberta": "Nenhuma evidência disponível para análise.",
            "confianca": "INDETERMINADO",
        })

    relatorio["resumo_executivo"] = {
        "sintese": (
            f"Investigação baseada em {n_evidencias} evidência(s). "
            f"Consulta original: {user_query[:200]}"
        ),
        "descobertas_principais": descobertas,
        "urgencia": "alta" if "urgente" in user_query.lower() else "média",
    }

    # Evidências
    for e in evidence:
        tipo = e.get("tipo", "documental").lower()
        item = {
            "id": f"F-{len(relatorio['fontes_citadas'])+1:03d}",
            "documento": e.get("nome", e.get("conteudo", "Documento")),
            "fonte": e.get("fonte", "Não informada"),
            "data": e.get("data", hoje),
            "confianca": _normalizar_confianca(e.get("confianca")),
            "relevancia": e.get("relevancia", 3),
            "descricao": e.get("descricao", e.get("conteudo", "")),
        }
        if tipo in ("documental", "documento"):
            relatorio["evidencias"]["documentais"].append(item)
        elif tipo in ("testemunhal", "testemunha", "relato"):
            relatorio["evidencias"]["testemunhais"].append({
                **item,
                "fonte_anonimizada": e.get("fonte", "Anônimo"),
                "corroboracao": e.get("corroboracao", []),
            })
        elif tipo in ("digital", "forense"):
            relatorio["evidencias"]["digitais"].append({
                **item,
                "tipo": e.get("subtipo", "arquivo"),
                "hash": e.get("hash", "N/A"),
                "data_coleta": e.get("data", hoje),
                "cadeia_custodia": e.get("cadeia_custodia", "INCOMPLETA"),
            })

        relatorio["fontes_citadas"].append({
            "id": item["id"],
            "referencia": f"{item['documento']} — {item['fonte']}",
            "data_acesso": hoje,
        })

    # Análise de Imagens
    if image_analysis:
        imagens = []
        for img in image_analysis:
            imagens.append({
                "arquivo": img.get("arquivo", "imagem_sem_nome"),
                "metadados": {
                    "dimensoes": img.get("dimensoes", "N/A"),
                    "formato": img.get("formato", "desconhecido"),
                    "data_criacao": img.get("data_criacao", hoje),
                    "gps": img.get("gps"),
                },
                "autenticidade": img.get("autenticidade", "INDETERMINADO"),
                "tecnicas_detectadas": img.get("tecnicas_detectadas", []),
                "ferramenta": img.get("ferramenta", "Ferramentas CIVITAS"),
                "confianca": _normalizar_confianca(img.get("confianca")),
                "descricao": img.get("descricao", ""),
                "ocr": img.get("ocr"),
            })
        relatorio["analise_imagens"] = {"presente": True, "imagens": imagens}

    # Timeline
    eventos_timeline = []
    for e in evidence:
        if "data" in e and e.get("data"):
            eventos_timeline.append({
                "data_hora": e["data"],
                "evento": e.get("descricao", e.get("conteudo", "Evento"))[:200],
                "fonte": e.get("fonte", "Desconhecida"),
                "confianca": _normalizar_confianca(e.get("confianca")),
            })

    if eventos_timeline:
        eventos_timeline.sort(key=lambda x: x["data_hora"])
        relatorio["timeline"] = {
            "presente": True,
            "titulo": f"Timeline do Caso: {titulo_base[:50]}",
            "eventos": eventos_timeline,
        }

    # Grafo de Relacionamentos
    entidades = graph_data.get("entidades", [])
    relacoes = graph_data.get("relacoes", [])

    if entidades:
        relatorio["grafo_relacionamentos"] = {
            "presente": True,
            "entidades": entidades,
            "relacoes": relacoes,
            "metricas": {
                "nos": len(entidades),
                "arestas": len(relacoes),
                "densidade": round(
                    (2 * len(relacoes)) / (len(entidades) * (len(entidades) - 1))
                    if len(entidades) > 1 else 0.0, 4
                ),
                "componentes_conectados": len(entidades) - len(relacoes)
                if relacoes else len(entidades),
                "no_central": entidades[0]["id"] if entidades else "",
            },
        }

    # Análise e Recomendações
    relatorio["analise_recomendacoes"] = {
        "sintese_analitica": (
            f"Análise baseada em {n_evidencias} evidência(s) "
            f"com {len(relatorio['fontes_citadas'])} fonte(s) referenciada(s). "
            f"Confiança global: {conf_global}. "
            f"{'Foram analisadas ' + str(len(image_analysis)) + ' imagem(ns).' if image_analysis else ''} "
            f"{'Mapeadas ' + str(len(entidades)) + ' entidade(s).' if entidades else ''}"
        ),
        "recomendacoes_imediatas": [
            "Correlacionar todas as evidências disponíveis",
            "Verificar cadeia de custódia das evidências digitais",
        ],
        "recomendacoes_curto_prazo": [
            "Entrevistar fontes para corroborar evidências de confiança BAIXA",
            "Solicitar dados adicionais às fontes identificadas",
        ],
        "recomendacoes_medio_longo_prazo": [
            "Integrar dados com outros sistemas de inteligência",
            "Produzir relatório complementar com novas evidências",
        ],
        "lacunas": [
            {
                "lacuna": "Evidências não correlacionadas",
                "info_necessaria": "Cruzamento completo das evidências",
                "prioridade": "ALTA",
                "fonte_potencial": "Análise dos investigadores designados",
            }
        ],
    }

    return relatorio


# ─── API do Claude (tentativa) ──────────────────────────────────────────────

def _try_claude_api(
    user_prompt: str,
    model: str = DEFAULT_MODEL,
) -> Optional[str]:
    """Tenta chamar a API do Claude Haiku. Retorna texto da resposta ou None."""
    try:
        import anthropic

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return None

        client = anthropic.Anthropic(api_key=api_key)

        message = client.messages.create(
            model=model,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        return message.content[0].text

    except ImportError:
        return None
    except Exception as e:
        print(f"[CIVITAS] Erro na API Claude: {e}", file=sys.stderr)
        return None


def _parse_json_response(texto: str) -> Optional[dict]:
    """Tenta extrair e parsear JSON da resposta do Claude."""
    if not texto:
        return None

    # Tenta parse direto
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        pass

    # Tenta extrair bloco JSON entre ``` ou ```json
    for marker in ["```json", "```"]:
        if marker in texto:
            partes = texto.split(marker)
            if len(partes) >= 2:
                bloco = partes[1].split("```")[0].strip()
                try:
                    return json.loads(bloco)
                except json.JSONDecodeError:
                    continue

    return None


def _validar_relatorio(relatorio: dict) -> dict:
    """Valida e corrige campos obrigatórios do relatório."""
    campos_obrigatorios = [
        "titulo", "data", "caso", "classificacao",
        "investigador", "confianca_global",
    ]

    for campo in campos_obrigatorios:
        if campo not in relatorio or not relatorio[campo]:
            relatorio[campo] = RELATORIO_EMPTY.get(campo, "")

    # Confiança global válida
    if relatorio.get("confianca_global") not in CONFIANCA_VALORES:
        relatorio["confianca_global"] = "MÉDIO"

    # Resumo executivo
    if "resumo_executivo" not in relatorio:
        relatorio["resumo_executivo"] = RELATORIO_EMPTY["resumo_executivo"]

    # Evidências
    if "evidencias" not in relatorio:
        relatorio["evidencias"] = RELATORIO_EMPTY["evidencias"]

    # Seções condicionais
    for secao in ["analise_imagens", "timeline", "grafo_relacionamentos"]:
        if secao not in relatorio:
            relatorio[secao] = RELATORIO_EMPTY[secao]

    return relatorio


# ─── Função Principal ───────────────────────────────────────────────────────

def generate_report(
    user_query: str,
    evidence: Optional[list] = None,
    image_analysis: Optional[list] = None,
    graph_data: Optional[dict] = None,
    use_fallback: bool = False,
) -> dict:
    """
    Gera um relatório investigativo estruturado.

    Args:
        user_query: Consulta / descrição do caso pelo usuário
        evidence: Lista de evidências [{tipo, conteudo, fonte, data, confianca, ...}]
        image_analysis: Lista de análises de imagem [{arquivo, descricao, ...}]
        graph_data: Dict com entidades e relacoes para o grafo
        use_fallback: Força fallback mesmo se API disponível

    Returns:
        Dict com relatório estruturado conforme schema do CIVITAS
    """
    user_query = user_query or "Investigação não especificada"
    evidence = evidence or []
    image_analysis = image_analysis or []
    graph_data = graph_data or {"entidades": [], "relacoes": []}

    # Tenta Claude API
    if not use_fallback:
        user_prompt = _build_user_prompt(
            user_query, evidence, image_analysis, graph_data
        )

        for tentativa in range(MAX_RETRIES + 1):
            resposta = _try_claude_api(user_prompt)
            if resposta:
                relatorio = _parse_json_response(resposta)
                if relatorio:
                    print(f"[CIVITAS] Relatório gerado via Claude Haiku (tentativa {tentativa+1})")
                    return _validar_relatorio(relatorio)
                else:
                    print(
                        f"[CIVITAS] Resposta não-JSON recebida. Tentativa {tentativa+1}.",
                        file=sys.stderr,
                    )
            else:
                if tentativa < MAX_RETRIES:
                    print(
                        f"[CIVITAS] API indisponível. Tentativa {tentativa+1}/{MAX_RETRIES}.",
                        file=sys.stderr,
                    )

    # Fallback
    print("[CIVITAS] Usando fallback local (template-based).")
    return _validar_relatorio(
        _gerar_fallback_relatorio(user_query, evidence, image_analysis, graph_data)
    )


# ─── CLI ────────────────────────────────────────────────────────────────────

def main():
    """Executa o gerador a partir de linha de comando."""
    import argparse

    parser = argparse.ArgumentParser(
        description="CIVITAS - Gerador de Relatórios Investigativos"
    )
    parser.add_argument(
        "--query", "-q",
        default="Investigação padrão",
        help="Consulta / descrição do caso",
    )
    parser.add_argument(
        "--evidence", "-e",
        type=str,
        help="Arquivo JSON com evidências (lista)",
    )
    parser.add_argument(
        "--images", "-i",
        type=str,
        help="Arquivo JSON com análises de imagem (lista)",
    )
    parser.add_argument(
        "--graph", "-g",
        type=str,
        help="Arquivo JSON com dados do grafo (dict)",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="relatorio_investigativo.json",
        help="Arquivo de saída para o relatório JSON",
    )
    parser.add_argument(
        "--fallback", "-f",
        action="store_true",
        help="Forçar uso de fallback (sem Claude)",
    )
    parser.add_argument(
        "--markdown", "-m",
        action="store_true",
        help="Gerar também versão Markdown legível",
    )

    args = parser.parse_args()

    # Carrega dados
    def _load_json(path: str, default=None):
        if path:
            try:
                with open(path, "r") as f:
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"[CIVITAS] Erro ao ler {path}: {e}", file=sys.stderr)
        return default

    evidence = _load_json(args.evidence, [])
    images = _load_json(args.images, [])
    graph = _load_json(args.graph, {"entidades": [], "relacoes": []})

    # Gera relatório
    relatorio = generate_report(
        user_query=args.query,
        evidence=evidence,
        image_analysis=images,
        graph_data=graph,
        use_fallback=args.fallback,
    )

    # Salva
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(relatorio, f, ensure_ascii=False, indent=2)
    print(f"[CIVITAS] Relatório salvo em: {args.output}")

    # Versão Markdown (opcional)
    if args.markdown:
        md_path = args.output.replace(".json", ".md")
        _salvar_markdown(relatorio, md_path)
        print(f"[CIVITAS] Versão Markdown salva em: {md_path}")

    return relatorio


def _salvar_markdown(relatorio: dict, path: str):
    """Gera versão Markdown do relatório para leitura humana."""
    r = relatorio
    lines = []

    lines.append(f"# {r.get('titulo', 'Relatório')}")
    lines.append("")
    lines.append(f"- **Data:** {r.get('data', 'N/A')}")
    lines.append(f"- **Caso:** {r.get('caso', 'N/A')}")
    lines.append(f"- **Classificação:** {r.get('classificacao', 'N/A')}")
    lines.append(f"- **Investigador:** {r.get('investigador', 'N/A')}")
    lines.append(f"- **Confiança Global:** {r.get('confianca_global', 'N/A')}")
    lines.append("")

    # Resumo Executivo
    if "resumo_executivo" in r:
        re = r["resumo_executivo"]
        lines.append("## Resumo Executivo")
        lines.append("")
        lines.append(re.get("sintese", ""))
        lines.append("")
        lines.append("**Descobertas Principais:**")
        for d in re.get("descobertas_principais", []):
            conf = d.get("confianca", "N/A")
            lines.append(f"- {d.get('descoberta', '')} (confiança: {conf})")
        lines.append("")
        lines.append(f"**Urgência:** {re.get('urgencia', 'N/A')}")
        lines.append("")

    # Evidências
    if "evidencias" in r:
        ev = r["evidencias"]
        lines.append("## Evidências")
        lines.append("")

        for tipo, titulo in [("documentais", "Documentais"),
                              ("testemunhais", "Testemunhais"),
                              ("digitais", "Digitais/Forenses")]:
            itens = ev.get(tipo, [])
            if itens:
                lines.append(f"### {titulo}")
                lines.append("")
                lines.append("| ID | Descrição | Confiança | Fonte |")
                lines.append("|----|-----------|-----------|-------|")
                for item in itens:
                    lines.append(
                        f"| {item.get('id', 'N/A')} | "
                        f"{item.get('descricao', item.get('documento', ''))[:80]} | "
                        f"{item.get('confianca', 'N/A')} | "
                        f"{item.get('fonte', 'N/A')} |"
                    )
                lines.append("")

    # Análise de Imagens
    if r.get("analise_imagens", {}).get("presente"):
        lines.append("## Análise de Imagens")
        lines.append("")
        for img in r["analise_imagens"]["imagens"]:
            lines.append(f"### {img.get('arquivo', 'Imagem')}")
            lines.append(f"- **Autenticidade:** {img.get('autenticidade', 'N/A')}")
            lines.append(f"- **Descrição:** {img.get('descricao', 'N/A')}")
            lines.append("")

    # Timeline
    if r.get("timeline", {}).get("presente"):
        lines.append("## Timeline")
        lines.append("")
        lines.append(f"**{r['timeline'].get('titulo', 'Eventos')}**")
        lines.append("")
        for evt in r["timeline"].get("eventos", []):
            lines.append(
                f"- **{evt.get('data_hora', 'N/A')}** — {evt.get('evento', '')} "
                f"(confiança: {evt.get('confianca', 'N/A')})"
            )
        lines.append("")

    # Grafo
    if r.get("grafo_relacionamentos", {}).get("presente"):
        lines.append("## Grafo de Relacionamentos")
        lines.append("")
        for ent in r["grafo_relacionamentos"].get("entidades", []):
            lines.append(
                f"- [{ent.get('id', 'N/A')}] {ent.get('nome', '')} "
                f"({ent.get('tipo', '')})"
            )
        lines.append("")
        for rel in r["grafo_relacionamentos"].get("relacoes", []):
            lines.append(
                f"- {rel.get('origem', '')} → {rel.get('destino', '')} "
                f"[{rel.get('tipo_relacao', '')}, {rel.get('forca_vinculo', '')}]"
            )
        lines.append("")

    # Análise e Recomendações
    if "analise_recomendacoes" in r:
        ar = r["analise_recomendacoes"]
        lines.append("## Análise e Recomendações")
        lines.append("")
        lines.append(ar.get("sintese_analitica", ""))
        lines.append("")

        for titulo, campo in [("Recomendações Imediatas", "recomendacoes_imediatas"),
                               ("Curto Prazo (1-7 dias)", "recomendacoes_curto_prazo"),
                               ("Médio/Longo Prazo", "recomendacoes_medio_longo_prazo")]:
            items = ar.get(campo, [])
            if items:
                lines.append(f"**{titulo}:**")
                for item in items:
                    lines.append(f"- {item}")
                lines.append("")

        # Lacunas
        lacunas = ar.get("lacunas", [])
        if lacunas:
            lines.append("### Lacunas e Próximos Passos")
            lines.append("")
            lines.append("| Lacuna | Prioridade | Fonte Potencial |")
            lines.append("|--------|------------|------------------|")
            for lac in lacunas:
                lines.append(
                    f"| {lac.get('lacuna', '')} | "
                    f"{lac.get('prioridade', 'N/A')} | "
                    f"{lac.get('fonte_potencial', 'N/A')} |"
                )
            lines.append("")

    # Fontes Citadas
    if "fontes_citadas" in r:
        lines.append("---")
        lines.append("### Fontes Citadas")
        lines.append("")
        for fonte in r["fontes_citadas"]:
            lines.append(
                f"- {fonte.get('id', 'N/A')}: {fonte.get('referencia', '')} "
                f"(acesso: {fonte.get('data_acesso', 'N/A')})"
            )

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
