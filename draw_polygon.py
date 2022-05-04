import shapely.geometry
import utm
import pandas as pd
import geopandas as gpd
import requests, io, json
from shapely.geometry import Point, Polygon, LineString
import shapely.speedups
shapely.speedups.enable()
import shapely.wkt
import rtree
import pygeos

# need to use UTM to express radius as a distance. UTM is zoned, so if GPS coords are very widely distributed
# distance will be incorrect.  zone is estimated from first GPS coordinate
# returns geopandas dataframe re-projected to GPS co-ordinates
# radius is expressed in metres
def poi_poly(
    df,
    radius,
    poi,
    lon_col="Long",
    lat_col="Lat",
    include_radius_poly=False,
):

    # Add radius buffer, + 1000 mts
    radius = radius + 1200

    # generate a geopandas data frame of the POI
    gdfpoi = gpd.GeoDataFrame(
        geometry=[shapely.geometry.Point(poi["Long"], poi["Lat"])],
        crs="EPSG:4326",
    )

    # Extend point to radius defined (a polygon).  Use UTM so that distances work, then back to WSG84
    gdfpoi = (
        gdfpoi.to_crs(gdfpoi.estimate_utm_crs())
        .geometry.buffer(radius)
        .to_crs("EPSG:4326")
    )

    # create a geopandas data frame of all the points / markers
    if not df is None:
        gdf = gpd.GeoDataFrame(
            geometry=df.loc[:, ["Long", "Lat"]]
            .dropna()
            .apply(
                lambda r: shapely.geometry.Point(r["Long"], r["Lat"]), axis=1
            )
            .values,
            crs="EPSG:4326",
        )
    else:
        gdf = gpd.GeoDataFrame(geometry=gdfpoi)

    # create a polygon around the edges of the markers that are within POI polygon
    return pd.concat(
        [
            gpd.GeoDataFrame(
                geometry=[
                    gpd.sjoin(
                        gdf, gpd.GeoDataFrame(geometry=gdfpoi), how="inner"
                    ).unary_union.convex_hull
                ]
            ),
            gpd.GeoDataFrame(geometry=gdfpoi if include_radius_poly else None),
        ]
    )


# Useful function to check whether a Point belongs to a polygon

# Function to find submarket based on lat, long

def market_Lookup(lat, long, geom_dict):

    # Iterate over dict of Submarket and polygon geom.
    # Check if the point lies within polygon, if true, get the submarket.

    for key, val in geom_dict.items():

        point = Point(long, lat)
        polygon = shapely.wkt.loads(val)

        if polygon.contains(point):

           return key.lower()
