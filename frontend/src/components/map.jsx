/* MapLibre GL JS map — real Rio GeoJSON polygons + occurrence circles. */

const _M = React;
const EMPTY_FC    = { type: 'FeatureCollection', features: [] };
const RIO_CENTER  = [-43.35, -22.92];
const RIO_ZOOM    = 10;

function MapPanel({
  areasByFid, loading,
  selectedFid, onSelectHex, onDeselect,
  hoverFid, onHover,
  showOccurrences, showHexes,
  flyToToken,
}) {
  const containerRef   = _M.useRef(null);
  const mapRef         = _M.useRef(null);
  const selectedFidRef = _M.useRef(selectedFid);
  const prevHoverRef   = _M.useRef(null);
  const [mapReady, setMapReady] = _M.useState(false);
  const [zoom, setZoom]         = _M.useState(RIO_ZOOM);

  // Keep ref current so map event handlers never close over a stale selectedFid
  _M.useEffect(() => { selectedFidRef.current = selectedFid; }, [selectedFid]);

  // Effect 1 — init map (runs once)
  _M.useEffect(() => {
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
      center: RIO_CENTER,
      zoom: RIO_ZOOM,
      minZoom: 9,
      maxZoom: 16,
      attributionControl: false,
    });

    map.on('load', () => {
      // ── Areas source + layers ──────────────────────────────────────────
      map.addSource('areas', { type: 'geojson', data: EMPTY_FC });

      map.addLayer({
        id: 'areas-fill', type: 'fill', source: 'areas',
        paint: {
          'fill-color': ['step', ['get', 'score'],
            '#007A4D', 20, '#3FA46A', 40, '#F5A623', 60, '#E2562A', 75, '#D0021B',
          ],
          'fill-opacity': 0.5,
        },
      });

      map.addLayer({
        id: 'areas-line', type: 'line', source: 'areas',
        paint: { 'line-color': '#BFD0E3', 'line-width': 1 },
      });

      // ── Occurrences source + layer ─────────────────────────────────────
      map.addSource('occurrences', { type: 'geojson', data: EMPTY_FC });
      map.addLayer({
        id: 'occ-circles', type: 'circle', source: 'occurrences',
        paint: {
          'circle-radius': ['interpolate', ['linear'], ['get', 'count'], 0, 5, 1000, 16],
          'circle-color': '#D0021B',
          'circle-opacity': 0.75,
          'circle-stroke-width': 1.5,
          'circle-stroke-color': '#fff',
        },
      });

      // ── Interaction ────────────────────────────────────────────────────
      map.on('click', 'areas-fill', e => {
        const fid = e.features[0]?.properties?.fid;
        if (fid == null) return;
        const numFid = Number(fid);
        if (numFid === selectedFidRef.current) onDeselect();
        else onSelectHex(numFid);
      });

      map.on('click', e => {
        if (!map.queryRenderedFeatures(e.point, { layers: ['areas-fill'] }).length)
          onDeselect();
      });

      map.on('mouseenter', 'areas-fill', e => {
        map.getCanvas().style.cursor = 'pointer';
        const fid = e.features[0]?.properties?.fid;
        onHover(fid != null ? Number(fid) : null);
      });
      map.on('mouseleave', 'areas-fill', () => {
        map.getCanvas().style.cursor = '';
        onHover(null);
      });

      map.on('zoom', () => setZoom(+map.getZoom().toFixed(1)));

      mapRef.current = map;
      setMapReady(true);
    });

    mapRef.current = map;
    return () => {
      setMapReady(false);
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Effect 2 — sync GeoJSON data to map sources
  _M.useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady) return;
    map.getSource('areas')?.setData(CIVITAS.buildAreasGeoJSON(areasByFid));
    map.setLayoutProperty('areas-fill', 'visibility', showHexes ? 'visible' : 'none');
    map.setLayoutProperty('areas-line', 'visibility', showHexes ? 'visible' : 'none');
    map.getSource('occurrences')?.setData(
      CIVITAS.buildOccurrencesGeoJSON(areasByFid, showOccurrences)
    );
  }, [areasByFid, showHexes, showOccurrences, mapReady]);

  // Effect 3 — selection highlight via paint expressions
  _M.useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady) return;
    if (selectedFid != null) {
      map.setPaintProperty('areas-fill', 'fill-opacity', [
        'case',
        ['==', ['get', 'fid'], selectedFid], 0.85,
        ['boolean', ['feature-state', 'hover'], false], 0.55,
        0.15,
      ]);
      map.setPaintProperty('areas-line', 'line-color', [
        'case', ['==', ['get', 'fid'], selectedFid], '#004A8F', '#BFD0E3',
      ]);
      map.setPaintProperty('areas-line', 'line-width', [
        'case', ['==', ['get', 'fid'], selectedFid], 2.5, 1,
      ]);
    } else {
      map.setPaintProperty('areas-fill', 'fill-opacity', [
        'case', ['boolean', ['feature-state', 'hover'], false], 0.65, 0.5,
      ]);
      map.setPaintProperty('areas-line', 'line-color', '#BFD0E3');
      map.setPaintProperty('areas-line', 'line-width', 1);
    }
  }, [selectedFid, mapReady]);

  // Effect 4 — hover feature-state (clears prev, sets new)
  _M.useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady) return;
    if (prevHoverRef.current != null)
      map.setFeatureState({ source: 'areas', id: prevHoverRef.current }, { hover: false });
    if (hoverFid != null)
      map.setFeatureState({ source: 'areas', id: hoverFid }, { hover: true });
    prevHoverRef.current = hoverFid;
  }, [hoverFid, mapReady]);

  // Effect 5 — fly to selected area centroid
  _M.useEffect(() => {
    if (!flyToToken || !selectedFid) return;
    const map = mapRef.current;
    const area = areasByFid[selectedFid];
    if (!map || !area) return;
    map.flyTo({
      center: [area.centroide.lon, area.centroide.lat],
      zoom: 13, duration: 800, essential: true,
    });
  }, [flyToToken]);

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <div ref={containerRef} style={{ width: '100%', height: '100%' }} />
      <MapLegend selectedArea={selectedFid ? areasByFid[selectedFid] : null} loading={loading} />
      <MapControls
        onZoomIn={()  => mapRef.current?.zoomIn()}
        onZoomOut={() => mapRef.current?.zoomOut()}
        onReset={()   => mapRef.current?.flyTo({ center: RIO_CENTER, zoom: RIO_ZOOM, duration: 600 })}
        scale={zoom}
        disabled={loading}
      />
      <MapMeta scale={zoom} loading={loading} />
      {loading && <LoadingOverlay />}
    </div>
  );
}

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
      pointerEvents: 'none',
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
        <div style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 10, color: '#44597A' }}>
          <span style={{ width: 7, height: 7, background: '#D0021B', borderRadius: '50%' }} />
          <span className="mono" style={{ fontWeight: 600 }}>Ocorrências (por bairro)</span>
        </div>
      </div>
      <div style={{
        borderTop: '1px solid #D6E0EC', padding: '8px 12px',
        background: selectedArea ? '#E8F1FB' : 'transparent',
        display: 'flex', alignItems: 'center', gap: 8,
      }}>
        {selectedArea ? (
          <>
            <span style={{ width: 8, height: 8, background: '#004A8F' }} />
            <span className="mono uc" style={{ fontSize: 9.5, color: '#004A8F', fontWeight: 800, letterSpacing: 0.1 }}>SELECIONADO</span>
            <span style={{ color: '#8FA3BE' }}>·</span>
            <span className="mono" style={{ fontSize: 10.5, color: '#0E1A2E', fontWeight: 700 }}>{selectedArea.polyId}</span>
            <span className="mono" style={{ fontSize: 10, color: '#44597A' }}>({selectedArea.nome_area})</span>
          </>
        ) : (
          <>
            <span style={{ width: 8, height: 8, border: '1px solid #BFD0E3' }} />
            <span className="mono uc" style={{ fontSize: 9.5, color: '#8FA3BE', fontWeight: 700, letterSpacing: 0.1 }}>— nenhuma seleção</span>
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
      pointerEvents: 'none',
    }}>
      <span>MapLibre GL</span>
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
