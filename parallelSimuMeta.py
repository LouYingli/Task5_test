   # -*- coding: utf-8 -*-
"""
Created on Tue Nov  7 10:50:32 2017

@author: yunyangye
"""

import multiprocessing as mp
import time
import math
import csv
import subprocess
from shutil import copyfile,rmtree
import pandas as pd
import os.path

######################################################
#run models and get the results in parallel
######################################################

######################################################
#run models
######################################################
#climate is the climate zone; weather file name is [climate].epw and baseline model file name is CZ[climate].osm
#param_values is the name of measures, name of arguments and values are used in each case (two-dimension list)
#num_model is the NO. of the model
#round_num is the number of the round times


def modifyIDF(climate,param_name,param_value,order_model):
    f = open('./Model/'+climate+'.idf','rb')
    lines=f.readlines()
    f.close()
    
    newlines = []
    modify_lines =[]
    modify_lines_id =[]
    modify_id=[]
    for i in range(2):
        intensity= float(param_value[i])*float(param_value[2])
        id_start = [] #!- Time 1
        id_end = [] #line after final schedule value
        for j in range(len(lines)):
            if lines[j].split(',')[0].replace(' ','').lower() == 'schedule:day:interval' and param_name[i] in lines[j+1].split(',')[0].replace(' ',''):
                id_start.append(j+4)
                for k in range(j+4,j+204):
                    if lines[k].split(',')[0].replace(' ','') == '24:00':
                        id_end.append(k+2)
                        break

        for i in range(len(id_start)):
            for j in range(id_start[i]+1,id_end[i],2):
                if lines[j-1].split(',')[0].replace(' ','') != '24:00':
                    value_old= float(lines[j].split(',')[0].replace(' ',''))
                    value_new = value_old*intensity
                    if (lines[id_start[i]-2].split(',')[0] == '  Fractional' or lines[id_start[i]-2].split(',')[0] == '  OnOff') and value_new > 1.0:
                        value_new = 1.000
                    modify_lines.append(lines[j].replace(lines[j].split(',')[0].replace(' ',''),str(value_new)))
                    modify_id.append(j)
                if lines[j-1].split(',')[0].replace(' ','') == '24:00':
                    value_old= float(lines[j].split(';')[0].replace(' ',''))
                    value_new = value_old*intensity
                    if (lines[id_start[i]-2].split(',')[0] == '  Fractional' or lines[id_start[i]-2].split(',')[0] == '  OnOff') and value_new > 1.0:
                        value_new = 1.000
                    modify_lines.append(lines[j].replace(lines[j].split(';')[0].replace(' ',''),str(value_new)))
                    modify_id.append(j)
                    
    for i in range(2,len(param_name)):
        intensity= float(param_value[i])
        id_start = [] #!- Time 1
        id_end = [] #line after final schedule value
        for j in range(len(lines)):
            if lines[j].split(',')[0].replace(' ','').lower() == 'schedule:day:interval' and param_name[i] in lines[j+1].split(',')[0].replace(' ',''):
                id_start.append(j+4)
                for k in range(j+4,j+204):
                    if lines[k].split(',')[0].replace(' ','') == '24:00':
                        id_end.append(k+2)
                        break

        for i in range(len(id_start)):
            for j in range(id_start[i]+1,id_end[i],2):
                if lines[j-1].split(',')[0].replace(' ','') != '24:00':
                    value_old= float(lines[j].split(',')[0].replace(' ',''))
                    value_new = value_old*intensity
                    if (lines[id_start[i]-2].split(',')[0] == '  Fractional' or lines[id_start[i]-2].split(',')[0] == '  OnOff') and value_new > 1.0:
                        value_new = 1.000
                    modify_lines.append(lines[j].replace(lines[j].split(',')[0].replace(' ',''),str(value_new)))
                    modify_id.append(j)
                if lines[j-1].split(',')[0].replace(' ','') == '24:00':
                    value_old= float(lines[j].split(';')[0].replace(' ',''))
                    value_new = value_old*intensity
                    if (lines[id_start[i]-2].split(',')[0] == '  Fractional' or lines[id_start[i]-2].split(',')[0] == '  OnOff') and value_new > 1.0:
                        value_new = 1.000
                    modify_lines.append(lines[j].replace(lines[j].split(';')[0].replace(' ',''),str(value_new)))
                    modify_id.append(j)  
                    
    for i in range(len(lines)):
        if i in modify_id:
            modify_lines_id = modify_id.index(i)
            newlines.append(modify_lines[modify_lines_id])
        else:
            newlines.append(lines[i])
    f = open('./Model/update_models/'+climate+str(order_model)+'.idf','w')
    for i in range(len(newlines)):
        f.writelines(newlines[i])
    f.close()       
    return str(order_model)+'.idf'     


