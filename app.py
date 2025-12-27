from flask import Flask, request, jsonify, send_from_directory, session, abort
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from groq import Groq
import os
from dotenv import load_dotenv
import uuid
import logging
from datetime import datetime, timedelta
from collections import defaultdict
import re

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

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# CORS configuration
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://sarvesh.codes", "https://www.sarvesh.codes"],
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type"]
    }
})

# IP tracking and blocking
blocked_ips = set()
suspicious_ips = defaultdict(int)
ip_request_history = defaultdict(list)
ip_bot_score = defaultdict(int)

# Bot detection patterns
BOT_USER_AGENTS = [
    'bot', 'crawl', 'spider', 'scraper', 'curl', 'wget', 'python-requests',
    'selenium', 'headless', 'phantom', 'scrapy', 'apache-httpclient',
    'go-http-client', 'java/', 'libwww', 'perl', 'scanner', 'nikto',
    'nmap', 'masscan', 'nessus', 'sqlmap', 'metasploit', 'burp',
    'zap', 'acunetix', 'openvas', 'grabber', 'dirbuster', 'gobuster',
    'wpscan', 'joomla-scan', 'nuclei', 'shodan', 'censys', 'zoomeye'
]

# Whitelist legitimate bots (allow these)
LEGITIMATE_BOTS = [
    'googlebot', 'bingbot', 'slackbot', 'twitterbot', 'facebookexternalhit',
    'linkedinbot', 'whatsapp', 'telegrambot', 'discordbot', 'oai-searchbot',
    'gptbot', 'claudebot', 'anthropic-ai', 'perplexitybot'
]

# Blocked paths
BLOCKED_PATHS = [
    '/wp-admin', '/wp-includes', '/wp-content', '/wp-login', '/wp-config',
    '/wordpress', '/xmlrpc', '/phpmyadmin', '/admin', '/administrator',
    '/.env', '/.git', '/.svn', '/.hg', '/config', '/.aws', '/.ssh',
    '/.docker', '/backup', '/db', '/database', '/sql', '/.bash_history'
]

BLOCKED_EXTENSIONS = ['.php', '.asp', '.aspx', '.jsp', '.cgi', '.pl', '.py']

# Get real IP from behind proxy
def get_real_ip():
    """Extract real IP from X-Forwarded-For header"""
    if 'X-Forwarded-For' in request.headers:
        # X-Forwarded-For can be: "client, proxy1, proxy2"
        ip_list = request.headers['X-Forwarded-For'].split(',')
        real_ip = ip_list[0].strip()
    elif 'X-Real-IP' in request.headers:
        real_ip = request.headers['X-Real-IP']
    else:
        real_ip = request.remote_addr
    
    return real_ip

# Rate limiting with real IP
limiter = Limiter(
    app=app,
    key_func=get_real_ip,
    default_limits=["200 per hour"],
    storage_uri="memory://",
    headers_enabled=True
)

# Store conversations per user session
conversations = {}

# Bot detection function
def is_bot():
    """Detect if request is from a bot"""
    user_agent = request.headers.get('User-Agent', '').lower()
    real_ip = get_real_ip()
    
    # Check if IP is already blocked
    if real_ip in blocked_ips:
        return True, "IP is blocked"
    
    # Check for legitimate bots first (allow them)
    for legitimate_bot in LEGITIMATE_BOTS:
        if legitimate_bot in user_agent:
            logger.info(f"✅ Legitimate bot allowed: {user_agent[:50]} from {real_ip}")
            return False, None
    
    # Check for malicious bot user agents
    for bot_pattern in BOT_USER_AGENTS:
        if bot_pattern in user_agent:
            ip_bot_score[real_ip] += 5
            logger.warning(f"🤖 Bot detected: {user_agent[:50]} from {real_ip}")
            return True, f"Bot user agent detected: {bot_pattern}"
    
    # Check for missing or suspicious user agent
    if not user_agent or len(user_agent) < 10:
        ip_bot_score[real_ip] += 2
        return True, "Missing or suspicious user agent"
    
    # Check for rapid requests (more than 10 in 10 seconds)
    now = datetime.now()
    ip_request_history[real_ip].append(now)
    
    # Clean old requests (older than 10 seconds)
    ip_request_history[real_ip] = [
        ts for ts in ip_request_history[real_ip]
        if now - ts < timedelta(seconds=10)
    ]
    
    if len(ip_request_history[real_ip]) > 10:
        ip_bot_score[real_ip] += 3
        logger.warning(f"⚡ Rapid requests detected from {real_ip}: {len(ip_request_history[real_ip])} in 10s")
        return True, "Too many rapid requests"
    
    # Check bot score threshold
    if ip_bot_score[real_ip] >= 10:
        blocked_ips.add(real_ip)
        logger.error(f"🚫 IP BLOCKED due to high bot score: {real_ip} (score: {ip_bot_score[real_ip]})")
        return True, "Bot score threshold exceeded"
    
    return False, None

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
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:;"
    return response

