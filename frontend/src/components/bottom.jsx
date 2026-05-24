/* Bottom bar — slides up when a polygon is selected.
   Two tabs: MÉTRICAS (4 cards; simulated) and RELATÓRIO DA ÁREA (lazy from report file). */

const _BB = React;

function BottomBar({ area, report, onDismiss }) {
  const [visible, setVisible] = _BB.useState(false);
  const [tab, setTab] = _BB.useState('metrics');
  _BB.useEffect(() => {
    if (area) {
      const t = setTimeout(() => setVisible(true), 20);
      return () => clearTimeout(t);
    } else setVisible(false);
  }, [area?.fid]);

  if (!area) return null;
  const c = CIVITAS.riskColor(area.score);

  return (
    <div style={{
      position: 'absolute', left: 0, right: 0, bottom: 0,
      transform: visible ? 'translateY(0)' : 'translateY(110%)',
      transition: 'transform 320ms cubic-bezier(0.2, 0.7, 0.1, 1)',
      borderTop: '1px solid var(--border)',
      background: 'var(--surface)',
      boxShadow: '0 -6px 18px rgba(0,30,80,0.10)',
    }}>
      <div style={{
        display: 'flex', alignItems: 'stretch', justifyContent: 'space-between',
        background: 'var(--brand)', color: '#fff',
        borderBottom: '1px solid #00305C', minHeight: 42,
      }}>
        <div style={{ display: 'flex', alignItems: 'stretch' }}>
          <BottomTab id="metrics" label="MÉTRICAS"          active={tab==='metrics'} onClick={() => setTab('metrics')} />
          <BottomTab id="report"  label="RELATÓRIO DA ÁREA" active={tab==='report'}  onClick={() => setTab('report')} />
          <div style={{ padding: '0 16px', display: 'flex', alignItems: 'center', gap: 12, borderLeft: '1px solid #00305C' }}>
            <span className="mono uc" style={{ fontSize: 9.5, color: '#BFD4EA', letterSpacing: 0.14, fontWeight: 700 }}>
              Painel detalhado
            </span>
            <span style={{ color: '#5E89B7' }}>·</span>
            <span className="h-cond-x" style={{ fontSize: 16, letterSpacing: 0.04, color: '#fff' }}>
              {area.polyId} · {area.nome_area.toUpperCase()}
            </span>
            <span className="mono" style={{ fontSize: 10, color: '#BFD4EA' }}>({area.zone})</span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6,
                           padding: '2px 8px', background: c, color: '#fff',
                           fontSize: 9.5, fontWeight: 800, letterSpacing: 0.1 }} className="mono uc">
              <span style={{ width: 5, height: 5, background: '#fff' }} /> {CIVITAS.RISK[CIVITAS.riskKeyFromScore(area.score)].label}
            </span>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'stretch' }}>
          {['24h','7d','30d','90d'].map((t, i) => (
            <button key={t} className="mono uc" style={{
              padding: '0 14px', background: i === 0 ? '#003B72' : 'transparent',
              border: 'none', borderLeft: '1px solid #00305C',
              color: '#fff', fontWeight: i === 0 ? 800 : 500,
              fontSize: 10.5, letterSpacing: 0.12,
            }}>{t}</button>
          ))}
          <button onClick={onDismiss} className="mono" style={{
            width: 38, background: 'transparent', border: 'none',
            borderLeft: '1px solid #00305C', color: '#fff', fontSize: 16,
          }} aria-label="Dispensar">×</button>
        </div>
      </div>

      {tab === 'metrics' ? <MetricsView area={area} accent={c} /> : <ReportView area={area} accent={c} report={report} />}
    </div>
  );
}

function BottomTab({ label, active, onClick }) {
  return (
    <button onClick={onClick} className="mono uc" style={{
      padding: '0 16px', background: active ? '#003B72' : 'transparent',
      border: 'none', borderLeft: '1px solid #00305C',
      color: '#fff', fontWeight: active ? 800 : 500, opacity: active ? 1 : 0.72,
      fontSize: 10.5, letterSpacing: 0.14, position: 'relative',
      display: 'flex', alignItems: 'center',
    }}>
      {label}
      {active && <span style={{ position: 'absolute', left: 12, right: 12, bottom: 0, height: 3, background: '#fff' }} />}
    </button>
  );
}

