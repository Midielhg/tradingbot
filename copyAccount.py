#this code will copy the account from Robinhood Individual account to Robinhood IRA account
#first it will get all the open positions from the individual account
#get its total value and calculate the percentage of the total value for each position in the account
#then it will get the total available cash in the Robinhood IRA account
#and purchase the same percentage of each position in the IRA account

from webull import webull
import pandas as pd
pd.set_option('display.max_rows', None)
import warnings
warnings.filterwarnings('ignore')
import robin_stocks.robinhood as rh
wb = webull()
import os
import pyotp

ROTH_IRA = "928817659"

totp  = pyotp.TOTP("6XMSLHZHUD2EHAV7").now()
print("Current OTP:", totp)
rh.login(os.getenv('ROBINHOOD_USERNAME'), os.getenv('ROBINHOOD_PASSWORD'), mfa_code=totp)

try:
    positions = rh.account.get_open_stock_positions()
except Exception as e:
    print(f"Error fetching positions: {e}")
    positions = []

#get all the symbols from the positions and create a list of symbols
symbols = [position['symbol'] for position in positions]
#get how many shares of each symbol are in the account
shares = [round(float(position['quantity']), 2) for position in positions]
#get the latest price of each symbol
prices = [round(float(price), 2) for price in rh.stocks.get_latest_price(symbols)]
#calculate the market value by multiplying the shares by the price
market_values = [round(float(shares[i]) * float(prices[i]), 2) for i in range(len(symbols))]
#get the percentage of the total value for each position in the account
percentages = [round((market_value / sum(market_values)) * 100, 2) for market_value in market_values]
print("Total Individual Account Market Value: ", sum(market_values))
# Create a DataFrame to display the data in a table format
data = {
    'Symbol': symbols,
    'Price': prices,
    'Shares': shares,
    'Market Value': market_values,
    'Percentage': percentages
}
df = pd.DataFrame(data)
print(df)
print("total percentage:                            ", round(sum(percentages), 0))

# Ask the user how much money to use on the Roth IRA for the copy of the portfolio
total_cash = float(input("Enter the amount of money to use on the Roth IRA for the copy of the portfolio: "))

# check is the Roth IRA account has some or all of the same positions as the individual account
# get the total value of these positions in the Roth IRA account
# calculate the percentage needed on the Roth IRA account to match the individual account
IRA_positions = rh.account.get_open_stock_positions(account_number=ROTH_IRA)
IRA_symbols = [position['symbol'] for position in IRA_positions]
IRA_shares = [round(float(position['quantity']), 2) for position in IRA_positions]
IRA_prices = [round(float(price), 2) for price in rh.stocks.get_latest_price(IRA_symbols)]
IRA_market_values = [round(float(IRA_shares[i]) * float(IRA_prices[i]), 2) for i in range(len(IRA_symbols))]
IRA_percentages = [round((IRA_market_value / sum(IRA_market_values)) * 100, 2) for IRA_market_value in IRA_market_values]
print("Total Market Value in Roth IRA: ", sum(IRA_market_values))
print("total percentage in Roth IRA: ", sum(IRA_percentages))


      
# Function to buy or sell shares if the position's percentage in the IRA account is less than the percentage in the Individual account
for i in range(len(symbols)):
    if symbols[i] in IRA_symbols:
        index = IRA_symbols.index(symbols[i]) # get the index of the symbol in the IRA account
        target_market_value = (percentages[i] / 100) * total_cash # calculate the target market value for the symbol in the IRA account
        current_market_value = IRA_market_values[index] # get the current market value of the symbol in the IRA account
        difference_market_value = target_market_value - current_market_value # calculate the difference between the target and current market value
        quantity = round(difference_market_value / prices[i], 1)
        # Check if the percentage in the individual account is different from the percentage in the IRA account
        if percentages[i] != IRA_percentages[index]:
            if quantity > 0:
                print("Buying ", quantity, " shares of ", symbols[i])
                order = rh.orders.order_buy_fractional_by_quantity(symbol=symbols[i], quantity=quantity, account_number=ROTH_IRA)
                # order = rh.orders.order(symbol=symbols[i], quantity=quantity, side="buy", account_number=ROTH_IRA, extendedHours=True, market_hours="extended_hours")
            else:
                print("No need to buy ", symbols[i], " in Roth IRA")
            if quantity < 0:
                quantity = abs(quantity)
                print("Selling ", quantity, " shares of ", symbols[i])
                order = rh.orders.order_sell_fractional_by_quantity(symbol=symbols[i], quantity=quantity, account_number=ROTH_IRA)
    if symbols[i] not in IRA_symbols:
        index = symbols.index(symbols[i]) #get the index of the symbol in the individual account
        target_market_value = (percentages[i] / 100) * total_cash #calculate the target market value for the symbol in the IRA account
        current_market_value = 0 #get the current market value of the symbol in the IRA account
        difference_market_value = target_market_value - current_market_value
        quantity = round(difference_market_value / prices[i], 1)
        print("Buying ", quantity, " shares of ", symbols[i])
        order = rh.orders.order_buy_fractional_by_quantity(symbol=symbols[i], quantity=quantity, account_number=ROTH_IRA)



#if the symbol in IRA is not on the individual account, sell all the shares
for i in range(len(IRA_symbols)):
    if IRA_symbols[i] not in symbols:
        quantity = round(float(IRA_shares[i]), 2)
        print("Selling ", quantity, " shares of ", IRA_symbols[i])
        try:
            order = rh.orders.order_sell_fractional_by_quantity(symbol=IRA_symbols[i], quantity=quantity, account_number=ROTH_IRA)
            # order = rh.orders.order(symbol=IRA_symbols[i], quantity=quantity, side="sell", account_number=ROTH_IRA, extendedHours=True, market_hours="extended_hours")
        except Exception as e:
            print(f"Error placing sell order for {IRA_symbols[i]}: {e}")
