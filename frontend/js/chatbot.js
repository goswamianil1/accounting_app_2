class Chatbot {
    constructor() {
        this.container = document.createElement('div');
        this.container.className = 'chatbot-container hidden';
        this.container.innerHTML = `
            <div class="chatbot-header">
                <span>AI Accounting Assistant</span>
                <button onclick="chatbot.toggleChat()" style="background: none; border: none; color: white;">×</button>
            </div>
            <div class="chatbot-messages"></div>
            <div class="chatbot-input">
                <input type="text" placeholder="Ask about accounting..." />
                <button>Send</button>
            </div>
        `;

        this.toggleButton = document.createElement('div');
        this.toggleButton.className = 'chatbot-toggle';
        this.toggleButton.innerHTML = '<i class="fas fa-comments"></i>';
        this.toggleButton.onclick = () => this.toggleChat();

        document.body.appendChild(this.container);
        document.body.appendChild(this.toggleButton);

        this.messagesContainer = this.container.querySelector('.chatbot-messages');
        this.input = this.container.querySelector('input');
        this.sendButton = this.container.querySelector('button');

        this.setupEventListeners();
        this.addWelcomeMessage();
    }

    setupEventListeners() {
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
    }

    addWelcomeMessage() {
        this.addMessage("Hello! I'm your AI accounting assistant. How can I help you today?", 'bot');
    }

    toggleChat() {
        this.container.classList.toggle('hidden');
        this.toggleButton.classList.toggle('hidden');
    }

    async sendMessage() {
        const message = this.input.value.trim();
        if (!message) return;

        // Clear input
        this.input.value = '';

        // Add user message to chat
        this.addMessage(message, 'user');

        try {
            // Disable input while waiting for response
            this.input.disabled = true;
            this.sendButton.disabled = true;

            // Send message to backend
            const response = await fetch('http://localhost:8000/api/chatbot/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({ message }),
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            this.addMessage(data.response, 'bot');
        } catch (error) {
            console.error('Error:', error);
            this.addMessage('Sorry, I encountered an error. Please try again.', 'bot');
        } finally {
            // Re-enable input
            this.input.disabled = false;
            this.sendButton.disabled = false;
        }
    }

    addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        messageDiv.textContent = text;
        this.messagesContainer.appendChild(messageDiv);
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }
}

// Initialize chatbot when document is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.chatbot = new Chatbot();
}); 