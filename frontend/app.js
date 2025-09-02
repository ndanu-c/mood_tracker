// API Configuration - Auto-detect environment
const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:5000/api'  // Development
    : `${window.location.protocol}//${window.location.hostname}/api`;  // Production

// Global state
let currentUser = null;
let authToken = null;
let currentSection = 'dashboard';
let moodChart = null;
let emotionChart = null;
let timelineChart = null;

// DOM Elements
const authModal = document.getElementById('authModal');
const loginForm = document.getElementById('loginForm');
const registerForm = document.getElementById('registerForm');
const mainContent = document.getElementById('mainContent');
const loadingSpinner = document.getElementById('loadingSpinner');
const toastContainer = document.getElementById('toastContainer');

// Initialize app
document.addEventListener('DOMContentLoaded', function () {
    initializeApp();
    setupEventListeners();
    checkAuthStatus();
});

// App Initialization
function initializeApp() {
    // Check for stored auth token
    authToken = localStorage.getItem('authToken');

    if (authToken) {
        hideAuthModal();
        loadUserData();
    } else {
        showAuthModal();
    }
}

// Event Listeners Setup
function setupEventListeners() {
    // Navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', handleNavigation);
    });

    // Mobile menu toggle
    const navToggle = document.getElementById('navToggle');
    const navMenu = document.getElementById('navMenu');
    navToggle.addEventListener('click', () => {
        navMenu.classList.toggle('active');
    });

    // Auth forms
    document.getElementById('showRegister').addEventListener('click', showRegisterForm);
    document.getElementById('showLogin').addEventListener('click', showLoginForm);
    loginForm.addEventListener('submit', handleLogin);
    registerForm.addEventListener('submit', handleRegister);

    // Logout
    document.getElementById('logoutBtn').addEventListener('click', handleLogout);

    // Journal functionality
    document.getElementById('newEntryBtn').addEventListener('click', showEntryForm);
    document.getElementById('cancelEntry').addEventListener('click', hideEntryForm);
    document.getElementById('journalForm').addEventListener('submit', handleCreateEntry);
}

// Authentication Functions
async function handleLogin(e) {
    e.preventDefault();

    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;

    showLoading();

    try {
        const response = await fetch(`${API_BASE_URL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (response.ok) {
            authToken = data.access_token;
            currentUser = {
                id: data.user_id,
                username: data.username
            };

            localStorage.setItem('authToken', authToken);
            localStorage.setItem('currentUser', JSON.stringify(currentUser));

            hideAuthModal();
            showToast('Welcome back!', 'success');
            loadUserData();
        } else {
            showToast(data.error || 'Login failed', 'error');
        }
    } catch (error) {
        showToast('Network error. Please try again.', 'error');
        console.error('Login error:', error);
    }

    hideLoading();
}

async function handleRegister(e) {
    e.preventDefault();

    const username = document.getElementById('registerUsername').value;
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;

    showLoading();

    try {
        const response = await fetch(`${API_BASE_URL}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, email, password })
        });

        const data = await response.json();

        if (response.ok) {
            authToken = data.access_token;
            currentUser = {
                id: data.user_id,
                username: username
            };

            localStorage.setItem('authToken', authToken);
            localStorage.setItem('currentUser', JSON.stringify(currentUser));

            hideAuthModal();
            showToast('Account created successfully! Welcome to Mood Journal!', 'success');
            loadUserData();
        } else {
            showToast(data.error || 'Registration failed', 'error');
        }
    } catch (error) {
        showToast('Network error. Please try again.', 'error');
        console.error('Registration error:', error);
    }

    hideLoading();
}

function handleLogout() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');

    showAuthModal();
    showToast('Logged out successfully', 'success');

    // Reset forms
    loginForm.reset();
    registerForm.reset();
}

// UI Helper Functions
function showAuthModal() {
    authModal.style.display = 'flex';
    mainContent.style.display = 'none';
}

function hideAuthModal() {
    authModal.style.display = 'none';
    mainContent.style.display = 'block';
}

function showRegisterForm() {
    loginForm.classList.add('hidden');
    registerForm.classList.remove('hidden');
    document.getElementById('authTitle').textContent = 'Create Your Account';
}

