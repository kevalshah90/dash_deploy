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
from funcs import clean_percent, clean_currency, get_geocodes, nearby_places, streetview, create_presigned_url
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
                                     dbc.CardHeader("Avg. Rent / SF Yr."),
                                     dbc.CardBody(
                                         [
                                             html.P(id="rent-card", style={"font-size": "2em"}),
                                         ]

                                     ),
                                 ],
                                 id="rent-stat",
                                 color="light",
                                 style={"width": "10rem", "margin-left": "-28%", "height": "9em"}
                     ),

                     dbc.Card(
                                 [
                                     dbc.CardHeader("Occupancy"),
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
                                     dbc.CardHeader("Opex"),
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

         ], style={"margin-top":"48em", "margin-left":"31px"}),



         dbc.Col([

            # dbc popup / modal
            html.Div([

                dbc.Modal(
                    [
                        dbc.ModalHeader("Property Information", style={"color":"white", "justify-content":"center"}),
                        dbc.ModalBody(
                            [

                                # Images
                                html.Div(id="carousel"),

                                dbc.Label("Property Name:", style={"color":"white", "margin-right":"10px", "margin-top":"1.5%"}),
                                dbc.Label("Property Name:", id="prop_name"),
                                html.Br(),

                                dbc.Label("Address:", style={"color":"white", "margin-right":"10px"}),
                                dbc.Label("Address:", id="Address"),
                                html.Br(),

                                dbc.Label("Number of Units:", style={"color":"white", "margin-right":"10px"}),
                                dbc.Label("Size:", id="Size"),
                                html.Br(),

                                dbc.Label("Year Built:", style={"color":"white", "margin-right":"10px"}),
                                dbc.Label("Year Built:", id="Yr_Built"),
                                html.Br(),

                                dbc.Label("Property: ", style={"color":"white", "margin-right":"10px"}),
                                dbc.Label("Property:", id="Property"),
                                html.Br(),

                                dbc.Label("Comparable Rent ($/SF Yr.):", style={"color":"white", "margin-right":"10px"}),
                                dbc.Label("Rent:", id="Rent"),
                                html.Br(),

                                dbc.Label("Fiscal Revenue:", style={"color":"white", "margin-right":"10px"}),
                                dbc.Label("Revenue:", id="Revenue"),
                                html.Br(),

                                dbc.Label("Rental rate / Sq.ft / Month:", style={"color":"white", "margin-right":"10px"}),
                                dbc.Label("Rental Rate:", id="Rent_rate"),
                                html.Br(),

                                dbc.Label("Avg. Rent / Month (1 Br 750 Sq.ft):", style={"color":"white", "margin-right":"10px"}),
                                dbc.Label("Rental Rate:", id="Rent_monthly"),
                                html.Br(),

                                dbc.Label("Occupancy:", style={"color":"white", "margin-right":"10px"}),
                                dbc.Label("Occupancy:", id="occ-modal"),
                                html.Br(),

                                dbc.Label("Rentable Area:", style={"color":"white", "margin-right":"10px"}),
                                dbc.Label("Rentable Area:", id="rent-area-modal"),
                                html.Br(),

                                dbc.Label("Assessed Value:", style={"color":"white", "margin-right":"10px"}),
                                dbc.Label("Assessed Value:", id="assessed-value"),
                                html.Br(),

                                dbc.Label("Distance:", style={"color":"white", "margin-right":"10px"}),
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

                ], style={"width":"50%", "margin-top": "15%"}),


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
                             {"id":"Rent_monthly","name":"Avg. Rent / Month / Unit (Typical 1 Bed)"},
                             {"id":"Opex", "name":"Opex (Monthly)"},
                             {'id':"EstValue", "name":"Assessed Value"}],

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
                    row_deletable=True,
                    export_format="csv"
                ),


            ], className="table-style",
               style={"display": "inline-block", "width": "100%", "float": "left", "margin-top": "2%"}),

        ]),

        html.Div(id="dummy-div"),

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
                     [Input("address_dropdown", "value")])
def resetInput(value):

    return value


# Autopopulate property details fields - mock API
@application.callback([

                        Output("built", "value"),
                        Output("renovated", "value"),
                        Output("space-acq", "value"),
                        Output("units-acq", "value")

                      ],
                      [
                        Input("address_autocomplete", "value")
                      ]
                     )
def autopopulate_propdetails(address):

    if address:
        g = geocoder.mapbox(address, key=token)
        geojson = g.json
        address = geojson["address"]

        coords = [geojson['lat'], geojson['lng']]

        # Convert to radian and search pandas dataframe
        X = np.deg2rad(df_lease_sf_mf[['Lat', 'Long']].values)
        y = np.deg2rad(np.array([coords]))

        tree = BallTree(X, leaf_size=2)
        dist, ind = tree.query(y)

        # Convert radians to miles and check the distance, 0.05 = precision / cutoff
        if dist[0][0] * 3963.1906 <= 0.05:

            details = df_lease_sf_mf[['Year Built','Renovated','EstRentableArea','Size']].iloc[ind[0][0]].tolist()

            return (int(details[0]), details[1], int(details[2]), int(details[3]))

        else:

            raise PreventUpdate

    else:

        raise PreventUpdate




