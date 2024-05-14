import robin_stocks.robinhood as rh
import sys
import os
import pyotp
import robin_stocks as rb

login = rh.login('midielhg@gmail.com','nuGcej-famzoj-vafce1')

symbol = 'SAVE'
quantity = 1

    
last_price = rh.get_latest_price(symbol)
last_price = float(last_price[0])
print("last price: $", last_price)

after_hours_price = rh.get_latest_price(symbol, includeExtendedHours=True)
print("after hours price: $", after_hours_price[0])

# place buy order on extended hours


buy_order = rh.orders.order_buy_limit(symbol, quantity, last_price, account_number=None, timeInForce='gtc', extendedHours=True, jsonify=True)

print("buy order: ", buy_order)
