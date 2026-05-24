#!/usr/bin/env python3
"""CIVITAS Backend — FastAPI Server"""

import sys
import os
import json
import base64
import io
import logging
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format="%(asctime)s [CIVITAS] %(message)s")
log = logging.getLogger("civitas")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# ─── App ────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="CIVITAS — Investigação de Segurança Pública",
    version="1.0.0",
    description="API de análise investigativa com busca semântica, "
                "redação de privacidade, grafos de movimento e relatórios.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Schemas ────────────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    query_text: str = Field("", description="Texto para busca semântica")
    query_image: Optional[str] = Field(None, description="Base64 da imagem para busca multimodal")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Filtros: bairro, tipo_crime, data_inicio, data_fim")
    top_k: int = Field(10, ge=1, le=100)

class SearchResult(BaseModel):
    id: int
    bairro: str
    tipo_crime: str
    data: str
    lat: float
    lon: float
    descricao: str
    similarity: float

class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int
    elapsed_ms: float

class AnalyzeResponse(BaseModel):
    success: bool
    analise: str
    redacted_image_length: int
    audit_log: List[str]
    elapsed_seconds: float
    error: Optional[str] = None

class GraphRequest(BaseModel):
    detections: List[Dict[str, Any]] = Field(..., description="Lista de detecções com camera_id, track_id, timestamp")

class GraphResponse(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    hotspots: List[Dict[str, Any]]
    likely_paths: List[List[str]]
    node_count: int
    edge_count: int

class ReportRequest(BaseModel):
    query: str = Field(..., description="Descrição do caso/consulta")
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    image_analysis: List[Dict[str, Any]] = Field(default_factory=list)
    graph_data: Dict[str, Any] = Field(default_factory=lambda: {"entidades": [], "relacoes": []})

class ReportResponse(BaseModel):
    success: bool
    relatorio: Dict[str, Any]
    generated_by: str
    elapsed_seconds: float

# ─── Module Imports ─────────────────────────────────────────────────────────

FAISS_MODULE = ROOT / "app" / "faiss"
OBLITERATUS_MODULE = ROOT / "app" / "obliteratus"
GRAPH_MODULE = ROOT / "app" / "graph"
REPORT_MODULE = ROOT / "app" / "report"

try:
    import numpy as np
    import json as _json
    log.info("✓ numpy loaded")
except ImportError:
    log.warning("✗ numpy not available")

# FAISS
faiss_index = None
synthetic_data = None
try:
    import faiss
    faiss_index_path = FAISS_MODULE / "civitas_hnsw.index"
    data_path = FAISS_MODULE / "synthetic_data.json"
    if faiss_index_path.exists():
        faiss_index = faiss.read_index(str(faiss_index_path))
        with open(data_path) as f:
            synthetic_data = json.load(f)
        log.info(f"✓ FAISS index loaded: {faiss_index.ntotal} vectors")
    else:
        log.warning("✗ FAISS index not found, run generate_data.py + test_index.py first")
except ImportError:
    log.warning("✗ faiss not installed")

# Obliteratus
obliteratus_fn = None
process_evidence_fn = None
try:
    from app.obliteratus.obliteratus import obliteratus as _oblit
    from app.obliteratus.pipeline import process_evidence as _pipeline
    obliteratus_fn = _oblit
    process_evidence_fn = _pipeline
    log.info("✓ Obliteratus module loaded")
except ImportError as e:
    log.warning(f"✗ Obliteratus not loaded: {e}")

# Graph
build_graph_fn = None
find_path_fn = None
get_hotspots_fn = None
graph_to_dict_fn = None
try:
    from app.graph.movement_graph import (
        build_movement_graph, find_most_likely_path,
        get_hotspots, graph_to_dict,
    )
    build_graph_fn = build_movement_graph
    find_path_fn = find_most_likely_path
    get_hotspots_fn = get_hotspots
    graph_to_dict_fn = graph_to_dict
    log.info("✓ Movement Graph module loaded")
except ImportError as e:
    log.warning(f"✗ Movement Graph not loaded: {e}")

# Report
report_generator_fn = None
try:
    from app.report.report_generator import generate_report
    report_generator_fn = generate_report
    log.info("✓ Report Generator module loaded")
except ImportError as e:
    log.warning(f"✗ Report Generator not loaded: {e}")

# Sentence Transformers for real embeddings
text_encoder = None
try:
    from sentence_transformers import SentenceTransformer
    text_encoder = SentenceTransformer("all-MiniLM-L6-v2")
    log.info("✓ SentenceTransformer loaded (all-MiniLM-L6-v2)")
except ImportError:
    log.warning("✗ sentence-transformers not installed, using mock embeddings")


# ─── Helper: Generate embedding from text ──────────────────────────────────

def _get_embedding(text: str, dim: int = 384) -> list:
    """Generate text embedding using sentence-transformers or mock."""
    if text_encoder is not None and text.strip():
        emb = text_encoder.encode(text)
        return emb.tolist()
    # Mock embedding for demo
    import random
    random.seed(hash(text) % (2**31))
    vec = [random.gauss(0, 0.1) for _ in range(dim)]
    norm = sum(x*x for x in vec) ** 0.5
    return [x/norm for x in vec]


# ─── Endpoints ──────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "service": "CIVITAS API",
        "version": "1.0.0",
        "status": "operational",
        "modules": {
            "faiss": faiss_index is not None,
            "obliteratus": obliteratus_fn is not None,
            "graph": build_graph_fn is not None,
            "report": report_generator_fn is not None,
            "embeddings": text_encoder is not None,
        },
        "endpoints": {
            "POST /api/search": "Busca semântica multimodal",
            "POST /api/analyze": "Upload + Análise de evidência visual",
            "POST /api/graph/build": "Construir grafo de movimento",
            "POST /api/report/generate": "Gerar relatório investigativo",
        },
    }


