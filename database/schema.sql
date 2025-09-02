-- Create database
CREATE DATABASE IF NOT EXISTS mood_journal;
USE mood_journal;

-- Users table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    trial_start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_premium BOOLEAN DEFAULT FALSE,
    premium_since TIMESTAMP NULL,
    premium_until TIMESTAMP NULL,
    paystack_customer_code VARCHAR(100) NULL,
    paystack_authorization_code VARCHAR(100) NULL,
    last_payment_date TIMESTAMP NULL
);

-- Journal entries table
CREATE TABLE journal_entries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Mood analysis table
CREATE TABLE mood_analysis (
    id INT AUTO_INCREMENT PRIMARY KEY,
    entry_id INT NOT NULL,
    happiness_score DECIMAL(5,4) DEFAULT 0,
    sadness_score DECIMAL(5,4) DEFAULT 0,
    anger_score DECIMAL(5,4) DEFAULT 0,
    fear_score DECIMAL(5,4) DEFAULT 0,
    surprise_score DECIMAL(5,4) DEFAULT 0,
    disgust_score DECIMAL(5,4) DEFAULT 0,
    overall_sentiment VARCHAR(20) NOT NULL,
    confidence_score DECIMAL(5,4) DEFAULT 0,
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (entry_id) REFERENCES journal_entries(id) ON DELETE CASCADE
);

-- Payments table
CREATE TABLE payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    reference VARCHAR(100) NOT NULL,
    paystack_reference VARCHAR(100) NULL,
    amount INT NOT NULL, -- Amount in kobo
    currency VARCHAR(3) DEFAULT 'NGN',
    status ENUM('pending', 'success', 'failed') DEFAULT 'pending',
    plan_type ENUM('monthly', 'yearly') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verified_at TIMESTAMP NULL,
    metadata JSON NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_reference (reference)
);

-- Subscriptions table
CREATE TABLE subscriptions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    paystack_subscription_code VARCHAR(100) NOT NULL,
    plan_code VARCHAR(100) NOT NULL,
    status ENUM('active', 'cancelled', 'expired') NOT NULL,
    starts_at TIMESTAMP NOT NULL,
    ends_at TIMESTAMP NULL,
    next_payment_date TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_subscription (paystack_subscription_code)
);

-- Payment webhook events
CREATE TABLE payment_webhook_events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    paystack_event_id VARCHAR(100) NOT NULL,
    reference VARCHAR(100) NULL,
    status VARCHAR(50) NOT NULL,
    payload JSON NOT NULL,
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP NULL,
    UNIQUE KEY unique_event (paystack_event_id)
);

-- Create indexes for better performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_premium ON users(is_premium, premium_until);
CREATE INDEX idx_journal_user_id ON journal_entries(user_id);
CREATE INDEX idx_journal_created_at ON journal_entries(created_at);
CREATE INDEX idx_mood_entry_id ON mood_analysis(entry_id);
CREATE INDEX idx_payments_user_id ON payments(user_id);
CREATE INDEX idx_payments_reference ON payments(reference);
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
CREATE INDEX idx_webhook_events_reference ON payment_webhook_events(reference);
CREATE INDEX idx_webhook_events_processed ON payment_webhook_events(processed, created_at);
