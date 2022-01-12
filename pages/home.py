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

# layout and tabs

layout =  html.Div([
            html.Div([

                dcc.Tabs(

                    id="tabs",
                    vertical=True,
                    className="mb-3",
                    persistence=True,

                    children=[


                         dcc.Tab(label="Acquisition", value="revenue_tab",
                                 children=[dcc.Tabs(id="subtabs", persistence=True, style={"margin-left":"30px"},
                                    children=[

                                              dcc.Tab(label='Comps', value='comps_subtab'),
                                              dcc.Tab(label='Market', value='analysis_subtab')

                                    ],
                                    value="comps_subtab",
                            )
                         ]),

                    ],
                    value="revenue_tab",
                 )

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
                          Input("tabs", "value"),
                          Input("subtabs", "value"),
                      ],
                     )
def render_content(tab, subtab):
    """
    For user selections, return the relevant tab
    """

    if tab == "revenue_tab":

        if subtab == "comps_subtab":
            return comps.layout

        if subtab == "analysis_subtab":
            return analysis.layout

    else:

        return (dash.no_update)
