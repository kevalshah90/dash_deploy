# Packages
import pandas as pd
import numpy as np
from numpy import median
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
from scipy import stats
from dash.dash import no_update
from dash.exceptions import PreventUpdate
from base_rent_calc import calc_rev, walkscore
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

# Run query
query = '''
        select *
        from stroom_main.df_raw_july
        where City = 'San Francisco'
        and zrent_median < 10000
        and Size >= 50
        LIMIT 25
        '''

df = pd.read_sql(query, con)

# App Layout for designing the page and adding elements
layout = html.Div([

   html.Div([

       dbc.Alert(id = "comps-alerts-1",
                 className = "comps-alerts-1",
                 dismissable = True,
                 duration = 7000,
                 is_open = False,
                 color="secondary"),

    ], id = "comps-alerts-div-1"),

    html.Div([

        dbc.Alert(id = "comps-alerts-2",
                  className = "comps-alerts-2",
                  dismissable = True,
                  duration = 7000,
                  is_open = False,
                  color="secondary"),

     ], id = "comps-alerts-div-2"),

   dbc.Row(
       [

         dbc.Col(

            html.Div([

                # Plot properties map
                dcc.Loading(
                    id = "map-comps-load",
                    type = "default",
                    className = "map-comps-load",
                    fullscreen=False,
                    children=dcc.Graph(id="map-graph1", className="map-graph1"),
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

                                                  html.H5(id="card-header"),
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

         ], style={"width":"100%", "margin-top":"36em", "margin-left":"16em"}),


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

                                dbc.Label("Rents:", id="RentS_lbl", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                dbc.Label("Rent:", id="RentCMBS"),
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

                               # dbc.Label("Number of Units:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                               # dbc.Label("Size:", id="Size_z"),
                               # html.Br(),
                               #
                               # dbc.Label("Year Built:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                               # dbc.Label("Year Built:", id="Yr_Built_z"),
                               # html.Br(),

                               dbc.Label("Avg. Rent (Studio):", id="RentSZ_lbl", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                               dbc.Label("Rent:", id="RentSZ"),
                               html.Br(),

                               dbc.Label("Avg. Rent (1Br):", id="Rent1BrZ_lbl", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                               dbc.Label("Rent:", id="Rent1BrZ"),
                               html.Br(),

                               dbc.Label("Avg. Rent (2Br):", id="Rent2BrZ_lbl", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                               dbc.Label("Rent:", id="Rent2BrZ"),
                               html.Br(),

                               dbc.Label("Avg. Rent (3Br):", id="Rent3BrZ_lbl", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                               dbc.Label("Rent:", id="Rent3BrZ"),
                               html.Br(),

                               # dbc.Label("Estimated Revenue:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                               # dbc.Label("Revenue:", id="Revenue_z"),
                               # html.Br(),

                               # dbc.Label("Rentable Area:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                               # dbc.Label("Rentable Area:", id="rent-area-modal-z"),
                               # html.Br(),

                               # dbc.Label("Assessed Value:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                               # dbc.Label("Assessed Value:", id="assessed-value-z"),
                               # html.Br(),

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

                                dbc.Label("Est. Rent (Studio, 1/2/3 Bed):", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                dbc.Label("Rents:", id="Rents-s"),
                                html.Br(),

                                dbc.Label("Estimated Fiscal Revenue:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
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

                        dbc.InputGroupText("Address"),

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

                        dbc.InputGroupText("Year Built", id="built-text", style={"margin-left":"8px"}),
                        dbc.Input(
                                  id="built",
                                  persistence=True,
                                  persistence_type="memory"
                                 ),

                        dbc.InputGroupText("Renovated", id="renovate-text", style={"margin-left":"8px"}),
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

                       dbc.InputGroupText("Area(RSF)", id="size-text", style={"margin-left":"8px"}),
                       dbc.Input(
                                 id="space-acq",
                                 persistence=True,
                                 persistence_type="memory"
                                ),

                       dbc.InputGroupText("Units", id="size-text", style={"margin-left":"8px"}),
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

                ], style={"width":"70%", "margin-top": "12%"}),


            ], className="prop-style",
               style={"width": "90%", "font-size":"1.08em"}),

        ], width={"size": 8, "order": "last", "offset": 8},),
    ]),


    dbc.Row([

            # # Lease Table
            html.Div([

                dash_table.DataTable(

                    id="comps-table",

                    columns=[{"id":"Property_Name","name":"Name"},
                             {"id":"Zip_Code","name":"Zip"},
                             {"id":"Year_Built","name": "Yr. Built"},
                             {"id":"Type","name":"Type"},
                             {"id":"bed_rooms","name":"# Beds"},
                             {"id":"zrent_median","name":"Avg. Rent"},
                             {"id":"Preceding_Fiscal_Year_Revenue","name": "Revenue"},
                             {"id":"EstRentableArea","name": "Area (Sq.ft)"},
                             {"id":"Most_Recent_Physical_Occupancy","name":"Occ."},
                             {"id":"Size","name": "Units"},
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

        dcc.Store(id='result-store', storage_type='memory'), # df cmbs and non-cmbs
        dcc.Store(id="api-store", storage_type='memory'), # api result
        dcc.Store(id="query-store", storage_type='memory'), # img src
        dcc.Store(id="table-store", storage_type='memory')

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
                        Output("ameneties", "value"),
                        Output("api-store", "data"),
                        Output("comps-alerts-div-1", "style"),
                        Output("comps-alerts-1", "children"),
                        Output("comps-alerts-1", "is_open")

                      ],
                      [
                        Input("address_dropdown", "value")
                      ],
                      [
                        State("comps-alerts-1", "is_open")
                      ]
                     )
def autopopulate_propdetails(address, is_open):

    details = None
    avdata = None

    if address and len(address) > 8:

        g = geocoder.mapbox(address, key=token)
        geojson = g.json
        addr = geojson["address"]

        coords = [geojson['lat'], geojson['lng']]

        geohashval = gh.encode(geojson['lat'], geojson['lng'], precision=5)

    else:
        return(no_update, no_update, no_update, no_update, no_update, no_update, {"display": "none"}, no_update, not is_open)
        #raise PreventUpdate


    if geojson:

        # Query to find property in the database - 0.12 miles to meters = 193
        query = '''
                select * from stroom_main.df_raw_july
                where st_distance_sphere(Point({},{}), coords) <= {};
                '''.format(geojson['lng'], geojson['lat'], 193)

        df_mf = pd.read_sql(query, con)

        # Check if dataframe is not empty and property was found
        if df_mf.shape[0] > 0:

            df_mf.reset_index(drop=True, inplace=True)

            details = df_mf[['Year_Built','Renovated','EstRentableArea','Size','Ownership','AirCon','Pool','Condition','constructionType','parkingType','numberOfBuildings','propertyTaxAmount','taxRate','Preceding_Fiscal_Year_Revenue','EstValue','lastSaleDate']].iloc[0].to_list()

            if details[0] and details[2] and details[3] not in [0, 0.0, '0', '0.0']:

                print("Match found in DB")

                print(details)

                # Get Ameneties
                amn_lst = ["Luxurious", "Park", "Gym", "Laundry", "Pool", "Rent-control", "Bike", "Patio", "Concierge", "Heat"]

                return (float(details[0]), details[1], float(details[2]), float(details[3]), amn_lst, {"attom_api": None, "geohash": geohashval, "propdetails": details}, {"display": "none"}, no_update, not is_open)

            else:

                # ATTOM API Call
                avdata = attom_api_avalue(addr)
                avdata = json.loads(avdata.decode("utf-8"))

                print("Attom api response", avdata)

        else:

            # ATTOM API Call
            avdata = attom_api_avalue(addr)
            avdata = json.loads(avdata.decode("utf-8"))

            print("Attom api response", avdata)


        if avdata is not None:

            try:

                if avdata['status']['msg'] == "SuccessWithResult" or avdata['property'] != []:

                    print("Address Found")
                    # Year Built
                    try:
                        if 'yearbuilt' in avdata['property'][0]['summary']:
                            built = avdata['property'][0]['summary']['yearbuilt']
                            built = int(built)
                    except Exception as e:
                        built = no_update
                        print("Year Built", e)
                        pass

                    # Area
                    try:
                        if 'grosssize' in avdata['property'][0]['building']['size']:
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
                            print("Area Exception", e)
                            pass

                    # Units
                    try:
                        if 'unitsCount' in avdata['property'][0]['building']['summary']:
                            units = avdata['property'][0]['building']['summary']['unitsCount']
                            units = int(units)
                        else:
                            if isinstance(area, 'int') == True:
                                # gross area / avg. apartment size - 882
                                units = int(area/882)
                            else:
                                units = no_update
                                pass
                    except Exception as e:
                        print("Units Exception", e)
                        if isinstance(area, int) == True:
                            # gross area / avg. apartment size - 882
                            units = int(area/882)
                        else:
                            units = no_update
                            pass

                    # Get Ameneties
                    amn_lst = ["Luxurious", "Park", "Gym", "Laundry", "Pool", "Rent-control", "Bike", "Patio", "Concierge", "Heat"]

                return (built, no_update, area, units, amn_lst, {"attom_api": avdata, "geohash": geohashval, "propdetails": details}, {"display": "none"}, no_update, not is_open)

                if avdata['property'] == []:

                    msg = "Address Not Found - Enter Manually"

                    if is_open == True:
                        return ('', '', '', '', '', no_update, {"display": "inline"}, msg, is_open)
                    else:
                        return ('', '', '', '', '', no_update, {"display": "inline"}, msg, not is_open)

            except Exception as e:
                print("Exception", e)
                msg = "Address Not Found - Enter Manually"

                if is_open == True:
                    return ('', '', '', '', '', no_update, {"display": "inline"}, msg, is_open)
                else:
                    return ('', '', '', '', '', no_update, {"display": "inline"}, msg, not is_open)

    else:
        return('', '', '', '', '', '', {"display": "none"}, no_update, no_update)



# Update map graph
@application.callback([

                          Output("map-graph1", "figure"),
                          Output("price-value", "value"),
                          Output("dummy-div", "value"),
                          Output("result-store", "data"),
                          Output("query-store", "data"),
                          Output("comps-alerts-div-2", "style"),
                          Output("comps-alerts-2", "children"),
                          Output("comps-alerts-2", "is_open")

                      ],
                      [

                          Input("address_dropdown", "value"),
                          Input("prop-type", "value"),
                          Input("built", "value"),
                          Input("units-acq","value"),
                          Input("space-acq","value"),
                          Input("ameneties", "value"),
                          Input("comps-button", "n_clicks"),
                          Input("map-graph1", "relayoutData")

                      ],
                      [
                          State("comps-store", "data"),
                          State("api-store", "data"),
                          State("comps-alerts-2", "is_open")
                      ]
             )
def update_graph(address, proptype, built, units_acq, space_acq, ameneties, n_clicks, mapdata, comps_store, api_store, is_open):

    '''
    Update this to adjust map layout.
    Default map view
    '''

    # sf bay area
    if mapdata is not None:
        if len(mapdata) > 1 and 'mapbox.center' in mapdata and 'mapbox.zoom' in mapdata:
            # set coords
            layout_lat = mapdata['mapbox.center']['lat']
            layout_lon = mapdata['mapbox.center']['lon']
            # set zoom level
            zoom = mapdata['mapbox.zoom']
        else:
            layout_lat = 37.7749
            layout_lon = -122.4194
            zoom = 11.5
    else:
        layout_lat = 37.7749
        layout_lon = -122.4194
        zoom = 11.5

    price = 0

    market_price = 0

    details = None

    result = None

    datac = []

    if proptype == "Multi-Family":

        # Generate Address string
        addr_cols = ["Address", "City", "State", "Zip_Code"]

        df['Address_Comp'] = df[addr_cols].apply(lambda row: ' '.join(row.values.astype(str)), axis=1)

        # String to numeric
        df['Preceding_Fiscal_Year_Revenue'] = pd.to_numeric(df['Preceding_Fiscal_Year_Revenue'], errors='coerce')
        df['Size'] = pd.to_numeric(df['Size'], errors='coerce')

        df['EstRevenueMonthly'] = (df['Preceding_Fiscal_Year_Revenue']/df['Size'])/12
        df['Distance'] = "N/A"

        # Columns for customdata
        cd_cols = ['Property_Name','Address_Comp','Size','Year_Built','zrent_quantile_random','zrent_median','Preceding_Fiscal_Year_Revenue','Opex','Occ','EstRentableArea','EstValue','lastSaleDate','Distance']

        propname = df["Property_Name"]

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
                        "customdata": df.loc[:,cd_cols].values, #subset .loc[row:col]
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

        for t in ctx.triggered:
            if 'comps-button.n_clicks' in t['prop_id']:
                btn = "clicked"
            else:
                btn = "notclicked"

        if n_clicks and btn == "clicked":
           # Query to find property within 5 miles radius to create geo-aggregated dicts
           g = geocoder.mapbox(address, key=token)
           geojson = g.json
           addr = geojson["address"]

           coords = [geojson['lat'], geojson['lng']]

           geohashval = gh.encode(geojson['lat'], geojson['lng'], precision=5)

           query = '''
                   SELECT *
                   FROM stroom_main.df_raw_july
                   WHERE st_distance_sphere(Point({},{}), coords) <= {};
                   '''.format(geojson['lng'], geojson['lat'], 10*1609)

           df_mf = pd.read_sql(query, con)

           #print("Fiscal Revenue", df_mf['Preceding_Fiscal_Year_Revenue'])

           if df_mf.shape[0] == 0 and address:

               msg = "Address outside of Coverage Area"

               if is_open == True:
                   return (no_update, no_update, no_update, no_update, no_update, {"display": "inline"}, msg, is_open)
               else:
                   return (no_update, no_update, no_update, no_update, no_update, {"display": "inline"}, msg, not is_open)

           else:

               datap = []

               # Create geo-aggregated dicts for occupancy, opex, tax rate and tax amount
               opex_geo = dict()
               taxRate_geo = dict()
               taxAmt_geo = dict()
               estVal_geo = dict()
               zrent_geo = dict()
               cap_geo = dict()
               home_geo = dict()
               area_geo = dict()

               # Construct opex / sqft column
               df_mf['opex_sqft_month'] = (df_mf['Most_Recent_Operating_Expenses'].apply(clean_currency).astype(float)/df_mf['EstRentableArea'].astype(float))/12
               df_mf['opex_sqft_month'].replace([np.inf, -np.inf], np.nan, inplace=True)
               df_mf['opex_sqft_month'] = df_mf['opex_sqft_month'].apply(lambda x: round(x, 2))

               # Area per unit
               df_mf['Area_per_unit'] = df_mf['EstRentableArea'].astype(float) / df_mf['Size'].astype(float)
               df_mf['Area_per_unit'].replace([np.inf, -np.inf], np.nan, inplace=True)
               df_mf['Area_per_unit'] = pd.to_numeric(df_mf['Area_per_unit'], errors="coerce")

               for name, group in df_mf.groupby(['geohash']):

                   # Opex
                   group['opex_sqft_month'] = group['opex_sqft_month'].apply(clean_currency).astype('float')
                   opex_geo[name] = group[group['opex_sqft_month'] > 0]['opex_sqft_month'].mean()
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
                   group['zrent_median'] = group['zrent_median'].apply(clean_currency).astype('float')
                   zrent_geo[name] = group[group['zrent_median'] > 0]['zrent_median'].mean()
                   # Dict to pandas dataframe
                   zrent_geo_df = pd.DataFrame(zip(zrent_geo.keys(), zrent_geo.values()), columns=['geohash', 'value'])

                   # Cap rate
                   group['Cap_Rate_Iss'] = group['Cap_Rate_Iss'].apply(clean_currency).astype('float')
                   cap_geo[name] = group[group['Cap_Rate_Iss'] > 0]['Cap_Rate_Iss'].mean()
                   # Dict to pandas dataframe
                   cap_geo_df = pd.DataFrame(zip(cap_geo.keys(), cap_geo.values()), columns=['geohash', 'value'])

                   # Home Value
                   group['Median_Home_Value_2019'] = group['Median_Home_Value_2019'].apply(clean_currency).astype('float')
                   home_geo[name] = group[group['Median_Home_Value_2019'] > 50000]['Median_Home_Value_2019'].mean()
                   # Dict to pandas dataframe
                   home_geo_df = pd.DataFrame(zip(home_geo.keys(), home_geo.values()), columns=['geohash', 'value'])

                   # Area per unit
                   group['Area_per_unit'] = group['Area_per_unit'].astype('float')
                   area_geo[name] = group[group['Area_per_unit'] > 100]['Area_per_unit'].mean()
                   # Dict to pandas dataframe
                   area_geo_df = pd.DataFrame(zip(area_geo.keys(), area_geo.values()), columns=['geohash', 'value'])


               # Check if found in DB or Attom API
               if api_store is not None:
                   if api_store['propdetails'] is not None:
                       details =  api_store['propdetails']
                   elif api_store['attom_api'] is not None:
                       details_api = api_store['attom_api']
               else:
                   details = None

               # ['Year_Built','Renovated','EstRentableArea','Size','Ownership','AirCon','Pool','Condition','constructionType','parkingType','numberOfBuildings','propertyTaxAmount','taxRate','Preceding_Fiscal_Year_Revenue','EstValue','lastSaleDate']
               #
               # ['1989.0', '2012', '212246.0', '320.0', 'Y', 'NONE', 'NONE', 'UNKNOWN', 'STEEL/HEAVY', 'UNKNOWN', '1.0', '1244309.54', '0.012', None, 178000000.0, '2006-06-09 00:00:00']
               #                                          4      5      6        7          8              9         10        11         12     13      14            15

               # Check if details or details API is not None

               # Ownership
               if details and details[4] is not None:
                   owner = str(details[4])
               else:
                   owner = 'N'

               # AirCon
               if details and details[5] is not None:
                   aircon = str(details[5])
               else:
                   # default
                   aircon = 'NONE'

               # Pool
               if details and details[6] is not None:
                   pool = str(details[6])
               elif api_store['attom_api'] is not None:
                   try:
                       pool = api_store['property'][0]['lot']['pooltype']
                       pool = str(pool)
                   except Exception as e:
                       pool = 'NONE'
               else:
                   # default
                   pool = 'NONE'

               # Condition
               if details and details[7] is not None:
                   condition = str(details[7])
               elif api_store['attom_api'] is not None:
                   try:
                       condition = api_store['property'][0]['building']['construction']['condition']
                       condition = str(condition)
                   except Exception as e:
                       condition = 'UNKNOWN'
               else:
                   # default
                   condition = 'UNKNOWN'

               # Construction Type
               if details and details[8] is not None:
                   constructionType = str(details[8])
               elif api_store['attom_api'] is not None:
                   try:
                       constructionType = api_store['attom_api']['property'][0]['building']['construction']['constructiontype']
                       constructionType = str(constructionType)
                   except Exception as e:
                       constructionType = 'UNKNOWN'
               else:
                   # default
                   constructionType = 'UNKNOWN'

               # Parking Type
               if details and details[9] is not None:
                   parkingType = str(details[9])
               elif api_store['attom_api'] is not None:
                   try:
                       parkingType = api_store['attom_api']['property'][0]['building']['parking']['parkingtype']
                       parkingType = str(parkingType)
                   except Exception as e:
                       parkingType = 'UNKNOWN'
               else:
                   # default
                   parkingType = 'UNKNOWN'

               #  Num buildings
               if details and details[10] is not None:
                   numBldgs = details[10]
               else:
                   numBldgs = 1

               # Property Tax - check API call, if not found prox_mean
               if details and details[11] is not None:
                   taxAmt = float(details[11])
               elif api_store is not None:
                   if api_store['attom_api'] is not None:
                       try:
                           taxAmt = api_store['attom_api']['property'][0]['assessment']['tax']['taxamt']
                           taxAmt = int(taxAmt)
                       except Exception as e:
                           taxAmt = prox_mean(taxAmt_geo_df, geohashval)
                           if taxAmt == 'nan':
                               taxAmt = 0
                           else:
                               taxAmt = int(taxAmt)
                   else:
                       taxAmt = prox_mean(taxAmt_geo_df, geohashval)
                       if taxAmt == 'nan':
                           taxAmt = 0
                       else:
                           taxAmt = int(taxAmt)
               else:
                   taxAmt = prox_mean(taxAmt_geo_df, geohashval)
                   try:
                       if taxAmt == 'nan':
                           taxAmt = 0
                       else:
                           taxAmt = int(taxAmt)
                   except Exception as e:
                       taxAmt = 0

               # Tax Rate
               if details and details[12] is not None:
                   taxRate = details[12]
                   taxRate = float(taxRate)
               else:
                   taxRate = prox_mean(taxRate_geo_df, geohashval)
                   taxRate = float(taxRate)


               # Assessed Value - check API call, if not found prox_mean
               if details and details[14] is not None:
                   assVal = float(details[11])
               elif api_store is not None:
                   if api_store['attom_api'] is not None:
                       try:
                           assVal = api_store['attom_api']['property'][0]['assessment']['assessed']['assdttlvalue']
                           assVal = int(assVal)
                       except Exception as e:
                           assVal = prox_mean(estVal_geo_df, geohashval)
                           assVal = int(assVal)
                   else:
                       assVal = prox_mean(estVal_geo_df, geohashval)
                       assVal = int(assVal)
               else:
                   assVal = prox_mean(estVal_geo_df, geohashval)
                   assVal = int(assVal)

               # Last Sale Date
               if details and details[15] is not None:
                   lastSaleDate = details[15]
                   lastSaleDate = datetime.strptime(lastSaleDate, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')

               else:
                   ten_today = datetime.today() + relativedelta(years=-10)
                   lastSaleDate = ten_today.strftime('%Y-%m-%d')

               # opex
               opex = prox_mean(opex_geo_df, geohashval)

               # Avg. Rents 1Br
               zrent = prox_mean(zrent_geo_df, geohashval)

               # Cap rate
               cap = prox_mean(cap_geo_df, geohashval)

               # Median Home Value
               home = prox_mean(home_geo_df, geohashval)

               # Area per unit
               area = prox_mean(area_geo_df, geohashval)

               print(opex, zrent, cap, home, area)

               # Function call to obtain rents
               result = calc_rev(address, built, space_acq, units_acq, assVal, opex, taxAmt, taxRate, zrent, cap, owner, aircon, pool, condition, constructionType, parkingType, numBldgs, zrent, home, area, lastSaleDate, geohashval)

               # Revenue / Sq.ft / Year
               price = result["y_pred"] * 12

               '''
               Set of Comps - CMBS
               '''

               # Lease Comp set
               df_cmbs = result["df_cmbs"]

               if df_cmbs.shape[0] > 0:

                   # Median Revenue / Sq.ft / Year
                   market_price = df_cmbs["Revenue_per_sqft_year"].apply(clean_currency).median()

                   # Generate Address string
                   addr_cols = ["Address", "City", "State", "Zip_Code"]

                   df_cmbs['Address_Comp'] = df_cmbs[addr_cols].apply(lambda row: ' '.join(row.values.astype(str)), axis=1)

                   # Columns for customdata
                   cd_cols = ['Property_Name','Address_Comp','Size','Year_Built','zrent_quantile_random','zrent_median','Preceding_Fiscal_Year_Revenue','Opex','Occ','EstRentableArea','EstValue','lastSaleDate','Distance']

                   propname = df_cmbs["Property_Name"]

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
               Set of Comps - Non CMBS
               '''

               df_noncmbs = result["df_noncmbs"]

               if df_noncmbs.shape[0] > 0:

                   # Estimate Annual Revenue
                   if 'unit_count' in list(df_noncmbs.columns):
                       df_noncmbs['unit_count'] = pd.to_numeric(df_noncmbs['unit_count'], errors='coerce')
                       df_noncmbs['EstRevenue'] = (df_noncmbs['unit_count'] * df_noncmbs['avg_rent'])*12

                       # Columns for groupby
                       grpcols = ['imgSrc','name','address_comp','Lat','Long','unit_count','year_built','EstRentableArea','EstValue','building_amenities','Distance']

                   # Aggregate with rent dict
                   df_noncmbs['rents'] = df_noncmbs[['bed_rooms', 'avg_rent']].to_dict(orient='records')

                   # Aggregate with rent dict
                   dff_noncmbs = df_noncmbs.groupby(grpcols, as_index=False).agg({'EstRevenue': 'mean', 'rents': list})

                   # Columns for customdata
                   cd_cols = ['imgSrc','name','address_comp','unit_count','year_built','rents','EstRevenue','EstRentableArea','EstValue','building_amenities','Distance']

                   propname = dff_noncmbs["name"]

                   datap.append({

                                   "type": "scattermapbox",
                                   "lat": dff_noncmbs['Lat'],
                                   "lon": dff_noncmbs['Long'],
                                   "name": "Location",
                                   "hovertext": propname,
                                   "showlegend": False,
                                   "hoverinfo": "text",
                                   "mode": "markers",
                                   "clickmode": "event+select",
                                   "customdata": dff_noncmbs.loc[:,cd_cols].values,
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

               # create ranges
               noi = float(price) * int(space_acq)

               min = noi - (10*noi/100)
               max = noi + (10*noi/100)

               min_fmt = float(min)/1000000
               max_fmt = float(max)/1000000

               # custom data for subject property
               cdata = np.asarray([address, units_acq, built, space_acq, min_fmt, max_fmt, assVal, taxAmt])

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



               # Subject Property Location
               datap.append({
                             "type": "scattermapbox",
                             "lat": [Lat],
                             "lon": [Long],
                             "hovertext": 'Subject Property',
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

        if n_clicks and result:

           poi = {"Lat": layout_lat, "Long": layout_lon}

           layout["mapbox"] = {
                                **layout["mapbox"],
                                **{
                                    "layers": [
                                        {
                                            "source": json.loads(
                                                # convert radius to meters * miles
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


        if n_clicks:
            # Sub columns for DataTable
            df_cmbs['bed_rooms'] = "Overall"

            df_cmbs_sub = df_cmbs[['Property_Name','Zip_Code','bed_rooms','zrent_median','Preceding_Fiscal_Year_Revenue','EstRentableArea','Most_Recent_Physical_Occupancy','Year_Built','Size','EstRevenueMonthly','Revenue_per_sqft_year','Opex','EstValue','Distance']]

            if df_noncmbs.shape[0] > 0:
                df_noncmbs_sub = df_noncmbs[['name','addressZipcode','bed_rooms','avg_rent','EstRevenue','EstRentableArea','year_built','unit_count','EstValue','Distance']]
            else:
                df_noncmbs_sub = df_noncmbs

            df_cmbs_img = df_cmbs[['Property_Name','Image_dicts']]

            return ({"data": datap, "layout": layout}, {"predicted": price, "market_price": market_price}, listToDict(details), {"df_cmbs": df_cmbs_sub.to_dict('records'), "df_noncmbs": df_noncmbs_sub.to_dict('records')}, df_cmbs_img.to_dict('records'), {"display": "none"}, no_update, no_update)
        else:
            df_sub = df[['Property_Name','Image_dicts']]
            return ({"data": datac, "layout": layout}, {"predicted": price, "market_price": market_price}, listToDict(details), no_update, df_sub.to_dict('records'), {"display": "none"}, no_update, no_update)

    else:
        #PreventUpdate
        return (no_update, no_update, no_update, no_update, no_update, {"display": "none"}, no_update, no_update)


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

    try:

        if n_clicks and api_store['propdetails'] and space and api_store['propdetails'][13] is not None > 0:

            # 10% upside
            upside10 = (10 * float(api_store['propdetails'][13]))/float(api_store['propdetails'][13])
            upside10 = float(api_store['propdetails'][13]) + upside10

            # Rents + Occupancy, add condition to check for revenue and occupancy below market level

            # If potential Revenue is < than 10% upside of existing revenue
            if float(price_values['predicted'] * space) <= upside10:

                img_link = "https://stroom-images.s3.us-west-1.amazonaws.com/low_indicator.png"

                card_img_src = img_link
                card_header = "Low Income Growth and Upside Potential"
                card_text = "Rental revenue is close to comparable market value."

                return (card_img_src, card_header, card_text)

            elif float(price_values['predicted'] * space) >= float(api_store['propdetails'][13]):

                # Calculate percentage upside
                diff = float(price_values['predicted'] * space) - float(api_store['propdetails'][13])
                avg = (float(price_values['predicted'] * space) + float(api_store['propdetails'][13]))/2
                pct_upside = int((diff / avg) * 100)

                if pct_upside >= 40:
                    pct_upside = 40

                img_link = "https://stroom-images.s3.us-west-1.amazonaws.com/high_indicator.png"

                card_img_src = img_link
                card_header = "{}%-{}% Income Growth and Upside Potential".format(pct_upside-2, pct_upside+2)
                card_text = "Rental revenue is lower than comparable market value."

                return (card_img_src, card_header, card_text)

        elif n_clicks:

            img_link = "https://stroom-images.s3.us-west-1.amazonaws.com/no-data.png"

            card_img_src = img_link
            card_header = "Not enough data"
            card_text = "Upload proforma to estimate Value-Add Potential"

            return (card_img_src, card_header, card_text)

        else:

            img_link = ""

            card_img_src = img_link
            card_header = ""
            card_text = ""

            return (card_img_src, card_header, card_text)

    except Exception as e:
        print('Exception upside', e)

        img_link = ""

        card_img_src = img_link
        card_header = ""
        card_text = ""

        return (card_img_src, card_header, card_text)

# Update DataTable and Local Level Stats
@application.callback([

                          Output("comps-table", "data"),
                          Output("table-store", "data"),
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

       df_cmbs['bed_rooms'] = 'Overall'

       df_cmbs_v1 = pd.DataFrame(df_cmbs, columns = ["Property_Name","Type","Year_Built","bed_rooms","Size","Preceding_Fiscal_Year_Revenue",
                                                     "Most_Recent_Physical_Occupancy", "SubMarket", "City", "MSA", "EstRevenueMonthly",
                                                     "Opex", "Address", "Zip_Code", "zrent_median", "Revenue_per_sqft_year", "EstRentableArea",
                                                     "EstValue","Distance"])


       # Prepare Non CMBS data
       df_noncmbs = pd.DataFrame(result_store["df_noncmbs"])

       df_noncmbs['Type'] = 'Non CMBS'

       df_noncmbs.rename(columns={'name': 'Property_Name',
                                  'addressZipcode': 'Zip_Code',
                                  'avg_rent': 'zrent_median',
                                  'EstRevenue': 'Preceding_Fiscal_Year_Revenue',
                                  'year_built': 'Year_Built',
                                  'unit_count': 'Size'}, inplace=True)


       # Append
       df = pd.concat([df_cmbs_v1, df_noncmbs], ignore_index=True)

       # Apply formatting
       df['Most_Recent_Physical_Occupancy'] = df['Most_Recent_Physical_Occupancy'].apply(clean_percent).astype('float')
       df['EstRevenueMonthly'] = df['EstRevenueMonthly'].apply(clean_currency).astype('float')
       df['Opex'] = df['Opex'].apply(clean_currency).astype('float')
       df['Revenue_per_sqft_year'] = df['Revenue_per_sqft_year'].apply(clean_currency).astype('float')
       df['EstValue'] = df['EstValue'].apply(clean_currency).astype('float')

       df.reset_index(inplace = True)

       df.fillna(0, inplace = True)

       # Filter by 1 bedroom, if 1 bed doesn't exist get the first value.
       df.groupby(['Property_Name','Zip_Code','Type','SubMarket','City','MSA','Address','bed_rooms']).agg({
                                                                                                            'Year_Built': lambda x:stats.mode(x)[0][0], #mode
                                                                                                            'Size': np.mean,
                                                                                                            'Preceding_Fiscal_Year_Revenue': np.mean,
                                                                                                            'Most_Recent_Physical_Occupancy': lambda x:stats.mode(x)[0][0],
                                                                                                            'EstRevenueMonthly': np.mean,
                                                                                                            'Opex': np.mean,
                                                                                                            'zrent_median': np.mean,
                                                                                                            'Revenue_per_sqft_year': np.mean,
                                                                                                            'EstRentableArea': np.mean,
                                                                                                            'EstValue': np.mean,
                                                                                                            'Distance': np.mean
                                                                                                         }).reset_index()

       # Drop duplicates
       #df.drop_duplicates(subset=['Property_Name'], keep='first', inplace=True)


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

       if df['zrent_median'].isna().sum() != len(df['zrent_median']):
           df['zrent_median'] = df['zrent_median'].apply('${:,.0f}'.format)

       if df['EstValue'].isna().sum() != len(df['EstValue']):
           df['EstValue'] = df['EstValue'].apply('${:,.0f}'.format)

       if df['Most_Recent_Physical_Occupancy'].isna().sum() != len(df['Most_Recent_Physical_Occupancy']):
           df['Most_Recent_Physical_Occupancy'] = df['Most_Recent_Physical_Occupancy'].apply('{:,.0f}%'.format)

       df['Year_Built'] = df['Year_Built'].astype('string').replace('\.0', '', regex=True)

       df['Distance'] = df['Distance'].apply('{:,.1f}'.format)

       df.replace(["$nan",""], 'nan', inplace=True)

       df.fillna('nan', inplace=True)

       comps_data = df.to_dict("rows")

       # Clean up columns to calculate stats
       #df['Most_Recent_Physical_Occupancy'] = df['Most_Recent_Physical_Occupancy'].apply(clean_percent).astype('float')

       df1 = df

       # Rent col
       if df1['zrent_median'].isna().sum() != len(df1['zrent_median']):
           df1['zrent_median'] = df1['zrent_median'].apply(clean_currency).astype(float)
           rent_col = df1[df1['zrent_median'] > 0]
           rent_avg = rent_col['zrent_median'].median()
           rent_avg = "${:,.0f}".format(rent_avg)
       else:
           rent_avg = "-"

       # Monthly Revenue
       if df1['EstRevenueMonthly'].isna().sum() != len(df1['EstRevenueMonthly']):
           df1['EstRevenueMonthly'] = df1['EstRevenueMonthly'].apply(clean_currency).astype(float)
           revenue_col = df1[df1['EstRevenueMonthly'] > 0]
           revenue_avg = revenue_col['EstRevenueMonthly'].median()
           revenue_avg = "${:,.0f}".format(revenue_avg)
       else:
           revenue_avg = "-"

       # Physical occupancy
       if df1['Most_Recent_Physical_Occupancy'].isna().sum() != len(df1['Most_Recent_Physical_Occupancy']):
           df1['Most_Recent_Physical_Occupancy'] = df1['Most_Recent_Physical_Occupancy'].apply(clean_percent).astype(float)
           occ_col = df1[df1['Most_Recent_Physical_Occupancy'] > 0]
           occ_avg = occ_col['Most_Recent_Physical_Occupancy'].mean()
           occ_avg = "{:,.1f}%".format(occ_avg)
       else:
           occ_avg = "-"

       # Format / clean up
       if df1['Opex'].isna().sum() != len(df1['Opex']):
           df1['Opex'] = df1['Opex'].apply(clean_currency).astype('float')
           opex_col = df1[df1['Opex'] > 0]
           opex_avg = opex_col['Opex'].mean()
           opex_avg = "${:,.0f}".format(opex_avg)
       else:
           opex_avg = "-"

       return (comps_data, comps_data, rent_avg, occ_avg, opex_avg)

    else:

       return (no_update, no_update, no_update, no_update, no_update)



# Update CMBS modal
@application.callback(

                        [

                             Output("modal-1","is_open"),
                             Output("carousel","children"),
                             Output("prop_name","children"),
                             Output("Address","children"),
                             Output("Size","children"),
                             Output("Yr_Built","children"),
                             Output("RentCMBS", "children"),
                             Output("Revenue","children"),
                             Output("Opex","children"),
                             Output("occ-modal","children"),
                             Output("rent-area-modal","children"),
                             Output("assessed-value","children"),
                             Output("sale-date","children"),
                             Output("distance","children")

                        ],

                        [
                             # Button clicks
                             Input("map-graph1","clickData"),
                             Input("close","n_clicks")
                        ],

                        [
                              State("modal-1", "is_open"),
                              State("query-store", "data")
                        ],

                    )
def display_popup1(clickData, n_clicks, is_open_c, query_store):

    if clickData and len(clickData['points'][0]['customdata']) == 13:

        res = json.dumps(clickData, indent=2)

        print("clickData response", res)

        Name = clickData["points"][0]["customdata"][0]
        Address = clickData["points"][0]["customdata"][1]
        Size = clickData["points"][0]["customdata"][2]
        Built = clickData["points"][0]["customdata"][3]

        '''
        Rents data
        '''
        # Rents Quantiles
        rent_quantiles = clickData["points"][0]["customdata"][4]

        rent_median = clickData["points"][0]["customdata"][5]
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

        Revenue = clickData["points"][0]['customdata'][6]
        Opex = clickData["points"][0]['customdata'][7]
        Occupancy = clickData["points"][0]["customdata"][8]
        RentArea = clickData["points"][0]["customdata"][9]
        AssessedValue = clickData["points"][0]["customdata"][10]
        lastSaleDate = clickData["points"][0]["customdata"][11]
        Distance = clickData["points"][0]["customdata"][12]

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
                url = create_presigned_url('gmaps-images-6771', 'property_images/no_imagery.png')

                carousel = dbc.Carousel(
                                        items=[
                                                {"key": "1", "src": url, "img_style": {"width": "300px", "height": "300px"}},
                                        ],
                                        controls=False,
                                        indicators=False,
                            )

            if Revenue in ["null", 0, None]:
                Revenue_fmt == "N/A"
            else:
                Revenue = float(Revenue)
                Revenue_fmt = "${:,.0f}".format(Revenue)

            if Opex in ["null", 0, None]:
                Opex_fmt == "-"
            else:
                Opex = float(Opex)
                Opex_fmt = "${:,.0f}".format(Opex)

            if Occupancy in ["null", "0%", 0, None]:
                Occupancy_fmt == "-"
            else:
                Occupancy = Occupancy.strip('%')
                Occupancy = float(Occupancy)
                Occupancy_fmt = "{:.0f}%".format(Occupancy)

            if RentArea in ["null", 0, None]:
                RentArea_fmt = "-"
            else:
                RentArea = float(RentArea)
                RentArea_fmt = "{:,.0f} sq.ft".format(RentArea)

            if AssessedValue in ["null", 0, None]:
                AssessedValue_fmt = "-"
            else:
                AssessedValue = float(AssessedValue)
                AssessedValue_fmt = "${:,.0f}".format(AssessedValue)

            if lastSaleDate in [None, "null"]:
                lastSaleDate_fmt = "-"
            else:
                lastSaleDate_fmt = lastSaleDate

            if Distance in [None, "null", "N/A"]:
                Distance_fmt = "-"
            else:
                Distance = float(Distance)
                Distance_fmt = "{:,.1f} miles".format(Distance)

        return(not is_open_c, carousel, Name, Address, Size, Built, Rents_fmt, Revenue_fmt, Opex_fmt, Occupancy_fmt, RentArea_fmt, AssessedValue_fmt, lastSaleDate_fmt, Distance_fmt)

    elif n_clicks:
        return is_open_c

    else:
        return no_update

# Modal Subject Property
@application.callback(
                          [

                               Output("modal-2","is_open"),
                               Output("carousel-s","children"),
                               Output("Address-s","children"),
                               Output("Size-s","children"),
                               Output("Yr_Built-s","children"),
                               Output("rent-area-modal-s","children"),
                               Output("Rents-s","children"),
                               Output("Revenue-s","children"),
                               Output("assessed-val-s","children"),
                               Output("prop-tax-s","children")

                          ],

                          [
                               # Button clicks
                               Input("map-graph1","clickData"),
                               Input("close-s","n_clicks")
                          ],

                          [
                                State("modal-2", "is_open"),
                                State("query-store", "data"),
                                State("table-store", "data")
                          ],
                    )
def display_popup2(clickData, n_clicks_sp, is_open_sp, query_store, table_store):

    if clickData and len(clickData['points'][0]['customdata']) == 8:

        res = json.dumps(clickData, indent=2)

        print("clickData response", res)

        # subject property
        Address = clickData["points"][0]["customdata"][0]
        Size = clickData["points"][0]["customdata"][1]
        Built = clickData["points"][0]["customdata"][2]
        RentArea = clickData["points"][0]["customdata"][3]
        ExpRevenueMin = clickData["points"][0]["customdata"][4]
        ExpRevenueMax = clickData["points"][0]["customdata"][5]
        AssessedVal = clickData["points"][0]["customdata"][6]
        PropTax = clickData["points"][0]["customdata"][7]

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

        # Calculate Rents from Comps Table
        if table_store:
            df = pd.DataFrame(table_store)
            s = df['zrent_median'].apply(clean_currency).astype(float)

            rmin = s.min()
            rmax = s.max()

            rents_fmt = "${:,.0f} - ${:,.0f}".format(rmin, rmax)
        else:
            rents_fmt = "-"

        # Formatted for default view (NA) and post button click and handling of None value
        if RentArea in ["null", 0, None]:
            RentArea_fmt = "-"
        else:
            RentArea = int(RentArea)
            RentArea_fmt = "{:,.0f} sq.ft".format(RentArea)

        if ExpRevenueMin in ["null", None]:
            ExpRevenue_fmt = "-"
        else:
            ExpRevenueMin = float(ExpRevenueMin)
            ExpRevenueMax = float(ExpRevenueMax)

            if ExpRevenueMin > -1 and ExpRevenueMax <= 1 and ExpRevenueMax > -1 and ExpRevenueMax < 1:
                ExpRevenueMin = ExpRevenueMin * 1000
                ExpRevenueMax = ExpRevenueMax * 1000
                ExpRevenue_fmt = "${:.0f}K - ${:.0f}K".format(ExpRevenueMin, ExpRevenueMax)

            elif ExpRevenueMin > -1 and ExpRevenueMin < 1 and ExpRevenueMax > 1:
                ExpRevenueMin = ExpRevenueMin * 1000
                ExpRevenue_fmt = "${:.0f}K - ${:.1f}M".format(ExpRevenueMin, ExpRevenueMax)

            elif ExpRevenueMin > 1 and ExpRevenueMax > 1:
                ExpRevenue_fmt = "${:.1f}M - ${:.1f}M".format(ExpRevenueMin, ExpRevenueMax)

            else:
                ExpRevenue_fmt = "${:.1f}M - ${:.1f}M".format(ExpRevenueMin, ExpRevenueMax)

        if AssessedVal in ["null", None]:
            AssessedVal_fmt = "-"
        else:
            AssessedVal = float(AssessedVal)
            AssessedVal_fmt = "${:,.0f}".format(AssessedVal)

        if PropTax in ["null", None]:
            PropTax_fmt = "-"
        else:
            PropTax = float(PropTax)
            PropTax_fmt = "${:,.0f}".format(PropTax)

        return(not is_open_sp, carousel, Address, Size, Built, RentArea_fmt, rents_fmt, ExpRevenue_fmt, AssessedVal_fmt, PropTax_fmt)

    elif n_clicks_sp:
        return is_open_sp

    else:
        return no_update

# Modal Zillow
@application.callback(
                          [

                               Output("modal-3","is_open"),
                               Output("carousel-z","children"),
                               Output("prop_name_z","children"),
                               Output("Address_z","children"),
                               #Output("Size_z","children"),
                               #Output("Yr_Built_z","children"),

                               Output("RentSZ", "children"),
                               Output("Rent1BrZ", "children"),
                               Output("Rent2BrZ", "children"),
                               Output("Rent3BrZ", "children"),

                               #Output("Revenue_z","children"),
                               #Output("rent-area-modal-z","children"),
                               #Output("assessed-value-z","children"),
                               Output("ameneties_z","children"),
                               Output("distance_z","children"),

                          ],

                          [
                               # Button clicks
                               Input("map-graph1","clickData"),
                               Input("close-z","n_clicks")
                          ],

                          [
                                State("modal-3", "is_open"),
                                State("query-store", "data")
                          ],
                    )
def display_popup3(clickData, n_clicks_z, is_open_z, query_store):

    if clickData and len(clickData['points'][0]['customdata']) == 11:

        img_link = clickData["points"][0]["customdata"][0]
        Name = clickData["points"][0]["customdata"][1]
        Address = clickData["points"][0]["customdata"][2]
        Size = clickData["points"][0]["customdata"][3]
        Built = clickData["points"][0]["customdata"][4]

        '''
        Parse rental data
        '''

        l0 = []
        l1 = []
        l2 = []
        l3 = []

        r0_fmt = None
        r1_fmt = None
        r2_fmt = None
        r3_fmt = None

        for i in clickData["points"][0]["customdata"][5]:

            # Check Apt type and calc. Avg. rent
            if i['bed_rooms'] == 0:
                l0.append(i)

                if len(l0) > 0:
                    r0 = int(sum(p['avg_rent'] for p in l0))/len(l0)
                    r0_fmt = "${:,.0f}".format(r0)
                else:
                    r0_fmt = "N/A"

            if i['bed_rooms'] == 1:
                l1.append(i)

                if len(l1) > 0:
                    r1 = int(sum(p['avg_rent'] for p in l1))/len(l1)
                    r1_fmt = "${:,.0f}".format(r1)
                else:
                    r1_fmt = "N/A"

            if i['bed_rooms'] == 2:
                l2.append(i)

                if len(l2) > 0:
                    r2 = int(sum(p['avg_rent'] for p in l2))/len(l2)
                    r2_fmt = "${:,.0f}".format(r2)
                else:
                    r2_fmt = "N/A"

            if i['bed_rooms'] == 3:
                l3.append(i)

                if len(l3) > 0:
                    r3 = int(sum(p['avg_rent'] for p in l3))/len(l3)
                    r3_fmt = "${:,.0f}".format(r3)
                else:
                    r3_fmt = "N/A"

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
            Name_fmt = "-"
        else:
            Name_fmt = Name

        if Address in [None, 'nan']:
            Address_fmt = "-"
        else:
            Address_fmt = Address

        if Size in [None, 'nan']:
            Size_fmt = "-"
        else:
            Size_fmt = int(Size)

        if Built in [None, 'nan']:
            Built_fmt = "-"
        else:
            Built_fmt = int(float(Built))

        if Revenue in [None, 'nan', 0]:
            Revenue_fmt = "-"
        else:
            Revenue = float(Revenue)
            Revenue_fmt = "${:,.0f}".format(Revenue)

        if RentArea in [None, 'nan']:
            RentArea_fmt = "-"
        else:
            RentArea = int(float(RentArea))
            RentArea_fmt = "{:,.0f} sq.ft".format(RentArea)

        if AssessedVal in [None, 'nan']:
            AssessedVal_fmt = "-"
        else:
            AssessedVal = int(float(AssessedVal))
            AssessedVal_fmt = "${:,.0f}".format(AssessedVal)

        if Ameneties in [None, 'nan']:
            Ameneties_fmt = "-"
        else:
            Ameneties = ast.literal_eval(Ameneties)
            Ameneties = ', '.join(Ameneties)
            Ameneties_fmt = Ameneties

        if Distance == "N/A":
            Distance_fmt = Distance
        else:
            Distance = float(Distance)
            Distance_fmt = "{:,.1f} miles".format(Distance)

        return(not is_open_z, carousel, Name_fmt, Address_fmt, r0_fmt, r1_fmt, r2_fmt, r3_fmt, Ameneties_fmt, Distance_fmt)

    elif n_clicks_z:
        return is_open_z

    else:
        return no_update




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
