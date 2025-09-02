import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

class Config:
    # Database Configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3307))
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'dupples1234')
    DB_NAME = os.getenv('DB_NAME', 'mood_journal')
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'fallback-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=14)  # 2-week trial
    
    # API Keys
    HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY')
    
    # Paystack Configuration
    PAYSTACK_SECRET_KEY = os.getenv('PAYSTACK_SECRET_KEY')
    PAYSTACK_PUBLIC_KEY = os.getenv('PAYSTACK_PUBLIC_KEY')
    PAYSTACK_BASE_URL = 'https://api.paystack.co'
    
    # Flask Configuration
    SECRET_KEY = JWT_SECRET_KEY
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
