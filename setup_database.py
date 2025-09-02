#!/usr/bin/env python3
"""
Database Setup Script for Mood Journal Application
This script creates the database and tables automatically.
"""

import pymysql
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_database_connection():
    """Create connection to MySQL server (without specifying database)"""
    try:
        connection = pymysql.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 3307)),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', 'dupples1234'),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as e:
        print(f"❌ Error connecting to MySQL: {e}")
        return None

def setup_database():
    """Set up the mood journal database and tables"""
    connection = create_database_connection()
    if not connection:
        return False
    
    try:
        with connection.cursor() as cursor:
            print("🔧 Setting up Mood Journal database...")
            
            # Create database
            cursor.execute("CREATE DATABASE IF NOT EXISTS mood_journal")
            cursor.execute("USE mood_journal")
            print("✅ Database 'mood_journal' created/verified")
            
            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    trial_start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_premium BOOLEAN DEFAULT FALSE,
                    premium_expires_at TIMESTAMP NULL
                )
            """)
            print("✅ Users table created/verified")
            
            # Create journal_entries table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS journal_entries (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    title VARCHAR(200) NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            print("✅ Journal entries table created/verified")
            
            # Create mood_analysis table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mood_analysis (
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
                )
            """)
            print("✅ Mood analysis table created/verified")
            
            # Create indexes with proper error handling
            indexes = [
                ("idx_users_email", "CREATE INDEX idx_users_email ON users(email)"),
                ("idx_users_username", "CREATE INDEX idx_users_username ON users(username)"),
                ("idx_journal_user_id", "CREATE INDEX idx_journal_user_id ON journal_entries(user_id)"),
                ("idx_journal_created_at", "CREATE INDEX idx_journal_created_at ON journal_entries(created_at)"),
                ("idx_mood_entry_id", "CREATE INDEX idx_mood_entry_id ON mood_analysis(entry_id)")
            ]
            
            for index_name, index_sql in indexes:
                try:
                    cursor.execute(index_sql)
                except pymysql.Error as e:
                    if e.args[0] == 1061:  # Duplicate key name error
                        print(f"✅ Index '{index_name}' already exists")
                    else:
                        print(f"⚠️  Warning creating index '{index_name}': {e}")
            print("✅ Database indexes created/verified")
            
            connection.commit()
            print("\n🎉 Database setup completed successfully!")
            print("📊 Tables created: users, journal_entries, mood_analysis")
            print("🔍 Indexes created for optimal performance")
            
        return True
        
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        return False
    finally:
        connection.close()

def verify_setup():
    """Verify that the database setup is correct"""
    connection = create_database_connection()
    if not connection:
        return False
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("USE mood_journal")
            
            # Check tables exist
            cursor.execute("SHOW TABLES")
            tables = [row[f'Tables_in_mood_journal'] for row in cursor.fetchall()]
            
            expected_tables = ['users', 'journal_entries', 'mood_analysis']
            missing_tables = [table for table in expected_tables if table not in tables]
            
            if missing_tables:
                print(f"❌ Missing tables: {missing_tables}")
                return False
            
            print("✅ All required tables are present")
            
            # Check table structures
            for table in expected_tables:
                cursor.execute(f"DESCRIBE {table}")
                columns = cursor.fetchall()
                print(f"📋 Table '{table}': {len(columns)} columns")
            
            return True
            
    except Exception as e:
        print(f"❌ Error verifying setup: {e}")
        return False
    finally:
        connection.close()

if __name__ == "__main__":
    print("🌈 Mood Journal Database Setup")
    print("=" * 40)
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("⚠️  Warning: .env file not found!")
        print("📝 Please copy .env.example to .env and configure your settings")
        print("💡 Using default values from .env.example")
    
    # Setup database
    if setup_database():
        print("\n🔍 Verifying setup...")
        if verify_setup():
            print("\n🎯 Setup verification passed!")
            print("🚀 Your Mood Journal database is ready to use!")
        else:
            print("\n❌ Setup verification failed!")
    else:
        print("\n❌ Database setup failed!")
        print("💡 Please check your database connection settings in .env")
