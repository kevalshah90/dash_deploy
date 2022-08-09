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
from funcs import clean_percent, clean_currency, get_geocodes, create_presigned_url, streetview, nearby_places, sym_dict, valid_geoms

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
MAPBOX_KEY="pk.eyJ1Ijoic3Ryb29tIiwiYSI6ImNsNWVnMmpueTEwejQza252ZnN4Zm02bG4ifQ.SMGyKFikz4uDDqN6JvEq7Q"
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

# def valid_geoms(x):
#     try:
#         return wkt.loads(x)
#     except:
#         return np.nan

#Query GeoData
try:

    # Tuple of markets
    msa = (
           'San Francisco-Oakland-Fremont, CA MSA',
           'San Jose-Sunnyvale-Santa Clara, CA MSA',
           'Los Angeles-Long Beach-Santa Ana, CA MSA',
           'San Diego-Carlsbad-San Marcos, CA MSA',
           'Phoenix-Mesa-Scottsdale, AZ MSA',
           'Dallas-Fort Worth-Arlington, TX MSA',
           'Austin-Round Rock, TX MSA'
    )

    query = '''
            select distinct MSA
            from stroom_main.df_raw_july
            where MSA IN {}
            '''.format(msa)

    df_market = pd.read_sql(query, con)

    query = '''
            select distinct Loan_Status
            from stroom_main.df_raw_july
            where MSA IN {}
            '''.format(msa)

    df_loan = pd.read_sql(query, con)

    Market_List = list(df_market['MSA'].unique())
    LoanStatus_List = list(df_loan['Loan_Status'].unique())

except Exception as e:
    print("usgeodata query exception", e)
    df_market = pd.DataFrame({})
    df_loan = pd.DataFrame({})

# Read census tract level geometries and geo data
url = "https://stroom-images.s3.us-west-1.amazonaws.com/usgeodata_july.geojson"

with urlopen(url) as response:
    geo_json = json.load(response)

