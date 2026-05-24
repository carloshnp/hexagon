/* CIVITAS — data store & loaders.
   Replaces the previous in-memory dataset. Areas/issues now come from JSON
   files fetched per period; per-area reports load lazily on demand. */

/* ==================== Static constants ==================== */

const RISK = {
  'CRÍTICO': { label: 'Crítico', color: '#D0021B', bg: 'rgba(208,2,27,0.10)',   border: '#D0021B33' },
  'ALTO':    { label: 'Alto',    color: '#E2562A', bg: 'rgba(226,86,42,0.10)',  border: '#E2562A33' },
  'MÉDIO':   { label: 'Médio',   color: '#F5A623', bg: 'rgba(245,166,35,0.10)', border: '#F5A62333' },
  'BAIXO':   { label: 'Baixo',   color: '#007A4D', bg: 'rgba(0,122,77,0.10)',   border: '#007A4D33' },
};

const URGENCY = {
  'CRÍTICO': { label: 'CRÍTICO', color: '#D0021B' },
  'ALTO':    { label: 'ALTO',    color: '#E2562A' },
  'MÉDIO':   { label: 'MÉDIO',   color: '#F5A623' },
};

const STATUS = {
  PENDENTE:       { label: 'AÇÃO PENDENTE',  color: '#D0021B', bg: 'rgba(208,2,27,0.12)',  border: '#D0021B55' },
  EM_ATENDIMENTO: { label: 'EM ATENDIMENTO', color: '#0066CC', bg: 'rgba(0,102,204,0.14)', border: '#0066CC44' },
  CONCLUIDO:      { label: 'CONCLUÍDO',      color: '#007A4D', bg: 'rgba(0,122,77,0.12)',  border: '#007A4D55' },
};

/* Map-pixel positions for each fid (synthetic placement for the demo SVG map). */
const AREA_PIXELS = {
  1:[490,200], 2:[560,320], 3:[340,250], 4:[430,230],
  5:[520,270], 6:[240,360], 7:[120,320], 8:[180,270],
  9:[400,260], 10:[470,180], 11:[570,360], 12:[280,320],
  13:[200,220], 14:[600,340], 15:[80,340], 16:[540,290],
};

function riskColor(score) {
  if (score >= 75) return '#D0021B';
  if (score >= 60) return '#E2562A';
  if (score >= 40) return '#F5A623';
  if (score >= 20) return '#3FA46A';
  return '#007A4D';
}
function riskKeyFromScore(score) {
  if (score >= 75) return 'CRÍTICO';
  if (score >= 55) return 'ALTO';
  if (score >= 35) return 'MÉDIO';
  return 'BAIXO';
}

/* ==================== Hex grid (geometry stays client-side) ==================== */

const HEX_SIZE = 22;
const HEX_W = HEX_SIZE * Math.sqrt(3);
const HEX_H = HEX_SIZE * 1.5;

function buildHexGrid(width, height, areasByFid) {
  const fids = Object.keys(AREA_PIXELS).map(Number);
  const hexes = [];
  const cols = Math.ceil(width / HEX_W) + 2;
  const rows = Math.ceil(height / HEX_H) + 2;
  for (let r = -1; r < rows; r++) {
    for (let q = -1; q < cols; q++) {
      const x = q * HEX_W + (r % 2 ? HEX_W / 2 : 0);
      const y = r * HEX_H;
      const inside =
        !(x < 60 && y > 380) &&
        !(x > 860 && y < 80) &&
        !(x < 30) && !(y < 20) && !(x > 900) && !(y > 540) &&
        !(x > 700 && y > 480) &&
        !((x - 800) ** 2 + (y - 120) ** 2 < 2200);
      if (!inside) continue;

      let nearestFid = null, nd = Infinity;
      for (const fid of fids) {
        const [ax, ay] = AREA_PIXELS[fid];
        const d = Math.hypot(ax - x, ay - y);
        if (d < nd) { nd = d; nearestFid = fid; }
      }
      const a = areasByFid?.[nearestFid];
      const baseScore = a?.score ?? 0;
      const falloff = Math.max(0, 1 - nd / 90);
      const noise = (Math.sin(x * 0.13 + y * 0.21) + Math.cos(x * 0.07 - y * 0.09)) * 8;
      const score = Math.round(Math.max(0, Math.min(100, baseScore * falloff * 0.85 + 14 + noise)));
      hexes.push({ id: `${q}_${r}`, q, r, x, y, score, fid: nearestFid });
    }
  }
  return hexes;
}

