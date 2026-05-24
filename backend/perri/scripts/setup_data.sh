#!/usr/bin/env bash
# setup_data.sh — bootstrap completo do backend CIVITAS.
#
# Pipeline:
#   1. sincroniza o submodule de dados (CompStat-Rio/claude_impact_lab_compstat_rio)
#   2. verifica que os arquivos esperados estão no lugar
#   3. (opcional, com --install) instala dependências Python
#   4. roda o pipeline espacial para todas as janelas (sem filtro, 1d, 3d, 7d)
#      e exporta JSON + CSV consumíveis pelo front-end
#   5. roda os smoke tests
#
# Uso:
#   bash perri/scripts/setup_data.sh                # tudo
#   bash perri/scripts/setup_data.sh --install      # idem + pip install
#   bash perri/scripts/setup_data.sh --pull-latest  # também atualiza submódulo p/ HEAD remoto
#   bash perri/scripts/setup_data.sh --skip-tests
#   bash perri/scripts/setup_data.sh --skip-spatial # pula os pipelines pesados (~12 s)
#
set -euo pipefail

# ─── helpers ────────────────────────────────────────────────────────────────
if [ -t 1 ]; then
    GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; BOLD='\033[1m'; NC='\033[0m'
else
    GREEN=''; YELLOW=''; RED=''; BOLD=''; NC=''
fi
ok()   { printf "  ${GREEN}[ok]${NC}   %s\n" "$1"; }
warn() { printf "  ${YELLOW}[warn]${NC} %s\n" "$1"; }
fail() { printf "  ${RED}[fail]${NC} %s\n" "$1"; exit 1; }
step() { printf "\n${BOLD}==> %s${NC}\n" "$1"; }

# ─── flags ──────────────────────────────────────────────────────────────────
INSTALL_DEPS=0
PULL_LATEST=0
SKIP_TESTS=0
SKIP_SPATIAL=0
for arg in "$@"; do
    case "$arg" in
        --install)        INSTALL_DEPS=1 ;;
        --pull-latest)    PULL_LATEST=1 ;;
        --skip-tests)     SKIP_TESTS=1 ;;
        --skip-spatial)   SKIP_SPATIAL=1 ;;
        -h|--help)
            sed -n '2,18p' "$0"
            exit 0
            ;;
        *) fail "argumento desconhecido: $arg" ;;
    esac
done

# ─── localiza repo root ─────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || true)"
[ -n "$REPO_ROOT" ] || fail "rodar dentro de um repo git"
cd "$REPO_ROOT"
ok "repo root: $REPO_ROOT"

DATA_PATH="perri/hexagon_spatial/claude_impact_lab_compstat_rio"
DATA_URL="https://github.com/CompStat-Rio/claude_impact_lab_compstat_rio.git"

# ─── 1. submodule ───────────────────────────────────────────────────────────
step "1/5  Sincronizando submodule de dados"
if [ -f .gitmodules ] && grep -q "$DATA_PATH" .gitmodules; then
    git submodule sync --quiet "$DATA_PATH"
    git submodule update --init --recursive "$DATA_PATH"
    if [ "$PULL_LATEST" -eq 1 ]; then
        ok "puxando HEAD remoto do submódulo (origin/main)"
        git -C "$DATA_PATH" fetch --quiet origin
        git -C "$DATA_PATH" checkout --quiet origin/main || git -C "$DATA_PATH" checkout --quiet origin/master
    fi
    head=$(git -C "$DATA_PATH" rev-parse --short HEAD)
    ok "submodule em $head"
else
    warn "submodule não registrado — clonando direto"
    if [ -d "$DATA_PATH/.git" ] || [ -d "$DATA_PATH" ]; then
        warn "diretório já existe; pulando clone (use --pull-latest para atualizar)"
    else
        git clone --depth 1 "$DATA_URL" "$DATA_PATH"
        ok "clonado em $DATA_PATH"
    fi
fi

