const chatContainer = document.getElementById('chatContainer');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const clearBtn = document.getElementById('clearBtn');

const API_URL = window.location.origin + '/api';

userInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
});

sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

async function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;

    const welcomeMsg = document.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.style.display = 'none';
    }

    addMessage(message, 'user');
    userInput.value = '';
    userInput.style.height = 'auto';

    const typingIndicator = showTypingIndicator();

    try {
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message })
        });

        const data = await response.json();
        typingIndicator.remove();
        
        if (data.status === 'success') {
            addMessage(data.response, 'assistant');
        } else {
            addMessage('Error: ' + (data.error || 'Unknown error'), 'assistant');
        }
    } catch (error) {
        typingIndicator.remove();
        addMessage('Error: Cannot connect to server. Make sure Ollama is running!', 'assistant');
    }
}

function addMessage(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = sender === 'user' ? 'U' : '🦙';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    content.textContent = text;
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    chatContainer.appendChild(messageDiv);
    
    messageDiv.style.opacity = '0';
    setTimeout(() => {
        messageDiv.style.transition = 'opacity 0.5s';
        messageDiv.style.opacity = '1';
    }, 10);
    
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function showTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message assistant';
    typingDiv.innerHTML = `
        <div class="message-avatar">🦙</div>
        <div class="message-content typing-indicator">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;
    chatContainer.appendChild(typingDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    return typingDiv;
}

clearBtn.addEventListener('click', async () => {
    if (confirm('Clear conversation history?')) {
        await fetch(`${API_URL}/clear`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const messages = document.querySelectorAll('.message');
        messages.forEach(msg => msg.remove());
        
        chatContainer.innerHTML = `
            <div class="welcome-message">
                <h2>Conversation cleared!</h2>
                <p>Start a new conversation</p>
            </div>
        `;
    }
});
