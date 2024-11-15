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


# Initialize Webull and Robinhood
wb = webull()
try:
    rh.login(os.getenv('ROBINHOOD_USERNAME'), os.getenv('ROBINHOOD_PASSWORD'))
    print("Welcome Back to the SuperTrend Bot")
except Exception as e:
    print(f"Failed to login: {e}")
    exit(1)


# Bot Configuration
symbol = "TQQQ"
inverse_symbol = "SQQQ"
period = 5
factor = 2
trade_amount = 500
market_value = 0

# Define Trading Hours (9:30 AM to 4:00 PM)
market_open = dtime(9, 30)
market_close = dtime(16, 0)

cooldown_period = 60
last_trailing_stop_time = 0
last_trailing_stop_price = 0
last_inverse_trailing_stop_price = 0
reference_id = " "

pending_orders = rh.orders.get_all_open_stock_orders()

# Initialize a list to store reference IDs of trailing stop orders placed by the bot
trailing_stop_order_ids = []

# Initialize position flags
in_long_position = False
in_short_position = False

#indicators funtions to calculate Supertrend
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

# Helper function to check if an order is pending
def is_order_pending(symbol, shares, side):
    for order in pending_orders:
        if order['instrument_id'] == symbol and order['quantity'] == shares and order['side'] == side and order['trigger'] == 'immediate':
            return True
    return False

# Helper function to check if a trailing stop order is pending
def is_trailing_stop_order_pending(symbol):
    for order in pending_orders:
        if order['instrument_id'] == symbol and order['trigger'] == "stop" and order['ref_id'] in trailing_stop_order_ids:
            return True
    return False



