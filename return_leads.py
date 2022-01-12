# Import Libraries
import numpy as np
import pandas as pd
import seaborn as sns
import scipy as stats
import matplotlib.pyplot as plt
import os
from datetime import date, datetime, timedelta
import random
from functools import partial
from pandas.io.json import json_normalize
import json
import ast
from difflib import SequenceMatcher
from sklearn.preprocessing import MinMaxScaler
import uuid
import string

# Load data
df_list = pd.read_csv('df_list.csv')
df_market = pd.read_csv('df_market.csv')

# Score matrix data
df_matrix = pd.read_csv('df_matrix.csv', index_col = 'comp')
df_matrix.drop(df_matrix.filter(regex="Unnamed"),axis=1, inplace=True)

#print(df_matrix)

# Set index as names column
#df_matrix = df_matrix.set_index('comp')

# Create dictionaries
prop_dict = dict(zip(df_list.id, df_list.Company))
city_dict = dict(zip(df_list.id, df_list.city))

# Define a function to lookup property ids
'''
Get a list of keys from dictionary which has the given value
'''

def getKeysByValue(dictOfElements, valueToFind):

    listOfKeys = list()
    listOfItems = dictOfElements.items()

    for item  in listOfItems:
        if item[1] == valueToFind:
            listOfKeys.append(item[0])
    return  listOfKeys


# Write a function that does the following -

# 1. Accepts Landlord/Owner string, market.
# 2. Looks up properties associated with the owner.
# 3. Select columns with the property ids
# 4. Calculate row-wise average score (across properties) and rank them
# 5. Return top 10 leads

def top_leads(landlord, market):

    # Load data
    #df_list = pd.read_csv('df_list.csv')
    #df_market = pd.read_csv('df_market.csv')

    # Score matrix data
    #df_matrix = pd.read_csv('df_matrix.csv')

    #print(df_matrix)

    # Create dictionaries
    prop_dict = dict(zip(df_list.id, df_list.Company))
    city_dict = dict(zip(df_list.id, df_list.city))

    # Lookup keys (property ids) from prop_dict
    propKeys = getKeysByValue(prop_dict, landlord)
    cityKeys = getKeysByValue(city_dict, market)

    prop_list = list(set(propKeys) & set(cityKeys))
    prop_list1 =[str(i) for i in prop_list]

    print(prop_list1)

    #df_temp = pd.DataFrame(df_matrix.values, columns=prop_list)

    df_temp = df_matrix.loc[:, prop_list1]

    print(df_temp)

    #Calculate Average score
    df_temp['mean'] = df_temp.mean(axis=1)

    # Return top n rows
    df_temp = df_temp.sort_values('mean',ascending = False).head(10)

    #print(df_temp)

    #df_temp = df_temp.loc[:,['mean']]
    #df_temp.index.name = 'comp'

    df_temp = df_temp.reset_index()

    df_temp['comp'] = df_temp['comp'].astype(str)
    df_market['Tenant'] = df_market['Tenant'].astype(str)

    res_leads = pd.merge(df_temp[['comp','mean']],
                         df_market[['Tenant_Industry','Tenant','num_employees','size_calc','Stage','New_Lease','New_Commencement']],
                         left_on = 'comp',
                         right_on = 'Tenant',
                         how='left')

    return res_leads
