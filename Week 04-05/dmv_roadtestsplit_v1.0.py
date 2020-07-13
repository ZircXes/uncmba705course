# -*- coding: utf-8 -*-
"""
MBA 705: DMV Case in Python with SimPy 4.x

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

class Customer(object):
    def __init__(self, env, c_name, c_segment, c_paperwork, c_rtt, dmv_setup):
        self.env = env
        self.name = c_name
        self.segment = c_segment
        self.paperwork = c_paperwork
        self.has_paperwork = np.random.random()
        self.roadtesttime = c_rtt
        self.t_start_time = env.now
        self.t_wait_time = 0
        self.t_work_time = 0
        self.t_paperwork = 0
        self.t_roadtest = 0
        self.active = 1
        self.paperwork_time = 10
        self.abandon = 0
        # Start the run process everytime an instance is created
        self.action = env.process(self.enter_dmv(dmv_setup))
            
    def get_paperwork_time(self):
        result = random.expovariate(1.0 / self.paperwork_time)
        return result
    
    def get_roadtest_time(self):
        result = random.expovariate(1.0 / self.roadtesttime)
        return result

    def enter_dmv(self, dmv_setup):
        with dmv_setup['Clerk'].request() as req:
            yield req
            
            self.t_paperwork = self.get_paperwork_time()
            self.t_work_time = self.t_work_time + self.t_paperwork
                     
            yield self.env.timeout(self.t_paperwork)
            
            # check if have paperwork
            if self.has_paperwork <= self.paperwork:
                # Continue on to road test
                self.env.process(self.perform_roadtest(dmv_setup))
            else:
                # Exit Process
                self.active = 0
                self.abandon = 1
                self.t_stop_time = self.env.now
                self.t_total_time = self.t_stop_time - self.t_start_time
                self.t_wait_time = self.t_total_time - self.t_work_time
        
        
    def perform_roadtest(self, dmv_setup):
        with dmv_setup['Roadtest'].request() as req:
            yield req
            
            self.t_roadtest = self.get_roadtest_time()
            self.t_work_time = self.t_work_time + self.t_roadtest
            
            yield self.env.timeout(self.t_roadtest)
            
            self.active = 0
            self.t_stop_time = self.env.now
            self.t_total_time = self.t_stop_time - self.t_start_time
            self.t_wait_time = self.t_total_time - self.t_work_time    

            # Customer completed DMV trip at this point
            
############################################################
# Functions        

def customer_source(env, arrival_interval, dmv, attributes):
    """Source generates customers randomly
       env = simpy Environment
       interval = arrival lambda for exponential distribution
       dmv = resource(s) required"""
    i = 0
    while True:
        i+= 1
        t = random.expovariate(1.0 / arrival_interval)
        yield env.timeout(t)
        c_name = 'Customer%000006d' % i

        c_segment = np.random.choice(attributes['Segments'],1,p=attributes['Segment %'])[0]
        c_paperwork = attributes[attributes['Segments'] == c_segment]['Paperwork'].values[0]
        c_roadtest  = attributes[attributes['Segments'] == c_segment]['RoadTestTime'].values[0]
        customer_list.append(Customer(env, c_name, c_segment, c_paperwork, c_roadtest, dmv))
        
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
    print("Print Reults: %s" % run_params.print_data)        
        
############################################################
# Run parameters''

run_params = RunParameters(problem_name = 'DMV Split Road Test Time on Segments',
                           random_seed  = 52,
                           replications = 5,
                           run_time     = 24 * 60 * 20,  
                           warm_up_time = 24 * 60 * 2,
                           time_units   = TimeUnits.minutes,
                           author       = "Chris Kennedy",
                           date_time    = datetime.now(),
                           print_data   = False)

############################################################
# Problem-specific parameters

# Resources
NUM_STAFF_CLERKS  = 1
NUM_STAFF_ROADTESTS = 1

# Customers
CUSTOMER_RATE = 15.0
SEGMENTS = [0.5, 0.5]
SEGMENT_NAMES = ["A","B"]
PAPERWORK = [0.95, 0.60]
ROAD_TEST_TIME = [16.0, 8.0]

attributes = pd.DataFrame({'Segments': SEGMENT_NAMES,
                           'Segment %': SEGMENTS,
                           'Paperwork': PAPERWORK,
                           'RoadTestTime': ROAD_TEST_TIME})

############################################################
# Monitoring
customer_list = []

############################################################
# Initialize and Run

# I need both seeds since I'm using the NP Random choice function
random.seed(run_params.random_seed)
np.random.seed(run_params.random_seed)

for i in range(run_params.replications):
    print("Starting replication...%06d" % (i+1))
    env = simpy.Environment()

    clerk = simpy.Resource(env, capacity = NUM_STAFF_CLERKS)
    roadtest = simpy.Resource(env, capacity = NUM_STAFF_ROADTESTS)
    dmv= {'Clerk': clerk, 
          'Roadtest': roadtest}

    # Run Sim.py
    
    env.process(customer_source(env,CUSTOMER_RATE, dmv, attributes))
    env.run(until=run_params.run_time)

############################################################
# Collect Results
finished_list = []
for i in customer_list:
    if (i.active == 0 and i.abandon == 0 and i.t_start_time > run_params.warm_up_time):
        finished_list.append(i)

df = pd.DataFrame(([x.name, x.segment, x.t_start_time, x.t_wait_time, 
                         x.t_work_time, x.t_stop_time, 
                         x.t_total_time, x.active, x.abandon] for x in finished_list), 
                        columns=['Name','Segment','Start Time','Wait Time',
                                 'Process Time','Stop Time','Total Time',
                                 'Unfinished (WIP)','No paperwork'])

segment_results = df.groupby(by=['Segment']).mean()
    
############################################################
# printresults
print("")
print("Simulation complete")
print("")
printRunParameters(run_params)   
print("")
print("Customers:            %6d" % len(customer_list))
print("Tallied Customers:    %6d" % len(finished_list))
print("")
print("Means for Data Tallies:")
print(df.mean())
print(segment_results[['Total Time','No paperwork']])
############################################################
# Finished
print("\nProgram Complete - END")
