/* Left sidebar — issue-centric reports + slide-out Assistente drawer. */

const _SB = React;

function Sidebar({ occurrences, areasByFid, loading, reports, selectedFid, hoverFid, onHover, filter, setFilter, flyingIssueId, onCardClick, chatOpen, onToggleChat }) {
  const filterTabs = ['Todas','Crítico','Alto','Médio','Em Atendimento'];
  const [expandedId, setExpandedId] = _SB.useState(null);

  const selectedArea = selectedFid ? areasByFid[selectedFid] : null;

  const matchesUrgency = (i) => {
    if (filter === 'Todas') return true;
    if (filter === 'Em Atendimento') return i.status === 'EM_ATENDIMENTO';
    if (filter === 'Crítico') return i.urgency === 'CRÍTICO';
    if (filter === 'Alto')    return i.urgency === 'ALTO';
    if (filter === 'Médio')   return i.urgency === 'MÉDIO';
    return true;
  };
  const matchesPolygon = (i) => {
    if (!selectedArea) return true;
    return i.primary_fid === selectedFid || (i.affected_fids || []).includes(selectedFid);
  };

  const visible = (occurrences || []).filter(i => matchesUrgency(i) && matchesPolygon(i));

  _SB.useEffect(() => {
    if (expandedId && !visible.find(i => i.id === expandedId)) setExpandedId(null);
  }, [selectedFid, filter, occurrences]);

  const handleExpand = (issue) => {
    setExpandedId(prev => {
      const next = prev === issue.id ? null : issue.id;
      if (next) CIVITAS.dataStore.loadReport(issue.primary_fid).catch(() => {});
      return next;
    });
  };

  return (
    <div style={{
      width: '33.333%', flexShrink: 0, height: '100%',
      borderRight: '1px solid var(--border)', background: 'var(--surface)',
      display: 'flex', flexDirection: 'column',
    }}>
      {/* Header */}
      <div style={{ padding: '12px 16px 10px', borderBottom: '1px solid var(--border)', flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
          <div className="h-cond-x" style={{ fontSize: 16, letterSpacing: 0.04 }}>
            OCORRÊNCIAS CRÍTICAS
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span className="mono" style={{ fontSize: 11, color: 'var(--text-2)', fontWeight: 700 }}>
              {loading ? '—/—' : `${visible.length}/${(occurrences || []).length}`}
            </span>
            <button onClick={onToggleChat} className="mono uc" style={{
              display: 'flex', alignItems: 'center', gap: 5,
              padding: '4px 9px',
              background: chatOpen ? 'var(--brand)' : 'var(--bg)',
              border: `1px solid ${chatOpen ? 'var(--brand)' : 'var(--border-2)'}`,
              color: chatOpen ? '#fff' : 'var(--text-2)',
              fontSize: 9.5, fontWeight: 800, letterSpacing: 0.12,
              cursor: 'pointer', transition: 'background 150ms, color 150ms',
            }}>
              <svg width="11" height="11" viewBox="0 0 16 16" fill="none">
                <path d="M14 2H2a1 1 0 00-1 1v8a1 1 0 001 1h2v3l4-3h6a1 1 0 001-1V3a1 1 0 00-1-1z"
                      stroke="currentColor" strokeWidth="1.4" fill={chatOpen ? 'rgba(255,255,255,0.2)' : 'none'} />
              </svg>
              Assistente
            </button>
          </div>
        </div>
        <div className="mono uc" style={{ fontSize: 10, color: 'var(--text-2)', letterSpacing: 0.12, marginTop: 4, fontWeight: 700 }}>
          {loading
            ? 'Carregando ciclo…'
            : selectedArea
              ? `Filtrado · ${selectedArea.polyId} (${selectedArea.nome_area})`
              : 'Itens acionáveis · ciclo 24h'}
        </div>
      </div>

      {/* Filter chips */}
      <div style={{ display: 'flex', borderBottom: '1px solid var(--border)', flexShrink: 0 }}>
        {filterTabs.map((z, i) => (
          <button key={z} onClick={() => setFilter(z)} disabled={loading} className="mono uc" style={{
            flex: 1, padding: '9px 0', fontSize: 10, letterSpacing: 0.08, fontWeight: 800,
            background: filter === z ? 'var(--brand-tint)' : 'var(--surface)',
            color: loading ? 'var(--text-3)' : filter === z ? 'var(--brand)' : 'var(--text-2)',
            border: 'none', borderRight: i < filterTabs.length - 1 ? '1px solid var(--border)' : 'none',
            cursor: loading ? 'default' : 'pointer', position: 'relative',
            whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
          }}>
            {z === 'Em Atendimento' ? 'EM ATEND.' : z.toUpperCase()}
            {filter === z && <span style={{ position: 'absolute', left: 0, right: 0, bottom: 0, height: 2, background: 'var(--brand)' }} />}
          </button>
        ))}
      </div>

      <div style={{
        padding: '6px 14px', display: 'flex', justifyContent: 'space-between',
        borderBottom: '1px solid var(--border)', background: 'var(--bg-2)', flexShrink: 0,
      }}>
        <span className="mono uc" style={{ fontSize: 10, color: 'var(--text-2)', fontWeight: 700 }}>
          {loading ? 'Carregando…' : selectedArea ? 'Filtrado por polígono' : 'Ordenar: Urgência ↓'}
        </span>
        <span className="mono" style={{ fontSize: 10, color: 'var(--text-2)' }}>
          {loading ? '' : `${visible.filter(i => i.status === 'PENDENTE').length} pendentes`}
        </span>
      </div>

      <div className="scroll" style={{ flex: 1, overflowY: 'auto', position: 'relative' }}>
        {loading ? (
          <><CardSkeleton /><CardSkeleton /><CardSkeleton /></>
        ) : visible.length === 0 ? (
          <EmptyState />
        ) : (
          visible.map(issue => (
            <IssueCard
              key={issue.id}
              issue={issue}
              expanded={issue.id === expandedId}
              onExpand={handleExpand}
              report={reports[issue.primary_fid]}
              selected={issue.primary_fid === selectedFid}
              hovered={issue.primary_fid === hoverFid}
              flying={issue.id === flyingIssueId}
              onClick={() => onCardClick(issue)}
              onMouseEnter={() => onHover(issue.primary_fid)}
              onMouseLeave={() => onHover(null)}
            />
          ))
        )}
        <div style={{ height: 24 }} />
      </div>

      <div style={{
        borderTop: '1px solid var(--border)', display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)',
        background: 'var(--bg-2)', flexShrink: 0,
      }}>
        <FootStat label="Pendentes" value={loading ? '—' : (occurrences || []).filter(i => i.status === 'PENDENTE').length}    delta="+2" tone="#D0021B" />
        <FootStat label="Em ação"   value={loading ? '—' : (occurrences || []).filter(i => i.status === 'EM_ATENDIMENTO').length} delta="+1" tone="#0066CC" border />
        <FootStat label="Críticas"  value={loading ? '—' : (occurrences || []).filter(i => i.urgency === 'CRÍTICO').length}    delta="+1" tone="#D0021B" />
      </div>
    </div>
  );
}

/* ── Assistente drawer (always mounted, slides in from the left sidebar) ──── */
const DRAWER_WIDTH = 360;

function AssistentePanel({ open, onClose, selectedFid, selectedArea }) {
  const [msgs, setMsgs]       = _SB.useState([]);
  const [input, setInput]     = _SB.useState('');
  const [sending, setSending] = _SB.useState(false);
  const bottomRef = _SB.useRef(null);

  _SB.useEffect(() => {
    if (open) bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [msgs, open]);

  const send = async () => {
    const q = input.trim();
    if (!q || sending) return;
    setInput('');
    setMsgs(prev => [...prev, { role: 'user', text: q, id: Date.now() }]);
    setSending(true);
    try {
      const res = await CIVITAS.dataStore.chat(q, selectedFid);
      setMsgs(prev => [...prev, {
        role: 'assistant', text: res.answer, id: Date.now() + 1,
        limitations: res.limitations, llm_mode: res.llm_mode,
        evidence_refs: res.evidence_refs,
      }]);
    } catch (e) {
      setMsgs(prev => [...prev, { role: 'error', text: 'Erro ao processar. Verifique a conexão.', id: Date.now() + 1 }]);
    }
    setSending(false);
  };

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
  };

  return (
    <div style={{
      width: open ? DRAWER_WIDTH : 0,
      flexShrink: 0,
      overflow: 'hidden',
      transition: 'width 260ms cubic-bezier(0.4, 0, 0.2, 1)',
      borderRight: '1px solid var(--border)',
      background: 'var(--surface)',
      display: 'flex', flexDirection: 'column',
      position: 'relative',
    }}>
      {/* Inner wrapper at fixed width so content never distorts during animation */}
      <div style={{ width: DRAWER_WIDTH, height: '100%', display: 'flex', flexDirection: 'column' }}>
        {/* Panel header */}
        <div style={{
          height: 48, display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '0 14px', borderBottom: '1px solid var(--border)',
          background: 'var(--brand)', flexShrink: 0,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
              <path d="M14 2H2a1 1 0 00-1 1v8a1 1 0 001 1h2v3l4-3h6a1 1 0 001-1V3a1 1 0 00-1-1z"
                    stroke="#9EC0E2" strokeWidth="1.4" fill="rgba(255,255,255,0.1)" />
            </svg>
            <span className="h-cond-x" style={{ fontSize: 13, color: '#fff', letterSpacing: 0.06 }}>
              ASSISTENTE
            </span>
            <span className="mono" style={{ fontSize: 9, color: '#9EC0E2', fontWeight: 600 }}>
              · FarolRio IA
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            {msgs.length > 0 && (
              <button onClick={() => setMsgs([])} className="mono uc" style={{
                background: 'transparent', border: '1px solid #00305C',
                color: '#9EC0E2', fontSize: 9, fontWeight: 700, letterSpacing: 0.1,
                padding: '3px 7px', cursor: 'pointer',
              }}>Limpar</button>
            )}
            <button onClick={onClose} style={{
              background: 'transparent', border: 'none', color: '#9EC0E2',
              fontSize: 18, cursor: 'pointer', lineHeight: 1, padding: '0 2px',
            }}>×</button>
          </div>
        </div>

        {/* Context badge */}
        {selectedArea && (
          <div style={{
            padding: '6px 14px', background: 'var(--brand-tint)',
            borderBottom: '1px solid var(--border-2)',
            display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0,
          }}>
            <span style={{ width: 6, height: 6, background: 'var(--brand)', flexShrink: 0 }} />
            <span className="mono" style={{ fontSize: 10, color: 'var(--brand)', fontWeight: 700 }}>
              Contexto: {selectedArea.polyId} · {selectedArea.nome_area}
            </span>
          </div>
        )}

        {/* Empty / welcome */}
        {msgs.length === 0 && (
          <div style={{
            flex: 1, display: 'flex', flexDirection: 'column',
            alignItems: 'center', justifyContent: 'center',
            gap: 14, padding: '20px 18px',
          }}>
            <div style={{
              width: 44, height: 44, background: 'var(--brand-tint)',
              border: '1px solid var(--border-2)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"
                      stroke="var(--brand)" strokeWidth="1.4" fill="var(--brand-tint)" />
              </svg>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div className="h-cond-x" style={{ fontSize: 12, color: 'var(--text)', marginBottom: 5 }}>
                ANÁLISE ASSISTIDA
              </div>
              <div style={{ fontSize: 11.5, color: 'var(--text-2)', lineHeight: 1.5, maxWidth: 260 }}>
                {selectedArea
                  ? `Pergunte sobre ${selectedArea.nome_area} — scores, ocorrências, horários críticos e ações recomendadas.`
                  : 'Pergunte sobre regiões, scores, ocorrências e dados do CompStat. Selecione uma região para análise específica.'}
              </div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 5, width: '100%' }}>
              {[
                selectedArea ? `Qual o risco de ${selectedArea.nome_area}?` : 'Quais são as regiões de maior risco?',
                'Quais os horários críticos de ocorrência?',
                'Que ações são recomendadas para esta área?',
              ].map(s => (
                <button key={s} onClick={() => setInput(s)} style={{
                  padding: '7px 10px', background: 'var(--bg)',
                  border: '1px solid var(--border)', textAlign: 'left',
                  fontSize: 11, color: 'var(--text-2)', cursor: 'pointer',
                  fontFamily: 'Inter', lineHeight: 1.35,
                  transition: 'background 100ms',
                }}>{s}</button>
              ))}
            </div>
          </div>
        )}

        {/* Messages */}
        {msgs.length > 0 && (
          <div className="scroll" style={{
            flex: 1, overflowY: 'auto',
            padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: 10,
          }}>
            {msgs.map(m => <ChatMessage key={m.id} msg={m} />)}
            {sending && <TypingIndicator />}
            <div ref={bottomRef} />
          </div>
        )}

        {/* Input */}
        <div style={{
          borderTop: '1px solid var(--border)', padding: '10px 14px',
          flexShrink: 0, background: 'var(--surface)',
        }}>
          <div style={{
            display: 'flex', gap: 8, alignItems: 'flex-end',
            border: '1px solid var(--border-2)', background: 'var(--bg)', padding: '8px 10px',
          }}>
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKey}
              placeholder="Pergunte sobre regiões, scores, ocorrências…"
              rows={2}
              style={{
                flex: 1, background: 'transparent', border: 'none', outline: 'none',
                resize: 'none', fontSize: 12, fontFamily: 'Inter',
                color: 'var(--text)', lineHeight: 1.45,
              }}
            />
            <button
              onClick={send}
              disabled={!input.trim() || sending}
              style={{
                width: 32, height: 32, flexShrink: 0,
                background: input.trim() && !sending ? 'var(--brand)' : 'var(--bg-2)',
                border: '1px solid var(--border-2)',
                color: input.trim() && !sending ? '#fff' : 'var(--text-3)',
                cursor: input.trim() && !sending ? 'pointer' : 'default',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                transition: 'background 120ms',
              }}
            >
              {sending
                ? <Spinner size={12} color="var(--brand)" />
                : <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                    <path d="M2 14L14 8 2 2v4.5l8 1.5-8 1.5z" fill="currentColor" />
                  </svg>
              }
            </button>
          </div>
          <div className="mono" style={{ fontSize: 9, color: 'var(--text-3)', marginTop: 5, textAlign: 'right' }}>
            Enter para enviar · Shift+Enter nova linha
          </div>
        </div>
      </div>
    </div>
  );
}

function ChatMessage({ msg }) {
  const [showMeta, setShowMeta] = _SB.useState(false);
  if (msg.role === 'user') {
    return (
      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
        <div style={{
          maxWidth: '85%', padding: '8px 12px',
          background: 'var(--brand)', color: '#fff',
          fontSize: 12, lineHeight: 1.5,
        }}>{msg.text}</div>
      </div>
    );
  }
  if (msg.role === 'error') {
    return (
      <div style={{
        padding: '8px 12px', background: '#FDECEE', border: '1px solid #F2B5BC',
        fontSize: 11.5, color: '#7A0411', lineHeight: 1.45,
      }}>{msg.text}</div>
    );
  }
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      <div style={{
        padding: '10px 12px', background: 'var(--bg-2)', border: '1px solid var(--border)',
        fontSize: 12, color: 'var(--text)', lineHeight: 1.6,
      }}>
        {msg.text}
      </div>
      {msg.limitations?.length > 0 && (
        <div style={{
          padding: '5px 8px', background: '#FFF4DC', border: '1px solid #F5A62355',
          fontSize: 10.5, color: '#8A5400', lineHeight: 1.4,
        }}>
          <span className="mono uc" style={{ fontSize: 8.5, fontWeight: 800 }}>Aviso · </span>
          {msg.limitations.join(' ')}
        </div>
      )}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span className="mono" style={{ fontSize: 9, color: 'var(--text-3)', fontWeight: 600 }}>
          {msg.llm_mode === 'fake' ? 'Determinístico' : 'Claude'}
        </span>
        {msg.evidence_refs?.length > 0 && (
          <button onClick={() => setShowMeta(v => !v)} className="mono" style={{
            background: 'transparent', border: 'none', padding: 0,
            fontSize: 9, color: 'var(--brand)', cursor: 'pointer', fontWeight: 700,
          }}>
            {showMeta ? '▴ ocultar fontes' : `▾ ${msg.evidence_refs.length} fonte(s)`}
          </button>
        )}
      </div>
      {showMeta && msg.evidence_refs?.length > 0 && (
        <div style={{
          padding: '6px 10px', background: 'var(--bg)', border: '1px solid var(--border)',
          display: 'flex', flexDirection: 'column', gap: 4,
        }}>
          {msg.evidence_refs.map((e, i) => (
            <div key={i} style={{ fontSize: 10.5, color: 'var(--text-2)', lineHeight: 1.4 }}>
              <span className="mono uc" style={{ fontSize: 8.5, fontWeight: 700, color: 'var(--brand)' }}>
                {e.source}
              </span>
              {e.description ? ` · ${e.description}` : ''}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function TypingIndicator() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '4px 0' }}>
      <Spinner size={11} color="var(--brand)" />
      <span className="mono" style={{ fontSize: 10, color: 'var(--text-3)', fontWeight: 600 }}>
        Analisando dados…
      </span>
    </div>
  );
}

/* ── Remaining sidebar sub-components ────────────────────────────────────── */

function CardSkeleton() {
  return (
    <div style={{ position: 'relative', padding: '12px 14px 14px 20px', borderBottom: '1px solid var(--border)', background: 'var(--surface)' }}>
      <span style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: 4, background: '#D6E0EC' }} />
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8 }}>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', flex: 1 }}>
          <Shimmer width={14} height={10} />
          <Shimmer width={140} height={13} />
        </div>
        <Shimmer width={56} height={14} />
      </div>
      <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 6 }}>
        <Shimmer width="100%" height={10} />
        <Shimmer width="84%"  height={10} />
      </div>
      <div style={{ marginTop: 10, display: 'flex', gap: 6 }}>
        <Shimmer width={40} height={14} />
        <Shimmer width={40} height={14} />
        <Shimmer width={40} height={14} />
      </div>
      <div style={{ marginTop: 10, display: 'flex', justifyContent: 'space-between' }}>
        <Shimmer width={92} height={14} />
        <Shimmer width={88} height={18} />
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div style={{
      padding: '36px 22px', textAlign: 'center',
      display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12,
      borderBottom: '1px solid var(--border)',
    }}>
      <div style={{
        width: 56, height: 56, border: '1.5px solid var(--border-2)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-3)',
      }}>
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
          <path d="M3 12l4-4 4 4 6-6 4 4" stroke="currentColor" strokeWidth="1.5" />
          <circle cx="17" cy="7" r="1.5" fill="currentColor" />
        </svg>
      </div>
      <div className="h-cond-x" style={{ fontSize: 13, color: 'var(--text)', letterSpacing: 0.04 }}>
        SEM OCORRÊNCIAS ATIVAS
      </div>
      <div style={{ fontSize: 11.5, color: 'var(--text-2)', lineHeight: 1.45, maxWidth: 220 }}>
        Este polígono não possui ocorrências críticas ativas no ciclo atual. Monitoramento padrão mantido.
      </div>
    </div>
  );
}

