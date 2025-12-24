from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from groq import Groq
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY not found!")

print("✅ GROQ_API_KEY loaded")

client = Groq(api_key=api_key)

# Flask app with static folder set to current directory
app = Flask(__name__, static_folder='.', static_url_path='')

# Enable CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})

conversation_history = []

# Serve index.html at root
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# Serve static files (CSS, JS)
@app.route('/<path:filename>')
def serve_file(filename):
    return send_from_directory('.', filename)

# API Status endpoint
@app.route('/api/status')
def status():
    return jsonify({
        "status": "🦙 Llama AI Chatbot API Running",
        "version": "1.0",
        "endpoints": {
            "chat": "/api/chat",
            "clear": "/api/clear"
        }
    })

# Chat endpoint
@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message')
        
        if not user_message:
            return jsonify({"error": "No message provided"}), 400
        
        print(f"User: {user_message}")
        
        conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # ✅ New, recommended
            messages=conversation_history,
            temperature=0.7,
            max_tokens=1000
    )   

        
        ai_response = response.choices[0].message.content
        print(f"AI: {ai_response[:50]}...")
        
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

# Clear conversation
@app.route('/api/clear', methods=['POST'])
def clear_history():
    global conversation_history
    conversation_history = []
    return jsonify({"status": "cleared"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print("\n" + "="*50)
    print("🦙 Llama AI Chatbot")
    print("="*50)
    print(f"🌐 Frontend: http://localhost:{port}")
    print(f"📡 API: http://localhost:{port}/api/status")
    print("="*50 + "\n")
    app.run(host='0.0.0.0', port=port, debug=True)
