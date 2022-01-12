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
from calendar import monthrange
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

# For adding tooltips
#FONT_AWESOME = "https://use.fontawesome.com/releases/v5.10.2/css/all.css"

plotly_template = pio.templates["plotly"]


# Date ranges for pricing matrix
weeks = {}
rents = {}

# Function controls the number of times to create cards in each row
def generate_matrix(date, base_rent, length):

    # generate 8 rows with 4 cells each - 32/8 = 4
    for d in range(1, 32, 4):

        # populate dates dict
        start = (date + timedelta(days=d)).strftime('%Y-%m-%d')
        week = pd.date_range(start, periods=4).to_pydatetime().tolist()
        weeks[d] = week

        # populate rents dict

        # Start with base rent and increments rent by x% to create a list

        # Increment dictionary
        inc_dict = {"12mos": 1.0025, "14mos": 1.0005, "0": 0}

        increment = inc_dict[length]
        arr = np.array([int(base_rent), *np.repeat(increment, 3)])
        arr1 = arr.cumprod().tolist()

        # convert to integers
        arr2 = [int(x) for x in arr1]

        rents[d] = arr2

        # Update base rent
        base_rent = arr2[3]*increment


def create_cards(date, rent):

    return dbc.Card(

                dbc.CardBody(
                    [
                        html.H5(date.strftime('%b-%d'), id=f"{date}-title"),
                        html.H6(rent, id=f"{date}-rent"),
                    ]
                )
            )



