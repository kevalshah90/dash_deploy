import numpy as np
import pandas as pd
import seaborn as sns
import scipy as stats
import sklearn
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

# Read SF Multi-Family data
LeaseComp_sf_la_mf = pd.read_csv(os.getcwd() + "/data/LeaseComp_sf_la_mf_agg_v11_raw.csv")

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

# Read ML data
df_lease = pd.read_csv(os.getcwd() + "/data/LeaseComp_sf_la_mf_agg_v12_ml.csv")

# Drop column
df_lease.drop(df_lease.filter(regex="Unname"),axis=1, inplace=True)

# Subset cols
df_sub = df_lease[['Year Built',
                   'Size',
                   'Most Recent Physical Occupancy',
                   'Preceding Fiscal Year Revenue',
                   'Most Recent Operating Expenses',
                   'WalkScore',
                   'TransitScore',
                   'geohash',
                   'EstRentableArea',
                   'Loan Status',
                   'EstValue',
                   'CapRate',
                   'Ownership',
                   'AirCon',
                   'Pool',
                   'Condition',
                   'constructionType',
                   'parkingType',
                   'parkingSpaces',
                   'numberOfBuildings',
                   'taxRate',
                   'Revenue_per_sqft_month']]


# Convert percentage to numeric
df_sub['Most Recent Physical Occupancy'] = df_sub['Most Recent Physical Occupancy'].apply(clean_percent).astype('float')
# Currency to numeric
df_sub['Most Recent Operating Expenses'] = df_sub['Most Recent Operating Expenses'].apply(clean_currency).astype('float')

# split df into train and test
X_train, X_test, y_train, y_test = train_test_split(df_sub.iloc[:,0:21], df_sub.iloc[:,-1], test_size=0.1, random_state=42)

# Encode categorical variables
cat_vars = ['geohash','Loan Status','Ownership','AirCon','Pool','Condition','constructionType','parkingType']
cat_transform = ColumnTransformer([('cat', OneHotEncoder(handle_unknown='ignore'), cat_vars)], remainder='passthrough')

# Create encoder object
encoder = cat_transform.fit(X_train)

# Append row to LeaseSample Pandas DataFrame
def append_prop(tenant, industry, address, city, zipcode, state, proptype, leasetype, propclass, floor, built, renovated, startdt, enddt, sqft, rentask, rentner, rentesc, free, ti, lf, opex):

    global LeaseComp_sf_la_mf

    # Get Lat, Long coordinates
    if address and city and state and zipcode:

        address_str = address + "," + city + "," + state + " " + zipcode

        loc = gmaps.geocode(address_str)
        lat = loc[0]['geometry']['location']['lat']
        lng = loc[0]['geometry']['location']['lng']

        # Get Walk and Transit scores
        Walk = walkscore(lat, lng, address_str, 'walk')
        Transit = walkscore(lat, lng, address_str, 'transit')

        vlist = [gen_ids(12), gen_ids(10), industry, tenant, sqft, renovated, floor, proptype, propclass, built, startdt, leasetype, enddt, city, rentner, lat, lng, address_str, zipcode, Walk, Transit]
        cols = ['LeaseID', 'PropertyID', 'Tenant Industry', 'Tenant', 'Square Footage', 'Year Renovated', 'Building Floor', 'Property Type', 'Building Class', 'Year Built', 'Commencement Date', 'Lease Type', 'Expiration Date', 'City', 'Rent', 'Lat', 'Long', 'Address', 'zipcode', 'WalkScore', 'TransitScore']

        # Using zip() to convert lists to dictionary
        res = dict(zip(cols, vlist))

        # Create pandas DataFrame for new row addition
        LeaseComp_sf_la_mf = LeaseComp_sf_la_mf.append(res, ignore_index=True)

# Calculate distance between properties
# Define radius and find similar leases executed recently within the proximity.
def calc_distance(prop_loc, Lat, Long, prop_id):

    prop_locs = (Lat, Long)

    dist = geopy.distance.distance(prop_loc, prop_locs).miles

    return (dist, prop_id)


