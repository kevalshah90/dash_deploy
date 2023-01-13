# Packages
import pandas as pd
import numpy as np
import dash
from dash.dependencies import Input, Output, State
from dash import dcc
from dash import dash_table, html
import dash_bootstrap_components as dbc
import plotly as py
from plotly import graph_objs as go
from plotly.graph_objs import *
import plotly.figure_factory as ff
import flask
from flask import Flask
from application import application
from datetime import date, datetime, timedelta
from dateutil import relativedelta
from collections import defaultdict
from dash.dash import no_update
import json
import plotly.io as pio
from funcs import DataProcessor
from config import *
from decimal import Decimal
import re
from re import sub
import random
import mapbox
import locale

# Google maps api key
import googlemaps
gmaps = googlemaps.Client(key = os.environ["gkey"])

# Mapbox
token = os.environ["MAPBOX_KEY"]
geocoder = mapbox.Geocoder(access_token=token)

# mysql connection
import pymysql
from sqlalchemy import create_engine

database = 'stroom_main'
engine = create_engine("mysql+pymysql://{}:{}@{}/{}".format(os.environ["user"], os.environ["pwd"], os.environ["host"], database))
con = engine.connect()

layout = html.Div([

   html.Div([

       html.H2("Custom Return Analysis", style={"text-align":"center","margin-left":"15%","margin-top":"1em"}),

   ]),

   dbc.Row(
       [
            # Col 1
            dbc.Col(

                html.Div([

                   # Location - Address
                   dbc.InputGroup(
                       [

                           # dbc.Card(
                           #      dbc.CardBody(
                           #          [
                           #              html.H6("Name:", className="card-title", style={"color":"black", "font-weight": "bold"}),
                           #              html.P(id="propname-card", style={"font-size": "1em"}, className="card-text"),
                           #          ]
                           #      ),
                           #      #className="w-40 mb-3",
                           #      style={'width':'40%'}
                           # ),

                           dbc.Card(
                                dbc.CardBody(
                                    [
                                        html.H5("Address:", className="card-title", style={"color":"black", "font-weight": "bold"}),
                                        html.P(id="address-card", style={"font-size": "1.5em"}, className="card-text"),
                                    ]
                                ),
                                #className="w-60 mb-3",
                                style={'width':'100%'}
                           ),

                       ],
                       id = "address-return-ig"
                   ),



                   # Rent Growth
                   dbc.InputGroup([

                       # Rent Growth
                       dbc.Label("Rent Growth Yr.: ", style={"font-size" : "100%", "margin-right": "4px"}),
                       dbc.InputGroupText("Min", style={"height":"max-content","margin-left":"4px"}),
                       dbc.Input(
                                 id="rent-min",
                                 type="number",
                                 persistence=True,
                                 persistence_type="memory",
                                 placeholder = "%",
                                 style={"height":"auto"}
                                ),

                       dbc.InputGroupText("Max", style={"height":"max-content","margin-left":"4px"}),
                       dbc.Input(
                                 id="rent-max",
                                 type="number",
                                 persistence=True,
                                 persistence_type="memory",
                                 placeholder = "%",
                                 style={"height":"auto"}
                                ),

                   ], style={"height":"44px"}),


                    # Opex
                    dbc.InputGroup([

                        dbc.Label("Operating Expenses (Monthly): ", style={"font-size" : "100%", "margin-right": "4px"}),

                        dbc.InputGroupText("OPEX", style={"height":"max-content"}),
                        dbc.Input(
                                  id="op-exp-return",
                                  persistence=True,
                                  persistence_type="memory",
                                  style={"height":"auto"}
                                 ),

                        dbc.InputGroupText("Taxes", style={"height":"max-content"}),
                        dbc.Input(
                                  id="tax-return",
                                  persistence=True,
                                  persistence_type="memory",
                                  style={"height":"auto"}
                                 ),

                     ], style={"height":"44px"}),

                     # Operating Expenses growth
                     dbc.InputGroup([

                         # Opex Growth
                         dbc.Label("Opex Growth Yr.: ", style={"font-size" : "100%", "margin-right": "4px"}),

                         html.Div(
                                [
                                    html.I(className="fas fa-question-circle fa-lg", id="opex-tooltip"),
                                    dbc.Tooltip("Operating Expenses include Utilities, Repairs and Maintenance, Janitorial, Payroll, Advertising, Professional Fees and other expenses.", target="opex-tooltip", style={"padding": "0rem"}),
                                ],
                                className="p-5 text-muted",
                                id="opex-tooltip"
                         ),

                         dbc.InputGroupText("Min", style={"height":"max-content","margin-left":"4px"}),
                         dbc.Input(
                                   id="opex-min",
                                   type="number",
                                   value=2,
                                   persistence=True,
                                   persistence_type="memory",
                                   style={"height":"auto"}
                                  ),

                         dbc.InputGroupText("Max", style={"height":"max-content","margin-left":"4px"}),
                         dbc.Input(
                                   id="opex-max",
                                   type="number",
                                   value=4,
                                   persistence=True,
                                   persistence_type="memory",
                                   style={"height":"auto"}
                                  ),

                     ], style={"height":"44px"}),




                     # Cap rates
                     dbc.InputGroup([

                             # Discount Rate
                             dbc.Label("Discount Rate: ", style={"font-size" : "100%", "margin-right": "4px"}),

                             html.Div(
                                    [
                                        html.I(className="fas fa-question-circle fa-lg", id="disc-tooltip"),
                                        dbc.Tooltip("This is estimated based on Riskfree Rate of 10-Year US Treasury, and additional Risk Premium using CMBS Spread", target="disc-tooltip", style={"padding": "0rem"}),
                                    ],
                                    className="p-5 text-muted",
                                    id="disc-tooltip"
                             ),

                             dbc.InputGroupText("Calc. (%)", style={"height":"max-content","margin-left":"4px"}),
                             dbc.Input(
                                       id="disc-rate",
                                       value = 8,
                                       persistence=True,
                                       persistence_type="memory",
                                       style={"height":"auto"}
                                      ),


                            # Valuation
                            dbc.InputGroupText("Hold", style={"height":"max-content"}),
                            dbc.Input(
                                      id = "hold-return",
                                      type = "text",
                                      persistence = True,
                                      persistence_type = "memory",
                                      placeholder = "Years",
                                      style = {"width":"12%", "height":"auto"}
                                     ),

                      ], style={"height":"44px"}),


                      html.Div([

                            dbc.Button("Model Returns",
                                       id="lease-button",
                                       size="lg",
                                       style={"margin-top":"15%"},
                                       className="mr-1"),

                      ]),



                ], className="return-style"),

                   width={"size": 6, "order": "first"}),


    # Row 1 close
    ], style={"margin-top":"2%"}),


        html.Div([

           dbc.Row(
               [


                   # Returns Graph
                   dcc.Graph(

                               id="returns-graph",
                               style={"display": "inline-block", "width": "600px", "float": "left", "height":"350px", "margin-top":"24%"}

                   ),


                   # Investment metrics
                   dbc.InputGroup([

                       dbc.Card(
                                   [
                                       dbc.CardHeader("IRR"),
                                       dbc.CardBody(
                                           [
                                               html.P(id="irr-card", style={"font-size": "1.6em"}),
                                           ]

                                       ),
                                   ],
                                   id="irr",
                                   color="light",
                                   style={"width": "7rem", "margin-left": "2%", "margin-top": "1.5em", "height": "7em"}
                       ),

                       dbc.Card(
                                   [
                                       dbc.CardHeader("Cash-on-cash"),
                                       dbc.CardBody(
                                           [
                                               html.P(id="coc-card", style={"font-size": "1.6em"}),
                                           ]

                                       ),
                                   ],
                                   id="coc",
                                   color="light",
                                   style={"width": "7rem", "margin-left": "2%", "margin-top": "1.5em", "height": "7em"}
                       ),

                       dbc.Card(
                                   [
                                       dbc.CardHeader("ARY"),
                                       dbc.CardBody(
                                           [
                                               html.P(id="ary-card", style={"font-size": "1.6em"}),
                                           ]

                                       ),
                                   ],
                                   id="ary",
                                   color="light",
                                   style={"width": "7rem", "margin-left": "2%", "margin-top": "1.5em", "height": "7em"}
                       ),

                       dbc.Card(
                                   [
                                       dbc.CardHeader("Exit Cap"),
                                       dbc.CardBody(
                                           [
                                               html.P(id="ecap-card", style={"font-size": "1.6em"}),
                                           ]

                                       ),
                                   ],
                                   id="ecap",
                                   color="light",
                                   style={"width": "7rem", "margin-left": "2%", "margin-top": "1.5em", "height": "7em"}
                       ),


                    ]),


        # row 2 closed
        ], justify="between"),

    ], className = "investment-block"),

    # dummy
    html.Div(id="dummy-div-returns"),

    # Row #3 DataTable
    dbc.Row(

            # Lease Table
            html.Div([

                dash_table.DataTable(

                    id="return-table",

                    columns=[{"id":"Year","name":"Year"},
                             {"id":"Periods","name":"Periods"},
                             {"id":"Gross_Rent","name": "Gross-Rent"},
                             {"id":"Free Month","name": "Rent Discount (Months)"},
                             {"id":"Expenses","name": "Expenses"},
                             {"id":"Cash Flow","name": "Cash Flow"},
                             {"id":"NPV","name": "NPV"}],

                    style_cell={
                        "fontFamily": "Arial",
                        "fontSize": 16,
                        "textAlign": "center",
                        "height": "auto",
                        "padding": "2px 22px",
                        "whiteSpace": "normal",
                        "overflow": "hidden",
                        "textOverflow": "ellipsis",
                        'minWidth': '100px', 'width': '100px', 'maxWidth': '100px',
                    },

                    style_table={
                        "maxHeight": "50ex",
                        "overflowY": "scroll",
                        "overflowX": "auto",
                        "width": "100%"
                    },

                    style_header={
                        "backgroundColor": "rgb(230, 230, 230)",
                        "fontSize": 16,
                    },

                    style_data_conditional=[{
                        "if": {"row_index": "odd"},
                        "backgroundColor": "rgb(248, 248, 248)",

                        "if": {"state": "selected"},
                        "backgroundColor": "rgba(174, 214, 241)",
                        "border": "1px solid blue",

                        "if": {"state": "active"},
                        "backgroundColor": "rgba(174, 214, 241)",
                        "border": "1px solid blue",

                    }],

                    export_format='xlsx',
                    export_headers='display',
                    merge_duplicate_headers=True,
                    persistence=True,
                    persistence_type="memory",
                    page_size = 10,
                    sort_action="native",
                    filter_action="native",
                    editable=True
                ),
            ], className="return-table-style"),

     )

 ])


