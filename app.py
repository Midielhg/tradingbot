from flask import Flask, render_template, request, jsonify
import threading
from bot import start_bot

app = Flask(__name__)

# Endpoint to start the bot
@app.route('/start_bot', methods=['POST'])
def start_bot_endpoint():
    threading.Thread(target=start_bot).start()
    return jsonify({"message": "Bot started"}), 200

# Homepage to control the bot
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)
