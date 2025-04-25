const API_URL = 'http://localhost:8000/api';

const api = {
    async request(endpoint, options = {}) {
        const token = localStorage.getItem('token');
        const headers = {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` }),
            ...options.headers
        };

        try {
            const response = await fetch(`${API_URL}${endpoint}`, {
                ...options,
                headers,
                credentials: 'include'
            });

            if (!response.ok) {
                if (response.status === 401) {
                    // Try to refresh token
                    const refreshToken = localStorage.getItem('refreshToken');
                    if (refreshToken) {
                        try {
                            const refreshResponse = await fetch(`${API_URL}/token/refresh/`, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ refresh: refreshToken }),
                                credentials: 'include'
                            });

                            if (refreshResponse.ok) {
                                const data = await refreshResponse.json();
                                localStorage.setItem('token', data.access);
                                // Retry the original request
                                return this.request(endpoint, options);
                            }
                        } catch (error) {
                            console.error('Token refresh failed:', error);
                        }
                    }
                    // If refresh fails or no refresh token, redirect to login
                    localStorage.removeItem('token');
                    localStorage.removeItem('refreshToken');
                    window.location.href = 'index.html';
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    },

    // Auth endpoints
    async login(username, password) {
        return this.request('/token/', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });
    },

    async logout() {
        localStorage.removeItem('token');
        localStorage.removeItem('refreshToken');
        window.location.href = 'index.html';
    },

    // Account endpoints
    async getAccounts() {
        return this.request('/accounts/');
    },

    async createAccount(accountData) {
        return this.request('/accounts/', {
            method: 'POST',
            body: JSON.stringify(accountData)
        });
    },

    // Transaction endpoints
    async getTransactions() {
        return this.request('/transactions/');
    },

    async createTransaction(transactionData) {
        return this.request('/transactions/', {
            method: 'POST',
            body: JSON.stringify(transactionData)
        });
    }
}; 