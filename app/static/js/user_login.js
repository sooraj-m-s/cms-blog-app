const BASE_URL = window.BASE_URL || '';

const welcomeMessages = {
    login: {
        title: "Welcome Back!",
        message: "Sign in to continue to your blog dashboard and manage your content."
    },
    register: {
        title: "Join Our Community!",
        message: "Create your account to start sharing your thoughts and connect with other bloggers."
    }
};

document.addEventListener('DOMContentLoaded', function() {
    // Initialize welcome message
    updateWelcomeMessage('login');
});

function updateWelcomeMessage(mode) {
    // Use setTimeout to ensure DOM elements are available
    setTimeout(() => {
        const titleElement = document.getElementById('welcomeTitle');
        const messageElement = document.getElementById('welcomeMessage');
        
        if (titleElement && messageElement) {
            titleElement.textContent = welcomeMessages[mode].title;
            messageElement.textContent = welcomeMessages[mode].message;
        }
    }, 0);
}

function showLogin() {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const toggleBtns = document.querySelectorAll('.toggle-btn');
    
    if (loginForm && registerForm && toggleBtns.length >= 2) {
        loginForm.classList.add('active');
        registerForm.classList.remove('active');
        toggleBtns[0].classList.add('active');
        toggleBtns[1].classList.remove('active');
        clearErrors();
        updateWelcomeMessage('login');
    }
}

function showRegister() {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const toggleBtns = document.querySelectorAll('.toggle-btn');
    
    if (loginForm && registerForm && toggleBtns.length >= 2) {
        registerForm.classList.add('active');
        loginForm.classList.remove('active');
        toggleBtns[1].classList.add('active');
        toggleBtns[0].classList.remove('active');
        clearErrors();
        updateWelcomeMessage('register');
    }
}

function clearErrors() {
    const errorElements = document.querySelectorAll('.error-text');
    errorElements.forEach(el => {
        if (el) el.textContent = '';
    });
}

function showNotification(message, type = 'success') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    if (document.body) {
        document.body.appendChild(notification);

        setTimeout(() => notification.classList.add('show'), 100);
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                if (document.body.contains(notification)) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
}

function validateRegisterForm() {
    clearErrors();
    let isValid = true;

    const fullNameEl = document.getElementById('fullName');
    const registerEmailEl = document.getElementById('registerEmail');
    const registerPasswordEl = document.getElementById('registerPassword');
    const confirmPasswordEl = document.getElementById('confirmPassword');

    if (!fullNameEl || !registerEmailEl || !registerPasswordEl || !confirmPasswordEl) {
        return false;
    }

    const fullName = fullNameEl.value.trim();
    const email = registerEmailEl.value.trim();
    const password = registerPasswordEl.value;
    const confirmPassword = confirmPasswordEl.value;

    if (fullName.length < 2) {
        const errorEl = document.getElementById('fullNameError');
        if (errorEl) errorEl.textContent = 'Full name must be at least 2 characters';
        isValid = false;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        const errorEl = document.getElementById('emailError');
        if (errorEl) errorEl.textContent = 'Please enter a valid email address';
        isValid = false;
    }

    if (password.length < 8) {
        const errorEl = document.getElementById('passwordError');
        if (errorEl) errorEl.textContent = 'Password must be at least 8 characters';
        isValid = false;
    }

    if (password !== confirmPassword) {
        const errorEl = document.getElementById('confirmPasswordError');
        if (errorEl) errorEl.textContent = 'Passwords do not match';
        isValid = false;
    }

    return isValid;
}

async function handleLogin(event) {
    event.preventDefault();
    
    const btn = document.getElementById('loginBtn');
    if (!btn) return;
    
    btn.disabled = true;
    btn.textContent = 'Logging in...';

    const formData = new FormData(event.target);
    const data = Object.fromEntries(formData);

    try {
        const response = await fetch(`${BASE_URL}/api/login/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
            credentials: 'include'
        });

        const result = await response.json();

        if (response.ok) {
            showNotification('Login successful! Redirecting...', 'success');
            setTimeout(() => {
                window.location.href = `${BASE_URL}/user/landing/`;
            }, 1500);
        } else {
            showNotification(result.detail || 'Login failed', 'error');
        }
    } catch (error) {
        showNotification('Network error. Please try again.', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Login';
    }
}

async function handleRegister(event) {
    event.preventDefault();
    
    if (!validateRegisterForm()) {
        return;
    }

    const btn = document.getElementById('registerBtn');
    if (!btn) return;
    
    btn.disabled = true;
    btn.textContent = 'Registering...';
    const formData = new FormData(event.target);
    const data = Object.fromEntries(formData);

    try {
        const response = await fetch(`${BASE_URL}/api/register/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (response.ok) {
            showNotification('Registration successful! Please login.', 'success');
            setTimeout(() => showLogin(), 1500);
            event.target.reset();
        } else {
            showNotification(result.detail || 'Registration failed', 'error');
        }
    } catch (error) {
        showNotification('Network error. Please try again.', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Register';
    }
}

function togglePassword(inputId, button) {
    const input = document.getElementById(inputId);
    if (!input || !button) return;
    
    const isPassword = input.type === 'password';
    input.type = isPassword ? 'text' : 'password';
    button.textContent = isPassword ? '👁️‍🗨️' : '👁️';
}

window.showLogin = showLogin;
window.showRegister = showRegister;
window.handleLogin = handleLogin;
window.handleRegister = handleRegister;
window.togglePassword = togglePassword;

