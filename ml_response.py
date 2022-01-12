import pandas as pd
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, MinMaxScaler, OrdinalEncoder
import os
from funcs import clean_percent, clean_currency
from sagemaker.serializers import CSVSerializer

# AWS SageMaker
import boto3
import pickle
import sagemaker
from sagemaker.amazon.amazon_estimator import get_image_uri
from time import gmtime, strftime
from sagemaker.xgboost import XGBoost, XGBoostModel
from sagemaker.session import Session
from sagemaker.local import LocalSession


# read data
df_lease = pd.read_csv(os.getcwd() + "/data/LeaseComp_sf_la_mf_agg_v12_ml.csv")

# drop column
df_lease.drop(df_lease.filter(regex="Unname"),axis=1, inplace=True)

# subset cols
df = df_lease[['Year Built',
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
df['Most Recent Physical Occupancy'] = df['Most Recent Physical Occupancy'].apply(clean_percent).astype('float')

# split df into train and test
X_train, X_test, y_train, y_test = train_test_split(df.iloc[:,0:21], df.iloc[:,-1], test_size=0.1, random_state=42)

# Encode categorical variables
cat_vars = ['geohash','Loan Status','Ownership','AirCon','Pool','Condition','constructionType','parkingType']
cat_transform = ColumnTransformer([('cat', OneHotEncoder(handle_unknown='ignore'), cat_vars)], remainder='passthrough')

# Create encoder object
encoder = cat_transform.fit(X_train)


# Create a test data point and save to csv - the input format for SageMaker Endpoint
df = pd.DataFrame({

                           'Year Built': 2010,
                           'Size': 200,
                           'Most Recent Physical Occupancy': 85,
                           'Preceding Fiscal Year Revenue': 1000000,
                           'Most Recent Operating Expenses': 25000,
                           'WalkScore': 60,
                           'TransitScore': 55,
                           'geohash': np.random.choice(df['geohash'], 1)[0],
                           'EstRentableArea': 50000,
                           'Loan Status': 'Paid in full',
                           'EstValue': 12000000,
                           'CapRate': 0.1,
                           'Ownership': np.random.choice(df['Ownership'], 1)[0],
                           'AirCon': np.random.choice(df['AirCon'], 1)[0],
                           'Pool': np.random.choice(df['Pool'], 1)[0],
                           'Condition': np.random.choice(df['Condition'], 1)[0],
                           'constructionType': np.random.choice(df['constructionType'], 1)[0],
                           'parkingType': np.random.choice(df['parkingType'], 1)[0],
                           'parkingSpaces': 10,
                           'numberOfBuildings': 2,
                           'taxRate': 0.05312

                    }, index=[0])


'''
AWS sagemaker endpoint invocation
'''

region = boto3.Session().region_name

role = 'arn:aws:iam::714042916771:role/stroom-sagemaker-role'

bucket = 'ml-model-stroom'
prefix = "sagemaker/stroom-xgboost-byo"
bucket_path = "https://s3-{}.amazonaws.com/{}".format('us-west-1', 'ml-model-stroom')

client = boto3.client(
    's3',
    aws_access_key_id='AKIA2MQCGH6RW7TE3UG2',
    aws_secret_access_key='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'
)


sm_client = boto3.client(
                         "sagemaker",
                         region_name="us-west-1",
                         aws_access_key_id='AKIA2MQCGH6RW7TE3UG2',
                         aws_secret_access_key='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'
                        )


# Define session
sagemaker_session = Session(sagemaker_client = sm_client)


xgb_inference_model = XGBoostModel(
                                   model_data=model_uri,
                                   role=role,
                                   entry_point="inference.py",
                                   framework_version="0.90-2",
                                   # Cloud
                                   sagemaker_session = sagemaker_session
                                   # Local
                                   # sagemaker_session = None
)


# Creates model, endpoint config and endpoint.
predictor = xgb_inference_model.deploy(
                                       initial_instance_count = 1,
                                       # Cloud
                                       instance_type="ml.t2.large",
                                       # Local
                                       # instance_type = "local",
                                       serializer = "text/csv"
)


predictor.serializer = CSVSerializer()

# Encode to handle categorical variables
testpoint = encoder.transform(df).toarray().tolist()

# to csv as fn_input accepts text/csv data type
np.savetxt("test_point.csv", testpoint, delimiter=",", fmt='%s')

file_name = ("test_point.csv")

with open(file_name, "r") as f:
    payload = f.read().strip()

payload = ', '.join(map(str, testpoint[0]))

# Predict method
output = predictor.predict(payload)

# response
res = float(output[0][0])
