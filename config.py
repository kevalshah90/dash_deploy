import os

env_var_dict = {
                'MAPBOX_KEY':'xxx',
                'gkey':'xxx',
                'GCLOUD_PROJECT':'stroom-data-exploration',
                'walk_api_key':'xxx',
                'ckey':'xxx',

                # db
                'user':'stroom',
                'pwd':'xxx',
                'host':'aa1jp4wsh8skxvw.csl5a9cjrheo.us-west-1.rds.amazonaws.com',
                'port':'3306',

                # aws
                'aws_access_key_id':'xxx',
                'aws_secret_access_key':'xxx',

                # flask
                'flask-port-docker': 5000,
                'flask-port-host': 8000
               }


# google maps api key
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="stroom-data-exploration-ebf3ef8e9bf0.json"

import googlemaps
gmaps = googlemaps.Client(key = env_var_dict['gkey'])

from google.cloud import bigquery
import pyarrow
client = bigquery.Client(project = env_var_dict['GCLOUD_PROJECT'])
os.environ.setdefault("GCLOUD_PROJECT", env_var_dict['GCLOUD_PROJECT'])

# walkscore API
from walkscore import WalkScoreAPI
walkscore_api = WalkScoreAPI(api_key = env_var_dict['walk_api_key'])


# US Census libraries and API key
# import censusgeocode as cg
# from census import Census
# from us import states
# ckey = "xxx"
# c = Census(ckey)

os.environ["MAPBOX_KEY"] = env_var_dict['MAPBOX_KEY']
os.environ["gkey"] = env_var_dict['gkey']
os.environ["GCLOUD_PROJECT"] = env_var_dict["GCLOUD_PROJECT"]
os.environ["walk_api_key"] = env_var_dict["walk_api_key"]
os.environ["ckey"] = env_var_dict["ckey"]

os.environ["aws_access_key_id"] = env_var_dict["aws_access_key_id"]
os.environ["aws_secret_access_key"] = env_var_dict["aws_secret_access_key"]

os.environ["user"] = env_var_dict["user"]
os.environ["pwd"] = env_var_dict["pwd"]
os.environ["host"] = env_var_dict["host"]
os.environ["port"] = env_var_dict["port"]
