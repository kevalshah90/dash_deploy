# Packages
import pandas as pd
import numpy as np
import os
import json
import geojson
import ast
import dash
from dash.dependencies import Input, Output, State
from dash import dcc
from dash import html, dash_table
import dash_bootstrap_components as dbc
import plotly as py
from plotly import graph_objs as go
from plotly.graph_objs import *
import plotly.figure_factory as ff
from application import application
from datetime import date, datetime, timedelta
from collections import defaultdict
import mapbox
import geocoder
import geopandas as gpd
import shapely.geometry
from shapely import wkt
from scipy import spatial
from dash.dash import no_update
from dash.exceptions import PreventUpdate
import io
from urllib.request import urlopen
from funcs import clean_percent, clean_currency, get_geocodes, create_presigned_url, streetview, coords_dict, nearby_places, sym_dict, valid_geom

# US Census libraries and API key
import censusgeocode as cg
from census import Census
from us import states
c = Census("71a69d38e3f63242eca7e63b8de1019b6e9f5912")

# AWS credentials
import boto3
aws_id = 'AKIA2MQCGH6RW7TE3UG2'
aws_secret = '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'
s3 = boto3.client('s3')

# Google Maps API key
import googlemaps
gmaps = googlemaps.Client(key="AIzaSyC0XCzdNwzI26ad9XXgwFRn2s7HrCWnCOk")

# Mapbox
MAPBOX_KEY="pk.eyJ1Ijoia2V2YWxzaGFoIiwiYSI6ImNqeDNsNzY2YTAwN3g0YW13aHMyNXIwMHAifQ.Hx8cPYyTFTSXP9ixiNcrTw"
token = MAPBOX_KEY
Geocoder = mapbox.Geocoder(access_token=token)

# mysql connection
import pymysql
from sqlalchemy import create_engine
user = 'stroom'
pwd = 'Stroomrds'
host =  'aa1jp4wsh8skxvw.csl5a9cjrheo.us-west-1.rds.amazonaws.com'
port = 3306
database = 'stroom_main'
engine = create_engine("mysql+pymysql://{}:{}@{}/{}".format(user,pwd,host,database))
con = engine.connect()

#Query GeoData
try:
    query = '''
            select * from stroom_main.usgeodata_v1
            '''

    df_geo = pd.read_sql(query, con)

    df_geo.tract_geom = df_geo.tract_geom.apply(valid_geom)

    Market_List = list(df_geo['MSA'].unique())

    # # Convert to GeoDataFrame
    gdf = gpd.GeoDataFrame(df_geo[df_geo['tract_geom'].notna()], geometry='tract_geom')
    # Polygon to strings
    gdf['tract_geom'] = gdf.tract_geom.apply(lambda x: wkt.dumps(x))

except:
    print("usgeodata query exception", e)
    df_geo = pd.DataFrame({})


# Read census tract level geometries and geo data
url = 'https://stroom-images.s3.us-west-1.amazonaws.com/uscensusgeo_v1.geojson'

with urlopen(url) as response:
    geo_json = json.load(response)