# ─── 2. verificação ─────────────────────────────────────────────────────────
step "2/5  Verificando arquivos esperados"
REQ_FILES=(
    "$DATA_PATH/dados/df_ocorrencias_tratado - Extração 1 .csv"
    "$DATA_PATH/dados/disk_denuncia.csv"
    "$DATA_PATH/dados/cameras_areas_fm.csv"
    "$DATA_PATH/dados/fatores_urbanos.csv"
    "$DATA_PATH/sh_area_forca/areas_forca_municipal.shp"
    "$DATA_PATH/sh_area_forca/areas_forca_municipal.dbf"
    "$DATA_PATH/sh_area_forca/areas_forca_municipal.shx"
)
for f in "${REQ_FILES[@]}"; do
    if [ -f "$f" ]; then
        size=$(du -h "$f" | cut -f1)
        ok "$(basename "$f") ($size)"
    else
        fail "ausente: $f"
    fi
done

n_docx=$(find "$DATA_PATH/relints" -maxdepth 1 -name "*.docx" 2>/dev/null | wc -l)
[ "$n_docx" -eq 8 ] && ok "8 RELINT .docx" || fail "esperado 8 .docx, achei $n_docx"

# ─── 3. python ──────────────────────────────────────────────────────────────
step "3/5  Verificando Python"
command -v python3 >/dev/null || fail "python3 não encontrado"
pyver=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
ok "python $pyver"

if [ "$INSTALL_DEPS" -eq 1 ]; then
    [ -f requirements.txt ] || fail "requirements.txt não encontrado"
    ok "instalando dependências"
    pip install -q -r requirements.txt
    ok "dependências OK"
else
    missing=""
    for pkg in fastapi pydantic geopandas pandas h3 shapely; do
        python3 -c "import $pkg" 2>/dev/null || missing="$missing $pkg"
    done
    if [ -n "$missing" ]; then
        warn "pacotes ausentes:$missing  (rode novamente com --install)"
    else
        ok "pacotes principais presentes"
    fi
fi

# ─── 4. exports ─────────────────────────────────────────────────────────────
step "4/5  Processando dados e gerando exports"
cd "$REPO_ROOT/perri"

EXPORT_FLAG=""
if [ "$SKIP_SPATIAL" -eq 1 ]; then
    EXPORT_FLAG="--no-spatial"
    warn "pulando pipelines espaciais (--skip-spatial)"
fi

if python3 -m hexagon_spatial.export_csv $EXPORT_FLAG >/tmp/civitas_export.log 2>&1; then
    ok "relints.json + areas_detalhadas.csv"
    if [ "$SKIP_SPATIAL" -eq 0 ]; then
        for f in spatial_priority_areas.json spatial_priority_areas_1d.json \
                 spatial_priority_areas_3d.json spatial_priority_areas_7d.json \
                 spatial_top_areas.csv; do
            [ -f "hexagon_spatial/exports/$f" ] && ok "$f ($(du -h "hexagon_spatial/exports/$f" | cut -f1))"
        done
    fi
else
    cat /tmp/civitas_export.log
    fail "export_csv falhou"
fi

# ─── 5. smoke tests ─────────────────────────────────────────────────────────
if [ "$SKIP_TESTS" -eq 0 ]; then
    step "5/5  Rodando smoke tests"
    if python3 -m hexagon_spatial.test_relints_api >/tmp/civitas_tests.log 2>&1; then
        passes=$(grep -c "\[PASS\]" /tmp/civitas_tests.log || true)
        ok "$passes asserções verdes"
    else
        cat /tmp/civitas_tests.log
        fail "smoke tests falharam (log em /tmp/civitas_tests.log)"
    fi
else
    step "5/5  Smoke tests pulados (--skip-tests)"
fi

# ─── done ───────────────────────────────────────────────────────────────────
step "Setup completo"
cat <<EOF

Backend pronto. Para servir:

  cd $REPO_ROOT/perri
  uvicorn hexagon_spatial.app:app --reload --port 8000

Exports prontos em $REPO_ROOT/perri/hexagon_spatial/exports/:
  relints.json                            agências + RELINTs
  areas_detalhadas.csv                    24 linhas (1 por agência×sub-área)
  spatial_priority_areas.json             pipeline MCDA (todo histórico)
  spatial_priority_areas_{1,3,7}d.json    pipeline filtrado por janela
  spatial_top_areas.csv                   top-N consolidado das 4 janelas

Endpoints úteis:
  http://localhost:8000/docs                                   → Swagger
  http://localhost:8000/spatial/priority-areas?top_n=10        → tudo
  http://localhost:8000/spatial/priority-areas?days=7&top_n=10 → últimos 7 dias
  http://localhost:8000/relints/agencias/10                    → Jardim de Alah
EOF
