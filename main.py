import pandas as pd
from bs4 import BeautifulSoup
import requests
import numpy as np
import matplotlib.pyplot as plt




url = r'https://webb-site.com/ccass/ctothist.asp?issue=26628'

# Get list of dates
resp = requests.get(url)
soup = BeautifulSoup(resp.text,'lxml')
table = soup.find_all('table')[1]

dates = pd.read_html(str(table))[0].Holdingdate.tolist()

issue = '26628'
queries = 10

my_list = []

for date in dates[:queries]:
    #resp = requests.get(r'https://webb-site.com/ccass/' + link + r'&sort=holddn')
    resp = requests.get(r'https://webb-site.com/ccass/chldchg.asp?issue=' + issue + '&d=' + date + '&sort=holddn')
    soup = BeautifulSoup(resp.text,'lxml')
    table = soup.find_all('table')[1]

    my_list.append(pd.read_html(str(table))[0][:100][['CCASS ID','Holding']].set_index('CCASS ID')['Holding'].to_dict())



df = pd.DataFrame(my_list, index = dates[:queries]).iloc[:,:9] #.interpolate(method = 'nearest')
df = df.interpolate(method='linear').ffill().bfill().reset_index().iloc[::-1]

# Initialize the figure
plt.style.use('seaborn-darkgrid')

# create a color palette
palette = plt.get_cmap('Set1')

# multiple line plot
num=0
for column in df.drop('index', axis=1):
    num+=1

    # Find the right spot on the plot
    plt.subplot(3,3, num)

    # plot every groups, but discreet
    for v in df.drop('index', axis=1):
        plt.plot(df['index'], df[v], marker='', color='grey', linewidth=0.6, alpha=0.3)

    # Plot the lineplot
    plt.plot(df['index'], df[column], marker='', color=palette(num), linewidth=2.4, alpha=0.9, label=column)

    # Same limits for everybody!
    #plt.xlim(0,10)
    #plt.ylim(-2,22)

    # Not ticks everywhere
    if num in range(7) :
        plt.tick_params(labelbottom='off')
    if num not in [1,4,7] :
        plt.tick_params(labelleft='off')

    # Add title
    plt.title(column, loc='left', fontsize=12, fontweight=0, color=palette(num) )

# general title
plt.suptitle("CCASS Status", fontsize=13, fontweight=0, color='black', style='italic', y=1.02)

# Axis title
plt.text(1, 0.02, 'Time', ha='center', va='center')
plt.text(0.06, 0.5, 'Shares', ha='center', va='center', rotation='vertical')

plt.show()