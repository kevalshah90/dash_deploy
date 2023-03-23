import os

env_var_dict = {
                'MAPBOX_KEY':'pk.eyJ1Ijoic3Ryb29tIiwiYSI6ImNsNWVnMmpueTEwejQza252ZnN4Zm02bG4ifQ.SMGyKFikz4uDDqN6JvEq7Q',
                'gkey':'AIzaSyC0XCzdNwzI26ad9XXgwFRn2s7HrCWnCOk',
                'GCLOUD_PROJECT':'stroom-data-exploration',
                'walk_api_key':'5ddeb512e4ac8046b46eca65a39ff9c5',
                'ckey':'71a69d38e3f63242eca7e63b8de1019b6e9f5912',

                # db
                'user':'stroom',
                'pwd':'$sSnbFaqViFG9RAbo:2g8uEV7HXU',
                'host':'aa1jp4wsh8skxvw.csl5a9cjrheo.us-west-1.rds.amazonaws.com',
                'port':'3306',

                # aws
                'aws_access_key_id':'AKIA2MQCGH6RW7TE3UG2',
                'aws_secret_access_key':'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',

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
# ckey = "71a69d38e3f63242eca7e63b8de1019b6e9f5912"
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
