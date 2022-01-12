# packages

import pandas as pd
import dash
from dash.dependencies import Input, Output, State
from dash import dcc
from dash import dash_table, html
import plotly as py
from plotly import graph_objs as go
from plotly.graph_objs import *
import flask
from app import app
from datetime import date, datetime, timedelta
import plotly.figure_factory as ff
import numpy as np
from collections import defaultdict
import dash_bootstrap_components as dbc

# Import file containing lead matrix
from return_leads import top_leads

# Read data - tenant
df_market = pd.read_csv('df_market.csv')

df_prop = pd.read_csv('df_list.csv')

# Dictionary to map cities to company
multivaldict = defaultdict(list)

for idx,row in df_prop.iterrows():

    if row['city'] not in multivaldict[row['Company']]:
        multivaldict[row['Company']].append(row['city'])


# Dropdown List
Company_List = list(df_prop['Company'].unique())
Asset_Type = list(df_market['Property_Type'].unique())


# App Layout for designing the page and adding elements
layout = html.Div([

    html.Div([

        dcc.Dropdown(
                id='company-select',
                options=[{'label': i, 'value': i} for i in multivaldict.keys()],
                value='Company',
                placeholder="Company",
                style={'width': '90%', 'float': 'left'}

        ),

        # Market/City
        dcc.Dropdown(
                id='market-select',
                value='',
                style={'width': '90%', 'float': 'left'}
        ),

        # Assets
        dcc.Dropdown(
                id='asset-select',
                options=[{'label': i, 'value': i} for i in Asset_Type],
                value='Asset 1',
                placeholder="Asset",
                style={'width': '90%', 'float': 'left', 'margin-left': '0%', 'margin-top': '0px'}
        ),

    ], style={"width": "38%", "margin-left": "0%", "margin-right": "1%", "margin-top":"18%" }),

    dbc.Modal(
        [
            dbc.ModalHeader("Hello there."),
            dbc.ModalBody("You have new leads to review."),
            dbc.ModalFooter(
                dbc.Button(
                    "Close", id="close-sm", className="ml-auto")
                ),
        ],
            id="modal-sm",
            size="sm"
            #style={'display': 'inline-block', 'width': '60%', 'float': 'right', 'margin-top': '-2em'}
    ),



    html.Div(id='welcome-text', style={'display': 'inline-block',
                                       'width':'50%',
                                       'float':'left',
                                       'margin-top': '1em',
                                       'font-size': 'x-large',
                                       'font-style': 'italic',
                                       'font-weight': '650'}),


    # html.Div([
    #
    #     dbc.Modal(
    #         [
    #             dbc.ModalHeader("Header"),
    #             dbc.ModalBody("This modal is vertically centered"),
    #             dbc.ModalFooter(
    #                 dbc.Button(
    #                     "Close", id="close-centered", className="ml-auto"
    #                 )
    #             ),
    #         ],
    #
    #         id="modal-centered",
    #         centered=True,
    #     ),
    #
    # ], style={'display': 'inline-block', 'width': '50%', 'float': 'left', 'margin-top': '1em'}),


    html.Div([

        html.H5("Prospective Tenant Leads"),

        dash_table.DataTable(

            id='tenant-table',

            columns=[{'id':'Tenant','name':'Tenant'},
                     {'id':'Tenant_Industry','name':'Tenant_Industry'},
                     {'id':'num_employees','name':'Number of Employees'},
                     {'id':'size_calc','name': 'Seeking RSF - Size'},
                     {'id':'Stage','name':'Status'},
                     {'id':'New_Lease','name': 'Lease Type'},
                     {'id':'New_Commencement','name': 'Commencement Date'},
                     {'id':'contact_info','name': 'Contact / Notes'}],
                     #{'id':'mean','name':'mean'}],

            style_data_conditional=[
                {

                    'if': {
                        'column_id': 'Tenant',
                        'filter_query': '{size_calc} >= 10000'
                    },
                    'backgroundColor': 'gold'
                },

            ],

            style_cell={
                'fontFamily': 'Open Sans',
                'textAlign': 'center',
                'height': '40px',
                'padding': '2px 22px',
                'whiteSpace': 'inherit',
                'overflow': 'hidden',
                'textOverflow': 'ellipsis',
            },

            style_table={
                'maxHeight': '50ex',
                'overflowY': 'scroll',
                'width': '90%',
                'minWidth': '100%',
            },

            page_size = 8,
            sort_action='native',
            row_selectable='multi',
            filter_action='native',
            row_deletable=True,
            editable=True
        ),
    ], style={'display': 'inline-block', 'width': '100%', 'float': 'left', 'margin-top': '3em'})

    #html.Div([

    #    dcc.Graph(id='lease-exp-plot')

    #], style={'display': 'inline-block', 'width': '45%', 'height': '100%', 'float': 'right', 'margin-top': '0em'})

])


