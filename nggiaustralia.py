# -*- coding: utf-8 -*-
"""
Created on Fri Mar 12 17:03:09 2021

@author: asdft
"""

import requests
import pandas as pd
import os
import datetime
from dateutil.relativedelta import relativedelta

XLS_NAME="nggi-quarterly-update-september-2020-data-sources.xlsx"
DL_NAME="https://www.industry.gov.au/sites/default/files/2021-02/nggi-quarterly-update-september-2020-data-sources.xlsx"
SHEET_NAME="Data Table 1A"

CSV_NAME="emissions_data.csv"

class emissions:
    '''
    Constants: The total carbon budget from 2013-2050 for 1.5C and 2C.
    '''
    carbon_budget_15C=7760
    carbon_budget_2C=10400

    def __init__(self):
        pass
    
    """
    Download emissions excel sheet, pick out relevant sheet and save. Create emissions dataset
    """
    @staticmethod
    def create_emissions_data(xls_name=XLS_NAME,dl_name=DL_NAME,  sheet_name=SHEET_NAME,csv_name=CSV_NAME,
                              include_LULUCF=False):
        #Download emissions dataset        
        if(not os.path.exists(xls_name)):
            print("Downloading dataset")
            resp = requests.get(dl_name)
            with open(XLS_NAME, 'wb') as output:
                output.write(resp.content)
                
        raw_data=pd.read_excel(XLS_NAME,SHEET_NAME,header=4)
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
        
        raw_data.to_csv(csv_name,index=False)
        pass
    
    @classmethod
    def load_emissions_data(cls):
        if(not os.path.exists(CSV_NAME)):
            cls.create_emissions_data()
        data=pd.read_csv(CSV_NAME)
        data["Quarter"]=pd.to_datetime(data["Quarter"]).dt.date
        return data
    
    """
    Create a carbon budget dataset.
    #n=2c/y0
    """    
    @classmethod
    def create_carbon_budget_data(cls,
                                  data, 
                                starting_date=pd.to_datetime('2013-01-01'),
                                target_budget=0,
                                target_type="1.5C"
                                     ):
        data_starting=data[data["Quarter"]>=starting_date]
        #c        
        if(target_type=="1.5C"):
            target_budget=cls.carbon_budget_15C
        elif(target_type=="2C"):
            target_budget=cls.carbon_budget_2C
        elif(target_type=="custom"):
            pass
            
        carbon_budget=target_budget-data_starting["Total (excluding LULUCF)"].sum()
        #y0
        emissions_start=data_starting["Total (excluding LULUCF)"].loc[-1]
        num_quarters=2*carbon_budget/emissions_start
        
        return cls.createLRdata(data_starting,num_quarters)
    
    """
    Create linear reduction data, seed with end value of raw dataset
    #n=2c/y0
    """
    @staticmethod
    def create_LRdata(data,num_quarters):
        
        data_LRdata=pd.DataFrame(columns = data.columns)
        data_start=data.iloc[-1,:]
        for i in range(num_quarters):    
            data_LRdata=data_LRdata.append(data_start)
            data_LRdata.iloc[-1,0]+=(i+1)*relativedelta(months=3)
            data_LRdata.iloc[-1,1:]*= 1-(i+1)/num_quarters
        
        # data['Cumulative emissions']=data["Total (excluding LULUCF)"].cumsum()
        return data.append(data_LRdata)
        
    """
    Create yearly rolling data from quarterly data 
    """
    @staticmethod
    def create_rolling_data(data):
        data_yearly_rolling=data.copy()
        for col in data.columns:
            if(pd.api.types.is_numeric_dtype( data[col].dtype )):
                data_yearly_rolling[col]=data[col].rolling(4).sum()
            else:
                data_yearly_rolling[col]=data[col]
        data_yearly_rolling=data_yearly_rolling.dropna(axis=0)
        
        #Round numeric values
        data_yearly_rolling=data_yearly_rolling.round(1)
        return data_yearly_rolling
    """
    Create cumulative data for carbon budgeting
    """
    @staticmethod
    def create_cumulative_data(data,column_name):
        return data.loc[:,column_name].cumsum()