# Callbacks
@application.callback(
                      [
                        #Output("propname-card","children"),
                        Output("address-card","children"),
                        Output("rent-min","value"),
                        Output("rent-max","value")
                      ],
                      [
                         Input("dummy-div-returns", "value"),
                      ],
                      [
                         State("modal-store", "data")
                      ]
                    )
def populate_fields(dummy, modal_store):

    print("modal store", type(modal_store), modal_store)

    Name = modal_store["points"][0]["customdata"][0]
    Address = modal_store["points"][0]["customdata"][1]

    if modal_store['points'][0]['lat'] and modal_store['points'][0]['lon']:
        Lat = modal_store['points'][0]['lat']
        Long = modal_store['points'][0]['lon']
    else:
        Lat, Long = DataProcessor.get_geocodes(Address)

    # Query Rent Growth
    con = engine.connect()

    query = '''

            select MsaName, zip_code, pct_change AS pct_change, ST_AsText(geometry) as geom
            from stroom_main.gdf_rent_growth_july
            GROUP BY MsaName, zip_code, Year, geometry
            HAVING st_distance_sphere(Point({},{}), ST_Centroid(geometry)) <= {};

            '''.format(Long, Lat, 1609*5)

    df_rg = pd.read_sql(query, con)

    if df_rg.shape[0] > 0:

        rgs = df_rg[df_rg['pct_change'] > 0]['pct_change']

        # Calculate quantiles
        q25 = rgs.quantile(.25)*100
        q75 = rgs.quantile(.75)*100

        q25_fmt = "{:.0f}%".format(q25)
        q75_fmt = "{:.0f}%".format(q75)

        return (Address, q25_fmt, q75_fmt)

    else:

        return (Address, no_update, no_update)