# App Layout for designing the page and adding elements
layout = html.Div([

                   dbc.Row([

                        dbc.Label("Buy Box", className = "buy-box"),

                        dbc.InputGroup(
                            [

                               dbc.InputGroupAddon("Market"),

                               dcc.Dropdown(
                                                id="market-deal",
                                                persistence=True,
                                                options=[{"label": name, "value": name} for name in Market_List],
                                                placeholder="Select a Market"
                               ),

                            ],

                         className="market-deal-style",

                        ),


                        dbc.InputGroup(
                            [

                               dbc.InputGroupAddon("Property type"),
                               dcc.Dropdown(
                                              id="prop-type-deal",
                                              persistence=True,
                                              persistence_type="memory",
                                              options=[
                                                       {"label": "Multi-Family", "value": "Multi-Family"}
                                              ],
                                              value="Multi-Family"
                               ),


                         ],

                         className="prop-type-deal-style",

                        ),

                        # Year Built
                        dbc.InputGroup(
                            [

                                dbc.InputGroupAddon("Year Built"),
                                dbc.Input(
                                          id="year-built-min",
                                          persistence=True,
                                          persistence_type="memory",
                                          placeholder="Min"
                                         ),
                                dbc.Input(
                                          id="year-built-max",
                                          persistence=True,
                                          persistence_type="memory",
                                          placeholder="Max"
                                         ),
                            ], style = {"height":"44px", "padding-left":"20px"},

                        ),

                        # Number of Units
                        dbc.InputGroup(
                            [

                                dbc.InputGroupAddon("Units"),
                                dbc.Input(
                                          id="num-units-min",
                                          persistence=True,
                                          persistence_type="memory",
                                          placeholder="Min"
                                         ),
                                dbc.Input(
                                          id="num-units-max",
                                          persistence=True,
                                          persistence_type="memory",
                                          placeholder="Max"
                                         ),

                            ], style={"height":"44px"},

                        ),

                        dbc.Button("Show Properties", id="show-properties-button", size="lg", className="mr-1", n_clicks=0),


                   ], className="row-1-deal"),


                   dbc.Row(
                       [

                         dbc.Col(

                           dbc.InputGroup(
                               [

                                  dbc.Label("Add Layers", className = "layers"),
                                  dcc.Checklist(
                                                id = "overlay",
                                                options=[{'label':'Overlay', 'value':'overlay'}]
                                  ),

                                  dbc.Label("Demographics"),
                                  dcc.Dropdown(

                                                 id="demo-deal",
                                                 persistence=True,
                                                 persistence_type="memory",
                                                 options=[
                                                          {'label': 'Rent Growth', 'value': 'RentGrowth'},
                                                          {'label': 'Market Volatility', 'value': 'Volatility'},
                                                          {'label': 'Home Value', 'value': 'Home'},
                                                          {'label': 'Population', 'value': 'Pop'},
                                                          {'label': 'Income', 'value': 'Income'},
                                                          {'label': 'Price-Rent Ratio', 'value': 'Price_Rent_Ratio'},
                                                          {'label': 'Income change (%)', 'value': 'Income-change'},
                                                          {'label': 'Population change (%)', 'value': 'Pop-change'},
                                                          {'label': 'Home Value change (%)', 'value': 'Home-value-change'},
                                                          {'label': 'Bachelor\'s', 'value': 'Bachelor'},
                                                          {'label': 'Graduate', 'value': 'Graduate'}
                                                 ],
                                                 value=""

                                  ),

                                  dbc.Label("Neighborhood"),
                                  dcc.Dropdown(

                                                 id="location-deal",
                                                 persistence=True,
                                                 persistence_type="memory",
                                                 options=[

                                                          {'label': 'Transit', 'value': 'Transit'},
                                                          {'label': 'Grocery', 'value': 'Grocery'},
                                                          {'label': 'School', 'value': 'School'},
                                                          {'label': 'Hospital', 'value': 'Hospital'},
                                                          {'label': 'Worship', 'value': 'Worship'},
                                                          {'label': 'Food/Cafe', 'value': 'Food/Cafe'},
                                                          {'label': 'Gas', 'value': 'Gas'}

                                                 ],
                                                 value=""

                                  ),


                               ], style={"width":"175%"},
                            ),

                            width={"size": 1, "order": "first"},
                            className="deal-dropdown",

                         ),


                         dbc.Col(

                            html.Div([

                                # Plot properties map
                                dcc.Graph(id="map-deal"),

                                ], className="deal-map-style"),


                         width={"size": 2}),


                         dbc.Col([

                            # dbc popup / modal - comps
                            html.Div([

                                dbc.Modal(
                                    [
                                        dbc.ModalHeader("Property Information", style={"color":"black", "justify-content":"center"}),
                                        dbc.ModalBody(
                                            [

                                                # Images
                                                html.Div(id="carousel_deal"),

                                                dbc.Label("Property Name:", style={"color":"black", "font-weight": "bold", "margin-right":"10px", "margin-top":"1.5%"}),
                                                dbc.Label("Property Name:", id="prop_name_deal"),
                                                html.Br(),

                                                dbc.Label("Address:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                                dbc.Label("Address:", id="Address_deal"),
                                                html.Br(),

                                                dbc.Label("Number of Units:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                                dbc.Label("Size:", id="Size_deal"),
                                                html.Br(),

                                                dbc.Label("Year Built:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                                dbc.Label("Year Built:", id="Yr_Built_deal"),
                                                html.Br(),

                                                dbc.Label("Property: ", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                                dbc.Label("Property:", id="Property_deal"),
                                                html.Br(),

                                                dbc.Label("Est. Rent:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                                dbc.Label("Rent:", id="Rent_deal"),
                                                html.Br(),

                                                dbc.Label("Fiscal Revenue:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                                dbc.Label("Revenue:", id="Revenue_deal"),
                                                html.Br(),

                                                dbc.Label("Occupancy:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                                dbc.Label("Occupancy:", id="occ-modal_deal"),
                                                html.Br(),

                                                dbc.Label("Rentable Area:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                                dbc.Label("Rentable Area:", id="rent-area-modal_deal"),
                                                html.Br(),

                                                dbc.Label("Assessed Value:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                                dbc.Label("Assessed Value:", id="assessed-value_deal"),
                                                html.Br(),

                                                dbc.Label("In-place Cap Rate:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                                dbc.Label("Cap Rate:", id="cap-rate_deal"),
                                                html.Br(),

                                                dbc.Label("Loan Info", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),

                                                dbc.Label("Loan Status:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                                dbc.Label("Loan Status:", id="loan-status_deal"),
                                                html.Br(),

                                                dbc.Label("Deal Type:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                                dbc.Label("Deal Type:", id="deal-type_deal"),
                                                html.Br(),

                                                dbc.Label("Loan Seller:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                                dbc.Label("Loan Seller:", id="loan-seller_deal"),
                                                html.Br(),

                                                dbc.Label("Owner Info:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                                dbc.Label("Owner Info:", id="owner-info_deal"),
                                                html.Br(),

                                                dbc.Label("Last Sale Date:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                                dbc.Label("Last Sale Date:", id="sale-date_deal"),
                                                html.Br(),

                                                #dbc.Button("View Returns", color="primary", size="lg", id="returns_btn", className="mr-1")

                                            ]
                                        ),
                                        dbc.ModalFooter(
                                            [

                                                dbc.Label("Sources: CMBS, CoreLogic", style={"float":"left", "padding-right":"26em", "font-size":"12px"}),

                                                dbc.Button("OK", color="primary", size="lg", id="close_deal", className="mr-1"),
                                            ]
                                        ),
                                    ],
                                    id="modal-1-deal",
                                ),

                            ], style={"width": "50%"}),

                        ], width={"size": 10, "order": "last", "offset": 8},),
                    ]),

                    html.Div(id="dummy-div"),

                    dbc.Row([

                            # # Lease Table
                            html.Div([

                                dash_table.DataTable(

                                    id="comps-table-deal",

                                    columns=[{"id":"Property Name","name":"Property Name"},
                                             {"id":"Property Type","name":"Property Type"},
                                             {"id":"Zip Code","name":"Zip Code"},
                                             {"id":"Year Built","name": "Year Built"},
                                             {"id":"Preceding Fiscal Year Revenue","name": "Revenue"},
                                             {"id":"EstRentableArea","name": "Area (Sq.ft)"},
                                             {"id":"Most Recent Physical Occupancy","name":"Occupancy"},
                                             {"id":"Size","name": "Number of Units"},
                                             {"id":"zrent_median","name": "Rent (Median)"},
                                             {"id":"Opex", "name":"Opex (Monthly)"},
                                             {'id':"EstValue", "name":"Assessed Value"},
                                             {'id':"Loan Status_y", "name":"Loan Status"},
                                             {'id':"lastSaleDate", "name":"Last Sale Date"}],

                                    style_cell={
                                        "fontFamily": "Arial",
                                        "fontSize": 12,
                                        "textAlign": "center",
                                        "height": "40px",
                                        "padding": "2px 22px",
                                        "whiteSpace": "inherit",
                                        "overflow": "hidden",
                                        "textOverflow": "ellipsis",
                                    },

                                    style_table={
                                        "maxHeight": "50ex",
                                        "overflowY": "scroll",
                                        "width": "100%",
                                    },

                                    style_header={
                                        "backgroundColor": "rgb(230, 230, 230)",
                                        "fontWeight": "bold"
                                    },

                                    style_data_conditional=[{
                                        "if": {"row_index": "odd"},
                                        "backgroundColor": "rgb(248, 248, 248)",

                                        # 'active' | 'selected'
                                        "if": {"state": "selected"},
                                        "backgroundColor": "rgba(174, 214, 241)",
                                        "border": "1px solid blue",

                                        # 'active' | 'selected'
                                        "if": {"state": "active"},
                                        "backgroundColor": "rgba(174, 214, 241)",
                                        "border": "1px solid blue",

                                    }],

                                    persistence=True,
                                    persistence_type="memory",
                                    page_size = 10,
                                    sort_action="native",
                                    filter_action="native",
                                    row_deletable=True,
                                    export_format="csv"
                                ),


                            ], className="table-style-deal"),

                        ]),

], id="deal-layout")


# Callbacks

# Auto Populate market
@application.callback([
                          Output("market-deal", "value")
                      ],
                      [
                          Input("dummy-div", "value")
                      ],
                      [
                          State("query-store", "data"),
                          State("result-store", "data"),
                          State("api-store", "data"),
                          State("table-store", "data")
                      ]
                     )
def autopop_market(dummy, query_store, result_store, api_store, table_store):

    print("autopop market cb")

    print("query store", query_store)
    print("result store", result_store)
    print("api store", api_store)
    print("table store", table_store)

    return (no_update)

# Update map graph
@application.callback([

                          Output("map-deal", "figure"),
                          Output("comps-table-deal", "data")

                      ],
                      [

                          Input("market-deal", "value"),
                          Input("overlay", "value"),
                          Input("demo-deal", "value"),
                          Input("location-deal", "value"),
                          Input("prop-type-deal", "value"),
                          Input("year-built-min", "value"),
                          Input("year-built-max", "value"),
                          Input("num-units-min", "value"),
                          Input("num-units-max", "value"),
                          Input("show-properties-button", "n_clicks"),
                          Input("map-deal", "relayoutData")

                      ],
                      )
def update_map_deal(market, overlay, demo_dropdown, loc_dropdown, proptype, year_built_min, year_built_max, num_units_min, num_units_max, show_properties_nclicks, mapdata):

    # check for triggered inputs / states
    ctx = dash.callback_context

    coords = [0,0]

    # Default layout
    coords[0] = 37.7749
    coords[1] = -122.4194

    zoom = 10

    datad = []

    data_def = []

    data_def.append({

                        "type": "scattermapbox",
                        "lat": coords[0],
                        "lon": coords[1],
                        "name": "Location",
                        "hovertext": "",
                        "showlegend": False,
                        "hoverinfo": "text",
                        "mode": "markers",
                        "clickmode": "event+select",
                        "marker": {
                            "symbol": "circle",
                            "size": 9,
                            "opacity": 0.8
                        }
                    }
    )

    if market is not None or ctx.triggered[0]['value'] is not None:

        if market in Market_List:
            lat, long = get_geocodes(market)
            coords[0] = lat
            coords[1] = long
            zoom = 9

        elif ctx.triggered[0]['value'] in Market_List:
            lat, long = get_geocodes(market)
            coords[0] = lat
            coords[1] = long
            zoom = 9

    if mapdata:

        if 'mapbox.center' in mapdata and 'mapbox.zoom' in mapdata:

            # Set coords
            coords[0] = mapdata['mapbox.center']['lat']
            coords[1] = mapdata['mapbox.center']['lon']

            # Set zoom level
            zoom = mapdata['mapbox.zoom']

    if proptype == "Multi-Family" and market and show_properties_nclicks > 0:

        # Plot sample properties - match with starting view of the map
        df_msa = gdf[gdf['MSA'] == market]

        # Apply filters
        df_msa['Year Built'] = df_msa['Year Built'].astype(int)

        df_msa['Size'] = df_msa['Size'].astype(int)

        if year_built_min and year_built_max:
            df_msa = df_msa[(df_msa['Year Built'] >= int(year_built_min)) & (df_msa['Year Built'] <= int(year_built_max))]

        if num_units_min and num_units_max:
            df_msa = df_msa[(df_msa['Size'] >= int(num_units_min)) & (df_msa['Size'] <= int(num_units_max))]

        # Generate Address string
        addr_cols = ["Address", "City", "State", "Zip Code"]
        df_msa['Address_Comp'] = df_msa[addr_cols].apply(lambda row: ' '.join(row.values.astype(str)), axis=1)

        # Format Columns
        df_msa['Occ.'] = df_msa['Occ.'].apply(clean_percent)

        # Filter by potential upside
        df1 = df_msa[(df_msa['diff_potential'] >= 0) & (df_msa['diff_potential'] <= 80)]

        # Format columns
        df1['EstValue'] = df1['EstValue'].apply('${:,.0f}'.format)
        df1['zrent_median'] = df1['zrent_median'].apply('${:,.0f}'.format)
        df1['Preceding Fiscal Year Revenue'] = df1['Preceding Fiscal Year Revenue'].apply('${:,.0f}'.format)

        # Hover Info
        propname = df1['Property Name']

        # Columns for customdata
        cd_cols = ['Property Name','Address_Comp','Size','Year Built','Property Type','zrent_quantile_random','zrent_median','Preceding Fiscal Year Revenue','Occ.','EstRentableArea','EstValue','CapRate','Loan Status_y','Deal Type','Loan Seller','PartyOwner1NameFull','lastSaleDate']

        datad.append({

                        "type": "scattermapbox",
                        "lat": df1['Lat'],
                        "lon": df1['Long'],
                        "name": "Location",
                        "hovertext": propname,
                        "showlegend": False,
                        "hoverinfo": "text",
                        "mode": "markers",
                        "clickmode": "event+select",
                        "customdata": df1.loc[:,cd_cols].values,
                        "marker": {
                            "autocolorscale": False,
                            "showscale":True,
                            "symbol": "circle",
                            "size": 9,
                            "opacity": 0.8,
                            "color": df1['diff_potential'],
                            "colorscale": "YlGnBu",
                            "cmin": df1[df1['diff_potential'] > 0]['diff_potential'].min(),
                            "cmax": df1['diff_potential'].max(),
                            "colorbar":dict(
                                            title= 'Upside',
                                            orientation= 'v',
                                            side= 'left',
                                            showticklabels=True,
                                            thickness= 20,
                                            tickformatstops=dict(dtickrange=[0,10]),
                                            titleside= 'top',
                                            ticks= 'outside'
                                           )
                            }
                     }
        )

    elif proptype == "Multi-Family" and market and show_properties_nclicks <= 0 and df_geo.shape[0] > 0:

        datad.append({

                        "type": "scattermapbox",
                        "lat": coords[0],
                        "lon": coords[1],
                        "name": "Location",
                        "hovertext": "",
                        "showlegend": False,
                        "hoverinfo": "text",
                        "mode": "markers",
                        "clickmode": "event+select",
                        "marker": {
                            "symbol": "circle",
                            "size": 9,
                            "opacity": 0.8
                            }
                     }
        )



    # Choroplethmapbox
    if demo_dropdown is not None and demo_dropdown != "" and gdf.shape[0] > 0:

        geo_level = None

        df_geo_sub = gdf[gdf['MSA'] == market]

        if mapdata is not None:

            if len(mapdata) > 1 and 'mapbox.center' in mapdata and 'mapbox.zoom' in mapdata:

                # set coords
                coords[0] = mapdata['mapbox.center']['lat']
                coords[1] = mapdata['mapbox.center']['lon']

                # set zoom level
                zoom = mapdata['mapbox.zoom']

        if demo_dropdown == "RentGrowth":
            # Query rental growth data
            query = '''

                    select MsaName, zip_code, AVG(pct_change) AS avg_rent_growth, ST_AsText(geometry) as geom
                    from stroom_main.gdf_rent_growth
                    GROUP BY MsaName, zip_code, geometry
                    HAVING st_distance_sphere(Point({},{}), ST_Centroid(geometry)) <= {};

                    '''.format(coords[1], coords[0], 1609*25)

            # To panads
            df_rg = pd.read_sql(query, con)

            # To GeoPandas
            df_rg['geom'] = gpd.GeoSeries.from_wkt(df_rg['geom'])
            gdf_rg = gpd.GeoDataFrame(df_rg, geometry='geom')

            gdf_rg['avg_rent_growth'] = round(gdf_rg['avg_rent_growth']*100,2)
            s = gdf_rg['avg_rent_growth'].astype(float)
            label = "Rent Growth (YoY)"

            geo_level = "zip"
            cscale = "Portland"

        # Volatility Index
        if demo_dropdown == "Volatility":
            # Query rental growth data
            query = '''

                    select MsaName, zip_code, STD(pct_change) AS std_rent_growth, ST_AsText(geometry) as geom
                    from stroom_main.gdf_rent_growth
                    GROUP BY MsaName, zip_code, geometry
                    HAVING st_distance_sphere(Point({},{}), ST_Centroid(geometry)) <= {};

                    '''.format(coords[1], coords[0], 1609*25)

            # To panads
            df_rg = pd.read_sql(query, con)

            # To GeoPandas
            df_rg['geom'] = gpd.GeoSeries.from_wkt(df_rg['geom'])
            gdf_rg = gpd.GeoDataFrame(df_rg, geometry='geom')

            gdf_rg['std_rent_growth'] = round(gdf_rg['std_rent_growth']*100,2)
            s = gdf_rg['std_rent_growth'].astype(float)
            label = "Volatility"

            geo_level = "zip"
            cscale = "Portland"

        if demo_dropdown == "Home":
            df = df_geo_sub[df_geo_sub['Median_Home_Value'] > 0]
            s = df['Median_Home_Value'].astype(float)
            label = "Median Home Value"
            geo_level = "census"

        elif demo_dropdown == "Pop":
            s = df_geo_sub['Population'].astype(float)
            label = "Population"
            geo_level = "census"

        elif demo_dropdown == "Income":
            df = df_geo_sub[df_geo_sub['Median_HH_Income'] > 0]
            s = df['Median_HH_Income'].astype(float)
            label = "Median Income"
            geo_level = "census"

        elif demo_dropdown == "Income-change":
            df = df_geo_sub[(df_geo_sub['median_hh_income_percent_change'] > 0) & (df_geo_sub['median_hh_income_percent_change'] < 100)]
            s = df['median_hh_income_percent_change'].astype(float)
            label = "Income Change"
            geo_level = "census"

        elif demo_dropdown == "Pop-change":
            df = df_geo_sub[(df_geo_sub['population_percent_change'] > 0) & (df_geo_sub['population_percent_change'] < 100)]
            s = df['population_percent_change'].astype(float)
            label = "Population Change"
            geo_level = "census"

        elif demo_dropdown == "Home-value-change":
            df = df_geo_sub[(df_geo_sub['median_home_value_percent_change'] > 0) & (df_geo_sub['median_home_value_percent_change'] < 100)]
            s = df['median_home_value_percent_change'].astype(float)
            label = "Home Value Change"
            geo_level = "census"

        elif demo_dropdown == "Price_Rent_Ratio":
            df = df_geo_sub[(df_geo_sub['price_rent_ratio'] > 0) & (df_geo_sub['price_rent_ratio'] < 80)]
            s = df['price_rent_ratio'].astype(float)
            label = "Price to Rent Ratio"
            geo_level = "census"

        elif demo_dropdown == "Bachelor":
            df = df_geo_sub[df_geo_sub['Bachelor\'s Degree'] > 0]
            s = df['Bachelor\'s Degree'].astype(float)
            label = "Bachelor\'s Degree"
            geo_level = "census"

        elif demo_dropdown == "Graduate":
            df = df_geo_sub[df_geo_sub['Graduate or Professional Degree'] > 0]
            s = df['Graduate or Professional Degree'].astype(float)
            label = "Graduate Degree"
            geo_level = "census"

        if not overlay:
            datad.clear()

        if geo_level == "census":

            datad.append({

                            "type": "choroplethmapbox",
                            "geojson": geo_json,
                            "locations": df_geo_sub['tract'],
                            "z": s,
                            "featureidkey": "properties.tract",
                            "hovertext": df_geo_sub['Census_name'],
                            "autocolorscale":False,
                            "colorscale":"Portland",
                            "colorbar":dict(
                                            title = dict(text=label,
                                                         font=dict(size=12)
                                                        ),
                                            orientation = 'h',
                                            x= -0.15,
                                            xanchor= "left",
                                            y= 0,
                                            yanchor= "bottom",
                                            showticklabels=True,
                                            thickness= 20,
                                            tickformatstops=dict(dtickrange=[0,10]),
                                            titleside= 'top',
                                            ticks= 'outside',
                                            font = dict(size=12)
                                           ),
                            "zmin": s.min(),
                            "zmax": s.max(),
                            "marker_line_width": 0,
                            "opacity": 0.2,
                            "labels": label,
                            "title": "Choropleth - Census Tract Level"

                         }
            )

        elif geo_level == 'zip':

            datad.append({

                            "type": "choroplethmapbox",
                            "geojson": gdf_rg.__geo_interface__,
                            "locations": gdf_rg['zip_code'],
                            "z": s,
                            "featureidkey": "properties.zip_code",
                            "hovertext": gdf_rg['MsaName'],
                            "autocolorscale":False,
                            "colorscale": cscale,
                            "colorbar":dict(
                                            title = dict(text=label,
                                                         font=dict(size=12)
                                                        ),
                                            orientation = 'h',
                                            x= -0.15,
                                            xanchor= "left",
                                            y= 0,
                                            yanchor= "bottom",
                                            showticklabels=True,
                                            thickness= 20,
                                            tickformatstops=dict(dtickrange=[0,10]),
                                            titleside= 'top',
                                            ticks= 'outside'
                                           ),
                            "zmin": s.min(),
                            "zmax": s.max(),
                            "marker_line_width": 0,
                            "opacity": 0.2,
                            "labels": label,
                            "title": "Choropleth - Zip Code Level"

                         }
            )

    # Location data layer
    if loc_dropdown is not None and loc_dropdown != "":

        if mapdata is not None:

            if len(mapdata) > 1 and 'mapbox.center' in mapdata and 'mapbox.zoom' in mapdata:

                # set coords
                coords[0] = mapdata['mapbox.center']['lat']
                coords[1] = mapdata['mapbox.center']['lon']

                # set zoom level
                zoom = mapdata['mapbox.zoom']

        g = geocoder.mapbox(coords, key=token, method='reverse')
        geojson = g.json
        addr = geojson["address"]

        if loc_dropdown == "Transit":
            df_nearby = nearby_places(addr, loc_dropdown)

        elif loc_dropdown == "Grocery":
            df_nearby = nearby_places(addr, loc_dropdown)

        elif loc_dropdown == "School":
            df_nearby = nearby_places(addr, loc_dropdown)

        elif loc_dropdown == "Hospital":
            df_nearby = nearby_places(addr, loc_dropdown)

        elif loc_dropdown == "Food/Cafe":
            df_nearby = nearby_places(addr, loc_dropdown)

        elif loc_dropdown == "Worship":
            df_nearby = nearby_places(addr, loc_dropdown)

        elif loc_dropdown == "Gas":
            df_nearby = nearby_places(addr, loc_dropdown)

        else:
            df_nearby = None

        # Check if DataFrame was returned
        if df_nearby is not None:
            if isinstance(df_nearby, pd.DataFrame):

               # Create a list of symbols by dict lookup
               sym_list = []

               for i in df_nearby['type_label']:
                   typ = sym_dict.get(i)
                   sym_list.append(typ)


               datad.append({

                              "type": "scattermapbox",
                              "lat": df_nearby["Lat"],
                              "lon": df_nearby["Lng"],
                              "name": "POI",
                              "hovertext": df_nearby['name'],
                              "showlegend": False,
                              "hoverinfo": "text",
                              "mode": "markers",
                              "clickmode": "event+select",
                              "marker": {
                                         "symbol": sym_list,
                                         "size": 15,
                                         "opacity": 0.7,
                                         "color": "blue"
                                        }
                              }
               )


    layout = {

                 "autosize": True,
                 "hovermode": "closest",
                 "mapbox": {

                     "accesstoken": MAPBOX_KEY,
                     "bearing": 0,
                     "center": {
                         "lat": coords[0],
                         "lon": coords[1]
                     },
                     "pitch": 0,
                     "zoom": zoom,
                     "style": "streets",

                 },

                 "margin": {
                    "r": 0,
                    "t": 0,
                    "l": 0,
                    "b": 0,
                    "pad": 0
                }

    }

    # Rearrange so that scattermapbox is top layer
    if len(datad) > 0:

        if datad[0]['type'] == 'scattermapbox':
            datad.append(datad.pop(datad.index(datad[0])))

        if show_properties_nclicks > 0:
            return ({"data": datad, "layout": layout}, df1.to_dict("records"))

        elif demo_dropdown != "" or loc_dropdown != "":
            return ({"data": datad, "layout": layout}, no_update)

        elif proptype == "Multi-Family" and market and show_properties_nclicks <= 0:
            return ({"data": datad, "layout": layout}, no_update)

    else:
        return ({"data": data_def, "layout": layout}, no_update)


# Update comps modal on click event
@application.callback(
                          [
                               # Modal Comps
                               Output("modal-1-deal","is_open"),
                               Output("carousel_deal","children"),
                               Output("prop_name_deal","children"),
                               Output("Address_deal","children"),
                               Output("Size_deal","children"),
                               Output("Yr_Built_deal","children"),
                               Output("Property_deal","children"),
                               Output("Rent_deal", "children"),
                               Output("Revenue_deal","children"),
                               Output("occ-modal_deal","children"),
                               Output("rent-area-modal_deal","children"),
                               Output("assessed-value_deal","children"),
                               Output("cap-rate_deal","children"),
                               Output("loan-status_deal","children"),
                               Output("deal-type_deal","children"),
                               Output("loan-seller_deal","children"),
                               Output("owner-info_deal","children"),
                               Output("sale-date_deal","children"),

                          ],

                          [
                               # Button clicks
                               Input("map-deal","clickData"),
                               Input("close_deal","n_clicks")

                          ],

                          [
                                State("modal-1-deal", "is_open")
                          ],
                    )
def display_popup2(clickData, n_clicks, is_open):

    if clickData:

        res = json.dumps(clickData, indent=2)

        print("clickData response", res)

        Name = clickData["points"][0]["customdata"][0]
        Address = clickData["points"][0]["customdata"][1]
        Size = clickData["points"][0]["customdata"][2]
        Built = clickData["points"][0]["customdata"][3]
        Property = clickData["points"][0]["customdata"][4]

        '''
        Rents data
        '''
        # Rents min - max
        # rents_min_max = clickData["points"][0]["customdata"][5]
        #
        # # string to list
        # rents_min_max1 = rents_min_max.replace(' ','')
        # rents_min_max2 = rents_min_max1.replace('[','')
        # rents_min_max3 = rents_min_max2.replace(']','')
        #
        # rents_min_max_lst = list(rents_min_max3.split(','))
        #
        # # Rents median
        # price_median = clickData["points"][0]["customdata"][6]
        #
        # try:
        #     if rents_min_max_lst[0] == rents_min_max_lst[1]:
        #         Rents_fmt = "${:,.0f} (Median)".format(price_median)
        #     else:
        #         Rents_fmt = "${} - ${}".format(rents_min_max_lst[0], rents_min_max_lst[1])
        # except:
        #     print("Rents Exception", e)
        #     Rents_fmt = "${:,.0f} (Median)".format(price_median)

        # Rents Quantiles
        rent_quantiles = clickData["points"][0]["customdata"][5]

        rent_median = clickData["points"][0]["customdata"][6]

        rent_median = clean_currency(rent_median)

        try:
            # string to list
            rent_quantiles = [int(float(x)) for x in rent_quantiles.strip('[]').split()]

            if rent_quantiles[0] == rent_quantiles[1]:
                Rents_fmt = "${:,.0f} (Median)".format(float(rent_median))
            else:
                Rents_fmt = "${} - ${}".format(rent_quantiles[0], rent_quantiles[1])
        except Exception as e:
            print("Rents Exception", e)
            Rents_fmt = "${:,.0f} (Median)".format(float(rent_median))

        Revenue = clickData["points"][0]['customdata'][7]
        Occupancy = clickData["points"][0]["customdata"][8]
        RentArea = clickData["points"][0]["customdata"][9]
        AssessedValue = clickData["points"][0]["customdata"][10]
        CapRate = clickData["points"][0]["customdata"][11]
        LoanStatus = clickData["points"][0]["customdata"][12]
        DealType = clickData["points"][0]["customdata"][13]
        LoanSeller = clickData["points"][0]["customdata"][14]
        OwnerInfo = clickData["points"][0]["customdata"][15]
        lastSaleDate = clickData["points"][0]["customdata"][16]

        # Construct a list of dictionaries
        # Filter Pandas DataFrame
        df = gdf[gdf['Property Name'] == Name]

        index = df.index[0]
        img_dict = df['Image_dicts'][index]

        # Construct carousel object
        try:

            if type(img_dict) is str:

                img_dict = ast.literal_eval(img_dict)

                # Add labels for carousel items property
                c = 1
                img_list = []

                # Make a call to obtain pre-signed urls of each object in S3
                for key, values in img_dict.items():

                    for v in values:

                        parts = os.path.split(v)

                        url = create_presigned_url('gmaps-images-6771', 'property_images/{}'.format(parts[len(parts)-1]))

                        # Create a list of dicts for carousel
                        img_dict1 = {"key": c, "src": url, "img_style": {"width": "300px", "height": "300px"}}
                        c = c + 1

                        img_list.append(img_dict1)

                carousel = dbc.Carousel(
                                        items=img_list,
                                        controls=True,
                                        indicators=True,
                           )

            else:

                # Get coordinates
                lat, long = get_geocodes(Address)

                # Get updated name of the streetview image
                name = streetview(lat, long, 'streetview')

                # Construct URL
                url = create_presigned_url('gmaps-images-6771', 'property_images/{}'.format(name))

                if "None" in url:
                    url = create_presigned_url('gmaps-images-6771', 'property_images/no_imagery.png')

                carousel = dbc.Carousel(
                                        items=[
                                                 {"key": "1", "src": url, "img_style": {"width": "300px", "height": "300px"}},
                                        ],
                                        controls=False,
                                        indicators=False,
                           )

        except Exception as e:
            print(e)

        # Formatted Rent for default view (NA) and calculated / post button click and handling of None values

        if Revenue is None:
            Revenue_fmt == "N/A"
        else:
            Revenue = clean_currency(Revenue)
            Revenue_fmt = "${:,.0f}".format(float(Revenue))

        if Occupancy is None:
            Occupancy_fmt == "N/A"
        else:
            Occupancy = float(Occupancy)
            Occupancy_fmt = "{:.0f}%".format(Occupancy)

        if RentArea is None:
            RentArea_fmt = "N/A"
        else:
            RentArea_fmt = "{:,.0f} sq.ft".format(RentArea)

        if AssessedValue is None:
            AssessedValue_fmt = "N/A"
        elif type(AssessedValue) != str:
            AssessedValue_fmt = "${:,.0f}".format(AssessedValue)
        else:
            AssessedValue_fmt = AssessedValue

        if CapRate is None:
            CapRate_fmt = "N/A"
        elif type(CapRate) != str:
            CapRate = CapRate * 100
            CapRate_fmt = "{:,.2f}%".format(CapRate)
        else:
            CapRate_fmt = CapRate

        if LoanStatus == "null":
            LoanStatus_fmt = "N/A"
        else:
            LoanStatus_fmt = LoanStatus

        if DealType == "null":
            DealType_fmt = "N/A"
        else:
            DealType_fmt = DealType

        if LoanSeller == "null":
            LoanSeller_fmt = "N/A"
        else:
            LoanSeller_fmt = LoanSeller

        if OwnerInfo == "null":
            OwnerInfo_fmt = "N/A"
        else:
            OwnerInfo_fmt = OwnerInfo

        if lastSaleDate == "null":
            lastSaleDate_fmt = "N/A"
        else:
            lastSaleDate_fmt = lastSaleDate

        return(not is_open, carousel, Name, Address, Size, Built, Property, Rents_fmt, Revenue_fmt, Occupancy_fmt, RentArea_fmt, AssessedValue_fmt, CapRate_fmt, LoanStatus_fmt, DealType_fmt, LoanSeller_fmt, OwnerInfo_fmt, lastSaleDate_fmt)

    elif n_clicks:
        return is_open

    else:
        return no_update
