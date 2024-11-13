
#!/bin/bash

# Upgrade pip
python3 -m pip install --upgrade pip

# Install required packages
pip install -r requirements.txt

# Install additional packages
pip install webull robin_stocks schedule

# Clone and install robin_stocks
git clone https://github.com/jmfernandes/robin_stocks.git
cd robin_stocks
pip install .
cd ..

echo "Dependencies installed."