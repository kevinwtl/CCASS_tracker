import pandas as pd
from bs4 import BeautifulSoup
import requests
import numpy as np
import time
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
start_time = time.time()

ticker = '1810'

browser = webdriver.Chrome(ChromeDriverManager().install()) # Download chromdriver
browser.implicitly_wait(3)

def get_issue_id(ticker):
    browser.get(r'https://webb-site.com/dbpub/orgdata.asp?code=' + ticker + '&Submit=current')
    browser.find_element_by_link_text('CCASS').click()
    issue_id = browser.current_url[-5:]
    return issue_id

def CCASS_scrape(issue_id, queries):
    # Get list of dates
    url = r'https://webb-site.com/ccass/ctothist.asp?issue=' + issue_id
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text,'lxml')
    table = soup.find_all('table')[1]

    dates = pd.read_html(str(table))[0].Holdingdate.tolist()

    my_list = []

    # Scrape through all pages
    for date in dates[:queries]:
        resp = browser.get(r'https://webb-site.com/ccass/chldchg.asp?issue=' + issue_id + '&d=' + date + '&sort=holddn')
        soup = BeautifulSoup(browser.page_source,'lxml')
        table = soup.find_all('table')[1]

        my_list.append(pd.read_html(str(table))[0][:20][['CCASS ID','Holding']].set_index('CCASS ID')['Holding'].to_dict())

    df = pd.DataFrame(my_list, index = dates[:queries]) 

    return df

df = CCASS_scrape(issue_id = get_issue_id(ticker), queries = 30)

# Mapping CCASS participants
participants = pd.read_csv('/Users/tinglam/Documents/GitHub/CCASS_tracker/CCASS_participants.csv',header=None).set_index(0)[1].to_dict()
df = df.rename(columns = participants)

# Export results
df.to_csv(ticker + '_CCASS.csv')

browser.close()

print("{} days of CCASS holdings scraped.".format(len(df)))
print("--- %s seconds ---" % (time.time() - start_time))
