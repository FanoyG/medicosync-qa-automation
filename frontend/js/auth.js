const container = document.querySelector('.container');
const registerBtn = document.querySelector('.register-btn');
const loginBtn = document.querySelector('.login-btn');
const baseUrl = window.baseUrl.replace(/\/+$/, '');

document.querySelectorAll('.form-box').forEach((panel) => {
    let scrollTimer;

    panel.addEventListener('scroll', () => {
        panel.classList.add('is-scrolling');
        clearTimeout(scrollTimer);
        scrollTimer = setTimeout(() => {
            panel.classList.remove('is-scrolling');
        }, 900);
    }, { passive: true });
});

function getErrorMessage(payload) {
    if (Array.isArray(payload.detail)) {
        return payload.detail.map((error) => error.msg).join(', ');
    }

    return payload.detail || 'The request could not be completed.';
}

async function submitAuthForm(form, endpoint, payload) {
    const message = form.querySelector('.auth-message');
    message.textContent = '';

    try {
        const response = await fetch(`${baseUrl}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        const result = await response.json();

        if (!response.ok) {
            message.textContent = getErrorMessage(result);
            return;
        }

        message.textContent = result.message || 'Request completed successfully.';

        if (endpoint === '/auth/login') {
            if (!result.access_token) {
                message.textContent = 'Login succeeded, but the server did not return an access token.';
                return;
            }

            localStorage.setItem('access_token', result.access_token);
            localStorage.setItem('user_email', payload.email);
            window.location.href = '/pages/dashboard.html';
            return;
        }

        form.reset();
    } catch (error) {
        message.textContent = error instanceof Error
            ? error.message
            : 'Unable to connect to the authentication server.';
    }
}

registerBtn.addEventListener('click', () => {
    document.querySelector('.form-box.login form').reset();
    container.classList.add('active');
});

loginBtn.addEventListener('click', () => {
    document.querySelector('.form-box.register form').reset();
    container.classList.remove('active');
});

document.querySelector('.form-box.login form').addEventListener('submit', (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const fields = new FormData(form);

    submitAuthForm(form, '/auth/login', {
        email: fields.get('email'),
        password: fields.get('password'),
    });
});

document.querySelector('.form-box.register form').addEventListener('submit', (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const fields = new FormData(form);

    submitAuthForm(form, '/auth/register', {
        full_name: fields.get('full_name'),
        email: fields.get('email'),
        password: fields.get('password'),
        gender: fields.get('gender'),
        phone: {
            country_code: fields.get('country_code'),
            number: fields.get('phone_number'),
        },
    });
});