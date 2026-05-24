# CIVITAS — Bootstrap (Front-end ↔ Back-end)

Guia rápido pra quem **não vai escrever Python**, mas precisa garantir que
o backend está respondendo certinho antes de chamar a API a partir do front.

> **TL;DR (3 comandos)**
> ```bash
> git clone --recurse-submodules https://github.com/carloshnp/hexagon.git
> cd hexagon
> bash perri/scripts/setup_data.sh --install
> ```
> Depois:
> ```bash
> cd perri && uvicorn hexagon_spatial.app:app --reload --port 8000
> ```

---

## 1. Por que existe um script de setup?

Os dados (24 MB de ocorrências, 19 MB de denúncias, RELINTs, shapefile) ficam
em **outro repositório público** vinculado ao principal como `git submodule`:

```
hexagon/                                                 ← repo principal
└── perri/hexagon_spatial/
    └── claude_impact_lab_compstat_rio/  ───►  https://github.com/CompStat-Rio/claude_impact_lab_compstat_rio
```

Quem clona o `hexagon` sozinho **não recebe os dados** automaticamente.
O script `perri/scripts/setup_data.sh`:

1. Sincroniza o submódulo (faz o pull dos dados).
2. Confere que todos os arquivos esperados estão lá.
3. Confere/instala dependências Python.
4. Gera os exports estáticos (`relints.json` + `areas_detalhadas.csv`).
5. Roda os smoke tests da API.

Se algo falhar, ele sai com status ≠ 0 e mostra exatamente o quê.

## 2. Pré-requisitos

| Ferramenta | Versão mínima |
|---|---|
| `git`      | 2.x |
| `python3`  | 3.10+ (validado em 3.13) |
| `pip`      | qualquer |

No WSL/Ubuntu: `sudo apt install -y git python3 python3-pip`.

## 3. Como rodar

```bash
# Clone (já trazendo o submódulo)
git clone --recurse-submodules https://github.com/carloshnp/hexagon.git
cd hexagon

# Bootstrap — instala deps e prepara tudo
bash perri/scripts/setup_data.sh --install
```

Flags disponíveis:

| flag | efeito |
|---|---|
| `--install` | roda `pip install -q -r requirements.txt` |
| `--skip-tests` | pula os smoke tests (útil em CI rápido) |
| `-h`, `--help` | mostra a ajuda |

Já clonou sem o `--recurse-submodules`? Roda só:
```bash
bash perri/scripts/setup_data.sh
```
ele cuida do `submodule update --init` por você.

## 4. Saída esperada

```
==> 1/5  Sincronizando submodule de dados
  [ok]   submodule em 2420bc2

==> 2/5  Verificando arquivos esperados
  [ok]   df_ocorrencias_tratado - Extração 1 .csv (24M)
  [ok]   disk_denuncia.csv (19M)
  [ok]   cameras_areas_fm.csv (144K)
  [ok]   fatores_urbanos.csv (1.3M)
  [ok]   areas_forca_municipal.shp (8.0K)
  [ok]   8 RELINT .docx

==> 3/5  Verificando Python
  [ok]   python 3.13
  [ok]   pacotes principais presentes

==> 4/5  Gerando exports estáticos
  [ok]   exports/relints.json (156K)
  [ok]   exports/areas_detalhadas.csv (24 linhas + header)

==> 5/5  Rodando smoke tests
  [ok]   34 asserções verdes, 0 falhas

==> Setup completo
```

## 5. O que o front-end pode consumir depois

### 5.1 API ao vivo (recomendado)

```bash
cd perri && uvicorn hexagon_spatial.app:app --reload --port 8000
```

Endpoints — schemas completos em [API.md](./API.md):

| Endpoint | Para que serve |
|---|---|
| `GET /relints/parametros` | dicionário dos 5 fatores canônicos |
| `GET /relints/agencias` | 8 áreas (centróide, bbox, RELINT casado) — payload leve |
| `GET /relints/agencias/{fid}` | 1 área com polígono GeoJSON + RELINT completo |
| `GET /relints/` | lista todos os RELINTs estruturados |
| `GET /relints/{codigo}` | RELINT por código (ex.: `RI_010_2026`) |
| `GET /spatial/priority-areas?top_n=5` | top-N células H3 (geral + 6 instituições) |

### 5.2 Arquivos estáticos (CDN-friendly)

Gerados pelo script em `perri/hexagon_spatial/exports/`:

| Arquivo | Schema |
|---|---|
| `relints.json` | `{ agencias: AgencyFull[], relints: Relint[] }` — mesma forma da API |
| `areas_detalhadas.csv` | 24 linhas (8 agências × 3 sub-áreas), 22 colunas — detalhado em [API.md §5.2](./API.md) |

## 6. Atualizar os dados depois

O backend roda em cima de uma versão **fixa** do submódulo (commit pinado).
Quando o repo de dados receber atualizações:

```bash
git submodule update --remote perri/hexagon_spatial/claude_impact_lab_compstat_rio
bash perri/scripts/setup_data.sh                # regera exports + testa
git add perri/hexagon_spatial/claude_impact_lab_compstat_rio
git commit -m "data: bump submodule"
```

## 7. Verificações úteis para o front

| Cenário | Como testar |
|---|---|
| API está no ar | `curl -s http://localhost:8000/ \| jq .name` → `"CIVITAS Spatial API"` |
| Dados carregados | `curl -s http://localhost:8000/relints/agencias \| jq 'length'` → `8` |
| Pipeline OK | `curl -s 'http://localhost:8000/spatial/priority-areas?top_n=3' \| jq .n_hotspot_clusters` → `> 0` |
| Exports atuais | `wc -l perri/hexagon_spatial/exports/areas_detalhadas.csv` → `25` (24 + header) |

## 8. Quando algo dá errado

| Sintoma | Provável causa | Fix |
|---|---|---|
| `submodule path 'X' not initialized` | Clonou sem `--recurse-submodules` | `git submodule update --init` |
| `ModuleNotFoundError: geopandas` | Faltou instalar deps | rodar script com `--install` |
| `404 fid 999 não encontrado` | Fid não existe | fids válidos: `2, 9, 10, 11, 12, 14, 19, 20` |
| API responde mas demora 5–7 s | 1ª chamada do `/spatial/*` (sem cache) | Esperado — depois cacheia em memória |
| `500` em `/spatial/*` | Dados ausentes no submódulo | Reexecutar `setup_data.sh` |

## 9. Estrutura entregue ao backend após o script

```
perri/
├── scripts/
│   └── setup_data.sh                            ← este script
└── hexagon_spatial/
    ├── app.py                                   ← FastAPI (porta 8000)
    ├── API.md                                   ← contrato completo
    ├── SETUP.md                                 ← este documento
    ├── exports/
    │   ├── relints.json                         ← consumível direto
    │   ├── areas_detalhadas.csv                 ← consumível direto
    │   └── api_samples/                         ← payloads de exemplo (1 por endpoint)
    └── claude_impact_lab_compstat_rio/          ← git submodule (dados)
        ├── dados/                               ← 4 CSVs do ISP-RJ/Disque/etc.
        ├── relints/                             ← 8 .docx
        └── sh_area_forca/                       ← shapefile das 8 áreas
```
