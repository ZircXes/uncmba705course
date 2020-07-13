# -*- coding: utf-8 -*-
"""
MBA 705: Call Center in Python with SimPy 4.x

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
TODO: Significant refactoring for tons of repeated code
TODO: Refactoring for trunk-line data - tie into call center
TODO: Utilization charts - easier monitoring

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

class Customer(object):
    def __init__(self, env, c_name, c_call_type, c_call_subtype, 
                       c_call_patience, c_call_status, call_center):
        self.env = env
        self.name = c_name
        self.call_type = c_call_type
        self.call_subtype = c_call_subtype
        self.patience = c_call_patience
        self.status = c_call_status
        self.new_sale = 0
        
        self.t_start_time = env.now
        self.t_wait_time = 0
        self.t_work_time = 0
        self.t_total_time = 0
        self.t_stop_time = 0
        
        # Start the run process everytime an instance is created
        self.action = env.process(self.start_call(call_center))
    
    def pick_resource(self, call_center):
        if self.call_type == SEGMENT_NAMES[0]:   # Tech
            if self.call_subtype == TECH_NAMES[0]:
                return call_center['Tech A']
            elif self.call_subtype == TECH_NAMES[1]:
                return call_center['Tech B']
            else:
                return call_center['Tech C']
        elif self.call_type == SEGMENT_NAMES[1]: # Sales
            return call_center['Sales']
        else:
            return call_center['Sales']                  # Order Status

    def start_call(self, call_center):
         if self.status != CALL_STATUS[0]: 
            # Available trunk line, Next step is start IVR
            # Need a yield here due to how Simpy and generators work
            # Can think of this as 2 second delay to pick up line/connect
            yield self.env.timeout(0.04)
            self.env.process(self.initial_IVR(call_center))
         else:
            yield self.env.timeout(0.04) # Busy signal and exit
            
    def initial_IVR(self, call_center):
        # Abandonment not considered during IVR phase, although in reality a customer could hang-up.
        # Could increase arrival rate to sieze trunk lines or consider non-abandoned arrival rate
        # Technically siezed trunk lines may matter even for 15 seconds, but simplifying assumption
 
        yield self.env.timeout(IVR_DELAY)
        self.t_work_time += IVR_DELAY
    
        # Which queue will I eventually need
        resource = self.pick_resource(call_center)        
        
        if self.call_type == SEGMENT_NAMES[0]:
            self.env.process(self.start_tech_path(resource))
        elif self.call_type == SEGMENT_NAMES[1]:
            self.env.process(self.start_sales_call(call_center))
        else:
            self.env.process(self.start_status_call(call_center))
    
    def start_tech_path(self, call_center_resource):
        # Step 1, Automated System
        yield self.env.timeout(IVR_DELAY)
        self.t_work_time += IVR_DELAY
        
        # Start tech call
        arrive = self.env.now
        
        with call_center_resource.request() as req:
            results = yield req | self.env.timeout(self.patience)
            
            # Add in the wait time
            self.t_wait_time += (self.env.now - arrive)
            
            # Determine if we got to the call or if we abandoned
            if req in results:
                # Made the call
                t_call = random.triangular(CALL_TIME_TECH[0],
                                           CALL_TIME_TECH[1],
                                           CALL_TIME_TECH[2])
                
                # Have the call
                yield self.env.timeout(t_call)
                self.t_work_time += t_call
                
                # Call completed
                self.status = CALL_STATUS[3] # Completed
                self.t_stop_time = env.now
                self.t_total_time = self.t_stop_time - self.t_start_time   

                # Release the trunk line
                call_center_trunk_lines['Active'] -= 1             

            else:
                # Customer abandoned the call, waited too long
                self.status = CALL_STATUS[1] # ABANDONED
                self.t_stop_time = env.now
                self.t_total_time = self.t_stop_time - self.t_start_time
            
            # Release the trunk line
                call_center_trunk_lines['Active'] -= 1                 
    
    def start_sales_call(self, call_center):
        arrive = self.env.now
        
        with call_center['Sales'].request() as req:
            results = yield req | self.env.timeout(self.patience)
            
            # Add in the wait time
            self.t_wait_time += (self.env.now - arrive)
            
            # Determine if we got to the call or if we abandoned
            if req in results:
                t_call = random.triangular(CALL_TIME_SALES[0],
                                           CALL_TIME_SALES[1],
                                           CALL_TIME_SALES[2])
                
                # Have the call with Sales Staff
                yield self.env.timeout(t_call)
                self.t_work_time += t_call
                
                # Call completed
                self.status = CALL_STATUS[3] # Completed
                self.t_stop_time = env.now
                self.t_total_time = self.t_stop_time - self.t_start_time                
                               
                # Did we make the sale?
                if random.random() <= SALE_CLOSE_RATE:
                    self.new_sale = 1
                                    
                # Release the trunk line
                call_center_trunk_lines['Active'] -= 1               
                                
            else:
                # Customer abandoned the call, waited too long
                self.status = CALL_STATUS[1] # ABANDONED
                self.t_stop_time = env.now
                self.t_total_time = self.t_stop_time - self.t_start_time
                # Release the trunk line
                call_center_trunk_lines['Active'] -= 1
                  
        
    def start_status_call(self, call_center):
        # Step 1, Automated System
        t_ivr = random.triangular(IVR_ORDER_STATUS_DELAY[0],
                                  IVR_ORDER_STATUS_DELAY[1],
                                  IVR_ORDER_STATUS_DELAY[2])
        
        # Have the call with IVR
        yield self.env.timeout(t_ivr)
        self.t_work_time += t_ivr
        
        # Do we need to transfer to a sales person?
        if random.random() <= ORDER_STATUS_REQUIRE_SALES:
            # Transfer to sales for order status
            self.env.process(self.order_status_requires_sales(call_center))
        else:
            # Finish call and log complete
            self.status = CALL_STATUS[3]
            self.t_stop_time = env.now
            self.t_total_time = self.t_stop_time - self.t_start_time
            # Release the trunk line -- probably should somehow link this through better
            call_center_trunk_lines['Active'] -= 1
            
            # Customer completed the call
    
    def order_status_requires_sales(self, call_center):
        arrive = self.env.now
        
        with call_center['Sales'].request() as req:
            results = yield req | self.env.timeout(self.patience)
            
            # Add in the wait time
            self.t_wait_time += (self.env.now - arrive)
            
            # Determine if we got to the call or if we abandoned
            if req in results:
                t_call = random.triangular(CALL_TIME_ORDER_STATUS[0],
                                           CALL_TIME_ORDER_STATUS[1],
                                           CALL_TIME_ORDER_STATUS[2])
                
                # Have the call with Sales Staff
                yield self.env.timeout(t_call)
                self.t_work_time += t_call
                
                # Call completed
                self.status = CALL_STATUS[3] # Completed
                self.t_stop_time = env.now
                self.t_total_time = self.t_stop_time - self.t_start_time
                                  
                # Release the trunk line
                call_center_trunk_lines['Active'] -= 1               
                                
            else:
                # Customer abandoned the call, waited too long
                self.status = CALL_STATUS[1] # ABANDONED
                self.t_stop_time = env.now
                self.t_total_time = self.t_stop_time - self.t_start_time
                # Release the trunk line
                call_center_trunk_lines['Active'] -= 1
          
############################################################
# Functions        

def customer_source(env, arrival_interval, call_center, trunk_lines):
    """Source generates customers randomly
       env = simpy Environment
       interval = arrival lambda for exponential distribution
       """
    i = 0
    while True:
        i+= 1
        
        t = random.expovariate(1.0 / arrival_interval)
        yield env.timeout(t)
        
        # Customers are cutoff from calling in and queuing after 6pm
        if env.now < DAILY_END_TIME:
            c_name = 'Customer%000006d' % i
            # Customer Initial Attributes
            c_call_type = np.random.choice(SEGMENT_NAMES, 1, p=SEGMENT_FRACTION)[0]
            c_call_subtype = np.random.choice(TECH_NAMES, 1, p=TECH_FRACTION)[0] # Used only by Techs
            
            c_call_patience = random.triangular(WAIT_TIME_PATIENCE[0],
                                                WAIT_TIME_PATIENCE[1],
                                                WAIT_TIME_PATIENCE[2])
           
            # Is trunk line available?
            if (trunk_lines['Active'] < trunk_lines['Max']):
                trunk_lines['Active'] += 1
                c_call_status = CALL_STATUS[2] # In Progress
                
            else:
                c_call_status = CALL_STATUS[0] # Line Busy
                          
            trunk_line_usage.append([env.now, trunk_lines['Active']])
                
            # Create the customer in the simulation
            customer_call_list.append(Customer(env, c_name, c_call_type, c_call_subtype, c_call_patience, c_call_status, call_center))
                
             
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

# Simulate a single day of calls
run_params = RunParameters(problem_name = 'Call Center Model',
                           random_seed  = 52,
                           replications = 10,
                           run_time     = 24 * 60 * 1,   # 1 Day
                           warm_up_time = 0,
                           time_units   = TimeUnits.minutes,
                           author       = "Chris Kennedy",
                           date_time    = datetime.now(),
                           print_data   = False)

############################################################
# Problem Description
"""
Customers call into the contact center
  Step 01    - Assign customer attributes
  Step 02    - Is there enough trunk lines to accept call?
             - No: Abandoned Call
  Step 03    - IVR - (delay of 15 seconds) then move customer to queue
  Step 04a   - Sales / Order Status - take call and record potential sale
  Step 04b   - Tech - IVR (describe issue) ( 1 minute ) and assign to Tech
  Step 04b.1 - Assign to Tech - take call
  Final Step - Release Trunk Line

