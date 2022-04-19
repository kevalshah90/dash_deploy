# Packages
import pandas as pd
import numpy as np
import dash
from dash.dependencies import Input, Output, State
from dash import dcc
from dash import html, dash_table
import plotly as py
from plotly import graph_objs as go
from plotly.subplots import make_subplots
from plotly.graph_objs import *
import flask
from application import application
from datetime import date, datetime, timedelta
import plotly.express as px
from collections import defaultdict
from dash.dash import no_update
import os
import dash_bootstrap_components as dbc
import plotly.io as pio
from scipy.stats import poisson
from statistics import mean
from natural_vac import reg_vacancy
from draw_polygon import market_Lookup
from funcs import clean_percent, clean_currency, get_geocodes
from dash.exceptions import PreventUpdate
from sklearn.preprocessing import MinMaxScaler
import geocoder
import mapbox

# Polynomial regression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline

# US Census libraries and API key
import censusgeocode as cg
from census import Census
from us import states
c = Census("71a69d38e3f63242eca7e63b8de1019b6e9f5912")

# Google maps api key
import googlemaps
gmaps = googlemaps.Client(key="AIzaSyC0XCzdNwzI26ad9XXgwFRn2s7HrCWnCOk")

# Google cloud + Big Query
from google.cloud import bigquery
import pyarrow
client = bigquery.Client(project = "stroom-data-exploration")
os.environ.setdefault("GCLOUD_PROJECT", "stroom-data-exploration")

# Mapbox
MAPBOX_KEY = "pk.eyJ1Ijoia2V2YWxzaGFoIiwiYSI6ImNqeDNsNzY2YTAwN3g0YW13aHMyNXIwMHAifQ.Hx8cPYyTFTSXP9ixiNcrTw"
token = MAPBOX_KEY
Geocoder = mapbox.Geocoder(access_token=token)

plotly_template = pio.templates["plotly"]

# Read all market data CA + PX - CBSA level Rents + Vacancy + Economic data
df_market = pd.read_csv(os.getcwd() + "/data/df_market_v1.csv")

# Geometries from Google Big Query
## Obtain MSA / CBSA geometries from Google Big Query
metros = ['San Jose-Sunnyvale-Santa Clara, CA','San Francisco-Oakland-Berkeley, CA','Los Angeles-Long Beach-Anaheim, CA','San Diego-Chula Vista-Carlsbad, CA','Phoenix-Mesa-Chandler, AZ']

sql = """
  SELECT *
  FROM `bigquery-public-data.geo_us_boundaries.cbsa`
  WHERE name IN UNNEST(%s)
""" %(metros)

df_geom = client.query(sql).to_dataframe()

# Create a dict of CBSAs and it's geometry
geom_dict = dict(zip(df_geom.name, df_geom.cbsa_geom))

# Market List
Market_List = list(df_market["CBSA"].unique())

# App Layout for designing the page and adding elements
layout = html.Div([

            html.Div([

                dbc.Card(
                            [
                                dbc.CardHeader("Market - MSA"),
                                dbc.CardBody(
                                    [
                                        html.P(id="market-card", style={"padding-right":"3px","font-size":"0.9em"}),
                                    ]

                                ),
                            ],
                            id="market",
                            color="light",
                            style={"width": "21rem", "margin-bottom": "5em", "height": "7em"}
                ),


                # Demographics data
                dbc.Row([
                            dbc.Card(
                                        [
                                            dbc.CardHeader("Median Income - County"),
                                            dbc.CardBody(
                                                [
                                                    html.P(id="income-card", style={"font-size": "1.7em"}),
                                                ]

                                            ),
                                        ],
                                        id="inc-stat",
                                        color="light",
                                        style={"width": "10rem", "margin-left": "2.5%", "height": "9em"}
                            ),

                            dbc.Card(
                                        [
                                            dbc.CardHeader("Population Density - County"),
                                            dbc.CardBody(
                                                [
                                                    html.P(id="pop-card", style={"font-size": "1.5em"}),
                                                ]

                                            ),
                                        ],
                                        id="pop-stat",
                                        color="light",
                                        style={"width": "10rem", "margin-left": "2.5%", "height": "9em"}
                            ),

                            dbc.Card(
                                        [
                                            dbc.CardHeader("Median Home Value - County"),
                                            dbc.CardBody(
                                                [
                                                    html.P(id="home-value", style={"font-size": "1.5em"}),
                                                ]

                                            ),
                                        ],
                                        id="home-stat",
                                        color="light",
                                        style={"width": "10rem", "margin-left": "2.5%", "height": "9em"}
                            ),

                            dbc.Card(
                                        [
                                            dbc.CardHeader("Rent to Income ratio"),
                                            dbc.CardBody(
                                                [
                                                    html.P(id="ratio-card", style={"font-size": "2em"}),
                                                ]

                                            ),
                                        ],
                                        id="ratio-stat",
                                        color="light",
                                        style={"width": "10rem", "margin-left": "2.5%", "height": "9em"}
                            ),

                ], className="row-demo-analysis"),

                # Natural Vacancy
                dcc.Graph(

                            id="vacancy-graph",
                            style={"display": "inline-block", "width": "1118px", "float": "left", "margin-top": "5%", "height":"500px"}

                ),

                # Economy Graph
                dcc.Graph(

                            id="economy-graph",
                            style={"display": "inline-block", "width": "1118px", "float": "left", "margin-top": "5%", "height":"500px"}

                ),

                html.Div(id="dummy-div"),


        ], className="vacancy-style",
           style={"display": "inline-block",
                  "width": "50%",
                  "float": "left"})

],id="graph-area")

