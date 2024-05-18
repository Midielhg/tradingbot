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

login = rh.login('midielhg@gmail.com','nuGcej-famzoj-vafce1')

ticker = "DOGE"
asset = "crypto"


#supper trend parameters
period = 10
factor = 3




#indicators
def tr(data):#true range
    data['previous_close'] = data['close'].shift(1)
    data['high-low'] = abs(data['high'] - data['low'])
    data['high-pc'] = abs(data['high'] - data['previous_close'])
    data['low-pc'] = abs(data['low'] - data['previous_close'])

    tr = data[['high-low', 'high-pc', 'low-pc']].max(axis=1)

    return tr

def atr(data, period):#average true range
    data['tr'] = tr(data)
    atr = data['tr'].rolling(period).mean()

    return atr

def supertrend(df, period, atr_multiplier): #supertrend
    hl2 = (df['high'] + df['low']) / 2  # typical price
    df['atr'] = atr(df, period) #average true range
    df['upperband'] = hl2 + (atr_multiplier * df['atr']) #upper band
    df['lowerband'] = hl2 - (atr_multiplier * df['atr']) #lower band
    df['in_uptrend'] = True

    for current in range(1, len(df.index)): #for each row in the dataframe
        previous = current - 1 #get the previous row

        if df['close'][current] > df['upperband'][previous]: #if the current close is greater than the previous upper band
            df['in_uptrend'][current] = True #set the current row to be in an uptrend
        elif df['close'][current] < df['lowerband'][previous]: #if the current close is less than the previous lower band
            df['in_uptrend'][current] = False #set the current row to be in a downtrend
        else:
            df['in_uptrend'][current] = df['in_uptrend'][previous] #if the current close is between the upper and lower bands, set the current row to be in the same trend as the previous row

            if df['in_uptrend'][current] and df['lowerband'][current] < df['lowerband'][previous]: #if the current row is in an uptrend and the current lower band is less than the previous lower band
                df['lowerband'][current] = df['lowerband'][previous] #set the current lower band to be the same as the previous lower band

            if not df['in_uptrend'][current] and df['upperband'][current] > df['upperband'][previous]: #if the current row is in a downtrend and the current upper band is greater than the previous upper band
                df['upperband'][current] = df['upperband'][previous] #set the current upper band to be the same as the previous upper band

    return df

#buy and sell signals
def place_orders(df):
    global in_longPosition #global in_longPosition
    
    print(df.tail(2)) #print the last 2 rows of the dataframe
    last_row_index = len(df.index) - 1 #get the index of the last row
    previous_row_index = last_row_index - 1 #get the index of the previous row


    # check account buying powet
    account_info = rh.account.load_account_profile()
    buying_power = float(account_info['buying_power'])
    buying_power = buying_power - 1
    print("Buying Power: $", buying_power)
    
# place orders if asset is stocks 
    if asset == "stock":
        stock_positions = rh.account.get_all_positions()
        stock_quote = rh.get_stock_quote_by_symbol(ticker)
        quantity = 0
        market_value = 0
        for item in stock_positions:
            if item['symbol'] == ticker:
                quantity = float(item['quantity'])
                market_value = float(item['quantity']) * float(stock_quote['last_trade_price'])
                print(ticker, "Market Value: $", float(market_value))

        if market_value >= 1:
            in_longPosition = True
        else:
            in_longPosition = False 

        if df['in_uptrend'][last_row_index]:
            # Define the variable "buying_power"
            print("Current Trend: UpTrend")
            if in_longPosition == False:
                order = rh.order_buy_market(ticker, buying_power)
                print("Buying ", ticker)
                pprint.pprint(order)
                in_longPosition = True  
            else:
                print("You are Long, Making Money")
        else:
            print("Current Trend: DownTrend")
            if in_longPosition == True:
                order = rh.order_sell_market(ticker, quantity)
                print("Selling",quantity, ticker)
                pprint.pprint(order)
                in_longPosition = False
            else:
                print("You don't have an open position, Saving Money")
# place orders if asset is crypto
    elif asset == "crypto":
        crypto_positions = rh.get_crypto_positions()
        crypto_quote = rh.get_crypto_quote(ticker)
        quantity = 0
        market_value = 0
        for item in crypto_positions:
            if item['currency']['code'] == ticker:
                quantity = float(item['quantity'])
                # market_value = quantity * price
                market_value = float(item['quantity']) * float(crypto_quote['mark_price'])
                print("Crypto Market Value: $", float(market_value))

        # print if in long position
        if market_value >= 1:
            in_longPosition = True
        else:
            in_longPosition = False 

        if df['in_uptrend'][last_row_index]:
            # Define the variable "buying_power"
            print("Current Trend: UpTrend")
            if in_longPosition == False:
                order = rh.order_buy_crypto_by_price(ticker, buying_power, timeInForce='gtc')
                print("Buying ", ticker)
                pprint.pprint(order)
                in_longPosition = True  
            else:
                print("You are Long, Making Money")
        else:
            print("Current Trend: DownTrend")
            if in_longPosition == True:
                order = rh.order_sell_crypto_by_quantity(ticker, quantity, timeInForce='gtc')
                print("Selling",quantity, ticker)
                pprint.pprint(order)
                in_longPosition = False
            else:
                print("You don't have an open position, Saving Money")

#Run the bot  
def run_bot():
    print(f"\nFetching new bars for {datetime.now().isoformat()}")
    bars = wb.get_bars(stock=ticker, interval='m1', count=100, extendTrading=1) #get the last 100 bars of TQQQ at 1 minute intervals
    df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']) #convert the fetched data into a pandas data-frame
    
    try:
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms') #convert the timestamp data to datetime format
    except FloatingPointError:
        print("Invalid timestamp encountered. Please check the 'timestamp' column of your dataframe.")
        return  # Skip the rest of the function if an error occurs

    supertrend(df, period, factor) #calculate the supertrend indicator
    place_orders(df)#check for buy and sell signals 

schedule.every(3).seconds.do(run_bot) #run the bot every 3 seconds

while True:
    
    schedule.run_pending() #run the scheduled tasks
    time.sleep(1) #wait 1 second