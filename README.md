# Setup 

pip install -r requirements.txt


intall the following packages
python3 -m pip install --upgrade pip
pip install webull
pip install robin_stocks
pip install schedule
git clone https://github.com/jmfernandes/robin_stocks.git 
>>> cd robin_stocks
pip install .


run the following command to start the script
  python -u "/workspaces/Robinhood/BarUpDown.py"


  
python -u "c:\Users\Midiel\OneDrive\Desktop\tradingbot\BarUpDown.py"






Solution for "Extended hours and market hours mismatch."


robin_stocks.robinhood.orders.order(symbol        = "DIS",
                                    quantity      = 1,
                                    side          = "buy",
                                    limitPrice    = 91.02,
                                    extendedHours = True,
                                    market_hours  = "extended_hours")

install flash





Trading bot for Robinhood accounts

For more info: https://medium.com/@kev.guo123/building-a-robinhood-stock-trading-bot-8ee1b040ec6a

5/1/19: Since Robinhood has updated it's API, you now have to enter a 2 factor authentication code whenever you run the script. To do this, go to the Robinhood mobile app and enable two factor authentication in your settings. You will now receive an SMS code when you run the script, which you have to enter into the script.

2/23/21: Check out this documentation page for a possible workaround https://github.com/jmfernandes/robin_stocks/blob/master/Robinhood.rst

This project supports Python 3.7+

To Install:

git clone https://github.com/2018kguo/RobinhoodBot.git
cd RobinhoodBot/
pip install -r requirements.txt
cp config.py.sample config.py # add auth info after copying
To Run:

cd RobinboodBot/robinhoodbot (If outside of root directory)
python3 main.py