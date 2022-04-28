import pandas as pd
from datetime import datetime
from os import path
from numpy import array


def write_excel_output(env):
    
    # Create excel writer
    #openpyxl gives some error in the encoding, but excel can recover the file. good for now
    if path.exists("Output/results.xlsx"):
        writer = pd.ExcelWriter("Output/results.xlsx",engine='openpyxl',mode='a', if_sheet_exists='overlay')  #removing engin=openpyxl leads to an error with max_row (due to xlsxwriter)
    else:
        writer = pd.ExcelWriter("Output/results.xlsx",engine='openpyxl')  
    
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    
    
    fixed_var = {}
    fixed_var['Timestamp'] = dt_string
    
    #scalars   THIS IS A PREDEFINED SCENARIO!!!!!
    fixed_var_mapping = {'Seed_basic':'basic_seed',
                        'Num_stations':'num_stations',
                        'Num_vehicles':'num_vehicles',
                        'Num_scenarios':'scenarios',
                        'Time_horizon':'time_horizon' ,
                        'Branching_constant':'init_branching',
                        'Strategy':'strategy',
                        } 
    
    for key, value in fixed_var_mapping.items():
        fixed_var[key] = getattr(env, value)
    
    #lists for every hour
    hour_var_mapping = {'Requests':'trips_per_hour',
                        'Starvations':'total_starvations_per_hour', 
                        'Congestions':'total_congestions_per_hour',
                        'Master_num_called':'master_problem_num_times_called',
                        'Master_cpu':'master_problem_cpu_time_per_hour',
                        'Scoring_cpu':'scoring_problem_cpu_time_per_hour',
                        'Heuristic_cpu_total':'simulation_duration_per_hour'
                        }
        
    columns = ['Timestamp'] + list(fixed_var_mapping.keys())+ ['Hour']+ list(hour_var_mapping.keys())
    
    df = pd.DataFrame(columns=columns)


    #HOURLY RESULTS
    for hour in range(env.num_hours):
        hour_var_dict = {}
        hour_var_dict['Hour'] = hour+env.start_hour
        for key, value in hour_var_mapping.items():
            hour_var_dict[key] = getattr(env, value)[hour]
        hour_var_dict.update(fixed_var)
        new_row = pd.DataFrame(hour_var_dict, index=[0])    
        df = pd.concat([df, new_row],ignore_index=True)
    
    #AGGREGATE RESULTS
    hour_var_dict = {}
    hour_var_dict['Hour'] = 'Aggr.'
    for key, value in hour_var_mapping.items():
        hour_var_dict[key] = sum(getattr(env, value))
        hour_var_dict.update(fixed_var)
    new_row = pd.DataFrame(hour_var_dict, index=[0])    
    df = pd.concat([df, new_row],ignore_index=True)


    if 'Results' in writer.book.sheetnames:
        start_row = writer.sheets['Results'].max_row
        df.to_excel(writer, startrow=start_row, index=False, header=False, sheet_name='Results')
        writer.save()
    else:
        df.to_excel(writer, index=False, sheet_name='Results')
        writer.save()
    #writer.close()
