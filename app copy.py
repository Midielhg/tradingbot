from flask import Flask, render_template, jsonify, Response
import subprocess
import threading
import pandas as pd
from datetime import datetime
from webull import webull
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

wb = webull()

app = Flask(__name__)
bot_process = None  # Global variable to store the bot process
log_lines = []  # List to store log lines

def read_process_output(process):
    global log_lines
    while True:
        output = process.stdout.readline()
        if output == b'' and process.poll() is not None:
            break
        if output:
            decoded_line = output.decode('utf-8').strip()
            log_lines.append(decoded_line)
            logging.debug(f"STDOUT: {decoded_line}")
            print(decoded_line)
            if len(log_lines) > 100:  # Limit log lines to the last 100 entries
                log_lines.pop(0)
        error = process.stderr.readline()
        if error:
            decoded_error = error.decode('utf-8').strip()
            log_lines.append(decoded_error)
            logging.debug(f"STDERR: {decoded_error}")
            print(decoded_error)
            if len(log_lines) > 100:  # Limit log lines to the last 100 entries
                log_lines.pop(0)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start-bot', methods=['POST'])
def start_bot():
    global bot_process
    if bot_process is None or bot_process.poll() is not None:  # Check if bot is not running
        logging.debug("Starting bot process...")
        bot_process = subprocess.Popen(['python', 'supertrend.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1, universal_newlines=True)
        threading.Thread(target=read_process_output, args=(bot_process,)).start()
        return jsonify({"status": "Bot started successfully"}), 200
    else:
        logging.debug("Bot is already running.")
        return jsonify({"status": "Bot is already running"}), 200

@app.route('/stop-bot', methods=['POST'])
def stop_bot():
    global bot_process
    if bot_process is not None and bot_process.poll() is None:  # Check if bot is running
        logging.debug("Stopping bot process...")
        bot_process.terminate()
        bot_process = None
        return jsonify({"status": "Bot stopped successfully"}), 200
    else:
        logging.debug("Bot is not running.")
        return jsonify({"status": "Bot is not running"}), 200

@app.route('/logs')
def logs():
    return jsonify({"logs": log_lines})

@app.route('/chart-data')
def chart_data():
    # Fetch the latest ticker data
    bars = wb.get_bars(stock='TQQQ', interval='m1', count=100, extendTrading=1)
    df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    timestamps = df['timestamp'].tolist()
    prices = df['close'].tolist()
    return jsonify({"timestamps": timestamps, "prices": prices})

if __name__ == '__main__':
    logging.debug("Starting Flask app...")
    app.run(debug=True)
