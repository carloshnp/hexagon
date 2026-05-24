"""H3 hexagonal indexing — encode any GeoDataFrame of points."""
import h3
import geopandas as gpd
import pandas as pd

H3_RESOLUTION = 8  # ~460m² per cell, ideal for urban micro-areas


def encode_h3(gdf: gpd.GeoDataFrame, resolution: int = H3_RESOLUTION) -> gpd.GeoDataFrame:
    """Add h3_cell column to a point GeoDataFrame."""
    gdf = gdf.copy()
    gdf["h3_cell"] = [
        h3.latlng_to_cell(geom.y, geom.x, resolution)
        for geom in gdf.geometry
    ]
    return gdf


def aggregate_by_h3(gdf: gpd.GeoDataFrame, count_col: str = "count") -> pd.DataFrame:
    """Group by h3_cell → counts + centroid lat/lon."""
    agg = gdf.groupby("h3_cell").size().reset_index(name=count_col)
    # Decode H3 centroid for convenience
    centroids = agg["h3_cell"].apply(
        lambda cell: pd.Series(h3.cell_to_latlng(cell), index=["lat", "lon"])
    )
    return pd.concat([agg, centroids], axis=1)