/* ==================== Tab 1 — MÉTRICAS (synthesized, marked SIMULADO) ==================== */
function MetricsView({ area, accent }) {
  // Synthesize 4 metric cards from the summary's score/occurrence data
  const metrics = _BB.useMemo(() => synthMetrics(area), [area.fid, area.score]);
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', background: 'var(--paper)' }}>
      {metrics.map((m, i) => (
        <DetailCard key={i} m={m} accent={accent} last={i === metrics.length - 1} />
      ))}
    </div>
  );
}

function DetailCard({ m, accent, last }) {
  return (
    <div style={{
      padding: '14px 18px 16px', borderRight: last ? 'none' : '1px solid var(--border-pp)',
      display: 'flex', flexDirection: 'column', gap: 8,
      minHeight: 132, background: 'var(--paper)', position: 'relative',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8 }}>
        <span className="mono uc" style={{ fontSize: 9.5, color: 'var(--brand)', letterSpacing: 0.14, fontWeight: 800 }}>
          {m.label}
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <SimuladoBadge />
          <span className="mono" style={{ fontSize: 9, color: 'var(--ink-2)', padding: '1px 5px', border: '1px solid var(--border-pp)', background: 'var(--paper-2)' }}>24h</span>
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
        <span className="h-cond-x" style={{ fontSize: 36, lineHeight: 0.95, letterSpacing: 0.02, color: 'var(--brand)' }}>
          {m.value}
        </span>
        {m.unit && <span className="mono" style={{ fontSize: 12, color: 'var(--ink-2)' }}>{m.unit}</span>}
        <span style={{ flex: 1 }} />
        <DeltaPaper value={m.delta} inverted={m.inverted} />
      </div>
      <div style={{ display: 'flex', alignItems: 'flex-end', gap: 10 }}>
        <Sparkline data={m.spark} color={accent} width={148} height={32} />
        <div className="mono" style={{ fontSize: 9, color: 'var(--ink-2)', lineHeight: 1.4 }}>
          <div>min {Math.min(...m.spark)}</div>
          <div>max {Math.max(...m.spark)}</div>
        </div>
      </div>
      <div className="mono" style={{ display: 'flex', justifyContent: 'space-between', fontSize: 8.5, color: 'var(--ink-2)', marginTop: -4 }}>
        <span>00:00</span><span>06:00</span><span>12:00</span><span>18:00</span><span>agora</span>
      </div>
    </div>
  );
}

function synthMetrics(area) {
  const seed = area.fid * 17 + 5;
  const sp = (s, base, amp) => {
    const out = []; let v = s;
    for (let i = 0; i < 24; i++) {
      v = (v * 9301 + 49297) % 233280;
      out.push(Math.max(0, Math.round(base + Math.sin(i * 0.6 + s * 0.3) * amp * 0.6 + (v / 233280 - 0.5) * amp * 0.8)));
    }
    return out;
  };
  return [
    { label: 'Ocorrências (24h)',    value: Math.round(area.occurrence_count / 6), unit: '',    delta: area.score_delta, spark: sp(seed, 40 + area.score / 3, 20 + area.score / 5) },
    { label: 'Tempo médio resposta', value: (4 + area.score / 14).toFixed(1),       unit: 'min', delta: area.score_delta > 0 ? +0.4 : -0.3, spark: sp(seed + 11, 6 + area.score / 18, 3), inverted: true },
    { label: 'Unidades em campo',    value: Math.round(6 + area.score / 8),         unit: '',    delta: Math.sign(area.score_delta), spark: sp(seed + 19, 10, 4) },
    { label: 'Reincidência (7d)',    value: Math.round(20 + area.score / 3),        unit: '%',   delta: area.score_delta, spark: sp(seed + 31, 25, 10), inverted: true },
  ];
}

/* ==================== Tab 2 — RELATÓRIO DA ÁREA (gated on report load) ==================== */

function ReportView({ area, accent, report }) {
  const status = report?.status;
  if (!status || status === 'loading') return <ReportSkeleton />;
  if (status === 'error') return <ReportError onRetry={() => CIVITAS.dataStore.loadReport(area.fid)} />;
  // ready
  return <ReportContent area={area} accent={accent} report={report.data} />;
}

