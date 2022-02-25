# Packages
import pandas as pd
import numpy as np
import os
import json
import ast
import dash
from dash.dependencies import Input, Output, State
from dash import dcc
from dash import html, dash_table
import dash_bootstrap_components as dbc
import plotly as py
from plotly import graph_objs as go
from plotly.graph_objs import *
import plotly.figure_factory as ff
from application import application
from datetime import date, datetime, timedelta
from collections import defaultdict
import mapbox
import geopandas as gpd
import shapely.geometry
from scipy import spatial
from dash.dash import no_update
from dash.exceptions import PreventUpdate

from funcs import clean_percent, clean_currency, get_geocodes, create_presigned_url, streetview, coords_dict

# Google Maps API key
import googlemaps
gmaps = googlemaps.Client(key="AIzaSyC0XCzdNwzI26ad9XXgwFRn2s7HrCWnCOk")

# Mapbox
MAPBOX_KEY="pk.eyJ1Ijoia2V2YWxzaGFoIiwiYSI6ImNreXhpeGlhYjAyMm8yb3VxbmRreTJzbmoifQ.ekuKTZVGZ08pnaOLOeMM1Q"
token = MAPBOX_KEY
Geocoder = mapbox.Geocoder(access_token=token)

# Read data
df_lease_mf = pd.read_csv(os.getcwd() + "/data/LeaseComp_mf_ml_forecasted_v1.csv")
Market_List = list(df_lease_mf['MSA'].unique())

