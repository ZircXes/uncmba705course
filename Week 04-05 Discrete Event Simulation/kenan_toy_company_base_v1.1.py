# -*- coding: utf-8 -*-
"""
MBA 705: Kenan toy Company in Python with SimPy 4.x - Base

simpy:          https://simpy.readthedocs.io/en/latest/
Installation:   pip install simpy

Simpy is not nearly as fast as ARENA in terms of simple model building;
however, once you have a model setup, Simpy is extremely flexible.

You can also build python simulation into workflows with version control,
including re-usable code and modules.

This example is more advanced than the ARENA model by allowing for customers
to abandon the call if they wait too long.

@author: Chris Kennedy
@license: MIT (https://en.wikipedia.org/wiki/MIT_License)

TODO: Fix tally class
TODO: Factory only operates 8 hours a day 

"""

# BASIC PEP Standards for Naming

# variable_names
# function_names
# ClassNames
# GLOBALS
# lambda_ or class_ (trailing underscore: to avoid conflict with python names)

#####################################################
# Libraries

import simpy
import random
import numpy as np
import pandas as pd
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import math
import matplotlib.pyplot as plt

#####################################################
# Classes

class TimeUnits(Enum):
    seconds = "seconds"
    minutes = "minutes"
    hours = "hours"
    days = "days"
    weeks = "weeks"
    months = "months"
    quarters = "quarters"
    years = "years"
    
@dataclass
class RunParameters:
    problem_name: str = "untitled"
    random_seed: int = 42
    replications: int = 1
    run_time: int= 10
    warm_up_time: int = 0
    time_units: str = "minutes"
    author: str = "author"
    date_time: datetime = datetime.now()
    print_data: bool = False

# TODO
# I need to figure out how to make these more like a data structure (attributes not vars)
# @dataclass
# class Tally:
#    start_time: float
#   stop_time: float
#    wait_time: float
#    process_time: float
#    total_time: float

class Toy(object):
    def __init__(self, env, toy_name, toy, factory, replication):
        self.env = env
        self.name = toy_name
        self.type = toy['Name']
        self.profit = toy['Profit']
        self.station_times = [toy['Station 1'], toy['Station 2'], toy['Station 3']]
        self.status = 'In Progress'
        self.rework = 0
        self.replication = replication
        
        self.t_start_time = env.now
        self.t_wait_time = 0
        self.t_work_time = 0
        self.t_total_time = 0
        self.t_stop_time = 0
          
        # Start the run process everytime an instance is created
        self.action = env.process(self.start_order(factory))
    
    def start_order(self, factory):
        
        # arrive at station 1
        arrive = self.env.now
        
        with factory['Station 1'].request() as req:
            yield req
            self.t_wait_time += self.env.now - arrive
            
            t_station_one = random.expovariate(1.0 / self.station_times[0])
            yield self.env.timeout(t_station_one)
            self.t_work_time += t_station_one
            
            # If plane, move to station 3, otherwise station 2
            if self.type == 'Plane':
                self.env.process(self.station_three(factory))
            else:
                self.env.process(self.station_two(factory))

    def station_two(self, factory):
        # arrive at station 2
        arrive = self.env.now
        
        with factory['Station 2'].request() as req:
            yield req
            self.t_wait_time += self.env.now - arrive
            
            t_station_two = random.expovariate(1.0 / self.station_times[1])
            yield self.env.timeout(t_station_two)
            self.t_work_time += t_station_two
            
            # If Auto, check for rework
            if self.type == 'Auto' and random.random() > AUTO_QUALITY:
                self.rework += 1
                self.env.process(self.station_two(factory))
            else:
                self.env.process(self.station_three(factory))
        
    def station_three(self, factory):
        # arrive at station 3
        arrive = self.env.now
        
        with factory['Station 3'].request() as req:
            yield req
            self.t_wait_time += self.env.now - arrive
            
            t_station_three = random.expovariate(1.0 / self.station_times[2])
            yield self.env.timeout(t_station_three)
            self.t_work_time += t_station_three
            
            # Done - Wrap up details
            self.t_stop_time = self.env.now
            self.t_total_time = self.t_stop_time - self.t_start_time
            self.status = 'Done'
          
