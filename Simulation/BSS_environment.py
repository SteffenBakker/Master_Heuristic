import json
#import random
import numpy as np
from trip import Trip
from Simulation.event import VehicleEvent
import copy
from Input.preprocess import create_subset
from vehicle import Vehicle
import time


class Environment:

    charged_rate = 0.95

    def __init__(self, start_hour, simulation_time, num_stations,all_stations, 
                 num_vehicles, init_branching,time_horizon, scenarios,
                 seed_generating_trips=1, 
                 seed_scenarios_subproblems = 2,
                 handling_time=0.5,parking_time=1 , 
                 flexibility=3,average_handling_time=6,memory_mode=False,
                 trigger_start_stack=list(), greedy=False, weights=(0.6, 0.1, 0.3, 0.8, 0.2),
                 criticality=True, crit_weights=(0.2, 0.1, 0.5, 0.2)):
        self.stations = None
        self.all_stations = all_stations
        self.vehicles = None
        
        self.num_stations = num_stations 
        self.num_vehicles = num_vehicles 
        
        self.start_hour = start_hour
        self.num_hours = simulation_time//60
        self.current_time = start_hour * 60
        self.simulation_time = simulation_time
        self.simulation_stop = simulation_time + self.current_time
        self.trigger_start_stack = trigger_start_stack
        self.trigger_stack = list()
        self.init_branching = init_branching
        self.scenarios = scenarios    #number of scenarios!!
        self.greedy = greedy
        self.weights = weights
        self.event_times = list()
        self.criticality = criticality
        self.crit_weights = crit_weights

        self.seed_generating_trips =  seed_generating_trips
        self.seed_scenarios_subproblems = seed_scenarios_subproblems

        self.time_horizon = time_horizon
        self.parking_time = parking_time
        self.handling_time = handling_time
        self.flexibility = flexibility 
        self.average_handling_time = average_handling_time
        self.strategy = None
        
        self.memory_mode = memory_mode
        self.initial_stack = None

        self.total_gen_trips = len(trigger_start_stack)
        self.trips_per_hour = []

        self.total_starvations = 0
        self.total_congestions = 0

        self.total_starvations_per_hour = list()
        self.total_congestions_per_hour = list()

        self.vehicle_vis = None
        
        self.system_setup = 0

        #OTHER
        self.times_called = 0
        self.simulation_start_clock_time = 0
        self.simulation_duration_total = 0
        self.simulation_duration = 0
        self.simulation_duration_per_hour = []
        self.master_problem_num_times_called = []
        self.master_problem_cpu_times = []  #just used as a placeholder
        self.master_problem_cpu_time_per_hour = []
        #self.master_duration_total = 0
        self.scoring_problem_cpu_times = []
        self.scoring_problem_cpu_time_per_hour = []
        #self.scoring_duration_total = 0    


    def set_up_system(self):
        
        self.rng1 = np.random.RandomState(self.seed_generating_trips)
        
        self.num_hours = self.simulation_time//60
        self.current_time = self.start_hour * 60
        
        if self.num_vehicles==0:
            self.strategy ='base'
        elif self.greedy:
            self.strategy = 'greedy'
        else:
            self.strategy = 'heuristic'
        
        self.stations = self.generate_stations(self.num_stations,self.all_stations)
        self.vehicles = self.generate_vehicles(self.num_vehicles)
        
        self.vehicle_vis = {v.id: [[v.current_station.id], [], [], []] for v in self.vehicles}
        self.print_number_of_bikes()
        
        for veh1 in self.vehicles:
            self.trigger_stack.append(VehicleEvent(self.current_time, self.current_time, veh1, self, greedy=self.greedy))
        if not self.memory_mode:
            self.generate_trips(self.simulation_time // 60)
        self.trigger_stack = self.trigger_start_stack + self.trigger_stack
        self.trigger_stack = sorted(self.trigger_stack, key=lambda l: l.end_time)

        self.system_setup = 1

    def generate_stations(self,num_stations,all_stations):
        #data_file = open("Input//AllData", "rb")     
        #all_stations = pickle.load(data_file)
        #data_file.close()
        stations = create_subset(all_stations, num_stations) #input//preprocess.py
        #reset_stations(stations)
        if self.num_stations >= 5:
            stations[4].depot = True   #why hardcoded?
        else:
            print('Possible error due to not setting a depot station')
        return stations

    def generate_vehicles(self,num_vehicles):
        vehicles = list()
        if self.num_stations < self.num_vehicles:
            print('Possible error: too few stations compared to vehicles')
        for k in range(num_vehicles):  #construct the actual vehicles...
            vehicles.append(Vehicle(init_battery_load=40, init_charged_bikes=0, init_flat_bikes=0,
                                    current_station=self.stations[k], id=k))
        return vehicles

    def run_simulation(self):
        self.simulation_start_clock_time = time.time()
        self.simulation_duration_start = time.time()
        if self.system_setup == 0:
            print('THE SYSTEM IS NOT SET UP')
        else:
            record_trigger = self.current_time + 60
            while self.current_time < self.simulation_stop:
                if self.current_time >= record_trigger:
                    record_trigger += 60
                    self.update_violations()
                    self.total_starvations_per_hour.append(self.total_starvations)
                    self.total_congestions_per_hour.append(self.total_congestions)
                    self.update_times_per_hour()
                self.event_trigger()
            print('End the simulation')
            self.end_simulation()
            self.simulation_duration_total = time.time() - self.simulation_start_clock_time

    def update_times_per_hour(self):
        self.simulation_duration_per_hour.append(time.time() - self.simulation_duration_start)
        self.simulation_duration_start = time.time()
        self.master_problem_cpu_time_per_hour.append(sum(self.master_problem_cpu_times))
        self.master_problem_num_times_called.append(len(self.master_problem_cpu_times))
        self.master_problem_cpu_times = []
        self.scoring_problem_cpu_time_per_hour.append(sum(self.scoring_problem_cpu_times))
        self.scoring_problem_cpu_times = []

        
    def update_violations(self):
        temp_starve = 0
        temp_cong = 0
        for st in self.stations:
            temp_starve += st.total_starvations
            temp_cong += st.total_congestions
        self.total_starvations = temp_starve
        self.total_congestions = temp_cong

    
    def event_trigger(self):
        if len(self.trigger_start_stack) == 0 and len(self.trigger_stack) == 0:
            print('ERROR: empty stacks')
        if len(self.trigger_start_stack) == 0:
            event = self.trigger_stack.pop(0)
            self.current_time = event.end_time
        elif len(self.trigger_stack) == 0:
            event = self.trigger_start_stack.pop(0)
            self.current_time = event.start_time
        else:
            if self.trigger_start_stack[0].start_time < self.trigger_stack[0].end_time:
                event = self.trigger_start_stack.pop(0)
                self.current_time = event.start_time
            else:
                event = self.trigger_stack.pop(0)
                self.current_time = event.end_time
        event.arrival_handling()
        if isinstance(event,VehicleEvent):   #or isinstance(event,VehicleEvent)
                self.scoring_problem_cpu_times.append(event.sub_time)
                self.master_problem_cpu_times.append(event.master_time)
        if event.event_time > 0:
            self.event_times.append(event.event_time)
        if isinstance(event, Trip) and event.redirect:
            self.trigger_stack.append(event)
            self.trigger_stack = sorted(self.trigger_stack, key=lambda l: l.end_time)

    def generate_trips(self, no_of_hours, gen=False):
        if not gen:
            total_start_stack = self.trigger_start_stack
        else:
            total_start_stack = list()
        current_hour = self.current_time // 60
        for hour in range(current_hour, current_hour + no_of_hours):
            trigger_start = list()
            num_trips = 0
            for st in self.stations:
                if not st.depot:
                    num_bikes_leaving = int(self.rng1.poisson(lam=st.get_outgoing_customer_rate(hour), size=1)[0])
                    num_trips += num_bikes_leaving
                    next_st_prob = st.get_subset_prob(self.stations)
                    for i in range(num_bikes_leaving):
                        start_time = self.rng1.randint(hour * 60, (hour+1) * 60)
                        next_station = self.rng1.choice(self.stations, p=next_st_prob)
                        charged = self.rng1.binomial(1, Environment.charged_rate)
                        trip = Trip(st, next_station, start_time, self.stations,
                                    charged=charged, num_bikes=1, rebalance="nearest")
                        trigger_start.append(trip)
            total_start_stack += trigger_start
            self.trips_per_hour.append(num_trips)
        self.trigger_start_stack = sorted(total_start_stack, key=lambda l: l.start_time)
        init_stack = [copy.copy(trip) for trip in self.trigger_start_stack]
        self.initial_stack = init_stack
        self.total_gen_trips += len(self.trigger_start_stack)
        return init_stack

    def end_simulation(self):
        self.update_violations()
        self.total_starvations_per_hour.append(self.total_starvations)
        self.total_congestions_per_hour.append(self.total_congestions)
        self.total_starvations_per_hour = ([self.total_starvations_per_hour[0]] + 
                                           list(np.diff(self.total_starvations_per_hour)))
        self.total_congestions_per_hour = ([self.total_congestions_per_hour[0]] + 
                                           list(np.diff(self.total_congestions_per_hour)))
        self.update_times_per_hour()
        self.visualize_system()
        self.status()

    def visualize_system(self):
        json_stations = {}
        for station in self.stations:
            # [lat, long], charged bikes, flat bikes, starvation score, congestion score
            json_stations[station.id] = [[station.latitude, station.longitude], station.current_charged_bikes,
                                         station.current_flat_bikes, station.total_congestions, station.total_starvations,
                                         station.station_cap, int(station.depot)]
        with open('Visualization/station_vis.json', 'w') as fp:
            json.dump(json_stations, fp)
        with open('Visualization/vehicle.json', 'w') as f:
            json.dump(self.vehicle_vis, f)

    def status(self):
        print("--------------------- SIMULATION STATUS -----------------------")
        print("Simulation time =", self.simulation_time, "minutes")
        print("Total requested trips =", self.total_gen_trips)
        print("Starvations =", self.total_starvations)
        print("Congestions =", self.total_congestions)
        self.print_number_of_bikes()
        print("---------------------------------------------------------------")

    def print_number_of_bikes(self):
        total_charged = 0
        total_flat = 0
        for station in self.stations:
            total_charged += station.current_charged_bikes
            total_flat += station.current_flat_bikes
        print("Total charged: ", total_charged)
        print("Total flat: ", total_flat)
