# 🏙️ Resumo do Desafio: CompStat Rio (Claude Impact Lab)

## 📌 Contexto

O **CompStat Municipal** é o modelo de gestão de segurança pública da Prefeitura do Rio de Janeiro. Ele utiliza dados criminais e inteligência territorial para coordenar ações entre a Força Municipal (focada em policiamento preventivo) e órgãos municipais (Comlurb, RioLuz, SEOP, etc., focados em resolver problemas urbanos que favorecem o crime, como falta de iluminação ou vias obstruídas).

## ⚠️ O Problema Atual

Atualmente, os dados necessários para o planejamento tático vivem em **silos isolados** (boletins de ocorrência, denúncias anônimas, relatórios de inteligência, mapeamento de problemas urbanos). O cruzamento dessas informações e a produção de relatórios para as reuniões semanais da alta gestão exigem muitas **horas de trabalho manual**.

## 🎯 O Objetivo Principal

Criar uma **plataforma de inteligência criminal potencializada por IA** para automatizar esse fluxo analítico. A solução deve:

1. **Integrar Dados:** Unificar automaticamente 5 fontes principais (Ocorrências, Disque Denúncia, Relatórios de Inteligência, Fatores Urbanos e Áreas de Atuação).
2. **Cruzar Informações:** Sobrepor dados quantitativos (mancha criminal) com qualitativos e espaciais para identificar **coincidências de alto risco** (áreas onde crimes, dinâmica criminal e problemas urbanos se encontram).
3. **Automatizar Relatórios:** Gerar automaticamente os **Relatórios Analíticos de Área** em formato `.doc` (contendo resumos, análise de cenários e planos de ação).
4. **Recomendar Ações via IA:**
    - Sugerir a alocação tática da Força Municipal (horário, local e modalidade de patrulhamento), otimizando o limite de 600 agentes.
    - Direcionar ordens de serviço precisas para outros órgãos atuarem na zeladoria urbana (ex: poda de árvores onde ocorrem furtos noturnos).

## 🚀 Desafios Extras (Opcionais)

O projeto também propõe 4 desafios complementares para expandir a capacidade analítica da prefeitura:

1. **Inteligência de Redes Sociais:** Monitorar, estruturar e geolocalizar menções sobre crimes e segurança pública nas redes.
2. **Migração do Crime:** Detectar e prever a migração da criminalidade para áreas vizinhas em resposta às operações em andamento.
3. **Decisão de Permanência Operacional:** Criar painéis de indicadores para apoiar a decisão de manter ou retirar operações após o ciclo inicial de 90 dias.
4. **Otimização de Câmeras:** Cruzar mapas de calor de ocorrências com a infraestrutura atual para identificar "pontos cegos" e sugerir a instalação de novas câmeras.

---

# 📊 Mapeamento e Relacionamento de Dados — CompStat Rio

Para construir a plataforma de inteligência do CompStat, não basta analisar os dados isoladamente. O verdadeiro valor está na **topologia relacional** entre eles. Abaixo, apresento a dissecação de cada base e como elas se interconectam.

---

## 1. Análise Individual dos Datasets

### 🔴 Ocorrências Criminais (`df_ocorrencias_tratado`)

- **Natureza:** Dados Estruturados Quantitativos.
- **Atributos Chave:** `latitude`, `longitude`, `data`, `hora`, `dia_semana`, `desc_delito`.
- **O que representa:** O *Efeito*. É a "temperatura" da criminalidade. Mostra exatamente a gravidade geométrica do problema, definindo a mancha criminal (hotspots).

### 🌳 Fatores Urbanos (`fatores_urbanos.csv`)

- **Natureza:** Dados Estruturados de Auditoria Ambiental.
- **Atributos Chave:** `coordenada_x`, `coordenada_y`, `tipo_ocorrencia_descricao`, `orgao_responsavel`, `subarea_nome`.
- **O que representa:** A *Causa Material*. Mostra o cenário que propicia o crime de oportunidade (ex: mato alto, poste apagado, calçada estreita).

