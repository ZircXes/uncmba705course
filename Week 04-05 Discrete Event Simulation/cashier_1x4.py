# -*- coding: utf-8 -*-
"""
Created on Sat Jun 27 17:14:14 2020

@author: Chris Kennedy
TODO: Fix tally class

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
    def __init__(self, env, name, cashier_list, select_method):
        self.env = env
        self.name = name
        self.select_method = select_method
        # self.tally = Tally
        # self.tally.start_time = env.now
        self.t_start_time = env.now
        self.active = 1
        self.co_time = 0
        # Start the run process everytime an instance is created
        self.action = env.process(self.checkout(cashier_list, select_method))

            
    def checkout_time(self):
        # bounded random normal (negative times not allowed)
        # Checkout time really should be a combination of goods from
        # customer as well as speed of cashier
        # so storing this all in the Customer class is not ideal
        MU = 1.0
        SIGMA = 0.5
        rn = random.normalvariate(MU, SIGMA)
        result = rn if rn >= 0.0000001 else 0.0000001
        return result
    
    def pick_cashier_greedy(self, cashier_list):
        # Picks the cashier with the shortest queue (by count)
        cashier = cashier_list[0]
        queue_len = len(cashier.queue)
        
        for checkout in cashier_list:
            if len(checkout.queue) < queue_len:
                cashier = checkout
                queue_len = len(checkout.queue)
        
        return cashier
            
    def pick_cashier_random(self, cashier_list):
        # Picks cashier at random
        cashier = random.choice(cashier_list)
        return cashier
        
    def pick_cashier_lazy(self, cashier_list):
        # Looks at two lines at random and picks the shortest one
        if len(cashier_list) == 1:
            return cashier_list[0]
        
        # Pick two at random
        tmp_list = list(range(len(cashier_list)))
        random.shuffle(tmp_list)
        cashier_result = cashier_list[tmp_list[0]] if len(cashier_list[tmp_list[0]].queue) < len(cashier_list[tmp_list[1]].queue) else cashier_list[tmp_list[1]]
        return cashier_result

    def pick_cashier(self, cashier_list, select_method):
        if select_method == 'greedy':
            return self.pick_cashier_greedy(cashier_list)
        elif select_method == 'random':
            return self.pick_cashier_random(cashier_list)
        elif select_method == 'lazy':
            return self.pick_cashier_lazy(cashier_list)
        else:
            return cashier_list[0]

    def checkout(self, cashier_list, select_method):
        # Pick a checkout line
        cashier = self.pick_cashier(cashier_list, select_method)
        with cashier.request() as req:
            yield req
            
            start_checkout = self.env.now
            self.co_time = self.checkout_time()
            yield self.env.timeout(self.co_time)
           
            # Record tallies
            # TODO I removed this because the tally data class was operating
            # TODO as a shared class variable as opposed to attributes for each class
            # TODO Will need to fix and make more appropriate data structure
            # self.tally.wait_time = start_checkout - self.tally.start_time
            # self.tally.process_time = self.co_time
            # self.tally.stop_time = self.env.now
            # self.tally.total_time = self.tally.stop_time - self.tally.start_time
            
            self.t_wait_time = start_checkout - self.t_start_time
            self.t_process_time = self.co_time
            self.t_stop_time = self.env.now
            self.t_total_time = self.t_stop_time - self.t_start_time
            self.active = 0
            
    def getTallies(self):
        return [self.name, self.t_start_time, self.t_wait_time, self.t_process_time, self.t_stop_time, self.t_total_time, self.active]
            
############################################################
# Functions        

def customer_source(env, arrival_interval, cashier_list):
    """Source generates customers randomly
       env = simpy Environment
       interval = arrival lambda for exponential distribution
       checkout = resource required"""
    i = 0
    while True:
        i+= 1
        t = random.expovariate(1.0 / arrival_interval)
        yield env.timeout(t)
        c_name = 'Customer%000006d' % i
        customer_list.append(Customer(env, c_name, cashier_list, 'random'))
        # method choices = 'random' 'lazy' 'greedy' 'first'
                    
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

run_params = RunParameters(problem_name = 'Grocery 1x4',
                           random_seed  = 52,
                           replications = 1, # Replications and warm-up time not supported in this version
                           run_time     = 24 * 60 * 10,
                           warm_up_time = 0, # Replications and warm-up time not supported in this version
                           time_units   = TimeUnits.minutes,
                           author       = "Chris Kennedy",
                           date_time    = datetime.now(),
                           print_data   = False)

############################################################
# Problem-specific parameters
NUM_CASHIERS  = 1
CUSTOMER_RATE = 0.33333

############################################################
# Monitoring
customer_list = []

############################################################
# Initialize and Run

random.seed(run_params.random_seed)
env = simpy.Environment()

cashier_list = []
for i in range(NUM_CASHIERS):
    cashier_list.append(simpy.Resource(env, capacity=4))

############################################################
# Run Sim.py
    
env.process(customer_source(env,CUSTOMER_RATE, cashier_list))
env.run(until=run_params.run_time)

############################################################
# Collect Results
finished_list = []
for i in customer_list:
    if i.active == 0:
        finished_list.append(i)

df = pd.DataFrame(([x.name, x.t_start_time, x.t_wait_time, 
                         x.t_process_time, x.t_stop_time, 
                         x.t_total_time, x.active] for x in finished_list), 
                        columns=['Name','Start Time','Wait Time',
                                 'Process Time','Stop Time','Total Time',
                                 'Unfinished (WIP)'])

############################################################
# printresults
print("")
print("Simulation complete")
print("")
printRunParameters(run_params)   
print("")
print("Customers:            %6d" % len(customer_list))
print("Completed Customers:  %6d" % len(finished_list))
print("")
print("Means for Data Tallies:")
print(df.mean())

############################################################
# Finished
print("\nProgram Complete - END")
