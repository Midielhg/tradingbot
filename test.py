import os
import time
import pprint
import robin_stocks.robinhood as rh

rh.login(os.getenv('ROBINHOOD_USERNAME'), os.getenv('ROBINHOOD_PASSWORD'))

order = rh.orders.get_all_open_stock_orders()
# pprint.pprint(order)

order_id = order[0]['id']
while True:
    open_orders = rh.orders.get_all_open_stock_orders()
    order_status = None
    for open_order in open_orders:
        if open_order['id'] == order_id:
            order_status = open_order['state']
            print("Order pending")
            break
        else:
            print("Order not pending")
            order_status = "closed"
            break
    if open_order['id'] != order_id:
        break
    time.sleep(5)  # Add a delay to avoid excessive API calls
in_short_position = False