"""

############################################################
# Problem-specific parameters

# Resources
NUM_TRUNK_LINES     = 18 
NUM_STAFF_TECH_A    = 2
NUM_STAFF_TECH_B    = 2
NUM_STAFF_TECH_C    = 2
NUM_STAFF_SALES     = 3

# Customers
CUSTOMER_RATE = 0.50   # Minutes between customers

SEGMENT_NAMES = ["Tech","Sales","Order Status"]
SEGMENT_FRACTION = [0.76, 0.16, 0.08]
TECH_NAMES = ["Tech 1","Tech 2", "Tech 3"]
TECH_FRACTION = [0.25, 0.34, 0.41]

CALL_TIME_SALES =  [4, 15, 45]              # Triangular Distribution
CALL_TIME_TECH  =  [3,  6, 18]              # Triangular Distribution
CALL_TIME_ORDER_STATUS = [2,  3,  4]        # Triangular Distribution

CALL_STATUS = ['LINE BUSY','ABANDONED','IN PROGRESS','COMPLETED']

IVR_DELAY = 0.25                            # 15 seconds
IVR_ORDER_STATUS_DELAY = [2, 3, 4]          # Triangular Distribution
ORDER_STATUS_REQUIRE_SALES = 0.15     # % of time a Salesperson is required

WAIT_TIME_PATIENCE = [0,  2, 13] # Triangular Distribution - source: Talkdesk

SALE_CLOSE_RATE = 0.90                # % of inbound sales calls that succeed

# reference to costs
COST_TRUNK_LINE    = 20
COST_STAFF_TECH_A  = 250
COST_STAFF_TECH_B  = 250
COST_STAFF_TECH_C  = 300
COST_STAFF_SALES   = 200

# No new calls after daily end-time.
DAILY_START_TIME = 0         # 6 AM
DAILY_END_TIME = 12 * 60     # 6 PM = 12 hours * 60 minutes per hour

############################################################
# Monitoring
customer_call_list = []
trunk_line_tally = []

############################################################
# Initialize and Run

# I need both seeds since I'm using the NP Random choice function
random.seed(run_params.random_seed)
np.random.seed(run_params.random_seed)

for i in range(run_params.replications):
    print("Starting replication...%06d" % (i+1))
    env = simpy.Environment()

    trunk_line_usage = []

    sales   = simpy.Resource(env, capacity = NUM_STAFF_SALES)
    tech_a  = simpy.Resource(env, capacity = NUM_STAFF_TECH_A)
    tech_b  = simpy.Resource(env, capacity = NUM_STAFF_TECH_A)
    tech_c  = simpy.Resource(env, capacity = NUM_STAFF_TECH_A)
      
    call_center_staff = {'Sales': sales, 
                         'Tech A': tech_a,
                         'Tech B': tech_b,
                         'Tech C': tech_c}
    
    active_trunk_lines = 0
    call_center_trunk_lines = {'Active': active_trunk_lines,
                               'Max': NUM_TRUNK_LINES}

    # Run Sim.py
    env.process(customer_source(env,CUSTOMER_RATE, call_center_staff, call_center_trunk_lines))
    env.run(until=run_params.run_time)
    
    # Get my utilization data for trunk lines for each replication
    trunk_line_tally.append([i, trunk_line_usage])
    

############################################################
# Collect & Process Results
finished_list = []
for i in customer_call_list:
    if (i.status != CALL_STATUS[2] and i.t_start_time > run_params.warm_up_time):
        finished_list.append(i)

df = pd.DataFrame(([x.name, x.call_type, x.call_subtype, x.status, x.new_sale,
                    x.t_start_time, x.t_wait_time, x.t_work_time, x.t_stop_time, 
                    x.t_total_time] for x in finished_list), 
                   columns=['Name','Segment','Tech Segment','Status','New Sale',
                            'Start Time','Wait Time','Process Time','Stop Time',
                            'Total Time'])

processed_trunk_line_tally = []

for i in trunk_line_tally:
    for j in i[1]:
        processed_trunk_line_tally.append([i[0], j[0], j[1]])
    
trunk_df = pd.DataFrame(processed_trunk_line_tally,columns=['Replication','Time','Active'])
trunk_df['Time Group'] = trunk_df.apply(lambda x: math.floor(x['Time'] / 10)*10 + 10, axis=1)
    
############################################################
# Display Results
print("")
print("Simulation complete")
print("")
printRunParameters(run_params)   
print("")
print("Customers:            %6d" % len(customer_call_list))
print("Tallied Customers:    %6d" % len(finished_list))
print("")
print("\nData Counts for Tallies across all replications:")
print("Completed Sales: ", df['New Sale'].sum())
print(df[['Name','Status']].groupby(by=['Status']).count())
print("\nCounts by Call Type and Status - focus on LINE BUSY:")
print(df[['Segment','Status','Name']].groupby(by=['Segment','Status']).count())
print("\nAverages by Call Type and Status")
print(df[['Segment','Total Time','Status','Wait Time']].groupby(by=['Status','Segment']).mean())
############################################################
# Plot Trunk Line usage
plt.plot(trunk_df[trunk_df['Replication']==0]['Time'], trunk_df[trunk_df['Replication']==0]['Active'])
plt.hist(trunk_df['Active'], bins=19, density=True)


############################################################
# Finished
print("\nProgram Complete - END")
