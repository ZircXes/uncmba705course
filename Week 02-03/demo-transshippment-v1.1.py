# -*- coding: utf-8 -*-
"""
MBA 705: Transshipment Demo Solution using Python and GEKKO optimization

Gekko:          https://gekko.readthedocs.io/en/latest/
Installation:   pip install gekko

GEKKO doesn't have a forced SIMPLEX LP solver like EXCEL
however, you can set the linear option to improve performance

I went with Gekko over SciPy due to the performance of the solver engines.
Commercial solvers tend to outperform open-source, and the APOPT/IPOPT
solvers seem to be significantly superior to SciPy open-source methods.

Some of the basic ones in SciPy are well-known from graduate level non-linear
vector space optimization courses but are less effective. 

Is Python/Gekko faster than EXCEL? Probably not.
Is Python/Gekko more powerful than EXCEL? Absolutely:
    - Support for more variables
    - More non-linear solve engines
    - More types of problems can be solved
    - Version Control / Unit testing can be integrated
    - Can be built into an analysis/prediction/modeling pipeline
    - Support for automation

@author: Chris Kennedy
@license: MIT (https://en.wikipedia.org/wiki/MIT_License)
"""

#####################

import pandas as pd
from itertools import product
from gekko import GEKKO
m = GEKKO()
m.options.SOLVER=1
m.solver_options = ['minlp_maximum_iterations 500', \
                # treat minlp as nlp
                'minlp_as_nlp 0', \
                # nlp sub-problem max iterations
                'nlp_maximum_iterations 50', \
                # 1 = depth first, 2 = breadth first
                'minlp_branch_method 1', \
                # maximum deviation from whole number
                'minlp_integer_tol 0.05', \
                # covergence tolerance
                'minlp_gap_tol 0.01']

# Recommend to solver that the problem is linear
m.options.linear = 1

###############################
# Raw Data
# Labels
farms = ['Nebraska','Colorado']
warehouses = ['Kansas City','Omaha','Des Moines']
stores = ['Chicago','St. Louis','Cincinnati']

# Shipping costs
ship_farms = pd.DataFrame([[16.0, 10.0, 12.0], [15.0,14.0,17.0]], columns=warehouses, index=farms)
ship_warehouses = pd.DataFrame([[6.0,8.0,10.0],[7.0,11.0,11.0],[4.0,5.0,12.0]], columns=stores, index=warehouses)

# Supply and Demand
supply= pd.DataFrame([[300],[300]], index=farms, columns=['Supply'])
demand = pd.DataFrame([[200],[100],[300]], index=stores, columns=['Demand'])

###############################
# Model Details

x_a = m.Array(m.Var, (2, 3), lb=0, value=1)  # Farm -> Warehouse
x_b = m.Array(m.Var, (3, 3), lb=0, value=1)  # Warehouse -> Stores

# Intermediates
# Sum products (X * Costs)
stage_a_costs = m.Intermediate(sum(
                        [ (x_a[r, c] * ship_farms.iloc[r, c]) 
                          for r, c in product(range(2), range(3)) ] ))

stage_b_costs = m.Intermediate(sum(
                        [ (x_b[r, c] * ship_warehouses.iloc[r, c])
                          for r, c in product(range(3), range(3)) ] ))

# Sums for rows and columns for constraints
from_nebraska     = m.Intermediate(sum([x_a[0, c] for c in range(3)]))
from_colorado     = m.Intermediate(sum([x_a[1, c] for c in range(3)]))

to_kansas_city    = m.Intermediate(sum([x_a[r, 0] for r in range(2)]))
to_omaha          = m.Intermediate(sum([x_a[r, 1] for r in range(2)]))
to_des_moines     = m.Intermediate(sum([x_a[r, 2] for r in range(2)]))

from_kansas_city  = m.Intermediate(sum([x_b[0, c] for c in range(3)]))
from_omaha        = m.Intermediate(sum([x_b[1, c] for c in range(3)]))
from_des_moines   = m.Intermediate(sum([x_b[2, c] for c in range(3)]))

to_chicago        = m.Intermediate(sum([x_b[r, 0] for r in range(3)]))
to_stlouis        = m.Intermediate(sum([x_b[r, 1] for r in range(3)]))
to_cincinnati     = m.Intermediate(sum([x_b[r, 2] for r in range(3)]))
    
# Objective function
m.Obj(stage_a_costs + stage_b_costs)

# Constraints ##########

# Supply Constraints
m.Equation(from_nebraska <= supply['Supply'].loc['Nebraska'])
m.Equation(from_colorado <= supply['Supply'].loc['Colorado'])

# Demand Constraints
m.Equation(to_chicago >= demand['Demand'].loc['Chicago'])
m.Equation(to_stlouis >= demand['Demand'].loc['St. Louis'])
m.Equation(to_cincinnati >= demand['Demand'].loc['Cincinnati'])

# Balance / Flow Constraints
m.Equation(to_kansas_city >= from_kansas_city)
m.Equation(to_omaha       >= from_omaha)
m.Equation(to_des_moines  >= from_des_moines)

## Solve
# Objectives are always minimized in Gekko, maximize by multiplying by -1
m.solve()

## Print Results
df_a = pd.DataFrame(x_a, columns=warehouses, index=farms)
df_b = pd.DataFrame(x_b, columns=stores, index=warehouses)

print("Solution:")
print(df_a)
print("")
print(df_b)
print("")
print('Objective (Total Cost): ', str(m.options.objfcnval))
