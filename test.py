import robin_stocks.robinhood as rh
import os
import pyotp
ROTH_IRA = "928817659"


totp  = pyotp.TOTP("6XMSLHZHUD2EHAV7").now()
print("Current OTP:", totp)
rh.login(os.getenv('ROBINHOOD_USERNAME'), os.getenv('ROBINHOOD_PASSWORD'), mfa_code=totp)



total_cash = rh.account.load_phoenix_account()['account_buying_power']
print("Portfolio Value ", ROTH_IRA, ": ", total_cash)