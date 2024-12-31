#
# This script logs into a Robinhood account using provided credentials and a Time-based One-Time Password (TOTP).
# It fetches the current open stock positions from the account with retry logic to handle rate limits.
# The script uses the following libraries:
# - pandas: for data manipulation and display settings
# - warnings: to suppress warnings
# - robin_stocks.robinhood: to interact with the Robinhood API
# - pyotp: to generate TOTP for multi-factor authentication
# - time: to handle delays between retries
#

import pandas as pd  # Import pandas for data manipulation
pd.set_option('display.max_rows', None)  # Set pandas to display all rows
import warnings  # Import warnings to suppress warnings
warnings.filterwarnings('ignore')  # Ignore all warnings
import robin_stocks.robinhood as rh  # Import Robinhood API wrapper
import pyotp  # Import pyotp for generating TOTP
import time  # Import time for handling delays

ROTH_IRA = "928817659"  # Roth IRA account number
username = 'midielhg@gmail.com'  # Robinhood username
password = 'nuGcej-famzoj-vafce12'  # Robinhood password
totp  = pyotp.TOTP("6XMSLHZHUD2EHAV7").now()  # Generate current TOTP
print("Current OTP:", totp)  # Print the current OTP

rh.login(username, password, mfa_code=totp)  # Log into Robinhood account

def fetch_positions_with_retry(max_retries=5, backoff_factor=1):  # Function to fetch positions with retry logic
    retries = 0  # Initialize retry counter
    while retries < max_retries:  # Loop until max retries reached
        try:
            positions = rh.account.get_open_stock_positions()  # Fetch open stock positions
            return positions  # Return positions if successful
        except Exception as e:  # Handle exceptions
            if '429' in str(e):  # Check if rate limit exceeded
                retries += 1  # Increment retry counter
                wait_time = backoff_factor * (2 ** retries)  # Calculate wait time
                print(f"Rate limit exceeded. Retrying in {wait_time} seconds...")  # Print retry message
                time.sleep(wait_time)  # Wait before retrying
            else:
                print(f"Error fetching positions: {e}")  # Print error message
                return []  # Return empty list if other error

positions = fetch_positions_with_retry()  # Fetch positions with retry logic

# Get all the symbols from the positions and create a list of symbols
symbols = [position['symbol'] for position in positions]
# Get how many shares of each symbol are in the account
shares = [round(float(position['quantity']), 2) for position in positions]
# Get the latest price of each symbol
prices = [round(float(price), 2) for price in rh.stocks.get_latest_price(symbols)]
# Calculate the market value by multiplying the shares by the price
market_values = [round(float(shares[i]) * float(prices[i]), 2) for i in range(len(symbols))]
# Get the percentage of the total value for each position in the account
percentages = [round((market_value / sum(market_values)) * 100, 2) for market_value in market_values]
print("Total Individual Account Market Value: ", sum(market_values))  # Print total market value

# Create a DataFrame to display the data in a table format
data = {
    'Symbol': symbols,
    'Price': prices,
    'Shares': shares,
    'Market Value': market_values,
    'Percentage': percentages
}
df = pd.DataFrame(data)  # Create DataFrame
print(df)  # Print DataFrame
print("total percentage:                            ", round(sum(percentages), 0))  # Print total percentage

# Ask the user how much money to use on the Roth IRA for the copy of the portfolio
total_cash = float(input("Enter the amount of money to use on the Roth IRA for the copy of the portfolio: "))

