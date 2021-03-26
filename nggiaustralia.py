# -*- coding: utf-8 -*-
"""
Created on Fri Mar 12 17:03:09 2021

@author: asdft
"""

import requests
import pandas as pd
import os
import datetime
import math
from dateutil.relativedelta import relativedelta
import numpy as np

class emissions:
    '''
    The global carbon budget from 2013-2050 for both 1.5C and 2C have been calculated.
    1.5C: 800GtCO2
    2C: 1041GtCO2
    
    Sources used.
    Meinshausen, M., Robiou du Pont, Y. and Talberg, A. (2018) Greenhouse Gas Emissions Budgets for Victoria.
    AUSTRALIA’S PARIS AGREEMENT PATHWAYS: UPDATING THE CLIMATE CHANGE AUTHORITY’S 2014 EMISSIONS REDUCTION TARGETS, Jan 2021
    
    Mt units used throughout calculations.
    '''
    global_budget_2013to2050_15C=800000
    global_budget_2013to2050_2C=1072165
    
    # carbon_budget_15C=7760
    # carbon_budget_2C=10400
    emissions_yearly_2005=535.27
    XLS_NAME="nggi-quarterly-update-september-2020-data-sources.xlsx"
    DL_NAME="https://www.industry.gov.au/sites/default/files/2021-02/nggi-quarterly-update-september-2020-data-sources.xlsx"
    SHEET_NAME="Data Table 1A"
    FOLDER_NAME="data"
    CSV_NAME="emissions_data.csv"

    def __init__(self):
        self.data=self.load_emissions_data()
        pass
    
    """
    Download emissions excel sheet, pick out relevant sheet and save. Create emissions dataset
    """
    
    def create_emissions_data(self,
                              xls_name=XLS_NAME,
                              dl_name=DL_NAME, 
                              sheet_name=SHEET_NAME,
                              csv_name=CSV_NAME,
                              folder_name=FOLDER_NAME,
                              include_LULUCF=False):
        print("Downloading emissions data")
        if(not os.path.exists(folder_name)):
            os.mkdir(folder_name)
        #Download emissions dataset        
        if(not os.path.exists(os.path.join(folder_name,xls_name))):
            print("Downloading dataset")
            resp = requests.get(dl_name)
            with open(os.path.join(folder_name,xls_name), 'wb') as output:
                output.write(resp.content)
                
        raw_data=pd.read_excel(os.path.join(folder_name,xls_name),sheet_name,header=4)
        col_index=2
        cols=raw_data.iloc[0]
        cols_new=list(cols.index)
        cols_new[col_index:col_index+4]=cols.iloc[col_index:col_index+4]
        raw_data = raw_data.iloc[1:,:]
        raw_data.columns=cols_new
        
        raw_data.loc[:,"Year"]=raw_data.loc[:,"Year"].fillna(method="bfill")
        raw_data = raw_data.iloc[:-3,:]
        raw_data = raw_data.reset_index(drop=True)
        raw_data=raw_data.drop("Year",axis=1)
        
        raw_data["Quarter"]=pd.to_datetime(raw_data["Quarter"]).dt.date
        # raw_data=raw_data.set_index("Quarter")
        raw_data.iloc[:,1:]=raw_data.iloc[:,1:].apply(lambda x:pd.to_numeric(x))
        
        #Remove LULUCF
        if(not include_LULUCF):
            raw_data=raw_data.iloc[:,:-2]
        print("Saving processed emissions data to: " + os.path.join(folder_name,csv_name))
        raw_data.to_csv(os.path.join(folder_name,csv_name),index=False)
        pass
    
    def load_emissions_data(self,
                            csv_name=CSV_NAME,
                            folder_name=FOLDER_NAME):
        if(not os.path.exists(os.path.join(folder_name,csv_name))):
            self.create_emissions_data()
        data=pd.read_csv(os.path.join(folder_name,csv_name),parse_dates=['Quarter'])
        # data["Quarter"]=pd.to_datetime(data["Quarter"]).dt.date
        return data
    
    """
    Create a carbon budget dataset, from preset temperatures. 
    I could probably just use reduction target and use known reduction targets for temperatures but anyway.
    
    """
    def create_carbon_budget_data_from_temp(
        self,
        data, 
        target_type="1.5C",
        share_perc=0.97,
        starting_date=pd.to_datetime('2013-01-01'),
        ):
        data_starting=data.loc[:,['Quarter',"Total (excluding LULUCF)"]]
        data_starting=data_starting[data_starting["Quarter"]>=starting_date]
        cumulative_offset=data_starting["Total (excluding LULUCF)"].iloc[:-1].sum() 
        #c        
        # if(target_type=="1.5C"):
        #     target_budget=self.carbon_budget_15C
        # elif(target_type=="2C"):
        #     target_budget=self.carbon_budget_2C
        if(target_type=="1.5C"):
            target_budget=self.global_budget_2013to2050_15C*share_perc/100
        elif(target_type=="2C"):
            target_budget=self.global_budget_2013to2050_2C*share_perc/100
            
        carbon_budget=target_budget-cumulative_offset
        #y0
        emissions_start=data_starting["Total (excluding LULUCF)"].iloc[-1]
        #n=2c/y0 for linear reduction
        num_quarters=math.floor(2*carbon_budget/emissions_start)
        
        return self.create_LRdata(data_starting,num_quarters,
                                  cumulative_offset=cumulative_offset,
                                  )
    """
    Create a carbon budget from reduction targets
    """
    def create_carbon_budget_data_from_reduction_target(
            self,
            data,
            starting_date=pd.to_datetime('2013-01-01'),
            reduction_perc=28,
            reduction_date=pd.to_datetime('2030-03-01'),
            ):
        
        data_starting=data.loc[:,['Quarter',"Total (excluding LULUCF)"]]
        data_starting=data_starting[data_starting["Quarter"]>=starting_date]
        cumulative_offset=data_starting["Total (excluding LULUCF)"].iloc[:-1].sum()
        
        #Calculationg the number of quarters 
        y0=data_starting["Total (excluding LULUCF)"].iloc[-1]
        x0=data_starting["Quarter"].iloc[-1]
        y1=self.emissions_yearly_2005*(1-0.01*reduction_perc)/4
        m=(y1-y0)/((reduction_date-x0)/np.timedelta64(3, 'M'))
        num_quarters=math.floor(-y0/m)
        
        return self.create_LRdata(data_starting,num_quarters,
                                  cumulative_offset=cumulative_offset
                                  )
    """
    Create linear reduction data, seed with end value of raw dataset
    
    """
    # @staticmethod
    def create_LRdata(self,data,num_quarters,cumulative_offset=0, is_append=False):
        
        data_start=data.iloc[-1,:]
        if(num_quarters==0):
            return data_start
        
        # data_LRdata=pd.DataFrame(columns = data.columns)
        
        # data_LRdata=data_LRdata.append(data_start)
        
        #Doing this optimisation makes fair share update much snappier
        quarters=np.array([data_start['Quarter']+i*relativedelta(months=3) for i in range(num_quarters+1)])
        total=np.array([data_start["Total (excluding LULUCF)"]*(1-i/num_quarters) for i in range(num_quarters+1)])
        
        # for i in range(num_quarters):    
        #     data_LRdata=data_LRdata.append(data_start)
        #     data_LRdata.iloc[-1,0]+=(i+1)*relativedelta(months=3)
        #     data_LRdata.iloc[-1,1:]*= 1-(i+1)/num_quarters
        
        data_LRdata=pd.DataFrame({
            'Quarter':quarters,
            "Total (excluding LULUCF)":total
            })
        if(is_append):
            data_LRdata=data.append(data_LRdata)
        data_LRdata['Cumulative emissions']=data_LRdata["Total (excluding LULUCF)"].cumsum()+cumulative_offset
        return data_LRdata
        
    """
    Create yearly rolling data from quarterly data 
    """
    # @staticmethod
    def create_rolling_data(self,data):
        data_yearly_rolling=data.copy()
        
        
        for col in data_yearly_rolling.columns:
            if(pd.api.types.is_numeric_dtype( data_yearly_rolling[col].dtype )):
                data_yearly_rolling[col]=data_yearly_rolling[col].rolling(4).sum()
            else:
                data_yearly_rolling[col]=data_yearly_rolling[col]
                
        data_yearly_rolling=data_yearly_rolling.dropna(axis=0)
        
        #Round numeric values
        data_yearly_rolling=data_yearly_rolling.round(1)
        return data_yearly_rolling
    """
    Create cumulative data for carbon budgeting
    """
    # @staticmethod
    def create_cumulative_data(self,data,column_name):
        return data.loc[:,column_name].cumsum()

    # @staticmethod
    # def round_numeric_data(data,num_places=1):
        