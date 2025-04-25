document.addEventListener('DOMContentLoaded', () => {
    // Check if user is logged in
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = 'index.html';
        return;
    }

    loadDashboardData();
});

async function loadDashboardData() {
    try {
        const response = await fetch('http://localhost:8000/api/transactions/', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`,
                'Content-Type': 'application/json'
            },
            credentials: 'include'
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const transactions = await response.json();
        updateDashboardUI(transactions);
    } catch (error) {
        console.error('Failed to load dashboard data:', error);
        alert('Failed to load dashboard data. Please try again.');
    }
}

function updateDashboardUI(transactions) {
    // Calculate totals
    let totalBalance = 0;
    let totalIncome = 0;
    let totalExpenses = 0;

    transactions.forEach(transaction => {
        const amount = parseFloat(transaction.amount);
        if (transaction.type === 'income') {
            totalIncome += amount;
            totalBalance += amount;
        } else {
            totalExpenses += amount;
            totalBalance -= amount;
        }
    });

    // Update UI
    document.getElementById('totalBalance').textContent = formatCurrency(totalBalance);
    document.getElementById('totalIncome').textContent = formatCurrency(totalIncome);
    document.getElementById('totalExpenses').textContent = formatCurrency(totalExpenses);

    // Update transactions table
    const transactionsTable = document.getElementById('transactionsTable');
    transactionsTable.innerHTML = transactions
        .slice(0, 5) // Show only last 5 transactions
        .map(transaction => `
            <tr>
                <td>${formatDate(transaction.date)}</td>
                <td>${transaction.description}</td>
                <td class="${transaction.type === 'income' ? 'text-success' : 'text-danger'}">
                    ${formatCurrency(transaction.amount)}
                </td>
                <td>${transaction.type}</td>
            </tr>
        `)
        .join('');
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString();
}

// Handle new transaction button
document.getElementById('newTransactionBtn')?.addEventListener('click', () => {
    window.location.href = 'transactions.html';
});

// Handle logout
function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('refreshToken');
    window.location.href = 'index.html';
} 