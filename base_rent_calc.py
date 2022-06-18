import numpy as np
import pandas as pd
import seaborn as sns
import scipy as stats
import sklearn
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, MinMaxScaler, OrdinalEncoder
import os
from funcs import clean_percent, clean_currency
import sagemaker
from sagemaker.serializers import CSVSerializer
from sagemaker.deserializers import CSVDeserializer
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt
import os
import random
import string
import geopy.distance
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import OneHotEncoder, MinMaxScaler, OrdinalEncoder
import pygeohash as gh
from geolib import geohash
from funcs import clean_percent, clean_currency, city_geohash, gen_ids, walkscore

# Google maps api key
import googlemaps
gmaps = googlemaps.Client(key='AIzaSyC0XCzdNwzI26ad9XXgwFRn2s7HrCWnCOk')

# Mapbox API
import mapbox
from mapbox import Geocoder
MAPBOX_ACCESS_TOKEN='pk.eyJ1Ijoia2V2YWxzaGFoIiwiYSI6ImNqbW1nbG90MDBhNTQza3IwM3pvd2I3bGUifQ.dzdTsg69SdUXY4zE9s2VGg'
# Must be a public token, starting with `pk`
token = MAPBOX_ACCESS_TOKEN
geocoder = mapbox.Geocoder(access_token=token)

# AWS SageMaker
import boto3
import pickle
import sagemaker
from sagemaker.predictor import json_serializer, json_deserializer, Predictor
from sagemaker.amazon.amazon_estimator import get_image_uri
from time import gmtime, strftime
from sagemaker.xgboost import XGBoost, XGBoostModel
from sagemaker.session import Session
from sagemaker.local import LocalSession

# mysql connection
import pymysql
from sqlalchemy import create_engine
user = 'stroom'
pwd = 'Stroomrds'
host =  'aa1jp4wsh8skxvw.csl5a9cjrheo.us-west-1.rds.amazonaws.com'
port = 3306
database = 'stroom_main'
engine = create_engine("mysql+pymysql://{}:{}@{}/{}".format(user,pwd,host,database))
con = engine.connect()

# Read ML data
df_lease = pd.read_csv(os.getcwd() + "/data/df_ml_v1_march.csv")

# Drop column
df_lease.drop(df_lease.filter(regex="Unname"), axis=1, inplace=True)

# Subset cols
df_sub = df_lease[['Year Built',
                   'Size',
                   'Most Recent Physical Occupancy', # average of comps
                   'Operating Expenses at Contribution', # average of comps
                   'WalkScore',
                   'TransitScore',
                   'geohash',
                   'EstRentableArea', # gross area
                   'Loan Status', # mode of geo
                   'EstValue',
                   'CapRate', # average of comps
                   'Ownership',
                   'AirCon',
                   'Pool',
                   'Condition',
                   'constructionType',
                   'parkingType',
                   'numberOfBuildings',
                   'propertyTaxAmount',
                   'taxRate',
                   'Rent_1Br',
                   'mos_since_last_sale',
                   'Revenue_per_sqft_month']]


# Convert percentage to numeric
df_sub['Most Recent Physical Occupancy'] = df_sub['Most Recent Physical Occupancy'].apply(clean_percent).astype('float')

# Currency to numeric
df_sub['Operating Expenses at Contribution'] = df_sub['Operating Expenses at Contribution'].apply(clean_currency).astype('float')

# split df into train and test
X_train, X_test, y_train, y_test = train_test_split(df_sub.iloc[:,0:22], df_sub.iloc[:,-1], test_size=0.1, random_state=42)

# Encode categorical variables
cat_vars = ['geohash','Loan Status','Ownership','AirCon','Pool','Condition','constructionType','parkingType']
cat_transform = ColumnTransformer([('cat', OneHotEncoder(handle_unknown='ignore'), cat_vars)], remainder='passthrough')

encoder = cat_transform.fit(df_sub.iloc[:,0:22])


# Calculate distance between properties
# Define radius and find similar leases executed recently within the proximity.
def calc_distance(prop_loc, Lat, Long):

    prop_locs = (Lat, Long)

    dist = geopy.distance.distance(prop_loc, prop_locs).miles

    return dist


