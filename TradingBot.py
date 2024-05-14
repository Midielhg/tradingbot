#This is a bot that will connect to Robinhood and place automatic trades based of the super trend indicator
#the bot will place a BUY signal for TQQQ when the super trend indicator is in an uptrend
#the bot will place a SELL signal for TQQQ when the super trend indicator is in a downtrend
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
wb = webull()

import robin_stocks.robinhood as rh
import sys
import os
import pyotp
import robin_stocks as rb

login = rh.login('midielhg@gmail.com','nuGcej-famzoj-vafce1')


#initial parameters
long_symbol = 'TQQQ'
short_symbol = 'SQQQ'


#supper trend parameters
period = 50
factor = 1

#market status
def market_status():
    #if time is from 9:30 to 15:58 maket open = true else market open = false
    if datetime.now().hour >= 9 and datetime.now().hour <= 15 and datetime.now().minute >= 30 and datetime.now().minute <= 58:
        market_open = True

# print current positions
positions_data = rh.account.build_holdings()

# Print Positions
if positions_data == {}: #if there are no positions
    print("No positions")
else:
    for ticker, data in positions_data.items():
        print( f'Position: {ticker}, Quantity: {data["quantity"]}, Market Value: {data["equity"]}')
        quantity = data["quantity"]


# if market value is > 0, you are in a position and you can sell
if market_status() == True:
    print ("Market is open")
    if float(data["equity"]) > 0:
        print("You are in a position")
        print("You can sell")
    else:
        print("You are not in a position")
        print("You can buy")
    # market is closed
else:
    print ("Market is closed")
    print("bot won't run")
    # end the program
    sys.exit()
        
# if position is TQQQ, you are long 
if ticker == 'TQQQ':
    in_longPosition = True
    in_shortPosition = False
    print("You are long")
    print("Looking for a place to short")
elif ticker == 'SQQQ':
    in_longPosition = False
    in_shortPosition = True
    print("You are short")
    print("Looking for a place to long")

# if market is about to close, close all positions
if datetime.now().hour == 15 and datetime.now().minute >= 58:
    print("Market is about to close")
    print("Closing all positions")
    # close all positions
    if in_longPosition == True:
        rh.order_sell_market(long_symbol, quantity)
        print("Closing TQQQ Long position")
    elif in_shortPosition == True:
        rh.order_buy_market(short_symbol, quantity)
        print("Closing TQQQ Short position")
    print("All positions closed")
    # end the program
    sys.exit()
    
# print buying power
account_info = rh.account.load_account_profile()
print("Buying Power: ", account_info['buying_power'])






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
def check_buy_sell_signals(df):
    global in_longPosition #global in_longPosition
    global in_shortPosition #global in_shortPosition

    print(df.tail(2)) #print the last 2 rows of the dataframe
    last_row_index = len(df.index) - 1 #get the index of the last row
    previous_row_index = last_row_index - 1 #get the index of the previous row

    if in_longPosition == True:
        print("You are in a long position")
    elif in_shortPosition == True:
        print("You are in a short position")
    elif in_longPosition == False and in_shortPosition == False:
        print("You are not in a position")
        
    if not df['in_uptrend'][previous_row_index] and df['in_uptrend'][last_row_index]: #if the previous row was not in an uptrend and the last row is in an uptrend
        print("changed to uptrend, Long")
        if not in_longPosition: #if not on long position, buy
            order = rh.order_buy_market(symbol, quantity)
            print("buying ", symbol)
            print(order)
            in_longPosition = True
        
            if in_shortPosition: #if is on Short position Buy back to close the Short position
                order = rh.order_buy_market(symbol, quantity)
                print("Closing TQQQ Short position")
                print(order)
                in_shortPosition = False
            else:
                print("No short position to close")
        else:
            print("already in Long, nothing to do")
        
    if df['in_uptrend'][previous_row_index] and not df['in_uptrend'][last_row_index]:#if the previous row was in an uptrend and the last row is not in an uptrend
        print ("changed to downtrend, Short")
        if not in_shortPosition: #if is not on Short position Sell
            order = rh.order_sell_market(symbol, quantity)
            print("Shorting TQQQ")
            print(order)
            in_shortPosition = True
        
            if in_longPosition: #if is on Long position Sell to close the Long position
                order = rh.order_sell_market(symbol, quantity)
                print("Closing TQQQ Long Position")
                print(order)
                in_longPosition = False
            else:
                print("No long position to close")
        else:
            print("already in Short, nothing to do")
        
#Run the bot  
def run_bot():
    
    print(f"\nFetching new bars for {datetime.now().isoformat()}")
    bars = wb.get_bars(stock=long_symbol, interval='m1', count=100, extendTrading=1) #get the last 100 bars of TQQQ at 1 minute intervals
    df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']) #convert the fetched data into a pandas data-frame
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms') #convert the timestamp data to datetime format
    supertrend(df, period, factor) #calculate the supertrend indicator
    check_buy_sell_signals(df)#check for buy and sell signals
    

schedule.every(3).seconds.do(run_bot) #run the bot every 3 seconds
while True:
    schedule.run_pending() #run the scheduled tasks
    time.sleep(0.01) #wait 1 second