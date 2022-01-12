
# coding: utf-8

# In[32]:

import pandas as pd
import dash
from dash.dependencies import Input, Output, State
from dash import dcc
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
                                html.Img(src='https://stroom-images.s3.us-west-1.amazonaws.com/STROOM-logo-white.png',height="100%")
                                ,style={"float":"right","width":"170px","height":"100px","margin-top":"-14px"}),

                            dcc.Location(id='url'),

                            html.Div(id='page-content', style={'margin-left': '2%'}),

                            # Store component
                            dcc.Store(id="comps-store", storage_type="local"),

                            # Store component for graphs
                            dcc.Store(id="analysis-store", storage_type="local"),

                            # Store component for deal tab
                            #dcc.Store(id="deal-store", storage_type="local"),

                            # Store component for deal mf tab
                            #dcc.Store(id="deal-mf-store", storage_type="local"),

                            # Store component for home page
                            dcc.Store(id="home-store", storage_type="local"),

                            ],
                            className="row header"
                        )

])



# Render page content
@application.callback(Output("page-content", "children"),
              [
                Input('url', 'pathname')
              ]
             )
def display_content(pathname):

    if pathname == '/home':
        return home.layout

    elif pathname == '/archive':
        return archive.layout()

    else:
        return home.layout



# In[10]:

#if __name__ == '__main__':

    # Production
    #app.run_server(debug=True)

    # Localhost
    #app.run_server(debug=True, port=8050)