function showLoginForm() {
    registerForm.classList.add('hidden');
    loginForm.classList.remove('hidden');
    document.getElementById('authTitle').textContent = 'Welcome Back';
}

function showLoading() {
    loadingSpinner.classList.remove('hidden');
}

function hideLoading() {
    loadingSpinner.classList.add('hidden');
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div class="toast-content">
            <p>${message}</p>
        </div>
    `;

    toastContainer.appendChild(toast);

    // Auto remove after 5 seconds
    setTimeout(() => {
        toast.remove();
    }, 5000);
}

// Navigation
function handleNavigation(e) {
    e.preventDefault();

    const targetSection = e.currentTarget.dataset.section;

    // Update active nav link
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    e.currentTarget.classList.add('active');

    // Show target section
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    document.getElementById(targetSection).classList.add('active');

    currentSection = targetSection;

    // Load section-specific data
    loadSectionData(targetSection);

    // Close mobile menu
    document.getElementById('navMenu').classList.remove('active');
}

// Data Loading Functions
async function loadUserData() {
    try {
        await Promise.all([
            loadUserStatus(),
            loadDashboardData(),
            loadJournalEntries()
        ]);
    } catch (error) {
        console.error('Error loading user data:', error);
        showToast('Error loading data', 'error');
    }
}

async function loadUserStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/user/status`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        const data = await response.json();

        if (response.ok) {
            updateTrialStatus(data.days_remaining);
            updateProfileInfo(data);
        }
    } catch (error) {
        console.error('Error loading user status:', error);
    }
}