function ReportSkeleton() {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'minmax(220px, 1fr) minmax(220px, 1.05fr) minmax(180px, 0.85fr) minmax(240px, 1.05fr) minmax(280px, 1.3fr)', background: 'var(--paper)', minHeight: 178 }}>
      {['Área','Ocorrências','Score','Efetividade','Tendência'].map((lbl, i) => (
        <div key={lbl} style={{
          padding: '12px 16px 14px', borderRight: i < 4 ? '1px solid var(--border-pp)' : 'none',
          background: 'var(--paper)', display: 'flex', flexDirection: 'column', gap: 10,
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="mono uc" style={{ fontSize: 9.5, color: 'var(--brand)', letterSpacing: 0.14, fontWeight: 800 }}>{lbl}</span>
            <Spinner size={11} color="var(--brand)" />
          </div>
          <Shimmer width="60%"  height={22} />
          <Shimmer width="100%" height={10} />
          <Shimmer width="86%"  height={10} />
          <Shimmer width="100%" height={36} />
        </div>
      ))}
    </div>
  );
}

function ReportError({ onRetry }) {
  return (
    <div style={{
      padding: 36, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 20,
      background: 'var(--paper)', minHeight: 178,
    }}>
      <div style={{ width: 8, height: 56, background: '#D0021B' }} />
      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        <span className="mono uc" style={{ fontSize: 11, color: '#D0021B', fontWeight: 800, letterSpacing: 0.14 }}>
          ERRO AO CARREGAR RELATÓRIO
        </span>
        <span style={{ fontSize: 12, color: 'var(--ink-2)' }}>
          Não foi possível obter o relatório completo deste polígono. Verifique a conexão e tente novamente.
        </span>
      </div>
      <button onClick={onRetry} className="mono uc" style={{
        padding: '8px 16px', background: 'var(--brand)', color: '#fff',
        border: 'none', fontSize: 11, fontWeight: 800, letterSpacing: 0.12, cursor: 'pointer',
      }}>↻ Tentar novamente</button>
    </div>
  );
}

function ReportContent({ area, accent, report }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'minmax(220px, 1fr) minmax(220px, 1.05fr) minmax(180px, 0.85fr) minmax(240px, 1.05fr) minmax(280px, 1.3fr)', background: 'var(--paper)', minHeight: 178 }}>
      <ReportCard label="Área"        last={false}><ReportArea area={area} /></ReportCard>
      <ReportCard label="Ocorrências" last={false}><ReportOccurrences area={area} report={report} /></ReportCard>
      <ReportCard label="Score"       last={false}><ReportScore area={area} /></ReportCard>
      <ReportCard label="Efetividade" last={false}><ReportEffectiveness area={area} /></ReportCard>
      <ReportCard label="Tendência"   last={true} ><ReportTrend area={area} accent={accent} /></ReportCard>
    </div>
  );
}

