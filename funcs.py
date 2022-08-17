
import geocoder
import pandas as pd
pd.options.display.float_format = '{:.8f}'.format
import numpy as np
import os
import google_streetview.api
import random
import string
import usaddress
import geopandas as gpd
import pygeohash as gh
from geolib import geohash
import pygeodesy as pgd
import shapely
from shapely.wkt import loads
import http.client
import urllib.parse

# mapbox
MAPBOX_KEY="pk.eyJ1Ijoic3Ryb29tIiwiYSI6ImNsNWVnMmpueTEwejQza252ZnN4Zm02bG4ifQ.SMGyKFikz4uDDqN6JvEq7Q"
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
LeaseComp_sf_la_mf = pd.read_csv(os.getcwd() + "/data/df_raw_v1_feb.csv")

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
        print("Error with WalkScore API", e)
        pass

# Clean currency
def clean_currency(x):
    """
    If the value is a string, then remove currency symbol and delimiters
    otherwise, the value is numeric and can be converted
    """
    if isinstance(x, str):
        return(x.replace('$', '').replace(',', ''))
    return(x)

# Clean percentage
def clean_percent(x):
    """
    If the value is a string, then remove percent symbol and delimiters
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

    # US bbox
    bbox = [-171.791110603, 18.91619, -66.96466, 71.3577635769]

    try:

        g = geocoder.mapbox(address, key=token)
        geojson = g.json

        coords = [geojson['lat'], geojson['lng']]

        Lat = coords[0]
        Long = coords[1]

        return (Lat, Long)

    except Exception as e:
        print("Exception", e)

        #bbox = {'northeast': {'lat': 18.91619, 'lng': -171.791110603}, 'southwest': {'lat': 71.3577635769, 'lng': -66.96466}}

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

# Dictionary for marker symbol
sym_dict = {"Office": "suitcase",
            "Multi-Family": "lodging",
            "Industrial": "circle",
            "grocery_or_supermarket": "grocery",
            "supermarket": "grocery",
            "department_store": "grocery",
            "convenience_store": "grocery",
            "hospital": "hospital",
            "car_rental": "car",
            "gas_station": "fuel",
            "movie_theater": "cinema",
            "bar": "bar",
            "restaurant": "restaurant",
            "cafe": "cafe",
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
            "subway_station": "rail-metro",
            "bus_station": "bus",
            "gym": "swimming",
            "pharmacy": "pharmacy",
            "drugstore": "pharmacy",
            "pet_store": "dog-park",
            "museum": "museum",
            "church": "place-of-worship",
            "synagogue": "place-of-worship",
            "hindu_temple": "place-of-worship",
            "mosque": "place-of-worship" }

# Get nearby place information
def nearby_places(addr, type):

    # API call to get place ID
    result = gmaps.find_place(addr, input_type = "textquery", language="en")

    plc_id = result['candidates'][0]['place_id']

    # API to get place details
    plc_details = gmaps.place(plc_id, fields=["formatted_address", "name", "geometry", "photo", "url", "type", "utc_offset", "vicinity"])
    result = plc_details['result']

    # Set place types
    if type == 'Transit':
        types = ['light_rail_station','train_station','transit_station','subway_station']

    elif type == 'Grocery':
        types = ['supermarket','grocery_or_supermarket','department_store','convenience_store']

    elif type == 'School':
        types = ['primary_school','secondary_school','school']

    elif type == 'Hospital':
        types = ['hospital','pharmacy','drugstore']

    elif type == 'Food/Cafe':
        types = ['bar','restaurant','cafe']

    elif type == 'Worship':
        types = ['church','synagogue','hindu_temple','mosque']

    elif type == 'Gas':
        types = ['gas_station']

    elif type == None:
        types = ['supermarket','grocery_or_supermarket','department_store','convenience_store','hospital','movie_theater','bar','restaurant','post_office','university','library','airport','bank','light_rail_station','primary_school','secondary_school','school','shopping_mall','train_station','transit_station','subway_station','bus_station','gym','pharmacy','drugstore','pet_store','museum','church','synagogue','hindu_temple','mosque']

    else:
        types = ['supermarket','grocery_or_supermarket','department_store','convenience_store','hospital','movie_theater','bar','restaurant','post_office','university','library','airport','bank','light_rail_station','primary_school','secondary_school','school','shopping_mall','train_station','transit_station','subway_station','bus_station','gym','pharmacy','drugstore','pet_store','museum','church','synagogue','hindu_temple','mosque']

    # Declare a list to store dicts of nearby places
    places_lst = []

    if type in ['Transit','Grocery','School','Hospital','Worship','Food/Cafe','Gas']:

        # Get nearby places from place location - radius in meters
        nearby = gmaps.places_nearby(location=result['geometry']['location'], radius = 8046, type = types)

        if nearby:

            print(nearby)

            for i in range(len(nearby['results'])):

                # Filter to include businesses currently operational
                if nearby['results'][i].get('business_status') == 'OPERATIONAL':

                    # Filter dict to only contain geometry, name, types
                    fdict = dict((k,v) for k, v in nearby['results'][i].items() if k in ['geometry','name','types','rating'])
                    places_lst.append(fdict)

    else:

        nearby = gmaps.places_nearby(location=result['geometry']['location'], radius = 4829)

        for i in range(len(nearby['results'])):

            for typ in types:

                if typ in nearby['results'][i]['types']:

                    if nearby['results'][i].get('business_status') == 'OPERATIONAL':

                       # Filter dict to only contain geometry, name, types
                       fdict = dict((k,v) for k, v in nearby['results'][i].items() if k in ['geometry','name','types','rating'])
                       places_lst.append(fdict)

    # check if list was populated with nearby places
    if len(places_lst) > 0:

        # List of dicts into DataFrame
        df_nearby = pd.DataFrame(places_lst)

        # Drop duplicates
        df_nearby.drop_duplicates(subset=['name'], keep='first', inplace=True)

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

# Check valid geometries
# def valid_geom(geom):
#     try:
#         return loads(geom)
#     except:
#         return np.nan

# Fix Bad Geometries
# def valid_geom(geom):
#     try:
#         return wkt.dumps(geom)
#     except:
#         return np.nan

# Find Invalid Geos
def valid_geoms(x):
    try:
        return shapely.wkt.loads(x)
    except:
        return np.nan


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
def attom_api_avalue(address):

    conn = http.client.HTTPSConnection("api.gateway.attomdata.com")

    headers = {
        'accept': "application/json",
        'apikey': "407cbd2300b77764311ed005c9d94376",
        }

    addr = urllib.parse.quote(address)

    url = "/propertyapi/v1.0.0/assessment/detail?address={}".format(addr)

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
