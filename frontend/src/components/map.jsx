/* Interactive map — H3 hex choropleth + occurrence markers.
   Supports zoom/pan, fly-to, and shows skeleton + loading overlay while data loads. */

const _M = React;

const MAP_W = 920;
const MAP_H = 560;
const MIN_SCALE = 1;
const MAX_SCALE = 7;

function MapPanel({
  areasByFid, loading,
  selectedFid, onSelectHex, onDeselect,
  hoverFid, onHover,
  showOccurrences, showHexes,
  flyToToken,
}) {
  const hexes = _M.useMemo(
    () => CIVITAS.buildHexGrid(MAP_W, MAP_H, areasByFid),
    [areasByFid]
  );
  const occ = _M.useMemo(
    () => CIVITAS.buildOccurrences(Object.values(areasByFid)),
    [areasByFid]
  );

  const svgRef = _M.useRef(null);
  const dragRef = _M.useRef(null);
  const didDragRef = _M.useRef(false);

  const [pulse, setPulse] = _M.useState(0);
  _M.useEffect(() => {
    let raf, t0 = performance.now();
    const tick = () => {
      setPulse((performance.now() - t0) / 1000);
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, []);

  const [tx, setTx] = _M.useState(0);
  const [ty, setTy] = _M.useState(0);
  const [scale, setScale] = _M.useState(1);
  const [animating, setAnimating] = _M.useState(false);

  _M.useEffect(() => {
    if (flyToToken && selectedFid && CIVITAS.AREA_PIXELS[selectedFid]) {
      const [cx, cy] = CIVITAS.AREA_PIXELS[selectedFid];
      const targetScale = 2.6;
      const targetTx = MAP_W / 2 - targetScale * cx;
      const targetTy = MAP_H / 2 - targetScale * cy;
      setAnimating(true);
      setScale(targetScale);
      setTx(targetTx);
      setTy(targetTy);
      const t = setTimeout(() => setAnimating(false), 460);
      return () => clearTimeout(t);
    }
  }, [flyToToken]);

  const screenToSvg = (e) => {
    const svg = svgRef.current; if (!svg) return [0, 0];
    const rect = svg.getBoundingClientRect();
    return [((e.clientX - rect.left) / rect.width) * MAP_W,
            ((e.clientY - rect.top) / rect.height) * MAP_H];
  };

  const onWheel = (e) => {
    if (loading) return;
    e.preventDefault();
    const [sx, sy] = screenToSvg(e);
    const dir = e.deltaY > 0 ? -1 : 1;
    const newScale = Math.max(MIN_SCALE, Math.min(MAX_SCALE, scale * (1 + dir * 0.12)));
    if (newScale === scale) return;
    const wx = (sx - tx) / scale, wy = (sy - ty) / scale;
    setAnimating(false);
    setScale(newScale);
    setTx(clampTx(sx - newScale * wx, newScale));
    setTy(clampTy(sy - newScale * wy, newScale));
  };

  const zoomBy = (factor) => {
    const newScale = Math.max(MIN_SCALE, Math.min(MAX_SCALE, scale * factor));
    if (newScale === scale) return;
    const cx = MAP_W / 2, cy = MAP_H / 2;
    const wx = (cx - tx) / scale, wy = (cy - ty) / scale;
    setAnimating(true);
    setScale(newScale);
    setTx(clampTx(cx - newScale * wx, newScale));
    setTy(clampTy(cy - newScale * wy, newScale));
    setTimeout(() => setAnimating(false), 260);
  };

  const resetView = () => {
    setAnimating(true);
    setScale(1); setTx(0); setTy(0);
    setTimeout(() => setAnimating(false), 360);
  };

  const onPointerDown = (e) => {
    if (loading || e.button !== 0) return;
    dragRef.current = { startX: e.clientX, startY: e.clientY, startTx: tx, startTy: ty, moved: false };
    e.currentTarget.setPointerCapture?.(e.pointerId);
    setAnimating(false);
    didDragRef.current = false;
  };
  const onPointerMove = (e) => {
    const d = dragRef.current; if (!d) return;
    const dx = e.clientX - d.startX, dy = e.clientY - d.startY;
    if (Math.abs(dx) + Math.abs(dy) < 3 && !d.moved) return;
    d.moved = true; didDragRef.current = true;
    const rect = svgRef.current.getBoundingClientRect();
    setTx(clampTx(d.startTx + (dx / rect.width) * MAP_W, scale));
    setTy(clampTy(d.startTy + (dy / rect.height) * MAP_H, scale));
  };
  const onPointerUp = () => {
    const d = dragRef.current;
    dragRef.current = null;
    if (d?.moved) queueMicrotask(() => { didDragRef.current = false; });
    else didDragRef.current = false;
  };

  const onHexClick = (fid) => {
    if (didDragRef.current || loading) return;
    if (fid === selectedFid) onDeselect();
    else onSelectHex(fid);
  };
  const onBgClick = () => {
    if (didDragRef.current || loading) return;
    if (selectedFid) onDeselect();
  };

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', overflow: 'hidden', background: '#EFF4FA' }}
         onWheel={onWheel}>
      <svg ref={svgRef} width="100%" height="100%" viewBox={`0 0 ${MAP_W} ${MAP_H}`} preserveAspectRatio="xMidYMid slice"
           style={{ position: 'absolute', inset: 0, display: 'block', cursor: loading ? 'progress' : 'grab', touchAction: 'none' }}
           onPointerDown={onPointerDown} onPointerMove={onPointerMove}
           onPointerUp={onPointerUp} onPointerCancel={onPointerUp}>
        <defs>
          <pattern id="grid" width={40} height={40} patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#D6E0EC" strokeWidth={0.6} />
          </pattern>
          <pattern id="grid-fine" width={10} height={10} patternUnits="userSpaceOnUse">
            <path d="M 10 0 L 0 0 0 10" fill="none" stroke="#E5ECF4" strokeWidth={0.4} />
          </pattern>
          <radialGradient id="bay" cx="0.86" cy="0.18" r="0.18">
            <stop offset="0%"  stopColor="#D7E5F2" />
            <stop offset="100%" stopColor="#EFF4FA" />
          </radialGradient>
          <radialGradient id="ocean" cx="0.65" cy="0.95" r="0.5">
            <stop offset="0%"  stopColor="#DCE7F2" />
            <stop offset="100%" stopColor="#EFF4FA" />
          </radialGradient>
          <filter id="hexGlow">
            <feGaussianBlur stdDeviation="2" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>

        <g transform={`translate(${tx.toFixed(2)} ${ty.toFixed(2)}) scale(${scale.toFixed(3)})`}
           style={{ transition: animating ? 'transform 400ms cubic-bezier(0.4, 0, 0.2, 1)' : 'none' }}>

          <rect width={MAP_W} height={MAP_H} fill="url(#ocean)" onClick={onBgClick} />
          <rect width={MAP_W} height={MAP_H} fill="url(#bay)"   onClick={onBgClick} pointerEvents="none" />
          <rect width={MAP_W} height={MAP_H} fill="url(#grid-fine)" onClick={onBgClick} pointerEvents="none" />
          <rect width={MAP_W} height={MAP_H} fill="url(#grid)" onClick={onBgClick} pointerEvents="none" />

          {Array.from({length: Math.floor(MAP_W/80)}).map((_,i) => (
            <text key={`gx${i}`} x={i*80+4} y={12} fontFamily="JetBrains Mono" fontSize={9} fill="#B6C5D9" pointerEvents="none">
              {`-22.${(8 + i*2).toString().padStart(2,'0')}`}
            </text>
          ))}
          {Array.from({length: Math.floor(MAP_H/80)}).map((_,i) => (
            <text key={`gy${i}`} x={4} y={i*80+24} fontFamily="JetBrains Mono" fontSize={9} fill="#B6C5D9" pointerEvents="none">
              {`-43.${(20 + i*3).toString().padStart(2,'0')}`}
            </text>
          ))}

          {/* hexagons */}
          {showHexes && hexes.map(h => {
            if (loading) {
              return (
                <path key={h.id}
                  d={CIVITAS.hexPath(h.x, h.y, CIVITAS.HEX_SIZE - 1)}
                  fill="#FFFFFF" fillOpacity={0.35}
                  stroke="#BFD0E3" strokeOpacity={0.55} strokeWidth={0.6} />
              );
            }
            const c = CIVITAS.riskColor(h.score);
            const isSelected = h.fid === selectedFid;
            const isHovered = h.fid === hoverFid;
            const dimmed = selectedFid && !isSelected;
            const opacity = h.score < 18 ? 0
                          : isSelected ? 0.85
                          : isHovered  ? 0.55
                          : dimmed     ? 0.18
                          : 0.45;
            return (
              <path key={h.id}
                d={CIVITAS.hexPath(h.x, h.y, CIVITAS.HEX_SIZE - 1)}
                fill={c} fillOpacity={opacity}
                stroke={c}
                strokeOpacity={isSelected ? 1 : dimmed ? 0.25 : 0.6}
                strokeWidth={isSelected ? 1.2 : 0.7}
                style={{ cursor: 'pointer', transition: 'fill-opacity 220ms, stroke-opacity 220ms' }}
                onMouseEnter={() => onHover(h.fid)}
                onMouseLeave={() => onHover(null)}
                onClick={(e) => { e.stopPropagation(); onHexClick(h.fid); }}
              />
            );
          })}

          {/* coastline */}
          <path d={`M ${MAP_W} 0 L ${MAP_W} 120 Q ${MAP_W-80} 140 ${MAP_W-40} 200 Q ${MAP_W-20} 260 ${MAP_W} 320 L ${MAP_W} 0 Z`}
                fill="#EFF4FA" stroke="#BFD0E3" strokeWidth={0.8} pointerEvents="none" />
          <path d={`M 0 ${MAP_H} L 60 ${MAP_H-30} Q 200 ${MAP_H-10} 360 ${MAP_H-5} Q 540 ${MAP_H} 720 ${MAP_H-20} L ${MAP_W} ${MAP_H-40} L ${MAP_W} ${MAP_H} Z`}
                fill="#EFF4FA" stroke="#BFD0E3" strokeWidth={0.8} pointerEvents="none" />

          {/* occurrences */}
          {!loading && showOccurrences && occ.map((o, i) => {
            const dimmed = selectedFid && o.fid !== selectedFid;
            return (
              <g key={i} style={{ pointerEvents: 'none', opacity: dimmed ? 0.2 : 1, transition: 'opacity 220ms' }}>
                {o.kind === 'priority' ? (
                  <g>
                    <circle cx={o.x} cy={o.y} r={3.5} fill="#D0021B" />
                    <circle cx={o.x} cy={o.y} r={6}   fill="none" stroke="#D0021B" strokeOpacity={0.5} />
                  </g>
                ) : (
                  <rect x={o.x-1.2} y={o.y-1.2} width={2.4} height={2.4} fill="#0E1A2E" fillOpacity={0.7} />
                )}
              </g>
            );
          })}

          {/* selected hex outline glow */}
          {!loading && selectedFid && hexes.filter(h => h.fid === selectedFid && h.score >= 18).map(h => (
            <path key={`sel-${h.id}`}
                  d={CIVITAS.hexPath(h.x, h.y, CIVITAS.HEX_SIZE - 1)}
                  fill="none" stroke="#FFFFFF" strokeWidth={2 / scale}
                  filter="url(#hexGlow)" pointerEvents="none" />
          ))}

          {/* polygon labels */}
          {!loading && Object.values(areasByFid).map(a => {
            const px = CIVITAS.AREA_PIXELS[a.fid]; if (!px) return null;
            const [x, y] = px;
            const selected = a.fid === selectedFid;
            const hovered = a.fid === hoverFid;
            if (!selected && !hovered && a.rank > 8 && !selectedFid) return null;
            if (selectedFid && !selected) return null;
            return (
              <g key={a.fid} style={{ pointerEvents: 'none' }}>
                <line x1={x} y1={y} x2={x} y2={y - 18}
                      stroke={selected ? '#004A8F' : '#8FA3BE'}
                      strokeWidth={(selected ? 1.4 : 0.8) / scale} />
                <rect x={x - 32} y={y - 32} width={64} height={14}
                      fill={selected ? '#004A8F' : '#FFFFFF'}
                      stroke={selected ? '#004A8F' : '#BFD0E3'}
                      strokeWidth={(selected ? 1.2 : 0.8) / scale} />
                <text x={x} y={y - 22} fontFamily="JetBrains Mono" fontSize={9.5}
                      fill={selected ? '#FFFFFF' : '#0E1A2E'} textAnchor="middle"
                      letterSpacing={0.8} fontWeight={selected ? 700 : 600}>
                  {`${a.polyId} · ${a.zoneCode}`}
                </text>
              </g>
            );
          })}

          {/* crosshair */}
          {!loading && selectedFid && CIVITAS.AREA_PIXELS[selectedFid] && (() => {
            const [x, y] = CIVITAS.AREA_PIXELS[selectedFid];
            const r0 = (24 + Math.sin(pulse * 2) * 4) / Math.sqrt(scale);
            const sw = 1 / scale;
            return (
              <g style={{ pointerEvents: 'none' }}>
                <circle cx={x} cy={y} r={r0} fill="none" stroke="#004A8F" strokeOpacity={0.6} strokeWidth={1.2 * sw} />
                <circle cx={x} cy={y} r={r0 + 14 / scale} fill="none" stroke="#004A8F" strokeOpacity={0.22} strokeWidth={sw} />
                <line x1={x - 80/scale} y1={y} x2={x - 28/scale} y2={y} stroke="#004A8F" strokeWidth={sw} strokeDasharray={`${2*sw} ${3*sw}`} />
                <line x1={x + 28/scale} y1={y} x2={x + 80/scale} y2={y} stroke="#004A8F" strokeWidth={sw} strokeDasharray={`${2*sw} ${3*sw}`} />
                <line x1={x} y1={y - 80/scale} x2={x} y2={y - 28/scale} stroke="#004A8F" strokeWidth={sw} strokeDasharray={`${2*sw} ${3*sw}`} />
                <line x1={x} y1={y + 28/scale} x2={x} y2={y + 80/scale} stroke="#004A8F" strokeWidth={sw} strokeDasharray={`${2*sw} ${3*sw}`} />
              </g>
            );
          })()}
        </g>

        <g transform={`translate(${MAP_W - 50}, ${MAP_H - 80})`}>
          <rect x={-18} y={-20} width={36} height={56} fill="#FFFFFF" stroke="#BFD0E3" />
          <polygon points="0,-14 6,4 0,0 -6,4" fill="#0E1A2E" />
          <text x={0} y={22} fontFamily="JetBrains Mono" fontSize={10} fill="#0E1A2E" textAnchor="middle" fontWeight="700">N</text>
          <text x={0} y={32} fontFamily="JetBrains Mono" fontSize={7} fill="#8FA3BE" textAnchor="middle">WGS84</text>
        </g>
      </svg>

      <MapLegend selectedArea={selectedFid ? areasByFid[selectedFid] : null} loading={loading} />
      <MapControls onZoomIn={() => zoomBy(1.35)} onZoomOut={() => zoomBy(1/1.35)} onReset={resetView} scale={scale} disabled={loading} />
      <MapMeta scale={scale} loading={loading} />
      {loading && <LoadingOverlay />}
    </div>
  );
}

function clampTx(t, scale) { const min = MAP_W - MAP_W * scale; return Math.max(min, Math.min(0, t)); }
function clampTy(t, scale) { const min = MAP_H - MAP_H * scale; return Math.max(min, Math.min(0, t)); }

function LoadingOverlay() {
  return (
    <div style={{
      position: 'absolute', inset: 0,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      pointerEvents: 'none',
    }}>
      <div style={{
        padding: '14px 22px', background: '#FFFFFF',
        border: '1px solid #BFD0E3',
        boxShadow: '0 4px 12px rgba(0,30,80,0.10)',
        display: 'flex', alignItems: 'center', gap: 12,
      }}>
        <Spinner size={16} color="#004A8F" />
        <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <span className="h-cond-x" style={{ fontSize: 13, color: '#0E1A2E', letterSpacing: 0.06 }}>
            CARREGANDO DADOS...
          </span>
          <span className="mono" style={{ fontSize: 9.5, color: '#44597A', letterSpacing: 0.04, fontWeight: 600 }}>
            Sincronizando ciclo · SISP/RJ
          </span>
        </div>
      </div>
    </div>
  );
}

function MapLegend({ selectedArea, loading }) {
  const steps = [
    { c: '#007A4D', label: '0–19' },
    { c: '#3FA46A', label: '20–39' },
    { c: '#F5A623', label: '40–59' },
    { c: '#E2562A', label: '60–74' },
    { c: '#D0021B', label: '75+' },
  ];
  return (
    <div style={{
      position: 'absolute', left: 14, top: 14,
      background: '#FFFFFF', border: '1px solid #BFD0E3',
      minWidth: 240, boxShadow: '0 1px 3px rgba(0,30,80,0.06)',
    }}>
      <div style={{ padding: '10px 12px' }}>
        <div className="mono uc" style={{ fontSize: 9, color: '#004A8F', marginBottom: 6, letterSpacing: 0.14, fontWeight: 800 }}>
          Choropleth · Índice de risco
        </div>
        <div style={{ display: 'flex', gap: 2, marginBottom: 6 }}>
          {steps.map(s => <div key={s.c} style={{ flex: 1, height: 10, background: loading ? '#D6E0EC' : s.c }} />)}
        </div>
        <div className="mono" style={{ display: 'flex', justifyContent: 'space-between', fontSize: 9, color: '#44597A', fontWeight: 600 }}>
          {steps.map(s => <span key={s.c} style={{ flex: 1, textAlign: 'left' }}>{s.label}</span>)}
        </div>
        <div style={{ height: 1, background: '#D6E0EC', margin: '10px 0' }} />
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, fontSize: 10, color: '#44597A' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <span style={{ width: 7, height: 7, background: '#D0021B', borderRadius: '50%' }} />
            <span className="mono" style={{ fontWeight: 600 }}>Prioridade</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <span style={{ width: 5, height: 5, background: '#0E1A2E' }} />
            <span className="mono" style={{ fontWeight: 600 }}>Ocorrência</span>
          </div>
        </div>
      </div>
      <div style={{
        borderTop: '1px solid #D6E0EC',
        padding: '8px 12px',
        background: selectedArea ? '#E8F1FB' : 'transparent',
        display: 'flex', alignItems: 'center', gap: 8,
      }}>
        {selectedArea ? (
          <>
            <span style={{ width: 8, height: 8, background: '#004A8F' }} />
            <span className="mono uc" style={{ fontSize: 9.5, color: '#004A8F', fontWeight: 800, letterSpacing: 0.1 }}>
              SELECIONADO
            </span>
            <span style={{ color: '#8FA3BE' }}>·</span>
            <span className="mono" style={{ fontSize: 10.5, color: '#0E1A2E', fontWeight: 700 }}>
              {selectedArea.polyId}
            </span>
            <span className="mono" style={{ fontSize: 10, color: '#44597A' }}>
              ({selectedArea.nome_area})
            </span>
          </>
        ) : (
          <>
            <span style={{ width: 8, height: 8, border: '1px solid #BFD0E3' }} />
            <span className="mono uc" style={{ fontSize: 9.5, color: '#8FA3BE', fontWeight: 700, letterSpacing: 0.1 }}>
              — nenhuma seleção
            </span>
          </>
        )}
      </div>
    </div>
  );
}

function MapControls({ onZoomIn, onZoomOut, onReset, scale, disabled }) {
  return (
    <div style={{
      position: 'absolute', right: 14, top: 14,
      display: 'flex', flexDirection: 'column',
      border: '1px solid #BFD0E3', background: '#FFFFFF',
      boxShadow: '0 1px 3px rgba(0,30,80,0.06)',
      opacity: disabled ? 0.45 : 1, pointerEvents: disabled ? 'none' : 'auto',
    }}>
      <button onClick={onZoomIn}  title="Aproximar" style={ctrlBtn(false)}>+</button>
      <button onClick={onZoomOut} title="Afastar"   style={ctrlBtn(false)}>−</button>
      <button onClick={onReset}   title="Centro"    style={ctrlBtn(true)}>◎</button>
      <div className="mono" style={{
        padding: '4px 0', textAlign: 'center', fontSize: 8.5,
        color: '#44597A', fontWeight: 700, borderTop: '1px solid #D6E0EC',
      }}>{scale.toFixed(1)}×</div>
    </div>
  );
}
function ctrlBtn(last) {
  return {
    width: 32, height: 32, background: '#FFFFFF', color: '#004A8F',
    border: 'none', borderBottom: last ? 'none' : '1px solid #D6E0EC',
    fontFamily: 'JetBrains Mono', fontSize: 15, fontWeight: 700, cursor: 'pointer',
  };
}

function MapMeta({ scale, loading }) {
  return (
    <div style={{
      position: 'absolute', right: 14, bottom: 14,
      padding: '6px 10px',
      background: '#FFFFFF', border: '1px solid #BFD0E3',
      fontFamily: 'JetBrains Mono', fontSize: 9.5, color: '#44597A', fontWeight: 600,
      display: 'flex', gap: 12,
      boxShadow: '0 1px 3px rgba(0,30,80,0.06)',
    }}>
      <span>H3 r9</span>
      <span style={{ color: '#BFD0E3' }}>·</span>
      <span>EPSG:4326</span>
      <span style={{ color: '#BFD0E3' }}>·</span>
      <span>SISP/RJ</span>
      <span style={{ color: '#BFD0E3' }}>·</span>
      <span>{loading ? 'sync…' : `z ${scale.toFixed(1)}`}</span>
    </div>
  );
}

Object.assign(window, { MapPanel });