function ReportCard({ label, last, children }) {
  return (
    <div style={{
      padding: '12px 16px 14px', borderRight: last ? 'none' : '1px solid var(--border-pp)',
      background: 'var(--paper)', display: 'flex', flexDirection: 'column', gap: 8,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span className="mono uc" style={{ fontSize: 9.5, color: 'var(--brand)', letterSpacing: 0.14, fontWeight: 800 }}>{label}</span>
        <span style={{ width: 14, height: 1, background: 'var(--brand)' }} />
      </div>
      {children}
    </div>
  );
}

function ReportArea({ area }) {
  const bounds = {
    n: (area.centroide.lat + 0.025).toFixed(4),
    s: (area.centroide.lat - 0.025).toFixed(4),
    w: (area.centroide.lon - 0.025).toFixed(4),
    e: (area.centroide.lon + 0.025).toFixed(4),
  };
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
        <span className="h-cond-x" style={{ fontSize: 22, color: 'var(--brand)', letterSpacing: 0.04 }}>{area.polyId}</span>
        <span className="mono" style={{ fontSize: 11, color: 'var(--ink)', fontWeight: 700 }}>{area.polyZoneId}</span>
        <span className="mono" style={{ fontSize: 9, color: 'var(--ink-2)', padding: '1px 5px', border: '1px solid var(--border-pp)', background: 'var(--paper-2)', marginLeft: 'auto' }}>{area.zoneCode}</span>
      </div>
      <div className="mono" style={{ fontSize: 10, color: 'var(--ink-2)', wordBreak: 'break-all', lineHeight: 1.45 }}>
        <span style={{ color: 'var(--brand)', fontWeight: 700 }}>H3</span> · {area.h3}
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '3px 8px', fontSize: 10 }} className="mono">
        <span style={{ color: 'var(--ink-2)' }}>N</span><span style={{ color: 'var(--ink)' }}>{bounds.n}°</span>
        <span style={{ color: 'var(--ink-2)' }}>S</span><span style={{ color: 'var(--ink)' }}>{bounds.s}°</span>
        <span style={{ color: 'var(--ink-2)' }}>O</span><span style={{ color: 'var(--ink)' }}>{bounds.w}°</span>
        <span style={{ color: 'var(--ink-2)' }}>L</span><span style={{ color: 'var(--ink)' }}>{bounds.e}°</span>
      </div>
      <div style={{ display: 'flex', gap: 10, marginTop: 'auto' }}>
        <Cell label="Zona" value={area.zone} />
        <Sep />
        <Cell label="Centroide" value={`${area.centroide.lat.toFixed(3)}, ${area.centroide.lon.toFixed(3)}`} mono />
      </div>
    </div>
  );
}

function ReportOccurrences({ area, report }) {
  // Breakdown: synth split of the area.occurrence_count by issue types it touches
  const occs = report.occurrences || [];
  const total = area.occurrence_count;
  // approximate split: 42 / 23 / 20 / 10 / 5
  const breakdown = [
    { label: area.type || 'Tipo principal', value: Math.round(total * 0.42), color: '#D0021B' },
    { label: 'Outros roubos',   value: Math.round(total * 0.23), color: '#F5A623' },
    { label: 'Furtos',          value: Math.round(total * 0.20), color: '#0066CC' },
    { label: 'Lesão corporal',  value: Math.round(total * 0.10), color: '#007A4D' },
    { label: 'Outros',          value: Math.round(total * 0.05), color: '#8FA3BE' },
  ];
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
        <span className="h-cond-x" style={{ fontSize: 28, color: 'var(--brand)', letterSpacing: 0.02 }}>
          {total.toLocaleString('pt-BR')}
        </span>
        <span className="mono uc" style={{ fontSize: 9.5, color: 'var(--ink-2)', fontWeight: 700 }}>últimas 24h</span>
        <span style={{ flex: 1 }} />
        <DeltaPaper value={area.score_delta} />
      </div>
      <div style={{ display: 'flex', height: 8, border: '1px solid var(--border-pp)' }}>
        {breakdown.map(b => (
          <div key={b.label} style={{ flex: b.value / total, background: b.color }} title={`${b.label}: ${b.value}`} />
        ))}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        {breakdown.map(b => (
          <div key={b.label} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ width: 8, height: 8, background: b.color, flexShrink: 0 }} />
            <span style={{ fontSize: 10.5, color: 'var(--ink)', flex: 1, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{b.label}</span>
            <span className="mono" style={{ fontSize: 10, color: 'var(--ink-2)', fontWeight: 600 }}>{b.value}</span>
            <span className="mono" style={{ fontSize: 9.5, color: 'var(--ink-2)', width: 30, textAlign: 'right' }}>{Math.round(b.value/total*100)}%</span>
          </div>
        ))}
      </div>
      <div style={{ marginTop: 4 }}>
        <SimuladoBadge />
      </div>
    </div>
  );
}

