from flask import Flask, request, jsonify, render_template
from src.agent.agent import run_agent
from src.chatbot.chatbot import run_chatbot

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/query', methods=['POST'])
def query():
    data = request.json
    mode = data.get('mode')  # 'chatbot' or 'agent'
    user_input = data.get('input')

    if mode == 'chatbot':
        response = run_chatbot(user_input)
    elif mode == 'agent':
        response = run_agent(user_input)
    else:
        return jsonify({"error": "Invalid mode"}), 400

    return jsonify({"response": response})

if __name__ == '__main__':
    app.run(debug=True)