@app.post("/api/search", response_model=SearchResponse)
async def search(req: SearchRequest):
    """Busca semântica multimodal (texto + imagem + filtros)."""
    start = time.time()

    if faiss_index is None or synthetic_data is None:
        raise HTTPException(503, "FAISS index not loaded. Run research/faiss first.")

    # Generate query embedding
    query_text = req.query_text or ""
    query_embedding = _get_embedding(query_text)

    # If image provided, combine embeddings (future: multimodal)
    # For now, text-only with image feature as optional future extension

    query_vec = np.array([query_embedding], dtype=np.float32)

    # Apply metadata filters BEFORE search
    filtered_indices = list(range(len(synthetic_data)))
    if req.filters:
        bairro_filter = req.filters.get("bairro", "").lower()
        crime_filter = req.filters.get("tipo_crime", "").lower()
        data_inicio = req.filters.get("data_inicio", "")
        data_fim = req.filters.get("data_fim", "")

        filtered_indices = [
            i for i, rec in enumerate(synthetic_data)
            if (not bairro_filter or bairro_filter in rec["bairro"].lower())
            and (not crime_filter or crime_filter in rec["tipo_crime"].lower())
            and (not data_inicio or rec["data"] >= data_inicio)
            and (not data_fim or rec["data"] <= data_fim)
        ]

    if not filtered_indices:
        return SearchResponse(results=[], total=0, elapsed_ms=0)

    # Search FAISS
    distances, indices = faiss_index.search(query_vec, min(req.top_k, len(filtered_indices)))

    # Map back to filtered data
    results = []
    seen = set()
    for dist, idx in zip(distances[0], indices[0]):
        if idx in seen or idx >= len(synthetic_data):
            continue
        seen.add(idx)
        rec = synthetic_data[idx]
        results.append(SearchResult(
            id=rec["id"],
            bairro=rec["bairro"],
            tipo_crime=rec["tipo_crime"],
            data=rec["data"],
            lat=rec["lat"],
            lon=rec["lon"],
            descricao=rec["descricao"][:200],
            similarity=round(float(1.0 - dist), 4),
        ))

    elapsed_ms = round((time.time() - start) * 1000, 2)
    return SearchResponse(results=results, total=len(results), elapsed_ms=elapsed_ms)


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(
    image: UploadFile = File(...),
    metadata: Optional[str] = Form(None),
    query: Optional[str] = Form(None),
):
    """Upload de evidência visual + Obliteratus (blur facial) + análise."""
    start = time.time()

    if obliteratus_fn is None:
        raise HTTPException(503, "Obliteratus module not loaded.")

    # Save upload to temp file
    temp_dir = ROOT / "app" / "temp"
    temp_dir.mkdir(exist_ok=True)
    temp_path = temp_dir / f"upload_{int(time.time())}_{image.filename}"

    contents = await image.read()
    with open(temp_path, "wb") as f:
        f.write(contents)

    # Parse metadata
    meta = {}
    if metadata:
        try:
            meta = json.loads(metadata)
        except json.JSONDecodeError:
            meta = {"raw": metadata}

    # Process via Obliteratus pipeline
    if process_evidence_fn:
        result = process_evidence_fn(
            image_path=str(temp_path),
            metadata=meta,
            query=query or "Analise esta evidência visual.",
        )
    else:
        # Fallback: just run obliteratus without pipeline
        ob_result = obliteratus_fn(image_path=str(temp_path), metadata=meta)
        result = type('obj', (), {
            'success': True,
            'analise': f"Imagem redigida: {len(ob_result['audit_log'])} ações de auditoria.",
            'redacted_image_base64': ob_result['redacted_image'],
            'audit_log': ob_result['audit_log'],
            'elapsed_seconds': time.time() - start,
            'error': None,
        })()

    # Cleanup temp
    try:
        temp_path.unlink()
    except OSError:
        pass

    return AnalyzeResponse(
        success=getattr(result, 'success', True),
        analise=getattr(result, 'analise', "Análise concluída."),
        redacted_image_length=len(getattr(result, 'redacted_image_base64', '')),
        audit_log=[e.get("evento", str(e)) if isinstance(e, dict) else str(e)
                   for e in getattr(result, 'audit_log', [])],
        elapsed_seconds=round(getattr(result, 'elapsed_seconds', time.time() - start), 2),
        error=getattr(result, 'error', None),
    )


