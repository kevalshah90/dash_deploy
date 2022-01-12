#Quandl api for 10YR Treasury yield (Min cap rate)
import quandl
quandl.ApiConfig.api_key = "t2bwFsYVn_sUymS1Degq"

from datetime import date
from decimal import Decimal
import re
from re import sub


# Dictionary with spread values
asset_type = {'Office': 0.75, 'Retail': 0.5, 'Industrial': 0.25, 'Flex': 0.5}
tenant_credit = {'Excellent': 1, 'Good': 1.5, 'Fair': 2, 'Poor': 2.5}
ofc_loc = {'CBD':0.5, 'Suburban': 1}
ret_loc = {'Neighborhood': 1.25, 'High Street': 0.75, 'Power Center': 0.5}
condition = {'Excellent': 1, 'Good': 1.5, 'Fair': 2, 'Poor': 2.5}
propclass = {'A': 1, 'B': 1.5, 'C': 2}


# Function to calculate cap rates
def calc_caprate(asset, tenant_cr, loc, cond, monthly_rent, vacancy_loss):

    at = asset_type[asset]

    ten = tenant_credit[tenant_cr]

    cond = condition[cond]

    # Risk Free 10 Year Treasury rate
    df = quandl.get("USTREASURY/YIELD", start_date="2020-01-01", end_date=date.today())
    data10yr = df[['10 YR']]
    tr = data10yr['10 YR'].iloc[-1]

    cap = tr + at + ten + cond

    # Calculate Asset Value
    noi = monthly_rent * 12

    # Make Final Adjustments to NOI - Debt, Vacancy Loss, Cash Reserves
    noi = noi - (int(1906807) + int(vacancy_loss))

    val = int(noi/cap)*100

    return {'cap_rate': cap, 'cap_value': val}

# Calculate Discount Rate
def calc_discrate(asset, loc, aclass):

    # Risk Free 10 Year Treasury rate
    df = quandl.get("USTREASURY/YIELD", start_date="2020-01-01", end_date=date.today())
    data10yr = df[['10 YR']]
    tr = data10yr['10 YR'].iloc[-1]

    at = asset_type[asset]

    loc = ofc_loc[loc]

    aclass = propclass[aclass]

    disc = tr + at + loc + aclass

    return {'disc_rate': disc}
