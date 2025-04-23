class WebClient {
    constructor() {
        this.ws = null;
        this.user = null;
        this.connect();
        
        // Bind event handlers
        document.getElementById('login-form')?.addEventListener('submit', this.handleLogin.bind(this));
        document.getElementById('create-vault')?.addEventListener('click', this.handleCreateVault.bind(this));
        
        // Vault operations
        this.bindVaultHandlers();
    }

    bindVaultHandlers() {
        document.addEventListener('click', event => {
            if (event.target.matches('.vault-item')) {
                this.handleSelectVault(event.target.dataset.vaultId);
            }
            if (event.target.matches('.copy-password')) {
                this.handleCopyPassword(event.target.dataset.password);
            }
        });
    }

    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        this.ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
        
        this.ws.addEventListener('message', event => {
            this.handleMessage(new Uint8Array(event.data));
        });
    }

    handleMessage(data) {
        // Handle binary messages from server
        const decoder = new TextDecoder();
        const message = JSON.parse(decoder.decode(data));
        
        switch(message.type) {
            case 'auth_result':
                this.handleAuthResult(message);
                break;
            case 'vault_list':
                this.updateVaultList(message.data);
                break;
            case 'vault_data':
                this.renderVaultContent(message.data);
                break;
            case 'vault_create_result':
                this.handleVaultCreateResult(message);
                break;
            case 'service_update_result':
                this.handleServiceUpdateResult(message);
                break;
            case 'vault_update_result':
                this.handleVaultUpdateResult(message);
                break;
        }
    }

    handleLogin(event) {
        event.preventDefault();
        const formData = new FormData(event.target);
        
        const authData = {
            email: formData.get('email'),
            mpass: formData.get('mpass')
        };

        const encoder = new TextEncoder();
        this.ws.send(encoder.encode(JSON.stringify({
            type: 'auth_request',
            ...authData
        })));
    }

    handleCreateVault() {
        const vaultName = prompt('Enter vault name:');
        if (vaultName) {
            this.ws.send(JSON.stringify({
                type: 'create_vault',
                name: vaultName
            }));
        }
    }

    // Vault operations
    async fetchVaults() {
        this.ws.send(JSON.stringify({
            type: 'get_vaults',
            uid: this.user?.id
        }));
    }

    async handleSelectVault(vaultId) {
        this.ws.send(JSON.stringify({
            type: 'get_vault',
            uid: this.user?.id,
            vault_id: vaultId
        }));
    }

    renderVaultContent(vaultData) {
        const container = document.querySelector('.vault-content');
        container.innerHTML = `
            <div class="vault-header">
                <h2>${vaultData.name}</h2>
                <button class="btn btn-secondary" 
                        data-vault-id="${vaultData.id}"
                        onclick="client.showAddServiceForm()">
                    Add Service
                </button>
            </div>
            <div class="service-list">
                ${vaultData.services.map(service => `
                    <div class="service-item">
                        <div class="service-info">
                            <h4>${service.service}</h4>
                            <span>${service.user}</span>
                        </div>
                        <button class="btn icon-btn copy-password" 
                                data-password="${service.password}">
                            ⎘
                        </button>
                    </div>
                `).join('')}
            </div>
        `;
    }

    handleVaultCreateResult(message) {
        if (message.success) {
            this.fetchVaults();
            this.showToast('Vault created successfully');
        } else {
            this.showError(message.error);
        }
    }

    handleServiceUpdateResult(message) {
        if (message.success) {
            this.closeForm();
            this.fetchVaults();
            this.showToast(message.message);
        } else {
            this.showError(message.error);
        }
    }

    handleVaultUpdateResult(message) {
        if (message.success) {
            this.showToast('Vault updated successfully');
        } else {
            this.showError(message.error);
        }
    }

    updateVaultList(vaults) {
        const container = document.querySelector('.vault-list');
        container.innerHTML = vaults.map(vault => `
            <div class="vault-item" data-vault-id="${vault.id}">
                <h3>${vault.name}</h3>
                <div class="vault-meta">
                    <span>${vault.items_count} items</span>
                    <button class="btn icon-btn" 
                            onclick="client.showRenameVaultPrompt('${vault.id}')">
                        ✎
                    </button>
                </div>
            </div>
        `).join('');
    }

    // Form handling
    showServiceForm(vaultId, existingService=null) {
        const formContainer = document.createElement('div');
        formContainer.innerHTML = `
            {% include "service_form.html" %}
        `;
        
        const form = formContainer.querySelector('#service-form');
        if (existingService) {
            form.querySelector('#service-name').value = existingService.service;
            form.querySelector('#username').value = existingService.user;
            form.querySelector('#password').value = existingService.password;
            form.querySelector('#notes').value = existingService.notes;
        }

        form.onsubmit = (e) => {
            e.preventDefault();
            const formData = new FormData(form);
            this.handleServiceSubmit(vaultId, existingService?.id, formData);
        };

        document.body.appendChild(formContainer);
    }

    handleServiceSubmit(vaultId, serviceId, formData) {
        const serviceData = {
            vault_id: vaultId,
            service: formData.get('service'),
            user: formData.get('user'),
            password: formData.get('password'),
            notes: formData.get('notes')
        };

        if (serviceId) serviceData.id = serviceId;

        this.ws.send(JSON.stringify({
            type: serviceId ? 'update_service' : 'create_service',
            ...serviceData
        }));
    }

    generatePassword() {
        const password = client.generateStrongPassword(16);
        const passwordField = document.querySelector('#password');
        if (passwordField) {
            passwordField.value = password;
            passwordField.type = 'text';
            setTimeout(() => passwordField.type = 'password', 2000);
        }
    }

    generateStrongPassword(length=16) {
        const charset = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()";
        return Array.from(crypto.getRandomValues(new Uint8Array(length)))
            .map(byte => charset[byte % charset.length])
            .join('');
    }

    closeForm() {
        const form = document.querySelector('.form-modal');
        if (form) form.remove();
    }

    // Helper functions
    showToast(message, type='success') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);
        
        setTimeout(() => toast.remove(), 3000);
    }

    showError(message) {
        this.showToast(message, 'error');
    }

    handleAuthResult(result) {
        if (result.success) {
            this.user = result.user;
            this.fetchVaults();
            window.location.href = '/vaults';
        } else {
            this.showError('Authentication failed: ' + result.error);
        }
    }

    handleCopyPassword(password) {
        navigator.clipboard.writeText(password)
            .then(() => this.showToast('Password copied to clipboard'))
            .catch(() => this.showError('Failed to copy password'));
    }
}

// Initialize when DOM loaded
document.addEventListener('DOMContentLoaded', () => {
    window.client = new WebClient();
});