
import geocoder
import pandas as pd
pd.options.display.float_format = '{:.8f}'.format
import os
import google_streetview.api
import random
import string
import usaddress
import geopandas as gpd
import pygeohash as gh
from geolib import geohash
import pygeodesy as pgd

import http.client
import urllib.parse

# mapbox
MAPBOX_KEY="pk.eyJ1Ijoia2V2YWxzaGFoIiwiYSI6ImNqbW1nbG90MDBhNTQza3IwM3pvd2I3bGUifQ.dzdTsg69SdUXY4zE9s2VGg"
token = MAPBOX_KEY

# google maps api key
import googlemaps
gmaps = googlemaps.Client(key="AIzaSyC0XCzdNwzI26ad9XXgwFRn2s7HrCWnCOk")
gkey = 'AIzaSyC0XCzdNwzI26ad9XXgwFRn2s7HrCWnCOk'

# walkscore
from walkscore import WalkScoreAPI
api_key = '5ddeb512e4ac8046b46eca65a39ff9c5'
walkscore_api = WalkScoreAPI(api_key = api_key)

# aws
import logging
import boto3
from botocore.exceptions import ClientError
bucket = 'gmaps-images-6771'

s3_client = boto3.client('s3',
                         aws_access_key_id='AKIA2MQCGH6RW7TE3UG2',
                         aws_secret_access_key='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')



# Read SF Multi-Family data
LeaseComp_sf_la_mf = pd.read_csv(os.getcwd() + "/data/LeaseComp_sf_la_mf_agg_v11_raw.csv")

# Generate alphanumeric lease id and property ids
def gen_ids(length):

    ids = ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    return ids

# Walkscore API Function
def walkscore(lat, long, address, scores):

    try:

        result = walkscore_api.get_score(latitude = lat, longitude = long, address = address)

        # WalkScore for location
        if scores == 'walk':

            ws = result.walk_score
            return ws

        # TransitScore for location
        if scores == 'transit':

            ts = result.transit_score
            return ts

    except Exception as e:
        print(e)
        pass

# Clean currency
def clean_currency(x):
    """ If the value is a string, then remove currency symbol and delimiters
    otherwise, the value is numeric and can be converted
    """
    if isinstance(x, str):
        return(x.replace('$', '').replace(',', ''))
    return(x)

# Clean percentage
def clean_percent(x):
    """ If the value is a string, then remove percent symbol and delimiters
    otherwise, the value is numeric and can be converted
    """
    if isinstance(x, str):
        return(x.replace('%', ''))
    return(x)

# String to floats
def str_num(x):

    if isinstance(x, str):
        return(x.replace(',', ''))
    return(int(x))

# Get Lat, Long
def get_geocodes(address):

    try:

        g = geocoder.mapbox(address, key=token)
        geojson = g.json

        coords = [geojson['lat'], geojson['lng']]

        Lat = coords[0]

        Long = coords[1]

        return (Lat, Long)

    except Exception as e:
        print("Exception", e)

        # API Call
        result = gmaps.geocode(address)

        lat = result[0]['geometry']['location']['lat']

        lng = result[0]['geometry']['location']['lng']

        return (lat, lng)


def city_geohash(geo):

    # Create a dict geohash and city
    city_geohash = dict()

    for name, group in LeaseComp_sf_la_mf.groupby(['geohash']):

        city_geohash[name] = set(group['City'])

    city = list(city_geohash[geo])[0]

    return city


