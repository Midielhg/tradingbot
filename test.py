from webull import webull
import schedule
import pandas as pd
pd.set_option('display.max_rows', None)
import warnings
warnings.filterwarnings('ignore')
import time
import robin_stocks.robinhood as rh
wb = webull()
import pprint
from datetime import datetime, time as dtime
import os

rh.login(os.getenv('ROBINHOOD_USERNAME'), os.getenv('ROBINHOOD_PASSWORD'))

# pprint.pprint(order)

# order = rh.orders.order(symbol        = "tqqq",
#                         quantity      = 5,
#                         side          = "buy",
#                         limitPrice= 50,
#                         extendedHours = True,
#                         market_hours  = "extended_hours")  
# pprint.pprint(order) 


open_orders = rh.orders.get_all_open_stock_orders()
#print all open orders id
for open_order in open_orders:
    print(open_order['id'])
    id = open_orders['id']
    rh.orders.cancel_stock_order(id)




# pprint.pprint(open_orders)
