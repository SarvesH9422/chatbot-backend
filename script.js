const chatContainer = document.getElementById('chatContainer');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const clearBtn = document.getElementById('clearBtn');
const API_URL = window.location.origin + '/api';



// ========== PREVENT BODY SCROLL ON MOBILE ==========

// Lock body scroll
document.body.style.overflow = 'hidden';
document.documentElement.style.overflow = 'hidden';

// Fix iOS viewport height
function updateViewportHeight() {
    const vh = window.innerHeight * 0.01;
    document.documentElement.style.setProperty('--vh', `${vh}px`);
}

// Set on load
updateViewportHeight();

// Update on resize/orientation change
window.addEventListener('resize', updateViewportHeight);
window.addEventListener('orientationchange', updateViewportHeight);

// Prevent pull-to-refresh on mobile
document.body.addEventListener('touchmove', function(e) {
    if (e.target.closest('.chat-container')) {
        // Allow scroll inside chat container
        return;
    }
    // Prevent scroll everywhere else
    e.preventDefault();
}, { passive: false });

// ========== REST OF YOUR CODE BELOW ==========







// ========== DARK MODE FUNCTIONALITY ==========

const themeToggle = document.getElementById('themeToggle');
const themeIcon = document.querySelector('.theme-icon');
const html = document.documentElement;

// Check for saved theme preference or default to light mode
const currentTheme = localStorage.getItem('theme') || 'light';

// Apply saved theme on load
if (currentTheme === 'dark') {
    html.setAttribute('data-theme', 'dark');
    themeIcon.textContent = '☀️';
}

// Toggle theme
themeToggle.addEventListener('click', () => {
    const theme = html.getAttribute('data-theme');
    
    if (theme === 'dark') {
        // Switch to light mode
        html.setAttribute('data-theme', 'light');
        localStorage.setItem('theme', 'light');
        themeIcon.textContent = '🌙';
        
        // Optional: Animate transition
        themeToggle.style.transform = 'rotate(360deg)';
        setTimeout(() => {
            themeToggle.style.transform = 'rotate(0deg)';
        }, 300);
    } else {
        // Switch to dark mode
        html.setAttribute('data-theme', 'dark');
        localStorage.setItem('theme', 'dark');
        themeIcon.textContent = '☀️';
        
        // Optional: Animate transition
        themeToggle.style.transform = 'rotate(-360deg)';
        setTimeout(() => {
            themeToggle.style.transform = 'rotate(0deg)';
        }, 300);
    }
});

// ========== REST OF YOUR CODE BELOW ==========


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
        sendBtn.classList.remove('loading');
    }
}

function addMessage(text, sender) {
    console.log('Adding message:', sender, text);
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = sender === 'user' ? 'U' : '🤖';
    
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

// Enhanced typewriter with rich formatting
async function addMessageWithTypewriter(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = sender === 'user' ? 'U' : '🤖';

    const content = document.createElement('div');
    content.className = 'message-content';
    content.innerHTML = ''; // Use innerHTML for rich formatting

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    chatContainer.appendChild(messageDiv);

    // Parse and format the response
    const formattedHTML = parseMarkdown(text);
    
    // Typewriter effect with HTML rendering
    await typewriterHTML(content, formattedHTML);
    
    chatContainer.scrollTo({
        top: chatContainer.scrollHeight,
        behavior: 'smooth'
    });
}

// Enhanced markdown parser - handles * and - bullets
function parseMarkdown(text) {
    let html = text;
    
    // **Bold text** → <strong>Bold text</strong>
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // *Italic text* (but NOT bullets) → <em>Italic text</em>
    // Only match * that are NOT at start of line and NOT followed by space
    html = html.replace(/(?<!^|\n)\*(?!\s)(.*?)\*(?!\s)/gm, '<em>$1</em>');
    
    // `code` → <code>code</code>
    html = html.replace(/`(.*?)`/g, '<code>$1</code>');
    
    // Parse lines for lists and paragraphs
    const lines = html.split('\n');
    let inList = false;
    let listType = null; // 'ul' or 'ol'
    let formatted = [];
    
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const trimmed = line.trim();
        
        // Check if line is a bullet point (- or * or •)
        if (trimmed.startsWith('- ') || trimmed.startsWith('* ') || trimmed.startsWith('• ')) {
            if (!inList || listType !== 'ul') {
                if (inList) {
                    formatted.push(listType === 'ul' ? '</ul>' : '</ol>');
                }
                formatted.push('<ul>');
                inList = true;
                listType = 'ul';
            }
            
            // Extract content after bullet marker
            let content = trimmed.substring(2).trim();
            formatted.push(`<li>${content}</li>`);
        }
        // Check if line is numbered list (1. 2. 3.)
        else if (/^\d+\.\s/.test(trimmed)) {
            if (!inList || listType !== 'ol') {
                if (inList) {
                    formatted.push(listType === 'ul' ? '</ul>' : '</ol>');
                }
                formatted.push('<ol>');
                inList = true;
                listType = 'ol';
            }
            
            const content = trimmed.replace(/^\d+\.\s/, '');
            formatted.push(`<li>${content}</li>`);
        }
        // Regular paragraph or empty line
        else {
            // Close list if open
            if (inList) {
                formatted.push(listType === 'ul' ? '</ul>' : '</ol>');
                inList = false;
                listType = null;
            }
            
            if (trimmed.length > 0) {
                formatted.push(`<p>${trimmed}</p>`);
            } else {
                formatted.push('<br>');
            }
        }
    }
    
    // Close list if still open at end
    if (inList) {
        formatted.push(listType === 'ul' ? '</ul>' : '</ol>');
    }
    
    return formatted.join('');
}

// Typewriter effect for HTML content
async function typewriterHTML(element, html) {
    // Create temporary div to parse HTML
    const temp = document.createElement('div');
    temp.innerHTML = html;
    
    // Get all nodes (text and elements)
    const nodes = Array.from(temp.childNodes);
    
    for (let node of nodes) {
        if (node.nodeType === Node.TEXT_NODE) {
            // Text node - type character by character
            const text = node.textContent;
            for (let char of text) {
                element.innerHTML += char;
                await sleep(10); // Fast typing for smooth effect
                chatContainer.scrollTo({
                    top: chatContainer.scrollHeight,
                    behavior: 'smooth'
                });
            }
        } else if (node.nodeType === Node.ELEMENT_NODE) {
            // Element node - add instantly or type content
            if (node.tagName === 'UL' || node.tagName === 'OL') {
                // Add list structure instantly
                const listClone = node.cloneNode(true);
                element.appendChild(listClone);
                await sleep(100);
            } else if (node.tagName === 'P') {
                // Type paragraph content
                const p = document.createElement('p');
                element.appendChild(p);
                
                for (let child of node.childNodes) {
                    if (child.nodeType === Node.TEXT_NODE) {
                        for (let char of child.textContent) {
                            p.innerHTML += char;
                            await sleep(10);
                        }
                    } else {
                        // Bold, italic, code tags
                        p.appendChild(child.cloneNode(true));
                        await sleep(20);
                    }
                }
            } else {
                // Other elements (br, strong, em, code)
                element.appendChild(node.cloneNode(true));
                await sleep(20);
            }
            
            chatContainer.scrollTo({
                top: chatContainer.scrollHeight,
                behavior: 'smooth'
            });
        }
    }
}

// Helper function for delay
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function showTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'typing-message';
    typingDiv.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content">
            <span class="typing-text">Typing</span>
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
