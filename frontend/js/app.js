// API Configuration
const API_BASE_URL = 'http://localhost:8000/api';

// DOM Elements
const elements = {
    pages: document.querySelectorAll('.page'),
    navLinks: document.querySelectorAll('.nav-link'),
    transactionForm: document.getElementById('transactionForm'),
    transactionsTable: document.getElementById('transactionsTable').getElementsByTagName('tbody')[0],
    toast: new bootstrap.Toast(document.getElementById('toast')),
    totalBalance: document.getElementById('totalBalance'),
    monthlyIncome: document.getElementById('monthlyIncome'),
    monthlyExpenses: document.getElementById('monthlyExpenses')
};

// Charts
const charts = {
    monthly: null,
    category: null
};

// Page Handlers
const pageHandlers = {
    dashboard: loadDashboardData,
    transactions: loadTransactions,
    reports: updateCharts
};

// Form Validation
const formValidators = {
    transactionDate: (value) => {
        const date = new Date(value);
        const today = new Date();
        return date <= today ? null : 'Date cannot be in the future';
    },
    transactionAmount: (value) => {
        const amount = parseFloat(value);
        return amount > 0 ? null : 'Amount must be greater than 0';
    },
    transactionCategory: (value) => {
        return value.trim().length >= 2 ? null : 'Category must be at least 2 characters';
    }
};

// Chatbot Configuration
const CHATBOT_CONFIG = {
    maxContextLength: 10, // Maximum number of messages to keep in context
    sensitiveKeywords: ['password', 'credit card', 'ssn', 'social security', 'bank account'],
    systemPrompt: `You are a helpful financial assistant for a personal finance application. 
    Your role is to help users understand their finances, provide insights about their spending patterns,
    and offer general financial advice. Never ask for or store sensitive personal information.
    If a user asks about sensitive topics, politely redirect them to appropriate resources.`
};

// Chatbot State Management
let chatContext = {
    messages: [],
    userPreferences: {},
    lastTransactionType: null,
    lastCategory: null
};

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    setupNavigation();
    setupTransactionForm();
    setupCharts();
    loadInitialData();
    handleInitialRoute();
    setupChatbot();
});

// Routing Setup
function handleInitialRoute() {
    const path = window.location.hash.slice(1) || 'dashboard';
    showPage(path);
}

function setupNavigation() {
    elements.navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const pageId = e.target.dataset.page;
            window.location.hash = pageId;
            showPage(pageId);
        });
    });

    // Handle browser back/forward
    window.addEventListener('hashchange', () => {
        const pageId = window.location.hash.slice(1) || 'dashboard';
        showPage(pageId);
    });
}

function showPage(pageId) {
    // Hide all pages and deactivate nav links
    elements.pages.forEach(page => page.classList.remove('active'));
    elements.navLinks.forEach(link => link.classList.remove('active'));

    // Show selected page and activate nav link
    document.getElementById(pageId).classList.add('active');
    document.querySelector(`[data-page="${pageId}"]`).classList.add('active');

    // Load page-specific data
    const pageHandler = pageHandlers[pageId];
    
    if (pageHandler) {
        pageHandler();
    }
}

