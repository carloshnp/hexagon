/* Top bars: header (w/ period selector), ranking strip (Bar 1), context strip (Bar 2). */

function HeaderBar({ now, periods, currentPeriod, periodLoading, periodOpen, setPeriodOpen, onChangePeriod, onStepPeriod }) {
  return (
    <div style={{
      height: 48, display: 'flex', alignItems: 'stretch',
      background: 'var(--brand)', color: '#fff',
      borderBottom: '1px solid #00305C',
      flexShrink: 0, position: 'relative', zIndex: 50,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '0 18px', borderRight: '1px solid #00305C', background: '#003B72' }}>
        <PrefeituraMark />
        <div style={{ display: 'flex', flexDirection: 'column', gap: 1, lineHeight: 1 }}>
          <span className="mono uc" style={{ fontSize: 8.5, color: '#9EC0E2', letterSpacing: 0.18 }}>
            Prefeitura da Cidade do Rio de Janeiro
          </span>
          <span className="h-cond-x" style={{ fontSize: 22, letterSpacing: 0.08, color: '#fff' }}>
            CIVITAS<span style={{ color: '#9EC0E2', marginLeft: 6, fontWeight: 500 }}>/RJ</span>
          </span>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', padding: '0 14px', borderRight: '1px solid #00305C' }}>
        <span className="mono uc" style={{ fontSize: 9.5, color: '#9EC0E2', letterSpacing: 0.14, fontWeight: 700 }}>
          Centro de Operações · Segurança Pública
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'stretch' }}>
        {['Mapa Operacional','Ocorrências','Análises','Recursos','Relatórios'].map((t, i) => (
          <button key={t} style={{
            padding: '0 18px', background: 'transparent', color: i===0 ? '#fff' : '#BFD4EA',
            border: 'none', borderRight: '1px solid #00305C',
            fontSize: 12, fontWeight: 600, letterSpacing: 0.04,
            position: 'relative',
          }}>
            {t}
            {i === 0 && <span style={{ position: 'absolute', left: 0, right: 0, bottom: -1, height: 3, background: '#fff' }} />}
          </button>
        ))}
      </div>

      <div style={{ flex: 1 }} />

      {/* period selector */}
      <PeriodSelector
        periods={periods}
        current={currentPeriod}
        loading={periodLoading}
        open={periodOpen}
        setOpen={setPeriodOpen}
        onChangePeriod={onChangePeriod}
        onStepPeriod={onStepPeriod}
      />

      <div style={{ padding: '0 16px', borderLeft: '1px solid #00305C', display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ width: 7, height: 7, background: '#3FE08A', borderRadius: '50%', boxShadow: '0 0 8px #3FE08A' }} />
        <span className="mono uc" style={{ fontSize: 10, color: '#fff', letterSpacing: 0.1, fontWeight: 700 }}>FEED AO VIVO</span>
      </div>
      <div style={{ padding: '0 16px', borderLeft: '1px solid #00305C', display: 'flex', alignItems: 'center', gap: 10 }}>
        <span className="mono" style={{ fontSize: 11, color: '#fff', fontWeight: 700 }}>{now}</span>
        <span className="mono" style={{ fontSize: 9.5, color: '#9EC0E2' }}>BRT</span>
      </div>
      <div style={{ padding: '0 16px', borderLeft: '1px solid #00305C', display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{ width: 24, height: 24, background: '#fff', color: 'var(--brand)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 10, fontWeight: 800 }}>RS</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          <span style={{ fontSize: 11.5, fontWeight: 700, color: '#fff' }}>R. Santos</span>
          <span className="mono" style={{ fontSize: 9, color: '#9EC0E2' }}>OP-44 · Analista</span>
        </div>
      </div>
    </div>
  );
}

function PrefeituraMark() {
  return (
    <div title="Logo Prefeitura do Rio (placeholder)" style={{
      width: 36, height: 36, border: '1.5px solid rgba(255,255,255,0.55)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      position: 'relative', flexShrink: 0,
    }}>
      <svg width="22" height="22" viewBox="0 0 24 24">
        <path d="M12 2 L21 5 L21 12 Q21 19 12 22 Q3 19 3 12 L3 5 Z"
              fill="none" stroke="#fff" strokeWidth="1.4" />
        <path d="M12 7 L12 17 M7 12 L17 12" stroke="#fff" strokeWidth="1.2" />
        <circle cx="12" cy="12" r="2" fill="#fff" />
      </svg>
    </div>
  );
}

/* === Period selector (label + chevrons + dropdown) === */
function PeriodSelector({ periods, current, loading, open, setOpen, onChangePeriod, onStepPeriod }) {
  const label = current ? `S${current.week} · ${current.year}` : 'S— · ——';
  return (
    <div style={{ display: 'flex', alignItems: 'stretch', borderLeft: '1px solid #00305C', position: 'relative' }}>
      <button onClick={() => onStepPeriod(+1)} title="Semana anterior" style={pillBtn()}>‹</button>
      <button
        onClick={() => setOpen(!open)}
        style={{
          background: open ? '#003B72' : 'transparent',
          border: 'none',
          borderLeft: '1px solid #00305C', borderRight: '1px solid #00305C',
          color: '#fff', padding: '0 14px',
          display: 'flex', alignItems: 'center', gap: 8,
          cursor: 'pointer', position: 'relative',
        }}
      >
        <span className="mono" style={{ fontSize: 12, fontWeight: 800, letterSpacing: 0.06 }}>{label}</span>
        {loading
          ? <span className="mono" style={{ width: 7, height: 7, background: '#F5A623', borderRadius: '50%', animation: 'pulse 0.9s ease-in-out infinite' }} />
          : <span className="mono" style={{ fontSize: 10, color: '#9EC0E2', fontWeight: 700 }}>▾</span>
        }
        <span style={{ position: 'absolute', left: 0, right: 0, bottom: 0, height: 2, background: open ? '#fff' : 'transparent' }} />
      </button>
      <button onClick={() => onStepPeriod(-1)} title="Semana posterior" style={pillBtn()}>›</button>

      {open && (
        <div style={{
          position: 'absolute', top: '100%', right: 0, marginTop: 1,
          background: '#FFFFFF', color: 'var(--text)',
          border: '1px solid #BFD0E3', minWidth: 220,
          boxShadow: '0 8px 24px rgba(0,30,80,0.18)', zIndex: 80,
        }}>
          <div style={{ padding: '8px 12px', background: '#F4F7FB', borderBottom: '1px solid #D6E0EC' }}>
            <span className="mono uc" style={{ fontSize: 9, color: 'var(--brand)', fontWeight: 800, letterSpacing: 0.14 }}>
              Períodos disponíveis
            </span>
          </div>
          {periods.map(p => (
            <button key={p.key}
              onClick={() => onChangePeriod(p.key)}
              style={{
                width: '100%', padding: '9px 12px',
                background: p.key === current?.key ? 'var(--brand-tint)' : '#FFFFFF',
                border: 'none', borderBottom: '1px solid #EEF2F8',
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                color: 'var(--text)', fontSize: 12, cursor: 'pointer',
                fontWeight: p.key === current?.key ? 700 : 500,
              }}>
              <span>{p.label}</span>
              <span className="mono" style={{ fontSize: 10, color: 'var(--text-2)' }}>
                S{p.week}/{p.year}
              </span>
            </button>
          ))}
          <div style={{ padding: '6px 12px', background: '#F4F7FB' }}>
            <span className="mono" style={{ fontSize: 9, color: 'var(--text-2)' }}>
              Esc para fechar
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

function pillBtn() {
  return {
    width: 28, background: 'transparent', border: 'none', color: '#fff',
    fontSize: 16, fontWeight: 700, cursor: 'pointer',
  };
}

/* === Bar 1 — ranking strip === */
function RankingStrip({ areas, loading, selectedFid, onSelect, tab, onTabChange, threshold, onThresholdChange }) {
  const isEmpty = !loading && areas.length === 0;
  return (
    <div style={{
      height: 56, display: 'flex', alignItems: 'stretch',
      background: 'var(--surface)', borderBottom: '1px solid var(--border)',
      flexShrink: 0,
    }}>
      <div style={{
        display: 'flex', alignItems: 'stretch', flexShrink: 0,
        background: 'var(--brand)', borderRight: '1px solid #00305C',
      }}>
        <StripTab label="TODOS"   active={tab === 'todos'}   onClick={() => onTabChange('todos')} />
        <StripTab label="CRÍTICO" active={tab === 'critico'} onClick={() => onTabChange('critico')} />
      </div>

      <div style={{
        display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0,
        padding: tab === 'critico' ? '0 14px' : '0',
        width: tab === 'critico' ? 240 : 0,
        overflow: 'hidden',
        opacity: tab === 'critico' ? 1 : 0,
        transition: 'opacity 200ms ease, width 220ms ease, padding 220ms ease',
        borderRight: tab === 'critico' ? '1px solid var(--border)' : 'none',
      }}>
        <span className="mono uc" style={{ fontSize: 9, color: 'var(--text-2)', fontWeight: 700, letterSpacing: 0.12, whiteSpace: 'nowrap' }}>
          Score mín.
        </span>
        <input
          type="range" className="score-slider"
          min={0} max={100} value={threshold}
          onChange={e => onThresholdChange(+e.target.value)}
          style={{ '--thumb-color': CIVITAS.riskColor(threshold), width: 110, flexShrink: 0 }}
        />
        <span className="mono" style={{ fontSize: 13, fontWeight: 800, color: CIVITAS.riskColor(threshold), minWidth: 26, textAlign: 'right' }}>
          {threshold}
        </span>
      </div>

      <div className="scroll" style={{ flex: 1, display: 'flex', overflowX: 'auto', alignItems: 'stretch' }}>
        {loading
          ? Array.from({ length: 8 }).map((_, i) => <ChipSkeleton key={i} />)
          : isEmpty
            ? <EmptyStrip threshold={threshold} />
            : areas.map((a, i) => (
                <RankingChip
                  key={a.fid}
                  a={a}
                  displayRank={tab === 'critico' ? i + 1 : a.rank}
                  selected={a.fid === selectedFid}
                  onSelect={() => onSelect(a.fid)}
                />
              ))
        }
      </div>
    </div>
  );
}

function ChipSkeleton() {
  return (
    <div style={{
      flex: '0 0 auto', minWidth: 168,
      display: 'flex', alignItems: 'center', gap: 8,
      borderRight: '1px solid var(--border)', padding: '0 12px 0 0',
    }}>
      <div style={{ width: 32, height: '100%', background: '#EEF2F8' }} />
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6, padding: '12px 0' }}>
        <Shimmer width={92} height={12} />
        <Shimmer width={56} height={10} />
      </div>
    </div>
  );
}

function RankingChip({ a, displayRank, selected, onSelect }) {
  const c = CIVITAS.riskColor(a.score);
  return (
    <button onClick={onSelect} className="focus-ring" style={{
      flex: '0 0 auto', minWidth: 168,
      display: 'flex', alignItems: 'stretch', gap: 0,
      background: selected ? 'var(--surface-2)' : 'transparent',
      border: 'none', borderRight: '1px solid var(--border)',
      padding: 0, color: 'var(--text)', position: 'relative',
      cursor: 'pointer',
    }}>
      <div style={{
        width: 32, background: selected ? 'var(--brand)' : 'transparent',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        borderRight: '1px solid var(--border)',
      }}>
        <span className="h-cond-x" style={{ fontSize: 16, color: selected ? '#fff' : 'var(--text-2)' }}>
          {String(displayRank).padStart(2,'0')}
        </span>
      </div>
      <div style={{ padding: '8px 12px', display: 'flex', flexDirection: 'column', gap: 4, alignItems: 'flex-start', textAlign: 'left', minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span className="h-cond-x" style={{ fontSize: 15, lineHeight: 1, letterSpacing: 0.06 }}>
            {a.polyId}
          </span>
          <span className="mono" style={{
            fontSize: 8.5, fontWeight: 800, letterSpacing: 0.08,
            padding: '1px 4px', background: 'var(--brand)', color: '#fff',
          }}>{a.zoneCode}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <ScoreBadge score={a.score} mini />
          <Delta value={a.score_delta} />
        </div>
      </div>
      <span style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: 2, background: c }} />
    </button>
  );
}

function StripTab({ label, active, onClick }) {
  return (
    <button onClick={onClick} className="mono uc" style={{
      padding: '0 18px',
      background: active ? 'rgba(0,0,0,0.18)' : 'transparent',
      border: 'none', borderRight: '1px solid #00305C',
      color: active ? '#fff' : '#9EC0E2',
      fontSize: 10.5, fontWeight: active ? 800 : 600, letterSpacing: 0.14,
      cursor: 'pointer', position: 'relative',
      display: 'flex', alignItems: 'center',
    }}>
      {label}
      {active && <span style={{ position: 'absolute', left: 0, right: 0, bottom: 0, height: 3, background: '#0066CC' }} />}
    </button>
  );
}

function EmptyStrip({ threshold }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', padding: '0 20px' }}>
      <span className="mono" style={{ fontSize: 11, color: 'var(--text-3)', fontWeight: 600 }}>
        Nenhuma área acima de{' '}
        <span style={{ fontWeight: 800, color: 'var(--text-2)' }}>{threshold}</span>
      </span>
    </div>
  );
}

function FilteredAggregate({ filteredAreas }) {
  const count = filteredAreas.length;
  const top = filteredAreas[0];
  const c = CIVITAS.riskColor(top.score);
  return (
    <div style={{
      height: 64, display: 'flex', alignItems: 'stretch',
      background: 'var(--surface)', borderBottom: '1px solid var(--border)',
      flexShrink: 0,
    }}>
      <span style={{ width: 3, background: '#D0021B', flexShrink: 0 }} />
      <ContextCell width={260} kind="primary">
        <div className="mono uc" style={{ fontSize: 9, color: 'var(--text-2)', fontWeight: 700, letterSpacing: 0.14 }}>
          Filtro ativo · Crítico
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ width: 8, height: 8, background: '#D0021B', flexShrink: 0 }} />
          <span className="h-cond" style={{ fontSize: 16 }}>
            {count} {count === 1 ? 'área qualificada' : 'áreas qualificadas'}
          </span>
        </div>
      </ContextCell>
      <ContextCell width={220} label="Score mais alto">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span className="h-cond-x" style={{ fontSize: 22, color: c }}>{top.score}</span>
          <span className="mono" style={{ fontSize: 10, color: 'var(--text-2)', fontWeight: 700 }}>/100</span>
        </div>
        <div className="mono" style={{ fontSize: 10, color: 'var(--text-3)' }}>
          {top.polyId} · {top.nome_area}
        </div>
      </ContextCell>
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', padding: '0 20px', color: 'var(--text-3)', fontSize: 11.5 }}>
        Selecione uma área para ver detalhes operacionais.
      </div>
    </div>
  );
}

