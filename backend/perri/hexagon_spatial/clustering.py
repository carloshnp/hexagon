"""DBSCAN spatial clustering on H3-aggregated data."""
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN

EARTH_RADIUS_KM = 6371.0
# ~300m radius, min 5 points to form a cluster
EPS_KM = 0.3
MIN_SAMPLES = 5


def cluster_hotspots(h3_agg: pd.DataFrame, eps_km: float = EPS_KM, min_samples: int = MIN_SAMPLES) -> pd.DataFrame:
    """DBSCAN on H3 centroids weighted by count. Returns df with cluster_id column."""
    coords = np.radians(h3_agg[["lat", "lon"]].values)
    eps_rad = eps_km / EARTH_RADIUS_KM

    # Repeat rows by count so denser cells have more weight in clustering
    weights = h3_agg["count"].clip(upper=50).astype(int)
    coords_weighted = np.repeat(coords, weights, axis=0)

    db = DBSCAN(eps=eps_rad, min_samples=min_samples, algorithm="ball_tree", metric="haversine")
    labels_weighted = db.fit_predict(coords_weighted)

    # Map back: first label per original row
    label_idx = np.concatenate([[0], weights.cumsum().values[:-1]])
    h3_agg = h3_agg.copy()
    h3_agg["cluster_id"] = labels_weighted[label_idx]
    return h3_agg
