from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
from groq import Groq
import os
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv()

# Get API key
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY not found!")
print("✅ GROQ_API_KEY loaded")

client = Groq(api_key=api_key)

# Flask app
app = Flask(__name__, static_folder='.', static_url_path='')

# Session configuration for unique users
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

# Enable CORS with credentials
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# Conversation storage - keyed by unique user IDs
conversations = {}

# Serve index.html at root
@app.route('/')
def index():
    # Generate unique session ID for each user
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
        print(f"✅ New user session: {session['user_id'][:8]}...")
    
    return send_from_directory('.', 'index.html')

# Serve static files (CSS, JS)
@app.route('/<path:filename>')
def serve_file(filename):
    return send_from_directory('.', filename)

# API Status endpoint
@app.route('/api/status')
def status():
    return jsonify({
        "status": "🤖 AI Chatbot API Running",
        "version": "1.0",
        "endpoints": {
            "chat": "/api/chat",
            "clear": "/api/clear"
        }
    })

# Chat endpoint - with user isolation
@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message')
        
        if not user_message:
            return jsonify({"error": "No message provided"}), 400
        
        # Get unique user ID
        if 'user_id' not in session:
            session['user_id'] = str(uuid.uuid4())
        
        user_id = session['user_id']
        
        # Initialize conversation for THIS user only
        if user_id not in conversations:
            conversations[user_id] = []
            print(f"🆕 Started new conversation for user: {user_id[:8]}...")
        
        print(f"👤 User {user_id[:8]}: {user_message}")
        
        # Add to THIS user's conversation
        conversations[user_id].append({
            "role": "user",
            "content": user_message
        })
        
        # Call Groq API with THIS user's history only
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=conversations[user_id],
            temperature=0.7,
            max_tokens=1000
        )
        
        ai_response = response.choices[0].message.content
        print(f"🤖 AI to {user_id[:8]}: {ai_response[:50]}...")
        
        # Add to THIS user's conversation
        conversations[user_id].append({
            "role": "assistant",
            "content": ai_response
        })
        
        # Keep only last 20 messages per user (memory management)
        if len(conversations[user_id]) > 20:
            conversations[user_id] = conversations[user_id][-20:]
        
        print(f"📊 User {user_id[:8]} has {len(conversations[user_id])} messages")
        
        return jsonify({
            "response": ai_response,
            "status": "success"
        })
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

# Clear conversation - only THIS user's history
@app.route('/api/clear', methods=['POST'])
def clear_history():
    try:
        if 'user_id' in session:
            user_id = session['user_id']
            
            if user_id in conversations:
                conversations[user_id] = []
                print(f"🗑️ Cleared conversation for user: {user_id[:8]}")
        
        return jsonify({"status": "cleared"})
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print("\n" + "="*50)
    print("🤖 Multi-User AI Chatbot")
    print("="*50)
    print(f"🌐 Frontend: http://localhost:{port}")
    print(f"📡 API: http://localhost:{port}/api/status")
    print("✅ User isolation: ENABLED")
    print("="*50 + "\n")
    
    app.run(host='0.0.0.0', port=port, debug=True)