async function loadDashboardData() {
    try {
        const [entriesResponse, summaryResponse] = await Promise.all([
            fetch(`${API_BASE_URL}/journal/entries`, {
                headers: { 'Authorization': `Bearer ${authToken}` }
            }),
            fetch(`${API_BASE_URL}/mood/summary`, {
                headers: { 'Authorization': `Bearer ${authToken}` }
            })
        ]);

        const entriesData = await entriesResponse.json();
        const summaryData = await summaryResponse.json();

        if (entriesResponse.ok) {
            updateDashboardStats(entriesData.entries);
            updateRecentEntries(entriesData.entries.slice(0, 5));
        }

        if (summaryResponse.ok && summaryData.mood_summary) {
            updateCurrentMood(summaryData.mood_summary);
            createMoodChart(summaryData.mood_summary);
        }

    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

async function loadJournalEntries() {
    try {
        const response = await fetch(`${API_BASE_URL}/journal/entries`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        const data = await response.json();

        if (response.ok) {
            displayJournalEntries(data.entries);
        }
    } catch (error) {
        console.error('Error loading journal entries:', error);
    }
}

async function loadSectionData(section) {
    switch (section) {
        case 'dashboard':
            await loadDashboardData();
            break;
        case 'journal':
            await loadJournalEntries();
            break;
        case 'insights':
            await loadInsightsData();
            break;
        case 'profile':
            await loadUserStatus();
            break;
    }
}

// Dashboard Updates
function updateTrialStatus(daysRemaining) {
    const trialDaysElement = document.getElementById('trialDays');
    if (daysRemaining > 0) {
        trialDaysElement.textContent = `${daysRemaining} days remaining`;
        trialDaysElement.parentElement.style.background = 'rgba(16, 185, 129, 0.2)';
    } else {
        trialDaysElement.textContent = 'Trial expired';
        trialDaysElement.parentElement.style.background = 'rgba(239, 68, 68, 0.2)';
    }
}

function updateDashboardStats(entries) {
    document.getElementById('totalEntries').textContent = entries.length;

    // Calculate streak (simplified - consecutive days with entries)
    const today = new Date();
    let streak = 0;
    const entriesByDate = {};

    entries.forEach(entry => {
        const date = new Date(entry.created_at).toDateString();
        entriesByDate[date] = true;
    });

    for (let i = 0; i < 30; i++) {
        const checkDate = new Date(today);
        checkDate.setDate(today.getDate() - i);

        if (entriesByDate[checkDate.toDateString()]) {
            streak++;
        } else {
            break;
        }
    }

    document.getElementById('streakDays').textContent = streak;
}

function updateCurrentMood(moodSummary) {
    const moodDisplay = document.getElementById('currentMood');
    const moodEmoji = moodDisplay.querySelector('.mood-emoji');
    const moodText = moodDisplay.querySelector('.mood-text');

    if (moodSummary.mood_averages) {
        const averages = moodSummary.mood_averages;
        const dominantEmotion = Object.keys(averages).reduce((a, b) =>
            averages[a] > averages[b] ? a : b
        );

        const emojiMap = {
            happiness: '😊',
            sadness: '😢',
            anger: '😠',
            fear: '😰',
            surprise: '😲',
            disgust: '🤢'
        };

        const textMap = {
            happiness: 'Happy',
            sadness: 'Sad',
            anger: 'Angry',
            fear: 'Anxious',
            surprise: 'Surprised',
            disgust: 'Disgusted'
        };

        moodEmoji.textContent = emojiMap[dominantEmotion] || '😐';
        moodText.textContent = textMap[dominantEmotion] || 'Neutral';
    }
}

function updateRecentEntries(entries) {
    const container = document.getElementById('recentEntriesList');

    if (entries.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-book-open"></i>
                <p>No entries yet. Start journaling to see your recent entries here!</p>
            </div>
        `;
        return;
    }

    container.innerHTML = entries.map(entry => `
        <div class="entry-preview">
            <div class="entry-header">
                <span class="entry-title">${entry.title || 'Untitled Entry'}</span>
                <span class="entry-date">${formatDate(entry.created_at)}</span>
            </div>
            <div class="entry-content">${entry.content}</div>
            <div class="entry-mood">
                <div class="mood-indicator mood-${entry.overall_sentiment || 'neutral'}"></div>
                <span>${capitalizeFirst(entry.overall_sentiment || 'neutral')}</span>
            </div>
        </div>
    `).join('');
}

// Journal Functions
function showEntryForm() {
    document.getElementById('entryForm').classList.remove('hidden');
    document.getElementById('entryContent').focus();
}

function hideEntryForm() {
    document.getElementById('entryForm').classList.add('hidden');
    document.getElementById('journalForm').reset();
}

async function handleCreateEntry(e) {
    e.preventDefault();

    const title = document.getElementById('entryTitle').value;
    const content = document.getElementById('entryContent').value;

    if (!content.trim()) {
        showToast('Please write something in your journal entry', 'warning');
        return;
    }

    showLoading();

    try {
        const response = await fetch(`${API_BASE_URL}/journal/entries`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ title, content })
        });

        const data = await response.json();

        if (response.ok) {
            showToast('Journal entry saved successfully!', 'success');
            hideEntryForm();

            // Reload journal entries and dashboard
            await Promise.all([
                loadJournalEntries(),
                loadDashboardData()
            ]);
        } else {
            showToast(data.error || 'Failed to save entry', 'error');
        }
    } catch (error) {
        showToast('Network error. Please try again.', 'error');
        console.error('Create entry error:', error);
    }

    hideLoading();
}

function displayJournalEntries(entries) {
    const container = document.getElementById('entriesContainer');

    if (entries.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-book"></i>
                <h3>No journal entries yet</h3>
                <p>Start your emotional wellness journey by writing your first entry!</p>
                <button class="btn-primary" onclick="showEntryForm()">
                    <i class="fas fa-plus"></i> Write First Entry
                </button>
            </div>
        `;
        return;
    }

    container.innerHTML = entries.map(entry => `
        <div class="journal-entry">
            <div class="entry-full-header">
                <div>
                    <h4 class="entry-full-title">${entry.title || 'Untitled Entry'}</h4>
                    <p class="entry-full-date">${formatDate(entry.created_at)}</p>
                </div>
            </div>
            <div class="entry-full-content">${entry.content}</div>
            ${entry.overall_sentiment ? `
                <div class="entry-sentiment">
                    <div class="sentiment-overall">
                        <div class="mood-indicator mood-${entry.overall_sentiment}"></div>
                        <span>Overall: ${capitalizeFirst(entry.overall_sentiment)}</span>
                    </div>
                    <div class="sentiment-scores">
                        ${entry.happiness_score ? `
                            <div class="sentiment-score">
                                <span class="sentiment-label">Joy</span>
                                <span class="sentiment-value">${Math.round(entry.happiness_score * 100)}%</span>
                            </div>
                        ` : ''}
                        ${entry.sadness_score ? `
                            <div class="sentiment-score">
                                <span class="sentiment-label">Sadness</span>
                                <span class="sentiment-value">${Math.round(entry.sadness_score * 100)}%</span>
                            </div>
                        ` : ''}
                        ${entry.anger_score ? `
                            <div class="sentiment-score">
                                <span class="sentiment-label">Anger</span>
                                <span class="sentiment-value">${Math.round(entry.anger_score * 100)}%</span>
                            </div>
                        ` : ''}
                    </div>
                </div>
            ` : ''}
        </div>
    `).join('');
}

// Insights Functions
async function loadInsightsData() {
    try {
        const [entriesResponse, summaryResponse] = await Promise.all([
            fetch(`${API_BASE_URL}/journal/entries`, {
                headers: { 'Authorization': `Bearer ${authToken}` }
            }),
            fetch(`${API_BASE_URL}/mood/summary`, {
                headers: { 'Authorization': `Bearer ${authToken}` }
            })
        ]);

        const entriesData = await entriesResponse.json();
        const summaryData = await summaryResponse.json();

        if (entriesResponse.ok && summaryResponse.ok) {
            createEmotionChart(summaryData.mood_summary);
            createTimelineChart(entriesData.entries);
            generateInsights(entriesData.entries, summaryData.mood_summary);
        }
    } catch (error) {
        console.error('Error loading insights:', error);
    }
}

// Chart Functions
function createMoodChart(moodSummary) {
    const ctx = document.getElementById('moodChart');

    if (moodChart) {
        moodChart.destroy();
    }

    if (!moodSummary || !moodSummary.mood_averages) {
        ctx.getContext('2d').clearRect(0, 0, ctx.width, ctx.height);
        return;
    }

    const averages = moodSummary.mood_averages;

    // Ensure all values are valid numbers
    const chartData = [
        averages.happiness || 0,
        averages.sadness || 0,
        averages.anger || 0,
        averages.fear || 0,
        averages.surprise || 0,
        averages.disgust || 0
    ];

    moodChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Happiness', 'Sadness', 'Anger', 'Fear', 'Surprise', 'Disgust'],
            datasets: [{
                label: 'Average Mood Scores',
                data: chartData,
                borderColor: '#6366f1',
                backgroundColor: 'rgba(99, 102, 241, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 1
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

function createEmotionChart(moodSummary) {
    const ctx = document.getElementById('emotionChart');

    if (!ctx) {
        console.error('emotionChart canvas not found');
        return;
    }

    if (emotionChart) {
        emotionChart.destroy();
    }

    if (!moodSummary || !moodSummary.mood_averages) {
        ctx.getContext('2d').clearRect(0, 0, ctx.width, ctx.height);
        return;
    }

    const averages = moodSummary.mood_averages;

    // Ensure all values are valid numbers
    const chartData = [
        averages.happiness || 0,
        averages.sadness || 0,
        averages.anger || 0,
        averages.fear || 0,
        averages.surprise || 0,
        averages.disgust || 0
    ];

    emotionChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Happiness', 'Sadness', 'Anger', 'Fear', 'Surprise', 'Disgust'],
            datasets: [{
                data: chartData,
                backgroundColor: [
                    '#10b981',
                    '#3b82f6',
                    '#ef4444',
                    '#f59e0b',
                    '#8b5cf6',
                    '#6b7280'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            aspectRatio: 1,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        boxWidth: 12,
                        padding: 15
                    }
                }
            },
            animation: {
                duration: 800,
                animateRotate: true,
                animateScale: false
            },
            layout: {
                padding: 10
            }
        }
    });
}

function createTimelineChart(entries) {
    const ctx = document.getElementById('timelineChart');

    if (!ctx) {
        console.error('timelineChart canvas not found');
        return;
    }

    if (timelineChart) {
        timelineChart.destroy();
    }

    if (!entries || entries.length === 0) {
        ctx.getContext('2d').clearRect(0, 0, ctx.width, ctx.height);
        return;
    }

    // Group entries by date and calculate average happiness
    const dailyMood = {};
    entries.forEach(entry => {
        const date = new Date(entry.created_at).toDateString();
        if (!dailyMood[date]) {
            dailyMood[date] = { total: 0, count: 0 };
        }
        const happiness = parseFloat(entry.happiness_score) || 0;
        dailyMood[date].total += happiness;
        dailyMood[date].count++;
    });

    const sortedDates = Object.keys(dailyMood).sort((a, b) => new Date(a) - new Date(b));
    const moodData = sortedDates.map(date => {
        const avg = dailyMood[date].total / dailyMood[date].count;
        return isNaN(avg) ? 0 : avg;
    });

    timelineChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: sortedDates.map(date => formatDate(date)),
            datasets: [{
                label: 'Daily Mood',
                data: moodData,
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                tension: 0.4,
                fill: true,
                pointRadius: 4,
                pointHoverRadius: 6,
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            aspectRatio: 2,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 1,
                    ticks: {
                        callback: function (value) {
                            return Math.round(value * 100) + '%';
                        },
                        stepSize: 0.2
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return 'Mood: ' + Math.round(context.parsed.y * 100) + '%';
                        }
                    }
                }
            },
            animation: {
                duration: 800,
                easing: 'easeInOutQuart'
            },
            layout: {
                padding: 10
            },
            elements: {
                point: {
                    hoverBackgroundColor: '#10b981'
                }
            }
        }
    });
}