### 📞 Disque Denúncia (`disk_denuncia.csv`) & 📄 RelInts (`relints/`)

- **Natureza:** Dados Semi-Estruturados e Não-Estruturados (Qualitativos).
- **Atributos Chave:** Textos narrativos, relatos de moradores, análises de inteligência.
- **O que representa:** A *Dinâmica e o Modus Operandi*. Explica como o crime acontece. Enquanto as ocorrências dizem "houve 10 roubos aqui", a denúncia diz "são 2 homens de moto vermelha armados que fogem para a praça".

### 📹 Câmeras de Segurança (`cameras_areas_fm.csv`)

- **Natureza:** Dados de Infraestrutura Espacial (Pontos).
- **Atributos Chave:** `id_ponto`, `geometry`, `nome_area_fm`.
- **O que representa:** A *Capacidade de Resposta/Monitoramento*. Define o campo de visão do estado.

### 🚩 Domínio Territorial (`dominio_territorial.csv`)

- **Natureza:** Dados Poligonais Sócio-Geográficos.
- **Atributos Chave:** Polígonos de fronteira, facção dominante.
- **O que representa:** A *Geopolítica Local*. Altera as regras de engajamento da Força Municipal e explica rotas de evasão.

### 🗺️ Polígonos da Força Municipal (`sh_area_forca/`)

- **Natureza:** Limites Geográficos (Shapefiles).
- **O que representa:** A *Jurisdição Analítica*. As 22 áreas prioritárias onde o modelo CompStat atua.

---

## 2. A Arquitetura Relacional (Como os dados se conectam)

O relacionamento entre esses dados **não se dá por chaves primárias/estrangeiras clássicas** (como `id_cliente` = `id_cliente`), mas sim através de **Relacionamentos Espaciais (Spatial Joins)** e **Relacionamentos Temporais**.

O diagrama abaixo ilustra o motor analítico que a IA precisará construir:

```mermaid
graph TD
    %% Entidades de Dados
    BO[(Ocorrências\\nCriminais)]
    FU[(Fatores\\nUrbanos)]
    DD[(Disque Denúncia\\n& RelInts)]
    CAM[(Câmeras)]
    DT[(Domínio\\nTerritorial)]
    FM_AREA{Áreas da\\nForça Municipal}

    %% Conectores Analíticos Espaciais
    BO -- "Spatial Join (Está dentro de?)" --> FM_AREA
    FU -- "Spatial Join (Está dentro de?)" --> FM_AREA
    CAM -- "Spatial Join (Está dentro de?)" --> FM_AREA

    %% O Coração da IA
    subgraph IA [Motor de Inteligência (IA)]
        MATCH{{"Coincidência de\\nAlto Risco"}}
        NLP["Extração de NLP\\n(Local, Veículo, Arma)"]
        BUFFER["Análise de Proximidade\\n(Raio de 50m-100m)"]
    end

    %% Fluxo para a IA
    DD -- Textos --> NLP
    NLP -- "Geolocalização inferida" --> BUFFER
    BO -- "Lat/Long + Horário" --> BUFFER
    FU -- "Coordenada + Categoria" --> BUFFER
    DT -- "Polígonos de Risco (Vizinhança)" --> BUFFER

    BUFFER --> MATCH

    %% Saídas e Ações
    MATCH -- Gera Plano Tático --> GM["Recomendação:\\nPatrulhamento FM\\n(Onde, Quando, Como)"]
    MATCH -- Gera Ordem de Serviço --> ORG["Recomendação:\\nÓrgãos Municipais\\n(Comlurb, RioLuz, SEOP)"]

    %% Desafios Extras
    BO -. "Spatial Difference" .- CAM
    CAM -. "Pontos Cegos" .-> CEGO["Recomendação de\\nNovas Câmeras"]
```

### Explicação das Relações (Spatial Joins)

