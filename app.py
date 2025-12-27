from flask import Flask, request, jsonify, send_from_directory, session, abort
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from groq import Groq
import os
from dotenv import load_dotenv
import uuid
import logging
from datetime import datetime

# Load environment variables
load_dotenv()

# Validate API key
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    raise ValueError("❌ GROQ_API_KEY not found in environment variables!")

if not api_key.startswith("gsk_"):
    raise ValueError("❌ GROQ_API_KEY format is invalid!")

print("✅ GROQ_API_KEY loaded")

# Initialize Groq client
try:
    client = Groq(api_key=api_key)
    print("✅ Groq client initialized")
except Exception as e:
    print(f"❌ Failed to initialize Groq client: {e}")
    raise

# Initialize Flask app
app = Flask(__name__, static_folder='static')
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# CORS configuration (restrict to your domain in production)
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://sarvesh.codes", "https://www.sarvesh.codes"],
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type"]
    }
})

# Rate limiting - protects against abuse
def get_real_ip():
    """Get real IP from behind Render proxy"""
    return request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()

limiter = Limiter(
    app=app,
    key_func=get_real_ip,
    default_limits=["200 per hour"],
    storage_uri="memory://"
)

# Store conversations per user session
conversations = {}

# Blocked paths and patterns
BLOCKED_PATHS = [
    '/wp-admin', '/wp-includes', '/wp-content', '/wp-login',
    '/wordpress', '/xmlrpc', '/phpmyadmin', '/.env', '/.git',
    '/admin', '/administrator', '/config', '/.aws', '/.ssh'
]

BLOCKED_EXTENSIONS = ['.php', '.asp', '.aspx', '.jsp', '.cgi']

# Security headers
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# Request logging and blocking
@app.before_request
def security_checks():
    """Security checks before processing any request"""
    real_ip = get_real_ip()
    user_agent = request.headers.get('User-Agent', 'Unknown')
    path = request.path.lower()
    
    # Log all requests
    logger.info(f"Request: {real_ip} → {request.method} {request.path} | UA: {user_agent[:50]}")
    
    # Block malicious paths
    for blocked in BLOCKED_PATHS:
        if blocked in path:
            logger.warning(f"🚨 BLOCKED: {real_ip} tried to access {request.path}")
            abort(403)
    
    # Block malicious file extensions
    for ext in BLOCKED_EXTENSIONS:
        if path.endswith(ext):
            logger.warning(f"🚨 BLOCKED: {real_ip} tried to access {ext} file")
            abort(403)
    
    # Block requests with double slashes (CDN hijacking attempts)
    if '//' in request.path and not request.path.startswith('//'):
        logger.warning(f"🚨 BLOCKED: {real_ip} - double slash in path")
        abort(403)
    
    # Block suspicious user agents
    suspicious_agents = ['sqlmap', 'nikto', 'nmap', 'masscan', 'nessus']
    if any(agent in user_agent.lower() for agent in suspicious_agents):
        logger.warning(f"🚨 BLOCKED: {real_ip} - suspicious user agent: {user_agent}")
        abort(403)

# Routes
@app.route('/')
@limiter.limit("30 per minute")
def index():
    """Serve the main chatbot interface"""
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
        print(f"✅ New user session: {session['user_id'][:12]}...")
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files securely"""
    # Prevent directory traversal
    if '..' in filename or filename.startswith('/'):
        abort(403)
    
    # Only allow specific file types
    allowed_extensions = ['.html', '.css', '.js', '.ico', '.png', '.jpg', '.svg']
    if not any(filename.endswith(ext) for ext in allowed_extensions):
        abort(403)
    
    try:
        return send_from_directory('.', filename)
    except:
        abort(404)

@app.route('/robots.txt')
def robots():
    """Robots.txt to guide search engines"""
    return """User-agent: *
Disallow: /api/
Disallow: /wp-admin/
Disallow: /wordpress/
Disallow: /.git/
Allow: /

User-agent: GPTBot
Allow: /

User-agent: OAI-SearchBot
Allow: /
""", 200, {'Content-Type': 'text/plain'}

@app.route('/health')
def health():
    """Health check endpoint for monitoring"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "chatbot-api"
    }), 200

@app.route('/api/status')
def api_status():
    """API status endpoint"""
    return jsonify({
        "status": "🤖 AI Chatbot API Running",
        "version": "2.0",
        "model": "llama-3.3-70b-versatile"
    })

@app.route('/api/chat', methods=['POST'])
@limiter.limit("20 per minute")
def chat():
    """Handle chat requests with rate limiting"""
    try:
        # Get user session
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                'status': 'error',
                'error': 'No session found'
            }), 401
        
        # Validate request
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({
                'status': 'error',
                'error': 'Message is required'
            }), 400
        
        user_message = data['message'].strip()
        
        # Validate message length
        if len(user_message) == 0:
            return jsonify({
                'status': 'error',
                'error': 'Message cannot be empty'
            }), 400
        
        if len(user_message) > 2000:
            return jsonify({
                'status': 'error',
                'error': 'Message too long (max 2000 characters)'
            }), 400
        
        # Initialize conversation for new users
        if user_id not in conversations:
            conversations[user_id] = []
        
        # Add user message to conversation
        conversations[user_id].append({
            "role": "user",
            "content": user_message
        })
        
        # Limit conversation history to last 20 messages (memory optimization)
        if len(conversations[user_id]) > 20:
            conversations[user_id] = conversations[user_id][-20:]
        
        # Get AI response
        try:
            chat_completion = client.chat.completions.create(
                messages=conversations[user_id],
                model="llama-3.3-70b-versatile",
                temperature=0.7,
                max_tokens=1024,
                top_p=0.9,
            )
            
            assistant_message = chat_completion.choices[0].message.content
            
            # Add assistant response to conversation
            conversations[user_id].append({
                "role": "assistant",
                "content": assistant_message
            })
            
            return jsonify({
                'status': 'success',
                'response': assistant_message
            })
            
        except Exception as e:
            logger.error(f"Groq API error: {str(e)}")
            return jsonify({
                'status': 'error',
                'error': 'AI service temporarily unavailable'
            }), 503
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': 'Internal server error'
        }), 500

@app.route('/api/clear', methods=['POST'])
@limiter.limit("10 per minute")
def clear_conversation():
    """Clear conversation history"""
    user_id = session.get('user_id')
    if user_id and user_id in conversations:
        del conversations[user_id]
    return jsonify({'status': 'success', 'message': 'Conversation cleared'})

# Error handlers
@app.errorhandler(403)
def forbidden(e):
    """Handle forbidden access"""
    return jsonify({
        'status': 'error',
        'error': 'Access forbidden'
    }), 403

@app.errorhandler(404)
def not_found(e):
    """Handle not found errors"""
    return jsonify({
        'status': 'error',
        'error': 'Resource not found'
    }), 404

@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded"""
    return jsonify({
        'status': 'error',
        'error': 'Rate limit exceeded. Please try again later.'
    }), 429

@app.errorhandler(500)
def internal_error(e):
    """Handle internal server errors"""
    logger.error(f"Internal server error: {str(e)}")
    return jsonify({
        'status': 'error',
        'error': 'Internal server error'
    }), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"🤖 Secure Multi-User AI Chatbot")
    print(f"🌐 Server: http://0.0.0.0:{port}")
    print(f"🛡️ Security: Rate limiting, path blocking, headers enabled")
    app.run(host='0.0.0.0', port=port, debug=False)
