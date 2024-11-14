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

# Initialize Webull and Robinhood
wb = webull()
login = rh.login('midielhg@gmail.com', 'nuGcej-famzoj-vafce12')
print("Welcome Back to the SuperTrend Bot")

# Bot Configuration
ticker = "TQQQ"
inverse_ticker = "SQQQ"
period = 5
factor = 2
trade_amount = 5000
market_value = 0

# Define Trading Hours (9:30 AM to 4:00 PM)
market_open = dtime(9, 30)
market_close = dtime(16, 0)

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

#buy and sell signals
def place_orders(df):
    print(df.tail(2)) #print the last 2 rows of the dataframe
    # if not within_trading_hours():
    #     print("Outside trading hours. No trades will be placed.")
    #     return
# else:
    global in_long_position
    stock_positions = rh.account.get_all_positions()
    stock_quote = rh.get_stock_quote_by_symbol(ticker)
    inverse_stock_quote = rh.get_stock_quote_by_symbol(inverse_ticker)
    
    shares_owned = 0
    for item in stock_positions:
        if item['symbol'] == ticker:
            shares_owned = float(item['quantity'])
            market_value = shares_owned * float(stock_quote['last_trade_price'])
            #ticker trail amount = 0.02% of the last trade price
            ticker_trail_amount = round(float(stock_quote['last_trade_price']) * 0.0002, 3)
              
            if shares_owned > 0:
                print("\nYou own ", int(shares_owned), "shares of ", ticker, " with a Market Value of: $", float(market_value))
        elif item['symbol'] == inverse_ticker:
            inverse_shares_owned = float(item['quantity'])
            inverse_market_value = inverse_shares_owned * float(stock_quote['last_trade_price'])
            inverse_ticker_trail_amount = round(float(inverse_stock_quote['last_trade_price']) * 0.0002, 3)
            if inverse_shares_owned:
                print("\nYou own ", int(inverse_shares_owned), "shares of ", inverse_ticker, " with a Market Value of: $", float(inverse_market_value))
    
    shares_to_trade = int(trade_amount // float(stock_quote['last_trade_price']))
    inverse_shares_to_trade = int(trade_amount // float(inverse_stock_quote['last_trade_price']))
    
    if shares_owned > shares_to_trade:
        print("You own more share than the ones that you were willing to trade with. Selling some:")
        extra_shares = shares_owned - shares_to_trade
        rh.orders.order(symbol        = ticker,
                        quantity      = shares_owned,
                        side          = "sell",
                        extendedHours = True,
                        market_hours  = "extended_hours")
        print("Selling ",extra_shares, " extra shares of ", ticker )
    if inverse_shares_owned > inverse_shares_to_trade:
        print("You own more share than the ones that you were willing to trade with. Selling some:")
        inverse_extra_shares = inverse_shares_owned - inverse_shares_to_trade
        rh.orders.order(symbol        = inverse_ticker,
                        quantity      = inverse_shares_owned,
                        side          = "sell",
                        extendedHours = True,
                        market_hours  = "extended_hours")
        print("Selling ",inverse_extra_shares, " extra shares of ", inverse_ticker )
    
    in_long_position = market_value >= 1
    in_short_position = inverse_market_value >=1
    
    
    
    last_row_index = len(df.index) - 1 #get the index of the last row
    if df['in_uptrend'][last_row_index]:
        print("Current Trend: UpTrend")
        print("You can trade with ", shares_to_trade, " shares")
        if not in_long_position:
            order = rh.orders.order(symbol        = ticker,
                                    quantity      = shares_to_trade,
                                    side          = "buy",
                                    extendedHours = True,
                                    market_hours  = "extended_hours")                
            print(f"Opening {ticker} position")
            print(order)
            in_long_position = True  
            trailing_stop = rh.orders.order_trailing_stop(
                                    symbol = ticker,
                                    quantity = shares_to_trade,
                                    side = "sell",
                                    trailAmount = ticker_trail_amount,
                                    trailType = 'amount',
                                    timeInForce = 'gtc',
                                    jsonify= True
                                )
            print(f"Trailing Stop Order for {ticker} position")
            print (trailing_stop)
                                                
        if in_short_position:
            print("In Short Position")
            order = rh.orders.order(symbol        = inverse_ticker,
                                    quantity      = inverse_shares_owned,
                                    side          = "sell",
                                    extendedHours = True,
                                    market_hours  = "extended_hours")
            print(f"Closing {inverse_ticker} position")
            print(order)
            in_short_position = False
    else:
        print("Current Trend: DownTrend")
        print("You can trade with ", inverse_shares_to_trade, " shares")
        if in_long_position:
            print("In Long Position")
            order = rh.orders.order(symbol        = ticker,
                                    quantity      = shares_owned,
                                    side          = "sell",
                                    extendedHours = True,
                                    market_hours  = "extended_hours")
            print(f"Closing {ticker} position")
            print(order)
            in_long_position = False
        if not in_short_position:
            order = rh.orders.order(symbol        = inverse_ticker,
                                    quantity      = inverse_shares_to_trade,
                                    side          = "buy",
                                    extendedHours = True,
                                    market_hours  = "extended_hours")
            print(f"Opening {inverse_ticker} position")
            print(order)
            in_short_position = True
            trailing_stop = rh.orders.order_trailing_stop(
                                    symbol = inverse_ticker ,
                                    quantity = inverse_shares_to_trade,
                                    side = "sell",
                                    trailAmount = inverse_ticker_trail_amount,
                                    trailType = 'amount',
                                    timeInForce = 'gtc',
                                    jsonify= True
                    )
            print(f"Trailing Stop Order for {ticker} position")
            print (trailing_stop)

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
        if item['symbol'] == ticker:
            shares_owned = float(item['quantity'])
            if shares_owned > 0:
                order = rh.orders.order(symbol        = ticker,
                                        quantity      = shares_owned,
                                        side          = "sell",
                                        extendedHours = True,
                                        market_hours  = "extended_hours")
                print(f"Closing all positions by selling {shares_owned} shares of {ticker}")
                print(order)
                in_long_position = False
        elif item['symbol'] == inverse_ticker:
            inverse_shares_owned = float(item['quantity'])
            if inverse_shares_owned > 0:
                order = rh.orders.order(symbol        = inverse_ticker,
                                        quantity      = inverse_shares_owned,
                                        side          = "sell",
                                        extendedHours = True,
                                        market_hours  = "extended_hours")
                print(f"Closing all positions by selling {inverse_shares_owned} shares of {inverse_ticker}")
                print(order)
                in_short_position = False

# Run the bot  
def run_bot():
    print(f"\nFetching new bars for {datetime.now().isoformat()}")
    bars = wb.get_bars(stock=ticker, interval='m1', count=100, extendTrading=1)
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