# Advanced request logging and security checks
@app.before_request
def security_checks():
    """Comprehensive security checks before processing any request"""
    real_ip = get_real_ip()
    user_agent = request.headers.get('User-Agent', 'Unknown')
    path = request.path.lower()
    method = request.method
    referrer = request.headers.get('Referer', 'Direct')

    WORDPRESS_SIGNATURES = ['/wp-', '/wp-content', '/wp-includes', 'wp-admin', 'wp-login']

    for sig in WORDPRESS_SIGNATURES:
        if sig in path:
            suspicious_ips[real_ip] += 1
            logger.warning(f"🚨 WordPress pattern hit: {real_ip} → {path}")

    # Log all requests with real IP
    logger.info(f"📍 {method} {path} | IP: {real_ip} | UA: {user_agent[:60]}")

    # If this IP is already over threshold, block hard
    if suspicious_ips[real_ip] >= 5:
        blocked_ips.add(real_ip)

    
    # Bot detection
    is_bot_request, bot_reason = is_bot()
    if is_bot_request:
        logger.warning(f"🤖 BOT BLOCKED: {real_ip} | Reason: {bot_reason} | Path: {path}")
        abort(403)
    
    # Block malicious paths
    for blocked in BLOCKED_PATHS:
        if blocked in path:
            suspicious_ips[real_ip] += 1
            logger.warning(f"🚨 BLOCKED PATH: {real_ip} → {path} | Referrer: {referrer}")
            
            # Auto-block after 5 suspicious requests
            if suspicious_ips[real_ip] >= 5:
                blocked_ips.add(real_ip)
                logger.error(f"🚫 IP AUTO-BLOCKED: {real_ip} (5+ suspicious requests)")
            
            abort(403)
    
    # Block malicious file extensions
    for ext in BLOCKED_EXTENSIONS:
        if path.endswith(ext):
            suspicious_ips[real_ip] += 1
            logger.warning(f"🚨 BLOCKED EXTENSION: {real_ip} tried to access {ext} file")
            abort(403)
    
    # Block double slash attacks (CDN hijacking)
    if '//' in path[1:]:  # Ignore first slash
        logger.warning(f"🚨 DOUBLE SLASH ATTACK: {real_ip} → {path}")
        abort(403)
    
    # Block directory traversal attempts
    if '..' in path or '%2e%2e' in path.lower():
        blocked_ips.add(real_ip)
        logger.error(f"🚫 DIRECTORY TRAVERSAL BLOCKED: {real_ip} → {path}")
        abort(403)

# Routes
@app.route('/')
@limiter.limit("30 per minute")
def index():
    """Serve the main chatbot interface"""
    real_ip = get_real_ip()
    
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
        logger.info(f"✅ New user session: {session['user_id'][:12]}... from {real_ip}")
    
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files securely"""
    # Prevent directory traversal
    if '..' in filename or filename.startswith('/'):
        abort(403)
    
    # Only allow specific file types
    allowed_extensions = ['.html', '.css', '.js', '.ico', '.png', '.jpg', '.jpeg', '.svg', '.gif', '.webp']
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

# Legitimate AI bots
User-agent: GPTBot
Allow: /

User-agent: OAI-SearchBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: PerplexityBot
Allow: /

# Block malicious scanners
User-agent: AhrefsBot
Disallow: /

User-agent: SemrushBot
Disallow: /

User-agent: MJ12bot
Disallow: /

User-agent: dotbot
Disallow: /
""", 200, {'Content-Type': 'text/plain'}

