import pandas as pd
from bs4 import BeautifulSoup
import requests
import numpy as np
import time
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import win32com.client as win32


df = pd.read_csv('CCASS_tracker\CCASS_database.csv')

# Rolling 15 days changes > 10%
def rolling_days_changes(days,threshold):
    date_list = sorted(list(df['Date'].unique()))[-days:]
    filtered_df = df[df.Date.isin(date_list)]
    df1 = filtered_df.groupby(['Ticker','CCASS ID'])['DoD Change'].sum().reset_index()
    df1.rename(columns = {'DoD Change':'Rolling ' + str(days) + ' day(s) Net Change (%) *'}, inplace = True)
    df1 = df1[abs(df1['Rolling ' + str(days) + ' day(s) Net Change (%) *']) > threshold]

    ## Mapping CCASS participants
    participants_dict = pd.read_csv('CCASS_tracker\CCASS_participants.csv',header=None).set_index(0)[1].to_dict()
    df1['Participant'] = df1['CCASS ID'].map(participants_dict)

    ## Mapping CCASS participants
    securities_dict = pd.read_csv('CCASS_tracker\securities_list.csv',header=None).set_index(0)[1].to_dict()
    df1['Stock Name'] = df1['Ticker'].map(securities_dict)

    ## Display current holdings
    df1['Current Shareholding'] = df['Shareholding']
    
    ## 
    df1[r'Weight in Issued Shares (%) *'] = df[r'% of Total Issued Shares/Warrants/Units']

    return df1[['Ticker','Stock Name','CCASS ID','Participant','Rolling ' + str(days) + ' day(s) Net Change (%) *','Current Shareholding', r'Weight in Issued Shares (%) *']]


outlook = win32.Dispatch('outlook.application')
mail = outlook.CreateItem(0)
mail.To = 'jameshan@chinasilveram.com'
mail.Subject = 'Testing -- CCASS big moves'
my_html = r"<p>Dear Team,</p><p>&nbsp;</p><p>Here's the summary of the CCASS big moves (&gt;0.4% change in the recent 10 trading days) recently.</p><p>&nbsp;</p>" + rolling_days_changes(10,0.4).to_html(index = False) + r"<p>* Denominator of the percentages is the number of all shares/warrants/units issued in total.</p><p>&nbsp;</p><p>Regards,</p><p>Kevin Wong</p>"
mail.HTMLBody = my_html
mail.Display(False)
#mail.Send()