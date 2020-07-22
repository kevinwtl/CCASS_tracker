import pandas as pd
from bs4 import BeautifulSoup
import requests
import numpy as np
import time
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
start_time = time.time()

tickers = ['9988','0700','3690','1810']

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
    df.columns = ['CCASS ID','Shareholding',r'% of total']
    df['CCASS ID'] = df['CCASS ID'].str[16:]
    df['Shareholding'] = df['Shareholding'].str[14:]
    df[r'% of total'] = df[r'% of total'].str[57:]
    shareholding_date = browser.find_element_by_name('txtShareholdingDate').get_attribute('value')
    df['Ticker'] = ticker
    df['Date'] = shareholding_date

    df.set_index(['Ticker','CCASS ID','Date'], inplace=True)

    time.sleep(3)
    #df.set_index('CCASS ID', inplace=True)

    return df

df = pd.read_csv(r'C:\Users\kevinwong\Documents\GitHub\CCASS_tracker\CCASS_database.csv',index_col=['Ticker','CCASS ID','Date'])

for ticker in tickers:
    df = df.append(single_page(ticker))

df = df.drop_duplicates()

df.to_csv(r'C:\Users\kevinwong\Documents\GitHub\CCASS_tracker\CCASS_database.csv')

browser.close()

print("--- %s seconds ---" % (time.time() - start_time))