1. **Relação Ocorrência ↔ Fator Urbano (A Coincidência de Risco)**
    - **Ligação:** `Buffer` Espacial (Ex: Raio de 50 metros) e sobreposição de horários.
    - **Exemplo:** Se as Ocorrências de roubo se concentram entre 19h e 22h no Ponto A, e o dataset de Fatores Urbanos aponta "Vegetação obstruindo visibilidade" ou "Área mal iluminada" no mesmo Ponto A (ou a 20 metros dali), a IA estabelece uma relação de causalidade ambiental. O output é acionar a RioLuz/Comlurb.
2. **Relação Ocorrência ↔ Denúncia/RelInt (O Enriquecimento)**
    - **Ligação:** Extração de Entidades Nomeadas (NLP) → Geocodificação → Join Espacial.
    - **Exemplo:** A IA lê o texto da denúncia, encontra a rua "Rua do Catete", geolocaliza a rua, e cruza com a mancha de `Ocorrências` daquela rua. Isso transforma o "ponto quente" no mapa em um "ponto quente com fuga de moto e homens armados", mudando a tática recomendada da FM de "patrulha a pé" para "viatura ostensiva".
3. **Relação Ocorrência ↔ Câmeras (A Relação Inversa)**
    - **Ligação:** Operação de Subtração Espacial (Anti-Join).
    - **Exemplo:** A IA varre o mapa buscando alta densidade de `Ocorrências` e calcula a distância para a `Câmera` mais próxima. Se o raio de visão da câmera não cobre a mancha criminal, a relação identificada é um **Ponto Cego**, gerando uma recomendação técnica para o Centro de Operações (COR) instalar uma câmera (Desafio Extra 4).
4. **Relação Geral ↔ Áreas da Força Municipal (A Contenção)**
    - **Ligação:** Intersecção de Polígonos.
    - **Exemplo:** Todos esses dados são filtrados pelos shapefiles das 22 áreas. O produto final é um relatório `.doc` por área, listando os problemas e soluções agrupados geograficamente.

# 🏗️ Mapeamento Arquitetural CompStat Rio: Do Dado Bruto ao Relatório Analítico

Após uma inspeção minuciosa na estrutura real de cada arquivo CSV, do `README.md` e do documento estratégico `Briefing_Hackathon_Desenvolvedores_CompStat-2.pdf`, consolidei este mapeamento definitivo.

O desafio central proposto no briefing não é criar um simples dashboard de BI, mas sim **um motor de IA que automatize o "Relatório Analítico de Área"** (modelo Anexo 12 do PDF). Para isso, a IA deve realizar a "Coincidência de Risco" (o *"Bingo"*) cruzando as camadas descritas abaixo.

---

## 1. Dicionário Técnico por Dataset vs. Objetivo no Briefing

### 🔴 1. Ocorrências Criminais (`df_ocorrencias_tratado - Extração 1 .csv`)

- **Estrutura (Separador `,`):** `id_criptografado`, `ano`, `data`, `mes`, `hora`, `delito`, `longitude`, `latitude`, `desc_delito`, `aisp`, `risp`, `locf`, `dia_semana`, `geometria`.
- **Papel no Relatório Final:**
    - **Análise Temporal:** Os campos `hora` e `dia_semana` calculam o "Período Predominante" e o "Dia/Horário Crítico" (ex: Sextas e Sábados às 21h).
    - **Mapa de Calor:** `latitude` e `longitude` alimentam a densidade espacial de roubos a transeunte/celular.
- **O que a IA deve fazer:** Agrupamento estatístico e *Clustering* espacial (DBSCAN/HDBSCAN) para encontrar os verdadeiros "Segmentos Críticos" (trechos de rua específicos).

### 📞 2. Disque Denúncia (`disk_denuncia.csv`)

- **Estrutura (Separador `;`):** `latitude`, `longitude`, `assuntos.assunto_principal`, `envolvidos.sexo`, `envolvidos.idade`, `envolvidos.porte`, `relato_redacted` (texto livre), entre outros.
- **Papel no Relatório Final:**
    - **Dinâmica Criminal (IA Qualitativa):** Este é o arquivo mais complexo. O PDF exige que a IA responda "qual é o modus operandi?".
