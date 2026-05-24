"""
movement_graph.py — Sistema de Grafo de Movimento (CIVITAS)

Funções principais:
  - build_movement_graph(detections) -> nx.DiGraph
  - find_most_likely_path(G, start, end) -> list
  - get_hotspots(G, threshold=3) -> list

Dependências: networkx, numpy
"""

import networkx as nx
import numpy as np
from collections import defaultdict
from typing import Any


# ──────────────────────────────────────────────
# 1. Construção do grafo a partir de detecções
# ──────────────────────────────────────────────

def build_movement_graph(detections: list[dict]) -> nx.DiGraph:
    """
    Constrói um grafo direcionado (DiGraph) onde:
      - Nós  → câmeras / localizações
      - Arestas → transições observadas entre câmeras

    Cada detecção deve conter:
      - 'camera_id'  : str  — identificador da câmera
      - 'track_id'   : str  — identificador único da pessoa/veículo
      - 'timestamp'  : float — instante da detecção
      - 'crime_type' : str (opcional) — tipo de crime associado

    Args:
        detections: lista de dicionários de detecção.

    Returns:
        nx.DiGraph com atributos nos nós e arestas.
    """
    G = nx.DiGraph()

    # Agrupa detecções por track_id, ordenadas por timestamp
    tracks: dict[str, list[dict]] = defaultdict(list)
    for d in detections:
        tracks[d['track_id']].append(d)

    # Ordena cada track e extrai transições
    for track_id, events in tracks.items():
        events.sort(key=lambda x: x['timestamp'])
        crime_type = events[0].get('crime_type', 'unknown')

        for i in range(len(events)):
            cam = events[i]['camera_id']

            # Adiciona / atualiza nó
            if not G.has_node(cam):
                G.add_node(
                    cam,
                    detections=0,
                    crime_types=set(),
                    last_seen=events[i]['timestamp']
                )

            node_data = G.nodes[cam]
            node_data['detections'] += 1
            node_data['crime_types'].add(crime_type)
            node_data['last_seen'] = max(
                node_data['last_seen'], events[i]['timestamp']
            )

            # Cria aresta da câmera anterior para a atual
            if i > 0:
                prev_cam = events[i - 1]['camera_id']
                if prev_cam != cam:
                    if G.has_edge(prev_cam, cam):
                        G.edges[prev_cam, cam]['weight'] += 1
                        G.edges[prev_cam, cam]['transitions'].append({
                            'track_id': track_id,
                            'time': events[i]['timestamp'],
                            'crime_type': crime_type,
                        })
                    else:
                        G.add_edge(
                            prev_cam, cam,
                            weight=1,
                            transitions=[{
                                'track_id': track_id,
                                'time': events[i]['timestamp'],
                                'crime_type': crime_type,
                            }]
                        )

    # Converte set de crime_types para lista (serializável)
    for node in G.nodes:
        G.nodes[node]['crime_types'] = list(G.nodes[node]['crime_types'])

    return G


# ──────────────────────────────────────────────
# 2. Rota mais provável entre dois nós
# ──────────────────────────────────────────────

def find_most_likely_path(G: nx.DiGraph, start: str, end: str) -> list[str]:
    """
    Encontra a rota mais provável entre 'start' e 'end' usando
    caminho mais curto ponderado pelo inverso do peso das arestas.

    Arestas com maior peso (mais transições) são favorecidas.

    Args:
        G: grafo direcionado.
        start: nó de partida.
        end: nó de destino.

    Returns:
        Lista de nós representando o caminho.
        Lista vazia se não houver caminho.
    """
    if start not in G or end not in G:
        return []

    try:
        # Usa o inverso do peso para que arestas mais usadas
        # tenham "menor custo"
        weight_attr = 'weight'

        def inverse_weight(u, v, d):
            return 1.0 / d.get(weight_attr, 1)

        path = nx.shortest_path(
            G, source=start, target=end,
            weight=inverse_weight
        )
        return path
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return []


# ──────────────────────────────────────────────
# 3. Identificação de hotspots (betweenness)
# ──────────────────────────────────────────────

def get_hotspots(
    G: nx.DiGraph,
    threshold: float = 3.0
) -> list[dict]:
    """
    Identifica hotspots no grafo baseado em betweenness centrality.

    Retorna nós cuja centralidade ultrapassa o threshold,
    ordenados do mais central para o menos central.

    Args:
        G: grafo direcionado.
        threshold: valor mínimo de betweenness para ser hotspot.

    Returns:
        Lista de dicionários { 'node', 'betweenness', 'detections',
                               'crime_types' }.
    """
    if G.number_of_nodes() == 0:
        return []

    # Betweenness centrality para grafos direcionados
    try:
        bc = nx.betweenness_centrality(G, weight='weight')
    except Exception:
        bc = nx.betweenness_centrality(G)

    hotspots = []
    for node, cent in bc.items():
        if cent >= threshold or (threshold <= 1 and cent >= threshold * 0.01):
            # Ajuste: threshold > 1 trata-se de contagem bruta;
            # caso contrário, é proporcional.
            adjusted_threshold = threshold if threshold > 1 else threshold
            if cent >= adjusted_threshold:
                hotspots.append({
                    'node': node,
                    'betweenness': round(cent, 6),
                    'detections': G.nodes[node].get('detections', 0),
                    'crime_types': G.nodes[node].get('crime_types', []),
                })

    # Se threshold é muito baixo (ex.: 3) mas betweenness é tipicamente
    # entre 0 e 1, usamos lógica de percentual
    if not hotspots and threshold > 1:
        # Fallback: top-k nós por detecções
        sorted_nodes = sorted(
            G.nodes(data=True),
            key=lambda x: x[1].get('detections', 0),
            reverse=True
        )
        threshold_count = max(1, int(threshold))
        for node, data in sorted_nodes[:threshold_count]:
            hotspots.append({
                'node': node,
                'betweenness': round(bc.get(node, 0), 6),
                'detections': data.get('detections', 0),
                'crime_types': data.get('crime_types', []),
            })

    hotspots.sort(key=lambda x: x['betweenness'], reverse=True)
    return hotspots


