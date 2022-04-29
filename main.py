from Input.preprocess import generate_all_stations
from Output.save_to_excel import write_excel_output
from Simulation.BSS_environment import Environment
import copy
import pandas as pd
import numpy as np
import itertools as it



simple_run = True
scenario_analysis = not simple_run

#BASE DATA

#Parameters
start_hour = 7
simulation_time = 240  # 7 am to 11 pm   = 60*16=960   -> Smaller: 240 (60*4)
num_stations = 50   #was at 200
num_vehicles = 3
subproblem_scenarios = 2   #was at ten
branching = 7
time_horizon=25   

#basic_seed = 1   #alternatively just do a seed here at the beginning. A bit less controll though. 
seed_generating_trips = 1
seed_scenarios_subproblems = 2    # TO DO

greedy = False

#SCENARIO DATA

inputs = {
#'seed_generating_trips':list(range(0,3)),   #simulate 10 different days
#'init_branching':[3,5,7],
'num_vehicles':[0,2,5],
'num_stations':[20,30]
}


#COMMON DATA FOR ALL SCENARIOS
all_stations = generate_all_stations(start_hour)


#RUN ANALYSIS

if __name__ == '__main__':
    
    
    if simple_run:
        
        sim_env = Environment(start_hour, simulation_time, num_stations, copy.deepcopy(all_stations), 
                              num_vehicles, branching, time_horizon, subproblem_scenarios, 
                              seed_generating_trips = seed_generating_trips, 
                              seed_scenarios_subproblems = seed_scenarios_subproblems,
                              greedy=greedy)
        sim_env.set_up_system()    # SETUP TO DO
        sim_env.run_simulation()
        write_excel_output(sim_env)

        
    if scenario_analysis:
        
        keys = sorted(inputs)
        combinations = list(it.product(*(inputs[key] for key in keys)))
        num_scenario_analyses = len(combinations)
        
        base_env = Environment(start_hour, simulation_time, num_stations, copy.deepcopy(all_stations), 
                              num_vehicles, branching,time_horizon, subproblem_scenarios, 
                              greedy=greedy)
        envs = [copy.deepcopy(base_env) for i in range(num_scenario_analyses)]
        
        for i in range(num_scenario_analyses):
            values = combinations[i]
            
            #initial setup
            
            #update the parameters for the scenario
            parameters = dict(zip(keys, values))
            for key, value in parameters.items():
                setattr(envs[i],key, value)
                print(key, value)
            
            envs[i].set_up_system()
            #start simulation
            envs[i].run_simulation()
            write_excel_output(envs[i])
            
            
    

    
# IT UPDATES :D 
# class child:
#     def __init__(self, parent):
#         parent.start_hour = parent.start_hour + 1
        

# class parent:
#     def __init__(self, start_hour):
#         self.start_hour = start_hour
        

    
# test = parent(2)
# child(test)
# test.start_hour

    
    
    
    
    
    
    
    
    
        
        
        
        #----------------- WEIGHT ANALYSIS -------------------#
        
if False:
    
    
    def get_criticality_weights():
        # w_drive, w_dev, w_viol, w_net
        vals = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]
        weights = list()
        for val1 in vals:
            w_drive = val1
            for val2 in vals:
                if w_drive + val2 <= 1:
                    w_dev = val2
                else:
                    break
                for val3 in vals:
                    if w_drive + w_dev + val3 <= 1:
                        w_viol = val3
                    else:
                        break
                    w_flat = 1 - w_drive - w_dev - w_viol
                    weights.append((w_drive, w_dev, w_viol, w_flat))
        return weights
    
    
    def get_weight_combination_reduced():
        # W_V, W_R, W_D, W_VN, W_VL
        weights = list()
        vals_d = [0.1, 0.2, 0.3, 0.4]
        vals_v = [0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]
        vals_n = [0.5, 0.6, 0.7, 0.8, 0.9, 1]
        for val1 in vals_v:
            W_V = val1
            for val2 in vals_d:
                if W_V + val2 <= 1:
                    W_D = val2
                else:
                    break
                W_R = 1 - W_D - W_V
                for val3 in vals_n:
                    W_N = val3
                    W_L = 1 - W_N
                    weights.append((W_V, W_R, W_D, W_N, W_L))
        return weights
    
    
    def weight_analysis(choice):
        all_sets = get_criticality_weights()
        env = Environment(start_hour, simulation_time, stations, list(), branching, subproblem_scenarios)
    
        # Generating 10 scenarios
        scenarios = [env.generate_trips(simulation_time//60, gen=True) for i in range(1)]
    
        # Create excel writer
        writer = pd.ExcelWriter("Output/output_weights_" + choice + ".xlsx", engine='openpyxl')
        #book = load_workbook("Output/output_weights_" + choice + ".xlsx")
        #writer.book = book
    
        base_viol = list()
        for j in range(len(scenarios)):
            reset_stations(stations)
            init_base_stack = [copy.copy(trip) for trip in scenarios[j]]
            sim_base = Environment(start_hour, simulation_time, stations, list(), branching, subproblem_scenarios,
                                   trigger_start_stack=init_base_stack, memory_mode=True)
            sim_base.run_simulation()
            base_viol.append(sim_base)
    
        for i in range(len(all_sets)):
            for j in range(len(scenarios)):
                reset_stations(stations)
                init_stack = [copy.copy(trip) for trip in scenarios[j]]
                v = Vehicle(init_battery_load=40, init_charged_bikes=20, init_flat_bikes=0, current_station=stations[0],
                              id=0)
                sim_env = Environment(start_hour, simulation_time, stations, [v], branching, subproblem_scenarios,
                                      trigger_start_stack=init_stack, memory_mode=True, crit_weights=all_sets[i])
                sim_env.run_simulation()
                save_weight_output(i+1, j+1, sim_env, base_viol[j].total_starvations, base_viol[j].total_congestions, writer)
    

