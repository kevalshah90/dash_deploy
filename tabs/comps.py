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
from collections import defaultdict
import mapbox
import geopandas as gpd
import shapely.geometry
from scipy import spatial
from dash.dash import no_update
from dash.exceptions import PreventUpdate
from base_rent_calc import calc_rent, append_prop, walkscore
from handle_images import getPlace_details
from funcs import clean_percent, clean_currency, get_geocodes, nearby_places, streetview, create_presigned_url, gen_ids, str_num, listToDict, prox_mean, attom_api_avalue
from draw_polygon import poi_poly
from sklearn.neighbors import BallTree
from parse import parse_contents
import string
import json
import os
import os.path
import ast
import random
import geocoder
import pygeohash as gh
import google_streetview.api
import requests

# Google Maps API key
import googlemaps
gmaps = googlemaps.Client(key="AIzaSyC0XCzdNwzI26ad9XXgwFRn2s7HrCWnCOk")

MAPBOX_KEY="pk.eyJ1Ijoia2V2YWxzaGFoIiwiYSI6ImNqbW1nbG90MDBhNTQza3IwM3pvd2I3bGUifQ.dzdTsg69SdUXY4zE9s2VGg"
token = MAPBOX_KEY
Geocoder = mapbox.Geocoder(access_token=token)


