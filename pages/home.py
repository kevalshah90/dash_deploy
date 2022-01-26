import pandas as pd
import dash
from dash.dependencies import Input, Output, State
from dash import dcc
from dash import html
import plotly as py
from plotly import graph_objs as go
from plotly.graph_objs import *
import flask
from application import application
import os
from tabs import comps, analysis
import dash_daq as daq
import dash_bootstrap_components as dbc

# layout and tabs

layout =  html.Div([
            html.Div([


                # html.Div(
                #     [
                #         html.H5("Acquisition", className="display-4"),
                #         html.Hr(),
                #         dbc.Nav(
                #             [
                #                 dbc.NavLink("Comps", href="/comps", active="exact"),
                #                 dbc.NavLink("Market", href="/market", active="exact"),
                #
                #             ],
                #             vertical="md",
                #             pills=True,
                #         ),
                #     ],
                #     style = {
                #         "position": "fixed",
                #         "top": 0,
                #         "left": 0,
                #         "bottom": 0,
                #         "width": "12rem",
                #         "padding": "1rem 1rem",
                #         "background-color": "#f8f9fa",
                #     }
                # ),


                # dcc.Tabs(
                #
                #     id="tabs",
                #     vertical=True,
                #     className="mb-3",
                #     persistence=True,
                #
                #     children=[
                #
                #
                #          dcc.Tab(label="Acquisition", value="revenue_tab",
                #                  children=[dcc.Tabs(id="subtabs", persistence=True, style={"margin-left":"30px"},
                #                     children=[
                #
                #                               dcc.Tab(label='Comps', value='comps_subtab'),
                #                               dcc.Tab(label='Market', value='analysis_subtab')
                #
                #                     ],
                #                     value="comps_subtab",
                #             )
                #          ]),
                #
                #     ],
                #     value="revenue_tab",
                #  )

                ],

                className="row tabs_div"

            ),

            # Tab content
            html.Div(id="tab_content", style={"margin": "2% 5%", "float":"left"}),

            html.Div(id='dummy_div'),

])



# Render tabs/subtabs
@application.callback(
                          Output("tab_content", "children"),

                      [
                          #Input("tabs", "value"),
                          #Input("subtabs", "value"),
                          Input("url", "pathname")
                      ],
                     )
def render_content(pathname): #tab, subtab):
    """
    For user selections, return the relevant tab
    """
    print(pathname)

    if pathname == "/":
        return comps.layout

    elif pathname == "/comps":
        return comps.layout

    elif pathname == "/market":
        return market.layout

    else:
        return dash.no_update

    # if tab == "revenue_tab":
    #
    #     if subtab == "comps_subtab":
    #         return comps.layout
    #
    #     if subtab == "analysis_subtab":
    #         return analysis.layout
    #
    # else:
    #
    #     return (dash.no_update)