#buy and sell signals
def place_orders(df):
    print(df.tail(2)) # Log the last 2 rows of the dataframe
    global reference_id
    global in_long_position, last_trailing_stop_time, last_trailing_stop_price, last_inverse_trailing_stop_price
    stock_positions = rh.account.get_all_positions()

    try:
        instrument_id = rh.get_instruments_by_symbols(symbol)[0]['id']
        inverse_instrument_id = rh.get_instruments_by_symbols(inverse_symbol)[0]['id']
    except (IndexError, KeyError) as e:
        print(f"Failed to get instrument IDs: {e}")
        return

    try:
        stock_quote = rh.get_stock_quote_by_symbol(symbol)
        inverse_stock_quote = rh.get_stock_quote_by_symbol(inverse_symbol)
    except KeyError as e:
        print(f"Failed to get stock quotes: {e}")
        return
    
    shares_owned = 0

    if is_order_pending(instrument_id, shares_owned, "buy"):
        print(f"Buy Order for {symbol} is still active")
    
    if is_trailing_stop_order_pending(instrument_id):
        print(f"Trailing Stop Order for {symbol} is still active")
    elif reference_id not in trailing_stop_order_ids:
        print(f"Trailing Stop not placed for {symbol}")
    else:
        print(f"Trailing Stop was executed for {symbol}")
        last_trailing_stop_time = time.time()
        last_trailing_stop_price = float(stock_quote['last_trade_price'])
        last_trailing_stop_time = 0  # Reset cooldown period
    print("Last Trailing Stop Price: ", last_trailing_stop_price)


    if is_trailing_stop_order_pending(inverse_instrument_id):
        print(f"Trailing Stop Order for {inverse_symbol} is still active")
    elif reference_id not in trailing_stop_order_ids:
        print(f"Trailing Stop not placed for {inverse_symbol}")
    else:
        print(f"Trailing Stop was executed for {inverse_symbol}")
        last_trailing_stop_time = time.time()
        last_inverse_trailing_stop_price = float(inverse_stock_quote['last_trade_price'])
        last_trailing_stop_time = 0  # Reset cooldown period
    print("Last Inverse Trailing Stop Price: ", last_inverse_trailing_stop_price)

    # Calculate trail amounts
    symbol_trail_amount = round(float(stock_quote['last_trade_price']) * 0.002, 3)
    inverse_symbol_trail_amount = round(float(inverse_stock_quote['last_trade_price']) * 0.002, 3)

    # Check cooldown period
    if time.time() - last_trailing_stop_time < cooldown_period:
        if (float(stock_quote['last_trade_price']) > last_trailing_stop_price + symbol_trail_amount or
            float(inverse_stock_quote['last_trade_price']) > last_inverse_trailing_stop_price + inverse_symbol_trail_amount):
            print("Symbol price is higher than the trailing stop price plus trail amount. Disabling cooldown.")
            last_trailing_stop_time = 0
        else:
            print("Cooldown period active. No trades will be placed.")
            return

    for item in stock_positions:
        if item['symbol'] == symbol:
            shares_owned = float(item['quantity'])
            market_value = shares_owned * float(stock_quote['last_trade_price'])
            if shares_owned > 0:
                print(f"\nYou own {int(shares_owned)} shares of {symbol} with a Market Value of: ${float(market_value)}")
        elif item['symbol'] == inverse_symbol:
            inverse_shares_owned = float(item['quantity'])
            inverse_market_value = inverse_shares_owned * float(stock_quote['last_trade_price'])
            if inverse_shares_owned:
                print(f"\nYou own {int(inverse_shares_owned)} shares of {inverse_symbol} with a Market Value of: ${float(inverse_market_value)}")
    
    shares_to_trade = int(trade_amount // float(stock_quote['last_trade_price']))
    inverse_shares_to_trade = int(trade_amount // float(inverse_stock_quote['last_trade_price']))
    
    # if shares_owned > shares_to_trade:
    #     print("You own more share than the ones that you were willing to trade with. Selling some:")
    #     extra_shares = shares_owned - shares_to_trade
    #     if not is_order_pending(symbol, shares_owned, "sell"):
    #         order  = rh.orders.order(symbol        = symbol,
    #                         quantity      = shares_owned,
    #                         side          = "sell",
    #                         extendedHours = True,
    #                         market_hours  = "extended_hours")
    #         print("Selling ", extra_shares, " extra shares of ", symbol)
    #     else:
    #         print("Pending order found for selling ", shares_owned, " shares of ", symbol)
    #     #get the reference id of from the order 
    #     reference_id = order['ref_id']
        
        
    # if inverse_shares_owned > inverse_shares_to_trade:
    #     print("You own more share than the ones that you were willing to trade with. Selling some:")
    #     inverse_extra_shares = inverse_shares_owned - inverse_shares_to_trade
    #     if not is_order_pending(inverse_symbol, inverse_shares_owned, "sell"):
    #         order = rh.orders.order(symbol        = inverse_symbol,
    #                         quantity      = inverse_shares_owned,
    #                         side          = "sell",
    #                         extendedHours = True,
    #                         market_hours  = "extended_hours")
    #         print("Selling ", inverse_extra_shares, " extra shares of ", inverse_symbol)
    #     else:
    #         print("Pending order found for selling ", inverse_shares_owned, " shares of ", inverse_symbol)
    
    in_long_position = market_value >= 1
    in_short_position = inverse_market_value >=1
    
    last_row_index = len(df.index) - 1 #get the index of the last row
    if df['in_uptrend'][last_row_index]:
        print("Current Trend: UpTrend")
        print("You can trade with ", shares_to_trade, " shares")
        if not in_long_position: #opening long position on uptrend
            if not is_order_pending(symbol, shares_to_trade, "buy"):
                order = rh.orders.order(symbol        = symbol,
                                        quantity      = shares_to_trade,
                                        side          = "buy",
                                        extendedHours = True,
                                        market_hours  = "extended_hours")                
                print(f"Opening {symbol} position")
                # print(order)
                while is_order_pending(symbol, shares_to_trade, "buy"):
                    print("Waiting for order to be executed...")
                    time.sleep(1)
                in_long_position = True
            if not is_trailing_stop_order_pending(instrument_id):
                trailing_stop = rh.orders.order_trailing_stop(
                                        symbol = symbol,
                                        quantity = shares_to_trade,
                                        side = "sell",
                                        trailAmount = symbol_trail_amount,
                                        trailType = 'amount',
                                        timeInForce = 'gtc',
                                        jsonify= True)
                print(f"Trailing Stop Order for {symbol} position")
                print (trailing_stop)
            else:
                print(f"Trailing Stop Order for {symbol} is still active")
            if 'ref_id' in trailing_stop:
                trailing_stop_order_ids.append(trailing_stop['ref_id'])  # Store the reference ID
                print("Refenrence ID added to the list")
            else:
                print(f"Trailing stop order for {symbol} did not return a reference ID.")
        if in_short_position: #close short position on uptrend
            print("In Short Position")
            if not is_order_pending(inverse_symbol, inverse_shares_owned, "sell"):
                order = rh.orders.order(symbol        = inverse_symbol,
                                        quantity      = inverse_shares_owned,
                                        side          = "sell",
                                        extendedHours = True,
                                        market_hours  = "extended_hours")
                print("Closing ", inverse_shares_owned, " shares of ", inverse_symbol)
                # pprint.pprint(order)
                while is_order_pending(inverse_symbol, inverse_shares_owned, "sell"):
                    print("Waiting for order to be executed...")
                    time.sleep(1)
                in_short_position = False
            else:
                print("Pending order found to close ", inverse_shares_owned, " shares of ", inverse_symbol)
    else:
        print("Current Trend: DownTrend")
        print("You can trade with ", inverse_shares_to_trade, " shares")
        if not in_short_position:
            if not is_order_pending(inverse_symbol, inverse_shares_to_trade, "buy"):
                order = rh.orders.order(symbol        = inverse_symbol,
                                        quantity      = inverse_shares_to_trade,
                                        side          = "buy",
                                        extendedHours = True,
                                        market_hours  = "extended_hours")
                print(f"Opening {inverse_symbol} position")
                # print(order)
                while is_order_pending(inverse_symbol, inverse_shares_to_trade, "buy"):
                    print("Waiting for order to be executed...")
                    time.sleep(1)
                in_short_position = True
            if not is_trailing_stop_order_pending(inverse_instrument_id):                       
                trailing_stop = rh.orders.order_trailing_stop(
                                        symbol = inverse_symbol,
                                        quantity = inverse_shares_to_trade,
                                        side = "sell",
                                        trailAmount = inverse_symbol_trail_amount,
                                        trailType = 'amount',
                                        timeInForce = 'gtc',
                                        jsonify= True)
                print(f"Trailing Stop Order for {inverse_symbol} position")
                print (trailing_stop)
                if 'ref_id' in trailing_stop:
                    trailing_stop_order_ids.append(trailing_stop['ref_id'])  # Store the reference ID
                    print("Refenrence ID added to the list")
                else:
                    print(f"Trail stop order for {inverse_symbol} did not return a reference ID.")
        if in_long_position: #close long position on downtrend
            print("In Long Position")
            if not is_order_pending(symbol, shares_owned, "sell"):
                order = rh.orders.order(symbol        = symbol,
                                        quantity      = shares_owned,
                                        side          = "sell",
                                        extendedHours = True,
                                        market_hours  = "extended_hours")
                print(f"Closing {symbol} position")
                # print(order)
                while is_order_pending(symbol, shares_owned, "sell"):
                    print("Waiting for order to be executed...")
                    time.sleep(1)
            else:
                print("Pending order found to close ", shares_owned, " shares of ", symbol)
        

# Check if current time is within trading hours
def within_trading_hours():
    current_time = datetime.now().time()
    return market_open <= current_time <= market_close

# Close all open positions before market closes
def close_all_positions():
    global in_long_position
    global in_short_position
    stock_positions = rh.account.get_all_positions()
    
    for item in stock_positions:
        if item['symbol'] == symbol:
            shares_owned = float(item['quantity'])
            if shares_owned > 0:
                order = rh.orders.order(symbol        = symbol,
                                        quantity      = shares_owned,
                                        side          = "sell",
                                        extendedHours = True,
                                        market_hours  = "extended_hours")
                print(f"Closing all positions by selling {shares_owned} shares of {symbol}")
                in_long_position = False
        elif item['symbol'] == inverse_symbol:
            inverse_shares_owned = float(item['quantity'])
            if inverse_shares_owned > 0:
                order = rh.orders.order(symbol        = inverse_symbol,
                                        quantity      = inverse_shares_owned,
                                        side          = "sell",
                                        extendedHours = True,
                                        market_hours  = "extended_hours")
                print(f"Closing all positions by selling {inverse_shares_owned} shares of {inverse_symbol}")
                in_short_position = False

# Run the bot  
def run_bot():
    print(f"\nFetching new bars for {datetime.now().isoformat()}")
    bars = wb.get_bars(stock=symbol, interval='m1', count=100, extendTrading=1)
    df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    try:
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    except FloatingPointError:
        print("Invalid timestamp encountered.")
        return
    supertrend(df, period, factor)
    place_orders(df)

schedule.every(5).seconds.do(run_bot) #run the bot every 5 seconds

# Schedule position close at 3:59 PM
schedule.every().day.at("15:59").do(close_all_positions)

while True:
    schedule.run_pending() #run the scheduled tasks
    time.sleep(1) #wait 1 second