const API_URL = '/api';

export interface User {
    id: number;
    username: string;
    email: string;
}

export const authService = {
    async register(username: string, email: string, password: string, adminSecret?: string) {
        const response = await fetch(`${API_URL}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password, admin_secret: adminSecret }),
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Registration failed');
        }
        const data = await response.json();
        if (data.is_admin) {
            localStorage.setItem('isAdmin', 'true');
        }
        return data;
    },

    async login(username: string, password: string) {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        const response = await fetch(`${API_URL}/token`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Login failed');
        }

        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('username', username);
        if (data.is_admin) {
            localStorage.setItem('isAdmin', 'true');
        }
        return data;
    },

    logout() {
        localStorage.removeItem('token');
        localStorage.removeItem('username');
        localStorage.removeItem('isAdmin');
    },

    isAdmin(): boolean {
        return localStorage.getItem('isAdmin') === 'true';
    },

    async mockSocialLogin(provider: string) {
        // Simulate network delay
        await new Promise(resolve => setTimeout(resolve, 1000));

        const mockUsername = `${provider.toLowerCase()}_user_${Math.floor(Math.random() * 1000)}`;
        const mockToken = `mock_token_${provider}_${Date.now()}`;

        localStorage.setItem('token', mockToken);
        localStorage.setItem('username', mockUsername);

        return { username: mockUsername, token: mockToken };
    },

    getCurrentUser(): string | null {
        return localStorage.getItem('username');
    },

    getToken(): string | null {
        return localStorage.getItem('token');
    },

    isAuthenticated(): boolean {
        return !!localStorage.getItem('token');
    }
};
