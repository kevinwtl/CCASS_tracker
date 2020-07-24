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


#my_path = '/Users/tinglam/Documents/GitHub'
my_path = ''
tickers = ['0024', '0412', '0456', '0556', '0997', '1166', '1563', '1600', '1608', '1862', '1962', '2014', '2060', '3836', '6828', '8047', '8078', '8086', '8422', '8501']

def scrape_single_page(ticker):
    '''Go to HKEX "CCASS Shareholding Search" and check the CCASS information of the stock on that day.'''

    global browser

    ## Get the browser set up
    try:
        test = browser.current_url
        if browser.current_url[:8] != 'https://':
            browser.get(r'https://www.hkexnews.hk/sdw/search/searchsdw.aspx')
    except:
        browser = webdriver.Chrome(ChromeDriverManager().install()) # Download chromdriver
        browser.get(r'https://www.hkexnews.hk/sdw/search/searchsdw.aspx')

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
    shareholding_date = browser.find_element_by_name('txtShareholdingDate').get_attribute('value')
    df['Ticker'] = ticker
    df['Date'] = shareholding_date

    ## Put intervals in between searches to avoid being spotted as a robot
    time.sleep(3)

    return df[['Ticker','CCASS ID','Date','Shareholding',r'% of Total Issued Shares/Warrants/Units']]

def get_DoD(df):
    '''Add a column of DoD Changes (in shareholding) to the DataFrame.'''
    df = df.sort_values(['Date', 'Ticker','Shareholding'], ascending=[False, True, False]).reset_index(drop = True)
    for ticker in list(df['Ticker'].unique()):
        for participant in list(df['CCASS ID'].unique()):
            df['DoD Change'].update(df.loc[(df['Ticker'] == ticker) & (df['CCASS ID'] == participant) & (df['Date'].isin(sorted(list(df['Date'].unique()))[-4:]))][r'% of Total Issued Shares/Warrants/Units'].diff(-1))
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
    ## Import existing CCASS database
    try:
        df = pd.read_csv('CCASS_tracker' + os.sep + 'CCASS_database.csv') 
    except FileNotFoundError:
        df = pd.DataFrame(columns = ['Ticker','CCASS ID','Date','Shareholding',r'% of Total Issued Shares/Warrants/Units','DoD Change'])

    ## Perform scraping
    for ticker in tickers:
        df = df.append(scrape_single_page(ticker), sort=True).reset_index(drop = True)

    browser.close()

    ## Drop duplicates in case the program was ran more than once a day
    df = df.drop_duplicates(subset = ['Ticker','CCASS ID','Date'])

    ## Drop Saturdays & historical data, then calculate DoD change 
    df = drop_saturdays(df)
    df = drop_historicals(df)
    df = get_DoD(df)

    ## Sort and export the database
    df.to_csv('CCASS_tracker' + os.sep + 'CCASS_database.csv', index = False)

    print("--- %s seconds ---" % (time.time() - start_time))

if __name__ == "__main__":
    main()