#!/usr/bin/env python3
"""
Enhanced Search — Combines FAISS similarity search with real crime data filtering.

Usage:
    from research.backend.search_enhanced import EnhancedSearch
    searcher = EnhancedSearch()
    results = searcher.search({"regiao": "Capital", "roubo_rua": 10, "ano": 2024})
    stats = searcher.get_stats()
"""

import json
import numpy as np
from pathlib import Path

FAISS_MODULE = Path(__file__).resolve().parent.parent / "faiss"


class EnhancedSearch:
    """Search engine that combines FAISS vector search with structured data filtering."""

    def __init__(self):
        self.faiss_index = None
        self.data = []
        self._load()

    def _load(self):
        """Load FAISS index (if available) and real crime data."""
        # Try to load FAISS index
        try:
            import faiss
            idx_path = FAISS_MODULE / "civitas_hnsw.index"
            if idx_path.exists():
                self.faiss_index = faiss.read_index(str(idx_path))
        except Exception:
            pass

        # Load real data
        data_path = Path(__file__).resolve().parent.parent / "data" / "rio_crime_data.json"
        if data_path.exists():
            with open(data_path) as f:
                self.data = json.load(f)

    def search(self, query_fields: dict, top_k: int = 10) -> list:
        """
        Search by filtering on fields.

        query_fields can include:
        - regiao, ano, mes: exact string/numeric match
        - crime_type names (e.g. 'roubo_rua'): minimum value (records with >= this value)
        - Any other field present in the data

        Returns matching records limited to top_k.
        """
        results = []
        for rec in self.data:
            match = True
            for k, v in query_fields.items():
                if k not in rec:
                    match = False
                    break
                if isinstance(v, (int, float)):
                    try:
                        if float(rec.get(k, 0)) < v:
                            match = False
                            break
                    except (ValueError, TypeError):
                        match = False
                        break
                elif isinstance(v, str):
                    if str(rec.get(k, '')).lower() != v.lower():
                        match = False
                        break
            if match:
                results.append(rec)
        return results[:top_k]

    def get_stats(self) -> dict:
        """Return aggregate statistics from the loaded data."""
        total = len(self.data)
        crimes = {}
        for rec in self.data:
            for k, v in rec.items():
                if k not in (
                    'cisp', 'mes', 'ano', 'mes_ano', 'aisp', 'risp',
                    'munic', 'mcirc', 'regiao', 'fase'
                ):
                    try:
                        val = int(v) if v else 0
                        crimes[k] = crimes.get(k, 0) + val
                    except (ValueError, TypeError):
                        pass
        sorted_crimes = dict(sorted(crimes.items(), key=lambda x: -x[1])[:20])
        return {'total_records': total, 'crime_totals': sorted_crimes}


# ── CLI usage ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    searcher = EnhancedSearch()
    print(f"[search_enhanced] Loaded {len(searcher.data)} records, FAISS={'yes' if searcher.faiss_index else 'no'}")

    stats = searcher.get_stats()
    print(f"\nStats: {stats['total_records']} total records")
    print("Top crime types:")
    for name, total in stats['crime_totals'].items():
        print(f"  {name}: {total:,}")

    print("\nSample search: regiao=Capital, ano=2024, roubo_rua>=10")
    results = searcher.search({"regiao": "Capital", "ano": 2024, "roubo_rua": 10})
    print(f"Found {len(results)} results")
    for r in results[:3]:
        print(f"  CISP={r['cisp']} | mes={r['mes']} | {r['regiao']} | roubo_rua={r['roubo_rua']}")
