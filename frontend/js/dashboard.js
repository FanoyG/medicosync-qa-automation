const token = localStorage.getItem('access_token');

if (!token) {
    window.location.replace('/');
} else {
    document.getElementById('user-email').textContent =
        localStorage.getItem('user_email') || '--';

    document.getElementById('logout-btn').addEventListener('click', () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_email');
        window.location.replace('/');
    });
}
