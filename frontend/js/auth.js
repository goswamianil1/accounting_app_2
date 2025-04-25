document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;

            try {
                const response = await fetch('http://localhost:8000/api/token/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ username, password }),
                    credentials: 'include'
                });

                if (!response.ok) {
                    throw new Error('Login failed');
                }

                const data = await response.json();
                localStorage.setItem('token', data.access);
                localStorage.setItem('refreshToken', data.refresh);
                window.location.href = 'dashboard.html';
            } catch (error) {
                alert('Login failed. Please check your credentials.');
                console.error('Login error:', error);
            }
        });
    }

    // Check if user is logged in
    const token = localStorage.getItem('token');
    if (token && window.location.pathname === '/index.html') {
        window.location.href = 'dashboard.html';
    }
}); 