- **O que a IA deve fazer:** Usar um LLM ou técnica de NLP sobre o campo de texto `relato_redacted` filtrado espacialmente para os "Segmentos Críticos" identificados nas ocorrências, extraindo se os criminosos usam motos, se são grupos armados, e quais as rotas de escoamento.

### 🌳 3. Fatores Urbanos (`fatores_urbanos.csv`)

- **Estrutura (Separador `,`):** `coordenada_x`, `coordenada_y`, `tipo_ocorrencia_descricao`, `orgao_responsavel`, `observacao` (texto), `bairro_nome`, `subarea_nome`.
- **Papel no Relatório Final:**
    - **Plano de Ação e Responsabilização:** Preenche a tabela de ações.
- **O que a IA deve fazer:** Fazer um *Spatial Join* (raio de tolerância, ex: 50 metros) com os clusters criminais. Se há um cluster criminal e a `coordenada` deste CSV diz `tipo_ocorrencia_descricao = "Área mal iluminada"`, a IA gera automaticamente a tarefa: **Responsável: RioLuz | Ação: Manutenção de postes apagados**.

### 🚩 4. Domínio Territorial (`dominio_territorial - Extração 1.csv`)

- **Estrutura (Separador `,`):** `nome_territorio`, `dominio_orcrim` (ex: ADA, CV, TCP), `geometria` (POLYGON).
- **Papel no Relatório Final:**
    - **Identificação da Área:** Preenche o campo "Área sob influência de grupo criminoso".
    - **Rotas de Fuga:** Explica a evasão.
- **O que a IA deve fazer:** Identificar se o "Segmento Crítico" criminal faz fronteira ou está contido no polígono do `geometria`. A polícia militar ou a FM não devem fazer patrulha velada em certas divisas sem apoio tático pesado.

### 📹 5. Câmeras de Segurança (`cameras_areas_fm.csv`)

- **Estrutura (Separador `,`):** `id_ponto`, `nome_area_fm`, `id_trecho`, `geometry` (POINT).
- **Papel no Relatório Final:**
    - **Desafio Extra / Mapa de Calor:** Identificar "Pontos Cegos".
- **O que a IA deve fazer:** Diferença espacial. Locais com densidade de `df_ocorrencias` que possuam distância `> X metros` da `geometry` de qualquer câmera devem gerar um "Alerta de Ponto Cego".

---

## 2. A Lógica de Decisão da IA (O "BINGO" do CompStat)

O PDF do Briefing (Seção 5.1) detalha perfeitamente como a IA deve raciocinar para gerar o "Plano de Ação Gerado". Eis o algoritmo mental que devemos programar:

**Se [MANCHA CRIMINAL] + [FATOR URBANO] + [DINÂMICA] = BINGO!**

### Exemplo Algorítmico (Pipeline NLP + GeoPandas):

1. **Passo 1 (Filtragem):** Pega a Área FM "Lauro Müller".
2. **Passo 2 (Geo Spatial):** Identifica um cluster denso de `df_ocorrencias` no trecho da "Av. Pasteur" (Horário crítico: 19h-21h).
3. **Passo 3 (Verificação de Causa):** Faz uma busca de `fatores_urbanos.csv` em um raio de 50m. Encontra `orgao_responsavel = "Seconserva"` e `tipo = "Calçadas estreitas forçando pedestres à pista"`.
4. **Passo 4 (NLP):** Busca `disk_denuncia.csv` nos mesmos 50m. O LLM lê os `relato_redacted` e extrai: *"ladrões em dupla de bicicleta assaltam pedestres no asfalto e fogem para o Túnel"*.
5. **Passo 5 (Domínio):** O Túnel cruza com `dominio_territorial = "CV"`.
6. **Passo 6 (Geração do Relatório):** O LLM cospe o Markdown/DOC final:
    - **Diagnóstico:** Roubos a transeunte concentrados (19h-21h), facilitados por calçada estreita (forçando vítimas à pista) com evasão rápida de bicicleta para território CV.
    - **Ação FM:** Patrulha ostensiva de Motos entre 18h30 e 21h30 nas saídas do túnel.
    - **Ação Seconserva:** Estudo para alargamento de calçada ou instalação de gradil de proteção.

