-- Migration to add payment and subscription support with MySQL-compatible syntax
USE mood_journal;

-- Helper procedure to add column if it doesn't exist
DELIMITER //
CREATE PROCEDURE AddColumnIfNotExists(
    IN dbName VARCHAR(100),
    IN tableName VARCHAR(100),
    IN columnName VARCHAR(100),
    IN columnDefinition TEXT
)
BEGIN
    DECLARE column_exists INT;
    
    SELECT COUNT(*) INTO column_exists
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = dbName
    AND TABLE_NAME = tableName
    AND COLUMN_NAME = columnName;
    
    IF column_exists = 0 THEN
        SET @ddl = CONCAT('ALTER TABLE ', tableName, ' ADD COLUMN ', columnName, ' ', columnDefinition);
        PREPARE stmt FROM @ddl;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
END //
DELIMITER ;

-- Add columns using the helper procedure
CALL AddColumnIfNotExists('mood_journal', 'users', 'premium_until', 'TIMESTAMP NULL AFTER is_premium');
CALL AddColumnIfNotExists('mood_journal', 'users', 'premium_since', 'TIMESTAMP NULL');
CALL AddColumnIfNotExists('mood_journal', 'users', 'paystack_customer_code', 'VARCHAR(100) NULL');
CALL AddColumnIfNotExists('mood_journal', 'users', 'paystack_authorization_code', 'VARCHAR(100) NULL');
CALL AddColumnIfNotExists('mood_journal', 'users', 'last_payment_date', 'TIMESTAMP NULL');

-- Drop the temporary procedure
DROP PROCEDURE IF EXISTS AddColumnIfNotExists;

-- Create tables if they don't exist
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
) ENGINE=InnoDB;

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
) ENGINE=InnoDB;

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
) ENGINE=InnoDB;

-- Add indexes if they don't exist
SET @prepared_statement = (SELECT IF(
    (
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_SCHEMA = 'mood_journal'
        AND TABLE_NAME = 'users'
        AND INDEX_NAME = 'idx_users_premium'
    ) = 0,
    'CREATE INDEX idx_users_premium ON users(is_premium, premium_until)',
    'SELECT 1'
));
PREPARE create_index FROM @prepared_statement;
EXECUTE create_index;
DEALLOCATE PREPARE create_index;

SET @prepared_statement = (SELECT IF(
    (
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_SCHEMA = 'mood_journal'
        AND TABLE_NAME = 'payments'
        AND INDEX_NAME = 'idx_payments_user_id'
    ) = 0,
    'CREATE INDEX idx_payments_user_id ON payments(user_id)',
    'SELECT 1'
));
PREPARE create_index FROM @prepared_statement;
EXECUTE create_index;
DEALLOCATE PREPARE create_index;

SET @prepared_statement = (SELECT IF(
    (
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_SCHEMA = 'mood_journal'
        AND TABLE_NAME = 'payments'
        AND INDEX_NAME = 'idx_payments_reference'
    ) = 0,
    'CREATE INDEX idx_payments_reference ON payments(reference)',
    'SELECT 1'
));
PREPARE create_index FROM @prepared_statement;
EXECUTE create_index;
DEALLOCATE PREPARE create_index;

SET @prepared_statement = (SELECT IF(
    (
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_SCHEMA = 'mood_journal'
        AND TABLE_NAME = 'payments'
        AND INDEX_NAME = 'idx_payments_status'
    ) = 0,
    'CREATE INDEX idx_payments_status ON payments(status)',
    'SELECT 1'
));
PREPARE create_index FROM @prepared_statement;
EXECUTE create_index;
DEALLOCATE PREPARE create_index;

SET @prepared_statement = (SELECT IF(
    (
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_SCHEMA = 'mood_journal'
        AND TABLE_NAME = 'subscriptions'
        AND INDEX_NAME = 'idx_subscriptions_user_id'
    ) = 0,
    'CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id)',
    'SELECT 1'
));
PREPARE create_index FROM @prepared_statement;
EXECUTE create_index;
DEALLOCATE PREPARE create_index;

SET @prepared_statement = (SELECT IF(
    (
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_SCHEMA = 'mood_journal'
        AND TABLE_NAME = 'subscriptions'
        AND INDEX_NAME = 'idx_subscriptions_status'
    ) = 0,
    'CREATE INDEX idx_subscriptions_status ON subscriptions(status)',
    'SELECT 1'
));
PREPARE create_index FROM @prepared_statement;
EXECUTE create_index;
DEALLOCATE PREPARE create_index;

SET @prepared_statement = (SELECT IF(
    (
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_SCHEMA = 'mood_journal'
        AND TABLE_NAME = 'payment_webhook_events'
        AND INDEX_NAME = 'idx_webhook_events_reference'
    ) = 0,
    'CREATE INDEX idx_webhook_events_reference ON payment_webhook_events(reference)',
    'SELECT 1'
));
PREPARE create_index FROM @prepared_statement;
EXECUTE create_index;
DEALLOCATE PREPARE create_index;

SET @prepared_statement = (SELECT IF(
    (
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_SCHEMA = 'mood_journal'
        AND TABLE_NAME = 'payment_webhook_events'
        AND INDEX_NAME = 'idx_webhook_events_processed'
    ) = 0,
    'CREATE INDEX idx_webhook_events_processed ON payment_webhook_events(processed, created_at)',
    'SELECT 1'
));
PREPARE create_index FROM @prepared_statement;
EXECUTE create_index;
DEALLOCATE PREPARE create_index;

-- Migration complete message
SELECT 'Migration 002 completed successfully' AS message;
