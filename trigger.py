import pandas as pd
from bs4 import BeautifulSoup
import numpy as np
import time
import os
import win32com.client as win32

pd.options.display.float_format = "{:,.2f}".format

df = pd.read_csv('CCASS_tracker' + os.sep + 'CCASS_database.csv')

# Rolling 15 days changes > 10%
def rolling_days_changes(df,days = 15 ,threshold = 1):
    '''Calculate rolling days changes in total CCASS holdings.'''
    date_list = sorted(list(df['Date'].unique()))[-days:]
    filtered_df = df[df.Date.isin(date_list)]
    df1 = filtered_df.groupby(['Ticker','CCASS ID'])['DoD Change'].sum().reset_index()
    df1.rename(columns = {'DoD Change':'Rolling ' + str(days) + ' day(s) Net Change (%) *'}, inplace = True)
    df1 = df1[abs(df1['Rolling ' + str(days) + ' day(s) Net Change (%) *']) > threshold]

    if len(df1) > 0:
        ## Mapping CCASS participants
        participants_dict = pd.read_csv('CCASS_tracker' + os.sep + 'CCASS_participants.csv',header=None).set_index(0)[1].to_dict()
        df1['Participant'] = df1['CCASS ID'].map(participants_dict)

        ## Mapping Stock names
        securities_dict = pd.read_csv('CCASS_tracker' + os.sep + 'securities_list.csv',header=None).set_index(0)[1].to_dict()
        df1['Stock Name'] = df1['Ticker'].map(securities_dict)

        ## Display current holdings
        df1['Shareholding'] = np.nan
        df1[r'% of Total Issued Shares/Warrants/Units'] = np.nan
        df1 = df1.set_index(['Ticker','CCASS ID'])
        df1.update(df[df['Date'] == date_list[-1]].set_index(['Ticker','CCASS ID']))

        ## Rename for easy understanding
        df1['Current Shareholding'] = df1['Shareholding']
        df1[r'Shares in Issued Total (%) *'] = df1[r'% of Total Issued Shares/Warrants/Units']

        return df1.reset_index()[['Ticker','Stock Name','CCASS ID','Participant','Rolling ' + str(days) + ' day(s) Net Change (%) *','Current Shareholding', r'Shares in Issued Total (%) *']]
    else:
        pass

# Test
#rolling_days_changes(df)

outlook = win32.Dispatch('outlook.application')
mail = outlook.CreateItem(0)
mail.To = 'jameshan@chinasilveram.com'
mail.Subject = 'Testing -- CCASS big moves'
my_html = r"<p>Dear Team,</p><p>&nbsp;</p><p>Here's the summary of the CCASS big moves (&gt;1% change in the recent 15 trading days) recently.</p><p>&nbsp;</p>" + rolling_days_changes(df).to_html(index = False) + r"<p>* Denominator of the percentages is the number of all shares/warrants/units issued in total.</p><p>&nbsp;</p><p>Regards,</p><p>Kevin Wong</p>"
mail.HTMLBody = my_html
mail.Display(False)
#mail.Send()