######################################################
#2.modify IDF file and run model, get model output (site EUI)
#run models and read htm file to get site EUI and source EUI
#save the model input and output into './results/energy_data.csv'
def runModel(climate,eplus_path,weather_file,eplus_file,param_value,output_file,output):
    #run model
    df = subprocess.Popen([eplus_path, "-w",weather_file, "-d",'./results/'+climate+output_file+eplus_file.split('.')[0], "-r", './Model/update_models/'+climate+eplus_file],stdout=subprocess.PIPE)
    output_eplus, err = df.communicate()
    print(output_eplus.decode('utf_8'))
    if not err is None:
        print(err.decode('utf_8'))
        
    if os.path.isfile('./results/'+climate+output_file+eplus_file.split('.')[0]+'/eplustbl.htm'):
         #get model input
        data = []
        data.append(eplus_file.split('.')[0]) #the name of idf file
        data.append(climate) #the name of climate
        for j in range(len(param_value)):
            data.append(param_value[j])
        
        #get output(site EUI and source EUI)
        dfs = pd.read_html('./results/'+climate+output_file+eplus_file.split('.')[0]+'/eplustbl.htm')
        df1 = dfs[0]
        df2 = dfs[2]
        site_energy = float(df1.loc[1][1])
        source_energy = float(df1.loc[3][1])
        area = float(df2.loc[1][1])
        data.append(str(0.088055066*1000*site_energy/area)) #get site EUI (KBtu/ft2)
        data.append(str(0.088055066*1000*source_energy/area)) #get source EUI (KBtu/ft2)
   
    
        #record the data in the './results/energy_data.csv'
        with open('./results/energy_data.csv', 'ab') as csvfile:
            energy_data = csv.writer(csvfile, delimiter=',')
            energy_data.writerow(data)

    else:
        with open('./results/energy_data_err.csv', 'ab') as csvfile:
            energy_data_err = csv.writer(csvfile, delimiter=',')
            energy_data_err.writerow(climate+eplus_file)
            
    rmtree('./results/'+climate+output_file+eplus_file.split('.')[0])
    #rmtree('./Model/update_models/'+climate+eplus_file)
    output.put([])

#################################################################################
#2.modify IDF file and run model, get model output (site EUI)
#run models in parallel for sensitivity analysis
#Climate is the list of climate zone; weather file name is [climate].epw and baseline model file name is CZ[climate].osm
#round_num is the number of the round times
def parallelSimu(climate,round_num):
    #record the start time
    start = time.time()
    eplus_path ='energyplus'
    weather_file ='./Model/'+climate+'.epw'
    output_file = 'temp'
    # get parameter name and parameter value    
    f = open('./variable.csv')
    lines = f.readlines()
    f.close()
    param_name = []
    param_value = []
    for i in range(1,len(lines)):
        param_name.append(lines[i].split(',')[0])
        
    with open('./results/samples/param_values_'+climate+'.csv', 'rb') as csvfile:
        data = csv.reader(csvfile, delimiter=',')
        for row in data:
            param_value.append(row)

    # modify the idf file
    order_idf = 1
    for i in range(len(param_value)):
        modifyIDF(climate,param_name,param_value[i],order_idf)
        order_idf += 1
   
    
    # idf file name    
    order_model = 1    
    eplus_files = []
    for i in range(len(param_value)):
        eplus_files.append(str(order_model)+'.idf')
        order_model +=1
    
            
    #multi-processing
    output = mp.Queue()
    processes = [mp.Process(target=runModel,args=(climate,eplus_path,weather_file,eplus_files[i],param_value[i],output_file,output)) for i in range(len(eplus_files))]
    
    #count the number of cpu
    cpu = mp.cpu_count()#record the results including inputs and outputs
    print cpu
    
    model_results = []
    
    run_times = math.floor(len(processes)/cpu)
    if run_times > 0:
        for i in range(int(run_times)):
            for p in processes[i*int(cpu):(i+1)*int(cpu)]:
                p.start()
            
            for p in processes[i*int(cpu):(i+1)*int(cpu)]:
                p.join()
    
            #get the outputs
            temp = [output.get() for p in processes[i*int(cpu):(i+1)*int(cpu)]]
            
            for x in temp:
                model_results.append(x)
    
    for p in processes[int(run_times)*int(cpu):len(processes)]:
        p.start()
            
    for p in processes[int(run_times)*int(cpu):len(processes)]:
        p.join()    
        
    #get the outputs
    temp = [output.get() for p in processes[int(run_times)*int(cpu):len(processes)]]
    for x in temp:
        model_results.append(x)
            
    #record the end time
    end = time.time()
    
    return model_results,end-start