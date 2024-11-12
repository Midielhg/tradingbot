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

ticker = "TQQQ"
inverseTicker = "SQQQ"
asset = "stock"

# Bot Configuration
ticker = "TQQQ"
inverseTicker = "SQQQ"
period = 5
factor = 2
tradeAmount = 550
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
    print(df.tail(4)) #print the last 2 rows of the dataframe
    if not within_trading_hours():
        print("Outside trading hours. No trades will be placed.")
        return
    else:
        global in_longPosition
        stock_positions = rh.account.get_all_positions()
        stock_quote = rh.get_stock_quote_by_symbol(ticker)
   
        shares_ownerd = 0
        for item in stock_positions:
            if item['symbol'] == ticker:
                shares_ownerd = float(item['quantity'])
                market_value = shares_ownerd * float(stock_quote['last_trade_price'])
                print("\nYou own ", int(shares_ownerd), "shares of ", ticker, " with a Market Value of: $", float(market_value))

        shares_to_trade = int(tradeAmount // float(stock_quote['last_trade_price']))
        print("You can trade with ", shares_to_trade, " shares")

        if shares_ownerd > shares_to_trade:
            print("You own more share than the ones that you were willing to trade with. Selling some:")
            extra_shares = shares_ownerd - shares_to_trade
            order = rh.orders.order(symbol        = ticker,
                        quantity      = shares_ownerd,
                        side          = "sell",
                        extendedHours = True,
                        market_hours  = "extended_hours")
            print("Selling ",extra_shares, " extra shares of ", ticker )

        in_longPosition = market_value >= 1

        last_row_index = len(df.index) - 1 #get the index of the last row
        if df['in_uptrend'][last_row_index]:
            print("Current Trend: UpTrend")
            if not in_longPosition:
                order = rh.order_buy_market(ticker, shares_to_trade)
                print(f"Opening {ticker} position")
                pprint.pprint(order)
                in_longPosition = True  
            else:
                print("Already Long, Making Money")
        else:
            print("Current Trend: DownTrend")
            if in_longPosition:
                order = rh.orders.order(symbol        = ticker,
                                        quantity      = shares_ownerd,
                                        side          = "sell",
                                        extendedHours = True,
                                        market_hours  = "extended_hours")
                print(f"Selling {shares_ownerd} shares of {ticker}")
                pprint.pprint(order)
                in_longPosition = False
            else:
                print("No position open, Saving Money on downtrend")

# Check if current time is within trading hours
def within_trading_hours():
    current_time = datetime.now().time()
    return market_open <= current_time <= market_close

# Close all open positions before market closes
def close_all_positions():
    global in_longPosition
    stock_positions = rh.account.get_all_positions()

    for item in stock_positions:
        if item['symbol'] == ticker:
            shares_ownerd = float(item['quantity'])
            if shares_ownerd > 0:
                order = rh.orders.order(symbol        = ticker,
                        quantity      = shares_ownerd,
                        side          = "sell",
                        extendedHours = True,
                        market_hours  = "extended_hours")
                print(f"Closing all positions by selling {shares_ownerd} shares of {ticker}")
                pprint.pprint(order)
                in_longPosition = False

#Run the bot  
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

schedule.every(5).seconds.do(run_bot) #run the bot every 3 seconds

# Schedule position close at 3:59 PM
schedule.every().day.at("15:59").do(close_all_positions)

while True:
    schedule.run_pending() #run the scheduled tasks
    time.sleep(1) #wait 1 second