# Update map graph
@application.callback([

                          Output("map-graph1", "figure"),
                          Output("price-value", "value")

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
                          State("comps-store", "data")
                      ]
             )
def update_graph(address, proptype, built, units_acq, space_acq, ameneties, n_clicks, comps_store):

    # Update this to adjust map layout.
    # Default map view

    # sf bay area
    layout_lat = 37.7749
    layout_lon = -122.4194

    zoom = 12

    price = 0

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
        cd_cols = ['Property Name','Address_Comp','Size','Year Built','Property Type','Rent','Preceding Fiscal Year Revenue','Revenue_per_sqft_month','Occ.','EstRentableArea','EstValue','Distance']

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

           '''
           Obtain features - lookup in mock API or from user input
           '''

           g = geocoder.mapbox(address, key=token)
           geojson = g.json
           address = geojson["address"]

           coords = [geojson['lat'], geojson['lng']]

           Lat = coords[0]
           Long = coords[1]

           geohashval = gh.encode(Lat, Long, precision=5)

           # Convert to radian and search pandas dataframe
           X = np.deg2rad(df_lease_sf_mf[['Lat', 'Long']].values)
           y = np.deg2rad(np.array([coords]))

           tree = BallTree(X, leaf_size=2)
           dist, ind = tree.query(y)

           # Convert radians to miles and check the distance, 0.05 = precision / cutoff

           # Declare variable to store mock API details
           details = None

           if dist[0][0] * 3963.1906 <= 0.05:

               details = df_lease_sf_mf[['Year Built','Renovated','EstRentableArea','Size','Most Recent Physical Occupancy','taxRate']].iloc[ind[0][0]].tolist()

           # occupancy and taxRate
           if details and details[4] is not None and type(details[4]) is str:
               occupancy = float(details[4].rstrip('%'))
           else:
               # simple mean
               df_lease_sf_mf['Most Recent Physical Occupancy'] = df_lease_sf_mf['Most Recent Physical Occupancy'].apply(clean_percent).astype('float')

               occupancy = df_lease_sf_mf[df_lease_sf_mf['Most Recent Physical Occupancy'] > 0]['Most Recent Physical Occupancy'].mean()

           if details and details[5] is not None:
               taxRate = details[5].astype(float)
           else:
               taxRate = df_lease_sf_mf[df_lease_sf_mf['taxRate'] > 0]['taxRate'].mean()

           ameneties_count = len(ameneties)

           # Function call to obtain rents
           result = calc_rent(address, proptype, built, space_acq, units_acq, ameneties_count, occupancy, taxRate, geohashval)


           price = result["y_pred"] * 12

           # Lease Comp set
           result_df = result["df_lease"]

           data = []

           # Outside of for-loop
           rent = result_df["Estimated_Rent"]
           propname = result_df["Property Name"]

           # Generate Address string
           addr_cols = ["Address", "City", "State", "Zip Code"]

           result_df['Address_Comp'] = result_df[addr_cols].apply(lambda row: ' '.join(row.values.astype(str)), axis=1)

           # Columns for customdata
           cd_cols = ['Property Name','Address_Comp','Size','Year Built','Property Type','Estimated_Rent','Preceding Fiscal Year Revenue','Revenue_per_sqft_month','Occ.','EstRentableArea','EstValue','Distance']

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


           noi = price * space_acq

           min = noi - (10*noi/100)
           max = noi + (10*noi/100)

           max_fmt = float(max)/1000000
           min_fmt = float(min)/1000000

           # Property Location
           data.append({
                        "type": "scattermapbox",
                        "lat": [Lat],
                        "lon": [Long],
                        "hovertext": '${:.0f}'.format(price),
                        "text": "Expected NOI: ${:.1}M-${:.1}M or {:.0f}/SF Yr.".format(min_fmt, max_fmt, price),
                        "textfont": {"color": "rgb(0, 0, 0)",
                                     "size": 18},
                        "textposition": "top right",
                        "showlegend": False,
                        "hoverinfo": "text",
                        "mode": "text+markers",
                        # Once the API is live, subject property data will be passed here for modal popup w carousel
                        "customdata": ['Subject property'],
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

        return ({"data": data, "layout": layout}, price)

    else:
           #PreventUpdate
        return (no_update, no_update)



# Update DataTable and Local Level Stats
@application.callback([
                          Output("comps-table", "data"),
                          Output("rent-card", "children"),
                          Output("occ-card", "children"),
                          Output("opex-card", "children")
                          #Output("dummy-div", "children")
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

                      ],
                      [

                          State("comps-table", "data"),
                          State("comps-table", "columns")

                      ]
                      )
def update_table(address, proptype, built, units_acq, space_acq, ameneties, n_clicks, rows, columns):


    # Generate comps
    if n_clicks:

       # Find address coordinates
       g = geocoder.mapbox(address, key=token)
       geojson = g.json
       address = geojson["address"]

       coords = [geojson['lat'], geojson['lng']]

       Lat = coords[0]
       Long = coords[1]

       geohashval = gh.encode(Lat, Long, precision=5)

       ameneties_count = len(ameneties)

       # occupancy
       df_lease_sf_mf['Most Recent Physical Occupancy'] = df_lease_sf_mf['Most Recent Physical Occupancy'].apply(clean_percent).astype('float')
       occupancy = df_lease_sf_mf[df_lease_sf_mf['Most Recent Physical Occupancy'] > 0]['Most Recent Physical Occupancy'].mean()

       # taxRate
       taxRate = df_lease_sf_mf[df_lease_sf_mf['taxRate'] > 0]['taxRate'].mean()

       # Function call to populate comps table and local stats
       result = calc_rent(address, proptype, built, space_acq, units_acq, ameneties_count, occupancy, taxRate, geohashval)

       result_df = result["df_lease"]

       # subset to first n rows only
       result_df = result_df.sort_values(by=['Estimated_Rent'], ascending=False).head(15)
       result_df = result_df.sample(len(result_df))

       df = pd.DataFrame(result_df, columns = ["Property Name","Year Renovated","Property Type","Year Built","Size",
                                               "Preceding Fiscal Year Revenue","Most Recent Physical Occupancy","Lease Type",
                                               "SubMarket", "City", "MSA", "Estimated_Rent", "Rent_monthly", "Opex", "Address",
                                               "Zip Code", "WalkScore", "TransitScore", "Revenue_per_sqft_month",
                                               "EstRentableArea","EstValue"])

       # Add Monthly Rent Column
       '''
       For Phoenix, Revenue / Size (# of units) appears to be a close approximation.
       For LA, SD and SF, Rate per sq.ft * 750 appears to be a close approximation.
       '''

       if df['MSA'].mode()[0] == "Phoenix-Mesa-Scottsdale, AZ MSA":
           df['Rent_monthly'] = (df['Revenue_per_sqft_month'] * 750).apply('${:,.0f}'.format)
       else:
           df['Rent_monthly'] = ((df['Preceding Fiscal Year Revenue'] / df['Size'])/12).apply('${:,.0f}'.format)

       # Format Revenue and Area Columns
       df['Preceding Fiscal Year Revenue'] = df['Preceding Fiscal Year Revenue'].apply('${:,.0f}'.format)
       df['EstRentableArea'] = df['EstRentableArea'].apply('{:,.0f}'.format)
       df['Opex'] = df['Opex'].apply('${:,.0f}'.format)
       df['EstValue'] = df['EstValue'].apply('${:,.0f}'.format)

       comps_data = df.to_dict("rows")

       df['Most Recent Physical Occupancy'] = df['Most Recent Physical Occupancy'].apply(clean_percent).astype('float')


       df1 = df

       # Format / clean up
       df1['Opex'] = df1['Opex'].apply(clean_currency).astype('float')

       # Rent col
       rent_col = df1[df1['Estimated_Rent'] > 0]
       occ_col = df1[df1['Most Recent Physical Occupancy'] > 0]
       opex_col = df1[df1['Opex'] > 0]

       rent_avg = rent_col['Estimated_Rent'].mean()
       occ_avg = occ_col['Most Recent Physical Occupancy'].mean()
       opex_avg = opex_col['Opex'].mean()

       # Formatting
       df1['Estimated_Rent'] = df1['Estimated_Rent'].apply('${:.0f}'.format)
       df1['Opex'] = df1['Opex'].apply('${:.0f}'.format)

       return (comps_data, "${:,.0f}".format(rent_avg), "{:,.1f}%".format(occ_avg), "${:,.0f}".format(opex_avg))

    else:

       return (no_update)


# Update modal on click event
@application.callback(
                          [
                               Output("modal-1","is_open"),

                               # Update Images in carousel based on selection
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
                               Output("distance","children")
                          ],

                          [
                               # Button clicks
                               Input("map-graph1","clickData"),
                               Input("comps-button", "n_clicks"),
                               Input("close","n_clicks")
                          ],

                          [
                                State("modal-1", "is_open")
                          ],
                    )
def display_popup(clickData, n_clicks, n_clicks1, is_open):

    if clickData:

        res = json.dumps(clickData, indent=2)

        print("clickData response", res)

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
        Distance = clickData["points"][0]["customdata"][11]

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

        if Distance == "N/A":
            Distance_fmt = Distance
        else:
            Distance = float(Distance)
            Distance_fmt = "{:,.1f} miles".format(Distance)

        return(not is_open, carousel, Name, Address, Size, Built, Property, rent_fmt, Revenue_fmt, RentRate_fmt, RentMon_fmt, Occupancy_fmt, RentArea_fmt, AssessedValue_fmt, Distance_fmt)

    elif n_clicks1:

        return is_open

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
                "local_rent": rent_card
               }
