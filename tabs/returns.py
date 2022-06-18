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
from cap_rate_calc import calc_caprate
from decimal import Decimal
import re
from re import sub
import random
import mapbox
import locale

# Google maps api key
import googlemaps
gmaps = googlemaps.Client(key="AIzaSyC0XCzdNwzI26ad9XXgwFRn2s7HrCWnCOk")

MAPBOX_KEY="pk.eyJ1Ijoia2V2YWxzaGFoIiwiYSI6ImNqbW1nbG90MDBhNTQza3IwM3pvd2I3bGUifQ.dzdTsg69SdUXY4zE9s2VGg"
token = MAPBOX_KEY
geocoder = mapbox.Geocoder(access_token=token)


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

                           dbc.InputGroupAddon("Address", style={"height":"max-content","margin-left":"4px"}),
                           dbc.Input(

                                     id="address-return",
                                     type="text",

                                    ),

                       ],
                       id = "address-return-ig"
                   ),


                   # Asset Information
                   dbc.InputGroup([

                       # Rent Growth
                       dbc.Label("Asset: ", style={"font-size" : "100%", "margin-right": "4px"}),
                       dbc.InputGroupAddon("Type", style={"height":"max-content","margin-left":"4px"}),
                       dcc.Dropdown(
                                 id="asset-type",
                                 options=[

                                     {"label": "Multi-Family", "value": "Multi-Family"}

                                 ],
                                 value="Multi-Family",
                                 persistence=True,
                                 persistence_type="memory",
                                 style={"height":"48px", "width":"50%"},
                                ),

                   ]),



                   # Rent Growth
                   dbc.InputGroup([

                       # Rent Growth
                       dbc.Label("Rent Growth Yr.: ", style={"font-size" : "100%", "margin-right": "4px"}),
                       dbc.InputGroupAddon("Min", style={"height":"max-content","margin-left":"4px"}),
                       dbc.Input(
                                 id="rent-min",
                                 type="number",
                                 persistence=True,
                                 persistence_type="memory",
                                 placeholder = "%"
                                ),

                       dbc.InputGroupAddon("Max", style={"height":"max-content","margin-left":"4px"}),
                       dbc.Input(
                                 id="rent-max",
                                 type="number",
                                 persistence=True,
                                 persistence_type="memory",
                                 placeholder = "%"
                                ),

                   ]),


                    # Opex
                    dbc.InputGroup([

                        dbc.Label("Operating Expenses (Monthly): ", style={"font-size" : "100%", "margin-right": "4px"}),

                        dbc.InputGroupAddon("OPEX", style={"height":"max-content"}),
                        dbc.Input(
                                  id="op-exp-return",
                                  persistence=True,
                                  persistence_type="memory"
                                 ),

                        dbc.InputGroupAddon("Taxes", style={"height":"max-content"}),
                        dbc.Input(
                                  id="tax-return",
                                  persistence=True,
                                  persistence_type="memory"
                                 ),

                     ]),

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

                         dbc.InputGroupAddon("Min", style={"height":"max-content","margin-left":"4px"}),
                         dbc.Input(
                                   id="opex-min",
                                   type="number",
                                   value=2,
                                   persistence=True,
                                   persistence_type="memory"
                                  ),

                         dbc.InputGroupAddon("Max", style={"height":"max-content","margin-left":"4px"}),
                         dbc.Input(
                                   id="opex-max",
                                   type="number",
                                   value=4,
                                   persistence=True,
                                   persistence_type="memory"
                                  ),

                     ]),




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

                             dbc.InputGroupAddon("Calc. (%)", style={"height":"max-content","margin-left":"4px"}),
                             dbc.Input(
                                       id="disc-rate",
                                       value = 8,
                                       persistence=True,
                                       persistence_type="memory"
                                      ),


                            # Valuation
                            dbc.InputGroupAddon("Hold", style={"height":"max-content"}),
                            dbc.Input(
                                      id = "hold-return",
                                      type = "text",
                                      persistence = True,
                                      persistence_type = "memory",
                                      placeholder = "Years",
                                      style = {"width":"12%"}
                                     ),

                      ]),


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
                               style={"display": "inline-block", "width": "600px", "float": "left", "height":"350px"}

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
                                   style={"width": "10rem", "margin-left": "2%", "margin-top": "1.5em", "height": "9em"}
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
                                   style={"width": "10rem", "margin-left": "2%", "margin-top": "1.5em", "height": "9em"}
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
                                   style={"width": "10rem", "margin-left": "2%", "margin-top": "1.5em", "height": "9em"}
                       ),


                    ]),


        # row 2 closed
        ], justify="between"),

    ], className = "investment-block"),

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
@application.callback(Output("address-return","value"),
                     [
                          Input("result-store","data")
                     ]
                    )
def pop_fields(result_store):

    print("result store", result_store)
