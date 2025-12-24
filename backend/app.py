from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq
import os

# Get API key from environment variable
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

app = Flask(__name__)

# Allow all origins (you can restrict this later)
CORS(app, resources={r"/api/*": {"origins": "*"}})

conversation_history = []

@app.route('/')
def index():
    return jsonify({
        "status": "🦙 Llama AI Chatbot API Running",
        "version": "1.0",
        "endpoints": {
            "chat": "/api/chat",
            "clear": "/api/clear"
        }
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message')
        
        if not user_message:
            return jsonify({"error": "No message provided"}), 400
        
        conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        response = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=conversation_history,
            temperature=0.7,
            max_tokens=1000
        )
        
        ai_response = response.choices[0].message.content
        
        conversation_history.append({
            "role": "assistant",
            "content": ai_response
        })
        
        return jsonify({
            "response": ai_response,
            "status": "success"
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@app.route('/api/clear', methods=['POST'])
def clear_history():
    global conversation_history
    conversation_history = []
    return jsonify({"status": "cleared"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
