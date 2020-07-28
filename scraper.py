import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import requests
import time
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import os
start_time = time.time()

os.chdir(r'C:\\Users\\kevinwong\\Documents\\GitHub\\')

# Global variables
try:
    database = pd.read_csv('CCASS_tracker' + os.sep + 'data' + os.sep + 'CCASS_database.csv') 
except FileNotFoundError:
    database = pd.DataFrame(columns = ['Ticker','CCASS ID','Date','Shareholding',r'% of Total Issued Shares/Warrants/Units','DoD Change'])
    
tickers = ['0024', '0412', '0456', '0556', '0997', '1166', '1563', '1600', '1608', '1862', '1962', '2014', '2060', '3836', '6828', '8047', '8078', '8086', '8422', '8501']

def scrape_single_page(ticker):
    '''Go to HKEX "CCASS Shareholding Search" and check the CCASS information of the stock on that day.'''

    ## Type in stock code and search
    browser.find_element_by_name('txtStockCode').clear()
    browser.find_element_by_name('txtStockCode').send_keys(ticker)
    browser.find_element_by_id('btnSearch').click()

    ## Get data on that page
    soup = BeautifulSoup(browser.page_source, 'lxml')
    table = soup.find('table')
    df = pd.read_html(str(table))[0][['Participant ID','Shareholding']]
    df.columns = ['CCASS ID','Shareholding']
    df['CCASS ID'] = df['CCASS ID'].str[16:]
    df['Shareholding'] = df['Shareholding'].str[14:].replace(',','',regex = True).astype(np.int64)
    issued_shares = int(browser.find_elements_by_class_name('summary-value')[0].text.replace(',',''))

    df[r'% of Total Issued Shares/Warrants/Units'] = df['Shareholding']/issued_shares * 100
    df['Ticker'] = int(ticker)
    df['Date'] = shareholding_date

    ## Put intervals in between searches to avoid being spotted as a robot
    time.sleep(3)

    return df[['Ticker','CCASS ID','Date','Shareholding',r'% of Total Issued Shares/Warrants/Units']]

def get_DoD(df):
    '''Add a column of DoD Changes (in shareholding) to the DataFrame.'''
    df = df.sort_values(['Date', 'Ticker','Shareholding'], ascending=[False, True, False]).reset_index(drop = True)


    for ticker in list(df['Ticker'].unique()):
        for participant in list(df['CCASS ID'].unique()):
            df['DoD Change'].update(df.loc[(df['Ticker'] == ticker) & (df['CCASS ID'] == participant) & (df['Date'].isin(sorted(list(df['Date'].unique()))))][r'% of Total Issued Shares/Warrants/Units'].diff(-1))
    
    # Handle first-time purchase (i.e. historical data is not available)
    for i in range(len(df[(df['DoD Change'].isnull())])):
        try:
            row = df[(df['DoD Change'].isnull())].iloc[i]
            if row['Date'] != sorted(list(df['Date'].unique()))[0]:
                index = row.name
                df.loc[index,'DoD Change'] = row[r'% of Total Issued Shares/Warrants/Units']
        except:
            pass

    return df[['Ticker','CCASS ID','Date','Shareholding',r'% of Total Issued Shares/Warrants/Units','DoD Change']]

def drop_saturdays(df):
    date_list = sorted(list(df['Date'].unique()))
    for date in date_list:
        if datetime(int(date[:4]),int(date[5:7]),int(date[8:])).isoweekday() == 6:
            df = df[~(df['Date'] == date)]
        else:
            pass
    return df

def drop_historicals(df, trailing_days = 20):
    '''Remove historical and unnecessary data.'''
    if len(list(df['Date'].unique())) > trailing_days:
        date_list = sorted(list(df['Date'].unique()))[-trailing_days:]
        df = df.drop(list(df[~df.Date.isin(date_list)].index))
    else:
        pass
    return df

def main():

    global database, browser, shareholding_date

    ## Get the browser set up
    try:
        test = browser.current_url
        if browser.current_url[:8] != 'https://':
            browser.get(r'https://www.hkexnews.hk/sdw/search/searchsdw.aspx')
    except:
        browser = webdriver.Chrome(ChromeDriverManager().install()) # Download chromdriver
        browser.get(r'https://www.hkexnews.hk/sdw/search/searchsdw.aspx')

    ## Check if the program was run today, or it's Saturday
    shareholding_date = browser.find_element_by_name('txtShareholdingDate').get_attribute('value')
    date_list = sorted(list(database['Date'].unique()))
    duplication_checker = shareholding_date in date_list or datetime(int(shareholding_date[:4]),int(shareholding_date[5:7]),int(shareholding_date[8:])).isoweekday() == 6

    if duplication_checker == True:
        browser.close()
        input("Database is already up to date. Press 'enter' to exit.")
    else:
        ## Perform scraping
        for ticker in tickers:
            database = database.append(scrape_single_page(ticker), sort=True).reset_index(drop = True)

        #command = input("Data on requested date has been scraped. Input 'g' to scrape another date or simply press enter to exit.")
        browser.close()

        ## Drop unnamed participants
        database.dropna(subset = ['CCASS ID'],inplace = True)

        ## Drop duplicates in case the program was ran more than once a day
        #database = database.drop_duplicates(subset = ['Ticker','CCASS ID','Date'])

        ## Drop Saturdays & historical data, then calculate DoD change 
        database = drop_saturdays(database)
        database = drop_historicals(database)
        database = get_DoD(database)

        ## Sort and export the database
        database.to_csv('CCASS_tracker' + os.sep + 'data' + os.sep + 'CCASS_database.csv', index = False)

        print("--- %s seconds ---" % (time.time() - start_time))
        input("Database updated. Press 'enter' to exit.")


if __name__ == "__main__":
    main()