# app.py
from flask import Flask, jsonify, request
from datetime import datetime
import threading
import schedule
import time
import pandas as pd

app = Flask(__name__)
bot_running = False

# Configure and run the bot function here
def run_bot():
    global bot_running
    while bot_running:
        # Add your bot's data fetching and processing code here
        print(f"\nFetching new bars for {datetime.now().isoformat()}")
        # Simulation of bot data fetching
        time.sleep(3)

def start_bot():
    global bot_running
    bot_running = True
    thread = threading.Thread(target=run_bot)
    thread.start()

def stop_bot():
    global bot_running
    bot_running = False

@app.route('/start_bot', methods=['POST'])
def start_bot_api():
    start_bot()
    return jsonify({'status': 'Bot started'})

@app.route('/stop_bot', methods=['POST'])
def stop_bot_api():
    stop_bot()
    return jsonify({'status': 'Bot stopped'})

@app.route('/status', methods=['GET'])
def status_api():
    return jsonify({'bot_running': bot_running})

if __name__ == '__main__':
    app.run(debug=True)
