"""
Example 04.03
Model for 4x4 Line and Cashier for Grocery StopIteration

Author: Chris Kennedy

Notes: This model mixes global types with iterators/functions
       A better approach would be to create objects and abstract
       away the general monitoring to make the code reusable.

       I'll refactor it in time to make it better and use SRP functions
"""

import random
import simpy
import pandas as pd
from math import sqrt

# Globals & Run Settings
RANDOM_SEED = 1337
NUM_REPLICATIONS = 25
WARM_UP_TIME = 60
SIMULATION_TIME = 600 + WARM_UP_TIME   # 10 hours
SIMULATION_UNITS = "minutes"
MODEL_NAME = "Grocery Store Demo: 4 Lines and 4 Cashiers"

# New Customer Arrivals
def customer_arrivals(env):
  """ Create new *customers* until the simulation reaches *SIMULATION_TIME*."""
  arrival_rate = 1.0 / 0.3333   # CHANGE A01
    
  while True:
    yield env.timeout(random.expovariate(arrival_rate))
        
    # Create a new customer
    # print ("New customer created")
    total_in_customers.append(env.now)

    # Select station at random
    station = random.choice(grocery_stations) # CHANGE A03
    # Generate the customer
    env.process(customer(env, station))  # CHANGE A03

def customer(env, station):
  """A customer tries to checkout at the grocery store
  """

  def random_checkout_time():
    mean = 1.0
    standard_deviation = 0.5
    floor = 0.15 
    return max(floor, random.normalvariate(mean, standard_deviation))

  start_time = env.now

  with station.request() as request:
    # Wait until it is my turn
    yield request

    wait_start = env.now
    yield env.timeout(random_checkout_time())
    waiting_time = env.now - wait_start
    total_time = env.now - start_time

    # print('Customer checkout took %.2f minutes.' % waiting_time)
    
    # print('Customer total time took %.2f minutes.' %total_time)
    wait_times.append(waiting_time)
    total_times.append(total_time)
    total_out_customers.append(start_time)
		
# Environment Setup
print("Grocery Store Demo: " + MODEL_NAME)
random.seed(RANDOM_SEED)
env = simpy.Environment()

# Monitors & Tallies
wait_times = []
total_times = []
total_in_customers = []
total_out_customers = []

# Grocery Store Setup
cashierA = simpy.Resource(env, capacity=1) # CHANGE A03
cashierB = simpy.Resource(env, capacity=1) # CHANGE A03
cashierC = simpy.Resource(env, capacity=1) # CHANGE A03
cashierD = simpy.Resource(env, capacity=1) # CHANGE A03
grocery_stations = [cashierA,cashierB,cashierC,cashierD] # CHANGE A03
env.process(customer_arrivals(env))

# Go
env.run(until=SIMULATION_TIME)
print("Done with Simulation")

# Process Statistics
print("Processing Statistics")

result_df = pd.DataFrame({'Arrival Time': total_out_customers, 'Wait Time': wait_times,'Total Time': total_times})

active_result_df = result_df[result_df['Arrival Time'] > WARM_UP_TIME]
print("Total Customers: " +str(len(active_result_df['Arrival Time'])))
# This is a lazy 95% confidence interval. Intead of importing statistics I use 2.0 which is good for Z or T for sample sizes greater than 55

# Wait
wait_mean = active_result_df['Wait Time'].mean()
wait_std = active_result_df['Wait Time'].std()
wait_n = len(active_result_df['Wait Time'])
wait_stderr = wait_std / sqrt(wait_n)
wait_t = 2.0
wait_moe = wait_t * wait_stderr
print("Wait Times: %.2f +/- %.2f (~95%% CI)" % (wait_mean, wait_moe))

# Total
total_mean = active_result_df['Total Time'].mean()
total_std = active_result_df['Total Time'].std()
total_n = len(active_result_df['Total Time'])
total_stderr = total_std / sqrt(total_n)
total_t = 2.0
total_moe = total_t * total_stderr
print("Total Time: %.2f +/- %.2f (~95%% CI)" % (total_mean, total_moe))

# Done
print("Done")