############################################################
# Functions        

def toy_source(env, toy, factory, replication):
    """Source generates toys randomly
       env = simpy Environment
       interval = arrival lambda for exponential distribution
       """
    i = 0
    while True:
        i+= 1
        
        t = random.expovariate(1.0 / toy['Arrival Rate'])
        yield env.timeout(t)
        
        toy_name = '%000006d' % i + '_' + toy['Name']
           
        # Create the customer in the simulation
        toy_list.append(Toy(env, toy_name, toy, factory, replication))
                             
# Could revoke the data class and add this as a method for run parameters class
def printRunParameters(run_params):
    print("Run Parameters...")
    print("Problem Name: %s" % run_params.problem_name)
    print("Random Seed: %d" % run_params.random_seed)
    print("# Replications: %d" % run_params.replications)
    print("Run Time: %d" % run_params.run_time)
    print("Warmup Time: %d" % run_params.warm_up_time)
    print("Active Time: %d" % (run_params.run_time - run_params.warm_up_time))
    print("Time Units: %s" % run_params.time_units)
    print("Author: %s" % run_params.author)
    print("DateTime: %s" % run_params.date_time)
    print("Print Results: %s" % run_params.print_data)        
        
############################################################
# Run parameters''

run_params = RunParameters(problem_name = 'Kenan Toy Company Model',
                           random_seed  = 52,
                           replications = 10,
                           run_time     = 300,   # Nets to 5 days/week, 50weeks/yr
                           warm_up_time = 50,
                           time_units   = TimeUnits.days,
                           author       = "Chris Kennedy",
                           date_time    = datetime.now(),
                           print_data   = False)

############################################################
# Problem Description
"""
Three toys arrive: Planes, Trains, and Autos
Autos have a quality indicator
3 Machine stations with rework for autos

"""
############################################################
# Problem-specific parameters

# DECISIONS
NUM_AUTO_INC           = 0         # Change this to adjust the model
EXTRA_MACHINES_ONE     = 0
EXTRA_MACHINES_TWO     = 0
EXTRA_MACHINES_THREE   = 0

# Resources
STATION_ONE_MACHINES   = 2 + EXTRA_MACHINES_ONE
STATION_TWO_MACHINES   = 2 + EXTRA_MACHINES_TWO
STATION_THREE_MACHINES = 2 + EXTRA_MACHINES_THREE

# Auto Choices
AUTO_5PCT          = 0.05


# reference to costs
COST_MACHINE       = 20000 
COST_AUTO_5PCT     = 15
COST_MKT           = 100000
MKT_PROMISE = 3 # days

# PRODUCT Details
PRODUCT_RATES = [1.0, 1.0, 1.0]
PRODUCT_NAMES = ["Plane","Train","Auto"]
PRODUCT_GROSS_PROFITS = [500.00, 250.00, 500.00 - COST_AUTO_5PCT * NUM_AUTO_INC] # Base for Auto is $500 @ 70%

# Other factors
AUTO_QUALITY = 0.70 + AUTO_5PCT * NUM_AUTO_INC

# Times
# Planes skip station 2
# Autos can be reworked at station 2
STATION_ONE_TIMES   =  [0.8,0.4,0.6]
STATION_TWO_TIMES   =  [0.0,0.6,0.6]
STATION_THREE_TIMES =  [0.8,0.1,0.4]


############################################################
# Monitoring
toy_list = []

############################################################
# Initialize and Run

# I need both seeds since I'm using the NP Random choice function
random.seed(run_params.random_seed)
np.random.seed(run_params.random_seed)


plane_data = {'Station 1': STATION_ONE_TIMES[0],
                  'Station 2': STATION_TWO_TIMES[0],
                  'Station 3': STATION_THREE_TIMES[0],
                  'Name': PRODUCT_NAMES[0],
                  'Profit': PRODUCT_GROSS_PROFITS[0],
                  'Arrival Rate': PRODUCT_RATES[0]}
    