layout = html.Div([

   dbc.Row(
       [
            # Col 1
            dbc.Col(

                html.Div([

                   html.Div([

                        html.H2("Price Matrix", style={"text-align":"center","margin-left":"45%"}),

                   ]),

                   # Hidden div for input
                   html.Div(id="hidden-input", style={"display": "none"}),

                   # Lease Information

                   dbc.InputGroup(
                       [

                           dbc.Label("Lease Information: ", style={"font-size" : "100%", "margin-right": "4px"}),

                           dbc.InputGroupAddon("Lease Start", style={"height":"48px"}),
                           dcc.DatePickerSingle(
                                                id="date-picker-deal-mf",
                                                #date=date(2021, 7, 30),
                                                persistence=True,
                                                persistence_type="memory",
                                                min_date_allowed=date.today(),
                                                className="mb-3"
                                                #style={"height":"48px", "width":"60%"},
                           ),

                           # Unit Available date
                           dbc.InputGroupAddon("Unit Available", style={"height":"48px", "margin-top":"10px"}),
                           dcc.DatePickerSingle(
                                                id="date-picker-unit-mf",
                                                #date=date(2021, 7, 30),
                                                persistence=True,
                                                persistence_type="memory",
                                                className="mb-3"
                           ),

                       ],
                   ),


                   # Lease deal type
                   dbc.InputGroup([

                        dbc.InputGroupAddon("Lease Type", style={"height":"max-content"}),
                        dcc.Dropdown(

                                id="lease-type-deal-mf",
                                persistence=True,
                                persistence_type="memory",
                                options=[

                                    {"label": "12-months", "value": "12mos"},
                                    {"label": "14-months", "value": "14mos"},
                                    {"label": "Flex", "value": "Flex"},
                                    {"label": "Sublease", "value": "Sublease"}

                                ],
                                value='12mos'
                                #style={"height":"48px", "width":"30%"},
                        ),

                   ]),

                   # Tenants
                   dbc.InputGroup([

                        # Tenancy
                        dbc.Label("Tenants: ", style={"font-size" : "100%", "margin-right": "4px"}),

                        # html.Div(
                        #        [
                        #            html.I(className="fas fa-question-circle fa-lg", id="tenant-tooltip"),
                        #            dbc.Tooltip("Tenant Info. pulled from Experian Business API", target="tenant-tooltip", style={"padding": "0rem"}),
                        #        ],
                        #        className="p-5 text-muted",
                        #        id="tenant-tooltip-mf"
                        # ),

                        dbc.InputGroupAddon("Industry", style={"height": "max-content", "margin-left": "4px"}),
                        dcc.Dropdown(

                                  id="tenant-industry-mf",
                                  persistence=True,
                                  persistence_type="memory",
                                  optionHeight=40,
                                  options=[

                                      {"label": "Agriculture, and Forestry", "value": "agri"},
                                      {"label": "Mining, and Oil and Gas", "value": "mine"},
                                      {"label": "Utilities", "value": "util"},
                                      {"label": "Construction", "value": "cons"},
                                      {"label": "Manufacturing", "value": "manu"},
                                      {"label": "Wholesale Trade", "value": "whole"},
                                      {"label": "Retail Trade", "value": "retail"},
                                      {"label": "Transportation and Warehousing", "value": "transport"},
                                      {"label": "Information", "value": "info"},
                                      {"label": "Finance and Insurance", "value": "finance"},
                                      {"label": "Real Estate", "value": "real"},
                                      {"label": "Professional, Scientific, and Technical Services", "value": "prof"},
                                      {"label": "Management of Companies and Enterprises", "value": "manage"},
                                      {"label": "Administrative and Support and Waste Management and Remediation Services", "value": "admin"},
                                      {"label": "Educational Services", "value": "educate"},
                                      {"label": "Health Care and Social Assistance", "value": "health"},
                                      {"label": "Arts, Entertainment, and Recreation", "value": "arts"},
                                      {"label": "Accommodation and Food Services", "value": "accomodate"},
                                      {"label": "Other Services (except Public Administration)", "value": "other_service"},
                                      {"label": "Public Administration", "value": "public"}

                                  ],

                         ),

                   ]),



                   # Tenant Risk - Credit and Renewal Probability
                   dbc.InputGroup([

                       dbc.InputGroupAddon("Credit", style={"height":"max-content","margin-left":"4px"}),
                       dcc.Dropdown(

                               id="tenant-credit-mf",
                               persistence=True,
                               persistence_type="memory",
                               options=[

                                   {"label": "Excellent", "value": "Excellent"},
                                   {"label": "Very Good", "value": "Very Good"},
                                   {"label": "Good", "value": "Good"},
                                   {"label": "Fair", "value": "Fair"},
                                   {"label": "Poor", "value": "Poor"}

                               ],
                               value="Excellent"
                               #style={"height":"48px", "width":"50%"},
                       ),


                   ]),


                   # Concessions and credit losses
                   dbc.Label("Concessions: ", style={"font-size" : "100%", "margin-right": "4px"}),

                   dbc.InputGroup([

                       dbc.InputGroupAddon("Free Months", style={"height":"max-content"}),
                       dbc.Input(
                                 id="free-month-deal-mf",
                                 persistence=True,
                                 persistence_type="memory"
                                ),

                   ]),

                   dbc.InputGroup([

                       dbc.InputGroupAddon("Vacancy loss", style={"height":"max-content"}),
                       dbc.Input(
                                 id="vacancy-loss-mf",
                                 persistence=True,
                                 persistence_type="memory"
                                ),

                   ]),

                   html.Div([

                        dbc.Button("Produce Lease Matrix",
                                   id="lease-button-mf",
                                   size="lg",
                                   style={"margin-top":"15%"},
                                   className="mr-1"),

                    ]),

                ], className="deal-style"),

                   width={"size": 4, "order": "first"}),


                # Column 2
                dbc.Col(

                    html.Div(id="matrix"),

                    #html.Div([

                        # # create initial matrix
                        # html.Div(id="create-matrix"),
                        #
                        # dbc.Row([
                        #     dbc.Col([create_cards(i)], width=3) for i in weeks[1]
                        # ], align='center', no_gutters=True),
                        #
                        # dbc.Row([
                        #     dbc.Col([create_cards(i)], width=3) for i in weeks[5]
                        # ], align='center', no_gutters=True),
                        #
                        # dbc.Row([
                        #     dbc.Col([create_cards(i)], width=3) for i in weeks[9]
                        # ], align='center', no_gutters=True),
                        #
                        # dbc.Row([
                        #     dbc.Col([create_cards(i)], width=3) for i in weeks[13]
                        # ], align='center', no_gutters=True),
                        #
                        # dbc.Row([
                        #     dbc.Col([create_cards(i)], width=3) for i in weeks[17]
                        # ], align='center', no_gutters=True),
                        #
                        # dbc.Row([
                        #     dbc.Col([create_cards(i)], width=3) for i in weeks[21]
                        # ], align='center', no_gutters=True),
                        #
                        # dbc.Row([
                        #     dbc.Col([create_cards(i)], width=3) for i in weeks[25]
                        # ], align='center', no_gutters=True),
                        #
                        # dbc.Row([
                        #     dbc.Col([create_cards(i)], width=3) for i in weeks[29]
                        # ], align='center', no_gutters=True)

                    #]),

                width={"size": 7, "order": "last"}, style={"margin-top": "2%","margin-left": "60px"}),


    # Row 1 close
    ], style={"margin-top":"2%","margin-left":"14%"})

 ])


