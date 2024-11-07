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