# Load dynamic market/city drop down
@app.callback(Output('market-select', 'options'),
              [
                  Input('company-select', 'value')
              ]
             )
def set_market_options(company):

    return [{'label': i, 'value': i} for i in multivaldict[company]]


# Show Markets
@app.callback(Output('display-market-select', 'children'),
              [
                  Input('market-select', 'value')
              ]
             )
def set_market_value(selected_value):

    return [{'label': i, 'value': i} for i in selected_value]


# Welcome Text Message
@app.callback(Output('welcome-text', 'children'),
              [
                  Input('company-select', 'value')
              ]
             )
def set_welcome_text(company):

    return "Welcome, {}.".format(company)


# Pop up message
@app.callback(Output('modal-sm', 'is_open'),
              [
                    Input('company-select', 'value'),
                    Input('market-select', 'value'),
                    Input("close-sm", "n_clicks")],
                [State("modal-sm", "is_open")],
            )
def toggle_modal(company, market, close, is_open):
    if company and market:
        return not is_open
    if close:
        return is_open

# Update submarket options based on selected market

#@app.callback(Output('submarket-select', 'options'),
#              [
#                  Input('location-select', 'value')
#              ]
#             )
#def set_cities_options(market):
#
#    df_market_sub = df_market.loc[(df_market['City'] == market)]
#
#    Submarket_List = list(df_market_sub['SubMarket'].unique())
#
#    return [{'label': i, 'value': i} for i in Submarket_List]


# Update benchmark table
#@app.callback(Output('benchmark-table', 'figure'),
#              [
#                  Input("company-select", "value"),
#                  Input("location-select", "value"),
#                  Input("sublocation-select", "value"),
#              ],
#             )
#def metric1_callback(company, market, submarket):
#
#    df_sub = df_market.loc[(df_market['Landlord'] == company)
#                          & (df_market['City'] == market)
#                          & (df_market['SubMarket'] == submarket)]
#
#     metric1 = df_sub['Rent_SF_Yr'].mean()
#     rate = '${:,.2f}'.format(metric1)

#     metric2 = df_sub['Lease_Term_Yr'].mean()
#     lease = round(metric2, 1)

#     df_metrics = pd.DataFrame([[rate, lease]], columns = ['Avg. Rental Rate ($/SF/Yr)','Avg. Lease Term (Yr)'])

#     prev = date.today().replace(day=1) - timedelta(days=1)
#     prev = datetime.strftime(prev, "%m/%d/%y")

#     last_update = "Last updated {}".format(prev)

#     return{

#         'data': [go.Table(

#                     header=dict(values=list(df_metrics.columns),
#                                 fill = dict(color='#C2D4FF'),
#                                 align = ['center'],
#                                 font = dict(color='black', size = 20),
#                                 height = 65),

#                     cells=dict(values=[rate,
#                                        lease,
#                                       ],
#                                 fill = dict(color='#F5F8FF'),
#                                 align = ['left'],
#                                 font = dict(color='black', size = 18),
#                                 height = 40)

#                     )],

#         'layout' : go.Layout(

#                     title="SubMarket Benchmarks",
#                     font=dict(size=20, color='black'),
#                     annotations=[dict(text = last_update,
#                                       align = "left",
#                                       valign = "bottom",
#                                       showarrow = False,
#                                       font = dict(color = "black", size = 12))],
#                     height=300,
#         )
#     }


