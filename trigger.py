import pandas as pd
from bs4 import BeautifulSoup
import numpy as np
import time
import os
import win32com.client as win32

pd.options.display.float_format = "{:,.2f}".format

database = pd.read_csv('CCASS_tracker' + os.sep + 'CCASS_database.csv')

last_data_date = sorted(list(database['Date'].unique()))[-1]

outlook = win32.Dispatch('outlook.application')

mail = outlook.CreateItem(0)


# Rolling 15 days changes > 10%
def rolling_days_changes(df, days = 15 ,threshold = 10):
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


def find_block_trader(df, days = 15 ,threshold = 10):
    date_list = sorted(list(df['Date'].unique()))[-days:]
    filtered_df = df[df.Date.isin(date_list)]
    df1 = filtered_df.groupby(['Ticker','CCASS ID'])['DoD Change'].sum().reset_index()
    df1.rename(columns = {'DoD Change':'Cumulative Change'}, inplace = True)
    df1['Date'] = last_data_date
    df1['Shareholding'] = np.nan
    df1[r'% of Total Issued Shares/Warrants/Units'] = np.nan
    df1['DoD Change'] = np.nan
    df1 = df1.set_index(['Ticker','CCASS ID'])
    df1.update(df[df['Date'] == date_list[-1]].set_index(['Ticker','CCASS ID']))
    df1 = df1[abs(df1['Cumulative Change']) > threshold]

    return df1.reset_index(drop = False)


def sub_table(row, threshold_multiplier = 0.1):
    ticker = row['Ticker']
    CCASS_ID = row['CCASS ID']
    threshold = row['Cumulative Change'] * threshold_multiplier

    df = database.groupby(['Ticker','CCASS ID']).get_group((ticker,CCASS_ID)).loc[(abs(database['DoD Change'])>threshold)].reset_index(drop = True)

    df = df.append(row)
    df = df.set_index(['Ticker','CCASS ID','Date'])

    df = df.sort_values(by = 'Date', ascending = True)

    df = df.replace(np.nan, '', regex=True) # Replace nan by blank for better formatting

    # Rename columns
    df.columns = ['Shareholding', '% of Total Issued Shares/Warrants/Units *', 'DoD Change (%) *','Cumulative Change (%) *']

    return df


def create_mail_draft(df):
    mail.To = 'jameshan@chinasilveram.com;prashantgurung@chinasilveram.com'
    mail.Subject = 'CCASS major changes (up to ' + last_data_date + ')'
    my_html = r"<p>Dear Team,</p><p>&nbsp;</p><p>Here's the summary of the recent CCASS major changes (&gt;10% change in the past 15 trading days) for stocks we are monitoring.</p><p>&nbsp;</p>" + df.to_html(index = True) + r"<p>* Denominator of the percentages is the number of all shares/warrants/units issued in total.</p><p>&nbsp;</p><p>Regards,</p><p>Kevin Wong</p>"
    mail.HTMLBody = my_html
    mail.Display(False)


def main():
    table = pd.DataFrame()
    for i in find_block_trader(database).index:
        table = table.append(sub_table(find_block_trader(database).iloc[i]).reset_index(drop = False))

    table = table.set_index(['Ticker','CCASS ID','Date'])

    create_mail_draft(table)

    mail.Send()