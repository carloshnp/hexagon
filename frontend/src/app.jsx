/* CIVITAS Operations Dashboard — root app + orchestration.
   3-step load: index → summary → (on demand) per-area report. */

const { useState: _S, useEffect: _E, useMemo: _U, useCallback: _C } = React;

function App() {
  const store = CIVITAS.useDataStore();

  // local UI state
  const [selectedFid, setSelectedFid] = _S(null);
  const [hoverFid, setHoverFid]       = _S(null);
  const [filter, setFilter]           = _S('Todas');
  const [showOcc, setShowOcc]         = _S(true);
  const [showHex, setShowHex]         = _S(true);
  const [now, setNow]                 = _S(formatNow());
  const [flyToToken, setFlyToToken]   = _S(0);
  const [flyingIssueId, setFlyingIssueId] = _S(null);
  const [periodOpen, setPeriodOpen]   = _S(false);
  const [stripTab, setStripTab]             = _S('todos');
  const [scoreThreshold, setScoreThreshold] = _S(74);

  // ---------- bootstrap: load index, then summary for latest ----------
  _E(() => {
    (async () => {
      try {
        const idx = await CIVITAS.dataStore.loadIndex();
        await CIVITAS.dataStore.loadSummary(idx.latest);
      } catch (e) {
        console.error('Bootstrap failed', e);
      }
    })();
  }, []);

  // clock
  _E(() => {
    const t = setInterval(() => setNow(formatNow()), 30000);
    return () => clearInterval(t);
  }, []);

  // Esc dismisses selection
  _E(() => {
    const k = (e) => { if (e.key === 'Escape') { setSelectedFid(null); setPeriodOpen(false); } };
    window.addEventListener('keydown', k);
    return () => window.removeEventListener('keydown', k);
  }, []);

  // --- derived data ---
  const summaryReady   = store.summaryStatus === 'ready' && store.summary;
  const summaryLoading = store.summaryStatus === 'loading' || store.summaryStatus === 'idle';
  const periods        = store.index?.available_periods || [];
  const currentPeriod  = periods.find(p => p.key === store.period);
  const areasByFid     = _U(() => CIVITAS.getAreasByFid(store.summary), [store.summary]);
  const areasByRank    = _U(() => CIVITAS.getAreasByRank(store.summary), [store.summary]);
  const filteredAreas  = _U(() => {
    if (stripTab === 'todos') return areasByRank;
    return areasByRank.filter(a => a.score >= scoreThreshold);
  }, [stripTab, scoreThreshold, areasByRank]);
  const occurrences    = _U(() => store.summary?.integrated_occurrences || [], [store.summary]);
  const area           = selectedFid && areasByFid[selectedFid];

  // ---------- selection handlers ----------
  const onDeselect = _C(() => {
    setSelectedFid(null);
    setFlyingIssueId(null);
  }, []);
  const onSelectMap = _C((fid) => setSelectedFid(fid), []);
  const onChipClick = _C((fid) => {
    setSelectedFid(prev => prev === fid ? null : fid);
  }, []);
  const onCardClick = _C((issue) => {
    if (issue.primary_fid === selectedFid) { onDeselect(); return; }
    setSelectedFid(issue.primary_fid);
    setFlyingIssueId(issue.id);
    setFlyToToken(t => t + 1);
    // Trigger lazy report load when a card is clicked (uses cache on repeat).
    CIVITAS.dataStore.loadReport(issue.primary_fid).catch(() => {});
    setTimeout(() => setFlyingIssueId(null), 1000);
  }, [selectedFid, onDeselect]);

  // When user selects via map, also kick off the area report fetch (cache-friendly)
  _E(() => {
    if (selectedFid) {
      CIVITAS.dataStore.loadReport(selectedFid).catch(() => {});
    }
  }, [selectedFid]);

  _E(() => {
    if (stripTab === 'critico' && selectedFid) {
      const a = areasByFid[selectedFid];
      if (a && a.score < scoreThreshold) onDeselect();
    }
  }, [stripTab, scoreThreshold]);

  // ---------- period change ----------
  const onChangePeriod = _C((key) => {
    setPeriodOpen(false);
    if (key === store.period) return;
    onDeselect();
    CIVITAS.dataStore.loadSummary(key).catch(() => {});
  }, [store.period, onDeselect]);
  const onStepPeriod = _C((dir) => {
    if (!periods.length) return;
    const idx = periods.findIndex(p => p.key === store.period);
    const next = periods[Math.min(periods.length - 1, Math.max(0, idx + dir))];
    if (next && next.key !== store.period) onChangePeriod(next.key);
  }, [periods, store.period, onChangePeriod]);

  return (
    <div data-screen-label="01 Dashboard" style={{
      width: '100%', minWidth: 1440, height: '100vh', minHeight: 900,
      display: 'flex', flexDirection: 'column', overflow: 'hidden',
      background: 'var(--bg)',
    }}>
      <HeaderBar
        now={now}
        periods={periods}
        currentPeriod={currentPeriod}
        periodLoading={summaryLoading}
        periodOpen={periodOpen}
        setPeriodOpen={setPeriodOpen}
        onChangePeriod={onChangePeriod}
        onStepPeriod={onStepPeriod}
      />
      <RankingStrip
        areas={filteredAreas}
        loading={summaryLoading}
        selectedFid={selectedFid}
        onSelect={onChipClick}
        tab={stripTab}
        onTabChange={setStripTab}
        threshold={scoreThreshold}
        onThresholdChange={setScoreThreshold}
      />
      <ContextStrip
        area={area}
        loading={summaryLoading && !area}
        tab={stripTab}
        filteredAreas={filteredAreas}
      />

      <div style={{ flex: 1, display: 'flex', minHeight: 0 }}>
        <Sidebar
          occurrences={occurrences}
          areasByFid={areasByFid}
          loading={summaryLoading}
          reports={store.reports}
          selectedFid={selectedFid}
          hoverFid={hoverFid}
          onHover={setHoverFid}
          filter={filter}
          setFilter={setFilter}
          flyingIssueId={flyingIssueId}
          onCardClick={onCardClick}
        />

        <div style={{ flex: 1, position: 'relative', display: 'flex', flexDirection: 'column', minWidth: 0, background: 'var(--bg)' }}>
          <MapToolbar
            showOcc={showOcc} setShowOcc={setShowOcc}
            showHex={showHex} setShowHex={setShowHex}
            area={area}
          />
          <div style={{ flex: 1, position: 'relative', minHeight: 0 }}>
            <MapPanel
              areasByFid={areasByFid}
              loading={summaryLoading}
              selectedFid={selectedFid}
              onSelectHex={onSelectMap}
              onDeselect={onDeselect}
              hoverFid={hoverFid}
              onHover={setHoverFid}
              showOccurrences={showOcc}
              showHexes={showHex}
              flyToToken={flyToToken}
            />
            <BottomBar
              area={area}
              report={selectedFid ? store.reports[selectedFid] : null}
              onDismiss={onDeselect}
            />
          </div>
          <StatusFooter
            area={area}
            store={store}
            summaryReady={summaryReady}
          />
        </div>
      </div>
    </div>
  );
}