@app.post("/api/graph/build", response_model=GraphResponse)
async def build_graph(req: GraphRequest):
    """Construir grafo de movimento a partir de detecções."""
    if build_graph_fn is None:
        raise HTTPException(503, "Movement Graph module not loaded.")

    G = build_graph_fn(req.detections)
    graph_dict = graph_to_dict_fn(G)

    # Find hotspots
    hotspots = get_hotspots_fn(G, threshold=0.05)

    # Find likely paths between all pairs of top nodes
    likely_paths = []
    nodes = list(G.nodes())
    for i in range(min(len(nodes), 5)):
        for j in range(i + 1, min(len(nodes), 5)):
            path = find_path_fn(G, nodes[i], nodes[j])
            if path:
                likely_paths.append(path)

    # Convert crime_types sets to lists for serialization
    cleaned_nodes = []
    for n in graph_dict["nodes"]:
        n["crime_types"] = list(n.get("crime_types", [])) if not isinstance(n.get("crime_types"), list) else n["crime_types"]
        cleaned_nodes.append(n)

    return GraphResponse(
        nodes=cleaned_nodes,
        edges=graph_dict["edges"],
        hotspots=hotspots,
        likely_paths=likely_paths,
        node_count=G.number_of_nodes(),
        edge_count=G.number_of_edges(),
    )


@app.post("/api/report/generate", response_model=ReportResponse)
async def generate_report_endpoint(req: ReportRequest):
    """Gerar relatório investigativo completo."""
    if report_generator_fn is None:
        raise HTTPException(503, "Report Generator module not loaded.")

    start = time.time()

    relatorio = report_generator_fn(
        user_query=req.query,
        evidence=req.evidence,
        image_analysis=req.image_analysis,
        graph_data=req.graph_data,
        use_fallback=True,  # Always use fallback (template-based) for speed
    )

    return ReportResponse(
        success=True,
        relatorio=relatorio,
        generated_by="CIVITAS Report Generator (Fallback)",
        elapsed_seconds=round(time.time() - start, 2),
    )


# ─── Health check diagnostic endpoint ──────────────────────────────────────

@app.get("/api/diagnostics")
async def diagnostics():
    """Run diagnostics on all modules."""
    results = {}

    # FAISS
    if faiss_index is not None:
        results["faiss"] = {
            "status": "ok",
            "vectors": faiss_index.ntotal,
            "dimension": faiss_index.d,
        }
    else:
        results["faiss"] = {"status": "not_loaded"}

    # Obliteratus
    results["obliteratus"] = {
        "status": "ok" if obliteratus_fn is not None else "not_loaded",
        "pipeline": "ok" if process_evidence_fn is not None else "not_loaded",
    }

    # Graph
    results["graph"] = {
        "status": "ok" if build_graph_fn is not None else "not_loaded",
    }

    # Report
    results["report"] = {
        "status": "ok" if report_generator_fn is not None else "not_loaded",
    }

    # Embeddings
    results["embeddings"] = {
        "status": "ok" if text_encoder is not None else "mock",
        "model": "all-MiniLM-L6-v2" if text_encoder is not None else "mock-random",
    }

    # Data
    results["data"] = {
        "synthetic_records": len(synthetic_data) if synthetic_data else 0,
    }

    return results


# ─── Main ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    print("CIVITAS Backend starting on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