/* === Bar 2 — context strip === */
function ContextStrip({ area, loading, tab, filteredAreas }) {
  if (loading) {
    return (
      <div style={{
        height: 64, display: 'flex', alignItems: 'center',
        background: 'var(--surface)', borderBottom: '1px solid var(--border)',
        padding: '0 16px', gap: 28,
      }}>
        {[1,2,3,4,5].map(i => (
          <div key={i} style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            <Shimmer width={86} height={9} />
            <Shimmer width={140} height={16} />
          </div>
        ))}
      </div>
    );
  }
  if (!area) {
    if (tab === 'critico' && filteredAreas && filteredAreas.length > 0) {
      return <FilteredAggregate filteredAreas={filteredAreas} />;
    }
    return (
      <div style={{
        height: 64, display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: 'var(--surface)', borderBottom: '1px solid var(--border)',
        color: 'var(--text-3)', fontSize: 12, gap: 10,
      }}>
        <span className="mono">▢</span>
        <span>Selecione um polígono para visualizar o contexto operacional.</span>
      </div>
    );
  }
  const c = CIVITAS.riskColor(area.score);
  return (
    <div style={{
      height: 64, display: 'flex', alignItems: 'stretch',
      background: 'var(--surface)', borderBottom: '1px solid var(--border)',
      flexShrink: 0, position: 'relative',
    }}>
      <span style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: 3, background: c }} />

      <ContextCell width={280} kind="primary">
        <div className="mono uc" style={{ fontSize: 9, color: 'var(--text-2)', fontWeight: 700, letterSpacing: 0.14 }}>
          Polígono selecionado · {area.zone}
        </div>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
          <span className="h-cond-x" style={{ fontSize: 22, letterSpacing: 0.04 }}>
            {area.polyId} · {area.nome_area.toUpperCase()}
          </span>
          <span className="mono" style={{ fontSize: 11, color: 'var(--text-3)' }}>
            #{String(area.rank).padStart(2,'0')}
          </span>
        </div>
        <div className="mono uc" style={{ fontSize: 9, color: 'var(--text-2)', letterSpacing: 0.14, fontWeight: 700 }}>
          Polígono H3 · {area.polyZoneId} <span style={{ opacity: 0.6 }}>· {area.h3.slice(0, 8)}…</span>
        </div>
      </ContextCell>

      <ContextCell width={236} label="Tipo principal">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ width: 8, height: 8, background: c, flexShrink: 0 }} />
          <span className="h-cond" style={{ fontSize: 15, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{area.type}</span>
        </div>
        <div className="mono" style={{ fontSize: 10, color: 'var(--text-3)', fontWeight: 600 }}>
          Frequência dominante · 24h
        </div>
      </ContextCell>

      <ContextCell width={170} label="Ocorrências">
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
          <span className="h-cond-x" style={{ fontSize: 22 }}>{area.occurrence_count.toLocaleString('pt-BR')}</span>
          <Delta value={area.score_delta} />
        </div>
        <div className="mono" style={{ fontSize: 10, color: 'var(--text-3)' }}>
          últimas 24h
        </div>
      </ContextCell>

      <ContextCell width={150} label="Nível de risco">
        <RiskBadge score={area.score} />
        <div className="mono" style={{ fontSize: 10, color: 'var(--text-3)' }}>
          Score {area.score}/100
        </div>
      </ContextCell>

      <ContextCell width={150} label="Última atualização">
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ width: 6, height: 6, background: '#007A4D', borderRadius: '50%' }} />
          <span className="mono" style={{ fontSize: 12, color: 'var(--text)' }}>há {area.updated}</span>
        </div>
        <div className="mono" style={{ fontSize: 10, color: 'var(--text-3)' }}>
          SISP feed · auto-sync 30s
        </div>
      </ContextCell>

      <div style={{ flex: 1 }} />

      <div style={{ display: 'flex', alignItems: 'center', borderLeft: '1px solid var(--border)' }}>
        <button className="mono uc" style={contextActionBtn}>
          <Mark kind="frame" size={10} /> Despachar
        </button>
        <button className="mono uc" style={contextActionBtn}>
          <Mark kind="plus" size={10} /> Relatório
        </button>
        <button className="mono uc" style={{
          height: '100%', padding: '0 18px',
          background: 'var(--brand)', border: 'none', color: '#fff',
          fontSize: 10.5, letterSpacing: 0.12, fontWeight: 700,
          display: 'flex', alignItems: 'center', gap: 6,
        }}>
          Abrir Painel <Mark kind="chevron-r" size={10} />
        </button>
      </div>
    </div>
  );
}

const contextActionBtn = {
  height: '100%', padding: '0 16px', background: 'transparent',
  border: 'none', borderRight: '1px solid var(--border)', color: 'var(--text-2)',
  fontSize: 10, letterSpacing: 0.1, fontWeight: 700, display: 'flex', alignItems: 'center', gap: 6,
};

function ContextCell({ width, label, kind, children }) {
  return (
    <div style={{
      width, padding: '8px 16px', borderRight: '1px solid var(--border)',
      display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 3,
      background: kind === 'primary' ? 'var(--bg-2)' : 'transparent',
    }}>
      {label && <div className="mono uc" style={{ fontSize: 9, color: 'var(--text-2)', letterSpacing: 0.14, fontWeight: 700 }}>{label}</div>}
      {children}
    </div>
  );
}

Object.assign(window, { HeaderBar, RankingStrip, ContextStrip });
