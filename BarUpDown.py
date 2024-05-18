from webull import webull
import json
import schedule
import pandas as pd
pd.set_option('display.max_rows', None)
import warnings
warnings.filterwarnings('ignore')
import numpy as np
from datetime import datetime
import time
import robin_stocks.robinhood as rh
import sys
import os
import pyotp
import robin_stocks as rb
wb = webull()
import pprint

login = rh.login('midielhg@gmail.com', 'nuGcej-famzoj-vafce1')

ticker_up = "DOGE"  # Example ticker for going up
ticker_down = "DOGE"  # Example ticker for going down



def bar_up_dn_strategy(df):
    df['previous_close'] = df['close'].shift(1)
    df['bar_up'] = (df['close'] > df['open']) & (df['open'] > df['previous_close'])
    df['bar_dn'] = (df['close'] < df['open']) & (df['open'] < df['previous_close'])  

    return df




# buy and sell signals
def place_orders(df):
    global in_longPosition  # global in_longPosition

    print(df.tail(2))  # print the last two rows of the data-frame
    last_row_index = len(df.index) - 1  # get the index of the last row
    previous_row_index = last_row_index - 1  # get the index of the previous row

    # check account buying power
    account_info = rh.account.load_account_profile()
    buying_power = float(account_info['buying_power'])
    buying_power = buying_power - 1
    print("Buying Power: $", buying_power)

    # Check positions for TQQQ and SQQQ
    stock_positions = rh.account.get_all_positions()
    quantity_up = 0
    market_value_up = 0
    quantity_down = 0
    market_value_down = 0


    stock_quote_up = rh.get_stock_quote_by_symbol(ticker_up)
    stock_quote_down = rh.get_stock_quote_by_symbol(ticker_down)

#   print(stock_positions)
    for item in stock_positions:
        if item['symbol'] == ticker_up:
            quantity_up = float(item['quantity'])
            market_value_up = float(item['quantity']) * float(stock_quote_up['last_trade_price'])
            print(ticker_up, "Market Value: $", float(market_value_up))
        elif item['symbol'] == ticker_down:
            quantity_down = float(item['quantity'])
            market_value_down = float(item['quantity']) * float(stock_quote_down['last_trade_price'])
            print(ticker_down, "Market Value: $", float(market_value_down))

    if market_value_up >= 1:
        in_longPosition_up = True
    else:
        in_longPosition_up = False

    if market_value_down >= 1:
        in_longPosition_down = True
    else:
        in_longPosition_down = False

    if df['bar_up'][last_row_index]:
        print("Signal: Bar Up")
        if not in_longPosition_up:
            order_up = rh.order_buy_market(ticker_up, buying_power)
            print("Buying ", ticker_up)
            pprint.pprint(order_up)
            in_longPosition_up = True
        if in_longPosition_down:
            order_down = rh.order_sell_market(ticker_down, quantity_down)
            print("Selling", quantity_down, ticker_down)
            pprint.pprint(order_down)
            in_longPosition_down = False
        else:
            print("You are Long TQQQ, Making Money")
    elif df['bar_dn'][last_row_index]:
        print("Signal: Bar Down")
        if not in_longPosition_down:
            order_down = rh.order_buy_market(ticker_down, buying_power)
            print("Buying ", ticker_down)
            pprint.pprint(order_down)
            in_longPosition_down = True
        if in_longPosition_up:
            order_up = rh.order_sell_market(ticker_up, quantity_up)
            print("Selling", quantity_up, ticker_up)
            pprint.pprint(order_up)
            in_longPosition_up = False
        else:
            print("You are Long SQQQ, Making Money")

# Run the bot
def run_bot():
    print(f"\nFetching new bars for {datetime.now().isoformat()}")
    bars = wb.get_bars(stock=ticker_up, interval='m1', count=100, extendTrading=1)  # get the last 100 bars at 1 minute intervals
    df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])  # convert the fetched data into a pandas data-frame

    try:
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')  # convert the timestamp data to datetime format
    except FloatingPointError:
        print("Invalid timestamp encountered. Please check the 'timestamp' column of your dataframe.")
        return  # Skip the rest of the function if an error occurs

    df = bar_up_dn_strategy(df)  # apply the BarUpDn strategy
    place_orders(df)  # check for buy and sell signals

schedule.every(3).seconds.do(run_bot)  # run the bot every 3 seconds

while True:
    schedule.run_pending()  # run the scheduled tasks
    time.sleep(1)  # wait 1 second
