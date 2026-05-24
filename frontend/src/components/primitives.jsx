/* Small primitives shared across the dashboard. */

const { useEffect, useRef, useState, useMemo } = React;

function RiskDot({ score, size = 8 }) {
  return <span className="risk-dot" style={{ width: size, height: size, background: CIVITAS.riskColor(score), borderRadius: 1 }} />;
}

function RiskBadge({ score, mini }) {
  const k = CIVITAS.riskKeyFromScore(score);
  const r = CIVITAS.RISK[k];
  return (
    <span className="mono uc" style={{
      fontSize: mini ? 9 : 10, fontWeight: 700,
      color: r.color, background: r.bg,
      border: `1px solid ${r.border}`,
      padding: mini ? '1px 4px' : '2px 6px',
      letterSpacing: 0.08, display: 'inline-flex', alignItems: 'center', gap: 4,
    }}>
      <span style={{ width: 5, height: 5, background: r.color, display: 'inline-block' }} />
      {r.label}
    </span>
  );
}

function ScoreBadge({ score, mini }) {
  const c = CIVITAS.riskColor(score);
  return (
    <span className="mono" style={{
      fontSize: mini ? 10 : 11, fontWeight: 700,
      color: c, background: '#FFFFFF',
      border: `1px solid ${c}55`,
      padding: mini ? '1px 5px' : '2px 6px',
      display: 'inline-flex', alignItems: 'center', gap: 4, lineHeight: 1,
    }}>
      <span style={{ display: 'inline-block', width: 4, height: 8, background: c }} />
      {String(score).padStart(2, '0')}
    </span>
  );
}

function Delta({ value, inverted }) {
  if (value === 0) return <span className="mono" style={{ color: 'var(--text-3)', fontSize: 10 }}>—</span>;
  const up = value > 0;
  const color = up ? '#D0021B' : '#007A4D';
  return (
    <span className="mono" style={{ color, fontSize: 11, fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: 3 }}>
      <span style={{ fontSize: 8 }}>{up ? '▲' : '▼'}</span>
      {Math.abs(value)}
    </span>
  );
}

function Sparkline({ data, color = '#0066CC', width = 110, height = 28, fill = true }) {
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const dx = width / (data.length - 1);
  const pts = data.map((v, i) => [i * dx, height - 2 - ((v - min) / range) * (height - 4)]);
  const path = 'M' + pts.map(p => p.map(n => n.toFixed(1)).join(',')).join(' L');
  const area = path + ` L${pts[pts.length-1][0].toFixed(1)},${height} L0,${height} Z`;
  return (
    <svg width={width} height={height} style={{ display: 'block' }}>
      {fill && <path d={area} fill={color} fillOpacity={0.15} />}
      <path d={path} fill="none" stroke={color} strokeWidth={1.4} strokeLinejoin="round" strokeLinecap="round" />
      <circle cx={pts[pts.length-1][0]} cy={pts[pts.length-1][1]} r={2.2} fill={color} />
    </svg>
  );
}

function Pill({ children, color = 'var(--text-2)', tone }) {
  const bg = tone ? `${tone}14` : 'transparent';
  const bd = tone ? `${tone}40` : 'var(--border)';
  return (
    <span className="mono" style={{
      fontSize: 10, color, padding: '2px 6px',
      border: `1px solid ${bd}`, background: bg,
      display: 'inline-flex', alignItems: 'center', gap: 4, lineHeight: 1.4,
      letterSpacing: 0.02,
    }}>{children}</span>
  );
}

/* Shimmer skeleton — used while data loads. */
function Shimmer({ width = '100%', height = 12, radius = 0, style = {}, dark = false }) {
  return (
    <div className="shimmer" style={{
      width, height, borderRadius: radius,
      background: dark ? '#23263C' : '#E2E9F2',
      position: 'relative', overflow: 'hidden',
      ...style,
    }} />
  );
}

/* Spinner (small, monochrome). */
function Spinner({ size = 14, color = '#004A8F', thickness = 2 }) {
  return (
    <span style={{
      width: size, height: size, display: 'inline-block',
      border: `${thickness}px solid ${color}33`,
      borderTopColor: color,
      borderRadius: '50%',
      animation: 'spin 0.8s linear infinite',
    }} />
  );
}

/* Tiny "SIMULADO" tag for non-backed fields. */
function SimuladoBadge() {
  return (
    <span className="mono uc" style={{
      fontSize: 8.5, fontWeight: 800, letterSpacing: 0.14,
      padding: '1px 5px', color: '#A66800', background: '#FFF4DC',
      border: '1px dashed #F5A623',
    }}>
      SIMULADO
    </span>
  );
}

/* Tiny mark icons. */
function Mark({ kind, size = 12, color = 'currentColor' }) {
  const s = size;
  if (kind === 'square')   return <span style={{ width: s, height: s, background: color, display: 'inline-block' }} />;
  if (kind === 'frame')    return <span style={{ width: s, height: s, border: `1.5px solid ${color}`, display: 'inline-block' }} />;
  if (kind === 'plus')     return <span style={{ width: s, height: s, display: 'inline-block', position: 'relative' }}>
    <span style={{ position: 'absolute', top: '50%', left: 0, right: 0, height: 1.5, background: color, transform: 'translateY(-50%)' }} />
    <span style={{ position: 'absolute', left: '50%', top: 0, bottom: 0, width: 1.5, background: color, transform: 'translateX(-50%)' }} />
  </span>;
  if (kind === 'chevron-r')return <span style={{ width: s, height: s, display: 'inline-block', position: 'relative' }}>
    <span style={{ position: 'absolute', top: '30%', left: '20%', width: '40%', height: '40%', borderRight: `1.5px solid ${color}`, borderTop: `1.5px solid ${color}`, transform: 'rotate(45deg)' }} />
  </span>;
  if (kind === 'cloud') return (
    <svg width={s} height={s} viewBox="0 0 16 16" style={{ display: 'inline-block' }}>
      <path d="M4 11 Q1 11 1 8 Q1 5.5 3.5 5.5 Q4 3 7 3 Q10 3 10.5 5.5 Q14 5.5 14 8.5 Q14 11 11 11 Z M7.5 7 V11 M5.5 9 L7.5 11 L9.5 9" stroke={color} strokeWidth="1.2" fill="none" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
  if (kind === 'dot')      return <span style={{ width: s, height: s, background: color, borderRadius: '50%', display: 'inline-block' }} />;
  return null;
}

Object.assign(window, { RiskDot, RiskBadge, ScoreBadge, Delta, Sparkline, Pill, Shimmer, Spinner, SimuladoBadge, Mark });
