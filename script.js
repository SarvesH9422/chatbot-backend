const chatContainer = document.getElementById('chatContainer');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const clearBtn = document.getElementById('clearBtn');
const API_URL = window.location.origin + '/api';





console.log('API URL:', API_URL);

// Change placeholder based on screen size
function updatePlaceholder() {
    if (window.innerWidth <= 768) {
        userInput.placeholder = 'Text here';
    } else {
        userInput.placeholder = 'Type your message here...';
    }
}

// Run on load
updatePlaceholder();

// Run on window resize
window.addEventListener('resize', updatePlaceholder);

// Auto-resize textarea
userInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 120) + 'px';
});

// Send message on button click
sendBtn.addEventListener('click', sendMessage);

// Send message on Enter key (Shift+Enter for new line)
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

async function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;

    // Disable send button while processing
    sendBtn.disabled = true;
    // sendBtn.textContent = 'Send ⏳';

    console.log('Sending message:', message);

    // Hide welcome message
   // Hide welcome message but keep the space
const welcomeMsg = document.querySelector('.welcome-message');
if (welcomeMsg) {
    welcomeMsg.style.transition = 'opacity 0.3s ease, visibility 0.3s ease';
    welcomeMsg.style.opacity = '0';
    welcomeMsg.style.visibility = 'hidden';
    welcomeMsg.style.position = 'absolute'; // Remove from flow after fade
}



    // Add user message
    addMessage(message, 'user');
    userInput.value = '';
    userInput.style.height = 'auto';

    // Show typing indicator
    const typingIndicator = showTypingIndicator();

    try {
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        });

        console.log('Response status:', response.status);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('Response data:', data);
        
        // Remove typing indicator
        typingIndicator.remove();
        
        if (data.status === 'success') {
            // Add message with typewriter effect
            await addMessageWithTypewriter(data.response, 'assistant');
        } else {
            addMessage('Error: ' + (data.error || 'Unknown error'), 'assistant');
        }
    } catch (error) {
        console.error('Fetch error:', error);
        typingIndicator.remove();
        addMessage('❌ Cannot connect to server. Please try again.', 'assistant');
    } finally {
        // Re-enable send button
        sendBtn.disabled = false;
        sendBtn.textContent = 'Send';
    }
}

function addMessage(text, sender) {
    console.log('Adding message:', sender, text);
    
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
    
    // Scroll to bottom smoothly
    chatContainer.scrollTo({
        top: chatContainer.scrollHeight,
        behavior: 'smooth'
    });
    
    console.log('Message added to DOM');
}

// New function: Add message with typewriter effect
async function addMessageWithTypewriter(text, sender) {
    console.log('Adding message with typewriter:', sender);
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = sender === 'user' ? 'U' : '🦙';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    content.textContent = ''; // Start empty
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    chatContainer.appendChild(messageDiv);
    
    // Typewriter effect
    const words = text.split(' ');
    let currentText = '';
    
    for (let i = 0; i < words.length; i++) {
        currentText += (i > 0 ? ' ' : '') + words[i];
        content.textContent = currentText;
        
        // Scroll to bottom during typing
        chatContainer.scrollTo({
            top: chatContainer.scrollHeight,
            behavior: 'smooth'
        });
        
        // Delay between words (adjust speed here)
        await sleep(50); // 50ms = fast, 100ms = medium, 150ms = slow
    }
    
    console.log('Typewriter complete');
}

// Helper function for delay
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function showTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'typing-message';
    typingDiv.innerHTML = `
        <div class="message-avatar">🦙</div>
        <div class="message-content">
            <span class="typing-text">Llama is typing</span>
            <div class="typing-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;
    chatContainer.appendChild(typingDiv);
    
    // Scroll to show typing indicator
    chatContainer.scrollTo({
        top: chatContainer.scrollHeight,
        behavior: 'smooth'
    });
    
    return typingDiv;
}

// Clear conversation
clearBtn.addEventListener('click', async () => {
    if (confirm('Clear conversation history?')) {
        try {
            await fetch(`${API_URL}/clear`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            // Clear all messages from UI
            const messages = document.querySelectorAll('.message, .typing-message');
            messages.forEach(msg => {
                msg.style.opacity = '0';
                msg.style.transform = 'translateY(-10px)';
            });
            
            setTimeout(() => {
                messages.forEach(msg => msg.remove());
                
                // Show welcome message
                chatContainer.innerHTML = `
                    <div class="welcome-message">
                        <h2>Welcome to Llama AI!</h2>
                        
                        <p class="info">Powered by Llama 3.3 • Free • Fast</p>
                    </div>
                `;
            }, 300);
        } catch (error) {
            console.error('Clear error:', error);
            alert('Failed to clear conversation');
        }
    }
});

// Focus input on load
window.addEventListener('load', () => {
    userInput.focus();
});
