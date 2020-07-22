import pandas as pd
from bs4 import BeautifulSoup
import requests
import time
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import win32com.client as win32
start_time = time.time()

tickers = ['9988','0700','3690','1810']

def CCASS_scraper(tickers):

    ## Import existing CCASS database
    df = pd.read_csv(r'C:\Users\kevinwong\Documents\GitHub\CCASS_tracker\CCASS_database.csv') 

    browser = webdriver.Chrome(ChromeDriverManager().install()) # Download chromdriver
    browser.implicitly_wait(3)
    browser.get(r'https://www.hkexnews.hk/sdw/search/searchsdw.aspx')

    def single_page(ticker):
            browser.find_element_by_name('txtStockCode').clear()
            browser.find_element_by_name('txtStockCode').send_keys(ticker)
            browser.find_element_by_id('btnSearch').click()
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

            time.sleep(3)

            return df

    ## Perform scraping
    for ticker in tickers:
        df = df.append(single_page(ticker))

    ## Drop duplicates in case the program is ran more than once a day
    df = df.drop_duplicates()

    ## Calculate the DoD Changes in shareholding
    for ticker in list(df['Ticker'].unique()):
        for participant in list(df['CCASS ID'].unique()):
            df['DoD Change'].update(df.loc[(df['Ticker'] == ticker) & (df['CCASS ID'] == participant)][r'% of Total Issued Shares/Warrants/Units'].diff(-1))

    ## Keep only data from 15 trading days ago
    if len(list(df['Date'].unique())) > 15:
        date_list = sorted(list(df['Date'].unique()))[-15:]
        df = df.drop(list(df[~df.Date.isin(date_list)].index))

    df.to_csv('CCASS_tracker\CCASS_database.csv', index = False)

    browser.close()

    print("--- %s seconds ---" % (time.time() - start_time))

CCASS_scraper(tickers)