# Callbacks

# Update market-select based on Address in Comps tab
@application.callback(Output("market-card", "children"),
                      [
                         Input("dummy-div", "children"),
                      ],
                      [
                         State("comps-store", "data")
                      ]
                     )
def update_market(dummy, comps_store):

    if comps_store:

        addr =  comps_store['propinfo'][0]['address']

        geocode_result = gmaps.geocode(addr)

        Lat = geocode_result[0]["geometry"]["location"]["lat"]
        Long = geocode_result[0]["geometry"]["location"]["lng"]

        # Lookup market / submarket
        market = market_Lookup(Lat, Long, geom_dict)

        if market:
            return market.upper()

        else:
            return no_update

    else:
        return no_update

# Demographics stats
@application.callback([

                         Output("income-card", "children"),
                         Output("pop-card", "children"),
                         Output("home-value", "children"),
                         Output("ratio-card", "children")

                      ],
                      [
                         Input("market-card", "children"),
                      ],
                      [
                         State("comps-store", "data")
                      ]
                )
def demo_data(market, comps_store):

    if comps_store:

        addr =  comps_store['propinfo'][0]['address']

        g = geocoder.mapbox(addr, key=token)
        geojson = g.json

        # Lookup market / submarket
        Lat, Long = get_geocodes(addr)
        market = market_Lookup(Lat, Long, geom_dict)

        # Census
        result = cg.coordinates(x=geojson['lng'], y=geojson['lat'])

        # Median Income
        cres = c.acs5.state_county(
                                   'B19013_001E',
                                   result['States'][0]['STATE'],
                                   result['County Subdivisions'][0]['COUNTY']
                                  )

        inc = '${:,.0f}'.format(cres[0]['B19013_001E'])

        # Median Home Value
        cres = c.acs5.state_county('B25077_001E',
                                   result['States'][0]['STATE'],
                                   result['County Subdivisions'][0]['COUNTY']
                                  )

        home_value = '${:,.0f}'.format(cres[0]['B25077_001E'])

        # Population
        cres = c.acs5.state_county(
                                   'B01003_001E',
                                   result['States'][0]['STATE'],
                                   result['County Subdivisions'][0]['COUNTY']
                                  )

        pop = '{:,.0f}'.format(cres[0]['B01003_001E'])

        # Calculate Population Density
        geo = result['Counties'][0]['GEOID']

        sql = """
          SELECT *
          FROM `bigquery-public-data.geo_us_boundaries.counties`
          WHERE geo_id IN UNNEST(%s)
        """ %([geo])

        df_counties_geo = client.query(sql).to_dataframe()

        # Meters to square miles
        area = df_counties_geo['area_land_meters'][0]/2.59e+6

        # Population / Area in Square Miles

        popdensity = cres[0]['B01003_001E']/area

        popdensity = '{:,.0f} mi\u00b2'.format(popdensity)

        # Monthly Average/Median rent to gross median income ratio

        income = int(clean_currency(inc))

        df = df_market[df_market['CBSA'] == market]

        df['Rent'] = df['Rent'].apply(clean_currency)

        ratio = df['Rent'].mean()/(income/12)
        ratio = '{:,.0f}%'.format(ratio*100)

        return (inc, popdensity, home_value, ratio)

    else:

        return (no_update, no_update, no_update)