# ──────────────────────────────────────────────
# 4. Utilitários para exportação
# ──────────────────────────────────────────────

def graph_to_dict(G: nx.DiGraph) -> dict:
    """Converte o grafo para dicionário serializável (JSON)."""
    nodes = []
    for node, data in G.nodes(data=True):
        nodes.append({
            'id': node,
            'detections': data.get('detections', 0),
            'crime_types': list(data.get('crime_types', [])),
            'last_seen': data.get('last_seen', 0),
        })

    edges = []
    for u, v, data in G.edges(data=True):
        edges.append({
            'source': u,
            'target': v,
            'weight': data.get('weight', 1),
            'transitions': data.get('transitions', []),
        })

    return {'nodes': nodes, 'edges': edges}


# ──────────────────────────────────────────────
# 5. Demo / executável
# ──────────────────────────────────────────────

if __name__ == '__main__':
    print("=" * 60)
    print("  CIVITAS — Movement Graph Module (Demo)")
    print("=" * 60)

    # Gera 20 detecções sintéticas em 5 câmeras
    fake_detections = [
        {'camera_id': 'CAM-01', 'track_id': 'T-001', 'timestamp': 0.0, 'crime_type': 'theft'},
        {'camera_id': 'CAM-02', 'track_id': 'T-001', 'timestamp': 1.0, 'crime_type': 'theft'},
        {'camera_id': 'CAM-03', 'track_id': 'T-001', 'timestamp': 2.5, 'crime_type': 'theft'},
        {'camera_id': 'CAM-01', 'track_id': 'T-002', 'timestamp': 0.5, 'crime_type': 'assault'},
        {'camera_id': 'CAM-02', 'track_id': 'T-002', 'timestamp': 1.5, 'crime_type': 'assault'},
        {'camera_id': 'CAM-04', 'track_id': 'T-002', 'timestamp': 3.0, 'crime_type': 'assault'},
        {'camera_id': 'CAM-01', 'track_id': 'T-003', 'timestamp': 0.2, 'crime_type': 'vandalism'},
        {'camera_id': 'CAM-03', 'track_id': 'T-003', 'timestamp': 2.0, 'crime_type': 'vandalism'},
        {'camera_id': 'CAM-05', 'track_id': 'T-003', 'timestamp': 4.0, 'crime_type': 'vandalism'},
        {'camera_id': 'CAM-02', 'track_id': 'T-004', 'timestamp': 1.0, 'crime_type': 'theft'},
        {'camera_id': 'CAM-03', 'track_id': 'T-004', 'timestamp': 2.0, 'crime_type': 'theft'},
        {'camera_id': 'CAM-04', 'track_id': 'T-005', 'timestamp': 1.0, 'crime_type': 'assault'},
        {'camera_id': 'CAM-05', 'track_id': 'T-005', 'timestamp': 3.0, 'crime_type': 'assault'},
        {'camera_id': 'CAM-01', 'track_id': 'T-006', 'timestamp': 0.0, 'crime_type': 'theft'},
        {'camera_id': 'CAM-02', 'track_id': 'T-006', 'timestamp': 1.2, 'crime_type': 'theft'},
        {'camera_id': 'CAM-03', 'track_id': 'T-006', 'timestamp': 2.8, 'crime_type': 'theft'},
        {'camera_id': 'CAM-04', 'track_id': 'T-006', 'timestamp': 3.9, 'crime_type': 'theft'},
        {'camera_id': 'CAM-01', 'track_id': 'T-007', 'timestamp': 0.1, 'crime_type': 'vandalism'},
        {'camera_id': 'CAM-05', 'track_id': 'T-007', 'timestamp': 2.1, 'crime_type': 'vandalism'},
        {'camera_id': 'CAM-03', 'track_id': 'T-008', 'timestamp': 1.5, 'crime_type': 'assault'},
    ]

    print(f"\n  Detecções sintéticas: {len(fake_detections)}")
    G = build_movement_graph(fake_detections)
    print(f"  Nós (câmeras): {list(G.nodes())}")
    print(f"  Arestas: {G.number_of_edges()}")

    for u, v, d in G.edges(data=True):
        print(f"    {u} → {v}  (peso={d['weight']})")

    path = find_most_likely_path(G, 'CAM-01', 'CAM-04')
    print(f"\n  Rota mais provável CAM-01 → CAM-04: {path}")

    hotspots = get_hotspots(G, threshold=0.05)
    print(f"\n  Hotspots (threshold=0.05):")
    for h in hotspots:
        print(f"    {h['node']}: betweenness={h['betweenness']}, detecções={h['detections']}")

    dump = graph_to_dict(G)
    print(f"\n  JSON nodes: {len(dump['nodes'])}, edges: {len(dump['edges'])}")
    print("=" * 60)