function hexPath(cx, cy, size) {
  const pts = [];
  for (let i = 0; i < 6; i++) {
    const a = (Math.PI / 3) * i + Math.PI / 6;
    pts.push(`${(cx + size * Math.cos(a)).toFixed(1)},${(cy + size * Math.sin(a)).toFixed(1)}`);
  }
  return `M${pts.join(' L')} Z`;
}

function buildOccurrences(areas) {
  if (!areas) return [];
  const out = [];
  let seed = 1;
  const rand = () => { seed = (seed * 9301 + 49297) % 233280; return seed / 233280; };
  for (const a of areas) {
    const px = AREA_PIXELS[a.fid]; if (!px) continue;
    const [cx, cy] = px;
    const n = Math.round(a.score / 8);
    for (let i = 0; i < n; i++) {
      const ang = rand() * Math.PI * 2;
      const r = rand() * 60 + 8;
      out.push({
        x: cx + Math.cos(ang) * r,
        y: cy + Math.sin(ang) * r,
        fid: a.fid,
        kind: rand() > 0.7 ? 'priority' : 'standard',
      });
    }
  }
  return out;
}

/* ==================== Fetch wrapper w/ artificial delay for visible loading ==================== */

async function fetchJSON(path, minDelay = 0) {
  const start = performance.now();
  const res = await fetch(path);
  if (!res.ok) throw new Error(`HTTP ${res.status} · ${path}`);
  const data = await res.json();
  const elapsed = performance.now() - start;
  if (minDelay && elapsed < minDelay) {
    await new Promise(r => setTimeout(r, minDelay - elapsed));
  }
  return data;
}

/* ==================== DataStore (simple pub/sub) ==================== */

const dataStore = {
  state: {
    index: null,
    indexStatus: 'idle',         // 'idle' | 'loading' | 'ready' | 'error'

    period: null,                // current period key
    summary: null,
    summaryStatus: 'idle',

    reports: {},                 // { [fid]: { status, data?, error? } }
  },
  listeners: new Set(),
  subscribe(fn) { this.listeners.add(fn); return () => this.listeners.delete(fn); },
  notify() { this.listeners.forEach(fn => fn()); },

  async loadIndex() {
    this.state.indexStatus = 'loading'; this.notify();
    try {
      const idx = await fetchJSON('data/index.json', 400);
      this.state.index = idx;
      this.state.indexStatus = 'ready';
      this.notify();
      return idx;
    } catch (e) {
      this.state.indexStatus = 'error';
      this.notify();
      throw e;
    }
  },

  async loadSummary(periodKey) {
    // Reset session state on period change
    this.state.period = periodKey;
    this.state.summary = null;
    this.state.summaryStatus = 'loading';
    this.state.reports = {};
    this.notify();
    try {
      const s = await fetchJSON(`data/${periodKey}_summary.json`, 800);
      this.state.summary = s;
      this.state.summaryStatus = 'ready';
      this.notify();
      return s;
    } catch (e) {
      this.state.summaryStatus = 'error';
      this.notify();
      throw e;
    }
  },

  async loadReport(fid) {
    const existing = this.state.reports[fid];
    if (existing?.status === 'ready')   return existing.data;
    if (existing?.status === 'loading') return null;
    this.state.reports = { ...this.state.reports, [fid]: { status: 'loading' } };
    this.notify();
    try {
      const data = await fetchJSON(`data/${this.state.period}_${fid}_report.json`, 600);
      this.state.reports = { ...this.state.reports, [fid]: { status: 'ready', data } };
      this.notify();
      return data;
    } catch (e) {
      this.state.reports = { ...this.state.reports, [fid]: { status: 'error', error: String(e) } };
      this.notify();
      throw e;
    }
  },
};

/* Hook: re-render on any store change. */
function useDataStore() {
  const [, force] = React.useState(0);
  React.useEffect(() => dataStore.subscribe(() => force(n => n + 1)), []);
  return dataStore.state;
}

/* Derived helpers (read-only). */
function getAreasByFid(summary) {
  if (!summary) return {};
  return Object.fromEntries(summary.areas.map(a => [a.fid, a]));
}
function getAreasByRank(summary) {
  if (!summary) return [];
  return [...summary.areas].sort((a, b) => a.rank - b.rank);
}

window.CIVITAS = {
  RISK, URGENCY, STATUS, AREA_PIXELS,
  riskColor, riskKeyFromScore,
  buildHexGrid, hexPath, buildOccurrences, HEX_SIZE,
  dataStore, useDataStore,
  getAreasByFid, getAreasByRank,
};