# Render list of all tenants likely to be in the market for an office space.

@app.callback(Output('tenant-table', 'data'),
               #Output('tenant-table', 'columns'),
              [
                  Input("company-select", "value"),
                  Input("market-select", "value")
              ],
             )
def render_table(company, market):

    # Lookup Properties based on selections - Landlord and market.

    if company and market:

        result = top_leads(company, market)

        print(f'company = {company} | market = {market}')

        df = pd.DataFrame(result, columns = ['Tenant_Industry','Tenant','num_employees','size_calc','Stage','New_Lease','New_Commencement','mean'])
        df.dropna(inplace=True)

        data_ob = df.to_dict('rows')

        return (data_ob)

    else:

        return (dash.no_update)


# Market Demand Activity - Plots of Leases set to Expire in a given Submarket
# @app.callback(Output('lease-exp-plot', 'data'),
#               [
#                   Input("company-select", "value"),
#                   Input("location-select", "value"),
#                   Input("asset-select", "value"),
#                   Input("sublocation-select", "value"),
#               ],
#              )
# def plot_hist(company, market, asset, submarket):

#     # Filter the dataframe with selected values
#     df_market_sub = df_market.loc[(df_market['Landlord'] == company)
#                                  & (df_market['City'] == market)
#                                  & (df_market['Property_Type'] == asset)
#                                  & (df_market['SubMarket'] == submarket)]


#     df_market_sub = df_market_sub[['City',
#                                    #'Commencement_Date',
#                                    'Expiration_Date',
#                                    'Landlord',
#                                    'Location',
#                                    'Property_Type',
#                                    'SubMarket',
#                                    'Rent_SF_Yr',
#                                    'Lease_Term_Yr'
#                                  ]]

#     df_market_sub['Expiration_Date'] = pd.to_datetime(df_market_sub['Expiration_Date'])

#     df_market_sub.set_index('Expiration_Date').groupby(['Landlord','City','Location','Property_Type','SubMarket']).resample('Q', convention='end').mean()

#     df_market_agg = df_market_sub

#     df_market_agg = df_market_agg.reset_index()

#     data = dict(
#                   x = df_market_agg['Expiration_Date'],
#                   autobinx = False,
#                   autobiny = True,
#                   marker = dict(color = 'rgb(68, 68, 68)'),
#                   name = 'date',
#                   type = 'histogram',
#                   xbins = dict(
#                                 end = '2019-06-30 12:00',
#                                 size = 'M1',
#                                 start = '2024-12-31 12:00'
#                   )
#             )

#     layout = dict(
#                   paper_bgcolor = 'rgb(240, 240, 240)',
#                   plot_bgcolor = 'rgb(240, 240, 240)',
#                   title = '<b>xyz</b>',
#                   xaxis = dict(
#                                 title = '',
#                                 type = 'date'
#                           ),
#                   yaxis = dict(
#                   title = 'xyz',
#                   type = 'linear'
#                   ),
#                   updatemenus = [dict(
#                                         x = 0.1,
#                                         y = 1.15,
#                                         xref = 'paper',
#                                         yref = 'paper',
#                                         yanchor = 'top',
#                                         active = 1,
#                                         showactive = True,
#                                         buttons = [
#                                                 dict(
#                                                      args = ['xbins.size', 'D1'],
#                                                      label = 'Day',
#                                                      method = 'restyle',
#                                                 ), dict(
#                                                      args = ['xbins.size', 'M1'],
#                                                      label = 'Month',
#                                                      method = 'restyle',
#                                                 ), dict(
#                                                      args = ['xbins.size', 'M3'],
#                                                      label = 'Quater',
#                                                      method = 'restyle',
#                                                 ), dict(
#                                                      args = ['xbins.size', 'M6'],
#                                                      label = 'Half Year',
#                                                      method = 'restyle',
#                                                 ), dict(
#                                                      args = ['xbins.size', 'M12'],
#                                                      label = 'Year',
#                                                      method = 'restyle',
#                                         )]
#                               )]
#                    )

#     return {"data": data, "layout": layout}