function generateInsights(entries, moodSummary) {
    const container = document.getElementById('insightsList');
    const insights = [];

    if (!entries || entries.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-lightbulb"></i>
                <p>Write more journal entries to unlock personalized insights!</p>
            </div>
        `;
        return;
    }

    // Generate insights based on data
    if (moodSummary && moodSummary.mood_averages) {
        const averages = moodSummary.mood_averages;
        const dominantEmotion = Object.keys(averages).reduce((a, b) =>
            averages[a] > averages[b] ? a : b
        );

        insights.push({
            title: 'Dominant Emotion',
            description: `Your most frequent emotion is ${dominantEmotion}. This represents ${Math.round(averages[dominantEmotion] * 100)}% of your emotional state.`
        });

        if (averages.happiness > 0.6) {
            insights.push({
                title: 'Positive Outlook',
                description: 'You maintain a generally positive emotional state. Keep up the great work!'
            });
        }

        if (entries.length >= 7) {
            insights.push({
                title: 'Consistent Journaling',
                description: `You've written ${entries.length} entries. Regular journaling helps improve emotional awareness and mental well-being.`
            });
        }
    }

    if (insights.length === 0) {
        insights.push({
            title: 'Getting Started',
            description: 'Continue writing journal entries to unlock personalized insights about your emotional patterns.'
        });
    }

    container.innerHTML = insights.map(insight => `
        <div class="insight-item">
            <div class="insight-title">${insight.title}</div>
            <div class="insight-description">${insight.description}</div>
        </div>
    `).join('');
}