# Read Multi-Family data
df_lease_sf_mf = pd.read_csv(os.getcwd() + "/data/LeaseComp_sf_la_mf_agg_v11_raw.csv")
df_lease_sf_mf = df_lease_sf_mf[df_lease_sf_mf['Revenue_per_sqft_month'] > 0]

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
                                     dbc.CardHeader("Median Rent"),
                                     dbc.CardBody(
                                         [
                                             html.P(id="rent-card", style={"font-size": "1.6em"}),
                                         ]

                                     ),
                                 ],
                                 id="rent-stat",
                                 color="light",
                                 style={"width": "10rem", "margin-left": "-28%", "height": "9em"}
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
                                 style={"width": "10rem", "margin-left": "5%", "height": "9em"}
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
                                 style={"width": "10rem", "margin-left": "5%", "height": "9em"}
                     ),

         ], style={"margin-top":"52em", "margin-left":"31px"}),



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

                                dbc.Label("Property: ", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                dbc.Label("Property:", id="Property"),
                                html.Br(),

                                dbc.Label("Comparable Rent ($/SF Yr.):", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                dbc.Label("Rent:", id="Rent"),
                                html.Br(),

                                dbc.Label("Fiscal Revenue:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                dbc.Label("Revenue:", id="Revenue"),
                                html.Br(),

                                dbc.Label("Rental rate / Sq.ft / Month:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                dbc.Label("Rental Rate:", id="Rent_rate"),
                                html.Br(),

                                dbc.Label("Avg. Rent / Month (1 Br 750 Sq.ft):", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                dbc.Label("Rental Rate:", id="Rent_monthly"),
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

                                dbc.Label("Property: ", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                dbc.Label("Property:", id="Property-s"),
                                html.Br(),

                                dbc.Label("Rentable Area:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                dbc.Label("Rentable Area:", id="rent-area-modal-s"),
                                html.Br(),

                                dbc.Label("Expected Fiscal Revenue:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                dbc.Label("Revenue:", id="Revenue-s"),
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

                                {"label": "Premium", "value": "premium"},
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

                    columns=[{"id":"Property Name","name":"Property Name"},
                             {"id":"Property Type","name":"Property Type"},
                             {"id":"Zip Code","name":"Zip Code"},
                             {"id":"Preceding Fiscal Year Revenue","name": "Revenue"},
                             {"id":"EstRentableArea","name": "Area (Sq.ft)"},
                             {"id":"Most Recent Physical Occupancy","name":"Occupancy"},
                             {"id":"Year Built","name": "Year Built"},
                             {"id":"Size","name": "Number of Units"},
                             {"id":"Estimated_Rent","name":"Rent / SF Yr."},
                             {"id":"Rent_monthly","name":"Avg. Rent (Typical 1 Bed)"},
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
                    row_deletable=False,
                    export_format="csv"
                ),


            ], className="table-style"),

        ]),

        html.Div(id="dummy-div"),

        dcc.Store(id='result-store', storage_type='memory'),
        dcc.Store(id="api-store", storage_type='memory')

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

    if address:
        if len(address) > 8:
            g = geocoder.mapbox(address, key=token)
            geojson = g.json
            addr = geojson["address"]

            coords = [geojson['lat'], geojson['lng']]

            geohashval = gh.encode(geojson['lat'], geojson['lng'], precision=5)

            # Convert to radian and search pandas dataframe
            X = np.deg2rad(df_lease_sf_mf[['Lat', 'Long']].values)
            y = np.deg2rad(np.array([coords]))

            tree = BallTree(X, leaf_size=2)
            dist, ind = tree.query(y)

    else:
        raise PreventUpdate


    if geojson:

        # Convert radians to miles and check the distance, 0.05 = precision / cutoff
        if dist[0][0] * 3963.1906 <= 0.05:

            details = df_lease_sf_mf[['Year Built','Renovated','EstRentableArea','Size','Most Recent Physical Occupancy','Operating Expenses at Contribution','propertyTaxAmount','taxRate']].iloc[ind[0][0]].tolist()

            return (int(details[0]), details[1], int(details[2]), int(details[3]), {"attom_api": None, "geohash": geohashval, "propdetails": details})

        else:

            # Address
            addr1 = geojson['housenumber'] + " " + geojson['raw']['text']
            addr2 = geojson['city'] + " " + geojson['state'] + " " + geojson['postal']

            # ATTOM API Call
            #avdata = attom_api_avalue(addr1, addr2)
            #avdata = json.loads(avdata.decode("utf-8"))

            # Dummy call
            avdata = {'status': {'version': '1.0.0',
                      'code': 0,
                      'msg': 'SuccessWithResult',
                      'total': 1,
                      'page': 1,
                      'pagesize': 10,
                      'transactionID': 'be285468d6847043b4a91148317e310f'},
                     'property': [{'identifier': {'Id': 151049065,
                        'fips': '06075',
                        'apn': '3716 -024',
                        'attomId': 151049065},
                       'lot': {'lotnum': '24', 'pooltype': 'NO POOL'},
                       'area': {'blockNum': '3716',
                        'loctype': 'VIEW - NONE',
                        'countrysecsubd': 'San Francisco',
                        'countyuse1': '104  ',
                        'muncode': 'SF',
                        'munname': 'SAN FRANCISCO',
                        'subdname': 'RINCON TOWERS 88 HOWARD STREET',
                        'taxcodearea': '1000'},
                       'address': {'country': 'US',
                        'countrySubd': 'CA',
                        'line1': '88 HOWARD ST',
                        'line2': 'SAN FRANCISCO, CA 94105',
                        'locality': 'SAN FRANCISCO',
                        'matchCode': 'ExaStr',
                        'oneLine': '88 HOWARD ST, SAN FRANCISCO, CA 94105',
                        'postal1': '94105',
                        'postal2': '1645',
                        'postal3': 'C012'},
                       'location': {'accuracy': 'Rooftop',
                        'latitude': '37.792265',
                        'longitude': '-122.392848',
                        'distance': 0.0,
                        'geoid': 'CO06075, CS0693067, DB0634410, ND0004795444, ND0004846521, PL0667000, SB0000139051, SB0000139554, SB0000140188, SB0000140189, SB0000140190, SB0000141943, SB0000141944, SB0000143750, SB0000143751, SB0000143752, SB0000147276, SB0000147277, SB0000149055, SB0000149056, SB0000150840, SB0000152671, ZI94105'},
                       'summary': {'absenteeInd': 'ABSENTEE(MAIL AND SITUS NOT =)',
                        'propclass': 'Apartment',
                        'propsubtype': 'Residential',
                        'proptype': 'APARTMENT',
                        'yearbuilt': 1989,
                        'propLandUse': 'APARTMENT',
                        'propIndicator': '22',
                        'legal1': 'SUBD:RINCON TOWERS 88 HOWARD STREET'},
                       'utilities': {},
                       'building': {'size': {'bldgsize': 212246,
                         'grosssize': 212246,
                         'grosssizeadjusted': 212246,
                         'livingsize': 212246,
                         'sizeInd': 'LIVING SQFT',
                         'universalsize': 212246},
                        'rooms': {},
                        'interior': {},
                        'construction': {'constructiontype': 'STEEL', 'frameType': 'STEEL'},
                        'parking': {},
                        'summary': {'levels': 23,
                         'unitsCount': '320',
                         'view': 'VIEW - NONE',
                         'viewCode': '000'}},
                       'vintage': {'lastModified': '2021-11-9', 'pubDate': '2021-11-9'},
                       'assessment': {'appraised': {},
                        'assessed': {'assdimprpersizeunit': 286.29,
                         'assdimprvalue': 60762929,
                         'assdlandvalue': 40242777,
                         'assdttlpersizeunit': 475.89,
                         'assdttlvalue': 101005706},
                        'calculations': {'calcimprind': 'ASSESSED VALUE',
                         'calcimprpersizeunit': 286.29,
                         'calcimprvalue': 60762929,
                         'calclandind': 'ASSESSED VALUE',
                         'calclandvalue': 40242777,
                         'calcttlind': 'ASSESSED VALUE',
                         'calcttlvalue': 101005706,
                         'calcvaluepersizeunit': 475.89},
                        'market': {},
                        'tax': {'taxamt': 1224714.1, 'taxpersizeunit': 5.77, 'taxyear': 2021}}}]}

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
                          Output("result-store", "data")

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

    # Update this to adjust map layout.
    # Default map view

    # sf bay area
    layout_lat = 37.7749
    layout_lon = -122.4194

    zoom = 12

    price = 0

    details = None

    result = None

    data = []

    if proptype == "Multi-Family":

        # Plot sample properties - match with starting view of the map
        df = df_lease_sf_mf[df_lease_sf_mf['County'] == "San Francisco"]

        #rent = df["Rent"]

        # Generate Address string
        addr_cols = ["Address", "City", "State", "Zip Code"]

        df['Address_Comp'] = df[addr_cols].apply(lambda row: ' '.join(row.values.astype(str)), axis=1)

        df['Rent'] = "N/A"
        df['Distance'] = "N/A"

        # Columns for customdata
        cd_cols = ['Property Name','Address_Comp','Size','Year Built','Property Type','Rent','Preceding Fiscal Year Revenue','Revenue_per_sqft_month','Occ.','EstRentableArea','EstValue','lastSaleDate','Distance']

        data.append({

                        "type": "scattermapbox",
                        "lat": df['Lat'],
                        "lon": df['Long'],
                        "name": "Location",
                        #"hovertext": rent,
                        "showlegend": False,
                        "hoverinfo": "text",
                        "mode": "markers",
                        "customdata": df.loc[:,cd_cols].values,
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

        # If storage component is not None
        # if comps_store is not None and not ctx.triggered:
        #     return ({"data" : comps_store["map"]["data"], "layout": comps_store["map"]["layout"]}, price)

        if n_clicks:

           # Create geo-aggregated dicts for occupancy, opex, tax rate and tax amount
           occ_geo = dict()
           opex_geo = dict()
           taxRate_geo = dict()
           taxAmt_geo = dict()
           estVal_geo = dict()
           rent1Br_geo = dict()

           for name, group in df_lease_sf_mf.groupby(['geohash']):

               # Occupancy
               group['Most Recent Physical Occupancy'] = group['Most Recent Physical Occupancy'].apply(clean_percent).astype('float')
               occ_geo[name] = group[group['Most Recent Physical Occupancy'] > 0]['Most Recent Physical Occupancy'].mean()
               # Dict to pandas dataframe
               occ_geo_df = pd.DataFrame(zip(occ_geo.keys(), occ_geo.values()), columns=['geohash', 'value'])

               # Opex
               group['Operating Expenses at Contribution'] = group['Operating Expenses at Contribution'].apply(clean_currency).astype('float')
               opex_geo[name] = group[group['Operating Expenses at Contribution'] > 0]['Operating Expenses at Contribution'].mean()
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
           print("api store", api_store)

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
           result = calc_rent(address, proptype, built, space_acq, units_acq, ameneties_count, assVal, occupancy, opex, taxAmt, taxRate, rent_1Br, geohashval)

           price = result["y_pred"] * 12

           # Lease Comp set
           result_df = result["df_lease"]

           # Assign pandas series
           rent = result_df["Estimated_Rent"]
           propname = result_df["Property Name"]

           # Generate Address string
           addr_cols = ["Address", "City", "State", "Zip Code"]

           result_df['Address_Comp'] = result_df[addr_cols].apply(lambda row: ' '.join(row.values.astype(str)), axis=1)

           # Columns for customdata
           cd_cols = ['Property Name','Address_Comp','Size','Year Built','Property Type','Estimated_Rent','Preceding Fiscal Year Revenue','Revenue_per_sqft_month','Occ.','EstRentableArea','EstValue','lastSaleDate','Distance']

           # Dictionary for marker symbol
           sym_dict = {"Office": "suitcase",
                       "Multi-Family": "lodging",
                       "Industrial": "circle",
                       "grocery_or_supermarket": "grocery",
                       "hospital": "hospital",
                       "movie_theater": "cinema",
                       "bar": "bar",
                       "restaurant": "restaurant",
                       "post_office": "post",
                       "university": "school",
                       "library": "library",
                       "airport": "airport",
                       "bank": "bank",
                       "light_rail_station": "rail-light",
                       "primary_school": "school",
                       "secondary_school": "school",
                       "school": "school",
                       "shopping_mall": "shop",
                       "train_station": "rail",
                       "transit_station": "rail-metro",
                       "gym": "swimming",
                       "pharmacy": "pharmacy",
                       "pet_store": "dog-park",
                       "museum": "museum" }


           # Set of Lease Comps
           data.append({

                        "type": "scattermapbox",
                        "lat": result_df["Lat"],
                        "lon": result_df["Long"],
                        "name": "Location",
                        "hovertext": propname,
                        "showlegend": False,
                        "hoverinfo": "text",
                        "mode": "markers",
                        "clickmode": "event+select",
                        "customdata": result_df.loc[:,cd_cols].values,
                        "marker": {
                                   "symbol": "circle",
                                   "size": 12,
                                   "opacity": 0.7,
                                   "color": "black"
                                  }
                        }
           )

           # Add POI data layer
           df_nearby = nearby_places(address)

           # Check if DataFrame was returned
           if isinstance(df_nearby, pd.DataFrame):

               # Create a list of symbols by dict lookup
               sym_list = []

               for i in df_nearby['type_label']:
                   typ = sym_dict.get(i)
                   sym_list.append(typ)

               data.append({

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

           layout_lat = Lat
           layout_lon = Long
           zoom = 12

           # Function to obtain geometry of polygon -- radius is passed in meters, 1 mile = 1609
           # gdf = circles(Long, Lat, radius=1609)
           # print("Geometry of Polygon around Points", gdf)

           # generate polygon of markers within 5 mile radius of Point of Interest
           # poi = result_df.loc[random.randint(0, len(result_df) - 1), ["Long", "Lat"]].to_dict()
           # gdf = poi_poly(None, poi=poi, radius=1609.34 * 1, include_radius_poly=True)

           # create ranges
           noi = float(price) * int(space_acq)

           min = noi - (10*noi/100)
           max = noi + (10*noi/100)

           min_fmt = float(min)/1000000
           max_fmt = float(max)/1000000

           # custom data for subject property
           cdata = np.asarray([address, units_acq, built, proptype, space_acq, min_fmt, max_fmt])

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
           data.append({
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
                                                poi_poly(None, poi=poi, radius = 1609.34 * 2).to_json()
                                            ),
                                            "below": "traces",
                                            "type": "fill",
                                            "opacity": .1,
                                            "fillcolor": "rgba(128, 128, 128, 0.1)",
                                        }
                                    ]
                                },
           }

        if result:
            return ({"data": data, "layout": layout}, price, listToDict(details), result["df_lease"].to_dict('records'))
        else:
            return ({"data": data, "layout": layout}, price, listToDict(details), no_update)
    else:
        #PreventUpdate
        return (no_update, no_update, no_update, no_update)

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
                          State("comps-table", "columns"),
                          #State("result-store", "data")

                      ]
                      )
def update_table(address, proptype, built, units_acq, space_acq, ameneties, n_clicks, result_store, rows, columns):

    if not result_store:
        raise PreventUpdate

    elif n_clicks and result_store:

       result_df = pd.DataFrame(result_store)

       # subset to first n rows only
       result_df = result_df.sort_values(by=['Estimated_Rent'], ascending=False).head(15)
       result_df = result_df.sample(len(result_df))

       df = pd.DataFrame(result_df, columns = ["Property Name","Year Renovated","Property Type","Year Built","Size",
                                               "Preceding Fiscal Year Revenue","Most Recent Physical Occupancy","Lease Type",
                                               "SubMarket", "City", "MSA", "Estimated_Rent", "Rent_monthly", "Opex", "Address",
                                               "Zip Code", "WalkScore", "TransitScore", "Revenue_per_sqft_month",
                                               "EstRentableArea","EstValue","Distance"])


       # Add Monthly Rent Column
       '''
       For Phoenix, Revenue / Size (# of units) appears to be a close approximation.
       For LA, SD and SF, Rate per sq.ft * 750 appears to be a close approximation.
       '''

       if df['MSA'].mode()[0] == "Phoenix-Mesa-Scottsdale, AZ MSA":
           df['Rent_monthly'] = (df['Revenue_per_sqft_month'] * 750).apply('${:,.0f}'.format)
       else:
           df['Rent_monthly'] = ((df['Preceding Fiscal Year Revenue'] / df['Size'])/12).apply('${:,.0f}'.format)

       # Format columns
       if df['Preceding Fiscal Year Revenue'].isna().sum() != len(df['Preceding Fiscal Year Revenue']):
           df['Preceding Fiscal Year Revenue'] = df['Preceding Fiscal Year Revenue'].apply('${:,.0f}'.format)

       if df['EstRentableArea'].isna().sum() != len(df['EstRentableArea']):
           df['EstRentableArea'] = df['EstRentableArea'].apply('{:,.0f}'.format)

       if df['Opex'].isna().sum() != len(df['Opex']):
           df['Opex'] = df['Opex'].apply('${:,.0f}'.format)

       if df['EstValue'].isna().sum() != len(df['EstValue']):
           df['EstValue'] = df['EstValue'].apply('${:,.0f}'.format)

       df['Distance'] = df['Distance'].apply('{:,.1f}'.format)

       comps_data = df.to_dict("rows")

       # Clean up columns to calculate stats
       df['Most Recent Physical Occupancy'] = df['Most Recent Physical Occupancy'].apply(clean_percent).astype('float')

       df1 = df

       # Format / clean up
       if df1['Opex'].isna().sum() != len(df1['Opex']):
           df1['Opex'] = df1['Opex'].apply(clean_currency).astype('float')
           opex_col = df1[df1['Opex'] > 0]
           opex_avg = opex_col['Opex'].mean()
           opex_avg = "${:,.0f}".format(opex_avg)
       else:
           opex_avg = "N/A"


       # Rent col
       if df1['Estimated_Rent'].isna().sum() != len(df1['Estimated_Rent']):
            # Formatting
            #df1['Estimated_Rent'] = df1['Estimated_Rent'].apply('${:.0f}'.format)
            rent_col = df1[df1['Estimated_Rent'] > 0]
            rent_avg = rent_col['Estimated_Rent'].median()
            rent_avg = "${:,.0f} SF/Yr.".format(rent_avg)
       else:
            rent_avg = "N/A"


       if df1['Most Recent Physical Occupancy'].isna().sum() != len(df1['Most Recent Physical Occupancy']):
           occ_col = df1[df1['Most Recent Physical Occupancy'] > 0]
           occ_avg = occ_col['Most Recent Physical Occupancy'].mean()
           occ_avg = "{:,.1f}%".format(occ_avg)
       else:
           occ_avg = "N/A"

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
                               Output("Property","children"),
                               Output("Rent","children"),
                               Output("Revenue","children"),
                               Output("Rent_rate","children"),
                               Output("Rent_monthly","children"),
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
                               Output("Property-s","children"),
                               Output("rent-area-modal-s","children"),
                               Output("Revenue-s","children")

                          ],

                          [
                               # Button clicks
                               Input("map-graph1","clickData"),
                               Input("comps-button", "n_clicks"),
                               Input("close","n_clicks"),
                               Input("close-s","n_clicks")
                          ],

                          [
                                State("modal-1", "is_open"),
                                State("modal-2", "is_open")
                          ],
                    )
def display_popup(clickData, n_clicks, n_clicks_c, n_clicks_sp, is_open_c, is_open_sp):

    if clickData:

        res = json.dumps(clickData, indent=2)

        print("clickData response", res)

        # Condition for comps clickData
        if len(clickData['points'][0]['customdata']) == 13:

            Name = clickData["points"][0]["customdata"][0]
            Address = clickData["points"][0]["customdata"][1]
            Size = clickData["points"][0]["customdata"][2]
            Built = clickData["points"][0]["customdata"][3]
            Property = clickData["points"][0]["customdata"][4]
            Rent = clickData["points"][0]["customdata"][5]
            Revenue = clickData["points"][0]["customdata"][6]
            RentRate = clickData["points"][0]["customdata"][7]
            Occupancy = clickData["points"][0]["customdata"][8]
            RentArea = clickData["points"][0]["customdata"][9]
            AssessedValue = clickData["points"][0]["customdata"][10]
            lastSaleDate = clickData["points"][0]["customdata"][11]
            Distance = clickData["points"][0]["customdata"][12]

            # Formatting
            Occupancy = float(Occupancy.strip('%'))

            # Monthly Rent - 1 BR, 750 sq.ft apartment
            Rent_monthly = RentRate * 750

            # Construct a list of dictionaries
            # Filter Pandas DataFrame
            df = df_lease_sf_mf[df_lease_sf_mf['Property Name'] == Name]

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

            # formatted Rent for default view (NA) and calculated / post button click and handling of None values
            if Rent == "N/A":
                rent_fmt = Rent
            else:
                rent_fmt = "${:.0f}".format(Rent)

            if Revenue is None:
                Revenue_fmt == "N/A"
            else:
                Revenue_fmt = "${:,.0f}".format(Revenue)

            if RentRate is None:
                RentRate_fmt == "N/A"
            else:
                RentRate_fmt = "${:,.1f} Sq.ft".format(RentRate)

            if Rent_monthly is None:
                RentMon_fmt == "N/A"
            else:
                RentMon_fmt = "${:,.0f}".format(Rent_monthly)

            if Occupancy is None:
                Occupancy_fmt == "N/A"
            else:
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

            return(not is_open_c, carousel, Name, Address, Size, Built, Property, rent_fmt, Revenue_fmt, RentRate_fmt, RentMon_fmt, Occupancy_fmt, RentArea_fmt, AssessedValue_fmt, lastSaleDate_fmt, Distance_fmt, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update)

        elif len(clickData['points'][0]['customdata']) == 7:

            Address = clickData["points"][0]["customdata"][0]
            Size = clickData["points"][0]["customdata"][1]
            Built = clickData["points"][0]["customdata"][2]
            Property = clickData["points"][0]["customdata"][3]
            RentArea = clickData["points"][0]["customdata"][4]
            ExpRevenueMin = clickData["points"][0]["customdata"][5]
            ExpRevenueMax = clickData["points"][0]["customdata"][6]

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
                ExpRevenue_fmt = "${:.1f}M-${:.1f}M".format(float(ExpRevenueMin), float(ExpRevenueMax))

            return(no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, not is_open_sp, carousel, Address, Size, Built, Property, RentArea_fmt, ExpRevenue_fmt)

        elif n_clicks_c:

            return is_open

        elif n_clicks_sp:

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
                "price": price,
                "local_rent": rent_card,
                "propdetails": dummy
               }
