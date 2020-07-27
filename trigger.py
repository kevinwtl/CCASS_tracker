import pandas as pd
from bs4 import BeautifulSoup
import numpy as np
import time
import os
import win32com.client as win32

os.chdir(r'C:\\Users\\kevinwong\\Documents\\GitHub\\')

# Global variables
pd.options.display.float_format = "{:,.2f}".format
database = pd.read_csv('data' + os.sep + 'CCASS_tracker' + os.sep + 'CCASS_database.csv')
last_data_date = sorted(list(database['Date'].unique()))[-1]
outlook = win32.Dispatch('outlook.application')
mail = outlook.CreateItem(0)
participants_dict = pd.read_csv('data' + os.sep + 'CCASS_tracker' + os.sep + 'CCASS_participants.csv',header=None).set_index(0)[1].to_dict()
securities_dict = pd.read_csv('data' + os.sep + 'CCASS_tracker' + os.sep + 'securities_list.csv',header=None).set_index(0)[1].to_dict()


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
    threshold = abs(row['Cumulative Change']) * threshold_multiplier

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
    mail.Subject = 'CCASS major changes (as of ' + last_data_date + ' day end)'
    my_html = r"<p>Dear Team,</p><p>&nbsp;</p><p>Here's the summary of the recent CCASS major changes (&gt;10% change in the past 15 trading days) for stocks that we are monitoring.</p><p>&nbsp;</p>" + df.to_html(index = True) + r"<p>* Denominator of the percentages is the number of all shares/warrants/units issued in total.</p><p>&nbsp;</p><p>Regards,</p><p>Kevin Wong</p>"
    mail.HTMLBody = my_html
    mail.Display(False)


def main():

    global last_data_date, database, mail, outlook

    table = pd.DataFrame()
    for i in find_block_trader(database).index:
        table = table.append(sub_table(find_block_trader(database).iloc[i]).reset_index(drop = False))

    ## Mapping CCASS participants & Stock names
    table['Participant'] = table['CCASS ID'].map(participants_dict)
    table['Stock Name'] = table['Ticker'].map(securities_dict)

    table = table.set_index(['Ticker','Stock Name','CCASS ID','Participant','Date'])

    create_mail_draft(table)
    
    #mail.Send()

if __name__ == "__main__":
    main()