function ReportScore({ area }) {
  const c = CIVITAS.riskColor(area.score);
  const tier = CIVITAS.RISK[CIVITAS.riskKeyFromScore(area.score)];
  // total polygon count is fixed at 16 in our model
  const total = 16;
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8, height: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'flex-end', gap: 6 }}>
        <span className="h-cond-x" style={{ fontSize: 56, color: c, lineHeight: 0.9, letterSpacing: 0.02 }}>{area.score}</span>
        <span className="mono" style={{ fontSize: 11, color: 'var(--ink-2)', marginBottom: 6, fontWeight: 700 }}>/100</span>
      </div>
      <span style={{
        display: 'inline-flex', alignSelf: 'flex-start', alignItems: 'center', gap: 5,
        padding: '3px 7px', background: c, color: '#fff',
        fontSize: 10, fontWeight: 800, letterSpacing: 0.1,
      }} className="mono uc">
        <span style={{ width: 5, height: 5, background: '#fff' }} />
        {tier.label}
      </span>
      <div style={{ marginTop: 'auto', display: 'flex', alignItems: 'baseline', gap: 6 }}>
        <span className="h-cond-x" style={{ fontSize: 22, color: 'var(--ink)' }}>
          #{String(area.rank).padStart(2,'0')}
        </span>
        <span className="mono uc" style={{ fontSize: 9, color: 'var(--ink-2)', fontWeight: 700 }}>
          de {total} polígonos
        </span>
      </div>
      <div style={{ display: 'flex', gap: 1.5, height: 6 }}>
        {Array.from({ length: total }).map((_, i) => (
          <div key={i} style={{
            flex: 1, background: i + 1 === area.rank ? c : (i + 1 < area.rank ? '#D0021B40' : 'var(--border-pp)'),
          }} />
        ))}
      </div>
    </div>
  );
}

function ReportEffectiveness({ area }) {
  const eff = Math.round(58 + (100 - area.score) * 0.3);
  const responseAvg = +(4 + area.score / 14).toFixed(1);
  const respPct = Math.min(100, (responseAvg / 8) * 100);
  const respOver = responseAvg > 8;
  const resources = Math.round(6 + area.score / 8);
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span className="h-cond-x" style={{ fontSize: 28, color: 'var(--brand)' }}>{eff}</span>
        <span className="mono" style={{ fontSize: 11, color: 'var(--ink-2)', fontWeight: 700 }}>%</span>
        <span className="mono uc" style={{ fontSize: 9, color: 'var(--ink-2)', fontWeight: 700, marginLeft: 4 }}>ações concluídas</span>
        <span style={{ flex: 1 }} />
        <SimuladoBadge />
      </div>
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 3 }}>
          <span className="mono uc" style={{ fontSize: 9, color: 'var(--ink-2)', fontWeight: 700, letterSpacing: 0.1 }}>
            Tempo médio resposta
          </span>
          <span className="mono" style={{ fontSize: 10, color: 'var(--ink)', fontWeight: 700 }}>
            {responseAvg}<span style={{ color: 'var(--ink-2)' }}>/8min</span>
          </span>
        </div>
        <div style={{ position: 'relative', height: 8, background: 'var(--paper-2)', border: '1px solid var(--border-pp)' }}>
          <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: `${Math.min(100, respPct)}%`,
                        background: respOver ? '#D0021B' : '#007A4D' }} />
          <div style={{ position: 'absolute', left: '100%', top: -2, bottom: -2, width: 2, background: 'var(--ink)', transform: 'translateX(-2px)' }} />
          <span className="mono" style={{ position: 'absolute', right: -2, top: -14, fontSize: 8.5, color: 'var(--ink-2)', fontWeight: 700, letterSpacing: 0.06 }}>META</span>
        </div>
      </div>
      <div style={{ display: 'flex', gap: 12, marginTop: 'auto' }}>
        <Cell label="Recursos" value={resources} big />
        <Sep />
        <Cell label="Patrulhas" value={Math.max(2, Math.round(resources * 0.6))} big />
        <Sep />
        <Cell label="Câmeras" value={Math.round(resources * 4.2)} big />
      </div>
    </div>
  );
}