# App Layout for designing the page and adding elements
layout = html.Div([

                   dbc.Row([

                        dbc.InputGroup(
                            [

                               dbc.InputGroupAddon("Market"),

                               dcc.Dropdown(
                                                id="market-deal",
                                                persistence=True,
                                                options=[{"label": name, "value": name} for name in Market_List],
                                                placeholder="Market",
                                                value="Los Angeles-Long Beach-Santa Ana, CA MSA"
                               ),

                            ],

                         className="market-deal-style",

                        ),


                        dbc.InputGroup(
                            [

                               dbc.InputGroupAddon("Property type"),
                               dcc.Dropdown(
                                              id="prop-type-deal",
                                              persistence=True,
                                              persistence_type="memory",
                                              options=[
                                                       {"label": "Multi-Family", "value": "Multi-Family"}
                                              ],
                                              value="Multi-Family"
                               ),


                         ],

                         className="prop-type-deal-style",

                        ),

                        # Year Built
                        dbc.InputGroup(
                            [

                                dbc.InputGroupAddon("Year Built"),
                                dbc.Input(
                                          id="year-built-min",
                                          persistence=True,
                                          persistence_type="memory",
                                          placeholder="Min"
                                         ),
                                dbc.Input(
                                          id="year-built-max",
                                          persistence=True,
                                          persistence_type="memory",
                                          placeholder="Max"
                                         ),
                            ], style = {"height":"44px"},

                        ),

                        # Number of Units
                        dbc.InputGroup(
                            [

                                dbc.InputGroupAddon("Units"),
                                dbc.Input(
                                          id="num-units-min",
                                          persistence=True,
                                          persistence_type="memory",
                                          placeholder="Min"
                                         ),
                                dbc.Input(
                                          id="num-units-max",
                                          persistence=True,
                                          persistence_type="memory",
                                          placeholder="Max"
                                         ),

                            ], style={"height":"44px"},

                        ),

                   ], className="row-1-deal"),

                   dbc.Row(
                       [

                         dbc.Col(

                            html.Div([

                                # Plot properties map
                                dcc.Graph(id="map-deal",
                                          style={"display": "inline-block", "width": "660%", "float": "left", "height":"700px"}
                                          ),

                                ], className="deal-map-style"),

                         width={"size": 2, "order": "first"}),


                         dbc.Col([

                            # dbc popup / modal - comps
                            html.Div([

                                dbc.Modal(
                                    [
                                        dbc.ModalHeader("Property Information", style={"color":"black", "justify-content":"center"}),
                                        dbc.ModalBody(
                                            [

                                                # Images
                                                html.Div(id="carousel_deal"),

                                                dbc.Label("Property Name:", style={"color":"black", "font-weight": "bold", "margin-right":"10px", "margin-top":"1.5%"}),
                                                dbc.Label("Property Name:", id="prop_name_deal"),
                                                html.Br(),

                                                dbc.Label("Address:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                                dbc.Label("Address:", id="Address_deal"),
                                                html.Br(),

                                                dbc.Label("Number of Units:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                                dbc.Label("Size:", id="Size_deal"),
                                                html.Br(),

                                                dbc.Label("Year Built:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                                dbc.Label("Year Built:", id="Yr_Built_deal"),
                                                html.Br(),

                                                dbc.Label("Property: ", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                                dbc.Label("Property:", id="Property_deal"),
                                                html.Br(),

                                                dbc.Label("Fiscal Revenue:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                                dbc.Label("Revenue:", id="Revenue_deal"),
                                                html.Br(),

                                                dbc.Label("Revenue / Unit / Month:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                                dbc.Label("Revenue / Month:", id="Monthly_Revenue_deal"),
                                                html.Br(),

                                                dbc.Label("Rental rate / Sq.ft / Month:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                                dbc.Label("Rental Rate:", id="Rent_Sqft_deal"),
                                                html.Br(),

                                                dbc.Label("Occupancy:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                                dbc.Label("Occupancy:", id="occ-modal_deal"),
                                                html.Br(),

                                                dbc.Label("Rentable Area:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                                dbc.Label("Rentable Area:", id="rent-area-modal_deal"),
                                                html.Br(),

                                                dbc.Label("Assessed Value:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                                dbc.Label("Assessed Value:", id="assessed-value_deal"),
                                                html.Br(),

                                                dbc.Label("Last Sale Date:", style={"color":"black", "font-weight": "bold", "margin-right":"10px"}),
                                                dbc.Label("Last Sale Date:", id="sale-date_deal"),
                                                html.Br(),

                                            ]
                                        ),
                                        dbc.ModalFooter(
                                            [

                                                dbc.Label("Sources: CMBS, CoreLogic", style={"float":"left", "padding-right":"26em", "font-size":"12px"}),

                                                dbc.Button("OK", color="primary", size="lg", id="close_deal", className="mr-1"),
                                            ]
                                        ),
                                    ],
                                    id="modal-1-deal",
                                ),

                            ], style={"width": "50%"}),

                        ], width={"size": 10, "order": "last", "offset": 8},),
                    ]),


                    dbc.Row([

                            # # Lease Table
                            html.Div([

                                dash_table.DataTable(

                                    id="comps-table-deal",

                                    columns=[{"id":"Property Name","name":"Property Name"},
                                             {"id":"Property Type","name":"Property Type"},
                                             {"id":"Zip Code","name":"Zip Code"},
                                             {"id":"Preceding Fiscal Year Revenue","name": "Revenue"},
                                             {"id":"EstRentableArea","name": "Area (Sq.ft)"},
                                             {"id":"Most Recent Physical Occupancy","name":"Occupancy"},
                                             {"id":"Year Built","name": "Year Built"},
                                             {"id":"Size","name": "Number of Units"},
                                             {"id":"Opex", "name":"Opex (Monthly)"},
                                             {'id':"EstValue", "name":"Assessed Value"},
                                             {'id':"lastSaleDate", "name":"Last Sale Date"}],

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


                            ], className="table-style-deal"),

                        ]),

], id="deal-layout")


# Callbacks
# Update map graph
@application.callback([

                          Output("map-deal", "figure"),
                          Output("comps-table-deal", "data")

                      ],
                      [

                          Input("market-deal", "value"),
                          Input("prop-type-deal", "value"),
                          Input("year-built-min", "value"),
                          Input("year-built-max", "value"),
                          Input("num-units-min", "value"),
                          Input("num-units-max", "value")

                      ],
             )
def update_map_deal(market, proptype, year_built_min, year_built_max, num_units_min, num_units_max):

    # Adjust map view
    lat, long = get_geocodes(market)

    coords = coords_dict[market]

    layout_lat = coords[0]
    layout_lon = coords[1]

    zoom = 10

    datad = []

    if proptype == "Multi-Family":

        # Plot sample properties - match with starting view of the map
        df = df_lease_mf[df_lease_mf['MSA'] == market]

        # Apply filters
        df_lease_mf['Year Built'] = df_lease_mf['Year Built'].astype(int)

        if year_built_min and year_built_max:
            df = df_lease_mf[(df_lease_mf['Year Built'] >= int(year_built_min)) & (df_lease_mf['Year Built'] <= int(year_built_max))]


        df_lease_mf['Size'] = df_lease_mf['Size'].astype(int)

        if num_units_min and num_units_max:
            df = df_lease_mf[(df_lease_mf['Size'] >= int(num_units_min)) & (df_lease_mf['Size'] <= int(num_units_max))]


        # Generate Address string
        addr_cols = ["Address", "City", "State", "Zip Code"]
        df['Address_Comp'] = df[addr_cols].apply(lambda row: ' '.join(row.values.astype(str)), axis=1)

        # Hover Info
        propname = df['Property Name']

        # Monthly Revenue / Unit / Month
        df['EstRevenueMonthly'] = (df['Preceding Fiscal Year Revenue']/df['Size'])/12

        # Format Columns
        df['EstValue'] = df['EstValue'].apply('${:,.0f}'.format)
        df['Preceding Fiscal Year Revenue'] = df['Preceding Fiscal Year Revenue'].apply('${:,.0f}'.format)
        df['Occ.'] = df['Occ.'].apply(clean_percent)

        # Columns for customdata
        cd_cols = ['Property Name','Address_Comp','Size','Year Built','Property Type','Preceding Fiscal Year Revenue','EstRevenueMonthly','Revenue_per_sqft_month','Occ.','EstRentableArea','EstValue','lastSaleDate']

        datad.append({

                        "type": "scattermapbox",
                        "lat": df['Lat'],
                        "lon": df['Long'],
                        "name": "Location",
                        "hovertext": propname,
                        "showlegend": False,
                        "hoverinfo": "text",
                        "mode": "markers",
                        "clickmode": "event+select",
                        "customdata": df.loc[:,cd_cols].values,
                        "marker": {
                            "autocolorscale": False,
                            "showscale":True,
                            "symbol": "circle",
                            "size": 9,
                            "opacity": 0.8,
                            "color": df['yhat'],
                            "colorscale": "blues",
                            "colorbar":dict(
                                            title= 'Upside',
                                            orientation= 'h',
                                            #nticks=10,
                                            showticklabels=True,
                                            thickness= 20,
                                            tickformatstops=dict(dtickrange=[0,10]),
                                            titleside= 'top',
                                            ticks= 'outside'
                                            #ticklen= 1
                                           )
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

        return ({"data": datad, "layout": layout}, df.to_dict("records"))




# Update comps modal on click event
@application.callback(
                          [
                               # Modal Comps
                               Output("modal-1-deal","is_open"),
                               Output("carousel_deal","children"),
                               Output("prop_name_deal","children"),
                               Output("Address_deal","children"),
                               Output("Size_deal","children"),
                               Output("Yr_Built_deal","children"),
                               Output("Property_deal","children"),
                               Output("Revenue_deal","children"),
                               Output("Monthly_Revenue_deal","children"),
                               Output("Rent_Sqft_deal","children"),
                               Output("occ-modal_deal","children"),
                               Output("rent-area-modal_deal","children"),
                               Output("assessed-value_deal","children"),
                               Output("sale-date_deal","children"),

                          ],

                          [
                               # Button clicks
                               Input("map-deal","clickData"),
                               Input("close_deal","n_clicks")

                          ],

                          [
                                State("modal-1-deal", "is_open")
                          ],
                    )
def display_popup(clickData, n_clicks, is_open):

    if clickData:

        res = json.dumps(clickData, indent=2)

        print("clickData response", res)

        Name = clickData["points"][0]["customdata"][0]
        Address = clickData["points"][0]["customdata"][1]
        Size = clickData["points"][0]["customdata"][2]
        Built = clickData["points"][0]["customdata"][3]
        Property = clickData["points"][0]["customdata"][4]
        Revenue = clickData["points"][0]['customdata'][5]
        Monthly_Revenue = clickData["points"][0]["customdata"][6]
        Revenue_Sqft = clickData["points"][0]["customdata"][7]
        Occupancy = clickData["points"][0]["customdata"][8]
        RentArea = clickData["points"][0]["customdata"][9]
        AssessedValue = clickData["points"][0]["customdata"][10]
        lastSaleDate = clickData["points"][0]["customdata"][11]

        # Formatting
        Occupancy = float(Occupancy.strip('%'))

        # Construct a list of dictionaries
        # Filter Pandas DataFrame
        df = df_lease_mf[df_lease_mf['Property Name'] == Name]

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

                # Get coordinates
                lat, long = get_geocodes(Address)

                # Get updated name of the streetview image
                name = streetview(lat, long, 'streetview')

                # Construct URL
                url = create_presigned_url('gmaps-images-6771', 'property_images/{}'.format(name))

                if "None" in url:
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
        if Revenue is None:
            Revenue_fmt == "N/A"
        else:
            Revenue = clean_currency(Revenue)
            Revenue_fmt = "${:,.0f}".format(float(Revenue))

        if Revenue_Sqft is None:
            Revenue_Sqft_fmt == "N/A"
        else:
            Revenue_Sqft_fmt = "${:,.1f} Sq.ft".format(Revenue_Sqft)

        if Monthly_Revenue is None:
            Monthly_Revenue_fmt == "N/A"
        else:
            Monthly_Revenue_fmt = "${:,.0f}".format(Monthly_Revenue)

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
        elif type(AssessedValue) != str:
            AssessedValue_fmt = "${:,.0f}".format(AssessedValue)
        else:
            AssessedValue_fmt = AssessedValue

        if lastSaleDate == "null":
            lastSaleDate_fmt = "N/A"
        else:
            lastSaleDate_fmt = lastSaleDate

        return(not is_open, carousel, Name, Address, Size, Built, Property, Revenue_fmt, Monthly_Revenue_fmt, Revenue_Sqft_fmt, Occupancy_fmt, RentArea_fmt, AssessedValue_fmt, lastSaleDate_fmt)

    elif n_clicks:

        return is_open

    else:
        return (no_update)
