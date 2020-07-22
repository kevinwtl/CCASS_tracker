import pandas as pd
from bs4 import BeautifulSoup
import requests
import time
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import os
start_time = time.time()

tickers = ['9988','0700','3690','1810']

def scrape_single_page(ticker):
    '''Go to HKEX "CCASS Shareholding Search" and check the CCASS information of the stock on that day.'''

    global browser

    ## Get the browser set up
    try:
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
    df = pd.read_html(str(table))[0][['Participant ID','Shareholding',r'% of the total number of Issued Shares/ Warrants/ Units']]
    df.columns = ['CCASS ID','Shareholding',r'% of Total Issued Shares/Warrants/Units']
    df['CCASS ID'] = df['CCASS ID'].str[16:]
    df['Shareholding'] = df['Shareholding'].str[14:]
    df[r'% of Total Issued Shares/Warrants/Units'] = df[r'% of Total Issued Shares/Warrants/Units'].str[57:-1].astype(float)
    shareholding_date = browser.find_element_by_name('txtShareholdingDate').get_attribute('value')
    df['Ticker'] = ticker
    df['Date'] = shareholding_date

    ## Put intervals in between searches to avoid being spotted as a robot
    time.sleep(3)

    return df[['Ticker','CCASS ID','Date','Shareholding',r'% of Total Issued Shares/Warrants/Units']]

def get_DoD(df):
    '''Add a column of DoD Changes (in shareholding) to the DataFrame.'''
    for ticker in list(df['Ticker'].unique()):
        for participant in list(df['CCASS ID'].unique()):
            df['DoD Change'].update(df.loc[(df['Ticker'] == ticker) & (df['CCASS ID'] == participant)][r'% of Total Issued Shares/Warrants/Units'].diff(-1))
    return df[['Ticker','CCASS ID','Date','Shareholding',r'% of Total Issued Shares/Warrants/Units','DoD Change']]

def drop_historicals(df, trailing_days = 15):
    '''Remove historical and unnecessary data.'''
    if len(list(df['Date'].unique())) > trailing_days:
        date_list = sorted(list(df['Date'].unique()))[-trailing_days:]
        df = df.drop(list(df[~df.Date.isin(date_list)].index))
    return df

def main():

    ## Import existing CCASS database
    df = pd.read_csv('CCASS_tracker' + os.sep + 'CCASS_database.csv') 

    ## Perform scraping
    for ticker in tickers:
        df = df.append(scrape_single_page(ticker), sort = True)

    ## Drop duplicates in case the program was ran more than once a day
    df = df.drop_duplicates()

    ## Calculate DoD change and drop historical data
    df = get_DoD(df)
    df = drop_historicals(df)

    ## Save and export the database
    df.to_csv('CCASS_tracker' + os.sep + 'CCASS_database.csv', index = False)

    browser.close()

    print("--- %s seconds ---" % (time.time() - start_time))

if __name__ == "__main__":
    main()