function MapToolbar({ showOcc, setShowOcc, showHex, setShowHex, area }) {
  return (
    <div style={{
      height: 38, display: 'flex', alignItems: 'stretch',
      background: 'var(--surface)', borderBottom: '1px solid var(--border)', flexShrink: 0,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', padding: '0 14px', gap: 14, borderRight: '1px solid var(--border)' }}>
        <span className="mono uc" style={{ fontSize: 9.5, color: 'var(--text-2)', letterSpacing: 0.14, fontWeight: 700 }}>Camadas</span>
        <ToolbarToggle label="Hex H3" active={showHex} onClick={() => setShowHex(!showHex)} swatch="#004A8F" />
        <ToolbarToggle label="Ocorrências" active={showOcc} onClick={() => setShowOcc(!showOcc)} swatch="#D0021B" />
        <ToolbarToggle label="Câmeras" active={false} onClick={() => {}} swatch="#44597A" />
        <ToolbarToggle label="Patrulhas" active={false} onClick={() => {}} swatch="#007A4D" />
      </div>
      <div style={{ display: 'flex', alignItems: 'center', padding: '0 14px', gap: 14, borderRight: '1px solid var(--border)' }}>
        <span className="mono uc" style={{ fontSize: 9.5, color: 'var(--text-2)', letterSpacing: 0.14, fontWeight: 700 }}>Resolução</span>
        {['r7','r8','r9','r10'].map((r, i) => (
          <button key={r} className="mono uc" style={{
            background: i === 2 ? 'var(--brand-tint)' : 'transparent',
            color: i === 2 ? 'var(--brand)' : 'var(--text-2)',
            fontWeight: i === 2 ? 800 : 600,
            border: '1px solid', borderColor: i === 2 ? 'var(--border-2)' : 'transparent',
            fontSize: 10, padding: '2px 6px', letterSpacing: 0.08,
          }}>{r}</button>
        ))}
      </div>
      <div style={{ flex: 1 }} />
      <div style={{ display: 'flex', alignItems: 'center', padding: '0 14px', gap: 12, borderLeft: '1px solid var(--border)' }}>
        <span className="mono" style={{ fontSize: 10, color: 'var(--text-2)', fontWeight: 600 }}>
          Janela: <span style={{ color: 'var(--text)' }}>24/05/2026 — 14:32 BRT</span>
        </span>
        <span style={{ width: 1, height: 14, background: 'var(--border)' }} />
        <button className="mono uc" style={{
          background: 'var(--surface)', color: 'var(--brand)',
          border: '1px solid var(--border-2)', fontSize: 10, padding: '3px 8px', letterSpacing: 0.1, fontWeight: 700,
        }}>Exportar GeoJSON</button>
      </div>
    </div>
  );
}

function ToolbarToggle({ label, active, onClick, swatch }) {
  return (
    <button onClick={onClick} style={{
      display: 'flex', alignItems: 'center', gap: 6,
      background: 'transparent', border: 'none', padding: 0,
      color: active ? 'var(--text)' : 'var(--text-3)',
      fontSize: 11.5, fontWeight: active ? 600 : 500, cursor: 'pointer',
    }}>
      <span style={{
        width: 14, height: 14, border: '1px solid var(--border-2)',
        background: active ? swatch : 'var(--surface)',
        display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
      }}>
        {active && <span style={{ width: 6, height: 6, background: '#fff' }} />}
      </span>
      {label}
    </button>
  );
}

function StatusFooter({ area, store, summaryReady }) {
  return (
    <div style={{
      height: 26, display: 'flex', alignItems: 'center',
      background: 'var(--surface)', borderTop: '1px solid var(--border)',
      fontFamily: 'JetBrains Mono', fontSize: 10, color: 'var(--text-2)', fontWeight: 600,
      flexShrink: 0,
    }}>
      <span style={{ padding: '0 14px', borderRight: '1px solid var(--border)', display: 'inline-flex', alignItems: 'center', gap: 6 }}>
        <span style={{ width: 6, height: 6, background: summaryReady ? '#007A4D' : '#F5A623', borderRadius: '50%' }} />
        <span style={{ color: 'var(--text)' }}>SISP · {summaryReady ? 'OK' : 'SYNC'}</span>
      </span>
      <span style={{ padding: '0 14px', borderRight: '1px solid var(--border)' }}>
        Período: {store.period || '—'}
      </span>
      <span style={{ padding: '0 14px', borderRight: '1px solid var(--border)' }}>
        H3 hex: {area ? '142 selecionadas' : '0 selecionadas'}
      </span>
      <span style={{ padding: '0 14px', borderRight: '1px solid var(--border)' }}>
        Ocorrências carregadas: {summaryReady ? '9.371' : '—'}
      </span>
      <span style={{ flex: 1 }} />
      <span style={{ padding: '0 14px', borderLeft: '1px solid var(--border)' }}>
        v2.4.1-rj · build 5821
      </span>
      <span style={{ padding: '0 14px', borderLeft: '1px solid var(--border)' }}>
        ↔ 1440 · ↕ {typeof window !== 'undefined' ? window.innerHeight : 900}
      </span>
    </div>
  );
}

function formatNow() {
  const d = new Date();
  const pad = n => String(n).padStart(2, '0');
  return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