# Function to populate card

# Callbacks

# Create Matrix
@application.callback(Output("matrix", "children"),
                     [
                       #Input("hidden-input", "children"),
                       Input("date-picker-deal-mf", "date"),
                       Input("lease-type-deal-mf", "value"),
                       Input("lease-button-mf", "n_clicks")
                     ],
                     [
                         State("comps-store", "data"),
                         State("analysis-store", "data")
                     ])
def create_matrix(startdt, length, n_clicks, comps_store, analysis_store):

    if n_clicks and comps_store and analysis_store:

        # Lease start date
        startdt1 = pd.to_datetime(startdt)

        # Hack to adjust date so that matrix starts at lease start date
        startdt2 = (startdt1 - timedelta(days=1)).strftime('%Y-%m-%d')
        startdt3 = pd.to_datetime(startdt2)

        monthly_rent = analysis_store["calc_price"]

        generate_matrix(startdt3, monthly_rent, length)

        # Get calculated monthly rent
        #monthly_rent = "${:,.0f}".format(analysis_store["calc_price"])

        # create matrix based on lease start date
        return html.Div([

                    dbc.Row([
                        dbc.Col([create_cards(i, j)], width=3) for i,j in zip(weeks[1], rents[1])
                    ], align='center', no_gutters=True),

                    dbc.Row([
                        dbc.Col([create_cards(i, j)], width=3) for i,j in zip(weeks[5], rents[5])
                    ], align='center', no_gutters=True),

                    dbc.Row([
                        dbc.Col([create_cards(i, j)], width=3) for i,j in zip(weeks[9], rents[9])
                    ], align='center', no_gutters=True),

                    dbc.Row([
                        dbc.Col([create_cards(i, j)], width=3) for i,j in zip(weeks[13], rents[13])
                    ], align='center', no_gutters=True),

                    dbc.Row([
                        dbc.Col([create_cards(i, j)], width=3) for i,j in zip(weeks[17], rents[17])
                    ], align='center', no_gutters=True),

                    dbc.Row([
                        dbc.Col([create_cards(i, j)], width=3) for i,j in zip(weeks[21], rents[21])
                    ], align='center', no_gutters=True),

                    dbc.Row([
                        dbc.Col([create_cards(i, j)], width=3) for i,j in zip(weeks[25], rents[25])
                    ], align='center', no_gutters=True),

                    dbc.Row([
                        dbc.Col([create_cards(i, j)], width=3) for i,j in zip(weeks[29], rents[29])
                    ], align='center', no_gutters=True)

        ])

    else:

        # Get today's date
        tdate = datetime.today().date()

        generate_matrix(tdate, 0, "0")

        # Create initial matrix
        return html.Div([

                    dbc.Row([
                        dbc.Col([create_cards(i, '-')], width=3) for i in weeks[1]
                    ], align='center', no_gutters=True),

                    dbc.Row([
                        dbc.Col([create_cards(i, '-')], width=3) for i in weeks[5]
                    ], align='center', no_gutters=True),

                    dbc.Row([
                        dbc.Col([create_cards(i, '-')], width=3) for i in weeks[9]
                    ], align='center', no_gutters=True),

                    dbc.Row([
                        dbc.Col([create_cards(i, '-')], width=3) for i in weeks[13]
                    ], align='center', no_gutters=True),

                    dbc.Row([
                        dbc.Col([create_cards(i, '-')], width=3) for i in weeks[17]
                    ], align='center', no_gutters=True),

                    dbc.Row([
                        dbc.Col([create_cards(i, '-')], width=3) for i in weeks[21]
                    ], align='center', no_gutters=True),

                    dbc.Row([
                        dbc.Col([create_cards(i, '-')], width=3) for i in weeks[25]
                    ], align='center', no_gutters=True),

                    dbc.Row([
                        dbc.Col([create_cards(i, '-')], width=3) for i in weeks[29]
                    ], align='center', no_gutters=True)

        ])


