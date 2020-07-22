import pandas as pd
from bs4 import BeautifulSoup
import requests
import numpy as np
import time
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

df = pd.read_csv(r'C:\Users\kevinwong\Documents\GitHub\CCASS_tracker\CCASS_database.csv')

df[('Ticker' == 9988)].groupby('Date').sum()

df.groupby(['Ticker','CCASS ID'])['DoD Change'].sum()

df.to_csv(r'C:\Users\kevinwong\Documents\GitHub\CCASS_tracker\CCASS_database.csv', index = False)

len(list(df['Date'].unique()))