# App Layout for designing the page and adding elements
layout = html.Div([

                   dbc.Row([

                        dbc.Label("Buy Box", className = "buy-box"),

                        dbc.InputGroup(
                            [

                               dbc.InputGroupText("Market"),

                               html.Datalist(id="market-list",
                                             children=[
                                                        html.Option(value = name) for name in Market_List
                                             ]
                               ),

                               dcc.Input(
                                            id = "market-deal",
                                            type = "search",
                                            autoComplete=True,
                                            autoFocus=True,
                                            list = "market-list",
                                            placeholder="Type here"
                               )

                            ],

                         className="market-deal-style",

                        ),

                        # Upside
                        dbc.InputGroup(
                            [

                               dbc.InputGroupText("Upside"),
                               dcc.Dropdown(

                                              id="upside-deal",
                                              persistence=True,
                                              persistence_type="memory",
                                              options=[
                                                       {'label': '0%-10%', 'value': '0-10'},
                                                       {'label': '10%-30%', 'value': '10-30'},
                                                       {'label': '30%+', 'value': '30+'},

                                              ],
                                              placeholder="Select"

                               ),

                         ],

                         className="upside-deal-style",

                        ),

                        # Year Built
                        dbc.InputGroup(
                            [

                                dbc.InputGroupText("Year Built"),
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
                            ], style = {"height":"44px", "margin-left":"-10px!important"},

                        ),

                        # Number of Units
                        dbc.InputGroup(
                            [

                                dbc.InputGroupText("Units"),
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

                            ], style={"height":"44px", "margin-left":"-2px!important"},

                        ),

                        # Loan Status
                        dbc.InputGroup(
                            [

                               dbc.InputGroupText("Loan"),
                               dcc.Dropdown(

                                              id="loan-deal",
                                              persistence=True,
                                              persistence_type="memory",
                                              options=[{"label": name, "value": name} for name in LoanStatus_List],
                                              optionHeight=50,
                                              placeholder="Select"

                               ),

                         ],

                         className="loan-deal-style",

                        ),

                        dbc.Label(id="prop_count", style={"float":"right", "color":"black", "font-weight": "bold"}),

                        #dbc.Button("Clear Properties", id="clear-properties-button", className="me-1", style={'height': '48px'}, n_clicks=0),

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


                                  dbc.Alert(id = "deal-alerts-1",
                                            className = "deal-alerts-1",
                                            dismissable = True,
                                            duration = 2500,
                                            is_open = False,
                                            color="light"),


                               ], style={"width":"175%"},
                            ),

                            width={"size": 1, "order": "first"},
                            className="deal-dropdown",

                         ),


                         dbc.Col(

                            html.Div([

                                # Plot properties map
                                dcc.Loading(
                                    id = "map-loading",
                                    type = "default",
                                    className = "map-loading",
                                    fullscreen=False,
                                    children=dcc.Graph(id="map-deal")
                                    #parent_style = {"opacity":"0.5"}
                                ),

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

                                                dbc.Card(
                                                    [
                                                        dbc.CardImg(id="card-img-deal", className="card-img-deal"),
                                                        dbc.CardBody(
                                                            html.P(id="card-text-deal", className="card-text-deal")
                                                        ),
                                                    ],
                                                    style={"width": "11rem", "position": "relative", "float": "right", "margin-top": "1.5%"},
                                                ),

                                                dbc.Label("Property Type: ", style={"color":"black", "font-weight": "bold", "margin-right":"10px", "margin-top":"1%", "float":"left"}),
                                                dbc.Label("Property Type:", id="Property_deal", style={"float":"left", "margin-top":"1%"}),
                                                html.Br(),
                                                html.Br(),

                                                dbc.Label("Number of Units:", style={"color":"black", "font-weight": "bold", "margin-right":"10px", "margin-top":"1%", "float":"left"}),
                                                dbc.Label("Size:", id="Size_deal", style={"float":"left", "margin-top":"1%"}),
                                                html.Br(),
                                                html.Br(),

                                                dbc.Label("Year Built:", style={"color":"black", "font-weight": "bold", "margin-right":"10px", "margin-top":"1%", "float":"left"}),
                                                dbc.Label("Year Built:", id="Yr_Built_deal", style={"float":"left", "margin-top":"1%"}),
                                                html.Br(),
                                                html.Br(),

                                                dbc.Label("Occupancy:", style={"color":"black", "font-weight": "bold", "margin-right":"10px", "margin-top":"1%", "float":"left"}),
                                                dbc.Label("Occupancy:", id="occ-modal_deal", style={"float":"left", "margin-top":"1%"}),
                                                html.Br(),
                                                html.Br(),

                                                dbc.Label("Rentable Area:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                                dbc.Label("Rentable Area:", id="rent-area-modal_deal", style={"float":"right", "margin-top":"1%"}),
                                                html.Br(),

                                                dbc.Label("Name:", style={"color":"black", "font-weight": "bold", "margin-right":"10px", "margin-top":"1.5%", "float":"left"}),
                                                dbc.Label("Name:", id="prop_name_deal", style={"float":"left", "margin-top":"1%"}),
                                                html.Br(),
                                                html.Br(),

                                                dbc.Label("Address:", style={"color":"black", "font-weight": "bold", "margin-right":"10px", "margin-top":"0%"}),
                                                dbc.Label("Address:", id="Address_deal", style={"float":"right", "margin-top":"0%"}),
                                                html.Br(),

                                                dbc.Label("Est. Rent:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                                dbc.Label("Rent:", id="Rent_deal", style={"float":"right"}),
                                                html.Br(),

                                                dbc.Label("Fiscal Revenue:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                                dbc.Label("Revenue:", id="Revenue_deal", style={"float":"right"}),
                                                html.Br(),

                                                dbc.Label("Opex:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                                dbc.Label("Opex:", id="Opex_deal", style={"float":"right"}),
                                                html.Br(),

                                                dbc.Label("Assessed Value:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                                dbc.Label("Assessed Value:", id="assessed-value_deal", style={"float":"right"}),
                                                html.Br(),

                                                dbc.Label("In-place Cap Rate:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                                dbc.Label("Cap Rate:", id="cap-rate_deal", style={"float":"right"}),
                                                html.Br(),

                                                # html.Br(),
                                                # dbc.Label("Loan Info", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                                # html.Br(),

                                                dbc.Label("Loan Status:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                                dbc.Label("Loan Status:", id="loan-status_deal", style={"float":"right"}),
                                                html.Br(),

                                                dbc.Label("Deal Type:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                                dbc.Label("Deal Type:", id="deal-type_deal", style={"float":"right"}),
                                                html.Br(),

                                                dbc.Label("Loan Seller:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                                dbc.Label("Loan Seller:", id="loan-seller_deal", style={"float":"right"}),
                                                html.Br(),

                                                dbc.Label("Owner Info:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                                dbc.Label("Owner Info:", id="owner-info_deal", style={"float":"right", "font-size": "12px"}),
                                                html.Br(),

                                                dbc.Label("Last Sale Date:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                                dbc.Label("Last Sale Date:", id="sale-date_deal", style={"float":"right"}),
                                                html.Br(),

                                                dbc.Label("Last Sale Price:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                                dbc.Label("Last Sale Price:", id="sale-price_deal", style={"float":"right"}),
                                                html.Br(),

                                                #dbc.Button("View Returns Profile", color="primary", size="lg", id="returns_btn", className="mr-1", href="/returns", style={"float":"right"})

                                            ]
                                        ),
                                        dbc.ModalFooter(
                                            [

                                                dbc.Label("Sources: Attom Data", style={"float":"left", "padding-right":"26em", "font-size":"12px"}),

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

                                    columns=[{"id":"Property_Name", "name":"Property Name"},
                                             {"id":"Zip_Code", "name":"Zip Code"},
                                             {"id":"Year_Built", "name": "Year Built"},
                                             {"id":"EstRentableArea", "name": "Area (Sq.ft)"},
                                             {"id":"Size", "name": "Number of Units"},
                                             {"id":"Preceding_Fiscal_Year_Revenue", "name": "Fiscal Revenue"},
                                             {"id":"Preceding_Fiscal_Year_Operating_Expenses", "name":"Fiscal Opex"},
                                             {"id":"Most_Recent_Physical_Occupancy", "name":"Occupancy"},
                                             {"id":"zrent_median", "name": "Rent (Median)"},
                                             {'id':"EstValue", "name":"Assessed Value"},
                                             {'id':"Loan_Status", "name":"Loan Status"},
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
                                    #row_deletable=True,
                                    export_format="csv"
                                ),


                            ], className="table-style-deal"),

                        ]),

], id="deal-layout")


# Callbacks
# Update map graph

@application.callback([

                          Output("map-deal", "figure"),
                          Output("comps-table-deal", "data"),
                          Output("prop_count", "children"),

                          # Map data storage component
                          Output("msa-prop-store", "data"),
                          Output("rg-store", "data")

                      ],
                      [
                          Input("market-deal", "value"),
                          Input("upside-deal", "value"),
                          Input("loan-deal", "value"),
                          Input("overlay", "value"),
                          Input("demo-deal", "value"),
                          Input("location-deal", "value"),
                          Input("year-built-min", "value"),
                          Input("year-built-max", "value"),
                          Input("num-units-min", "value"),
                          Input("num-units-max", "value"),
                          #Input("clear-properties-button", "n_clicks"),
                          Input("map-deal", "relayoutData")
                      ],
                      [
                          State("msa-prop-store", "data"),
                          State("rg-store", "data")
                      ],
                      )
def update_map_deal(market, upside_dropdown, loan_dropdown, overlay, demo_dropdown, loc_dropdown, year_built_min, year_built_max, num_units_min, num_units_max, mapdata, msa_store, rg_store):

    # check for triggered inputs / states
    ctx = dash.callback_context
    print("triggered id", ctx.triggered_id)

    coords = [0,0]

    # Default layout - Continental USA
    coords[0] = 37.0902
    coords[1] = -95.7129
    zoom = 3

    if mapdata is not None:

        if len(mapdata) > 1 and 'mapbox.center' in mapdata and 'mapbox.zoom' in mapdata:

            # set coords
            coords[0] = mapdata['mapbox.center']['lat']
            coords[1] = mapdata['mapbox.center']['lon']

            # set zoom level
            zoom = mapdata['mapbox.zoom']

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

    # Set flag to check if market is triggered
    msa_ctx = False

    if market is not None and market in Market_List or ctx.triggered_id == 'market-deal' and ctx.triggered[0]['value'] in Market_List:
    #if ctx.triggered_id == 'market-deal' and ctx.triggered[0]['value'] in Market_List:

        # Update market select flag
        msa_ctx = True

        lat, long = get_geocodes(market.split('-')[0] + ' ,United States')
        coords[0] = lat
        coords[1] = long
        zoom = 10

        print(coords)

    # Reset to default coords when market cleared
    elif market is None and market not in Market_List or ctx.triggered_id == 'market-deal' and ctx.triggered[0]['value'] == '':

        datad.clear()
        df_msa = pd.DataFrame({})

        # Update market select Flag
        msa_ctx = False

        # Default view - US continental
        coords[0] = 37.0902
        coords[1] = -95.7129
        zoom = 3

    if market is not None and market in Market_List or ctx.triggered_id == 'market-deal':

        # Market is selected, not triggered.
        if mapdata is not None: #and ctx.triggered_id != 'market-deal' and ctx.triggered[0]['prop_id'] == 'map-deal.relayoutData':

            #print('set coords market selected not triggered')

            if len(mapdata) > 1 and 'mapbox.center' in mapdata and 'mapbox.zoom' in mapdata:

                print("mapdata", mapdata)

                # set coords
                coords[0] = mapdata['mapbox.center']['lat']
                coords[1] = mapdata['mapbox.center']['lon']

                # set zoom level
                zoom = mapdata['mapbox.zoom']

        # Find properties within 10 mile radius
        query = '''
                select Property_Name,
                       Property_Type,
                       Year_Built,
                       Size,
                       Address,
                       City,
                       State,
                       Zip_Code,
                       Lat,
                       `Long`,
                       Image_dicts,
                       diff_potential,
                       Loan_Status,
                       Deal_Type,
                       Loan_Seller,
                       EstRentableArea,
                       EstValue,
                       zrent_quantile_random,
                       zrent_median,
                       Preceding_Fiscal_Year_Revenue,
                       Preceding_Fiscal_Year_Operating_Expenses,
                       Most_Recent_Physical_Occupancy,
                       Cap_Rate_Iss,
                       PartyOwner1NameFull,
                       lastSaleDate,
                       lastSalePrice
                from stroom_main.usgeodata_july_v1
                where st_distance_sphere(Point({},{}), coords) <= {};
                '''.format(coords[1], coords[0], 1609*10)

        df_msa = pd.read_sql(query, con)

    # check previously queried from datastore
    #elif msa_ctx == False and msa_store:
    #    print('msa store')
    #    df_msa = pd.DataFrame.from_dict(msa_store)

    else:
        df_msa = pd.DataFrame({})

    print("df_msa", df_msa.shape)

    # Apply filters
    if df_msa.shape[0] > 0:

        if year_built_min and year_built_max or ctx.triggered_id in ["year-built-min", "year-built-max"]:
            df_msa['Year_Built'] = df_msa['Year_Built'].astype(float).astype(int)
            df_msa = df_msa[(df_msa['Year_Built'] >= int(year_built_min)) & (df_msa['Year_Built'] <= int(year_built_max))]

        if num_units_min and num_units_max or ctx.triggered_id in ["num-units-min", "num-units-max"]:
            df_msa['Size'] = df_msa['Size'].astype(float).astype(int)
            df_msa = df_msa[(df_msa['Size'] >= int(num_units_min)) & (df_msa['Size'] <= int(num_units_max))]

        # Generate Address string
        df_msa['Zip_Code'] = df_msa['Zip_Code'].astype(float).astype(int)

        addr_cols = ["Address", "City", "State", "Zip_Code"]
        df_msa['Address_Comp'] = df_msa[addr_cols].apply(lambda row: ' '.join(row.values.astype(str)), axis=1)

        # Filter by potential upside
        df_msa['diff_potential'] = df_msa['diff_potential'].astype(float)
        df1 = df_msa[(df_msa['diff_potential'] >= 0) & (df_msa['diff_potential'] <= 80)]

        # Categorical potential upside
        df1['upside_cat'] = pd.cut(df1['diff_potential'], bins=[0, 10, 30, 80], labels=['Low', 'Medium', 'High'])

        # User upside filter
        if upside_dropdown or ctx.triggered_id == "upside-deal":
            if upside_dropdown == "0-10":
                df1 = df1[(df1['diff_potential'] >= 0) & (df1['diff_potential'] <= 9)]
            elif upside_dropdown == "10-30":
                df1 = df1[(df1['diff_potential'] >= 10) & (df1['diff_potential'] <= 25)]
            elif upside_dropdown == "30+":
                df1 = df1[(df1['diff_potential'] > 25)]

        if loan_dropdown or ctx.triggered_id == "loan-deal":
            if loan_dropdown == "Performing":
                df1 = df1[(df1['Loan_Status'] == loan_dropdown)]
            elif loan_dropdown == "Paid in full":
                df1 = df1[(df1['Loan_Status'] == loan_dropdown)]
            elif loan_dropdown == "Loss":
                df1 = df1[(df1['Loan_Status'] == loan_dropdown)]
            elif loan_dropdown == "Significant Loss":
                df1 = df1[(df1['Loan_Status'] == loan_dropdown)]
            elif loan_dropdown == "Performing, Watchlisted":
                df1 = df1[(df1['Loan_Status'] == loan_dropdown)]
            elif loan_dropdown == "Paid in full, Defeased":
                df1 = df1[(df1['Loan_Status'] == loan_dropdown)]
            elif loan_dropdown == "Performing, Specially Serviced":
                df1 = df1[(df1['Loan_Status'] == loan_dropdown)]
            elif loan_dropdown == "Defeased":
                df1 = df1[(df1['Loan_Status'] == loan_dropdown)]

        # Format columns
        df1['Zip_Code'] = df1['Zip_Code'].astype(float).apply('{:.0f}'.format)
        df1['Size'] = df1['Size'].astype(float).apply('{:.0f}'.format)
        df1['Year_Built'] = df1['Year_Built'].astype(float).apply('{:.0f}'.format)
        df1['EstValue'] = df1['EstValue'].astype(float).apply('${:,.0f}'.format)
        df1['zrent_median'] = df1['zrent_median'].astype(float).apply('${:.0f}'.format)
        df1['Preceding_Fiscal_Year_Revenue'] = df1['Preceding_Fiscal_Year_Revenue'].astype(float).apply('${:,.0f}'.format)

        df1['Preceding_Fiscal_Year_Operating_Expenses'] = df1['Preceding_Fiscal_Year_Operating_Expenses'].apply(clean_currency)
        df1['Preceding_Fiscal_Year_Operating_Expenses'] = df1['Preceding_Fiscal_Year_Operating_Expenses'].astype(float).apply('${:,.0f}'.format)

        df1['Most_Recent_Physical_Occupancy'] = df1['Most_Recent_Physical_Occupancy'].apply(clean_percent).astype(float).apply('{:.0f}%'.format)

        df1['EstRentableArea'] = df1['EstRentableArea'].astype(float).apply('{:,.0f}'.format)

        df1['lastSaleDate'] = pd.to_datetime(df1['lastSaleDate'], infer_datetime_format=True, errors="coerce")
        df1['lastSaleDate'] = df1['lastSaleDate'].dt.strftime('%Y-%m-%d')

        # Drop duplicates
        df1.drop_duplicates(subset=['Property_Name','Zip_Code','Year_Built'], inplace=True)

        # Hover Info
        propname = df1['Property_Name']

        # Columns for customdata
        cd_cols = ['Property_Name','Address_Comp','Zip_Code','Size','Year_Built','Property_Type','zrent_quantile_random','zrent_median','Preceding_Fiscal_Year_Revenue','Preceding_Fiscal_Year_Operating_Expenses','Most_Recent_Physical_Occupancy','EstRentableArea','EstValue','Cap_Rate_Iss','Loan_Status','Deal_Type','Loan_Seller','PartyOwner1NameFull','lastSaleDate','lastSalePrice','upside_cat']

        datad.append({

                        "type": "scattermapbox",
                        "lat": df1['Lat'],
                        "lon": df1['Long'],
                        "name": "Location",
                        "hovertext": df1['Property_Name'],
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
                            "colorscale": "YlOrRd",
                            "cmin": df1['diff_potential'].min(),
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


    # Choroplethmapbox
    if demo_dropdown is not None and demo_dropdown != "" and market is not None and market in Market_List:

        geo_level = None

        if mapdata is not None:

            if len(mapdata) > 1 and 'mapbox.center' in mapdata and 'mapbox.zoom' in mapdata:

                print('demo dd mapdata', mapdata)

                # set coords
                coords[0] = mapdata['mapbox.center']['lat']
                coords[1] = mapdata['mapbox.center']['lon']

                # set zoom level
                zoom = mapdata['mapbox.zoom']

        if demo_dropdown == "RentGrowth":

            if ctx.triggered[0]['value'] == 'RentGrowth':
                # Query rental growth data
                query = '''
                        select MsaName, zip_code, AVG(pct_change) AS avg_rent_growth, ST_AsText(geometry) as geom
                        from stroom_main.gdf_rent_growth_july
                        GROUP BY MsaName, zip_code, geometry
                        HAVING st_distance_sphere(Point({},{}), ST_Centroid(geometry)) <= {};
                        '''.format(coords[1], coords[0], 1609*25)

                # To pandas
                df_rg = pd.read_sql(query, con)

                df_rg['avg_rent_growth'] = round(df_rg['avg_rent_growth']*100,2)

            # Read from local memory / storage
            elif rg_store is not None:

                df_rg = pd.DataFrame.from_dict(rg_store['RentGrowth'])

            else:
                df_rg = pd.DataFrame({})

            if df_rg.shape[0] > 0:
                # To GeoPandas
                df_rg['geom'] = gpd.GeoSeries.from_wkt(df_rg['geom'])
                gdf_rg = gpd.GeoDataFrame(df_rg, geometry='geom')

                s = gdf_rg['avg_rent_growth'].astype(float)
                label = "Rent Growth (% YoY)"

                geo_level = "zip"
                cscale = "Portland"

        # Volatility Index
        elif demo_dropdown == "Volatility":

            if ctx.triggered[0]['value'] == 'Volatility':
                # Query rental growth data
                query = '''
                        select MsaName, zip_code, STD(pct_change) AS std_rent_growth, ST_AsText(geometry) as geom
                        from stroom_main.gdf_rent_growth_july
                        GROUP BY MsaName, zip_code, geometry
                        HAVING st_distance_sphere(Point({},{}), ST_Centroid(geometry)) <= {};
                        '''.format(coords[1], coords[0], 1609*25)

                # To panads
                df_rg = pd.read_sql(query, con)

                df_rg['std_rent_growth'] = round(df_rg['std_rent_growth']*100,2)

            elif rg_store is not None:

                df_rg = pd.DataFrame.from_dict(rg_store['Volatility'])

            else:

                df_rg = pd.DataFrame({})

            if df_rg.shape[0] > 0:
                # To GeoPandas
                df_rg['geom'] = gpd.GeoSeries.from_wkt(df_rg['geom'])
                gdf_rg = gpd.GeoDataFrame(df_rg, geometry='geom')

                s = gdf_rg['std_rent_growth'].astype(float)
                label = "Volatility"

                geo_level = "zip"
                cscale = "Portland"

        elif demo_dropdown == "Home":

            query = '''
                    select Median_Home_Value_2019, tract_geom, tract_ce, lsad_name
                    from stroom_main.usgeodata_july_v1
                    where MSA IN ('{}')
                    '''.format(market)

            dfc = pd.read_sql(query, con)
            dfc =  dfc[dfc['tract_geom'].notna()]

            dfc['tract_geom'] = dfc.tract_geom.apply(valid_geoms)
            dfc = dfc[dfc['tract_geom'].notna()]

            # Convert to GeoDataFrame
            gdfc = gpd.GeoDataFrame(dfc, geometry='tract_geom', crs='epsg:4326')

            gdfc['Median_Home_Value_2019'] = gdfc['Median_Home_Value_2019'].astype(float)
            gdfc = gdfc[gdfc['Median_Home_Value_2019'] > 100000]
            s = gdfc['Median_Home_Value_2019']
            label = "Median Home Value"
            geo_level = "census"


        elif demo_dropdown == "Pop":

            query = '''
                    select Population_2019, tract_geom, tract_ce, lsad_name
                    from stroom_main.usgeodata_july_v1
                    where MSA IN ('{}');
                    '''.format(market)

            dfc = pd.read_sql(query, con)
            dfc =  dfc[dfc['tract_geom'].notna()]

            dfc['tract_geom'] = dfc.tract_geom.apply(valid_geoms)
            dfc = dfc[dfc['tract_geom'].notna()]

            # Convert to GeoDataFrame
            gdfc = gpd.GeoDataFrame(dfc, geometry='tract_geom', crs='epsg:4326')

            gdfc['Population_2019'] = gdfc['Population_2019'].astype(float)
            gdfc = gdfc[gdfc['Population_2019'] > 0]
            s = gdfc['Population_2019']
            label = "Population"
            geo_level = "census"

        elif demo_dropdown == "Income":

            query = '''
                    select Median_HH_Income_2019, tract_geom, tract_ce, lsad_name
                    from stroom_main.usgeodata_july_v1
                    where MSA IN ('{}');
                    '''.format(market)

            dfc = pd.read_sql(query, con)
            dfc =  dfc[dfc['tract_geom'].notna()]

            dfc['tract_geom'] = dfc.tract_geom.apply(valid_geoms)
            dfc = dfc[dfc['tract_geom'].notna()]

            # Convert to GeoDataFrame
            gdfc = gpd.GeoDataFrame(dfc, geometry='tract_geom', crs='epsg:4326')

            gdfc['Median_HH_Income_2019'] = gdfc['Median_HH_Income_2019'].astype(float)
            gdfc = gdfc[gdfc['Median_HH_Income_2019'] > 25000]
            s = gdfc['Median_HH_Income_2019']
            label = "Median Income"
            geo_level = "census"


        elif demo_dropdown == "Income-change":

            query = '''
                    select median_hh_income_percent_change, tract_geom, tract_ce, lsad_name
                    from stroom_main.usgeodata_july_v1
                    where MSA IN ('{}');
                    '''.format(market)

            dfc = pd.read_sql(query, con)
            dfc =  dfc[dfc['tract_geom'].notna()]

            dfc['tract_geom'] = dfc.tract_geom.apply(valid_geoms)
            dfc = dfc[dfc['tract_geom'].notna()]

            # Convert to GeoDataFrame
            gdfc = gpd.GeoDataFrame(dfc, geometry='tract_geom', crs='epsg:4326')

            gdfc['median_hh_income_percent_change'] = gdfc['median_hh_income_percent_change'].astype(float)
            gdfc = gdfc[(gdfc['median_hh_income_percent_change'] > -20) & (gdfc['median_hh_income_percent_change'] < 100)]
            s = gdfc['median_hh_income_percent_change']
            label = "Income Change (%)"
            geo_level = "census"


        elif demo_dropdown == "Pop-change":

            query = '''
                    select population_percent_change, tract_geom, tract_ce, lsad_name
                    from stroom_main.usgeodata_july_v1
                    where MSA IN ('{}');
                    '''.format(market)

            dfc = pd.read_sql(query, con)
            dfc =  dfc[dfc['tract_geom'].notna()]

            dfc['tract_geom'] = dfc.tract_geom.apply(valid_geoms)
            dfc = dfc[dfc['tract_geom'].notna()]

            # Convert to GeoDataFrame
            gdfc = gpd.GeoDataFrame(dfc, geometry='tract_geom', crs='epsg:4326')

            gdfc['population_percent_change'] = gdfc['population_percent_change'].astype(float)
            gdfc = gdfc[(gdfc['population_percent_change'] > -20) & (gdfc['population_percent_change'] < 100)]
            s = gdfc['population_percent_change']
            label = "Population Change (%)"
            geo_level = "census"

        elif demo_dropdown == "Home-value-change":

            query = '''
                    select median_home_value_percent_change, tract_geom, tract_ce, lsad_name
                    from stroom_main.usgeodata_july_v1
                    where MSA IN ('{}');
                    '''.format(market)

            dfc = pd.read_sql(query, con)
            dfc =  dfc[dfc['tract_geom'].notna()]

            dfc['tract_geom'] = dfc.tract_geom.apply(valid_geoms)
            dfc = dfc[dfc['tract_geom'].notna()]

            # Convert to GeoDataFrame
            gdfc = gpd.GeoDataFrame(dfc, geometry='tract_geom', crs='epsg:4326')

            gdfc['median_home_value_percent_change'] = gdfc['median_home_value_percent_change'].astype(float)
            gdfc = gdfc[(gdfc['median_home_value_percent_change'] > -20) & (gdfc['median_home_value_percent_change'] < 100)]
            s = gdfc['median_home_value_percent_change']
            label = "Home Value Change (%)"
            geo_level = "census"

        elif demo_dropdown == "Price_Rent_Ratio":

            query = '''
                    select (Median_Home_Value_2019)/((zrent_median)*12) as price_rent_ratio, tract_geom, tract_ce, lsad_name
                    from stroom_main.usgeodata_july_v1
                    where MSA IN ('{}');
                    '''.format(market)

            dfc = pd.read_sql(query, con)
            dfc =  dfc[dfc['tract_geom'].notna()]

            dfc['tract_geom'] = dfc.tract_geom.apply(valid_geoms)
            dfc = dfc[dfc['tract_geom'].notna()]

            # Convert to GeoDataFrame
            gdfc = gpd.GeoDataFrame(dfc, geometry='tract_geom', crs='epsg:4326')

            gdfc['price_rent_ratio'] = gdfc['price_rent_ratio'].astype(float)
            gdfc = gdfc[(gdfc['price_rent_ratio'] > 0) & (gdfc['price_rent_ratio'] < 80)]
            s = gdfc['price_rent_ratio']
            label = "Price to Rent Ratio"
            geo_level = "census"

        elif demo_dropdown == "Bachelor":

            query = '''
                    select Bachelors_Degree_2019, tract_geom, tract_ce, lsad_name
                    from stroom_main.usgeodata_july_v1
                    where MSA IN ('{}');
                    '''.format(market)

            dfc = pd.read_sql(query, con)
            dfc =  dfc[dfc['tract_geom'].notna()]

            dfc['tract_geom'] = dfc.tract_geom.apply(valid_geoms)
            dfc = dfc[dfc['tract_geom'].notna()]

            # Convert to GeoDataFrame
            gdfc = gpd.GeoDataFrame(dfc, geometry='tract_geom', crs='epsg:4326')

            gdfc['Bachelors_Degree_2019'] = gdfc['Bachelors_Degree_2019'].astype(float)
            gdfc = gdfc[gdfc['Bachelors_Degree_2019'] > 100]
            s = gdfc['Bachelors_Degree_2019']
            label = "Bachelor\'s Degree"
            geo_level = "census"

        elif demo_dropdown == "Graduate":

            query = '''
                    select Graduate_Degree_2019, tract_geom, tract_ce, lsad_name
                    from stroom_main.usgeodata_july_v1
                    where MSA IN ('{}');
                    '''.format(market)

            dfc = pd.read_sql(query, con)
            dfc =  dfc[dfc['tract_geom'].notna()]

            dfc['tract_geom'] = dfc.tract_geom.apply(valid_geoms)
            dfc = dfc[dfc['tract_geom'].notna()]

            # Convert to GeoDataFrame
            gdfc = gpd.GeoDataFrame(dfc, geometry='tract_geom', crs='epsg:4326')

            gdfc['Graduate_Degree_2019'] = gdfc['Graduate_Degree_2019'].astype(float)
            gdfc = gdfc[gdfc['Graduate_Degree_2019'] > 0]
            s = gdfc['Graduate_Degree_2019']
            label = "Graduate Degree"
            geo_level = "census"

        # Clear scattermapbox - properties layer
        if not overlay:
            datad.clear()

        if geo_level == "census":

            datad.append({

                            "type": "choroplethmapbox",
                            "geojson": gdfc.__geo_interface__,
                            "locations": gdfc['tract_ce'],
                            "z": s,
                            "featureidkey": "properties.tract_ce",
                            "hovertext": gdfc['lsad_name'],
                            "autocolorscale":False,
                            "colorscale":"Portland",
                            "colorbar":dict(
                                            title = dict(text=label,
                                                         font=dict(size=12)
                                                        ),
                                            orientation = 'v',
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
                            "marker": dict(opacity = 0.6),
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
                                            orientation = 'v',
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
                            "marker": dict(opacity = 0.6),
                            "marker_line_width": 0,
                            "opacity": 0.2,
                            "labels": label,
                            "title": "Choropleth - Zip Code Level"

                         }
            )

    # Location data layer
    if loc_dropdown is not None and market is not None and loc_dropdown != "" or ctx.triggered_id == "location-deal" and loc_dropdown is not None and loc_dropdown != "":

        zoom = 12

        if mapdata is not None:

            if len(mapdata) > 1 and 'mapbox.center' in mapdata and 'mapbox.zoom' in mapdata:

                # set coords
                coords[0] = mapdata['mapbox.center']['lat']
                coords[1] = mapdata['mapbox.center']['lon']

                # set zoom level
                if mapdata['mapbox.zoom'] < 11:
                    zoom = mapdata['mapbox.zoom'] + (11 - mapdata['mapbox.zoom'])
                else:
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

               print("datad loc dd")
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
                                         "opacity": 0.6,
                                         "color": "blue"
                                        }
                              }
               )

    layout = {

                 "autosize": False,
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

    if len(datad) > 0:

        # If clear properties - eject scattermapbox property layer
        # if clear_properties_nclicks > 0:
        #     for d in datad:
        #         if d['type'] == 'scattermapbox':
        #             datad.remove(d)

        # Rearrange so that scattermapbox is top layer
        for i in range(len(datad)):
            if datad[i]['type'] == 'scattermapbox':
                datad.append(datad.pop(datad.index(datad[i])))

        if market is not None and df_msa.shape[0] > 0 and demo_dropdown is None and loc_dropdown is None:
            print('return case #1 - market selected, show properties')

            return ({"data": datad, "layout": layout}, df1.to_dict("records"), "Property Count:{}".format(df1.shape[0]), df_msa.to_dict('records'), no_update)

        elif market is not None and market in Market_List and demo_dropdown is not None:
            print('return case #2 - market selected and demo dropdown')

            demo_store = no_update

            if demo_dropdown in ['RentGrowth', 'Volatility']:
                # Polygon to strings
                df_rg['geom'] = df_rg.geom.apply(lambda x: wkt.dumps(x))

                demo_store = {demo_dropdown : df_rg.to_dict("records")}
            else:
                demo_store = no_update

            return ({"data": datad, "layout": layout}, df1.to_dict("records"), "Property Count: {}".format(df1.shape[0]), df_msa.to_dict("records"), demo_store)

        elif market is not None and market in Market_List and loc_dropdown is not None:
            print('return case #3 - market selected and location dropdown')
            return ({"data": datad, "layout": layout}, no_update, no_update, no_update, no_update)

    elif len(data_def) > 0 and market is None:
        print('return case #4 - data default')
        datad.clear()
        return ({"data": data_def, "layout": layout}, no_update, "Property Count: {}".format(0), no_update, no_update)

    else:
        print('return case #5 - final else')
        datad.clear()
        return ({"data": data_def, "layout": layout}, no_update, "Property Count: {}".format(0), no_update, no_update)



# Reset dropdowns upon market change OR clerance
@application.callback(
                        [
                            Output("upside-deal", "value"),
                            Output("upside-deal", "disabled"),

                            Output("loan-deal", "value"),
                            Output("loan-deal", "disabled"),

                            Output("overlay", "value"),

                            Output("demo-deal", "value"),
                            Output("demo-deal", "disabled"),

                            Output("location-deal", "value"),
                            Output("location-deal", "disabled"),

                            Output("year-built-min", "value"),
                            Output("year-built-min", "disabled"),
                            Output("year-built-max", "value"),
                            Output("year-built-max", "disabled"),

                            Output("num-units-min", "value"),
                            Output("num-units-min", "disabled"),
                            Output("num-units-max", "value"),
                            Output("num-units-max", "disabled"),

                        ],
                        [
                            Input("market-deal", "value")
                            #Input("show-properties-button", "n_clicks")
                        ],
                     )
def reset_selections(market):

    ctx = dash.callback_context

    print('reset selections callback')

    # Disable filters until market is selected
    if market is None or ctx.triggered_id == "market-deal" and ctx.triggered[0]['value'] == '':
        return ("", True, "", True, "", "", True, "", True, "", True, "", True, "", True, "", True)
    else:
        return (no_update, False, no_update, False, no_update, no_update, False, no_update, False, no_update, False, no_update, False, no_update, False, no_update, False)



# Update comps modal on click event
@application.callback(
                          [
                               # Modal Comps
                               Output("modal-1-deal","is_open"),
                               Output("carousel_deal","children"),

                               # Upside indicator
                               Output("card-text-deal", "children"),
                               Output("card-img-deal", "src"),

                               Output("prop_name_deal","children"),
                               Output("Address_deal","children"),
                               Output("Size_deal","children"),
                               Output("Yr_Built_deal","children"),
                               Output("Property_deal","children"),
                               Output("Rent_deal", "children"),
                               Output("Revenue_deal","children"),
                               Output("Opex_deal","children"),
                               Output("occ-modal_deal","children"),
                               Output("rent-area-modal_deal","children"),
                               Output("assessed-value_deal","children"),
                               Output("cap-rate_deal","children"),
                               Output("loan-status_deal","children"),
                               Output("deal-type_deal","children"),
                               Output("loan-seller_deal","children"),
                               Output("owner-info_deal","children"),
                               Output("sale-date_deal","children"),
                               Output("sale-price_deal","children")

                          ],

                          [
                               # Button clicks
                               Input("map-deal","clickData"),
                               Input("close_deal","n_clicks")

                          ],

                          [
                                State("modal-1-deal", "is_open"),
                                State("msa-prop-store", "data")
                          ],
                    )
def display_popup2(clickData, n_clicks, is_open, msa_store):

    if clickData and "customdata" in clickData["points"][0]:

        res = json.dumps(clickData, indent=2)

        print("clickData response", res)

        Name = clickData["points"][0]["customdata"][0]
        Address = clickData["points"][0]["customdata"][1]
        Zip = clickData["points"][0]["customdata"][2]
        Size = clickData["points"][0]["customdata"][3]
        Built = clickData["points"][0]["customdata"][4]
        Property = clickData["points"][0]["customdata"][5]

        '''
        Rents data
        '''
        # Rents Quantiles
        rent_quantiles = clickData["points"][0]["customdata"][6]

        rent_median = clickData["points"][0]["customdata"][7]

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

        Revenue = clickData["points"][0]['customdata'][8]
        Opex = clickData["points"][0]['customdata'][9]
        Occupancy = clickData["points"][0]["customdata"][10]
        RentArea = clickData["points"][0]["customdata"][11]
        AssessedValue = clickData["points"][0]["customdata"][12]
        CapRate = clickData["points"][0]["customdata"][13]
        LoanStatus = clickData["points"][0]["customdata"][14]
        DealType = clickData["points"][0]["customdata"][15]
        LoanSeller = clickData["points"][0]["customdata"][16]
        OwnerInfo = clickData["points"][0]["customdata"][17]
        lastSaleDate = clickData["points"][0]["customdata"][18]
        lastSalePrice = clickData["points"][0]["customdata"][19]
        upsideCat = clickData["points"][0]["customdata"][20]

        # Dictionary to pandas DataFrame
        if msa_store:
            df_msa = pd.DataFrame.from_dict(msa_store)
            print("df msa", df_msa.shape)

            # Construct a list of dictionaries
            # Filter Pandas DataFrame
            df = df_msa[df_msa['Property_Name'] == Name]

            index = df.index[0]
            img_dict = df['Image_dicts'][index]
        else:
            img_dict = 0


        # Construct carousel object
        try:

            if type(img_dict) is str and img_dict != "0":

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
            print('Exception', e)
            url = create_presigned_url('gmaps-images-6771', 'property_images/no_imagery.png')

            carousel = dbc.Carousel(
                                    items=[
                                            {"key": "1", "src": url, "img_style": {"width": "300px", "height": "300px"}},
                                    ],
                                    controls=False,
                                    indicators=False,
                        )

        # Formatted Rent for default view (NA) and calculated / post button click and handling of None values
        if upsideCat in ["null", None, 0, "0", 0.0, "0.0"]:
            upsideCat_src = no_update
            upsideCat_txt = no_update
        elif upsideCat == "High":
            upsideCat_src = "https://stroom-images.s3.us-west-1.amazonaws.com/high-growth.png"
            upsideCat_txt = "High Upside Potential (> 25%+)"
        elif upsideCat == "Medium":
            upsideCat_src = "https://stroom-images.s3.us-west-1.amazonaws.com/average_chart.png"
            upsideCat_txt = "Medium Upside Potential (10% - 25%)"
        elif upsideCat == "Low":
            upsideCat_src = "https://stroom-images.s3.us-west-1.amazonaws.com/low-growth.png"
            upsideCat_txt = "Low Upside Potential (< 10%)"

        if Built in ["null", None, 0, "0", 0.0, "0.0"]:
            Built_fmt = "N/A"
        else:
            Built_fmt = Built

        if Revenue in ["null", None, 0, "0", 0.0, "0.0"]:
            Revenue_fmt = "N/A"
        else:
            Revenue = clean_currency(Revenue)
            Revenue_fmt = "${:,.0f}".format(float(Revenue))

        if Opex in ["null", None, 0, "0", 0.0, "0.0"]:
            Opex_fmt = "N/A"
        else:
            Opex = clean_currency(Opex)
            Opex_fmt = "${:,.0f}".format(float(Opex))

        if Occupancy in ["null", None, 0, "0", 0.0, "0.0", "0%", "0.0%"]:
            Occupancy_fmt = "N/A"
        else:
            Occupancy = clean_percent(Occupancy)
            Occupancy = float(Occupancy)
            Occupancy_fmt = "{:.0f}%".format(Occupancy)

        if RentArea in ["null", None, 0, "0", 0.0, "0.0"]:
            RentArea_fmt = "N/A"
        else:
            RentArea = RentArea.replace(',','')
            RentArea_fmt = "{:,.0f} sq.ft".format(float(RentArea))

        if AssessedValue in ["null", None, 0, "0", 0.0, "0.0"]:
            AssessedValue_fmt = "N/A"
        elif type(AssessedValue) != str:
            AssessedValue_fmt = "${:,.0f}".format(AssessedValue)
        else:
            AssessedValue_fmt = AssessedValue

        if CapRate in ["null", None, 0, "0", 0.0, "0.0"]:
            CapRate_fmt = "N/A"
        elif type(CapRate) != str:
            CapRate = CapRate * 100
            CapRate_fmt = "{:,.2f}%".format(CapRate)
        elif type(CapRate) == str:
            CapRate = float(CapRate) * 100
            CapRate_fmt = "{:,.2f}%".format(CapRate)
        else:
            CapRate_fmt = CapRate

        if LoanStatus in ["null", None, 0, "0", 0.0, "0.0"]:
            LoanStatus_fmt = "N/A"
        else:
            LoanStatus_fmt = LoanStatus

        if DealType in ["null", None, 0, "0", 0.0, "0.0"]:
            DealType_fmt = "N/A"
        else:
            DealType_fmt = DealType

        if LoanSeller in ["null", None, 0, "0", 0.0, "0.0"]:
            LoanSeller_fmt = "N/A"
        else:
            LoanSeller_fmt = LoanSeller

        if OwnerInfo in ["null", None, 0, "0", 0.0, "0.0"]:
            OwnerInfo_fmt = "N/A"
        else:
            OwnerInfo_fmt = OwnerInfo

        if lastSaleDate in ["null", None, 0, "0", 0.0, "0.0"]:
            lastSaleDate_fmt = "N/A"
        else:
            lastSaleDate_fmt = lastSaleDate.split(' ')[0]

        if lastSalePrice in ["null", None, 0, "0", 0.0, "0.0"]:
            lastSalePrice_fmt = "N/A"
        elif isinstance(lastSalePrice, str) == True:
            lastSalePrice =  float(lastSalePrice)
            # Bad SalePrice
            if lastSalePrice <= 100000:
                lastSalePrice_fmt = "N/A"
            else:
                lastSalePrice_fmt = "${:,.0f}".format(lastSalePrice)
        else:
            lastSalePrice_fmt = "N/A"

        return(not is_open, carousel, upsideCat_txt, upsideCat_src, Name, Address, Size, Built_fmt, Property, Rents_fmt, Revenue_fmt, Opex_fmt, Occupancy_fmt, RentArea_fmt, AssessedValue_fmt, CapRate_fmt, LoanStatus_fmt, DealType_fmt, LoanSeller_fmt, OwnerInfo_fmt, lastSaleDate_fmt, lastSalePrice_fmt)

    elif n_clicks:
        print('ok modal')
        return is_open

    else:
        return no_update

# Storage component
@application.callback(Output("modal-store","data"),
                      [
                        Input("map-deal","clickData")
                        #Input("returns_btn","n_clicks")
                      ]
                     )
def modal_returns_click(clickData):

    if clickData:

        return clickData
