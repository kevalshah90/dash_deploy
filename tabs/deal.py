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

# For adding tooltips
#FONT_AWESOME = "https://use.fontawesome.com/releases/v5.10.2/css/all.css"

plotly_template = pio.templates["plotly"]


layout = html.Div([

   dbc.Row(
       [
            # Col 1
            dbc.Col(

                html.Div([

                    html.Div([

                        html.H2("Effective Lease Calculations", style={"text-align":"center","margin-left":"45%"}),

                    ]),

                   # Cash flow modeling options
                   dcc.RadioItems(
                         options=[
                             {'label': 'Standard', 'value': 'DCF'},
                             {'label': 'Simulate', 'value': 'Sim'},
                         ],
                         value="Sim",
                         id='model-radio',
                         style={"text-align":"center", "font-size" : "16px", "margin-left": "26em"}
                   ),


                   # Location - Address
                   dbc.InputGroup(
                       [

                           dbc.Label("Address:", style={"font-size" : "100%", "margin-right": "4px"}),
                           #dbc.InputGroupAddon("Address", style={"margin-left":"8px"}),
                           dbc.Input(

                                     id="address-deal",
                                     type="text",
                                     value="2000 Alameda De Las Pulgas, San Mateo, California 94403, United States"

                                    ),

                           dcc.Dropdown(
                                        id="address-deal-dropdown",
                                        persistence=True,
                                        persistence_type="memory",
                                        placeholder="Address Suggestions",
                                        style={"width":"79%", "font-size" : "90%", "margin-left": "9.5em"}
                                    )


                       ],

                   ),


                   # Asset Information
                   dbc.InputGroup([

                       # Rent Growth
                       dbc.Label("Asset: ", style={"font-size" : "100%", "margin-right": "4px"}),
                       dbc.InputGroupAddon("Type", style={"height":"max-content","margin-left":"4px"}),
                       dcc.Dropdown(
                                 id="asset-type",
                                 options=[

                                     {"label": "Office", "value": "Office"},
                                     {"label": "Industrial", "value": "Industrial"},
                                     {"label": "Multi-Family", "value": "Multi-Family"}

                                 ],
                                 value="Office",
                                 persistence=True,
                                 persistence_type="memory",
                                 style={"height":"48px", "width":"50%"},
                                ),

                       dbc.InputGroupAddon("Class", style={"height":"max-content","margin-left":"-11em"}),
                       dcc.Dropdown(
                                 id="asset-class",
                                 options=[

                                     {"label": "A", "value": "A"},
                                     {"label": "B", "value": "B"},
                                     {"label": "C", "value": "C"}

                                 ],
                                 value="A",
                                 persistence=True,
                                 persistence_type="memory",
                                 style={"height":"48px", "width":"48%"},
                                ),
                   ]),




                   # Lease Information
                   dbc.InputGroup(
                       [

                           dbc.Label("Lease Information: ", style={"font-size" : "100%", "margin-right": "4px"}),
                           dbc.InputGroupAddon("Total Square Footage (RSF)", style={"margin-left":"8px"}),
                           dbc.Input(
                                     id="space-deal",
                                     type="number",
                                     persistence=True,
                                     persistence_type="memory"
                                    ),

                       ],

                   ),

                   dbc.InputGroup(
                       [

                           dbc.InputGroupAddon("Lease Start", style={"height":"max-content"}),
                           dcc.DatePickerSingle(
                                                id="date-picker-deal",
                                                #date=date(2021, 7, 30),
                                                persistence=True,
                                                persistence_type="memory",
                                                min_date_allowed=date.today(),
                                                className="mb-3",
                           ),

                           # Populated via callback based on dates selected
                           dbc.InputGroupAddon("Total Months", style={"height":"max-content"}),
                           dbc.Input(
                                     id="term-deal",
                                     type="number",
                                     #value=60,
                                     persistence=True,
                                     persistence_type="memory",
                                    ),

                       ],
                   ),


                   # Lease deal type
                   dbc.InputGroup([

                        dbc.InputGroupAddon("Lease Type", style={"height":"max-content"}),
                        dcc.Dropdown(

                                id="lease-type-deal",
                                persistence=True,
                                persistence_type="memory",
                                options=[

                                    {"label": "Gross or Full Service", "value": "Gross or Full Service"},
                                    {"label": "Modified Gross", "value": "Modified Gross"},
                                    {"label": "Triple Net Lease", "value": "NNN"}

                                ],
                                value='NNN',
                                style={"height":"48px", "width":"60%"},
                        ),

                   ]),


                   # Rent Growth
                   dbc.InputGroup([

                       # Rent Growth
                       dbc.Label("Rent Growth Yr. (%): ", style={"font-size" : "100%", "margin-right": "4px"}),
                       dbc.InputGroupAddon("Min", style={"height":"max-content","margin-left":"4px"}),
                       dbc.Input(
                                 id="rent-min",
                                 type="number",
                                 persistence=True,
                                 persistence_type="memory",
                                 value=-3
                                ),

                       dbc.InputGroupAddon("Max", style={"height":"max-content","margin-left":"4px"}),
                       dbc.Input(
                                 id="rent-max",
                                 type="number",
                                 persistence=True,
                                 persistence_type="memory",
                                 value=3
                                ),

                   ]),



                   # Tenants
                   dbc.InputGroup([

                        # Tenancy
                        dbc.Label("Tenants: ", style={"font-size" : "100%", "margin-right": "4px"}),

                        html.Div(
                               [
                                   html.I(className="fas fa-question-circle fa-lg", id="tenant-tooltip"),
                                   dbc.Tooltip("Tenant Info. pulled from Experian Business API", target="tenant-tooltip", style={"padding": "0rem"}),
                               ],
                               className="p-5 text-muted",
                               id="tenant-tooltip"
                        ),

                        dbc.InputGroupAddon("Industry", style={"height": "max-content", "margin-left": "4px"}),
                        dcc.Dropdown(

                                  id="tenant-industry",
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

                         dbc.InputGroupAddon("Name", style={"height":"max-content","margin-left":"-20%"}),
                         dbc.Input(
                                   id="tenant-name",
                                   persistence=True,
                                   persistence_type="memory"
                                  ),

                   ]),



                   # Tenant Risk - Credit and Renewal Probability
                   dbc.InputGroup([

                       dbc.InputGroupAddon("Credit", style={"height":"max-content","margin-left":"4px"}),
                       dcc.Dropdown(

                               id="tenant-credit",
                               persistence=True,
                               persistence_type="memory",
                               options=[

                                   {"label": "Excellent", "value": "Excellent"},
                                   {"label": "Very Good", "value": "Very Good"},
                                   {"label": "Good", "value": "Good"},
                                   {"label": "Fair", "value": "Fair"},
                                   {"label": "Poor", "value": "Poor"}

                               ],
                               value="Excellent",
                               style={"height":"48px", "width":"50%"},
                       ),

                       dbc.InputGroupAddon("Renewal %", style={"height":"max-content","margin-left":"4px"}),
                       dbc.Input(
                                 id="tenant-renewal",
                                 type="number",
                                 value=75,
                                 persistence=True,
                                 persistence_type="memory"
                                ),
                   ]),


                   # Concessions and credit losses
                   dbc.InputGroup([

                        dbc.Label("Concessions: ", style={"font-size" : "100%", "margin-right": "4px"}),
                        dbc.InputGroupAddon("Vacancy loss", style={"height":"max-content"}),
                        dbc.Input(
                                  id="vacancy-loss",
                                  persistence=True,
                                  persistence_type="memory"
                                 ),

                       dbc.InputGroupAddon("Free Months", style={"height":"max-content"}),
                       dbc.Input(
                                 id="free-month-deal",
                                 persistence=True,
                                 persistence_type="memory"
                                ),

                    ]),


                    # Above TI
                    dbc.InputGroup([

                         dbc.Label("Operating Expenses (Monthly): ", style={"font-size" : "100%", "margin-right": "4px"}),
                         dbc.InputGroupAddon("TI (RSF)", style={"height":"max-content"}),
                         dbc.Input(
                                   id="tenant-improvement-deal",
                                   type="text",
                                   value=30,
                                   persistence=True,
                                   persistence_type="memory"
                                  ),

                        dbc.InputGroupAddon("OPEX", style={"height":"max-content"}),
                        dbc.Input(
                                  id="op-exp-deal",
                                  persistence=True,
                                  persistence_type="memory"
                                 ),

                     ]),


                     # Operating Expenses
                     dbc.InputGroup([

                            dbc.InputGroupAddon("Taxes", style={"height":"max-content"}),
                            dbc.Input(
                                      id="tax-deal",
                                      persistence=True,
                                      persistence_type="memory"
                                     ),

                            dbc.InputGroupAddon("Insurance", style={"height":"max-content"}),
                            dbc.Input(
                                      id="insurance-deal",
                                      persistence=True,
                                      persistence_type="memory"
                                     ),

                     ]),


                     # Operating Expenses growth
                     dbc.InputGroup([

                         # Opex Growth
                         dbc.Label("Opex Growth Yr. (%): ", style={"font-size" : "100%", "margin-right": "4px"}),

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

                             #dbc.Label("Exit Cap Rate:", style={"font-size" : "100%", "margin-right": "4px"}),
                             #dbc.InputGroupAddon("Actual (%)", style={"height":"max-content"}),
                             # dbc.Input(
                             #           id="actual-cap-deal",
                             #           type="text",
                             #           persistence=True,
                             #           persistence_type="memory",
                             #          ),

                             # Discount Rate
                             dbc.Label("Discount Rate (%): ", style={"font-size" : "100%", "margin-right": "4px"}),

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
                            dbc.InputGroupAddon("Value", style={"height":"max-content"}),
                            dbc.Input(
                                      id="value-cap-deal",
                                      type="text",
                                      persistence=True,
                                      persistence_type="memory",
                                      style={"width":"25%"}
                                     ),

                      ]),


                      html.Div([

                            dbc.Button("Produce Lease Scenario",
                                       id="lease-button",
                                       size="lg",
                                       style={"margin-top":"15%"},
                                       className="mr-1"),

                      ]),



                ], className="deal-style"),

                   width={"size": 6, "order": "first"}),

            # Col 2
            #  Effective Rent Calculator
            dbc.Col(

              html.Div([

                html.H6("Net Effective Rent ($ SF/Yr.)", style={"text-align":"left","margin-left":"1%"}),

                dbc.Input(
                          id="net",
                          style={"font-size":"36px","margin-left":"15px","height":"80px"}
                         ),

                # Dummy div
                html.Div(id='test-div', style={'display': 'none'}),

                # Monthly Rent
                dbc.Label("Rent:", style={"font-size" : "100%", "margin-right": "4px"}),
                dbc.Input(
                             id="monthly",
                             className="monthly-rent"
                ),


                #  Property Details
                dbc.Label("Value:", style={"font-size" : "100%", "margin-right": "4px"}),
                dbc.Input(
                             id="assessed-value",
                             className="assessed-value"
                ),

                # Total Square Footage
                dbc.Label("Sq. Ft:", style={"font-size" : "100%", "margin-right": "4px"}),
                dbc.Input(
                             id="total-sq-ft",
                             className="total-sq-ft"
                ),

                # Cap Rates
                dbc.Label("Cap Rate: ", style={"font-size" : "100%", "margin-right": "4px"}),
                dbc.Input(
                             id="calc-cap-rate",
                             className="calc-cap-rate"
                ),

            ], className="rent-block"),

            #], style={"margin-right":"-45%","width":"100%", "margin-top":"-256%"}),
            width={"size": 4, "order": "second"}),


        # Col 3
        # Asset Stabilization score graph
        dbc.Col([
                 html.Div([
                            dcc.Graph(id='score-circle'),
                 ], className="stablization-block"),
        ], width={"size": 2, "order":"last"}),

    # Row 1 close
    ], style={"margin-top":"2%"}),


        html.Div([

           dbc.Row(
               [
                # Property Financing Information
                dbc.InputGroup([

                        dbc.Label("Financing: ", style={"font-size" : "100%", "margin-right": "4px"}),
                        dbc.InputGroupAddon("Loan Amt.", style={"height":"max-content","width":"16%"}),
                        dbc.Input(
                                  id="loan-amt",
                                  persistence=True,
                                  persistence_type="memory",
                                  style={"width":"30%"}
                                 ),

                       dbc.InputGroupAddon("Term (Yr)", style={"height":"max-content"}),
                       dbc.Input(
                                 id="loan-term",
                                 persistence=True,
                                 persistence_type="memory"
                                ),


                       dbc.InputGroupAddon("Interest", style={"height":"max-content"}),
                       dbc.Input(
                                 id="loan-interest",
                                 persistence=True,
                                 persistence_type="memory",
                                 style={"width":"10%"}
                                ),

                 ], style={"margin-top":"-19%", "margin-left":"-10%", "width": "130%", "float": "left", "position":"relative"}),


                  # Lending Info.
                  dbc.InputGroup([

                         dbc.InputGroupAddon("Lender", style={"height":"max-content"}),
                         dcc.Input(
                                        id="loan-lender",
                                        persistence=True,
                                        persistence_type="memory"
                                        #style={"width":"53%"}
                                  ),


                         dbc.InputGroupAddon("Date", style={"height":"max-content"}),
                         dcc.DatePickerSingle(
                                              id="loan-date",
                                              persistence=True,
                                              persistence_type="memory",
                                              min_date_allowed=date(2000, 1, 1)
                                              #style={"width":"30%","margin-right":"-12%"}
                                             ),

                  ]),



                  # Debt Metrics
                  dbc.InputGroup([

                          dbc.Label("Debt Metrics: ", style={"font-size" : "100%", "margin-right": "4px"}),
                          dbc.InputGroupAddon("LTV", style={"height":"max-content"}),
                          dbc.Input(
                                    id="loan-ltv",
                                    persistence=True,
                                    persistence_type="memory",
                                   ),

                         dbc.InputGroupAddon("DSCR", style={"height":"max-content"}),
                         dbc.Input(
                                   id="loan-dscr",
                                   persistence=True,
                                   persistence_type="memory",
                                   style={"width":"25%"}
                                  ),

                   ]),

                   # Investment metrics
                   dbc.InputGroup([

                       dbc.Label("Investment Metrics: ", style={"font-size" : "100%", "margin-right": "4px", "margin-top": "10%"}),

                       dbc.InputGroupAddon("IRR: ", style={"height":"max-content"}),
                       dbc.Input(
                                    id="irr"
                       ),

                       dbc.InputGroupAddon("CoC: ", style={"height":"max-content"}),
                       dbc.Input(
                                    id="coc"
                       ),

                       dbc.InputGroupAddon("ARY: ", style={"height":"max-content"}),
                       dbc.Input(
                                    id="ary"
                       ),

                    ]),

                    #], style={"margin-top":"10%", "margin-left":"-10%", "width": "130%", "float": "left", "position":"relative"}),


        # row 2 closed
        ], justify="between"),
           #style={"margin-top":"-25%", "margin-left":"56%"}),

    ], className = "financing-block"),

    # Row #3 DataTable
    dbc.Row(

            # Lease Table
            html.Div([

                dash_table.DataTable(

                    id="deal-table",

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
                        #"fontWeight": "bold",
                        "fontSize": 16,
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
            ], className="table-style"),

     ),

     # Tornado Diagram
     html.Div([

         # Plot properties map
         dcc.Graph(id="tornado"),

         ], className="tornado-style"
    ),


    #Distribution of Asset Value
    html.Div([

        # Plot properties map
        dcc.Graph(id="asset"),

        ], className="asset-style"
    )

 ])


# Callbacks

# Address dropdown, autocomplete
@application.callback(Output("address-deal-dropdown", "options"),
              [Input("address-deal", "value")])
def autocomplete_address(value):

    if value and len(value) >= 8:

        addr = {}

        # Call mapbox API and limit Autocomplete address suggestions
        ret_obj = geocoder.forward(value, lon=-95.7128, lat=37.0902, limit=2, country=["us"])
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
@application.callback(Output("address-deal", "value"),
              [Input("address-deal-dropdown", "value")])
def resetInput(value):

    if value:
        return value
    else:
        return (no_update)



# Effective rent calculations - When Comps and Analysis tabs have been executed
# Update Net Effective Rent field only
@application.callback(Output("net", "value"),
              [

                 Input("space-deal", "value"),
                 Input("address-deal", "value")

              ],
              [

                  State("comps-store", "data"),
                  State("analysis-store", "data")

              ]
             )
def rent_datacard(space, address, comps_store, analysis_store):

    if comps_store and analysis_store and address:

       # Space size
       size = comps_store["leaseinfo"][0]["space"]
       net = analysis_store["calc_price"]

       return (int(net))

    else:

        return(no_update)


# Dash Gotchas - Input type needs to be either a input or state in at least one of the callbacks
# Workaround here: we use the test-input value as
# the input of a callback that updates a hidden div
@application.callback(Output('test-div', 'children'),
              [Input('net', 'value')])
def update_div(input_value):
    #print('Input value: {}'.format(input_value))
    return input_value



# Update Monthly rent - Case when Revenue Management and No RM.
@application.callback(Output("monthly", "value"),
              [

                 Input("space-deal", "value"),
                 Input("net", "value"),
                 Input("model-radio", "value"),
                 Input("lease-button", "n_clicks")

              ],
              [

                  State("comps-store", "data"),
                  State("analysis-store", "data")

              ]
             )
def rent_datacard(space, net, model_radio, n_clicks, comps_store, analysis_store):

    if comps_store and analysis_store and net and model_radio == "DCF":

       # Space size
       size = comps_store["leaseinfo"][0]["space"]

       # Calc. rent
       ask = round(analysis_store["calc_price"],2)
       monthly_rent = (float(analysis_store["calc_price"])*int(size))/12

       return ("${:,.0f}".format(monthly_rent))

    # For case when there is no Revenue Management Component and / or user overwrites the Rent in Input field.
    if space and net and model_radio == "Sim":

       monthly_rent = (float(net)*int(space))/12

       return ("${:,.0f}".format(monthly_rent))

    else:

        return(no_update)


# Asset Stabilization Pie Graph
@application.callback([
               Output("score-circle", "figure"),
               Output("score-circle", "style")
              ],
              [
               Input("lease-button", "n_clicks"),
              ]
             )
def render_score(n_clicks):

    if n_clicks:

        score = np.random.randint(60,80,1)[0]

        fig = go.Figure(

            data=[

                go.Pie(
                    labels=['', ''],
                    values=[score, 100-score],
                    hole=.5,
                    textinfo='none'
                    #marker_colors=['rgb(113, 209, 145)', 'rgb(240, 240, 240)'],
                )

            ],


            layout=go.Layout(
                width=400,
                height=400,
                annotations=[{'text': str(score) + "%", 'x':0.5, 'y':0.5, 'font': dict(size=35, color="#aaa"), 'showarrow':False}],
                paper_bgcolor = 'rgba(0,0,0,0)',
                plot_bgcolor = 'rgba(0,0,0,0)',
                showlegend=False
            )
        )

        fig.update_layout(title={
                                    'text': "Asset Stabilization",
                                     'y':0.9,
                                     'x':0.5,
                                     'xanchor': 'center',
                                     'yanchor': 'top'
                                },
                           title_font_color="#aaa",
                           template=plotly_template
                          )

        return [fig, {"display":"inline", "position":"relative", "width":"100%", "height":"100%"}]

    else:

        return [no_update, {"display":"none"}]


# Calculate Vacancy Loss
@application.callback(Output("vacancy-loss", "value"),
              [
                 Input("date-picker-deal", "date"),
                 Input("monthly", "value"),
                 Input("model-radio", "value"),
                 Input("lease-button", "n_clicks")
              ],
              [
                  State("comps-store", "data"),
                  State("analysis-store", "data")
              ]
             )
def rent_datacard(start_date, monthly, model_radio, n_clicks, comps_store, analysis_store):

    if n_clicks and comps_store and model_radio=="DCF":

       if comps_store and comps_store["leaseinfo"][0]["dealtype"] == 'New' and start_date:
          # Lease start date
          start = comps_store["leaseinfo"][0]["start"]
          startdt = datetime.strptime(start, '%Y-%m-%d').date()

          # Get Space size, calc. rent
          size = comps_store["leaseinfo"][0]["space"]
          monthly_rent = (float(analysis_store["calc_price"])*int(size))/12

          # Sample lease end date <--- THIS WOULD BE READ FROM EXISTING LEASE IF ANY OR LAST SIGNED LEASE END DATE
          prev_dt = startdt + relativedelta.relativedelta(months=-4)

          # Calculate number of vacant months
          calc = relativedelta.relativedelta(startdt, prev_dt)
          vlossmos = calc.months + calc.years * 12

          vlossrent = vlossmos * monthly_rent

          return ("${:,.0f}".format(vlossrent))

       if start_date and monthly:

          # Lease start date
          startdt = datetime.strptime(start_date, '%Y-%m-%d').date()

          # Sample lease end date <--- THIS WOULD BE READ FROM EXISTING LEASE IF ANY OR LAST SIGNED LEASE END DATE
          prev_dt = startdt + relativedelta.relativedelta(months=-4)

          # Calculate number of vacant months
          calc = relativedelta.relativedelta(startdt, prev_dt)
          vlossmos = calc.months + calc.years * 12

          monthly_rent = monthly.replace(',','')

          vlossrent = vlossmos * float(monthly_rent[1:])

          return ("${:,.0f}".format(vlossrent))

    else:

        return(no_update)



# Pull property level information - This information will be populated from an API - Reonomy or Moody's REIS
@application.callback([

                  Output("assessed-value", "value"),
                  Output("total-sq-ft", "value"),

              ],
              [
                  Input("address-deal", "value")
              ],
             )
def prop_details(address):

    zipcode = re.search('(\d{5})([- ])?(\d{4})?', address)

    if address:
       if zipcode:

          # Property Details - will be read from the data - lookup based on Address
          amv = 70500000
          totalsqft = 143805

          return ("${:,.0f}".format(amv), "{:,.0f} SF".format(totalsqft))

    if address == "":

        amv = 0
        totalsqft = 0

        return ("${:,.0f}".format(amv), "{:,.0f} SF".format(totalsqft))

    else:

        return (no_update)

# Update expenses - data pulled from Reonomy / CredIQ APIs
@application.callback([

                  Output("op-exp-deal", "value"),
                  Output("tax-deal", "value"),
                  Output("insurance-deal", "value")

              ],
              [

                  Input("address-deal", "value"),
                  Input("space-deal", "value")

              ],
             )
def exp_details(address, space):

    if address and space:
       # Property Details - will be read from the data - lookup based on Address
       # Update tax and insurance rates here based on State from Address
       tax = 5.80 * int(space)
       insurance = 1.13 * int(space)
       opex = 2128813

       return ("${:,.0f}".format(opex), "${:,.0f}".format(tax), "${:,.0f}".format(insurance))

    if address == "":

       opex = ""
       tax = ""
       insurance = ""

       return (opex, tax, insurance)

    else:

        return (no_update)



# Pull Financing information based on Address
@application.callback([

                  Output("loan-amt", "value"),
                  Output("loan-interest", "value"),
                  Output("loan-lender", "value"),
                  Output("loan-term", "value"),
                  Output("loan-date", "date"),

              ],
              [
                  Input("address-deal", "value"),

              ],
             )
def debt_details(address):

    zipcode = re.search('(\d{5})([- ])?(\d{4})?', address)

    if address:
       if zipcode:

          # Financial Details - will be read from the data - lookup based on Address
          loan_amt = 14850000
          loan_int = 3.78
          lender = "Bank of America"
          loan_term = 10
          loan_date = date(2019, 9, 30)

          return ("${:,.0f}".format(loan_amt), "{:,.2f}%".format(loan_int), lender, loan_term, loan_date)

    if address == "":

        loan_amt = ""
        loan_int = ""
        lender = ""
        loan_term = ""
        loan_date = ""

        return (loan_amt, loan_int, lender, loan_term, loan_date)

    else:

        return (no_update)




# Auto populate fields
@application.callback([
                 Output("space-deal", "value"),
                 Output("lease-type-deal", "value"),
                 Output("date-picker-deal", "date"),
                 Output("term-deal", "value")
              ],
              [
                 Input("model-radio", "value"),
                 Input("lease-button", "n_clicks")
              ],
              [
                  State("comps-store", "data"),
                  State("analysis-store", "data")
              ]
             )
def auto_pop(model_radio, n_clicks, comps_store, analysis_store):

    if n_clicks and comps_store and model_radio == "DCF":

       # Space size
       size = comps_store["leaseinfo"][0]["space"]

       # Lease type
       type = comps_store["leaseinfo"][0]["type"]

       # Lease dates
       start = comps_store["leaseinfo"][0]["start"]
       end = comps_store["leaseinfo"][0]["end"]

       startdt = datetime.strptime(start, "%Y-%m-%d")
       enddt = datetime.strptime(end, "%Y-%m-%d")

       # Total months
       calc = relativedelta.relativedelta(enddt, startdt)
       mos = calc.months + calc.years * 12

       # format date to %m/%d/%Y
       fmt_dt = startdt.strftime("%m/%d/%Y")

       return (size, type, fmt_dt, mos)

    else:

        return(no_update)

# Update Cashflow DataTable
@application.callback([

                  Output("deal-table", "data"),
                  Output("value-cap-deal", "value"),
                  Output("calc-cap-rate", "value"),
                  Output("irr", "value"),
                  Output("coc", "value"),
                  Output("ary", "value")

              ],
              [
                  Input("model-radio","value"),
                  Input("space-deal","value"),
                  Input("monthly", "value"),
                  Input("assessed-value", "value"),
                  Input("date-picker-deal", "date"),
                  Input("term-deal", "value"),
                  Input("vacancy-loss", "value"),
                  Input("free-month-deal", "value"),
                  Input("tenant-improvement-deal", "value"),
                  Input("opex-max", "value"),
                  Input("opex-min", "value"),
                  Input("rent-max", "value"),
                  Input("rent-min", "value"),
                  Input("tenant-credit", "value"),
                  Input("disc-rate", "value"),
                  Input("op-exp-deal", "value"),
                  Input("tax-deal", "value"),
                  Input("insurance-deal", "value"),
                  Input("lease-button", "n_clicks"),
                  Input("deal-table", "data_timestamp")

              ],
              [
                  State("deal-table", "data"),
                  State("comps-store", "data"),
                  State("analysis-store", "data")
              ]
             )
def cashflow_table(model_radio, space, monthly, assessed_value, start_date, term, vacancy_loss, free, ti, opex_max, opex_min, rent_max, rent_min, tenant_credit, disc_rate, opex, tax, insurance, n_clicks, timestamp, rows, comps_store, analysis_store):

    ctx = dash.callback_context

    # Check state and comps_store for pricing input
    if rows and timestamp and comps_store:

        print("Part 1")

        # Get Monthly rent
        size = comps_store["leaseinfo"][0]["space"]
        monthly_rent = (float(comps_store["price"])*int(size))/12

        for row in rows:
            try:
                row["Cash Flow"] = int(row["Gross_Rent"] - row['Expenses']) - int(row["Free Month"])*int(monthly_rent)
            except:
                row["Cash Flow"] = int(row["Gross_Rent"] - row['Expenses'])

        df = pd.DataFrame(rows)

        # Cap rate calculations --> Pass variables for cap rate calculations
        result = calc_caprate(comps_store["leaseinfo"][0]["proptype"], tenant_credit, 'CBD', 'Excellent', monthly_rent)
        cap = result["cap_rate"]
        val = result["cap_value"]

        # Investment metrics calc - IRR = Discount Rate, CoC = Net CF / (Cash Investment) [PV - Loan]
        # Filter Pandas DF to include annual occupancy only
        dff = df[df["Periods"] == 12]
        NCF = dff['Cash Flow'].mean()

        #  Net Cash / Cash Investment
        coc = round(NCF / (60000000 - 14850000),1)*100

        # Risk Metric
        if assessed_value:

            av = Decimal(sub(r'[^\d.]', '', assessed_value))

            ary = round(float(NCF) / int(av),1)*100

        return(df.to_dict("records"), "${:,.0f}".format(val), "{:,.1f}%".format(cap), "{:,.1f}%".format(dr[0]), "{:,.1f}%".format(coc), "{:,.1f}%".format(ary))

    if n_clicks and comps_store and model_radio == "DCF":

        print("Part 2")

        # Lease dates
        start = comps_store["leaseinfo"][0]["start"]
        end = comps_store["leaseinfo"][0]["end"]

        startdt = datetime.strptime(start, "%Y-%m-%d")
        enddt = datetime.strptime(end, "%Y-%m-%d")

        # Space size
        size = comps_store["leaseinfo"][0]["space"]

        # Income
        monthly_rent = (float(analysis_store["calc_price"])*int(size))/12
        daily_rent = (float(analysis_store["calc_price"])*int(size))/365

        # Clean up expenses
        # ti = Decimal(sub(r'[^\d.]', '', ti))

        # Expenses - All values annual expenses
        if ti and opex and tax and insurance:

            opex = Decimal(sub(r'[^\d.]', '', opex))
            tax = Decimal(sub(r'[^\d.]', '', tax))
            insurance = Decimal(sub(r'[^\d.]', '', insurance))

            # Monthly Expenses sum - Note: TI is included for the first year below in the code
            exp_sum = (int(opex) + int(tax) + int(insurance))/12


        # Gross Rent Calculations
        year_list = []

        # Generate a list of years
        for i in range(startdt.year, enddt.year+1, 1):
            year_list.append(i)

        # Declare dictionary
        rent_dict = {}
        # Iterate over year list
        for i in range(startdt.year, enddt.year+1, 1):

            yearenddt = datetime(i, 12, 31)
            yearstartdt = datetime(i, 1, 1)

            if (enddt >= yearenddt) and (startdt >= yearstartdt) and (startdt != yearenddt):

                delta = yearenddt - startdt
                rent_dict[i] = [(delta.days+1)*daily_rent, int((delta.days+1)/30)]

            elif (startdt <= yearstartdt) and (enddt >= yearenddt):

                delta = yearenddt - yearstartdt
                rent_dict[i] = [(delta.days+1)*daily_rent, int((delta.days+1)/30)]

            elif (enddt <= yearenddt):

                delta = enddt - yearstartdt
                rent_dict[i] = [(delta.days+1)*daily_rent, int((delta.days+1)/30)]

        # Construct Pandas DataFrame - Aggregate yearly cashflow
        df = pd.DataFrame({
                           "Year": year_list,
                           "Periods": np.nan,
                           "Gross_Rent": np.nan,
                           "Free Month": np.nan,
                           "Expenses": np.nan,
                           "Cash Flow": np.nan,
                           "NPV": np.nan,
                         })

        # Lookup rents from dictionary
        for key in rent_dict.keys():
            df.loc[df["Year"]==key, "Periods"] = rent_dict[key][1]

        # Rent growth %
        r = np.random.uniform(float(opex_min), float(opex_max), size=1)

        for index, row in df.iterrows():
            # calculate period 1 value - no increments
            if index == 0:
                df.at[index, "Gross_Rent"] = round(row['Periods']*monthly_rent,0)
            else:
                # Calculate values for subsequent periods with increments
                inc_monthly_rent = monthly_rent + (r * monthly_rent)/100
                df.at[index, "Gross_Rent"] = row['Periods']*inc_monthly_rent
                r = float(r) + float(r)

        # Total TI
        total_ti = float(ti)*int(size)

        # Opex growth %
        op = np.random.uniform(float(opex_min), float(opex_max), size=1)

        for index, row in df.iterrows():
            if index == 0:
                df.at[index, "Expenses"] = row['Periods']*exp_sum + int(total_ti)
            else:
                inc_opex_sum = exp_sum + (op * exp_sum)/100
                df.at[index, "Expenses"] = row['Periods']*inc_opex_sum
                op = float(op) + float(op)

        # Cash Flow Column calculations
        for index, row in df.iterrows():
            df.at[index, "Cash Flow"] = row["Gross_Rent"] - row['Expenses']

        # NPV calculations. Formula = CF / (1+r)^n,
        # r will be calculated based on avg. cap rate for proptype and submarket.
        # r for Phoenix in Summer 2020 = 0.06

        # Select Discount rate %
        #dr = np.random.uniform(float(dr_min), float(dr_max), size=1)

        dr = float(disc_rate)

        # Calculate NPV - Discount Net Cash Flow
        for index, row in df.iterrows():
            df.at[index, "NPV"] = (row["Cash Flow"] / pow((1+dr/100),index+1))


        # Format floats as currencies
        df['Gross_Rent'] = df['Gross_Rent'].map('${:,.0f}'.format)
        df['Expenses'] = df['Expenses'].map('${:,.0f}'.format)
        df['Cash Flow'] = df['Cash Flow'].map('${:,.0f}'.format)
        df['NPV'] = df['NPV'].map('${:,.0f}'.format)

        cashflow_data = df.to_dict("records")

        # Cap rate calculations
        result = calc_caprate(comps_store["leaseinfo"][0]["proptype"], 'Good', 'CBD', 'Excellent', monthly_rent, vacancy_loss)
        cap = result["cap_rate"]
        val = result["cap_value"]

        # Investment metrics calc - IRR = Discount Rate, CoC = Net CF / (Cash Investment) [PV - Loan]
        # Filter Pandas DF to include annual occupancy only
        dff = df[df["Periods"] == 12]

        # Format to numeric to calculate mean
        dff["Cash Flow"] = dff["Cash Flow"].replace('[\$\,\.]',"",regex=True).astype(int)

        NCF = dff['Cash Flow'].mean()

        #  Net Cash / Cash Investment
        coc = round(NCF / (60000000 - 14850000),1)*100

        # Risk Metric
        if assessed_value:

            av = Decimal(sub(r'[^\d.]', '', assessed_value))

            ary = round(float(NCF) / int(av),1)*100

        return (cashflow_data, "${:,.0f}".format(val), "{:,.1f}%".format(cap), "{:,.1f}%".format(dr[0]), "{:,.1f}%".format(coc), "{:,.1f}%".format(ary))

    # Lease calculations only, no pricing
    if n_clicks and monthly and model_radio == "DCF":

        print("Part 3")

        # Lease dates
        startdt = datetime.strptime(start_date, "%Y-%m-%d")

        enddt = startdt + relativedelta.relativedelta(months=int(term))

        # Space size
        size = space

        # Income
        monthly_rent = Decimal(sub(r'[^\d.]', '', monthly))
        daily_rent = (monthly_rent*12)/365

        opex = Decimal(sub(r'[^\d.]', '', opex))
        tax = Decimal(sub(r'[^\d.]', '', tax))
        insurance = Decimal(sub(r'[^\d.]', '', insurance))

        # Expenses
        if opex and tax and insurance:
            exp_sum = int(opex) + int(tax) + int(insurance)


        # Gross Rent Calculations
        year_list = []

        # Generate a list of years
        for i in range(startdt.year, enddt.year+1, 1):
            year_list.append(i)

        # Declare dictionary
        rent_dict = {}
        # Iterate over year list
        for i in range(startdt.year, enddt.year+1, 1):

            yearenddt = datetime(i, 12, 31)
            yearstartdt = datetime(i, 1, 1)

            if (enddt >= yearenddt) and (startdt >= yearstartdt) and (startdt != yearenddt):

                delta = yearenddt - startdt
                rent_dict[i] = [(delta.days+1)*daily_rent, int((delta.days+1)/30)]

            elif (startdt <= yearstartdt) and (enddt >= yearenddt):

                delta = yearenddt - yearstartdt
                rent_dict[i] = [(delta.days+1)*daily_rent, int((delta.days+1)/30)]

            elif (enddt <= yearenddt):

                delta = enddt - yearstartdt
                rent_dict[i] = [(delta.days+1)*daily_rent, int((delta.days+1)/30)]

        # Construct Pandas DataFrame - Aggregate yearly cashflow
        df = pd.DataFrame({
                           "Year": year_list,
                           "Periods": np.nan,
                           "Gross_Rent": np.nan,
                           "Free Month": np.nan,
                           "Expenses": np.nan,
                           "Cash Flow": np.nan,
                           "NPV": np.nan,
                         })

        # Lookup rents from dictionary
        for key in rent_dict.keys():
            df.loc[df["Year"]==key, "Periods"] = rent_dict[key][1]

        # Gross rents with annual escalations column calculations

        # Discount rent growth %
        r = np.random.uniform(float(opex_min), float(opex_max), size=1)

        for index, row in df.iterrows():
            # calculate period 1 value - no increments
            if index == 0:
                df.at[index, "Gross_Rent"] = round(row['Periods']*float(monthly_rent),0)
            else:
                # calculate values for subsequent periods with increments
                inc_monthly_rent = float(monthly_rent) + (r * float(monthly_rent))/100
                df.at[index, "Gross_Rent"] = round(row['Periods']*float(inc_monthly_rent),0)
                r = float(r) + float(r)

        # Expenses with annual increments

        # Total TI
        if ti:
            total_ti = float(ti)*int(size)

        # Discount opex growth %
        op = np.random.uniform(float(opex_min), float(opex_max), size=1)

        for index, row in df.iterrows():
            if index == 0:
                df.at[index, "Expenses"] = exp_sum
            else:
                inc_opex_sum = exp_sum + (op * exp_sum)/100

                # Subtract total_ti from expenses as it is not a recurring expense
                df.at[index, "Expenses"] = round(float(inc_opex_sum),0)
                op = float(op) + float(op)

        # Cash Flow Column calculations
        for index, row in df.iterrows():
            df.at[index, "Cash Flow"] = round(row["Gross_Rent"] - row['Expenses'],0)

        # NPV calculations. Formula = CF / (1+r)^n,
        # r will be calculated based on avg. cap rate for proptype and submarket.
        # r for Phoenix in Summer 2020 = 0.06

        # # Discount rate %
        # dr = np.random.uniform(float(dr_min), float(dr_max), size=1)

        dr = float(disc_rate)

        for index, row in df.iterrows():
            df.at[index, "NPV"] = (row["Cash Flow"] / pow((1+dr/100),index+1))

        # Investment metrics calc - IRR = Discount Rate, CoC = Net CF / (Cash Investment) [PV - Loan]
        # Filter Pandas DF to include annual occupancy only
        dff = df[df["Periods"] == 12]
        NCF = dff['Cash Flow'].mean()

        #  Net Cash / Cash Investment
        coc = round(NCF / (60000000 - 14850000),1)*100
        # Risk Metric
        if assessed_value:

            av = Decimal(sub(r'[^\d.]', '', assessed_value))

            ary = round(float(NCF) / int(av),1)*100

        # Format Pandas columns as currencies
        df['Gross_Rent'] = df['Gross_Rent'].map('${:,.0f}'.format)
        df['Expenses'] = df['Expenses'].map('${:,.0f}'.format)
        df['Cash Flow'] = df['Cash Flow'].map('${:,.0f}'.format)
        df['NPV'] = df['NPV'].map('${:,.0f}'.format)

        cashflow_data = df.to_dict("records")

        # Cap rate calculations
        result = calc_caprate('Office', 'Good', 'CBD', 'Excellent', float(monthly_rent), vacancy_loss)
        cap = result["cap_rate"]
        val = result["cap_value"]

        return (cashflow_data, "${:,.0f}".format(val), "{:,.1f}%".format(cap), "{:,.1f}%".format(dr[0]), "{:,.1f}%".format(coc), "{:,.1f}%".format(ary))

    # Lease calculations only, no pricing + comps_store
    #  Run Monte Carlo Simulations
    if n_clicks and monthly and model_radio == "Sim":

       print("Part 4")

       # Lease dates - depending on date format
       try:
           startdt = datetime.strptime(start_date, "%m/%d/%Y")
       except:
           startdt = datetime.strptime(start_date, "%Y-%m-%d")
       finally:
           enddt = startdt + relativedelta.relativedelta(months=int(term))

       # # Space size
       size = space

       # Lease variables that vary - Rental Growth, Opex, Vacancy rate, Discount Rate

       # Income
       monthly_rent = Decimal(sub(r'[^\d.]', '', monthly))
       daily_rent = (monthly_rent*12)/365

       # Expenses
       if opex and tax and insurance:

          opex = Decimal(sub(r'[^\d.]', '', opex))
          tax = Decimal(sub(r'[^\d.]', '', tax))
          insurance = Decimal(sub(r'[^\d.]', '', insurance))

          exp_sum = int(opex) + int(tax) + int(insurance)

       # Gross Rent Calculations
       year_list = []

       # Generate a list of years
       for i in range(startdt.year, enddt.year+1, 1):
           year_list.append(i)

       # Declare dictionary
       rent_dict = {}

       # Iterate over year list
       for i in range(startdt.year, enddt.year+1, 1):

           yearenddt = datetime(i, 12, 31)
           yearstartdt = datetime(i, 1, 1)

           if (enddt >= yearenddt) and (startdt >= yearstartdt) and (startdt != yearenddt):

               delta = yearenddt - startdt
               rent_dict[i] = [(delta.days+1)*daily_rent, int((delta.days+1)/30)]

           elif (startdt <= yearstartdt) and (enddt >= yearenddt):

                delta = yearenddt - yearstartdt
                rent_dict[i] = [(delta.days+1)*daily_rent, int((delta.days+1)/30)]

           elif (enddt <= yearenddt):

                delta = enddt - yearstartdt
                rent_dict[i] = [(delta.days+1)*daily_rent, int((delta.days+1)/30)]

       # Construct Pandas DataFrame - Aggregate yearly cashflow
       df = pd.DataFrame({
                           "Year": year_list,
                           "Periods": np.nan,
                           "Gross_Rent": np.nan,
                           "Free Month": np.nan,
                           "Expenses": np.nan,
                           "Cash Flow": np.nan,
                           "NPV": np.nan,
                        })

       # Lookup rents from dictionary
       for key in rent_dict.keys():
           df.loc[df["Year"]==key, "Periods"] = rent_dict[key][1]

       # # Run Monte Carlo simulations

       # Simulate rent growth %
       # Calculate mean of the range values - rent
       if rent_max and rent_min:
           mu = (float(rent_min) + float(rent_max))/2
           # Adjust scale (standard deviation) based on market volatility
           r = np.random.normal(mu, scale=1.5, size=100)
           r = r.mean()

       if r:
           for index, row in df.iterrows():
               # Calculate period 1 value - no increments
               if index == 0:
                    df.at[index, "Gross_Rent"] = round(row['Periods']*float(monthly_rent),0)
               else:
                    # Calculate values for subsequent periods with increments
                    inc_monthly_rent = float(monthly_rent) + (r * float(monthly_rent))/100
                    df.at[index, "Gross_Rent"] = round(row['Periods']*float(inc_monthly_rent),0)
                    r = float(r) + float(r)

       # Expenses with annual increments, Total TI
       if ti:
          total_ti = float(ti)*int(size)

       # Simulate opex growth %
       # Calculate mean of the range values
       if opex_max and opex_min:
           mu = (float(opex_min) + float(opex_max))/2
           # Adjust scale (standard deviation) based on market volatility
           op = np.random.normal(mu, scale=0.5, size=100)
           op = op.mean()

       for index, row in df.iterrows():
           if index == 0:
              df.at[index, "Expenses"] = exp_sum
           else:
              inc_opex_sum = exp_sum + (op * exp_sum)/100

              # Subtract total_ti from expenses as it is not a recurring expense
              df.at[index, "Expenses"] = round(float(inc_opex_sum),0)
              op = float(op) + float(op)

       # # Cash Flow Column calculations
       for index, row in df.iterrows():
           df.at[index, "Cash Flow"] = round(row["Gross_Rent"] - row['Expenses'],0)

       # NPV calculations. Formula = CF / (1+r)^n,
       # r will be calculated based on avg. cap rate for proptype and submarket.
       # r for Phoenix in Summer 2020 = 0.06

       # Simulate discount rate %
       if disc_rate:

           mean = float(disc_rate)
           stddev = 2 # Adjust based on market volatility

           # Calculate parameters mu, sigma of lognormal distribution.
           sigma_squared = np.log((stddev/mean)**2 + 1)
           mu = np.log(mean) - 0.5*sigma_squared
           sigma = np.sqrt(sigma_squared)

           dr = np.random.lognormal(mu, sigma, size=100)
           dr = dr.mean()

       for index, row in df.iterrows():
           df.at[index, "NPV"] = (row["Cash Flow"] / pow((1+dr/100),index+1))

       # # Investment metrics calc - IRR = Discount Rate, CoC = Net CF / (Cash Investment) [PV - Loan]
       # # Filter Pandas DF to include annual occupancy only
       dff = df[df["Periods"] == 12]
       NCF = dff['Cash Flow'].mean()

       #  Net Cash Flow / Cash Investment
       coc = (NCF /(60000000 - 14850000))*100

       # Risk Metric
       if assessed_value:
           av = Decimal(sub(r'[^\d.]', '', assessed_value))
           ary = ((NCF) / int(av))*100

       # Format Pandas columns as currencies
       df['Gross_Rent'] = df['Gross_Rent'].map('${:,.0f}'.format)
       df['Expenses'] = df['Expenses'].map('${:,.0f}'.format)
       df['Cash Flow'] = df['Cash Flow'].map('${:,.0f}'.format)
       df['NPV'] = df['NPV'].map('${:,.0f}'.format)

       cashflow_data = df.to_dict("records")

       # # Cap rate calculations

       # Simulate Vacancy loss - Adjust scale based on market volatility
       if type(vacancy_loss) == str:
           vacancy_loss = Decimal(sub(r'[^\d.]', '', vacancy_loss))

       vloss = np.random.normal(int(vacancy_loss), scale=1, size=100)
       vloss = vloss.mean()

       result = calc_caprate('Office', 'Good', 'CBD', 'Excellent', float(monthly_rent), vloss)
       cap = result["cap_rate"]
       val = result["cap_value"]

       return (cashflow_data, "${:,.0f}".format(val), "{:,.1f}%".format(cap), "{:,.1f}%".format(dr), "{:,.1f}%".format(coc), "{:,.1f}%".format(ary))

    else:

        return (no_update)



# Tornado Diagram
@application.callback(
                Output("tornado", "figure"),

            [
                Input("lease-button", "n_clicks")
            ],
)
def plot_tornado(n_clicks):

    if n_clicks:

        trace1 = go.Bar(
            x = [-0.02, -0.015, -0.012, -0.01, -0.004, -0.005],
            y = ["Exit Cap Rate", "Occupancy", "Interest Rates", "Discount Rate", "Tax Rate", "Rent Growth"],
            orientation = "h",
            marker = {
                "color": 'rgba(58, 71, 80, 0.6)'
            },
        )

        trace2 = go.Bar(
            x = [0.022, 0.018, 0.013, 0.009, 0.003, 0.005],
            y = ["Exit Cap Rate", "Occupancy", "Interest Rates", "Discount Rate", "Tax Rate", "Rent Growth"],
            orientation = "h",
            marker = {
                "color": 'rgba(246, 78, 139, 0.6)'
            },
            base=0
        )

        data = Data([trace1, trace2])

        layout = {
                    "xaxis": {'title': 'Percent sensitive',
                              'tickformat': '%',
                              'range': [-0.03, 0.03]
                             },
                    "title": "Sensitivity Analysis - Tornado Diagram",
                    "width": 650,
                    "height": 400,
                    "barmode": "stack",
                    "autosize": True,
                    "showlegend": False,
        }

        return{'data':data, 'layout':layout}

    else:

        return(no_update)




# Plot Histogram / Distribution of Asset Values
@application.callback(
                Output("asset", "figure"),

            [
                Input("value-cap-deal", "value"),
                Input("lease-button", "n_clicks")
            ],
)
def plot_histogram(asset_value, n_clicks):

    if n_clicks and asset_value:

        av = Decimal(sub(r'[^\d.]', '', asset_value))

        # For calculating parameters mu, sigma of lognormal distribution.
        mean = int(av)
        stddev = 1000000 # Adjust this based on market volatility / uncertainty

        sigma_squared = np.log((stddev/mean)**2 + 1)
        mu = np.log(mean) - 0.5*sigma_squared
        sigma = np.sqrt(sigma_squared)

        xtup = np.random.lognormal(mu, sigma, size=1000),
        xtup = list(map('{:.0f}'.format,xtup[0]))
        xarr = np.asarray(xtup).astype(np.float)

        fig = go.Figure(

                data = [go.Histogram(
                                     x = xarr,
                                     nbinsx=50,
                                     marker=dict(color="rgb(105,105,105)",
                                                 opacity=0.5
                                                ),

                )],

                layout = go.Layout(
                                    xaxis =  dict(
                                                  title = 'Asset Values'
                                                  #tickformat = '${:,.0f}'
                                             ),
                                    title = "Distribution of Asset Values",
                                    width = 650,
                                    height = 400,
                                    autosize = True
                )

        )

        fig.add_vline(x=np.median(xarr), line_dash = 'dash', line_color = 'black')

        fig.add_annotation(x = np.median(xarr), y=80,
                           text = "Median value ${:,.0f}".format(np.median(xarr)),
                           showarrow = False,
                           yshift = 10,
                           font=dict(
                                family="sans serif",
                                size=18,
                                color="black"
                            )
                          )

        return fig

    else:

        return(no_update)




# Populate Financing info.
@application.callback([
                 Output("loan-ltv", "value"),
                 Output("loan-dscr", "value")
              ],
              [
                 Input("loan-amt", "value"),
                 Input("loan-interest", "value"),
                 Input("loan-lender", "value"),
                 Input("loan-term", "value"),
                 Input("loan-date", "date"),
                 Input("assessed-value","value"),
                 Input("monthly","value"),
                 Input("lease-button", "n_clicks")
              ],
             )
def finance_info(loan_amt, loan_int, loan_lender, loan_term, loan_date, market_value, monthly_rent, n_clicks):

    if n_clicks and market_value and loan_amt and loan_int:

       # LTV Calculation
       value = Decimal(sub(r'[^\d.]','', market_value))
       loan = Decimal(sub(r'[^\d.]','', loan_amt))
       ltv = float(loan)/float(value)

       # DSCR, Solve for payment
       loan_int = Decimal(sub(r'[^\d.]','', loan_int))

       P = float(loan)
       i = (float(loan_int)/100)/12
       n = int(loan_term)*12

       mortgage = P*(i*(1+i)**n)/(((1+i)**n) - 1)

       # NOI / Debt Service - Annually
       # Format monthly rent
       if monthly_rent:
           rent = Decimal(sub(r'[^\d.]','', monthly_rent))
           dscr = float(rent * 12)/float(mortgage * 12)

       return ("{:,.01f}%".format(ltv*100), round(dscr,1))

    else:

        return(no_update)


# Store graphs dcc.Store component
@application.callback(Output("deal-store","data"),
             [

                  Input("space-deal", "value"),
                  Input("date-picker-deal","date"),
                  Input("term-deal","value"),
                  Input("lease-type-deal", "value"),
                  Input("free-month-deal", "value"),
                  Input("tenant-improvement-deal", "value"),
                  Input("opex-max", "value"),
                  Input("opex-min", "value"),
                  Input("rent-max", "value"),
                  Input("rent-min", "value"),
                  Input("op-exp-deal", "value"),
                  Input("tax-deal", "value"),
                  Input("insurance-deal", "value"),
                  Input("value-cap-deal", "value"),
                  Input("loan-ltv", "value"),
                  Input("loan-dscr", "value"),
                  Input("lease-button", "n_clicks")

             ]
             )
def deal_store(size, date, term, lease_type, free, ti, rent_max, rent_min, opex_max, opex_min, opex, tax, insurance, value_cap, ltv, dscr, n_clicks):

    if n_clicks:

        return {
                "space_size": size,
                "start_date": date,
                "lease_term": term,
                "lease_type": lease_type,
                "free_months": free,
                "ti": ti,
                "ai": rent_max,
                "opex": opex,
                "tax": tax,
                "insurance": insurance,
                "cap_value": value_cap,
                "ltv": ltv,
                "dscr": dscr
               }
