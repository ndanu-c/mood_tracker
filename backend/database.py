import pymysql
from config import Config
import logging
import time

class Database:
    def __init__(self):
        self.config = Config()
        self.connection = None
        self._last_ping = 0
    
    def connect(self):
        """Establish database connection"""
        try:
            if self.connection:
                self.connection.close()
            
            self.connection = pymysql.connect(
                host=self.config.DB_HOST,
                port=self.config.DB_PORT,
                user=self.config.DB_USER,
                password=self.config.DB_PASSWORD,
                database=self.config.DB_NAME,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True,
                connect_timeout=10,
                read_timeout=10,
                write_timeout=10
            )
            self._last_ping = time.time()
            return self.connection
        except Exception as e:
            logging.error(f"Database connection error: {e}")
            raise e
    
    def _ensure_connection(self):
        """Ensure database connection is alive"""
        current_time = time.time()
        
        # Ping connection every 30 seconds to keep it alive
        if current_time - self._last_ping > 30:
            try:
                if self.connection:
                    self.connection.ping(reconnect=True)
                    self._last_ping = current_time
            except:
                self.connect()
        
        # Check if connection exists and is open
        if not self.connection or not self.connection.open:
            self.connect()
    
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def execute_query(self, query, params=None):
        """Execute a SELECT query and return results"""
        self._ensure_connection()
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params or ())
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Query execution error: {e}")
            # Try to reconnect once
            try:
                self.connect()
                with self.connection.cursor() as cursor:
                    cursor.execute(query, params or ())
                    return cursor.fetchall()
            except Exception as e2:
                logging.error(f"Retry query execution error: {e2}")
                raise e2
    
    def execute_update(self, query, params=None):
        """Execute INSERT, UPDATE, DELETE queries"""
        self._ensure_connection()
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params or ())
                return cursor.lastrowid
        except Exception as e:
            logging.error(f"Update execution error: {e}")
            # Try to reconnect once
            try:
                self.connect()
                with self.connection.cursor() as cursor:
                    cursor.execute(query, params or ())
                    return cursor.lastrowid
            except Exception as e2:
                logging.error(f"Retry update execution error: {e2}")
                raise e2
    
    def get_user_by_email(self, email):
        """Get user by email"""
        query = "SELECT * FROM users WHERE email = %s"
        result = self.execute_query(query, (email,))
        return result[0] if result else None
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        query = "SELECT * FROM users WHERE id = %s"
        result = self.execute_query(query, (user_id,))
        return result[0] if result else None
    
    def create_user(self, username, email, password_hash):
        """Create new user"""
        query = """
        INSERT INTO users (username, email, password_hash, trial_start_date) 
        VALUES (%s, %s, %s, NOW())
        """
        return self.execute_update(query, (username, email, password_hash))
    
    def create_journal_entry(self, user_id, title, content):
        """Create new journal entry"""
        query = """
        INSERT INTO journal_entries (user_id, title, content) 
        VALUES (%s, %s, %s)
        """
        return self.execute_update(query, (user_id, title, content))
    
    def get_user_entries(self, user_id, limit=50):
        """Get user's journal entries"""
        query = """
        SELECT je.*, ma.overall_sentiment, ma.happiness_score, ma.sadness_score, 
               ma.anger_score, ma.fear_score, ma.surprise_score, ma.disgust_score
        FROM journal_entries je
        LEFT JOIN mood_analysis ma ON je.id = ma.entry_id
        WHERE je.user_id = %s
        ORDER BY je.created_at DESC
        LIMIT %s
        """
        return self.execute_query(query, (user_id, limit))
    
    def save_mood_analysis(self, entry_id, sentiment_data):
        """Save mood analysis results"""
        query = """
        INSERT INTO mood_analysis 
        (entry_id, happiness_score, sadness_score, anger_score, fear_score, 
         surprise_score, disgust_score, overall_sentiment, confidence_score)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        return self.execute_update(query, (
            entry_id,
            sentiment_data.get('happiness', 0),
            sentiment_data.get('sadness', 0),
            sentiment_data.get('anger', 0),
            sentiment_data.get('fear', 0),
            sentiment_data.get('surprise', 0),
            sentiment_data.get('disgust', 0),
            sentiment_data.get('overall_sentiment', 'neutral'),
            sentiment_data.get('confidence', 0)
        ))
    
    def check_user_trial_status(self, user_id):
        """Check if user's trial is still active"""
        query = """
        SELECT 
            DATEDIFF(NOW(), trial_start_date) as days_since_trial,
            is_premium,
            premium_expires_at
        FROM users 
        WHERE id = %s
        """
        result = self.execute_query(query, (user_id,))
        if result:
            user_data = result[0]
            days_since_trial = user_data['days_since_trial']
            is_premium = user_data['is_premium']
            
            # Check if trial is still active (14 days) or user is premium
            return days_since_trial <= 14 or is_premium
        return False
