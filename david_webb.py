import pandas as pd
from bs4 import BeautifulSoup
import requests
import numpy as np
import time
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from imagetyperzapi3.imagetyperzapi import ImageTyperzAPI
start_time = time.time()

tickers = ['9988','0700','3690','1810']

browser = webdriver.Chrome(ChromeDriverManager().install()) # Download chromdriver
browser.implicitly_wait(3)

def get_issue_id(ticker):
    browser.get(r'https://webb-site.com/dbpub/orgdata.asp?code=' + ticker + '&Submit=current')
    browser.find_element_by_link_text('CCASS').click()
    issue_id = browser.current_url[-5:]
    return issue_id

def reCAPTCHA_solver():
    time.sleep(2)
    # init imagetyperz api obj
    API_KEY = r'881830E389FA4DFFBD05626C361688DC'
    ita = ImageTyperzAPI(API_KEY)
    # get and print account balance  
    balance = ita.account_balance()
    print('Balance: {}'.format(balance))

    if float(balance[1:]) <= 6:
        exit("Below funds limit! Exiting.")

    p = {}

    p['page_url'] = browser.current_url
    p['sitekey'] = browser.find_element_by_xpath("//*[@data-sitekey]").get_attribute("data-sitekey")

    while True:
        try:
            captcha_id = ita.submit_recaptcha(p)
            break
        except Exception as e:
            if e == "LIMIT_EXCEED":
                sleep(15) # try again later
            elif e:
                break

    while ita.in_progress():
        time.sleep(10)

    recaptcha_response = ita.retrieve_recaptcha(captcha_id)           # captcha_id is optional, if not given, will use last captcha id submited
    print('Recaptcha response: {}'.format(recaptcha_response))         # print google response
    browser.execute_script("document.getElementById('g-recaptcha-response').innerHTML = '"+recaptcha_response+"';")

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

        try:
            browser.find_element_by_xpath("//*[@data-sitekey]")
            captcha = True
        except:
            captcha = False

        if captcha == False:
            table = soup.find_all('table')[1]
            my_list.append(pd.read_html(str(table))[0][:20][['CCASS ID','Holding']].set_index('CCASS ID')['Holding'].to_dict())
        else:
            reCAPTCHA_solver()
            table = soup.find_all('table')[1]
            my_list.append(pd.read_html(str(table))[0][:20][['CCASS ID','Holding']].set_index('CCASS ID')['Holding'].to_dict())

        time.sleep(2)


    df = pd.DataFrame(my_list, index = dates[:queries]) 

    return df

#CCASS_1810 = CCASS_scrape(issue_id = get_issue_id('1810'), queries = 10)

my_dictionary = dict()
for ticker in tickers:
    my_dictionary['CCASS_{}'.format(ticker)] = CCASS_scrape(issue_id = get_issue_id(ticker), queries = 5)

####
# Mapping CCASS participants
participants = pd.read_csv('CCASS_tracker\CCASS_participants.csv',header=None).set_index(0)[1].to_dict()
df = df.rename(columns = participants)

# Export results
df.to_csv(ticker + '_CCASS.csv')

browser.close()

print("{} days of CCASS holdings scraped.".format(len(df)))
print("--- %s seconds ---" % (time.time() - start_time))



    