# Function to calculate optimal rent.
def calc_rent(prop_address, proptype, yr_built, space, units, ameneties, occupancy, taxRate, geohash):

    np.random.seed(0)

    # Geocoding an address <-- Address of the subject property.
    geocode_result = gmaps.geocode(prop_address)

    Lat = geocode_result[0]['geometry']['location']['lat']
    Long = geocode_result[0]['geometry']['location']['lng']

    prop_loc = (Lat, Long)

    # Location characteristics
    Walk = walkscore(Lat, Long, prop_address, 'walk')
    Transit = walkscore(Lat, Long, prop_address, 'transit')


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

    # In order to impute the missing data, we need to filter the df by city / location of the subject property, so that are estimates are representative of the market.
    geo = gh.encode(Lat, Long, 5)

    # Lookup city
    city = city_geohash(geo)

    df_sub = LeaseComp_sf_la_mf[LeaseComp_sf_la_mf['City'] == city]

    # Convert percentage to numeric
    df_sub['Most Recent Physical Occupancy'] = df_sub['Most Recent Physical Occupancy'].apply(clean_percent).astype('float')
    # Currency to numeric
    df_sub['Most Recent Operating Expenses'] = df_sub['Most Recent Operating Expenses'].apply(clean_currency).astype('float')

    # Create a test data point and save to csv - the input format for SageMaker Endpoint
    df = pd.DataFrame({

                               'Year Built': int(yr_built),
                               'Size': int(units),
                               'Most Recent Physical Occupancy': occupancy,
                               'Preceding Fiscal Year Revenue': df_sub['Preceding Fiscal Year Revenue'].quantile(0.25),
                               'Most Recent Operating Expenses': df_sub['Most Recent Operating Expenses'].quantile(0.25),
                               'WalkScore': Walk,
                               'TransitScore': Transit,
                               'geohash': geohash,
                               'EstRentableArea': df_sub['EstRentableArea'].median(),
                               'Loan Status': df_sub['Loan Status'].mode(),
                               'EstValue': df_sub['EstValue'].median(),
                               'CapRate': df_sub['CapRate'].median(),
                               'Ownership': np.random.choice(df_sub['Ownership'], 1)[0],
                               'AirCon': np.random.choice(df_sub['AirCon'], 1)[0],
                               'Pool': np.random.choice(df_sub['Pool'], 1)[0],
                               'Condition': np.random.choice(df_sub['Condition'], 1)[0],
                               'constructionType': np.random.choice(df_sub['constructionType'], 1)[0],
                               'parkingType': np.random.choice(df_sub['parkingType'], 1)[0],
                               'parkingSpaces': df_sub['parkingSpaces'].median(),
                               'numberOfBuildings': df_sub['numberOfBuildings'].median(),
                               'taxRate': taxRate

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
    endpoint_name = "sagemaker-xgboost-2021-12-11-23-17-37-092"

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
    Cosine similarity code
    '''

    # Create a dataframe of subject property from comps tab -- (Ideally this will be pulled in through Reonomy API)
    df = pd.DataFrame({
                       'Area': int(space),
                       'Year Built': int(yr_built),
                       'Most Recent Physical Occupancy': occupancy,
                       'WalkScore': Walk,
                       'taxRate': taxRate,
                       #'ameneties': ameneties
                     }, index=[1])

    ### COSINE SIMILARITY CALCULATIONS

    # Apply a function to calculate distance from the subject property to Lease Sample DataFrame
    dist = LeaseComp_sf_la_mf.apply(lambda x: calc_distance(prop_loc, x['Lat'], x['Long'], x['PropertyID']), axis=1)

    # Convert tuple to dictionary - property id = key and Lat / Long = value
    dist_dict = dict((y, x) for x, y in dist)

    # Set radius based on geo filter
    radius = 1.5 # Default

    # Filter by properties located within x mile radius
    dist_dict_filter = {key: value for key, value in dist_dict.items() if value <= radius}

    # If no properties are within default geofilter radius, then 2x / expand the radius
    if bool(dist_dict_filter) == False:
        # update value of radius for drawing circle
        radius = 2*radius

        dist_dict_filter = {key: value for key, value in dist_dict.items() if value <= radius}

    # Sample dataframe to include only property ids
    LeaseSamplev2 = LeaseComp_sf_la_mf[LeaseComp_sf_la_mf['PropertyID'].isin(list(dist_dict_filter.keys()))]

    # Subset Features to be compared for similarity
    cols = ['PropertyID','EstRentableArea','Year Built','Most Recent Physical Occupancy','WalkScore','taxRate']
    dfComp = LeaseSamplev2[[c for c in LeaseSamplev2.columns if c in cols]]

    # Clean up
    dfComp['Most Recent Physical Occupancy'] = dfComp['Most Recent Physical Occupancy'].apply(clean_percent).astype('float')

    # Making up ameneties data for comparables
    #dfComp['ameneties'] = ameneties

    dfComp = dfComp.reset_index()

    # Calculate cosine similarity - all rows, 5 columns - - drop PropertyID
    dfCompv1 = dfComp.iloc[:,2:7]

    df.fillna(0, inplace=True)
    dfCompv1.fillna(0, inplace=True)

    # Apply cosine similarity - df = subject property and dfCompv1 = comparables
    cos_arr = cosine_similarity(df.values, dfCompv1.values)

    # Store cosine similarity scores in an array
    cos_lst = []

    for i in cos_arr[0]:
        cos_lst.append(i)

    # Create dataframe with propertyID and Similarity measure.
    dfSimilarity = pd.DataFrame({
                                 'PropertyID': dfComp['PropertyID'],
                                 'Cos_sim': cos_lst
                               })

    # Scale cosine similarity measure
    scaler = MinMaxScaler(feature_range=(0.1,100))

    # Calculate Rent based on Square foot area * Revenue Per Square Feet
    LeaseSamplev2['Revenue_per_sqft_month'].replace([np.inf, -np.inf], np.nan, inplace=True)
    LeaseSamplev2 = LeaseSamplev2[LeaseSamplev2['Revenue_per_sqft_month'].notna()]

    if flow_type == "Leasing":
        LeaseSamplev2['Estimated_Rent'] = (LeaseSamplev2['Revenue_per_sqft_month'] * int(space)).astype(int)
    else:
        LeaseSamplev2['Estimated_Rent'] = (LeaseSamplev2['Revenue_per_sqft_month']*12).astype(int)

    # Add distance from subject property column
    LeaseSamplev2['Distance'] = LeaseSamplev2['PropertyID'].map(dist_dict_filter)

    # Use similarity measures as weights
    dfSimilarity['Weights'] = scaler.fit_transform(dfSimilarity[['Cos_sim']])

    # All properties in Comp set
    dfCompSet = pd.merge(dfSimilarity, LeaseSamplev2, how='inner', left_on='PropertyID', right_on='PropertyID')

    # Drop duplications
    dfCompSet.drop_duplicates(subset=['Property Name','Zip Code'], keep='last', inplace=True)

    dfCompSetv1 = dfCompSet.sort_values(by=['Estimated_Rent'], ascending=False)

    # Calculate weighted average rental price
    dfSimilarityv1 = pd.merge(dfSimilarity, LeaseSamplev2[['PropertyID','Estimated_Rent','Opex']], how='inner', left_on='PropertyID', right_on='PropertyID')

    # Datatype consistency
    dfSimilarityv1['Weights'] = dfSimilarityv1['Weights'].astype(float)

    # Sort by similarity weight and sample top n rows -- This will likely elimimate the low income / affordable housing
    dfSimilarityv2 = dfSimilarityv1.sort_values(by=['Estimated_Rent'], ascending=False)

    # Top 10 similar properties
    dfSimilarityv2 = dfSimilarityv2.head(10)

    #  Use weights of top 10 similar properties
    calc_rent = round(np.average(dfSimilarityv2['Estimated_Rent'], weights = dfSimilarityv2['Weights']),2)

    return {'y_pred': res,  'price' : calc_rent, 'df_lease' : dfCompSetv1.head(15), 'radius': radius}
