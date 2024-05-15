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

crypto = "DOGE"

#supper trend parameters
period = 10
factor = 1

# get positions
crypto_positions = rh.get_crypto_positions()
quote = rh.get_crypto_quote(crypto)


# Print Positions
for item in crypto_positions:
    if item['currency']['code'] == crypto:
        quantity = item['quantity']
        print(crypto, "quantity: ", quantity)
        # market_value = qurrency * quantity
        market_value = float(item['quantity']) * float(quote['mark_price'])
        print(crypto, "Position Market Value: $", market_value)

            
# print buying power
account_info = rh.account.load_account_profile()
buying_power = float(account_info['buying_power'])
print("Buying Power: $", buying_power)

# print if in long position
if market_value >= 1:
    in_longPosition = True
    print("You are in a long position, looking for a place to sell")
else:
    in_longPosition = False
    print("You are not in a long position, looking for a place to buy")

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

    # print(df.tail(2)) #print the last 2 rows of the dataframe
    last_row_index = len(df.index) - 1 #get the index of the last row
    previous_row_index = last_row_index - 1 #get the index of the previous row
    
    #if the current row is in an uptrend
    if df['in_uptrend'][last_row_index]:
        print("Current Trend: UpTrend")
        if in_longPosition == False:
            order = rh.order_buy_crypto_by_price(crypto, buying_power, timeInForce='gtc')
            print("Buying ", crypto)
            print(order)
            in_longPosition = True
        else:
            print("already in Long, Making Money")
    else:
        print("Current Trend: DownTrend")
        if in_longPosition == True:
            order = rh.order_sell_crypto_by_price(crypto, quantity, timeInForce='gtc')   
            print("Selling", crypto)
            print(order)
            in_longPosition = False
        else:
            print("Already out of the position, Saved from the DownTrend")

    
    # #if trend change from downtrend to uptrend, buy 
    # if not df['in_uptrend'][previous_row_index] and df['in_uptrend'][last_row_index]: #if the previous row was not in an uptrend and the last row is in an uptrend
    #     print("changed to uptrend, Long")
    #     if  in_longPosition == False: #if not on long position, buy
    #         order = rh.order_buy_crypto_by_price(crypto, buying_power, timeInForce='gtc')
    #         print("Buying ", crypto)
    #         print(order)
    #         in_longPosition = True
    #     else:
    #         print("already in Long, nothing to do")
        
    # # if trend change from uptrend to downtrend, sell
    # if df['in_uptrend'][previous_row_index] and not df['in_uptrend'][last_row_index]:#if the previous row was in an uptrend and the last row is not in an uptrend
    #     print ("changed to downtrend, Short")
    #     if in_longPosition == True: #if is not on Short position Sell
    #         order = rh.order_sell_crypto_by_price(crypto, total_market_value, timeInForce='gtc')   
    #         print("Selling", crypto)
    #         print(order)
    #         in_longPosition = False
    #     else:
    #         print("already in Short, nothing to do")
        
#Run the bot  
def run_bot():
    print(f"\nFetching new bars for {datetime.now().isoformat()}")
    bars = wb.get_bars(stock=crypto, interval='m1', count=100, extendTrading=1) #get the last 100 bars of TQQQ at 1 minute intervals
    df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']) #convert the fetched data into a pandas data-frame
    
    try:
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms') #convert the timestamp data to datetime format
    except FloatingPointError:
        print("Invalid timestamp encountered. Please check the 'timestamp' column of your dataframe.")
        return  # Skip the rest of the function if an error occurs

    supertrend(df, period, factor) #calculate the supertrend indicator
    check_buy_sell_signals(df)#check for buy and sell signals 

schedule.every(3).seconds.do(run_bot) #run the bot every 3 seconds
while True:
    schedule.run_pending() #run the scheduled tasks
    time.sleep(1) #wait 1 second