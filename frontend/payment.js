// Payment functionality for Paystack integration
const API_BASE_URL = window.location.hostname === 'localhost'
    ? 'http://localhost:5000'
    : 'https://your-production-api-url.com';

// Paystack test public key
const PAYSTACK_PUBLIC_KEY = 'pk_test_e175695b8c5e24c1d571c697460b447c802e241d';

let paymentConfig = {};
let userEmail = '';

// Initialize payment page
document.addEventListener('DOMContentLoaded', function () {
    checkAuth();
    loadPaymentConfig();
    loadSubscriptionStatus();
    setupEventListeners();
});

function checkAuth() {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = 'login.html';
        return;
    }
}

function setupEventListeners() {
    // Payment button listeners
    document.querySelectorAll('.payment-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            const planType = this.getAttribute('data-plan');
            initiatePayment(planType);
        });
    });

    // Logout button
    document.getElementById('logoutBtn')?.addEventListener('click', function () {
        localStorage.removeItem('token');
        window.location.href = 'login.html';
    });
}

async function loadPaymentConfig() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/payment/config`);
        const data = await response.json();

        if (response.ok) {
            paymentConfig = data;
            // Update pricing display
            document.getElementById('monthlyPrice').textContent =
                new Intl.NumberFormat('en-NG').format(data.monthly_price || 2999);
            document.getElementById('yearlyPrice').textContent =
                new Intl.NumberFormat('en-NG').format(data.yearly_price || 29999);
        } else {
            showError('Failed to load payment configuration');
        }
    } catch (error) {
        console.error('Error loading payment config:', error);
        showError('Failed to load payment configuration');
    }
}

async function initiatePayment(planType) {
    try {
        showLoading(true);

        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE_URL}/api/payment/initialize`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                plan_type: planType,
                callback_url: `${window.location.origin}/payment-success.html`
            })
        });

        const data = await response.json();

        if (response.ok) {
            // Get user email for Paystack
            await getUserEmail();

            // Initialize Paystack payment
            const amount = planType === 'yearly' ?
                (paymentConfig.yearly_price || 2999900) :
                (paymentConfig.monthly_price || 299900);

            const handler = PaystackPop.setup({
                key: PAYSTACK_PUBLIC_KEY,
                email: userEmail,
                amount: amount,
                currency: 'NGN',
                ref: data.reference,
                callback: function (response) {
                    verifyPayment(response.reference);
                },
                onClose: function () {
                    showLoading(false);
                    showMessage('Payment cancelled', 'warning');
                }
            });

            showLoading(false);
            handler.openIframe();
        } else {
            showLoading(false);
            showError(data.error || 'Failed to initialize payment');
        }
    } catch (error) {
        showLoading(false);
        console.error('Error initiating payment:', error);
        showError('Failed to initiate payment');
    }
}

async function getUserEmail() {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE_URL}/api/user/profile`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        const data = await response.json();
        if (response.ok) {
            userEmail = data.email;
        }
    } catch (error) {
        console.error('Error getting user email:', error);
    }
}

async function verifyPayment(reference) {
    try {
        showLoading(true);

        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE_URL}/api/payment/verify`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ reference })
        });

        const data = await response.json();

        if (response.ok) {
            showLoading(false);
            showMessage('Payment successful! Welcome to Premium!', 'success');

            // Redirect to dashboard after success
            setTimeout(() => {
                window.location.href = 'index.html';
            }, 2000);
        } else {
            showLoading(false);
            showError(data.error || 'Payment verification failed');
        }
    } catch (error) {
        showLoading(false);
        console.error('Error verifying payment:', error);
        showError('Payment verification failed');
    }
}

function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.display = show ? 'flex' : 'none';
    }
}

function showMessage(message, type = 'info') {
    // Create message element
    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${type}`;
    messageDiv.textContent = message;

    // Add to page
    document.body.appendChild(messageDiv);

    // Auto remove after 5 seconds
    setTimeout(() => {
        if (messageDiv.parentNode) {
            messageDiv.parentNode.removeChild(messageDiv);
        }
    }, 5000);
}

function showError(message) {
    showMessage(message, 'error');
}

// Load subscription status
async function loadSubscriptionStatus() {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE_URL}/api/subscription/status`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        const data = await response.json();

        if (response.ok) {
            updateStatusUI(data);
        } else {
            showError('Failed to load subscription status');
        }
    } catch (error) {
        console.error('Error loading subscription status:', error);
        showError('Failed to load subscription status');
    }
}

function updateStatusUI(status) {
    const statusElement = document.getElementById('subscriptionStatus');
    if (!statusElement) return;

    if (status.is_premium) {
        const expiryDate = new Date(status.premium_expires).toLocaleDateString();
        statusElement.innerHTML = `
            <div class="status-message success">
                <i class="fas fa-check-circle"></i>
                <span>Premium active until ${expiryDate}</span>
            </div>
        `;
    } else if (status.trial_expired) {
        statusElement.innerHTML = `
            <div class="status-message error">
                <i class="fas fa-exclamation-circle"></i>
                <span>Your trial has expired. Please upgrade to continue.</span>
            </div>
        `;
    } else {
        const trialEnd = new Date(new Date(status.created_at).getTime() + 14 * 24 * 60 * 60 * 1000);
        const daysLeft = Math.ceil((trialEnd - new Date()) / (1000 * 60 * 60 * 24));
        statusElement.innerHTML = `
            <div class="status-message info">
                <i class="fas fa-info-circle"></i>
                <span>${daysLeft} days left in your free trial</span>
            </div>
        `;
    }
}
