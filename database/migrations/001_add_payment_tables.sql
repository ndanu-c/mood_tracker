-- Migration to add payment and subscription support
USE mood_journal;

-- Add new columns to users table
ALTER TABLE users 
ADD COLUMN premium_since TIMESTAMP NULL AFTER is_premium,
ADD COLUMN paystack_customer_code VARCHAR(100) NULL AFTER premium_until,
ADD COLUMN paystack_authorization_code VARCHAR(100) NULL AFTER paystack_customer_code,
ADD COLUMN last_payment_date TIMESTAMP NULL AFTER paystack_authorization_code;

-- Rename premium_expires_at to premium_until for consistency
ALTER TABLE users 
CHANGE COLUMN premium_expires_at premium_until TIMESTAMP NULL;

-- Create payments table
CREATE TABLE IF NOT EXISTS payments (
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

-- Create subscriptions table
CREATE TABLE IF NOT EXISTS subscriptions (
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

-- Create payment webhook events table
CREATE TABLE IF NOT EXISTS payment_webhook_events (
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

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_premium ON users(is_premium, premium_until);
CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_reference ON payments(reference);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_webhook_events_reference ON payment_webhook_events(reference);
CREATE INDEX IF NOT EXISTS idx_webhook_events_processed ON payment_webhook_events(processed, created_at);

-- Migration complete message
SELECT 'Migration 001 completed successfully' AS message;
