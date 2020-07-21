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
browser.get(r''https://www.hkexnews.hk/sdw/search/searchsdw.aspx'')
browser.find_element_by_name('txtStockCode').send_keys(ticker)
browser.find_element_by_id('btnSearch').click()
soup = BeautifulSoup(browser.page_source, 'lxml')

table = soup.find('table')
pd.read_html(str(table))



browser.find_element_by_xpath('//*[@id="txtShareholdingDate"]').click()
browser.find_elements_by