train_data = {'Station 1': STATION_ONE_TIMES[1],
                  'Station 2': STATION_TWO_TIMES[1],
                  'Station 3': STATION_THREE_TIMES[1],
                  'Name': PRODUCT_NAMES[1],
                  'Profit': PRODUCT_GROSS_PROFITS[1],
                  'Arrival Rate': PRODUCT_RATES[1]}
    
auto_data  = {'Station 1': STATION_ONE_TIMES[2],
                  'Station 2': STATION_TWO_TIMES[2],
                  'Station 3': STATION_THREE_TIMES[2],
                  'Name': PRODUCT_NAMES[2],
                  'Profit': PRODUCT_GROSS_PROFITS[2],
                  'Arrival Rate': PRODUCT_RATES[2]}

toy_attributes = [plane_data, train_data, auto_data]

print("Starting Model: ", run_params.problem_name)
for i in range(run_params.replications):
    print("Starting replication...%06d" % (i+1))
    env = simpy.Environment()

    machine_a = simpy.Resource(env, capacity = STATION_ONE_MACHINES)
    machine_b = simpy.Resource(env, capacity = STATION_TWO_MACHINES)
    machine_c = simpy.Resource(env, capacity = STATION_THREE_MACHINES)
      
    factory = {'Station 1': machine_a, 
               'Station 2': machine_b,
               'Station 3': machine_c}
    
    # Initialize toy sources
    for toy in toy_attributes:
        env.process(toy_source(env, toy, factory, i)) 
    
    # Run environment
    env.run(until=run_params.run_time)
    
############################################################
# Collect & Process Results
finished_list = []
for i in toy_list:
    if (i.status == 'Done' and i.t_start_time > run_params.warm_up_time):
        finished_list.append(i)

df = pd.DataFrame(([x.name, x.type, x.rework, x.profit, x.replication,
                    x.t_start_time, x.t_wait_time, x.t_work_time, x.t_stop_time, 
                    x.t_total_time] for x in finished_list), 
                   columns=['Name','Type','Rework (ST2)','Profit', ' Replication',
                            'Start Time','Wait Time','Process Time','Stop Time',
                            'Total Time'])

result_percent_exceeding_marketing_promise = df[df['Total Time'] > MKT_PROMISE]['Name'].count() / df['Name'].count()    
    
result_average_times = df[['Type','Total Time']].groupby(by=['Type']).mean()
result_counts = df[['Name','Type']].groupby(by=['Type']).count()
    
result_product_profit = df['Profit'].sum() / run_params.replications

result_baseline_costs = COST_MACHINE * (EXTRA_MACHINES_ONE + 
                                        EXTRA_MACHINES_TWO + 
                                        EXTRA_MACHINES_THREE)

result_marketing_penalty = ((result_average_times - MKT_PROMISE > 0) * \
                            (result_average_times - MKT_PROMISE)).sum().values[0] * COST_MKT
                            
result_profit = result_product_profit - result_baseline_costs - result_marketing_penalty
    
############################################################
# Display Results
print("")
print("Simulation complete")
print("")
printRunParameters(run_params)   
print("")
print("Customers:            %6d" % len(toy_list))
print("Tallied Customers:    %6d" % len(finished_list))

print("\nAverage Times:")
print(result_average_times)

print("\nThroughput Counts:")
print(result_counts)
print("Percent Exceeding Marketing Promise {:5.1f}%".format(result_percent_exceeding_marketing_promise*100))

print("\nFinancial Results:")
print ("Product Gross Profit:    ${:11.2f}".format(result_product_profit))
print ("Fixed Costs - Machines:  ${:11.2f}".format(result_baseline_costs))
print ("Marketing Penalty:       ${:11.2f}".format(result_marketing_penalty))
print ("------------------------   ----------")
print ("Overall Profit:          ${:11.2f}".format(result_profit))

############################################################
# Finished
print("\nProgram Complete - END")