// Transaction Form Setup
function setupTransactionForm() {
    const form = elements.transactionForm;
    const inputs = form.querySelectorAll('input, select, textarea');

    // Add validation on input
    inputs.forEach(input => {
        input.addEventListener('input', () => validateInput(input));
        input.addEventListener('blur', () => validateInput(input));
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Validate all inputs
        const isValid = Array.from(inputs).every(input => validateInput(input));
        if (!isValid) {
            showToast('Please correct the errors in the form', 'error');
            return;
        }

        const formData = {
            date: document.getElementById('transactionDate').value,
            type: document.getElementById('transactionType').value,
            amount: parseFloat(document.getElementById('transactionAmount').value),
            category: document.getElementById('transactionCategory').value.trim(),
            description: document.getElementById('transactionDescription').value.trim()
        };

        try {
            showLoading(true);
            const response = await fetch(`${API_BASE_URL}/transactions/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                showToast('Transaction added successfully!', 'success');
                form.reset();
                refreshData();
            } else {
                const error = await response.json();
                throw new Error(error.message || 'Failed to add transaction');
            }
        } catch (error) {
            showToast('Error: ' + error.message, 'error');
        } finally {
            showLoading(false);
        }
    });
}

function validateInput(input) {
    const validator = formValidators[input.id];
    if (!validator) return true;

    const error = validator(input.value);
    const errorElement = input.nextElementSibling;

    if (error) {
        if (!errorElement || !errorElement.classList.contains('error-message')) {
            const newErrorElement = document.createElement('div');
            newErrorElement.className = 'error-message';
            newErrorElement.textContent = error;
            input.parentNode.insertBefore(newErrorElement, input.nextSibling);
        } else {
            errorElement.textContent = error;
        }
        input.classList.add('is-invalid');
        return false;
    } else {
        if (errorElement && errorElement.classList.contains('error-message')) {
            errorElement.remove();
        }
        input.classList.remove('is-invalid');
        return true;
    }
}

// Loading State
function showLoading(isLoading) {
    const submitButton = elements.transactionForm.querySelector('button[type="submit"]');
    if (isLoading) {
        submitButton.disabled = true;
        submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
    } else {
        submitButton.disabled = false;
        submitButton.textContent = 'Add Transaction';
    }
}

// Data Loading Functions
async function loadInitialData() {
    await Promise.all([
        loadDashboardData(),
        loadTransactions()
    ]);
}

async function refreshData() {
    await Promise.all([
        loadDashboardData(),
        loadTransactions(),
        updateCharts()
    ]);
}

async function loadDashboardData() {
    try {
        const response = await fetch(`${API_BASE_URL}/dashboard/`);
        const data = await response.json();

        elements.totalBalance.textContent = formatCurrency(data.total_balance);
        elements.monthlyIncome.textContent = formatCurrency(data.monthly_income);
        elements.monthlyExpenses.textContent = formatCurrency(data.monthly_expenses);
    } catch (error) {
        showToast('Error loading dashboard data', 'error');
    }
}

async function loadTransactions() {
    try {
        const response = await fetch(`${API_BASE_URL}/transactions/`);
        const transactions = await response.json();

        elements.transactionsTable.innerHTML = transactions.map(transaction => `
            <tr>
                <td>${formatDate(transaction.date)}</td>
                <td>${transaction.type}</td>
                <td class="${transaction.type === 'income' ? 'text-success' : 'text-danger'}">
                    ${formatCurrency(transaction.amount)}
                </td>
                <td>${transaction.category}</td>
                <td>${transaction.description || '-'}</td>
                <td>
                    <button class="btn btn-sm btn-danger" onclick="deleteTransaction(${transaction.id})">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        showToast('Error loading transactions', 'error');
    }
}

// Chart Functions
function setupCharts() {
    setupMonthlyChart();
    setupCategoryChart();
}

function setupMonthlyChart() {
    const ctx = document.getElementById('monthlyChart').getContext('2d');
    charts.monthly = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Income',
                    data: [],
                    borderColor: '#198754',
                    tension: 0.1
                },
                {
                    label: 'Expenses',
                    data: [],
                    borderColor: '#dc3545',
                    tension: 0.1
                }
            ]
        },
        options: {
            responsive: true,
            plugins: { legend: { position: 'top' } }
        }
    });
}

function setupCategoryChart() {
    const ctx = document.getElementById('categoryChart').getContext('2d');
    charts.category = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: ['#0d6efd', '#198754', '#dc3545', '#ffc107', '#0dcaf0']
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { position: 'right' } }
        }
    });
}

async function updateCharts() {
    try {
        const response = await fetch(`${API_BASE_URL}/reports/`);
        const data = await response.json();

        // Update Monthly Chart
        charts.monthly.data.labels = data.monthly.labels;
        charts.monthly.data.datasets[0].data = data.monthly.income;
        charts.monthly.data.datasets[1].data = data.monthly.expenses;
        charts.monthly.update();

        // Update Category Chart
        charts.category.data.labels = data.categories.labels;
        charts.category.data.datasets[0].data = data.categories.values;
        charts.category.update();
    } catch (error) {
        showToast('Error updating charts', 'error');
    }
}