---

## 3. Conclusão para o Desenvolvimento

Para gabaritar este Hackathon, o código não precisa ser uma IA generalista. Precisamos de uma "Linha de Montagem" de dados:

1. **Script de Ingestão Geográfica:** Script em Python (`geopandas`, `shapely`) que padronize lat/long, POINT e POLYGON para o mesmo Sistema de Referência de Coordenadas (CRS, ex: EPSG:4326).
2. **Script de NLP:** Uma rotina simples que passe os textos aglomerados de `disk_denuncia` e `relints` em um LLM (ex: Claude) pedindo para retornar um JSON estruturado com `{modalidade: "", armas: "", fuga: ""}`.
3. **Gerador de Documentos:** Um script que pegue essas saídas (clusters criminais e ações urbanas) e preencha um template pré-formatado parecido com o **12. Anexo do PDF**, exportando em `.docx` ou `.pdf`.

# times series

Sim, com certeza! A criação de **séries temporais** não só é possível, como é um **requisito obrigatório** estabelecido no Briefing Técnico (Módulo *Análise Temporal*, que aparece nas páginas 13 e 14 do PDF).

A base de dados de **Ocorrências Criminais** (`df_ocorrencias_tratado`) foi estruturada perfeitamente para isso. Veja as colunas que temos à disposição:

- `ano`, `mes`, `data` (Data exata do crime)
- `hora` (Horário do crime)
- `dia_semana` (Dia da semana)

Com essas colunas, podemos construir o código em Python (usando `Pandas` e bibliotecas visuais como `Seaborn` ou `Plotly`) para extrair três tipos de análises temporais cruciais para o relatório do CompStat:

### 1. Evolução Histórica (Linha do Tempo)

- **Como fazer:** Agrupando os dados por `ano` e `mes` (`df.groupby(['ano', 'mes'])['id_criptografado'].count()`).
- **O que responde:** Mostra se os crimes estão subindo ou descendo ao longo do ano na área da Força Municipal. É o clássico gráfico de linhas de tendência.

### 2. Mapa de Calor Temporal (Dia da Semana x Hora)

- **Como fazer:** Criando uma matriz cruzada (*Pivot Table*) colocando os `dias_semana` nas linhas (Segunda a Domingo) e a `hora` (00h às 23h) nas colunas.
- **O que responde:** Isso reproduz exatamente o gráfico exigido na página 14 do PDF. Permite que a IA bata o olho na matriz e diga: *"Atenção, há uma concentração gigante de roubos às Sextas-feiras entre 21h e 23h"*.

### 3. Extração do "Período Crítico" via Algoritmo

- **Como fazer:** Escrever uma função que encontre o "pico" da matriz temporal gerada acima.
- **O que responde:** O Briefing exige que a plataforma indique **Qual deve ser o horário de patrulhamento da FM**. Se a série temporal detecta o pico às 21h, a IA escreve automaticamente no relatório: *"Horário de pico do crime coincide com o período da noite. Ação recomendada: Alocar reforço de patrulhamento da Força Municipal das 20h às 00h."*

### Desafio Extra: Análise de "Time Lag" (Atraso)

Como temos a data do crime nas **Ocorrências** e a data da denúncia no **Disque Denúncia** (`data_denuncia`), podemos fazer uma série temporal avançada medindo o *Tempo de Reação* da sociedade. (Ex: "Quantos dias após uma onda de furtos as denúncias sobre os suspeitos começam a chegar?").

Você quer que eu construa e mostre o **script em Python (Pandas)** que você poderia rodar para gerar essa matriz temporal e extrair automaticamente o horário crítico dos dados?