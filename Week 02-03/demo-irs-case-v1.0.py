# -*- coding: utf-8 -*-
"""
MBA 705: IRS Optimization in Python with GEKKO

This case assumes we have already fit the models
In a future version, I may do the data analysis here as well
The full case involves database manipulation, modeling, and optimization

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

#############################################################

from gekko import GEKKO
import pandas as pd

#############################################################
# Setup Solver

m = GEKKO(remote=False)
m.options.SOLVER=1 # APOPT - for Mixed Non-linear Integer Programming
m.solver_options = ['minlp_maximum_iterations 5000', \
                # treat minlp as nlp
                'minlp_as_nlp 0', \
                # nlp sub-problem max iterations
                'nlp_maximum_iterations 1000', \
                # 1 = depth first, 2 = breadth first
                'minlp_branch_method 1', \
                # maximum deviation from whole number
                'minlp_integer_tol 0.005', \
                # covergence tolerance
                'minlp_gap_tol 0.0001']

#############################################################
# Raw Data - Names
# TO DO - Move data to XML or JSON or TXT and use a data load function
AUDIT_NAMES = ['1040A',
                 '1040 Sch. C',
                 '1040 Sch. F']

NC_ATR_MODEL = pd.DataFrame([[458.9042097, 0.64329457, 354.9557, 0.005, 43619000],
                             [498.6219442, 0.44756887, 537.6039, 0.005, 63315200],
                             [838.2074013, 0.35727854, 856.1545, 0.005,  7609900]],
                            columns=['A','b','Audit Cost', 'Coverage Minimum', 'Population'], index=AUDIT_NAMES)

BUDGET_MAX = 560000000

#############################################################
# Model Details

#######################
# Model Decision Variables
# Total Variables = 3

# Audit Coverage %
x_1 = m.Var(value=NC_ATR_MODEL['Coverage Minimum'][AUDIT_NAMES[0]], lb=0, ub=1)
x_2 = m.Var(value=NC_ATR_MODEL['Coverage Minimum'][AUDIT_NAMES[1]], lb=0, ub=1)
x_3 = m.Var(value=NC_ATR_MODEL['Coverage Minimum'][AUDIT_NAMES[2]], lb=0, ub=1)

#######################
# Intermediate Calculations

# Compute Normalized Cumulative Additional Tax Revenue (NCATR) 
#    for each audit class given audit coverage % (x)
i_NCATR_1 = m.Intermediate(NC_ATR_MODEL['A'][AUDIT_NAMES[0]] * x_1 ** NC_ATR_MODEL['b'][AUDIT_NAMES[0]])
i_NCATR_2 = m.Intermediate(NC_ATR_MODEL['A'][AUDIT_NAMES[1]] * x_2 ** NC_ATR_MODEL['b'][AUDIT_NAMES[1]])
i_NCATR_3 = m.Intermediate(NC_ATR_MODEL['A'][AUDIT_NAMES[2]] * x_3 ** NC_ATR_MODEL['b'][AUDIT_NAMES[2]])

# Compute Cumulative Additional Tax Revenue (CATR) given the population
i_CATR_1 = m.Intermediate(i_NCATR_1 * NC_ATR_MODEL['Population'][AUDIT_NAMES[0]])
i_CATR_2 = m.Intermediate(i_NCATR_2 * NC_ATR_MODEL['Population'][AUDIT_NAMES[1]])
i_CATR_3 = m.Intermediate(i_NCATR_3 * NC_ATR_MODEL['Population'][AUDIT_NAMES[2]])

# (Cost / Audit) * (Audit Coverage %) * Population = $
i_cost_1 = m.Intermediate(x_1 * NC_ATR_MODEL['Audit Cost'][AUDIT_NAMES[0]] 
                              * NC_ATR_MODEL['Population'][AUDIT_NAMES[0]])
i_cost_2 = m.Intermediate(x_2 * NC_ATR_MODEL['Audit Cost'][AUDIT_NAMES[1]] 
                              * NC_ATR_MODEL['Population'][AUDIT_NAMES[1]])
i_cost_3 = m.Intermediate(x_3 * NC_ATR_MODEL['Audit Cost'][AUDIT_NAMES[2]] 
                              * NC_ATR_MODEL['Population'][AUDIT_NAMES[2]])

# Compute Net Revenues (CATR - Audit Total Cost)
i_net_revenue_1 = m.Intermediate(i_CATR_1 - i_cost_1)
i_net_revenue_2 = m.Intermediate(i_CATR_2 - i_cost_2)
i_net_revenue_3 = m.Intermediate(i_CATR_3 - i_cost_3)

total_spend = m.Intermediate(i_cost_1 + i_cost_2 + i_cost_3)
total_net_revenue = m.Intermediate(i_net_revenue_1 + i_net_revenue_2 + i_net_revenue_3)

#######################
# Objective function

# Maximize Revenue means Minimize (-Revenue)
m.Obj(-total_net_revenue)

#######################
# Constraints

m.Equation(x_1 >= NC_ATR_MODEL['Coverage Minimum'][AUDIT_NAMES[0]])
m.Equation(x_2 >= NC_ATR_MODEL['Coverage Minimum'][AUDIT_NAMES[1]])
m.Equation(x_3 >= NC_ATR_MODEL['Coverage Minimum'][AUDIT_NAMES[2]])
m.Equation(total_spend <= BUDGET_MAX)
m.Equation(total_spend >= 0)

#############################################################
## Solve
# Objectives are always minimized in Gekko
# We multiplied objective by -1 to "maximize"
m.solve()

#############################################################
## Print Results
print("\nSolution:")

print("Net Revenue:    ${:20,.2f}".format(m.options.objfcnval*-1))
print("Rev per $Spend: ${:20,.2f}".format((m.options.objfcnval*-1 + total_spend.value[0]) / total_spend.value[0]))
print("1040A:            {:19.2f}%".format(x_1.value[0]*100))
print("1040 Sch. C:      {:19.2f}%".format(x_2.value[0]*100))
print("1040 Sch. F:      {:19.2f}%".format(x_3.value[0]*100))
