from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
import bcrypt
import uuid
from datetime import datetime, timedelta
from .database import Database
from sentiment_analyzer import SentimentAnalyzer
from paystack_service import PaystackService
from config import Config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
cors = CORS(app)
jwt = JWTManager(app)

# Initialize services
db = Database()
sentiment_analyzer = SentimentAnalyzer()
paystack_service = PaystackService()

# Ensure database connection is established
try:
    db.connect()
    logging.info("Database connection established successfully")
except Exception as e:
    logging.error(f"Failed to establish database connection: {e}")
    logging.error("Please check your database settings in .env file")

@app.route('/api/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not all([username, email, password]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Check if user already exists
        existing_user = db.get_user_by_email(email)
        if existing_user:
            return jsonify({'error': 'User already exists'}), 409
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create user
        user_id = db.create_user(username, email, password_hash)
        
        # Create access token
        access_token = create_access_token(identity=user_id)
        
        return jsonify({
            'message': 'User registered successfully',
            'access_token': access_token,
            'user_id': user_id,
            'trial_days_remaining': 14
        }), 201
        
    except Exception as e:
        logging.error(f"Registration error: {e}")
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not all([email, password]):
            return jsonify({'error': 'Missing email or password'}), 400
        
        # Get user from database
        user = db.get_user_by_email(email)
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Check trial status
        trial_active = db.check_user_trial_status(user['id'])
        if not trial_active:
            return jsonify({'error': 'Trial expired. Please upgrade to premium.'}), 403
        
        # Create access token
        access_token = create_access_token(identity=user['id'])
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user_id': user['id'],
            'username': user['username']
        }), 200
        
    except Exception as e:
        logging.error(f"Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500

@app.route('/api/journal/entries', methods=['POST'])
@jwt_required()
def create_entry():
    """Create new journal entry with sentiment analysis"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        title = data.get('title', '')
        content = data.get('content', '')
        
        if not content:
            return jsonify({'error': 'Content is required'}), 400
        
        # Check trial status
        trial_active = db.check_user_trial_status(user_id)
        if not trial_active:
            return jsonify({'error': 'Trial expired. Please upgrade to premium.'}), 403
        
        # Create journal entry
        entry_id = db.create_journal_entry(user_id, title, content)
        
        # Analyze sentiment
        sentiment_data = sentiment_analyzer.analyze_emotion(content)
        
        # Save sentiment analysis
        db.save_mood_analysis(entry_id, sentiment_data)
        
        return jsonify({
            'message': 'Journal entry created successfully',
            'entry_id': entry_id,
            'sentiment': sentiment_data
        }), 201
        
    except Exception as e:
        logging.error(f"Create entry error: {e}")
        return jsonify({'error': 'Failed to create entry'}), 500

@app.route('/api/journal/entries', methods=['GET'])
@jwt_required()
def get_entries():
    """Get user's journal entries with sentiment data"""
    try:
        user_id = get_jwt_identity()
        
        # Check trial status
        trial_active = db.check_user_trial_status(user_id)
        if not trial_active:
            return jsonify({'error': 'Trial expired. Please upgrade to premium.'}), 403
        
        # Get entries
        entries = db.get_user_entries(user_id)
        
        return jsonify({
            'entries': entries,
            'total': len(entries)
        }), 200
        
    except Exception as e:
        logging.error(f"Get entries error: {e}")
        return jsonify({'error': 'Failed to retrieve entries'}), 500

@app.route('/api/mood/summary', methods=['GET'])
@jwt_required()
def get_mood_summary():
    """Get mood analysis summary for user"""
    try:
        user_id = get_jwt_identity()
        
        # Check trial status
        trial_active = db.check_user_trial_status(user_id)
        if not trial_active:
            return jsonify({'error': 'Trial expired. Please upgrade to premium.'}), 403
        
        # Get entries with sentiment data
        entries = db.get_user_entries(user_id, limit=30)  # Last 30 entries
        
        # Generate mood summary
        mood_summary = sentiment_analyzer.get_mood_summary(entries)
        
        return jsonify({
            'mood_summary': mood_summary,
            'recent_entries': len(entries)
        }), 200
        
    except Exception as e:
        logging.error(f"Mood summary error: {e}")
        return jsonify({'error': 'Failed to generate mood summary'}), 500

@app.route('/api/user/status', methods=['GET'])
@jwt_required()
def get_user_status():
    """Get user trial and subscription status"""
    try:
        user_id = get_jwt_identity()
        user = db.get_user_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        trial_active = db.check_user_trial_status(user_id)
        
        # Calculate days remaining in trial
        query = "SELECT DATEDIFF(NOW(), trial_start_date) as days_since_trial FROM users WHERE id = %s"
        result = db.execute_query(query, (user_id,))
        days_since_trial = result[0]['days_since_trial'] if result else 14
        days_remaining = max(0, 14 - days_since_trial)
        
        return jsonify({
            'user_id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'trial_active': trial_active,
            'days_remaining': days_remaining,
            'is_premium': user['is_premium']
        }), 200
        
    except Exception as e:
        logging.error(f"User status error: {e}")
        return jsonify({'error': 'Failed to get user status'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'Mood Journal API is running'}), 200

# Payment Endpoints
@app.route('/api/payment/initialize', methods=['POST'])
@jwt_required()
def initialize_payment():
    """Initialize a Paystack payment"""
    try:
        user_id = get_jwt_identity()
        user = db.get_user_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        data = request.get_json()
        plan_type = data.get('plan_type', 'monthly')
        
        # Get amount based on plan type
        if plan_type == 'yearly':
            amount = app.config.get('PREMIUM_PRICE_YEARLY', 2999900)  # ₦29,999.00
        else:
            amount = app.config.get('PREMIUM_PRICE_MONTHLY', 299900)  # ₦2,999.00
            
        # Generate a unique reference
        reference = f"moodjournal_{uuid.uuid4().hex}"
        
        # Initialize transaction with Paystack
        response = paystack_service.initialize_transaction(
            email=user['email'],
            amount=amount,
            reference=reference,
            callback_url=data.get('callback_url'),
            metadata={
                'user_id': user_id,
                'plan_type': plan_type
            }
        )
        
        # Save payment reference to database
        db.execute_query(
            """
            INSERT INTO payments (user_id, reference, amount, status, plan_type)
            VALUES (%s, %s, %s, 'pending', %s)
            """,
            (user_id, reference, amount, plan_type)
        )
        
        return jsonify({
            'status': True,
            'message': 'Payment initialized',
            'data': {
                'authorization_url': response['data']['authorization_url'],
                'access_code': response['data']['access_code'],
                'reference': reference
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Payment initialization error: {e}")
        return jsonify({'status': False, 'message': 'Failed to initialize payment'}), 500

@app.route('/api/payment/verify', methods=['POST'])
@jwt_required()
def verify_payment():
    """Verify a Paystack payment"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        reference = data.get('reference')
        
        if not reference:
            return jsonify({'error': 'Reference is required'}), 400
            
        # Verify payment with Paystack
        response = paystack_service.verify_transaction(reference)
        
        if response['data']['status'] == 'success':
            # Update payment status in database
            db.execute_query(
                """
                UPDATE payments 
                SET status = 'success', 
                    verified_at = NOW(),
                    amount = %s,
                    paystack_reference = %s
                WHERE reference = %s AND user_id = %s
                """,
                (
                    response['data']['amount'],
                    response['data']['reference'],
                    reference,
                    user_id
                )
            )
            
            # Get payment details
            payment = db.execute_query(
                "SELECT * FROM payments WHERE reference = %s AND user_id = %s",
                (reference, user_id)
            )
            
            if payment:
                payment = payment[0]
                plan_type = payment['plan_type']
                
                # Calculate subscription expiry
                now = datetime.utcnow()
                if plan_type == 'yearly':
                    expires_at = now + timedelta(days=365)  # 1 year
                else:
                    expires_at = now + timedelta(days=30)  # 1 month
                
                # Update user to premium
                db.execute_query(
                    """
                    UPDATE users 
                    SET is_premium = TRUE,
                        premium_since = %s,
                        premium_until = %s
                    WHERE id = %s
                    """,
                    (now, expires_at, user_id)
                )
                
                return jsonify({
                    'status': True,
                    'message': 'Payment verified successfully',
                    'is_premium': True,
                    'premium_until': expires_at.isoformat()
                }), 200
            
        return jsonify({
            'status': False,
            'message': 'Payment verification failed',
            'data': response['data']
        }), 400
        
    except Exception as e:
        logging.error(f"Payment verification error: {e}")
        return jsonify({'status': False, 'message': 'Payment verification failed'}), 500

@app.route('/api/payment/config', methods=['GET'])
def get_payment_config():
    """Get payment configuration for frontend"""
    try:
        return jsonify({
            'public_key': app.config.get('PAYSTACK_PUBLIC_KEY'),
            'monthly_price': app.config.get('PREMIUM_PRICE_MONTHLY', 299900),
            'yearly_price': app.config.get('PREMIUM_PRICE_YEARLY', 2999900),
            'currency': 'NGN'
        }), 200
    except Exception as e:
        logging.error(f"Payment config error: {e}")
        return jsonify({'error': 'Failed to get payment config'}), 500

@app.route('/api/subscription/status', methods=['GET'])
@jwt_required()
def get_subscription_status():
    """Get user's subscription status"""
    try:
        user_id = get_jwt_identity()
        user = db.get_user_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        # Check if user is on trial
        trial_active = db.check_user_trial_status(user_id)
        trial_expired = False
        days_remaining = 0
        
        if trial_active:
            # Calculate days remaining in trial
            query = """
                SELECT 
                    DATEDIFF(
                        DATE_ADD(trial_start_date, INTERVAL 14 DAY), 
                        NOW()
                    ) as days_remaining
                FROM users 
                WHERE id = %s
            """
            result = db.execute_query(query, (user_id,))
            if result and 'days_remaining' in result[0]:
                days_remaining = max(0, result[0]['days_remaining'])
                trial_expired = days_remaining <= 0
        
        return jsonify({
            'user_id': user['id'],
            'is_premium': user['is_premium'],
            'premium_until': user.get('premium_until'),
            'on_trial': trial_active,
            'trial_expired': trial_expired,
            'days_remaining': days_remaining,
            'created_at': user.get('created_at')
        }), 200
        
    except Exception as e:
        logging.error(f"Subscription status error: {e}")
        return jsonify({'error': 'Failed to get subscription status'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
