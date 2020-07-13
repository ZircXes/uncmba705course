# -*- coding: utf-8 -*-
"""
MBA 705: Tarheel Tractor in Python with GEKKO

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

# Recommend to solver that the problem is linear
m.options.linear = 1

#############################################################
# Raw Data - Names
# TO DO - Move data to XML or JSON or TXT and use a data load function
PRODUCT_NAMES = ['Tar Heel Model 100',
                 'Tar Heel Model 125']

PRODUCT_REVENUE = [10000, 15000]

FIBERGLASS_PARTS = [60, 30]
FIBERGLASS_AVAILABLE = 2400

MODIFICATION_PARTS = [40, 100]
MODIFICATIONS_AVAILABLE = 4000
# 1 Engine and assembly per tractor
ENGINES_AVAILABLE = 50
M100_ASSEMBLIES = 36
M125_ASSEMBLIES = 38

#############################################################
# Model Details

#######################
# Model Decision Variables
# Total Variables = 2

x_m100 = m.Var(value=0,lb=0, ub=M100_ASSEMBLIES)
x_m125 = m.Var(value=0,lb=0, ub=M125_ASSEMBLIES)

#######################
# Objective function
# Maximize Revenue = Minimize -Revenue
m.Obj(-(x_m100*PRODUCT_REVENUE[0] + x_m125*PRODUCT_REVENUE[1]))

#######################
# Constraints

m.Equation(x_m100*FIBERGLASS_PARTS[0] + x_m125*FIBERGLASS_PARTS[1] <= FIBERGLASS_AVAILABLE)
m.Equation(x_m100*MODIFICATION_PARTS[0] + x_m125*MODIFICATION_PARTS[1] <= MODIFICATIONS_AVAILABLE)
m.Equation(x_m100 + x_m125 <= ENGINES_AVAILABLE)
# I moved the two constraint equations to upper-bounds for vars

#############################################################
## Solve
# Objectives are always minimized in Gekko
# We multiplied objective by -1 to "maximize"
m.solve()

#############################################################
## Print Results
print("\nSolution:")
print("M100 Tractors: ", x_m100.value)
print("M125 Tractors: ", x_m125.value)
print("Revenue: ",  str(m.options.objfcnval*-1))