from Input.preprocess import *
from vehicle import Vehicle
from Output.save_to_excel import write_excel_output
from Simulation.BSS_environment import Environment
import copy
import pandas as pd
from openpyxl import load_workbook


start_hour = 7
no_stations = 20   #was at 200
branching = 7
subproblem_scenarios = 2   #was at ten
simulation_time = 240  # 7 am to 11 pm   = 60*16=960   -> Smaller: 240 (60*4)
all_stations = generate_all_stations(start_hour)
stations = create_subset(all_stations,no_stations)
stations[4].depot = True




def first_step():
    v = Vehicle(init_battery_load=40, init_charged_bikes=10, init_flat_bikes=0
                , current_station=stations[0], id=0)
    sim_env = Environment(start_hour, simulation_time, stations, [v], branching, subproblem_scenarios, greedy=True)
    sim_env.run_simulation()
    write_excel_output(sim_env)


def vehicle_analysis(days, veh, run):
    env = Environment(start_hour, simulation_time, stations, list(), branching, subproblem_scenarios)

    # Generating days
    days = [env.generate_trips(simulation_time // 60, gen=True) for i in range(days)]


    base_envs = list()
    for j in range(len(days)):
        reset_stations(stations)
        init_base_stack = [copy.copy(trip) for trip in days[j]]
        sim_base = Environment(start_hour, simulation_time, stations, list(), branching, subproblem_scenarios,
                               trigger_start_stack=init_base_stack, memory_mode=True)
        sim_base.run_simulation()
        base_envs.append(sim_base)

    for d in range(len(days)):
        for n_veh in range(1, veh+1):
            vehicles = list()
            for k in range(n_veh):
                vehicles.append(Vehicle(init_battery_load=40, init_charged_bikes=0, init_flat_bikes=0,
                                        current_station=stations[k], id=k))
            reset_stations(stations)
            init_heur_stack = [copy.copy(trip) for trip in days[d]]
            vehicles_heur = [copy.copy(veh) for veh in vehicles]
            sim_heur = Environment(start_hour, simulation_time, stations, vehicles_heur, branching,
                                   subproblem_scenarios, trigger_start_stack=init_heur_stack, memory_mode=True,
                                   criticality=True)
            sim_heur.run_simulation()
            save_vary_vehicle_output(d+1, n_veh, sim_heur, base_envs[d], writer)


if __name__ == '__main__':
    print("w: weight analysis, c: strategy comparison, r: runtime analysis, fs: first step analysis, v: vehicles,"
          "charge: charging analysis, vf: fleet analysis")
    choice = 'fs'  # OR 'v' for vehicle
    sim_env = Environment(start_hour, 0, stations, list(), branching, subproblem_scenarios)
    sim_env.run_simulation()
    if choice == 'v':
        scenarios = input('Number of days:')
        vehicles = input('Number of vehicles:')
        run = input('run number:')
        vehicle_analysis(int(scenarios), int(vehicles), run)
    elif choice == 'fs':
        first_step()
    else:
        print("No analysis")
        
        
        
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
    

