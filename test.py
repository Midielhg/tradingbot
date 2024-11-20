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

order = rh.orders.order(symbol        = "tqqq",
                        quantity      = 5,
                        side          = "buy",
                        limitPrice= 50,
                        extendedHours = True,
                        market_hours  = "extended_hours")   


order_id = order['id']
while True:
    open_orders = rh.orders.get_all_open_stock_orders()
    order_status = None
    for open_order in open_orders:
        if open_order['id'] == order_id:
            order_status = open_order['state']
            print("Order pending")
            break
        else:
            order_status = "closed"
            print("Order ", order_id," ", order_status)
            break
    if open_order['id'] != order_id:
        break
    time.sleep(5)  # Add a delay to avoid excessive API calls
in_short_position = False