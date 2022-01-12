import pandas as pd
import numpy as np
from sympy import Symbol, Eq, solve
import statsmodels.formula.api as sm
import os


# Solving the regression equation for Natural vacancy rate, i.e vacancy rate when Y = Change in rent = 0.
def calc_natural_vacancy(V, E, P, df):

    # PropType Multi-Family
    model = sm.ols(formula = 'Rent_Change ~ VACANCY_RATE + Employment + Population', data=df).fit()

    Int_coef = model.params[0]
    Vac_coef = model.params[1]
    emp_coef = model.params[2]
    pop_coef = model.params[3]

    # Solve for Natural rate of Vacancy Algebraically
    Vn = - (Int_coef + emp_coef*E + pop_coef*P) / Vac_coef

    # Solving using Sympy package

    #V = Symbol('V')

    # set rhs = 0 and solve for 'V'
    #eq1 = Eq(Int_coef + Vac_coef * V + emp_coef * E + inc_coef * I, 0)

    #solution = solve(eq1)

    return Vn


# Fit a regression model to calculate long run equilibrium vacancy rate.
def reg_vacancy(df):

    # Apply function to calculate Natural vacancy for each time period
    df['Natural_Vacancy'] = df.apply(lambda x: calc_natural_vacancy(x['VACANCY_RATE'], x['Employment'], x['Population'], df), axis=1)

    decimals = 3
    df['Natural_Vacancy'] = df['Natural_Vacancy'].apply(lambda x: round(x, decimals))
    #df['Natural_Vacancy'] = df['Natural_Vacancy'].astype(int)

    # Calculate difference between observed and natural levels of vacancy
    # Negative Diff implies high vacancy = downward pressure on rents
    # Positive Diff implies low vacancy = upward pressure on rents
    df['Diff_observed_natural'] = df['Natural_Vacancy'] - df['VACANCY_RATE']
    df['Diff_observed_natural'] = df['Diff_observed_natural'].apply(lambda x: round(x, decimals))

    return df