# Check if the Roth IRA account has some or all of the same positions as the individual account
# Get the total value of these positions in the Roth IRA account
# Calculate the percentage needed on the Roth IRA account to match the individual account
IRA_positions = rh.account.get_open_stock_positions(account_number=ROTH_IRA)  # Fetch Roth IRA positions
IRA_symbols = [position['symbol'] for position in IRA_positions]  # Get symbols in Roth IRA
IRA_shares = [round(float(position['quantity']), 2) for position in IRA_positions]  # Get shares in Roth IRA
IRA_prices = [round(float(price), 2) for price in rh.stocks.get_latest_price(IRA_symbols)]  # Get prices in Roth IRA
IRA_market_values = [round(float(IRA_shares[i]) * float(IRA_prices[i]), 2) for i in range(len(IRA_symbols))]  # Calculate market values in Roth IRA
IRA_percentages = [round((IRA_market_value / sum(IRA_market_values)) * 100, 2) for IRA_market_value in IRA_market_values]  # Calculate percentages in Roth IRA
print("Total Market Value in Roth IRA: ", sum(IRA_market_values))  # Print total market value in Roth IRA
print("total percentage in Roth IRA: ", sum(IRA_percentages))  # Print total percentage in Roth IRA

# Function to buy or sell shares if the position's percentage in the IRA account is less than the percentage in the Individual account
for i in range(len(symbols)):
    if symbols[i] in IRA_symbols:
        index = IRA_symbols.index(symbols[i])  # Get the index of the symbol in the IRA account
        target_market_value = (percentages[i] / 100) * total_cash  # Calculate the target market value for the symbol in the IRA account
        current_market_value = IRA_market_values[index]  # Get the current market value of the symbol in the IRA account
        difference_market_value = target_market_value - current_market_value  # Calculate the difference between the target and current market value
        quantity = round(difference_market_value / prices[i], 1)  # Calculate the quantity to buy or sell
        # Check if the percentage in the individual account is different from the percentage in the IRA account
        if percentages[i] != IRA_percentages[index]:
            if quantity > 0:
                if difference_market_value < 10.00:
                    print(f"Skipping buy order for {symbols[i]} as the expected purchase is under $10.00")
                    continue
                print("Buying ", quantity, " shares of ", symbols[i])
                order = rh.orders.order_buy_fractional_by_quantity(symbol=symbols[i], quantity=quantity, account_number=ROTH_IRA)
            else:
                print("No need to buy ", symbols[i], " in Roth IRA")
            if quantity < 0:
                quantity = abs(quantity)
                if abs(difference_market_value) < 10.00:
                    print(f"Skipping sell order for {symbols[i]} as the expected value to sell is under $10.00")
                    continue
                print("Selling ", quantity, " shares of ", symbols[i])
                order = rh.orders.order_sell_fractional_by_quantity(symbol=symbols[i], quantity=quantity, account_number=ROTH_IRA)
    if symbols[i] not in IRA_symbols:
        index = symbols.index(symbols[i])  # Get the index of the symbol in the individual account
        target_market_value = (percentages[i] / 100) * total_cash  # Calculate the target market value for the symbol in the IRA account
        current_market_value = 0  # Get the current market value of the symbol in the IRA account
        difference_market_value = target_market_value - current_market_value  # Calculate the difference between the target and current market value
        quantity = round(difference_market_value / prices[i], 1)  # Calculate the quantity to buy
        if difference_market_value < 10.00:
            print(f"Skipping buy order for {symbols[i]} as the expected purchase is under $10.00")
            continue
        print("Buying ", quantity, " shares of ", symbols[i])
        order = rh.orders.order_buy_fractional_by_quantity(symbol=symbols[i], quantity=quantity, account_number=ROTH_IRA)

# If the symbol in IRA is not on the individual account, sell all the shares
for i in range(len(IRA_symbols)):
    if IRA_symbols[i] not in symbols:
        quantity = round(float(IRA_shares[i]), 2)  # Get the quantity to sell
        if quantity * IRA_prices[i] < 10.00:
            print(f"Skipping sell order for {IRA_symbols[i]} as the expected value to sell is under $10.00")
            continue
        print("Selling ", quantity, " shares of ", IRA_symbols[i])
        try:
            order = rh.orders.order_sell_fractional_by_quantity(symbol=IRA_symbols[i], quantity=quantity, account_number=ROTH_IRA)
        except Exception as e:
            print(f"Error placing sell order for {IRA_symbols[i]}: {e}")
