# Packages
import pandas as pd
import numpy as np
import dash
from dash.dependencies import Input, Output, State
from dash import dcc
from dash import html, dash_table
import dash_bootstrap_components as dbc
import plotly as py
from plotly import graph_objs as go
from plotly.graph_objs import *
import plotly.figure_factory as ff
import flask
from flask import Flask
from application import application
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from collections import defaultdict
import mapbox
import geopandas as gpd
import shapely.geometry
from scipy import spatial
from dash.dash import no_update
from dash.exceptions import PreventUpdate
from base_rent_calc import calc_rent, walkscore
from handle_images import getPlace_details
from funcs import clean_percent, clean_currency, get_geocodes, nearby_places, streetview, create_presigned_url, gen_ids, str_num, listToDict, prox_mean, attom_api_avalue, sym_dict
from draw_polygon import poi_poly
from sklearn.neighbors import BallTree
from parse import parse_contents
import string
import json
import os
import os.path
import ast
import random
import requests
import geocoder
import pygeohash as gh
import google_streetview.api

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

# Run query
query = '''
        select *
        from stroom_main.df_raw_v1_march
        where City = 'San Francisco'
        and avg_price < 10000
        and Size >= 50
        LIMIT 25
        '''

df = pd.read_sql(query, con)

# App Layout for designing the page and adding elements
layout = html.Div([

   dbc.Row(
       [
         dbc.Col(

            html.Div([

                # Plot properties map
                dcc.Graph(id="map-graph1",
                          style={"display": "inline-block", "width": "52em", "float": "left", "height":"700px", "margin-left":"0%"}
                          ),

                # Hidden div inside the app that stores the intermediate value
                html.Div(id="price-value", style={"display": "none"}),

                ], className="map-style"),

         width={"size": 2, "order": "first"},),

         # Local level Statistics
         dbc.Row([

                     dbc.Card(
                          [
                              dbc.Row(
                                  [
                                      dbc.Col(
                                          dbc.CardImg(
                                              id="card-img",
                                              #src="/static/images/portrait-placeholder.png",
                                              className="card-img",
                                          ),
                                          className="card-img",
                                      ),

                                      #dbc.CardHeader(id="summary-header"),

                                      dbc.Col(
                                          dbc.CardBody(
                                              [

                                                  html.H4(id="card-header"),
                                                  html.P(
                                                      id="card-text",
                                                      className="card-text",
                                                  ),

                                              ]
                                          ),
                                          className="col-md-8",
                                      ),
                                  ],
                                  className="g-0 d-flex align-items-center",
                              )
                           ],
                           className="summary",
                     ),

                     dbc.Card(
                                 [
                                     dbc.CardHeader("Median Rent"),
                                     dbc.CardBody(
                                         [
                                             html.P(id="rent-card", style={"font-size": "1.6em"}),
                                         ]

                                     ),
                                 ],
                                 id="rent-stat",
                                 color="light",
                                 style={"width": "10rem", "margin-left": "2%", "height": "9em"}
                     ),

                     dbc.Card(
                                 [
                                     dbc.CardHeader("Avg. Occupancy"),
                                     dbc.CardBody(
                                         [
                                             html.P(id="occ-card", style={"font-size": "2em"}),
                                         ]

                                     ),
                                 ],
                                 id="occ-stat",
                                 color="light",
                                 style={"width": "10rem", "margin-left": "2%", "height": "9em"}
                     ),

                     dbc.Card(
                                 [
                                     dbc.CardHeader("Avg. Opex /Mo."),
                                     dbc.CardBody(
                                         [
                                             html.P(id="opex-card", style={"font-size": "2em"}),
                                         ]

                                     ),
                                 ],
                                 id="opex-stat",
                                 color="light",
                                 style={"width": "10rem", "margin-left": "2%", "height": "9em"}
                     ),

         ], style={"width":"100%", "margin-top":"52em", "margin-left":"16em"}),


         # CMBS pop up
         dbc.Col([

            # dbc popup / modal - comps
            html.Div([

                dbc.Modal(
                    [
                        dbc.ModalHeader("Property Information", style={"color":"black", "justify-content":"center"}),
                        dbc.ModalBody(
                            [

                                # Images
                                html.Div(id="carousel"),

                                dbc.Label("Property Name:", style={"color":"black", "font-weight": "bold", "margin-right":"10px", "margin-top":"1.5%"}),
                                dbc.Label("Property Name:", id="prop_name"),
                                html.Br(),

                                dbc.Label("Address:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                dbc.Label("Address:", id="Address"),
                                html.Br(),

                                dbc.Label("Number of Units:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                dbc.Label("Size:", id="Size"),
                                html.Br(),

                                dbc.Label("Year Built:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                dbc.Label("Year Built:", id="Yr_Built"),
                                html.Br(),

                                dbc.Label("Avg. Rent:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                dbc.Label("Avg. Rent:", id="Rent_cmbs"),
                                html.Br(),

                                dbc.Label("Fiscal Revenue:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                dbc.Label("Revenue:", id="Revenue"),
                                html.Br(),

                                dbc.Label("Opex:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                dbc.Label("Opex:", id="Opex"),
                                html.Br(),

                                dbc.Label("Occupancy:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                dbc.Label("Occupancy:", id="occ-modal"),
                                html.Br(),

                                dbc.Label("Rentable Area:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                dbc.Label("Rentable Area:", id="rent-area-modal"),
                                html.Br(),

                                dbc.Label("Assessed Value:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                dbc.Label("Assessed Value:", id="assessed-value"),
                                html.Br(),

                                dbc.Label("Last Sale Date:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                dbc.Label("Last Sale Date:", id="sale-date"),
                                html.Br(),

                                dbc.Label("Distance:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                dbc.Label("Distance:", id="distance"),
                                html.Br(),

                            ]
                        ),
                        dbc.ModalFooter(
                            [

                                dbc.Label("Sources: CMBS, CoreLogic", style={"float":"left", "padding-right":"26em", "font-size":"12px"}),

                                dbc.Button("OK", color="primary", size="lg", id="close", className="mr-1"),
                            ]
                        ),
                    ],
                    id="modal-1",
                ),

            ], style={"width": "50%"}),


           # modal popup - zillow
           html.Div([

               dbc.Modal(
                   [
                       dbc.ModalHeader("Property Information", style={"color":"black", "justify-content":"center"}),
                       dbc.ModalBody(
                           [

                               # Images
                               html.Div(id="carousel-z"),

                               dbc.Label("Property Name:", style={"color":"black", "font-weight": "bold", "margin-right":"10px", "margin-top":"1.5%"}),
                               dbc.Label("Property Name:", id="prop_name_z"),
                               html.Br(),

                               dbc.Label("Address:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                               dbc.Label("Address:", id="Address_z"),
                               html.Br(),

                               dbc.Label("Number of Units:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                               dbc.Label("Size:", id="Size_z"),
                               html.Br(),

                               dbc.Label("Year Built:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                               dbc.Label("Year Built:", id="Yr_Built_z"),
                               html.Br(),

                               dbc.Label("Average Rent:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                               dbc.Label("Rent:", id="rent_z"),
                               html.Br(),

                               dbc.Label("Estimated Revenue:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                               dbc.Label("Revenue:", id="Revenue_z"),
                               html.Br(),

                               dbc.Label("Rentable Area:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                               dbc.Label("Rentable Area:", id="rent-area-modal-z"),
                               html.Br(),

                               dbc.Label("Assessed Value:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                               dbc.Label("Assessed Value:", id="assessed-value-z"),
                               html.Br(),

                               dbc.Label("Ameneties:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                               dbc.Label("Ameneties:", id="ameneties_z"),
                               html.Br(),

                               dbc.Label("Distance:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                               dbc.Label("Distance:", id="distance_z"),
                               html.Br(),

                           ]
                       ),
                       dbc.ModalFooter(
                           [

                               dbc.Label("Source: Internet Listings", style={"float":"left", "padding-right":"26em", "font-size":"12px"}),

                               dbc.Button("OK", color="primary", size="lg", id="close-z", className="mr-1"),
                           ]
                       ),
                   ],
                   id="modal-3",
               ),

            ], style={"width": "50%"}),


            # Modal / pop up for subject property
            html.Div([

                dbc.Modal(
                    [
                        dbc.ModalHeader("Property Information", style={"color":"black", "justify-content":"center"}),
                        dbc.ModalBody(
                            [

                                # Images
                                html.Div(id="carousel-s"),

                                dbc.Label("Address:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                dbc.Label("Address:", id="Address-s"),
                                html.Br(),

                                dbc.Label("Number of Units:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                dbc.Label("Size:", id="Size-s"),
                                html.Br(),

                                dbc.Label("Year Built:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                dbc.Label("Year Built:", id="Yr_Built-s"),
                                html.Br(),

                                dbc.Label("Rentable Area:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                dbc.Label("Rentable Area:", id="rent-area-modal-s"),
                                html.Br(),

                                dbc.Label("Expected Fiscal Revenue:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                dbc.Label("Revenue:", id="Revenue-s"),
                                html.Br(),

                                dbc.Label("Assessed Value:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                dbc.Label("Assessed Value:", id="assessed-val-s"),
                                html.Br(),

                                dbc.Label("Property Taxes:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                dbc.Label("Property Taxes:", id="prop-tax-s"),
                                html.Br(),

                            ]
                        ),
                        dbc.ModalFooter(
                            [

                                dbc.Label("Sources: CMBS, CoreLogic", style={"float":"left", "padding-right":"26em", "font-size":"12px"}),

                                dbc.Button("OK", color="primary", size="lg", id="close-s", className="mr-1"),
                            ]
                        ),
                    ],
                    id="modal-2",
                ),

            ], style={"width": "50%"}),



            # Address autocomplete
            html.Div([

                dbc.InputGroup(
                    [

                        dbc.InputGroupAddon("Address"),

                        dcc.Input(id="address_autocomplete",
                                  persistence=True,
                                  persistence_type="memory",
                                  required=True,
                                  style={"width":"72%"}),

                        dcc.Dropdown(id="address_dropdown",
                                     persistence=True,
                                     persistence_type="memory",
                                     placeholder="Address Suggestions",
                                     style={"width":"95%", "display":"inline-block", "font-size" : "70%"})

                    ],
                    style={"margin-top":"0px", "width": "53%", "float": "left"},
                ),

                dbc.InputGroup(
                    [

                       dbc.Label("Property type"),
                       dcc.Dropdown(
                                      id="prop-type",
                                      persistence=True,
                                      persistence_type="memory",
                                      options=[
                                               {"label": "Multi-Family", "value": "Multi-Family"}
                                      ],
                                      value="Multi-Family"
                       ),

                 ],
                 style={"margin-top":"20px","width": "80%", "float": "left"},
                ),


                # Year Built
                dbc.InputGroup(
                    [

                        dbc.InputGroupAddon("Year Built", id="built-text", style={"margin-left":"8px"}),
                        dbc.Input(
                                  id="built",
                                  persistence=True,
                                  persistence_type="memory"
                                 ),

                        dbc.InputGroupAddon("Renovated", id="renovate-text", style={"margin-left":"8px"}),
                        dbc.Input(
                                  id="renovated",
                                  persistence=True,
                                  persistence_type="memory"
                                 ),

                    ],
                    style={"margin-top":"1%","width": "50%", "float": "left"},
                ),


               # Number of Units - Acqusition
               dbc.InputGroup(
                   [

                       dbc.InputGroupAddon("Area(RSF)", id="size-text", style={"margin-left":"8px"}),
                       dbc.Input(
                                 id="space-acq",
                                 persistence=True,
                                 persistence_type="memory"
                                ),

                       dbc.InputGroupAddon("Units", id="size-text", style={"margin-left":"8px"}),
                       dbc.Input(
                                 id="units-acq",
                                 persistence=True,
                                 persistence_type="memory"
                                ),
                   ],

                   id = "layout-acq",
                   style={"margin-top":"1%","width": "50%", "float": "left"},

               ),


               html.Div([

                    dbc.Label("Ameneties", style={"font-size" : "150%"}),
                    dcc.Dropdown(
                            id="ameneties",
                            persistence=True,
                            persistence_type="memory",
                            options=[

                                {"label": "Luxurious", "value": "Luxurious"},
                                {"label": "Garage Parking", "value": "Park"},
                                {"label": "Gym", "value": "Gym"},
                                {"label": "In-unit Laundry", "value": "Laundry"},
                                {"label": "Pool", "value": "Pool"},
                                {"label": "Rent Controlled", "value": "Rent-control"},
                                {"label": "Bike Storage", "value": "Bike"},
                                {"label": "Patio", "value": "Patio"},
                                {"label": "Concierge", "value": "Concierge"},
                                {"label": "Central AirCon", "value": "Heat"},

                            ],
                            value = ["Park", "Gym", "Laundry", "Pool", "Rent-control", "Bike", "Patio", "Concierge", "Heat"],
                            multi=True,
                    ),

                ], style={"height":"40px", "width":"95%", "margin-top": "1.5%", "font-size" : "66%"}),

                html.Div([

                    dbc.Button("Find Comps", id="comps-button", size="lg", className="mr-1"),

                ], style={"width":"70%", "margin-top": "15%"}),


            ], className="prop-style",
               style={"width": "75%", "font-size":"1.08em"}),

        ], width={"size": 10, "order": "last", "offset": 8},),
    ]),


    dbc.Row([

            # # Lease Table
            html.Div([

                dash_table.DataTable(

                    id="comps-table",

                    columns=[{"id":"Property_Name","name":"Property_Name"},
                             {"id":"Zip_Code","name":"Zip_Code"},
                             {"id":"Type","name":"Type"},
                             {"id":"avg_price","name":"Avg. Rent"},
                             {"id":"Preceding_Fiscal_Year_Revenue","name": "Revenue"},
                             {"id":"EstRentableArea","name": "Area (Sq.ft)"},
                             {"id":"Most_Recent_Physical_Occupancy","name":"Occupancy"},
                             {"id":"Year_Built","name": "Year Built"},
                             {"id":"Size","name": "Number of Units"},
                             {"id":"Opex", "name":"Opex (Monthly)"},
                             {'id':"EstValue", "name":"Assessed Value"},
                             {'id':"Distance", "name":"Distance (in miles)"}],

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


            ], className="table-style"),

        ]),

        html.Div(id="dummy-div"),

        dcc.Store(id='result-store', storage_type='memory'),
        dcc.Store(id="api-store", storage_type='memory'),
        dcc.Store(id="query-store", storage_type='memory')

])



# Property address autocomplete
@application.callback(Output("address_dropdown", "options"),
                     [Input("address_autocomplete", "value")])
def autocomplete_address(value):

    if value and len(value) >= 8:

        addr = {}

        # Call mapbox API and limit Autocomplete address suggestions
        ret_obj = Geocoder.forward(value, lon=-122.436029586314, lat=37.7588531529652, limit=3, country=["us"])
        response = ret_obj.json()

        for i in range(len(response["features"])):

            addr["res{}".format(i)] = response["features"][i]["place_name"]

        if len(addr) == 1:

            return [{"label": addr["res0"], "value": addr["res0"]}]

        if len(addr) == 2:

            return [{"label": addr["res0"], "value": addr["res0"]},
                    {"label": addr["res1"], "value": addr["res1"]}]

        if len(addr) == 3:

            return [{"label": addr["res0"], "value": addr["res0"]},
                    {"label": addr["res1"], "value": addr["res1"]},
                    {"label": addr["res2"], "value": addr["res2"]}]

    else:

        return (no_update)



# Set input value to the one selected by dropdown.
@application.callback(Output("address_autocomplete", "value"),
                      [Input("address_dropdown", "value")]
                     )
def resetInput(address):

    return address


# Autopopulate property details fields - mock API
@application.callback([

                        Output("built", "value"),
                        Output("renovated", "value"),
                        Output("space-acq", "value"),
                        Output("units-acq", "value"),
                        Output("api-store", "data")

                      ],
                      [
                        Input("address_dropdown", "value")
                      ]
                     )
def autopopulate_propdetails(address):

    details = None

    if address and len(address) > 8:

        g = geocoder.mapbox(address, key=token)
        geojson = g.json
        addr = geojson["address"]

        coords = [geojson['lat'], geojson['lng']]

        geohashval = gh.encode(geojson['lat'], geojson['lng'], precision=5)

    else:
        raise PreventUpdate


    if geojson:

        # Query to find property in the database - 0.05 miles to meters = 80.47
        query = '''
                select * from stroom_main.df_raw_v1_march
                where st_distance_sphere(Point({},{}), coords) <= {};
                '''.format(geojson['lng'], geojson['lat'], 80.47)

        df_mf = pd.read_sql(query, con)

        # Check if dataframe is not empty and property was found
        if not df_mf.empty:

            details = df_mf[['Year_Built','Renovated','EstRentableArea','Size','Most_Recent_Physical_Occupancy','Operating_Expenses_at_Contribution','propertyTaxAmount','taxRate','Preceding_Fiscal_Year_Revenue','lastSaleDate']].iloc[0].to_list()

            return (int(details[0]), details[1], int(details[2]), int(details[3]), {"attom_api": None, "geohash": geohashval, "propdetails": details})

        else:

            # ATTOM API Call
            avdata = attom_api_avalue(addr)
            avdata = json.loads(avdata.decode("utf-8"))

            if avdata:

                # Year Built
                try:
                    built = avdata['property'][0]['summary']['yearbuilt']
                    built = int(built)
                except Exception as e:
                    built = no_update
                    print(e)
                    pass

                # Area
                try:
                    area = avdata['property'][0]['building']['size']['grosssize']
                    area = int(area)
                except Exception as e:
                    if e == "grosssize":
                        try:
                            area = avdata['property'][0]['lot']['lotsize2']
                            area = int(area)
                        except Exception as e:
                            pass
                    else:
                        area = no_update
                        print(e)
                        pass

                # Units
                try:
                    units = avdata['property'][0]['building']['summary']['unitsCount']
                    units = int(units)
                except Exception as e:
                    units = no_update
                    print(e)
                    pass

            return (built, no_update, area, units, {"attom_api": avdata, "geohash": geohashval, "propdetails": details})

    else:
        raise PreventUpdate



# Update map graph
@application.callback([

                          Output("map-graph1", "figure"),
                          Output("price-value", "value"),
                          Output("dummy-div", "value"),
                          Output("result-store", "data"),
                          Output("query-store", "data")

                      ],
                      [

                          Input("address_dropdown", "value"),
                          Input("prop-type", "value"),
                          Input("built", "value"),
                          Input("units-acq","value"),
                          Input("space-acq","value"),
                          Input("ameneties", "value"),
                          Input("comps-button", "n_clicks")

                      ],
                      [
                          State("comps-store", "data"),
                          State("api-store", "data")
                      ]
             )
def update_graph(address, proptype, built, units_acq, space_acq, ameneties, n_clicks, comps_store, api_store):

    '''
    Update this to adjust map layout.
    Default map view
    '''

    # sf bay area
    layout_lat = 37.7749
    layout_lon = -122.4194

    zoom = 12

    price = 0

    market_price = 0

    details = None

    result = None

    datac = []

    if proptype == "Multi-Family":

        # Generate Address string
        addr_cols = ["Address", "City", "State", "Zip_Code"]

        df['Address_Comp'] = df[addr_cols].apply(lambda row: ' '.join(row.values.astype(str)), axis=1)

        df['EstRevenueMonthly'] = (df['Preceding_Fiscal_Year_Revenue']/df['Size'])/12
        df['Distance'] = "N/A"

        propname = df["Property_Name"]

        # Columns for customdata
        cd_cols = ['Property_Name','Address_Comp','Size','Year_Built','avg_price','Preceding_Fiscal_Year_Revenue','Opex','Occ','EstRentableArea','EstValue','lastSaleDate','Distance']

        datac.append({

                        "type": "scattermapbox",
                        "lat": df['Lat'],
                        "lon": df['Long'],
                        "name": "Location",
                        "hovertext": propname,
                        "showlegend": False,
                        "hoverinfo": "text",
                        "mode": "markers",
                        "clickmode": "event+select",
                        "customdata": df.loc[:,cd_cols].values,
                        "below": "''",
                        "marker": {
                            "symbol": "circle",
                            "size": 8,
                            "opacity": 0.8,
                            "color": "black"
                            }
                     }
        )


        # Global variable for callbacks
        ctx = dash.callback_context

        '''
        Property search
        '''

        if n_clicks:

           # Query to find property within 5 miles radius to create geo-aggregated dicts
           g = geocoder.mapbox(address, key=token)
           geojson = g.json
           addr = geojson["address"]

           query = '''
                   SELECT *
                   FROM stroom_main.df_raw_v1_march
                   WHERE st_distance_sphere(Point({},{}), coords) <= {};
                   '''.format(geojson['lng'], geojson['lat'], 5*1609)

           df_mf = pd.read_sql(query, con)


           datap = []

           # Create geo-aggregated dicts for occupancy, opex, tax rate and tax amount
           occ_geo = dict()
           opex_geo = dict()
           taxRate_geo = dict()
           taxAmt_geo = dict()
           estVal_geo = dict()
           rent1Br_geo = dict()

           for name, group in df_mf.groupby(['geohash']):

               # Occupancy
               group['Most_Recent_Physical_Occupancy'] = group['Most_Recent_Physical_Occupancy'].apply(clean_percent).astype('float')
               occ_geo[name] = group[group['Most_Recent_Physical_Occupancy'] > 0]['Most_Recent_Physical_Occupancy'].mean()
               # Dict to pandas dataframe
               occ_geo_df = pd.DataFrame(zip(occ_geo.keys(), occ_geo.values()), columns=['geohash', 'value'])

               # Opex
               group['Operating_Expenses_at_Contribution'] = group['Operating_Expenses_at_Contribution'].apply(clean_currency).astype('float')
               opex_geo[name] = group[group['Operating_Expenses_at_Contribution'] > 0]['Operating_Expenses_at_Contribution'].mean()
               # Dict to pandas dataframe
               opex_geo_df = pd.DataFrame(zip(opex_geo.keys(), opex_geo.values()), columns=['geohash', 'value'])

               # Tax Rate
               group['taxRate'] = group['taxRate'].apply(clean_percent).astype('float')
               taxRate_geo[name] = group[group['taxRate'] > 0]['taxRate'].mean()
               # Dict to pandas dataframe
               taxRate_geo_df = pd.DataFrame(zip(taxRate_geo.keys(), taxRate_geo.values()), columns=['geohash', 'value'])

               # Property Tax
               group['propertyTaxAmount'] = group['propertyTaxAmount'].apply(clean_currency).astype('float')
               taxAmt_geo[name] = group[group['propertyTaxAmount'] > 0]['propertyTaxAmount'].mean()
               # Dict to pandas dataframe
               taxAmt_geo_df = pd.DataFrame(zip(taxAmt_geo.keys(), taxAmt_geo.values()), columns=['geohash', 'value'])

               # Assessed Value
               group['EstValue'] = group['EstValue'].apply(clean_currency).astype('float')
               estVal_geo[name] = group[group['EstValue'] > 0]['EstValue'].mean()
               # Dict to pandas dataframe
               estVal_geo_df = pd.DataFrame(zip(estVal_geo.keys(), estVal_geo.values()), columns=['geohash', 'value'])

               # Avg. Rents
               group['Rent_1Br'] = group['Rent_1Br'].apply(clean_currency).astype('float')
               rent1Br_geo[name] = group[group['Rent_1Br'] > 0]['Rent_1Br'].mean()
               # Dict to pandas dataframe
               rent1Br_geo_df = pd.DataFrame(zip(rent1Br_geo.keys(), rent1Br_geo.values()), columns=['geohash', 'value'])


           # Check if found in DB
           geohashval = api_store['geohash']

           if api_store['propdetails'] is not None:
               details =  api_store['propdetails']
           else:
               details = None

           # Occupancy
           if details and details[4] is not None and type(details[4]) is str:
               occupancy = clean_percent(details[4])
               occupancy = float(occupancy)
           else:
               occupancy = prox_mean(occ_geo_df, geohashval)
               occupancy = float(occupancy)

           # Operating Expenses
           if details and details[5] is not None:
               if type(details[5]) is str and '$' in details[5]:
                   opex = clean_currency(details[5])
                   opex = float(opex)
               else:
                   opex = details[5]
                   opex = float(opex)
           else:
               opex = prox_mean(opex_geo_df, geohashval)
               opex = float(opex)

           # Tax Rate
           if details and details[7] is not None:
               taxRate = details[7]
               taxRate = float(taxRate)
           else:
               taxRate = prox_mean(taxRate_geo_df, geohashval)
               taxRate = float(taxRate)

           # Last Sale Date
           if details and details[9] is not None:
               lastSaleDate = details[9]
           else:
               ten_today = datetime.today() + relativedelta(years=-10)
               lastSaleDate = ten_today.strftime('%Y-%m-%d')

           # Property Tax - check API call, if not found prox_mean
           if api_store['attom_api'] is not None:
               try:
                   taxAmt = ['attom_api']['property'][0]['assessment']['tax']['taxamt']
                   taxAmt = int(taxAmt)
               except Exception as e:
                   taxAmt = prox_mean(taxAmt_geo_df, geohashval)
                   taxAmt = int(taxAmt)
           else:
               taxAmt = prox_mean(taxAmt_geo_df, geohashval)
               taxAmt = int(taxAmt)

           # Assessed Value - check API call, if not found prox_mean
           if api_store['attom_api'] is not None:
               try:
                   assVal = d['attom_api']['property'][0]['assessment']['assessed']['assdttlvalue']
                   assVal = int(assVal)
               except Exception as e:
                   assVal = prox_mean(estVal_geo_df, geohashval)
                   assVal = int(assVal)
           else:
               assVal = prox_mean(estVal_geo_df, geohashval)
               assVal = int(assVal)


           # Avg. Rents 1Br
           rent_1Br = prox_mean(rent1Br_geo_df, geohashval)

           # Ameneties
           ameneties_count = len(ameneties)

           # Function call to obtain rents
           result = calc_rent(address, proptype, built, space_acq, units_acq, ameneties_count, assVal, occupancy, opex, taxAmt, taxRate, rent_1Br, lastSaleDate, geohashval)

           # Revenue / Sq.ft / Year
           price = result["y_pred"] * 12

           '''
           Set of Comps - CMBS
           '''

           # Lease Comp set
           df_cmbs = result["df_cmbs"]

           # Median Revenue / Sq.ft / Year
           market_price = df_cmbs["Revenue_per_sqft_year"].apply(clean_currency).median()

           # Assign pandas series
           propname = df_cmbs["Property_Name"]

           # Generate Address string
           addr_cols = ["Address", "City", "State", "Zip_Code"]

           df_cmbs['Address_Comp'] = df_cmbs[addr_cols].apply(lambda row: ' '.join(row.values.astype(str)), axis=1)

           # Columns for customdata
           cd_cols = ['Property_Name','Address_Comp','Size','Year_Built','avg_price','Preceding_Fiscal_Year_Revenue','Opex','Occ','EstRentableArea','EstValue','lastSaleDate','Distance']

           datap.append({

                         "type": "scattermapbox",
                         "lat": df_cmbs["Lat"],
                         "lon": df_cmbs["Long"],
                         "name": "Location",
                         "hovertext": propname,
                         "showlegend": False,
                         "hoverinfo": "text",
                         "mode": "markers",
                         "clickmode": "event+select",
                         "customdata": df_cmbs.loc[:,cd_cols].values,
                         "marker": {
                                    "symbol": "circle",
                                    "size": 8,
                                    "opacity": 0.7,
                                    "color": "black"
                                   }
                         }
           )


           '''
           Set of comps - Non CMBS
           '''

           df_noncmbs = result["df_noncmbs"]

           propname = df_noncmbs["name"]

           # Estimate Annual Revenue
           df_noncmbs['unit_count'] = pd.to_numeric(df_noncmbs['unit_count'], errors='coerce')
           df_noncmbs['EstRevenue'] = (df_noncmbs['unit_count'] * df_noncmbs['avg_rent'])*12

           # Columns for customdata
           cd_cols = ['imgSrc','name','address_comp','unit_count','year_built','avg_rent','EstRevenue','EstRentableArea','EstValue','building_amenities','Distance']

           datap.append({

                           "type": "scattermapbox",
                           "lat": df_noncmbs['Lat'],
                           "lon": df_noncmbs['Long'],
                           "name": "Location",
                           "hovertext": propname,
                           "showlegend": False,
                           "hoverinfo": "text",
                           "mode": "markers",
                           "clickmode": "event+select",
                           "customdata": df_noncmbs.loc[:,cd_cols].values,
                           "marker": {
                               "symbol": "circle",
                               "size": 8,
                               "opacity": 0.8,
                               "color": "#4275f5"
                               }
                        }
           )

           # Add POI data layer
           df_nearby = nearby_places(address, None)

           # Check if DataFrame was returned
           if isinstance(df_nearby, pd.DataFrame):

              # Create a list of symbols by dict lookup
              sym_list = []

              for i in df_nearby['type_label']:
                  typ = sym_dict.get(i)
                  sym_list.append(typ)

              datap.append({

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


           Lat, Long = get_geocodes(address)

           layout_lat = Lat
           layout_lon = Long
           zoom = 12

           # create ranges
           noi = float(price) * int(space_acq)

           min = noi - (10*noi/100)
           max = noi + (10*noi/100)

           min_fmt = float(min)/1000000
           max_fmt = float(max)/1000000

           # custom data for subject property
           cdata = np.asarray([address, units_acq, built, proptype, space_acq, min_fmt, max_fmt, assVal, taxAmt])

           if min_fmt > -1 and min_fmt < 1 and max_fmt > -1 and max_fmt < 1:
               min_fmt = min_fmt * 1000
               max_fmt = max_fmt * 1000
               txt = "Expected Revenue: ${:.0f}K-${:.0f}K or approx. ${:.0f}/SF Yr.".format(min_fmt, max_fmt, price)

           elif min_fmt > -1 and min_fmt < 1 and max_fmt > 1:
               min_fmt = min_fmt * 1000
               txt = "Expected Revenue: ${:.0f}K-${:.1f}M or approx. ${:.0f}/SF Yr.".format(min_fmt, max_fmt, price)

           elif min_fmt > 1 and max_fmt > 1:
               txt = "Expected Revenue: ${:.1f}M-${:.1f}M or approx. ${:.0f}/SF Yr.".format(min_fmt, max_fmt, price)

           else:
               txt = "Expected Revenue: ${:.1f}M-${:.1f}M or approx. ${:.0f}/SF Yr.".format(min_fmt, max_fmt, price)

           # Property Location
           datap.append({
                         "type": "scattermapbox",
                         "lat": [Lat],
                         "lon": [Long],
                         "hovertext": '${:.0f}'.format(price),
                         "text": txt,
                         "textfont": {"color": "rgb(0, 0, 0)",
                                      "size": 18},
                         "textposition": "top right",
                         "showlegend": False,
                         "hoverinfo": "text",
                         "mode": "text+markers",
                         # Once the API is live, subject property data will be passed here for modal popup w carousel
                         "customdata": [cdata],
                         "marker": {
                             "symbol": sym_dict[proptype],
                             "size": 28,
                             "opacity": 0.7,
                             "color": "rgb(128, 128, 128)"
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
                             "lat": layout_lat,
                             "lon": layout_lon
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

        if n_clicks:

           poi = {"Lat": Lat, "Long": Long}

           layout["mapbox"] = {
                                **layout["mapbox"],
                                **{
                                    "layers": [
                                        {
                                            "source": json.loads(
                                                # convert radius to meters * miles
                                                #poi_poly(None, poi=poi, radius = 1609.34 * result["radius"]).to_json()
                                                poi_poly(None, poi=poi, radius = result['radius']).to_json()
                                            ),
                                            "below": "traces",
                                            "type": "fill",
                                            "opacity": .1,
                                            "fillcolor": "rgba(128, 128, 128, 0.1)",
                                        }
                                    ]
                                },
           }



        if n_clicks and result:
            # Sub columns for DataTable
            df_cmbs_sub = df_cmbs[['Property_Name','Zip_Code','avg_price','Preceding_Fiscal_Year_Revenue','EstRentableArea','Most_Recent_Physical_Occupancy','Year_Built','Size','EstRevenueMonthly','Revenue_per_sqft_year','Opex','EstValue','Distance']]

            df_noncmbs_sub = df_noncmbs[['name','addressZipcode','avg_rent','EstRevenue','EstRentableArea','year_built','unit_count','EstValue','Distance']]

            df_cmbs_img = df_cmbs[['Property_Name','Image_dicts']]

            return ({"data": datap, "layout": layout}, {"predicted": price, "market_price": market_price}, listToDict(details), {"df_cmbs": df_cmbs_sub.to_dict('records'), "df_noncmbs": df_noncmbs_sub.to_dict('records')}, df_cmbs_img.to_dict('records'))
        else:
            df_sub = df[['Property_Name','Image_dicts']]

            return ({"data": datac, "layout": layout}, {"predicted": price, "market_price": market_price}, listToDict(details), no_update, df_sub.to_dict('records'))

    else:
        #PreventUpdate
        return (no_update, no_update, no_update, no_update)


# Update upside card
@application.callback([
                        Output("card-img", "src"),
                        Output("card-header", "children"),
                        Output("card-text", "children")
                      ],
                      [
                        Input("comps-button", "n_clicks"),
                        Input("price-value", "value"),
                        Input("space-acq", "value")
                      ],
                      [
                        State("api-store", "data")
                      ]
                      )
def update_image(n_clicks, price_values, space, api_store):

    if n_clicks and api_store['propdetails'] and space:

        # 10% upside
        upside10 = (10 * float(api_store['propdetails'][8]))/float(api_store['propdetails'][8])
        upside10 = float(api_store['propdetails'][8]) + upside10

        # Rents + Occupancy, add condition to check for occupancy below market level
        if float(price_values['predicted'] * space) <= upside10:

            img_link = "https://stroom-images.s3.us-west-1.amazonaws.com/low_indicator.png"

            card_img_src = img_link
            card_header = "Low Income Growth and Upside Potential"
            card_text = "Rental revenue is close to comparable market value."

            return (card_img_src, card_header, card_text)

        elif float(price_values['predicted'] * space) >= float(api_store['propdetails'][8]):

            img_link = "https://stroom-images.s3.us-west-1.amazonaws.com/high_indicator.png"

            card_img_src = img_link
            card_header = "Income Growth and Upside Potential"
            card_text = "Rental revenue is lower than comparable market value."

            return (card_img_src, card_header, card_text)

    elif n_clicks:

        img_link = "https://stroom-images.s3.us-west-1.amazonaws.com/no-data.png"

        card_img_src = img_link
        card_header = "Not enough data"
        card_text = "Upload Proforma or upgrade to estimate Value-Add Potential"

        return (card_img_src, card_header, card_text)

    else:

        img_link = ""

        card_img_src = img_link
        card_header = ""
        card_text = ""

        return (card_img_src, card_header, card_text)


# Update DataTable and Local Level Stats
@application.callback([

                          Output("comps-table", "data"),
                          Output("rent-card", "children"),
                          Output("occ-card", "children"),
                          Output("opex-card", "children")

                      ],
                      [

                          Input("address_dropdown", "value"),
                          Input("prop-type", "value"),
                          Input("built", "value"),
                          Input("units-acq","value"),
                          Input("space-acq","value"),
                          Input("ameneties", "value"),

                          # Buttons
                          Input("comps-button", "n_clicks"),
                          Input("result-store", "data")

                      ],
                      [

                          State("comps-table", "data"),
                          State("comps-table", "columns")

                      ]
                      )
def update_table(address, proptype, built, units_acq, space_acq, ameneties, n_clicks, result_store, rows, columns):

    if not result_store:
        raise PreventUpdate

    elif n_clicks and result_store:

       # Prepare CMBS data
       df_cmbs = pd.DataFrame(result_store["df_cmbs"])

       df_cmbs = df_cmbs.sort_values(by=['EstRevenueMonthly'], ascending=False).head(15)
       df_cmbs = df_cmbs.sample(len(df_cmbs))

       df_cmbs['Type'] = 'CMBS'

       df_cmbs_v1 = pd.DataFrame(df_cmbs, columns = ["Property_Name","Type","Year_Built","Size","Preceding_Fiscal_Year_Revenue",
                                                     "Most_Recent_Physical_Occupancy", "SubMarket", "City", "MSA", "EstRevenueMonthly",
                                                     "Opex", "Address", "Zip_Code", "avg_price", "Revenue_per_sqft_year", "EstRentableArea",
                                                     "EstValue","Distance"])

       # Prepare Non CMBS data
       df_noncmbs = pd.DataFrame(result_store["df_noncmbs"])

       df_noncmbs['Type'] = 'Non CMBS'

       df_noncmbs.rename(columns={'name': 'Property_Name',
                                  'addressZipcode': 'Zip_Code',
                                  'avg_rent': 'avg_price',
                                  'EstRevenue': 'Preceding_Fiscal_Year_Revenue',
                                  'year_built': 'Year_Built',
                                  'unit_count': 'Size'}, inplace=True)

       # Append
       df = pd.concat([df_cmbs_v1, df_noncmbs])

       # Add Monthly Rent Column
       '''
       For Phoenix, Revenue / Size (# of units) appears to be a close approximation.
       For LA, SD and SF, Rate per sq.ft * 750 appears to be a close approximation.
       '''

       # Format columns
       if df['Preceding_Fiscal_Year_Revenue'].isna().sum() != len(df['Preceding_Fiscal_Year_Revenue']):
           df['Preceding_Fiscal_Year_Revenue'] = df['Preceding_Fiscal_Year_Revenue'].apply('${:,.0f}'.format)

       if df['EstRevenueMonthly'].isna().sum() != len(df['EstRevenueMonthly']):
           df['EstRevenueMonthly'] = df['EstRevenueMonthly'].apply('${:,.0f}'.format)

       if df['EstRentableArea'].isna().sum() != len(df['EstRentableArea']):
           df['EstRentableArea'] = df['EstRentableArea'].astype('string').replace('\.0', '', regex=True)

       if df['Opex'].isna().sum() != len(df['Opex']):
           df['Opex'] = df['Opex'].apply('${:,.0f}'.format)

       if df['avg_price'].isna().sum() != len(df['avg_price']):
           df['avg_price'] = df['avg_price'].apply('${:,.0f}'.format)

       if df['EstValue'].isna().sum() != len(df['EstValue']):
           df['EstValue'] = df['EstValue'].astype('string').replace('\.0', '', regex=True)

       df['Year_Built'] = df['Year_Built'].astype('string').replace('\.0', '', regex=True)

       df['Distance'] = df['Distance'].apply('{:,.1f}'.format)

       df.replace(["$nan",""],'nan', inplace=True)

       df.fillna('nan', inplace=True)

       comps_data = df.to_dict("rows")

       # Clean up columns to calculate stats
       df['Most_Recent_Physical_Occupancy'] = df['Most_Recent_Physical_Occupancy'].apply(clean_percent).astype('float')

       df1 = df

       # Rent col
       if df1['avg_price'].isna().sum() != len(df1['avg_price']):
           df1['avg_price'] = df1['avg_price'].apply(clean_currency).astype(float)
           rent_col = df1[df1['avg_price'] > 0]
           rent_avg = rent_col['avg_price'].median()
           rent_avg = "${:,.0f}".format(rent_avg)
       else:
           rent_avg = "N/A"

       # Monthly Revenue
       if df1['EstRevenueMonthly'].isna().sum() != len(df1['EstRevenueMonthly']):
           df1['EstRevenueMonthly'] = df1['EstRevenueMonthly'].apply(clean_currency).astype(float)
           revenue_col = df1[df1['EstRevenueMonthly'] > 0]
           revenue_avg = revenue_col['EstRevenueMonthly'].median()
           revenue_avg = "${:,.0f}".format(revenue_avg)
       else:
           revenue_avg = "N/A"

       # Physical occupancy
       if df1['Most_Recent_Physical_Occupancy'].isna().sum() != len(df1['Most_Recent_Physical_Occupancy']):
           occ_col = df1[df1['Most_Recent_Physical_Occupancy'] > 0]
           occ_avg = occ_col['Most_Recent_Physical_Occupancy'].mean()
           occ_avg = "{:,.1f}%".format(occ_avg)
       else:
           occ_avg = "N/A"

       # Format / clean up
       if df1['Opex'].isna().sum() != len(df1['Opex']):
           df1['Opex'] = df1['Opex'].apply(clean_currency).astype('float')
           opex_col = df1[df1['Opex'] > 0]
           opex_avg = opex_col['Opex'].mean()
           opex_avg = "${:,.0f}".format(opex_avg)
       else:
           opex_avg = "N/A"

       return (comps_data, rent_avg, occ_avg, opex_avg)

    else:

       return (no_update, no_update, no_update, no_update)



# Update comps modal on click event
@application.callback(
                          [
                               # Modal Comps
                               Output("modal-1","is_open"),
                               Output("carousel","children"),
                               Output("prop_name","children"),
                               Output("Address","children"),
                               Output("Size","children"),
                               Output("Yr_Built","children"),
                               Output("Rent_cmbs", "children"),
                               Output("Revenue","children"),
                               Output("Opex","children"),
                               Output("occ-modal","children"),
                               Output("rent-area-modal","children"),
                               Output("assessed-value","children"),
                               Output("sale-date","children"),
                               Output("distance","children"),

                               # Modal Subject Property
                               Output("modal-2","is_open"),
                               Output("carousel-s","children"),
                               Output("Address-s","children"),
                               Output("Size-s","children"),
                               Output("Yr_Built-s","children"),
                               Output("rent-area-modal-s","children"),
                               Output("Revenue-s","children"),
                               Output("assessed-val-s","children"),
                               Output("prop-tax-s","children"),

                               # Modal Zillow
                               Output("modal-3","is_open"),
                               Output("carousel-z","children"),
                               Output("prop_name_z","children"),
                               Output("Address_z","children"),
                               Output("Size_z","children"),
                               Output("Yr_Built_z","children"),
                               Output("rent_z","children"),
                               Output("Revenue_z","children"),
                               Output("rent-area-modal-z","children"),
                               Output("assessed-value-z","children"),
                               Output("ameneties_z","children"),
                               Output("distance_z","children"),

                          ],

                          [
                               # Button clicks
                               Input("map-graph1","clickData"),
                               Input("comps-button", "n_clicks"),
                               Input("close","n_clicks"),
                               Input("close-s","n_clicks"),
                               Input("close-z","n_clicks")
                          ],

                          [
                                State("modal-1", "is_open"),
                                State("modal-2", "is_open"),
                                State("modal-3", "is_open"),
                                State("query-store", "data")
                          ],
                    )
def display_popup(clickData, n_clicks, n_clicks_c, n_clicks_sp, n_clicks_z, is_open_c, is_open_sp, is_open_z, query_store):

    if clickData:

        res = json.dumps(clickData, indent=2)

        print("clickData response", res)

        # Condition for comps clickData
        if len(clickData['points'][0]['customdata']) == 12:

            Name = clickData["points"][0]["customdata"][0]
            Address = clickData["points"][0]["customdata"][1]
            Size = clickData["points"][0]["customdata"][2]
            Built = clickData["points"][0]["customdata"][3]
            Rent = clickData["points"][0]["customdata"][4]
            Revenue = clickData["points"][0]['customdata'][5]
            Opex = clickData["points"][0]['customdata'][6]
            Occupancy = clickData["points"][0]["customdata"][7]
            RentArea = clickData["points"][0]["customdata"][8]
            AssessedValue = clickData["points"][0]["customdata"][9]
            lastSaleDate = clickData["points"][0]["customdata"][10]
            Distance = clickData["points"][0]["customdata"][11]

            # Check dataframe - default view or property search geofilter
            if query_store:

                df = pd.DataFrame(query_store)

                # Construct a list of dictionaries
                df = df[df['Property_Name'] == Name]

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

                         # Get streetview image

                         lat, long = get_geocodes(Address)
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

            # Formatted Rent for default view (NA), calculated / post button click and handling of None values
            if Rent in [None, 'nan']:
                Rent_fmt == "N/A"
            else:
                Rent = int(Rent)
                Rent_fmt = "${:,.0f}".format(Rent)

            if Revenue is None:
                Revenue_fmt == "N/A"
            else:
                Revenue = float(Revenue)
                Revenue_fmt = "${:,.0f}".format(Revenue)

            if Opex is None:
                Opex_fmt == "N/A"
            else:
                Opex_fmt = "${:,.0f}".format(Opex)

            if Occupancy is None:
                Occupancy_fmt == "N/A"
            else:
                Occupancy = Occupancy.strip('%')
                Occupancy = float(Occupancy)
                Occupancy_fmt = "{:.0f}%".format(Occupancy)

            if RentArea is None:
                RentArea_fmt = "N/A"
            else:
                RentArea_fmt = "{:,.0f} sq.ft".format(RentArea)

            if AssessedValue is None:
                AssessedValue_fmt = "N/A"
            else:
                AssessedValue_fmt = "${:,.0f}".format(AssessedValue)

            if lastSaleDate == "null":
                lastSaleDate_fmt = "N/A"
            else:
                lastSaleDate_fmt = lastSaleDate

            if Distance == "N/A":
                Distance_fmt = Distance
            else:
                Distance = float(Distance)
                Distance_fmt = "{:,.1f} miles".format(Distance)

            return(not is_open_c, carousel, Name, Address, Size, Built, Rent_fmt, Revenue_fmt, Opex_fmt, Occupancy_fmt, RentArea_fmt, AssessedValue_fmt, lastSaleDate_fmt, Distance_fmt, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update)

        # subject property
        elif len(clickData['points'][0]['customdata']) == 9:

            Address = clickData["points"][0]["customdata"][0]
            Size = clickData["points"][0]["customdata"][1]
            Built = clickData["points"][0]["customdata"][2]
            Property = clickData["points"][0]["customdata"][3]
            RentArea = clickData["points"][0]["customdata"][4]
            ExpRevenueMin = clickData["points"][0]["customdata"][5]
            ExpRevenueMax = clickData["points"][0]["customdata"][6]
            AssessedVal = clickData["points"][0]["customdata"][7]
            PropTax = clickData["points"][0]["customdata"][8]

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


            # formatted for default view (NA) and calculated / post button click and handling of None value
            if RentArea is None:
                RentArea_fmt = "N/A"
            else:
                RentArea = int(RentArea)
                RentArea_fmt = "{:,.0f} sq.ft".format(RentArea)

            if ExpRevenueMin is None:

                ExpRevenue_fmt = "N/A"

            else:

                ExpRevenueMin = float(ExpRevenueMin)
                ExpRevenueMax = float(ExpRevenueMax)

                if ExpRevenueMin > -1 and ExpRevenueMax <= 1 and ExpRevenueMax > -1 and ExpRevenueMax < 1:
                    ExpRevenueMin = ExpRevenueMin * 1000
                    ExpRevenueMax = ExpRevenueMin * 1000
                    ExpRevenue_fmt = "${:.0f}K-${:.0f}K".format(ExpRevenueMin, ExpRevenueMax)

                elif ExpRevenueMin > -1 and ExpRevenueMin < 1 and ExpRevenueMax > 1:
                    ExpRevenueMin = ExpRevenueMin * 1000
                    ExpRevenue_fmt = "${:.0f}K-${:.1f}M".format(ExpRevenueMin, ExpRevenueMax)

                elif ExpRevenueMin > 1 and ExpRevenueMax > 1:
                    ExpRevenue_fmt = "${:.1f}M-${:.1f}M".format(ExpRevenueMin, ExpRevenueMax)

                else:
                    ExpRevenue_fmt = "${:.1f}M-${:.1f}M".format(ExpRevenueMin, ExpRevenueMax)


            if AssessedVal is None:
                AssessedVal_fmt = "N/A"
            else:
                AssessedVal = int(AssessedVal)
                AssessedVal_fmt = "${:,.0f}".format(AssessedVal)

            if PropTax is None:
                PropTax_fmt = "N/A"
            else:
                PropTax = int(PropTax)
                PropTax_fmt = "${:,.0f}".format(PropTax)

            return(no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, not is_open_sp, carousel, Address, Size, Built, Property, RentArea_fmt, ExpRevenue_fmt, AssessedVal_fmt, PropTax_fmt, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update)

        elif n_clicks_sp:
            return is_open

        # zillow data
        elif len(clickData['points'][0]['customdata']) == 11:

            img_link = clickData["points"][0]["customdata"][0]
            Name = clickData["points"][0]["customdata"][1]
            Address = clickData["points"][0]["customdata"][2]
            Size = clickData["points"][0]["customdata"][3]
            Built = clickData["points"][0]["customdata"][4]
            Rent = clickData["points"][0]["customdata"][5]
            Revenue = clickData["points"][0]["customdata"][6]
            RentArea = clickData["points"][0]["customdata"][7]
            AssessedVal = clickData["points"][0]["customdata"][8]
            Ameneties = clickData["points"][0]["customdata"][9]
            Distance = clickData["points"][0]["customdata"][10]

            if img_link:

                carousel = dbc.Carousel(
                                        items=[
                                                 {"key": "1", "src": img_link, "img_style": {"width": "300px", "height": "300px"}},
                                        ],
                                        controls=True,
                                        indicators=True,
                           )

            # formatted for default view (NA) and calculated / post button click and handling of None value
            if Name in [None, 'nan']:
                Name_fmt = "Unknown"
            else:
                Name_fmt = Name

            if Address in [None, 'nan']:
                Address_fmt = "Unknown"
            else:
                Address_fmt = Address

            if Size in [None, 'nan']:
                Size_fmt = "Unknown"
            else:
                Size_fmt = int(Size)

            if Built in [None, 'nan']:
                Built_fmt = "Unknown"
            else:
                Built_fmt = int(float(Built))

            if Rent in [None, 'nan']:
                Rent_fmt = "Unknown"
            else:
                Rent = int(Rent)
                Rent_fmt = "${:,.0f}".format(Rent)

            if Revenue in [None, 'nan']:
                Revenue_fmt = "Unknown"
            else:
                Revenue = float(Revenue)
                Revenue_fmt = "${:,.0f}".format(Revenue)

            if RentArea in [None, 'nan']:
                RentArea_fmt = "Unknown"
            else:
                RentArea = int(float(RentArea))
                RentArea_fmt = "{:,.0f} sq.ft".format(RentArea)

            if AssessedVal in [None, 'nan']:
                AssessedVal_fmt = "Unknown"
            else:
                AssessedVal = int(float(AssessedVal))
                AssessedVal_fmt = "${:,.0f}".format(AssessedVal)

            if Ameneties in [None, 'nan']:
                Ameneties_fmt = "Unknown"
            else:
                Ameneties = ast.literal_eval(Ameneties)
                Ameneties = ', '.join(Ameneties)
                Ameneties_fmt = Ameneties

            if Distance == "N/A":
                Distance_fmt = Distance
            else:
                Distance = float(Distance)
                Distance_fmt = "{:,.1f} miles".format(Distance)

            return(no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, not is_open_z, carousel, Name_fmt, Address_fmt, Size_fmt, Built_fmt, Rent_fmt, Revenue_fmt, RentArea_fmt, AssessedVal_fmt, Ameneties_fmt, Distance_fmt)

        elif n_clicks_z:
            return is_open

        else:
            return (no_update)

    else:

        return (no_update)



# Store map-graph and data-table in dcc.Store component
@application.callback(Output("comps-store","data"),
                     [
                          Input("map-graph1","figure"),
                          Input("comps-table","data"),

                          # Comp dataset -- useful for local stats calculation
                          Input("address_autocomplete","value"),
                          Input("prop-type","value"),
                          Input("built","value"),
                          Input("units-acq","value"),
                          Input("space-acq","value"),
                          Input("dummy-div", "value"),
                          Input("price-value","value"),

                          # Local stats
                          Input("rent-card","children"),

                          Input("comps-button","n_clicks")

                     ]
                    )
def comp_store(map, table, propaddress, proptype, built, units_acq, space_acq, dummy, price, rent_card, n_clicks):

    # Store map-graph and data-table as dictionary.
    if n_clicks:

        return {
                "map": map,
                "table": table,
                "propinfo": [{"address": propaddress, "type": proptype, "year-built": built, "units": units_acq, "space": space_acq}],
                "price_values": price,
                "local_rent": rent_card,
                "propdetails": dummy
               }
