import dash
import flask
from dash import dcc, html
import dash_bootstrap_components as dbc
import os

# External stylesheets

SANDSTONE = "https://cdn.jsdelivr.net/npm/bootswatch@4.5.2/dist/sandstone/bootstrap.min.css"

external_stylesheets = [
    SANDSTONE,
    {
        'href': 'custom.css',
        'rel': 'stylesheet'
    },
    {
        'href': 'https://use.fontawesome.com/releases/v5.10.2/css/all.css',
        'rel': 'stylesheet'
    }
]

application = dash.Dash(__name__,
                        requests_pathname_prefix='/dashboard/',
                        #serve_locally = False,
                        suppress_callback_exceptions = True,
                        meta_tags=[
                            {"name": "viewport", "content": "width=device-width, initial-scale=1"}
                        ],
                        external_stylesheets=external_stylesheets,
               )


server = application.server

# Title the app.
application.title = "Stroom - Platform Demo"