// Delete Transaction
async function deleteTransaction(id) {
    if (confirm('Are you sure you want to delete this transaction?')) {
        try {
            const response = await fetch(`${API_BASE_URL}/transactions/${id}/`, {
                method: 'DELETE'
            });

            if (response.ok) {
                showToast('Transaction deleted successfully!', 'success');
                refreshData();
            } else {
                throw new Error('Failed to delete transaction');
            }
        } catch (error) {
            showToast('Error deleting transaction: ' + error.message, 'error');
        }
    }
}

// Utility Functions
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR'
    }).format(amount);
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function showToast(message, type = 'info') {
    const toastElement = document.getElementById('toast');
    const toastBody = toastElement.querySelector('.toast-body');
    
    toastBody.textContent = message;
    toastElement.classList.remove('bg-success', 'bg-danger', 'bg-info');
    toastElement.classList.add(`bg-${type}`);
    
    elements.toast.show();
}

// Enhanced Chatbot Logic
function setupChatbot() {
    const chatForm = document.getElementById('chatForm');
    const chatInput = document.getElementById('chatInput');
    const chatMessages = document.getElementById('chatMessages');

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const userMessage = chatInput.value.trim();
        
        if (!userMessage) return;

        // Check for sensitive information
        if (containsSensitiveInfo(userMessage)) {
            appendMessage('system', 'I apologize, but I cannot process sensitive personal information. Please contact our support team for assistance with sensitive matters.');
            chatInput.value = '';
            return;
        }

        // Add user message to chat
        appendMessage('user', userMessage);
        chatInput.value = '';

        // Show loading state
        const loadingMessage = appendMessage('system', 'Thinking...');
        
        try {
            // Prepare context for the API
            const context = prepareChatContext(userMessage);
            
            // Get chatbot response
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: userMessage,
                    context: context,
                    systemPrompt: CHATBOT_CONFIG.systemPrompt
                })
            });

            if (!response.ok) {
                throw new Error('Failed to get chatbot response');
            }

            const data = await response.json();
            
            // Remove loading message
            loadingMessage.remove();
            
            // Add chatbot response
            appendMessage('assistant', data.response);
            
            // Update context
            updateChatContext(userMessage, data.response);
            
        } catch (error) {
            loadingMessage.remove();
            appendMessage('system', 'Sorry, I encountered an error. Please try again later.');
            console.error('Chatbot error:', error);
        }
    });
}

// Helper Functions
function containsSensitiveInfo(message) {
    const lowerMessage = message.toLowerCase();
    return CHATBOT_CONFIG.sensitiveKeywords.some(keyword => 
        lowerMessage.includes(keyword.toLowerCase())
    );
}

function prepareChatContext(userMessage) {
    // Get recent messages
    const recentMessages = chatContext.messages
        .slice(-CHATBOT_CONFIG.maxContextLength)
        .map(msg => ({
            role: msg.role,
            content: msg.content
        }));

    // Add relevant context based on user preferences and recent activity
    const context = {
        messages: recentMessages,
        preferences: chatContext.userPreferences,
        lastTransaction: chatContext.lastTransactionType,
        lastCategory: chatContext.lastCategory
    };

    return context;
}

function updateChatContext(userMessage, assistantResponse) {
    // Add new messages to context
    chatContext.messages.push(
        { role: 'user', content: userMessage },
        { role: 'assistant', content: assistantResponse }
    );

    // Keep context within limits
    if (chatContext.messages.length > CHATBOT_CONFIG.maxContextLength * 2) {
        chatContext.messages = chatContext.messages.slice(-CHATBOT_CONFIG.maxContextLength * 2);
    }

    // Extract and update relevant context
    updateContextFromMessages(userMessage, assistantResponse);
}

function updateContextFromMessages(userMessage, assistantResponse) {
    // Extract transaction type if mentioned
    const transactionTypes = ['income', 'expense', 'transfer'];
    transactionTypes.forEach(type => {
        if (userMessage.toLowerCase().includes(type)) {
            chatContext.lastTransactionType = type;
        }
    });

    // Extract category if mentioned
    const categoryMatch = userMessage.match(/category\s+(\w+)/i);
    if (categoryMatch) {
        chatContext.lastCategory = categoryMatch[1];
    }
}

function appendMessage(role, content) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${role}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = content;
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageDiv;
} 