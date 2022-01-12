# Import Libraries



# Function to calculate similarity score 

def matching_func(loc_t, loc_p, employees, size, days_lease_exp, ask_rent, budget):
    
    # Define dictionary with scoring weights
    
    weights = {
      "size": 6,
      "time": -3,      # Higher the days to expiration, less likely to lease. 
      "money": -8,     # Higher the different between tenant budget and asking price, less likely to lease. 
    }
    
    # Check if locations match, string matching
    # Comparison can be at submarket level based on geohash, point level. 
    s = SequenceMatcher(None, loc_p, loc_t)
    
    loc_match = s.ratio()
    
    # Size of the property and num of employees
    s1 = SequenceMatcher(None, size, employees)
    
    size_match = s1.ratio()
    
    # Time sensitivity, lower the # of days, higher the likelihood to match and sign the deal
    # We control this by assigning a negative weight to this. 
    # Can also use the data point to compare w/ properties that are going to be in market, but are currently not vacant. 
    time_match = days_lease_exp 
    
    # Check if rent is within the range. 
    # Rent Budget can also come directly from the Tenants. 
    #if (budget + ((15*budget)/100)) <= (ask_rent + ((15*ask_rent)/100)):
        
    # Calculate difference
    rent_diff = abs(budget - ask_rent) 
    
    # Compute score 
    score = loc_match + size_match * weights['size'] + time_match * weights['time'] + rent_diff * weights['money']
    
    return score 
    