# Get nearby place information
def nearby_places(addr):

    # API call to get place ID
    result = gmaps.find_place(addr, input_type = "textquery", language="en")
    plc_id = result['candidates'][0]['place_id']

    # API to get place details
    plc_details = gmaps.place(plc_id, fields=["formatted_address", "name", "geometry", "photo", "url", "type", "utc_offset", "vicinity"])
    result = plc_details['result']

    # Get nearby places from place location - radius in meters
    nearby = gmaps.places_nearby(location=result['geometry']['location'], radius = 4829)

    # Declare a list to store dicts of nearby places
    places_lst = []

    for i in range(len(nearby['results'])):

        # Filter to include only POIs
        types = ['supermarket','hospital','movie_theater','bar','restaurant','post_office','university','library','airport','bank','light_rail_station','primary_school','secondary_school','school','shopping_mall','train_station','transit_station','gym','pharmacy','pet_store','museum']

        for typ in types:

            if typ in nearby['results'][i]['types']:

                # Filter to include businesses currently operational
                if nearby['results'][i].get('business_status') == 'OPERATIONAL':

                    # Filter dict to only contain geometry, name, types
                    fdict = dict((k,v) for k, v in nearby['results'][i].items() if k in ['geometry','name','types'])
                    places_lst.append(fdict)

    # check if list was populated with nearby places
    if len(places_lst) > 0:

        # List of dicts into DataFrame
        df_nearby = pd.DataFrame(places_lst)

        # Format columns
        df_nearby['Lat'] = df_nearby['geometry'].str['location'].str['lat']
        df_nearby['Lng'] = df_nearby['geometry'].str['location'].str['lng']
        df_nearby['type_label'] = df_nearby['types'].str[0]

        # Check for None places list
        if isinstance(df_nearby, pd.DataFrame):

            return df_nearby

    else:

        return None

# Google Streetview image
def streetview(lat, long, identifier):

    try:

        # Define parameters for street view api
        params = [{
                   'size': '600x300', # max 640x640 pixels
                   'location': '{},{}'.format(lat,long),
                   'heading': '151.78',
                   'pitch': '-0.76',
                   'key': gkey
        }]

        # Create a results object
        results = google_streetview.api.results(params,
                                                site_api='https://maps.googleapis.com/maps/api/streetview',
                                                site_metadata='https://maps.googleapis.com/maps/api/streetview/metadata')

        # Download images to directory 'downloads'
        results.download_links('photos')

        directory = os.getcwd() + "/photos/"

        old_name = os.path.join(directory, results.metadata[0]['_file'])
        new_name = os.path.join(directory, "{}_image.png".format(identifier))

        os.rename(old_name, new_name)

        # Add code to upload to S3 and access object using presigned urls
        s3_client.upload_file(os.getcwd() + '/photos/{}_image.png'.format(identifier), bucket, 'property_images/{}_image.png'.format(identifier))

        return "{}_image.png".format(identifier)

    except Exception as e:
            print("Exception", e)
            pass


# AWS Pre-signed URLs
def create_presigned_url(bucket_name, object_name, expiration=3600):
    """Generate a presigned URL to share an S3 object

    :param bucket_name: string
    :param object_name: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """

    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_name},
                                                    ExpiresIn=expiration)

    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL
    return response

# Convert list to dict for JSON serialization
def listToDict(lst):
    if lst:
        detailsDict = { i : lst[i] for i in range(0, len(lst) ) }
        return detailsDict
    else:
        return None


# ATTOM API - propety details
def attom_api_avalue(addr1, addr2):

    conn = http.client.HTTPSConnection("api.gateway.attomdata.com")

    headers = {
        'accept': "application/json",
        'apikey': "98b25d7c38aeb771184dd885b92b5cb5",
        }

    addr1 = urllib.parse.quote(addr1)
    addr2 = urllib.parse.quote(addr2)

    url = "/propertyapi/v1.0.0/assessment/detail?address1={}&address2={}".format(addr1, addr2)

    conn.request("GET", url, headers=headers)

    res = conn.getresponse()
    res = res.read()

    return res

# Geohash Proximity / nearest neighbor search
def approximate_distance(geohash1, geohash2):
    return pgd.geohash.distance_(geohash1, geohash2)

def prox_mean(df, x, n=3):

    #set number of closest geohashes to use for approximation with n
    val = df.loc[df['geohash'] == x]

    if not val.empty:
        return val['value'].iloc[0]
    else:
        df['tmp_dist'] = df['geohash'].apply(lambda y: approximate_distance(y,x))
        return df.nlargest(n, 'tmp_dist')['value'].mean()