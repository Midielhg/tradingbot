from flask import Flask, render_template, jsonify
import subprocess

app = Flask(__name__)
bot_process = None  # Global variable to store the bot process

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start-bot', methods=['POST'])
def start_bot():
    global bot_process
    if bot_process is None or bot_process.poll() is not None:  # Check if bot is not running
        bot_process = subprocess.Popen(['python', 'supertrend.py'])
        return jsonify({"status": "Bot started successfully"}), 200
    else:
        return jsonify({"status": "Bot is already running"}), 200

@app.route('/stop-bot', methods=['POST'])
def stop_bot():
    global bot_process
    if bot_process is not None and bot_process.poll() is None:  # Check if bot is running
        bot_process.terminate()
        bot_process = None
        return jsonify({"status": "Bot stopped successfully"}), 200
    else:
        return jsonify({"status": "Bot is not running"}), 200

if __name__ == '__main__':
    app.run(debug=True)
