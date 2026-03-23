function toggleFloatingChatbot() {
    const chatWindow = document.getElementById('chatWindow');
    const chatBadge = document.querySelector('.chat-badge');
    
    chatWindow.classList.toggle('hidden');
    
    if (!chatWindow.classList.contains('hidden')) {
        if (chatBadge) chatBadge.style.display = 'none';
        document.getElementById('floatingChatInput').focus();
        
        // Auto-scroll to bottom
        const chatBody = document.getElementById('floatingChatMessages');
        chatBody.scrollTop = chatBody.scrollHeight;
    }
}

function sendFloatingChat() {
    const input = document.getElementById('floatingChatInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    appendChatMessage('user', message);
    input.value = '';
    
    // Simulate AI response
    setTimeout(() => {
        fetch('/api/ai/chatbot', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: message })
        })
        .then(response => response.json())
        .then(data => {
            appendChatMessage('bot', data.response);
        })
        .catch(error => {
            console.error('Error:', error);
            appendChatMessage('bot', 'Sorry, I am having trouble connecting right now. Please try again later.');
        });
    }, 500);
}

function sendQuickChat(suggestion) {
    // Hide suggestions
    const suggestions = document.querySelector('.chat-suggestions');
    if (suggestions) suggestions.style.display = 'none';
    
    appendChatMessage('user', suggestion);
    
    // Simulate AI response
    setTimeout(() => {
        fetch('/api/ai/chatbot', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: suggestion })
        })
        .then(response => response.json())
        .then(data => {
            appendChatMessage('bot', data.response);
        })
        .catch(error => {
            console.error('Error:', error);
            appendChatMessage('bot', 'I encountered an error. How else can I help?');
        });
    }, 500);
}

function appendChatMessage(sender, text) {
    const chatBody = document.getElementById('floatingChatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${sender}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'chat-avatar';
    avatar.innerHTML = sender === 'bot' ? '<i class="fas fa-robot"></i>' : '<i class="fas fa-user"></i>';
    
    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble';
    bubble.innerHTML = `<p>${text}</p>`;
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(bubble);
    chatBody.appendChild(messageDiv);
    
    // Scroll to bottom
    chatBody.scrollTop = chatBody.scrollHeight;
}
