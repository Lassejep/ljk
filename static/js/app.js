class WebClient {
    constructor() {
        this.socket = io();
        this.errorElement = document.getElementById('error-message');
    }

    async register(credentials) {
        return new Promise((resolve, reject) => {
            this.socket.emit('register', credentials, (response) => {
                if (response.status === 'success') {
                    resolve();
                } else {
                    reject(new Error(response.message));
                }
            });
        });
    }

    showError(message) {
        this.errorElement.textContent = message;
        this.errorElement.classList.remove('hidden');
        setTimeout(() => {
            this.errorElement.classList.add('hidden');
        }, 5000);
    }
}

// Initialize when DOM loaded
document.addEventListener('DOMContentLoaded', () => {
    window.client = new WebClient();
});

// Registration form handling
document.getElementById('register-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('email').value;
    const password = document.getElementById('mpass').value;
    const confirmPassword = document.getElementById('mpass-confirm').value;

    if (password !== confirmPassword) {
        client.showError('Passwords do not match');
        return;
    }

    try {
        await client.register({
            email: email,
            mkey: password
        });
        window.location.href = '/vaults';
    } catch (error) {
        client.showError(error.message);
    }
});
