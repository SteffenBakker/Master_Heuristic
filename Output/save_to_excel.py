import pandas as pd
from datetime import datetime
from os import path


def write_excel_output(env):
    
    # Create excel writer
    #openpyxl gives some error in the encoding, but excel can recover the file. good for now
    if path.exists("Output/results.xlsx"):
        writer = pd.ExcelWriter("Output/results.xlsx",engine='openpyxl',mode='a', if_sheet_exists='overlay')  #removing engin=openpyxl leads to an error with max_row (due to xlsxwriter)
    else:
        writer = pd.ExcelWriter("Output/results.xlsx",engine='openpyxl')  
    
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    df = pd.DataFrame(columns=['Timestamp','Seed_gen_trips','Hour','Num_stations','Num_vehicles',
                               'Num_scenarios','Time_horizon' ,'Branching_constant','Total_requests', 
                                 'Starvations', 'Congestions','Strategy',
                                 'Master_num_called','Master_cpu','Scoring_cpu',
                                 'Heuristic_cpu_total'])

    for hour in range(len(env.total_starvations_per_hour)):
        new_row = pd.DataFrame({'Timestamp':dt_string,
                    'Seed_gen_trips': env.seed_generating_trips,
                   'Num_stations': len(env.stations), 
                   'Num_vehicles': len(env.vehicles), 
                   'Num_scenarios': env.scenarios, 
                   'Time_horizon': env.time_horizon,
                   'Branching_constant': env.init_branching,
                   'Hour': hour+7,
                   'Starvations': env.total_starvations_per_hour[hour], 
                   'Congestions': env.total_congestions_per_hour[hour]
                   # 'Strategy': env.strategy,
                   # 'Total_requests': env.total_gen_trips,
                   # 'Master_cpu': sum(env.master_problem_cpu_times_per_hour[hour]),
                   # 'Master_num_called': len(env.master_problem_cpu_times_per_hour[hour]),
                   # 'Scoring_cpu': sum(env.scoring_problem_cpu_times_per_hour[hour]),
                   # 'Heuristic_cpu_total': env.simulation_duration_per_hour[hour]
                   }, index=[0])    
        df = pd.concat([df, new_row],ignore_index=True)

    if 'Results' in writer.book.sheetnames:
        start_row = writer.sheets['Results'].max_row
        df.to_excel(writer, startrow=start_row, index=False, header=False, sheet_name='Results')
        writer.save()
    else:
        df.to_excel(writer, index=False, sheet_name='Results')
        writer.save()
    #writer.close()
