# 🌈 Mood Journal - AI-Powered Emotion Tracker

An intelligent journaling application that helps users track their emotions, visualize mood patterns, and promote mental well-being through AI-powered sentiment analysis, with integrated payment processing via Paystack.

## 🌍 SDG Alignment
**SDG 3 – Good Health and Well-being**

Mental health matters. This project empowers users to understand their emotional patterns by combining simple journaling with AI-powered sentiment analysis and premium subscription features.

## ✨ Features

- **🔐 User Authentication**: Secure registration and login with JWT tokens
- **📝 Smart Journaling**: Write journal entries with AI-powered emotion analysis
- **📊 Mood Visualization**: Beautiful charts showing emotional patterns over time
- **💳 Premium Subscriptions**: Monthly and yearly subscription options with Paystack integration
- **🧠 AI Insights**: Personalized insights based on emotional data using Hugging Face's transformer models
- **📱 Responsive Design**: Works perfectly on desktop, tablet, and mobile
- **⏰ Freemium Model**: 14-day free trial with premium upgrade options
- **🔒 Secure**: Environment variables for API keys and secure data handling

## 🛠️ Tech Stack

### Frontend
- **HTML5, CSS3, Vanilla JavaScript**
- **Chart.js** for data visualization
- **Font Awesome** for icons
- **Google Fonts (Inter)** for typography

### Backend
- **Python Flask** - REST API server
- **MySQL** - Database for user data and journal entries
- **JWT** - Authentication and session management
- **bcrypt** - Password hashing
- **Paystack API** - Payment processing and subscription management

### AI Integration
- **Hugging Face Transformers** - Emotion detection and sentiment analysis
- **j-hartmann/emotion-english-distilroberta-base** model
- **PyTorch** - Deep learning framework

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- MySQL Server
- Node.js (optional, for development)
- Paystack account (for payment processing)
- Hugging Face API key (for sentiment analysis)

### 1. Clone the Repository
```bash
git clone <repository-url>
cd sdg-project
```

### 2. Set Up Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up MySQL Database
1. Ensure MySQL server is running
2. Create a new database:
   ```sql
   CREATE DATABASE mood_journal;
   ```
3. Update the database configuration in `.env` file

### 5. Configure Environment Variables
Create a `.env` file in the project root with the following variables:
```
# Database Configuration
MYSQL_HOST=localhost
MYSQL_USER=your_username
MYSQL_PASSWORD=your_password
MYSQL_DB=mood_journal

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-here

# Hugging Face API
HUGGINGFACE_API_KEY=your-huggingface-api-key

# Paystack Configuration
PAYSTACK_SECRET_KEY=your-paystack-secret-key
PAYSTACK_PUBLIC_KEY=your-paystack-public-key
```

### 6. Initialize the Database
```bash
python setup_database.py
```

### 7. Start the Application
```bash
# Start the Flask backend
cd backend
python app.py

# In a new terminal, start the frontend
# Open frontend/index.html in your web browser
```

## 🌐 Live Demo

Experience Mood Journal with our live demo:  
[![Live Demo](https://img.shields.io/badge/🚀-Live_Demo-6e40c9?style=for-the-badge)](https://your-demo-url.herokuapp.com)

### 🚀 Deployment Options

#### 1. One-Click Deploy (Recommended)
[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/yourusername/sdg-project)
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https://github.com/yourusername/sdg-project)

#### 2. Manual Deployment
1. **Backend Setup**:
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Set environment variables
   export FLASK_APP=app.py
   export FLASK_ENV=production
   
   # Run with Gunicorn
   gunicorn --bind 0.0.0.0:$PORT app:app
   ```

2. **Frontend Setup**:
   - Host the `frontend` folder on Netlify, Vercel, or GitHub Pages
   - Set `API_BASE_URL` in `frontend/app.js` to your backend URL

### 📱 Demo Credentials
- **Email**: demo@example.com
- **Password**: Demo@123

> ℹ️ Note: The demo resets every hour. For full access, please deploy your own instance.

## 💳 Subscription Plans
- **Free Trial**: 14 days with basic features
- **Monthly Plan**: ₦2,999/month
- **Yearly Plan**: ₦29,999/year (Save 17%)

## 📝 Database Schema
- **users**: User accounts and subscription details
- **journal_entries**: User journal entries
- **mood_analysis**: AI analysis of journal entries
- **payments**: Payment transactions
- **subscriptions**: User subscription details

## 🔧 Troubleshooting
- Ensure all environment variables are set correctly
- Verify MySQL server is running and accessible
- Check logs in the Flask console for errors
- Ensure required ports are not in use (default: 5000 for Flask)

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments
- Hugging Face for the emotion analysis model
- Paystack for payment processing
- Chart.js for data visualization
