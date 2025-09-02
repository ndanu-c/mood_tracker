import pymysql
from pymysql import Error as PyMySQLError
from pymysql.cursors import DictCursor
from .config import Config
import logging
import time
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handle_db_errors(func):
    """Decorator to handle database connection errors"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                # Ensure connection is active
                if not self.connection or not self.connection.open:
                    self.connect()
                
                # Execute the function
                return func(self, *args, **kwargs)
                
            except (PyMySQLError, ConnectionError) as e:
                logger.error(f"Database error (attempt {attempt + 1}/{max_retries}): {str(e)}")
                self.connection = None  # Force reconnection on next attempt
                
                if attempt == max_retries - 1:  # Last attempt
                    logger.error("Max retries reached. Could not connect to database.")
                    raise
                    
                time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
    return wrapper

class Database:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.config = Config()
        self.connection = None
        self._last_ping = 0
        self._initialized = True
        self.connect()
    
    def connect(self):
        """Establish database connection with retry logic"""
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                if self.connection and self.connection.open:
                    self.connection.close()
                
                logger.info(f"Connecting to database at {self.config.DB_HOST}:{self.config.DB_PORT}")
                
                self.connection = pymysql.connect(
                    host=self.config.DB_HOST,
                    port=self.config.DB_PORT,
                    user=self.config.DB_USER,
                    password=self.config.DB_PASSWORD,
                    database=self.config.DB_NAME,
                    charset='utf8mb4',
                    cursorclass=DictCursor,
                    autocommit=True,
                    connect_timeout=10,
                    read_timeout=10,
                    write_timeout=10,
                    client_flag=pymysql.constants.CLIENT.MULTI_STATEMENTS
                )
                
                logger.info("Successfully connected to the database")
                return self.connection
                
            except PyMySQLError as e:
                logger.error(f"Connection attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    logger.error("Max connection attempts reached. Could not connect to database.")
                    raise
                    
                time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
    
    def ensure_connection(self):
        """Ensure database connection is active"""
        try:
            if not self.connection or not self.connection.open:
                return self.connect()
                
            # Ping every 5 minutes to keep connection alive
            current_time = time.time()
            if current_time - self._last_ping > 300:  # 5 minutes
                self.connection.ping(reconnect=True)
                self._last_ping = current_time
                
            return self.connection
            
        except PyMySQLError as e:
            logger.error(f"Database ping failed: {str(e)}")
            return self.connect()
    
    @handle_db_errors
    def execute_query(self, query, params=None, fetch_one=False):
        """Execute a query with parameters"""
        connection = self.ensure_connection()
        with connection.cursor() as cursor:
            cursor.execute(query, params or ())
            if query.strip().upper().startswith('SELECT'):
                return cursor.fetchone() if fetch_one else cursor.fetchall()
            return cursor.lastrowid
    
    @handle_db_errors
    def execute_many(self, query, params_list):
        """Execute multiple parameterized queries"""
        connection = self.ensure_connection()
        with connection.cursor() as cursor:
            return cursor.executemany(query, params_list)
    
    def close(self):
        """Close the database connection"""
        if self.connection and self.connection.open:
            self.connection.close()
            self.connection = None
            logger.info("Database connection closed")
    
    def __del__(self):
        self.close()

    # Transaction support
    @handle_db_errors
    def begin_transaction(self):
        """Begin a transaction"""
        self.connection.begin()
        
    @handle_db_errors
    def commit(self):
        """Commit the current transaction"""
        self.connection.commit()
        
    @handle_db_errors
    def rollback(self):
        """Roll back the current transaction"""
        self.connection.rollback()
    
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
        return self.execute_query(query, (username, email, password_hash))
    
    def create_journal_entry(self, user_id, title, content):
        """Create new journal entry"""
        query = """
        INSERT INTO journal_entries (user_id, title, content) 
        VALUES (%s, %s, %s)
        """
        return self.execute_query(query, (user_id, title, content))
    
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
        return self.execute_query(query, (
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
