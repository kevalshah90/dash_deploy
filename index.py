
# coding: utf-8

# In[32]:

import pandas as pd
import dash
from dash.dependencies import Input, Output, State
from dash import dcc
import dash_bootstrap_components as dbc
from dash import html
#import dash_design_kit as ddk
import plotly as py
from plotly import graph_objs as go
from plotly.graph_objs import *
import flask
from application import application
import os
from tabs import comps, analysis
from pages import home
import traceback

# In[8]:
server = application.server

# App Layout
application.layout = html.Div([

                        # header
                        html.Div([

                            html.H2("Stroom Product Suite ®", style={"float":"center",
                                                                     "margin-left":"40%",
                                                                     "margin-top":"30px"}),

                            html.Div(

                                html.Img(src='https://stroom-images.s3.us-west-1.amazonaws.com/STROOM-logo-black.png',height="100%"),
                                style={"float":"right",
                                       "width":"170px",
                                       "height":"100px",
                                       "margin-top":"-84px"
                                       }
                            ),

                            html.Div(

                                [
                                    html.H4("Market Intelligence", style={"textAlign":"center"}),
                                    html.Hr(),
                                    dbc.Nav(
                                        [
                                            dbc.NavLink("Comps", href="/comps", active="partial"),
                                            dbc.NavLink("Market", href="/market", active="partial"),
                                            dbc.NavLink("Deals", href="/deals", disabled=True),

                                        ],
                                        vertical=True,
                                        fill=True,
                                        pills=True,
                                    ),
                                ],

                                style = {
                                    "position": "fixed",
                                    "top": 0,
                                    "left": 0,
                                    "bottom": 0,
                                    "width": "12rem",
                                    "padding": "1rem 1rem",
                                    "background-color": "#f8f9fa",
                                },

                            ),

                            dcc.Location(id='url'),

                            html.Div(id='page-content'),

                            # Store component
                            dcc.Store(id="comps-store", storage_type="local"),

                            # Store component for graphs
                            dcc.Store(id="analysis-store", storage_type="local"),

                            ],

                        )

])



# Render page content
@application.callback(Output("page-content", "children"),
              [
                Input('url', 'pathname')
              ]
             )
def display_content(pathname):

    if pathname in ["/","/dashboard/","/dashboard2","/comps"]:
        print(pathname)
        return comps.layout

    elif pathname == "/market":
        return analysis.layout

    else:
        return dash.no_update




# In[10]:

#if __name__ == '__main__':

    # Production
    #app.run_server(debug=True)

    # Localhost
    #app.run_server(debug=True, port=8050)