# Function to calculate optimal rent.
def calc_rent(prop_address, proptype, yr_built, space, units, ameneties, assval, occupancy, opex, taxAmt, taxRate, rent, lastSaleDate, geohash):

    np.random.seed(0)

    # Geocoding an address <-- Address of the subject property.
    geocode_result = gmaps.geocode(prop_address)

    Lat = geocode_result[0]['geometry']['location']['lat']
    Long = geocode_result[0]['geometry']['location']['lng']

    prop_loc = (Lat, Long)

    # Location characteristics
    Walk = walkscore(Lat, Long, prop_address, 'walk')
    Transit = walkscore(Lat, Long, prop_address, 'transit')

    # Format date
    if len(lastSaleDate) <= 10:
        lastSaleDate = datetime.strptime(lastSaleDate, '%Y-%m-%d')
    else:
        lastSaleDate = datetime.strptime(lastSaleDate, '%Y-%m-%dT%H:%M:%S').strftime('%Y-%m-%d')
        lastSaleDate = datetime.strptime(lastSaleDate, '%Y-%m-%d')

    # Calculate Months since last sale date
    mosLastSale = (pd.to_datetime('today') - lastSaleDate)/np.timedelta64(1, 'M')

    '''
    AWS endpoint invoke code
    '''

    client = boto3.session.Session(
        #'sagemaker-runtime',
        region_name="us-west-1",
        aws_access_key_id='AKIA2MQCGH6RW7TE3UG2',
        aws_secret_access_key='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'
    )

    sagemaker_client = sagemaker.session.Session(boto_session = client)

    # Create a test data point and save to csv - the input format for SageMaker Endpoint
    df = pd.DataFrame({

                               'Year Built': int(yr_built),
                               'Size': int(units),
                               'Most Recent Physical Occupancy': float(occupancy),
                               'Operating Expenses at Contribution': float(opex),
                               'WalkScore': Walk,
                               'TransitScore': Transit,
                               'geohash': geohash,
                               'EstRentableArea': space,
                               'Loan Status': df_sub['Loan Status'].mode(),
                               'EstValue': assval,
                               'CapRate': df_sub['CapRate'].median(),
                               'Ownership': np.random.choice(df_sub['Ownership'], 1)[0],
                               'AirCon': np.random.choice(df_sub['AirCon'], 1)[0],
                               'Pool': np.random.choice(df_sub['Pool'], 1)[0],
                               'Condition': np.random.choice(df_sub['Condition'], 1)[0],
                               'constructionType': np.random.choice(df_sub['constructionType'], 1)[0],
                               'parkingType': np.random.choice(df_sub['parkingType'], 1)[0],
                               'numberOfBuildings': df_sub['numberOfBuildings'].median(),
                               'propertyTaxAmount': taxAmt,
                               'taxRate': taxRate,
                               'Rent_1Br': rent,
                               'mos_since_last_sale': mosLastSale

                        }, index=[0])


    # Encode to handle categorical variables
    testpoint = encoder.transform(df).toarray().tolist()

    # to csv as fn_input accepts text/csv data type
    np.savetxt("test_point.csv", testpoint, delimiter=",", fmt='%s')

    file_name = ("test_point.csv")

    with open(file_name, "r") as f:
        payload = f.read().strip()

    payload = ', '.join(map(str, testpoint[0]))


    '''
    Endoint Name
    '''

    # Predict method
    endpoint_name = "sagemaker-xgboost-2022-03-29-19-22-30-787"

    predictor = Predictor(
                          endpoint_name = endpoint_name,
                          sagemaker_session = sagemaker_client,
                          serializer = CSVSerializer(),
                          deserializer = CSVDeserializer()
                         )

    response = predictor.predict(payload)

    # response
    res = float(response[0][0])

    print("Predicted value", res)


    '''
    Query to pull nearby comps - Default to 1 mile radius
    '''

    # Apply units / size filter - set lower and upper bounds
    lower_bound = int(units) - 65*int(units)/100
    upper_bound = int(units) + 65*int(units)/100

    '''
    CMBS data
    '''

    # Run query within a while-loop to get the required # of rows
    df_raw = pd.DataFrame({})
    rows = df_raw.shape[0]

    # Search radius - miles to meters
    radius_cmbs = 1.5*1609

    # Expand radius 1x
    for i in range(2):

        query = '''
                select * from stroom_main.df_raw_v1_march
                where st_distance_sphere(Point({},{}), coords) <= {};
                '''.format(Long, Lat, radius_cmbs)

        df_raw = pd.read_sql(query, con)

        # if no comps found, expand radius
        if df_raw.shape[0] == 0:
            radius_cmbs = radius_cmbs * 2
        else:
            break

    if df_raw.shape[0] > 0:

        # Add additional cols
        df_raw['Revenue_per_sqft_year'] = df_raw['Revenue_per_sqft_month'] * 12
        df_raw['Revenue_per_sqft_year'] = df_raw['Revenue_per_sqft_year'].apply('${:,.1f}'.format)

        # Monthly Revenue / Unit / Month
        df_raw['EstRevenueMonthly'] = (df_raw['Preceding_Fiscal_Year_Revenue']/df_raw['Size'])/12

        # Apply a function to calculate distance from the subject property to Lease Sample DataFrame
        df_raw['Distance'] = df_raw.apply(lambda x: calc_distance(prop_loc, x['Lat'], x['Long']), axis=1)

        # Apply distance filter (In miles)
        df_raw_dist = df_raw[df_raw['Distance'] <= radius_cmbs/1609]

        # Fill NAs
        df_raw_dist.fillna(0, inplace=True)
        df_raw_dist.replace('nan', 0, inplace=True)

        # To numeric
        df_raw_dist['Size'] = pd.to_numeric(df_raw_dist['Size'], errors="coerce")
        df_raw_dist['Size'] = df_raw_dist['Size'].astype(int)

        # Only apply size filter if there are > 10 comps
        if df_raw_dist.shape[0] > 10:
            dfr = df_raw_dist[(df_raw_dist['Size'] >= lower_bound) & (df_raw_dist['Size'] <= upper_bound)]
        else:
            dfr = df_raw_dist

        dfr.sort_values(by='Size', ascending=False, inplace=True)

    '''
    Non-CMBS data
    '''

    # Get the state to be passed into the query
    if geocode_result:

        for d in geocode_result[0]['address_components']:

            for k, v in d.items():

                if 'administrative_area_level_1' in d['types']:

                    if k == 'short_name':

                        state = v.lower()

                        # Search radius - miles to meters
                        radius_noncmbs = 1.5*1609

                        # Attempt to expand radius 3x
                        for i in range(3):

                            # Run query
                            query = '''

                                    SELECT ds.*, dzr.bed_rooms, AVG(dzr.price) as avg_rent
                                    FROM stroom_main.df_zillow_{} ds
                                    JOIN stroom_main.df_zillow_rent dzr
                                        ON ds.id = dzr.id
                                    GROUP BY ds.id, dzr.bed_rooms
                                    HAVING ds.geomatch = 'no match'
                                    AND st_distance_sphere(Point({},{}), ds.coords) <= {}
                                    AND dzr.bed_rooms <= 4
                                    AND avg_rent <= 10000;

                                    '''.format(state, Long, Lat, radius_noncmbs)

                            df_comps = pd.read_sql(query, con)

                            # If no comps result, expand radius
                            if df_comps.shape[0] == 0:
                                radius_noncmbs = radius_noncmbs * 2
                            else:
                                break


    if df_comps.shape[0] > 0:

        # Apply a function to calculate distance from the subject property to Lease Sample DataFrame
        df_comps['Distance'] = df_comps.apply(lambda x: calc_distance(prop_loc, x['Lat'], x['Long']), axis=1)

        # Apply distance filter (In miles)
        df_comps_dist = df_comps[df_comps['Distance'] <= radius_noncmbs/1609]

        # Fill NAs
        df_comps_dist.fillna(0, inplace=True)
        df_comps_dist.replace('nan', 0, inplace=True)

        # To numeric
        df_comps_dist['unit_count'] = pd.to_numeric(df_comps_dist['unit_count'], errors="coerce")
        df_comps_dist['unit_count'] = df_comps_dist['unit_count'].astype(int)

        # Only apply size filter if there are > 10 comps
        if df_comps_dist.shape[0] > 10:
            dfc = df_comps_dist[(df_comps_dist['unit_count'] >= lower_bound) & (df_comps_dist['unit_count'] <= upper_bound)]
        else:
            dfc = df_comps_dist

        dfc.sort_values(by='unit_count', ascending=False, inplace=True)

    if radius_noncmbs >= radius_cmbs:
        radius = radius_noncmbs
    else:
        radius = radius_cmbs

    return {'y_pred': res, 'df_cmbs': dfr.head(20), 'df_noncmbs': dfc.head(20), 'radius': radius}
