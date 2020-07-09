import pandas as pd
from bs4 import BeautifulSoup
import requests
import numpy as np
import time
start_time = time.time()

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
        resp = requests.get(r'https://webb-site.com/ccass/chldchg.asp?issue=' + issue_id + '&d=' + date + '&sort=holddn')
        soup = BeautifulSoup(resp.text,'lxml')
        table = soup.find_all('table')[1]

        my_list.append(pd.read_html(str(table))[0][:20][['CCASS ID','Holding']].set_index('CCASS ID')['Holding'].to_dict())



    df = pd.DataFrame(my_list, index = dates[:queries]) 

    return df

df = CCASS_scrape(issue_id = '26628', queries = 20)

# Mapping CCASS participants
participants = pd.read_csv('/Users/tinglam/Documents/GitHub/CCASS_tracker/CCASS_participants.csv',header=None).set_index(0)[1].to_dict()
df = df.rename(columns = participants)

# Export results
df.to_csv('CCASS.csv')

print("{} days of CCASS holdings scraped.".format(len(df)))
print("--- %s seconds ---" % (time.time() - start_time))