function IssueCard({ issue, expanded, onExpand, report, selected, hovered, flying, onClick, onMouseEnter, onMouseLeave }) {
  const u = CIVITAS.URGENCY[issue.urgency];
  const reportStatus  = report?.status;
  const reportReady   = reportStatus === 'ready';
  const reportFailed  = reportStatus === 'error';
  const reportLoading = reportStatus === 'loading';
  const detail = reportReady ? (report.data.occurrences || []).find(o => o.id === issue.id) : null;

  return (
    <div onMouseEnter={onMouseEnter} onMouseLeave={onMouseLeave}
         style={{
           position: 'relative', borderBottom: '1px solid var(--border)',
           background: selected ? 'var(--brand-tint)' : hovered ? 'var(--bg-2)' : 'var(--surface)',
           transition: 'background 100ms',
           animation: reportLoading ? 'border-pulse 1.4s ease-in-out infinite' : 'none',
         }}>
      <span style={{
        position: 'absolute', left: 0, top: 0, bottom: 0,
        width: expanded ? 6 : 4, background: expanded ? 'var(--brand-2)' : 'var(--brand)',
        transition: 'width 160ms',
      }} />
      <span style={{ position: 'absolute', left: 0, top: 0, width: expanded ? 6 : 4, height: 22, background: u.color }} />

      <div onClick={onClick} style={{ padding: '12px 14px 0 20px', cursor: 'pointer' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 0, flex: 1 }}>
            {reportLoading
              ? <span style={{ width: 14, display: 'inline-flex', justifyContent: 'center' }}><Spinner size={11} color="var(--brand-2)" /></span>
              : <span className="mono" style={{ fontSize: 11, color: 'var(--text-2)', fontWeight: 700 }}>#{String(issue.rank).padStart(2,'00')}</span>
            }
            <span className="h-cond" style={{ fontSize: 15, color: 'var(--text)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {issue.type}
            </span>
            {flying && <FlyIcon />}
          </div>
          <span className="mono uc" style={{
            fontSize: 10, fontWeight: 800, letterSpacing: 0.12,
            padding: '3px 6px', background: u.color, color: '#fff', flexShrink: 0,
          }}>{u.label}</span>
        </div>

        <div style={{ marginTop: 8, fontSize: 13, color: 'var(--text-2)', lineHeight: 1.5, textWrap: 'pretty' }}>
          {issue.summary}
        </div>

        <div style={{ marginTop: 10, display: 'flex', gap: 5, flexWrap: 'wrap', alignItems: 'center' }}>
          <span className="mono uc" style={{ fontSize: 10, color: 'var(--text-2)', letterSpacing: 0.1, fontWeight: 700, marginRight: 2 }}>FIDS</span>
          {(issue.affected_fids || []).map(fid => (
            <span key={fid} className="mono" style={{
              fontSize: 11, fontWeight: 700, padding: '2px 6px',
              border: '1px solid var(--border-2)', background: 'var(--brand-tint)', color: 'var(--brand)', letterSpacing: 0.04,
            }}>R{String(fid).padStart(2,'0')}</span>
          ))}
        </div>

        <div style={{ marginTop: 10, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ display: 'inline-flex', alignItems: 'baseline', gap: 4 }}>
              <span className="h-cond-x" style={{ fontSize: 19, color: 'var(--text)' }}>{issue.occurrence_count}</span>
              <span className="mono uc" style={{ fontSize: 10, color: 'var(--text-2)', fontWeight: 700 }}>ocor</span>
            </span>
            <span style={{ width: 1, height: 14, background: 'var(--border)' }} />
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
              <span className="mono uc" style={{ fontSize: 10, color: 'var(--text-2)', fontWeight: 700 }}>Δ24H</span>
              <Delta value={issue.score_delta_24h} />
            </span>
          </div>
          <ActionPill status={issue.status} />
        </div>
      </div>

      <ExpandedBody issue={issue} detail={detail} report={report} expanded={expanded} />

      <button onClick={(e) => { e.stopPropagation(); onExpand(issue); }} className="mono uc" style={{
        width: '100%', background: 'transparent', border: 'none',
        borderTop: expanded ? '1px solid var(--border)' : 'none',
        padding: '8px 14px 12px 20px',
        display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: 6,
        fontSize: 11, fontWeight: 800, letterSpacing: 0.12,
        color: expanded ? 'var(--brand-2)' : 'var(--text-2)', cursor: 'pointer',
      }}>
        {expanded ? '▴ RECOLHER'
          : reportLoading  ? <><Spinner size={9} color="var(--brand-2)" /> CARREGANDO…</>
          : reportFailed   ? <span style={{ color: '#D0021B' }}>↻ TENTAR NOVAMENTE</span>
          : reportReady    ? '▾ VER ANÁLISE'
          : <><Mark kind="cloud" size={11} color="currentColor" /> CARREGAR RELATÓRIO</>}
      </button>
    </div>
  );
}

function ExpandedBody({ issue, detail, report, expanded }) {
  const status = report?.status;
  return (
    <div style={{ overflow: 'hidden', maxHeight: expanded ? 600 : 0, transition: 'max-height 300ms cubic-bezier(0.4,0,0.2,1)' }}>
      <div style={{ padding: '6px 14px 6px 20px', display: 'flex', flexDirection: 'column', gap: 12 }}>
        {status === 'loading' && <ExpandedSkeleton />}
        {status === 'error' && (
          <div style={{ padding: '10px 12px', background: '#FDECEE', border: '1px solid #F2B5BC', display: 'flex', gap: 10, alignItems: 'flex-start' }}>
            <span style={{ width: 6, height: 6, background: '#D0021B', marginTop: 6 }} />
            <div style={{ fontSize: 13, color: '#7A0411', lineHeight: 1.45 }}>
              <div className="mono uc" style={{ fontSize: 10.5, fontWeight: 800, marginBottom: 2 }}>ERRO AO CARREGAR</div>
              Não foi possível obter o relatório do polígono. Verifique a conexão e tente novamente.
            </div>
          </div>
        )}
        {status === 'ready' && detail && (
          <>
            <div>
              <div className="mono uc" style={{ fontSize: 10.5, color: 'var(--brand)', fontWeight: 800, letterSpacing: 0.12, marginBottom: 6 }}>Análise Operacional</div>
              <div style={{ fontSize: 13, color: 'var(--text)', lineHeight: 1.6, textWrap: 'pretty' }}>{detail.detail}</div>
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                <div className="mono uc" style={{ fontSize: 10.5, color: 'var(--brand)', fontWeight: 800, letterSpacing: 0.12 }}>Distribuição · 24h</div>
                <SimuladoBadge />
              </div>
              <HourlyBars seed={issue.rank * 7 + 13} accent={CIVITAS.URGENCY[issue.urgency].color} />
            </div>
            {detail.affected_subareas?.length > 0 && (
              <div>
                <div className="mono uc" style={{ fontSize: 10.5, color: 'var(--brand)', fontWeight: 800, letterSpacing: 0.12, marginBottom: 6 }}>Subáreas afetadas</div>
                <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
                  {detail.affected_subareas.map(s => (
                    <span key={s} className="mono" style={{ fontSize: 11.5, padding: '3px 7px', border: '1px solid var(--border)', background: 'var(--bg-2)', color: 'var(--text-2)', fontWeight: 600 }}>{s}</span>
                  ))}
                </div>
              </div>
            )}
            {detail.fatores_acionados?.length > 0 && (
              <div>
                <div className="mono uc" style={{ fontSize: 10.5, color: 'var(--brand)', fontWeight: 800, letterSpacing: 0.12, marginBottom: 6 }}>Fatores acionados</div>
                <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
                  {detail.fatores_acionados.map(f => (
                    <span key={f} className="mono uc" style={{ fontSize: 11, fontWeight: 700, letterSpacing: 0.06, padding: '3px 7px', border: '1px solid #F5A62355', background: '#FFF4DC', color: '#8A5400' }}>{f.replace(/_/g, ' ')}</span>
                  ))}
                </div>
              </div>
            )}
            {detail.action_plan?.length > 0 && (
              <div style={{ padding: '10px 12px', background: 'var(--brand)', color: '#fff' }}>
                <div className="mono uc" style={{ fontSize: 10.5, color: '#BFD4EA', fontWeight: 800, letterSpacing: 0.12, marginBottom: 8 }}>Plano de ação</div>
                <ul style={{ margin: 0, paddingLeft: 18, fontSize: 13, lineHeight: 1.6 }}>
                  {detail.action_plan.map((a, i) => <li key={i}>{a}</li>)}
                </ul>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function ExpandedSkeleton() {
  return (
    <>
      <div>
        <Shimmer width={120} height={9} style={{ marginBottom: 6 }} />
        <Shimmer width="100%" height={10} style={{ marginBottom: 4 }} />
        <Shimmer width="92%"  height={10} style={{ marginBottom: 4 }} />
        <Shimmer width="78%"  height={10} />
      </div>
      <div>
        <Shimmer width={100} height={9} style={{ marginBottom: 8 }} />
        <Shimmer width="100%" height={36} />
      </div>
      <div>
        <Shimmer width={140} height={9} style={{ marginBottom: 6 }} />
        <div style={{ display: 'flex', gap: 5 }}>
          <Shimmer width={62} height={16} />
          <Shimmer width={86} height={16} />
          <Shimmer width={48} height={16} />
        </div>
      </div>
      <Shimmer width="100%" height={64} />
    </>
  );
}

function HourlyBars({ seed, accent }) {
  const data = _SB.useMemo(() => {
    const out = [];
    let s = seed;
    for (let h = 0; h < 24; h++) {
      s = (s * 9301 + 49297) % 233280;
      const peak = Math.min(Math.abs(20 - h), 24 - Math.abs(20 - h));
      const inf  = Math.max(0, 1 - peak / 5);
      out.push(Math.max(2, Math.round(10 + inf * 78 + (s / 233280 - 0.5) * 18)));
    }
    return out;
  }, [seed]);
  const max = Math.max(...data);
  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'flex-end', gap: 1, height: 36 }}>
        {data.map((v, i) => (
          <div key={i} style={{ flex: 1, background: accent, opacity: 0.25 + (v / max) * 0.75, height: `${(v / max) * 100}%`, minHeight: 2 }} />
        ))}
      </div>
      <div className="mono" style={{ display: 'flex', justifyContent: 'space-between', fontSize: 8.5, color: 'var(--text-2)', marginTop: 3, fontWeight: 600 }}>
        <span>00h</span><span>06h</span><span>12h</span><span>18h</span><span>24h</span>
      </div>
    </div>
  );
}

function FlyIcon() {
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 16, height: 16, color: 'var(--brand)', animation: 'fly-pulse 1s ease-in-out', flexShrink: 0 }}>
      <svg width="14" height="14" viewBox="0 0 16 16">
        <circle cx="8" cy="8" r="6" fill="none" stroke="currentColor" strokeWidth="1.2" />
        <line x1="8" y1="2" x2="8" y2="14" stroke="currentColor" strokeWidth="1.2" />
        <line x1="2" y1="8" x2="14" y2="8" stroke="currentColor" strokeWidth="1.2" />
        <circle cx="8" cy="8" r="1.5" fill="currentColor" />
      </svg>
    </span>
  );
}

function ActionPill({ status }) {
  const s = CIVITAS.STATUS[status];
  if (!s) return null;
  return (
    <button onClick={(e) => e.stopPropagation()} className="mono uc" style={{
      fontSize: 10.5, fontWeight: 800, letterSpacing: 0.1, padding: '4px 8px',
      background: s.bg, color: s.color, border: `1px solid ${s.border}`,
      display: 'inline-flex', alignItems: 'center', gap: 5, cursor: 'pointer',
    }}>
      <span style={{
        width: 6, height: 6, background: s.color,
        borderRadius: status === 'EM_ATENDIMENTO' ? '50%' : 0,
        animation: status === 'PENDENTE' ? 'pulse 1.6s ease-in-out infinite' : 'none',
      }} />
      {s.label}
    </button>
  );
}

function FootStat({ label, value, delta, tone }) {
  return (
    <div style={{ padding: '11px 12px', borderRight: '1px solid var(--border)', display: 'flex', flexDirection: 'column', gap: 3 }}>
      <span className="mono uc" style={{ fontSize: 10, color: 'var(--text-2)', fontWeight: 700 }}>{label}</span>
      <span className="h-cond-x" style={{ fontSize: 20, color: tone || 'var(--text)' }}>{value}</span>
      <span className="mono" style={{ fontSize: 10, color: 'var(--text-2)' }}>{delta}</span>
    </div>
  );
}

Object.assign(window, { Sidebar, AssistentePanel });