function ReportTrend({ area, accent }) {
  const W = 280, H = 70;
  const data = _BB.useMemo(() => {
    const out = []; let s = area.fid * 13 + 7;
    const base = 40 + area.score / 2;
    for (let i = 0; i < 7; i++) {
      s = (s * 9301 + 49297) % 233280;
      out.push(Math.max(2, Math.round(base + Math.sin(i * 0.9) * 8 + (s / 233280 - 0.5) * 10)));
    }
    return out;
  }, [area.fid]);
  const max = Math.max(...data), min = Math.min(...data);
  const range = (max - min) || 1;
  const dx = W / (data.length - 1);
  const pts = data.map((v, i) => [i * dx, H - 4 - ((v - min) / range) * (H - 18)]);
  const path = 'M' + pts.map(p => p.map(n => n.toFixed(1)).join(',')).join(' L');
  const area2 = path + ` L${pts[pts.length-1][0].toFixed(1)},${H} L0,${H} Z`;
  const days = ['Seg','Ter','Qua','Qui','Sex','Sáb','Dom'];
  const infl = area.score >= 60 ? [{ day: 4, label: 'Reforço 19h' }] : [{ day: 3, label: 'Pico observado' }];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
        <span className="h-cond-x" style={{ fontSize: 18, color: 'var(--brand)' }}>7 DIAS</span>
        <span className="mono uc" style={{ fontSize: 9.5, color: 'var(--ink-2)', fontWeight: 700 }}>ocor./dia</span>
        <span style={{ flex: 1 }} />
        <SimuladoBadge />
        <span className="mono" style={{ fontSize: 10, color: 'var(--ink-2)' }}>
          min {min} · <span style={{ color: 'var(--ink)', fontWeight: 700 }}>max {max}</span>
        </span>
      </div>
      <svg width={W} height={H + 16} style={{ display: 'block' }}>
        {[0.25, 0.5, 0.75].map(t => (
          <line key={t} x1={0} y1={H * t + 4} x2={W} y2={H * t + 4} stroke="#E6ECF3" strokeWidth={0.6} strokeDasharray="2 3" />
        ))}
        <path d={area2} fill={accent} fillOpacity={0.16} />
        <path d={path} fill="none" stroke={accent} strokeWidth={1.6} strokeLinejoin="round" />
        {infl.map((inf, i) => {
          const [px, py] = pts[inf.day];
          const labelLeft = inf.day > 4;
          return (
            <g key={i}>
              <line x1={px} y1={py} x2={px} y2={H + 1} stroke={accent} strokeWidth={0.8} strokeDasharray="2 2" />
              <circle cx={px} cy={py} r={3.4} fill="#fff" stroke={accent} strokeWidth={1.8} />
              <rect x={labelLeft ? px - 88 : px + 6} y={py - 10} width={82} height={14} fill="var(--brand)" />
              <text x={labelLeft ? px - 84 : px + 10} y={py} fontSize={9} fontFamily="JetBrains Mono"
                    fill="#fff" letterSpacing={0.04} fontWeight={700} dominantBaseline="middle">
                {inf.label}
              </text>
            </g>
          );
        })}
        {days.map((d, i) => (
          <text key={d} x={i * dx} y={H + 14} fontSize={9} fontFamily="JetBrains Mono"
                fill={i === days.length - 1 ? 'var(--ink)' : 'var(--ink-2)'}
                textAnchor={i === 0 ? 'start' : i === days.length - 1 ? 'end' : 'middle'}
                fontWeight={i === days.length - 1 ? 700 : 500}>{d}</text>
        ))}
      </svg>
    </div>
  );
}

/* small atoms */
function Cell({ label, value, big, mono }) {
  return (
    <div>
      <div className="mono uc" style={{ fontSize: 8.5, color: 'var(--ink-2)', fontWeight: 700, letterSpacing: 0.1 }}>{label}</div>
      <div className={mono ? 'mono' : 'h-cond'} style={{ fontSize: big ? 18 : 13, color: 'var(--ink)', fontWeight: big ? 800 : 700 }}>{value}</div>
    </div>
  );
}
function Sep() { return <div style={{ width: 1, background: 'var(--border-pp)' }} />; }

function DeltaPaper({ value, inverted }) {
  if (value === 0) return <span className="mono" style={{ color: 'var(--ink-2)', fontSize: 10 }}>—</span>;
  const up = value > 0;
  const color = up ? '#D0021B' : '#007A4D';
  return (
    <span className="mono" style={{ color, fontSize: 11, fontWeight: 800, display: 'inline-flex', alignItems: 'center', gap: 3 }}>
      <span style={{ fontSize: 8 }}>{up ? '▲' : '▼'}</span>
      {Math.abs(value)}
    </span>
  );
}

Object.assign(window, { BottomBar });