# Natural level of vacancy
@application.callback([
                        Output("vacancy-graph", "figure"),
                        Output("economy-graph", "figure")
                      ],
                      [
                         #Input("market-select", "value")
                         Input("dummy-div", "children"),
                      ],
                      [
                         State("comps-store", "data")
                      ]
                     )
def update_vacancy(dummy, comps_store):

    if comps_store:

       addr =  comps_store['propinfo'][0]['address']

       geocode_result = gmaps.geocode(addr)

       Lat = geocode_result[0]["geometry"]["location"]["lat"]
       Long = geocode_result[0]["geometry"]["location"]["lng"]

       # Lookup market / submarket
       market = market_Lookup(Lat, Long, geom_dict)

       # Make lowercase
       df_market['CBSA'] = df_market['CBSA'].str.lower()

       #  Run regression model for Natural vacancy rate for each market
       df = df_market[df_market["CBSA"] == market]

       '''
       # Code for Natural Vacancy graph
       '''

       df1 = reg_vacancy(df)

       # Reset index for tickvals in Vacancy Graph
       df1.reset_index(drop=True, inplace=True)

       # Scale Difference between Observed and Calculated Natural Vacancy column between -5 and 5
       scaler = MinMaxScaler(feature_range=(-5,5))

       df1['scaled_diff'] = scaler.fit_transform(df1['Diff_observed_natural'].values.reshape(-1,1))

       df1["Color"] = np.where(df1["scaled_diff"]<0, 'rgb(0,0,255)', 'rgb(255,0,0)')
       df1["Name"] = np.where(df1["scaled_diff"]<0, 'Low Demand, High Vacancy', 'High Demand, Low Vacancy')

       df_High = df1[df1['Name'] == 'High Demand, Low Vacancy']
       df_Low = df1[df1['Name'] == 'Low Demand, High Vacancy']

       fig1 = go.Figure(

            data=[

                  go.Bar(
                            x=list(df_High.index),
                            y=df_High["scaled_diff"],
                            name='High Demand, Low Vacancy',
                            marker=dict(color="rgb(255,0,0)")
                        ),

                  ],

       )

       fig1.add_trace(go.Bar(
                            x=list(df_Low.index),
                            y=df_Low["scaled_diff"],
                            name="Low demand, High Vacancy",
                            marker=dict(color="rgb(20,148,244)")
                        )
       )


       fig1.update_layout(

                            title="Rents follow Vacancy rates: Measuring excess demand and supply in the market.",

                            xaxis=dict(
                                title="Source: BLS, Realtor.com, Moody's Analytics",
                                title_font_size=10,
                                tickangle=60,
                                tickvals=list(df1.index),
                                ticktext=df1['Date_Col'],
                                tickfont=dict(family="Rockwell", color="crimson", size=14)
                            ),

                            yaxis=dict(
                                title="Net Change in Demand and Vacancy",
                                showticklabels=True
                            ),

                            barmode="stack",

                            template=plotly_template,
                            showlegend=True

                        )




       '''
       Code for Economy Graph
       '''

       fig2 = go.Figure(

            data=[

                  go.Scatter(
                            x=df['Date_Col'],
                            y=df['Rent_Change'],
                            name='Rent',
                            marker=dict(color="rgb(255,0,0)", size=25)
                        ),

                  ],

       )

       fig2.add_trace(go.Scatter(
                            x=df["Date_Col"],
                            y=df["Employment_Change"],
                            name="Employment",
                            marker=dict(color="rgb(20,148,244)", size=25)
                        )
       )


       fig2.update_layout(

                            title="{} - Change in Employment and Avg. Rents for 1 BR".format(market.upper()),

                            xaxis=dict(
                                title="Source: BLS/Census, Realtor.com",
                                title_font_size=10,
                                tickangle=60,
                                tickfont=dict(family="Rockwell", color="crimson", size=14)
                            ),

                            yaxis=dict(
                                title="Percentage Change",
                                showticklabels=True
                            ),

                            template=plotly_template,
                            showlegend=True

                        )

       return (fig1, fig2)

    else:

       return (no_update)




# Store graphs dcc.Store component
@application.callback(Output("analysis-store","data"),
                     [
                          Input("vacancy-graph","figure"),
                          Input("price", "children")
                     ]
                     )
def comp_store(vacancy_graph, calc_price):

    if calc_price:
        val1 = calc_price.split('-')[0]
        val2 = val1.replace("$","")

    #if vacancy and price and market:
    if vacancy_graph and calc_price:

        return {
                "vacancy": vacancy_graph,
                "calc_price": float(val2)
               }
