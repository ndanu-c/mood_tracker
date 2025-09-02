#!/usr/bin/env python3
"""
Deployment Helper Script for Mood Journal Application
Prepares the application for production deployment.
"""

import os
import secrets
import string

def generate_secret_key(length=32):
    """Generate a secure random secret key"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def create_production_env():
    """Create a production-ready .env file"""
    print("🔧 Creating production environment configuration...")
    
    # Generate secure JWT secret
    jwt_secret = generate_secret_key(64)
    
    env_content = f"""# Production Environment Configuration
# Database Configuration (Update with your production database)
DB_HOST=your_production_db_host
DB_PORT=3306
DB_USER=your_db_user
DB_PASSWORD=your_secure_db_password
DB_NAME=mood_journal

# API Keys (Required for functionality)
HUGGINGFACE_API_KEY=your_huggingface_api_key_here

# JWT Configuration (Auto-generated secure key)
JWT_SECRET_KEY={jwt_secret}

# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False
"""
    
    with open('.env.production', 'w') as f:
        f.write(env_content)
    
    print("✅ Production .env.production file created")
    print("📝 Please update the database and API key values")

def update_procfile():
    """Update Procfile for production deployment"""
    procfile_content = """web: cd backend && gunicorn --bind 0.0.0.0:$PORT app:app
"""
    
    with open('Procfile', 'w') as f:
        f.write(procfile_content)
    
    print("✅ Procfile updated for production deployment")

def add_gunicorn_to_requirements():
    """Add gunicorn to requirements.txt for production"""
    with open('requirements.txt', 'r') as f:
        requirements = f.read()
    
    if 'gunicorn' not in requirements:
        with open('requirements.txt', 'a') as f:
            f.write('gunicorn==21.2.0\n')
        print("✅ Added gunicorn to requirements.txt")
    else:
        print("✅ Gunicorn already in requirements.txt")

def create_deployment_checklist():
    """Create a deployment checklist"""
    checklist = """# 🚀 Deployment Checklist

## Pre-Deployment
- [ ] Set up production database (MySQL)
- [ ] Get Hugging Face API key
- [ ] Configure environment variables
- [ ] Test application locally

## Database Setup
- [ ] Create production MySQL database
- [ ] Run: `python setup_database.py` (with production .env)
- [ ] Verify tables are created correctly

## Environment Variables
- [ ] Copy .env.production to .env (or set in hosting platform)
- [ ] Update DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
- [ ] Add your HUGGINGFACE_API_KEY
- [ ] Verify JWT_SECRET_KEY is secure

## Frontend Deployment
- [ ] Deploy frontend folder to static hosting (Netlify/Vercel)
- [ ] Update CORS settings in Flask app if needed
- [ ] Test frontend can connect to backend API

## Backend Deployment
- [ ] Deploy to Railway/Render/Heroku
- [ ] Set environment variables in platform
- [ ] Verify /api/health endpoint works
- [ ] Test authentication endpoints

## Final Testing
- [ ] Register a new user account
- [ ] Create a journal entry
- [ ] Verify sentiment analysis works
- [ ] Check mood visualization charts
- [ ] Test on mobile devices

## Security
- [ ] HTTPS enabled
- [ ] CORS properly configured
- [ ] Environment variables secured
- [ ] Database access restricted

## Monitoring
- [ ] Set up error logging
- [ ] Monitor API response times
- [ ] Track user registrations
- [ ] Monitor database performance
"""
    
    with open('DEPLOYMENT.md', 'w') as f:
        f.write(checklist)
    
    print("✅ Created DEPLOYMENT.md checklist")

def main():
    """Main deployment preparation function"""
    print("🌈 Mood Journal - Deployment Preparation")
    print("=" * 50)
    
    create_production_env()
    update_procfile()
    add_gunicorn_to_requirements()
    create_deployment_checklist()
    
    print("\n🎉 Deployment preparation completed!")
    print("\n📋 Next steps:")
    print("1. Review .env.production and update with your values")
    print("2. Follow the checklist in DEPLOYMENT.md")
    print("3. Test locally before deploying")
    print("4. Deploy backend and frontend separately")
    
    print("\n💡 Quick start:")
    print("   python setup_database.py  # Set up database")
    print("   cd backend && python app.py  # Test backend")
    print("   cd frontend && python -m http.server 8000  # Test frontend")

if __name__ == "__main__":
    main()