@app.route('/health')
def health():
    """Health check endpoint for monitoring"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "chatbot-api",
        "blocked_ips": len(blocked_ips),
        "suspicious_ips": len(suspicious_ips)
    }), 200

@app.route('/api/status')
def api_status():
    """API status endpoint"""
    return jsonify({
        "status": "🤖 AI Chatbot API Running",
        "version": "2.1",
        "model": "llama-3.3-70b-versatile",
        "security": "IP tracking & bot blocking enabled"
    })

@app.route('/api/chat', methods=['POST'])
@limiter.limit("20 per minute")
def chat():
    """Handle chat requests with rate limiting"""
    real_ip = get_real_ip()
    
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
        
        logger.info(f"💬 Chat request from {real_ip} | User: {user_id[:8]}... | Message: {user_message[:50]}...")
        
        # Initialize conversation for new users
        if user_id not in conversations:
            conversations[user_id] = []
        
        # Add user message to conversation
        conversations[user_id].append({
            "role": "user",
            "content": user_message
        })
        
        # Limit conversation history to last 20 messages
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
            
            logger.info(f"✅ Chat response sent to {real_ip}")
            
            return jsonify({
                'status': 'success',
                'response': assistant_message
            })
            
        except Exception as e:
            logger.error(f"❌ Groq API error for {real_ip}: {str(e)}")
            return jsonify({
                'status': 'error',
                'error': 'AI service temporarily unavailable'
            }), 503
        
    except Exception as e:
        logger.error(f"❌ Chat error for {real_ip}: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': 'Internal server error'
        }), 500

@app.route('/api/clear', methods=['POST'])
@limiter.limit("10 per minute")
def clear_conversation():
    """Clear conversation history"""
    user_id = session.get('user_id')
    real_ip = get_real_ip()
    
    if user_id and user_id in conversations:
        del conversations[user_id]
        logger.info(f"🗑️ Conversation cleared for {real_ip}")
    
    return jsonify({'status': 'success', 'message': 'Conversation cleared'})

# Admin endpoint to view blocked IPs (protect this in production!)
@app.route('/api/admin/blocked-ips')
def admin_blocked_ips():
    """View blocked IPs - protect this endpoint with authentication in production!"""
    # TODO: Add authentication here
    return jsonify({
        'blocked_ips': list(blocked_ips),
        'suspicious_ips': dict(suspicious_ips),
        'ip_bot_scores': dict(ip_bot_score),
        'total_blocked': len(blocked_ips)
    })

@app.route('/api/admin/unblock-ip/<ip>')
def admin_unblock_ip(ip):
    """Manually unblock an IP - protect this endpoint with authentication in production!"""
    # TODO: Add authentication here
    if ip in blocked_ips:
        blocked_ips.remove(ip)
        suspicious_ips.pop(ip, None)
        ip_bot_score.pop(ip, None)
        logger.info(f"🔓 IP manually unblocked: {ip}")
        return jsonify({'status': 'success', 'message': f'IP {ip} unblocked'})
    return jsonify({'status': 'error', 'message': 'IP not in blocklist'}), 404

# Error handlers
@app.errorhandler(403)
def forbidden(e):
    """Handle forbidden access"""
    real_ip = get_real_ip()
    logger.warning(f"🚫 403 Forbidden: {real_ip} → {request.path}")
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
    real_ip = get_real_ip()
    logger.warning(f"⚠️ Rate limit exceeded: {real_ip}")
    return jsonify({
        'status': 'error',
        'error': 'Rate limit exceeded. Please try again later.'
    }), 429

@app.errorhandler(500)
def internal_error(e):
    """Handle internal server errors"""
    logger.error(f"💥 Internal server error: {str(e)}")
    return jsonify({
        'status': 'error',
        'error': 'Internal server error'
    }), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"🤖 Secure Multi-User AI Chatbot with IP Tracking")
    print(f"🌐 Server: http://0.0.0.0:{port}")
    print(f"🛡️ Security: IP tracking, bot blocking, rate limiting enabled")
    print(f"📊 Monitoring: Real IP logging active")
    app.run(host='0.0.0.0', port=port, debug=False)