function updateProfileInfo(userData) {
    const profileDetails = document.getElementById('profileDetails');
    const subscriptionDetails = document.getElementById('subscriptionDetails');

    profileDetails.innerHTML = `
        <div class="detail-item">
            <span class="detail-label">Username</span>
            <span class="detail-value">${userData.username}</span>
        </div>
        <div class="detail-item">
            <span class="detail-label">Email</span>
            <span class="detail-value">${userData.email}</span>
        </div>
        <div class="detail-item">
            <span class="detail-label">Member Since</span>
            <span class="detail-value">${formatDate(new Date())}</span>
        </div>
    `;

    subscriptionDetails.innerHTML = `
        <div class="detail-item">
            <span class="detail-label">Plan</span>
            <span class="detail-value">${userData.is_premium ? 'Premium' : 'Free Trial'}</span>
        </div>
        <div class="detail-item">
            <span class="detail-label">Status</span>
            <span class="detail-value">${userData.trial_active ? 'Active' : 'Expired'}</span>
        </div>
        <div class="detail-item">
            <span class="detail-label">Days Remaining</span>
            <span class="detail-value">${userData.days_remaining}</span>
        </div>
    `;
}

// Utility Functions
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function capitalizeFirst(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function checkAuthStatus() {
    // Check if token is still valid
    if (authToken) {
        fetch(`${API_BASE_URL}/user/status`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        }).then(response => {
            if (!response.ok) {
                // Token is invalid, logout
                handleLogout();
            }
        }).catch(() => {
            // Network error, but keep token for now
        });
    }
}