# Set lease start date
@application.callback(Output("date-picker-deal-mf", "date"),
                     [
                       Input("hidden-input", "children"),
                     ],
                     [
                       State("comps-store", "data")
                     ])
def setStartDate(hidden_input, comps_store):

    if comps_store:

       startdt = comps_store["leaseinfo"][0]["start"]

       return startdt

    else:

        return (no_update)



# Calculate Vacancy Loss
@application.callback(Output("vacancy-loss-mf", "value"),
                      [
                         Input("date-picker-deal-mf", "date"),
                         Input("date-picker-unit-mf", "date"),
                         Input("lease-button-mf", "n_clicks")
                      ],
                      [
                          State("comps-store", "data"),
                          State("analysis-store", "data")
                      ]
             )
def vacancy_loss(start_date, available_date, n_clicks, comps_store, analysis_store):

    #if n_clicks and comps_store and analysis_store:
    if n_clicks:

        if n_clicks:

       #if comps_store and comps_store["leaseinfo"][0]["dealtype"] == 'New' and start_date:

          # Lease start date
          startdt = datetime.strptime(start_date, '%Y-%m-%d').date()
          availabledt = datetime.strptime(available_date, '%Y-%m-%d').date()

          # Get rent from analysis tab
          monthly_rent = analysis_store["calc_price"]

          # Sample lease end date <--- THIS WOULD BE READ FROM EXISTING LEASE IF ANY OR LAST SIGNED LEASE END DATE
          # prev_dt = startdt + relativedelta.relativedelta(months=-4)

          # Calculate number of vacant days
          # daysdiff = relativedelta.relativedelta(startdt, availabledt)

          daysdiff = abs((startdt - availabledt).days)

          # Get number of days in month of lease start date
          num_days = monthrange(startdt.year, startdt.month)[1]

          # Calculate daily rent for vacancy loss calculations
          vlossdaily = float(monthly_rent)/int(num_days)

          vlosstotal = daysdiff * vlossdaily

          return("${:,.0f}".format(vlosstotal))

    else:

        return(no_update)



# Store graphs dcc.Store component
@application.callback(Output("deal-mf-store","data"),
                     [

                          Input("space-deal", "value"),
                          Input("date-picker-deal","date"),
                          Input("term-deal","value"),
                          Input("lease-type-deal", "value"),
                          Input("free-month-deal", "value"),
                          Input("lease-button", "n_clicks")

                     ]
                     )
def deal_store(size, date, term, lease_type, free, n_clicks):

    if n_clicks:

        return {
                "space_size": size,
                "start_date": date,
                "lease_term": term,
                "lease_type": lease_type,
                "free_months": free,
               }
