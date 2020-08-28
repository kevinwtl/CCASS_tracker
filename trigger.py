import pandas as pd
from bs4 import BeautifulSoup
import numpy as np
import time
import os
import matplotlib.pyplot as plt
import win32com.client as win32

os.chdir(r'C:\\Users\\kevinwong\\Documents\\GitHub')

# Global variables
pd.options.display.float_format = "{:,.2f}".format
database = pd.read_csv('CCASS_tracker' + os.sep + 'data' + os.sep + 'CCASS_database.csv')
last_data_date = sorted(list(database['Date'].unique()))[-1]
outlook = win32.Dispatch('outlook.application')
mail = outlook.CreateItem(0)
participants_dict = pd.read_csv('CCASS_tracker' + os.sep + 'data' + os.sep + 'CCASS_participants.csv',header=None).set_index(0)[1].to_dict()
securities_dict = pd.read_csv('CCASS_tracker' + os.sep + 'data' + os.sep + 'securities_list.csv',header=None).set_index(0)[1].to_dict()


def block_trade_query(df, days = 15 ,threshold = 10):

    date_list = sorted(list(df['Date'].unique()))[-days:]
    filtered_df = df[df.Date.isin(date_list)]
    df1 = filtered_df.groupby(['Ticker','CCASS ID'])['DoD Change (%) *'].sum().reset_index()
    df1.rename(columns = {'DoD Change (%) *':'Net Cumulative Change (%) *'}, inplace = True)
    df1 = df1[abs(df1['Net Cumulative Change (%) *']) > threshold]
    df1['Date'] = last_data_date
    df1['Shareholding'] = np.nan
    df1[r'% of Issued Shares *'] = np.nan
    df1['DoD Change (%) *'] = np.nan
    df1 = df1.set_index(['Ticker','CCASS ID'])
    df1.update(df[df['Date'] == last_data_date].set_index(['Ticker','CCASS ID']))

    return df1.reset_index(drop = False)


def recent_trades_query(ticker,CCASS_ID,cum_change,threshold_multiplier = 0.1):

    threshold = abs(cum_change) * threshold_multiplier

    df = database.groupby(['Ticker','CCASS ID']).get_group((ticker,CCASS_ID)).loc[(abs(database['DoD Change (%) *'])>threshold)].reset_index(drop = True)

    df['Net Cumulative Change (%) *'] = cum_change

    df = df.set_index(['Ticker','CCASS ID','Net Cumulative Change (%) *', 'Date'])

    df = df.sort_values(by = 'Date', ascending = True)

    df = df.replace(np.nan, '', regex=True) # Replace nan by blank for better formatting

    # Rename columns
    df.columns = ['Shareholding', '% of Issued Shares *', 'DoD Change (%) *']

    return df.reset_index()


def create_graph(ticker, CCASS_ID, export_path):

    df1 = database[(database['Ticker'] == ticker) & (database['CCASS ID'] == CCASS_ID)][['Date', 'Shareholding']].sort_values('Date').set_index('Date')
    date = df1.index.str[-2:]
    data = df1['Shareholding']/1000000

    t = np.arange(0,len(df1))
    fig, ax = plt.subplots()

    #ax.plot(date, data)
    ax.bar(date, data, 0.45)

    ax.set(xlabel = 'Day in month', ylabel = 'Shareholding (million)',
            title = str(ticker) + ' Shareholdings by "' + participants_dict.get(CCASS_ID) + '"')

    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    fig.set_size_inches(9, 3.7)
    fig.savefig(export_path)
    #plt.show()
    plt.close(fig)


