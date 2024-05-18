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

ticker_up = "TQQQ"  # Example ticker for going up
ticker_down = "SQQQ"  # Example ticker for going down
asset = "stock"

# Initialize position flags
in_longPosition_up = False
in_longPosition_down = False

def heikin_ashi(df):
    ha_df = df.copy()
    
    # Heikin Ashi close is the average of the open, close, high, and low values
    ha_df['ha_close'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4
    
    # Heikin Ashi open is the average of the previous Heikin Ashi open and close
    ha_df['ha_open'] = (df['open'].shift(1) + df['close'].shift(1)) / 2
    
    # The first Heikin Ashi open is just the open of the first candle
    ha_df.iloc[0, ha_df.columns.get_loc('ha_open')] = df.iloc[0]['open']
    
    # Heikin Ashi high is the maximum of the high, Heikin Ashi open, and Heikin Ashi close
    ha_df['ha_high'] = ha_df[['high', 'ha_open', 'ha_close']].max(axis=1)
    
    # Heikin Ashi low is the minimum of the low, Heikin Ashi open, and Heikin Ashi close
    ha_df['ha_low'] = ha_df[['low', 'ha_open', 'ha_close']].min(axis=1)
    
    return ha_df

def bar_up_dn_strategy(df):
    df['previous_close'] = df['ha_close'].shift(1)
    df['bar_up'] = (df['ha_close'] > df['ha_open']) & (df['ha_open'] > df['previous_close'])
    df['bar_dn'] = (df['ha_close'] < df['ha_open']) & (df['ha_open'] < df['previous_close'])
    return df

# buy and sell signals
def place_orders(df):
    global in_longPosition_up, in_longPosition_down  # global in_longPosition

    last_row_index = len(df.index) - 1  # get the index of the last row

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

    print(df[['timestamp', 'ha_open', 'ha_close', 'previous_close', 'bar_up', 'bar_dn']].tail(2))  # Debug print to check the conditions

    if df['bar_up'].iloc[last_row_index]:
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
    elif df['bar_dn'].iloc[last_row_index]:
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

    df = heikin_ashi(df)  # calculate Heikin Ashi values
    df = bar_up_dn_strategy(df)  # apply the BarUpDn strategy
    place_orders(df)  # check for buy and sell signals

schedule.every(3).seconds.do(run_bot)  # run the bot every 3 seconds

while True:
    schedule.run_pending()  # run the scheduled tasks
    time.sleep(1)  # wait 1 second