def main():

    global last_data_date, database, mail, outlook

    ## Create a summary tables of all the block traders
    summary_df = block_trade_query(df = database, days = 15 ,threshold = 10)
    ### Temporary tracker for 997.HK
    #summary_df = summary_df.append(block_trade_query(df = database[(database['Ticker'] == 997)], days = 15 ,threshold = 1))
    
    summary_df.reset_index(drop = True, inplace = True)


    if len(summary_df) == 0: # When there were no changes
        mail.To = 'jameshan@chinasilveram.com;prashantgurung@chinasilveram.com'
        mail.Subject = 'CCASS major changes (as of ' + last_data_date + ' day end)'
        aggregated_html = '<body style="font-size:11pt;font-family:Calibri"><p>Dear Team,</p><p>&nbsp;</p><p>There were NO significant net changes on CCASS (&gt; 10% net cumulative change) over the last 15 trading days.</p><p>&nbsp;</p><p>Regards,</p><p>Kevin Wong</p></body>'

    else:
        ## Create a table which shows block traders & its recent trades
        table = pd.DataFrame()
        for i in summary_df.index:
            temp_row = summary_df.iloc[i]
            temp_table = recent_trades_query(ticker = temp_row['Ticker'],CCASS_ID = temp_row['CCASS ID'],cum_change = temp_row['Net Cumulative Change (%) *'])
            table = table.append(temp_table)
        table.reset_index(drop = True, inplace = True)

        table = table.merge(summary_df, how = 'outer')

        ## Mapping CCASS participants & Stock names
        table['Participant'] = table['CCASS ID'].map(participants_dict)
        table['Stock Name'] = table['Ticker'].map(securities_dict)

        table = table.set_index(['Ticker','Stock Name','CCASS ID','Participant','Net Cumulative Change (%) *', 'Date']).sort_index(level=0)

        graphing_df = table.reset_index()[['Ticker','Stock Name','CCASS ID','Participant']].drop_duplicates().reset_index(drop = True)

        ## Create multiple graphs and save them
        graphs_count = len(graphing_df.index)
        for i in range(graphs_count):
            ticker = graphing_df.iloc[i]['Ticker']
            CCASS_ID = graphing_df.iloc[i]['CCASS ID']
            fig_path = 'CCASS_tracker' + os.sep + 'cache' + os.sep + 'fig_' + str(i)
            create_graph(ticker = ticker, CCASS_ID = CCASS_ID, export_path = fig_path)

        png_address_list = []
        for i in range(graphs_count):
            png_address_list.append('<img src="' + os.getcwd() + os.sep + 'CCASS_tracker' + os.sep + 'cache' + os.sep + 'fig_' + str(i) +'.png"/>')

        ## Adding thousand separator to "Shareholding"
        num_format = lambda x: '{:,}'.format(x)
        def build_formatters(df, format):
            return {
                column:format 
                for column, dtype in df.dtypes.items()
                if dtype in [ np.dtype('int64')] 
            }
        formatters = build_formatters(table, num_format)

        mail.To = 'jameshan@chinasilveram.com;prashantgurung@chinasilveram.com'
        mail.Subject = 'CCASS major changes (as of ' + last_data_date + ' day end)'
        png_aggregated_html = ''.join(png_address_list)

        heading_html =  "<p>Dear Team,</p><p>&nbsp;</p>"
        no_change_html = "<p>There were NO significant changes on CCASS yesterday. Here's the recap of the previous major changes (&gt;10% net cumulative change over the last 15 trading days).</p>"
        with_change_html = "<p>Here's the summary of the recent CCASS major changes (&gt;10% net cumulative change over the last 15 trading days).</p><p>&nbsp;</p>"
        opening_html = with_change_html if last_data_date in list(table.reset_index()['Date'].unique()) else no_change_html
        ending_html = "<p>Regards,</p><p>Kevin Wong</p>"
        content_html = table.to_html(index = True,formatters=formatters) + "<p>* Denominators are the number of all shares/warrants/units issued in total.</p><p>&nbsp;</p>"  + png_aggregated_html

        aggregated_html = '<body style="font-size:11pt;font-family:Calibri">' + heading_html + opening_html + content_html + ending_html + '</body>'

    mail.HTMLBody = aggregated_html
    mail.Display(False)
    
    #mail.Send()



if __name__ == "__main__":
    main()