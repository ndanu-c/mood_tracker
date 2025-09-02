from paystackapi.paystack import Paystack
from paystackapi.transaction import Transaction
from paystackapi.customer import Customer
from paystackapi.plan import Plan
from paystackapi.subscription import Subscription
import logging
from .config import Config
from datetime import datetime, timedelta

class PaystackService:
    def __init__(self):
        self.config = Config()
        # Initialize Paystack with test secret key
        Paystack(secret_key=self.config.PAYSTACK_SECRET_KEY)
        
    def initialize_transaction(self, email, amount, reference, callback_url=None, metadata=None):
        """Initialize a Paystack transaction"""
        try:
            response = Transaction.initialize(
                email=email,
                amount=amount,  # Amount in kobo
                reference=reference,
                callback_url=callback_url,
                metadata=metadata or {}
            )
            return response
        except Exception as e:
            logging.error(f"Error initializing transaction: {e}")
            raise e
            
    def verify_transaction(self, reference):
        """Verify a Paystack transaction"""
        try:
            response = Transaction.verify(reference=reference)
            return response
        except Exception as e:
            logging.error(f"Error verifying transaction: {e}")
            raise e
            
    def create_customer(self, email, first_name=None, last_name=None, phone=None):
        """Create a Paystack customer"""
        try:
            response = Customer.create(
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone=phone
            )
            return response
        except Exception as e:
            logging.error(f"Error creating customer: {e}")
            raise e
            
    def get_customer(self, customer_id):
        """Get customer details from Paystack"""
        try:
            response = Customer.get(customer_id=customer_id)
            return response
        except Exception as e:
            logging.error(f"Error getting customer: {e}")
            raise e
            
    def create_plan(self, name, amount, interval='monthly'):
        """Create a subscription plan"""
        try:
            response = Plan.create(
                name=name,
                amount=amount,  # Amount in kobo
                interval=interval,
                currency='NGN'
            )
            return response
        except Exception as e:
            logging.error(f"Error creating plan: {e}")
            raise e
            
    def create_subscription(self, customer, plan, authorization):
        """Create a subscription"""
        try:
            response = Subscription.create(
                customer=customer,
                plan=plan,
                authorization=authorization
            )
            return response
        except Exception as e:
            logging.error(f"Error creating subscription: {e}")
            raise e
            
    def disable_subscription(self, code, token):
        """Disable a subscription"""
        try:
            response = Subscription.disable(
                code=code,
                token=token
            )
            return response
        except Exception as e:
            logging.error(f"Error disabling subscription: {e}")
            raise e
            
    def get_subscription(self, subscription_id):
        """Get subscription details"""
        try:
            response = Subscription.get(subscription_id=subscription_id)
            return response
        except Exception as e:
            logging.error(f"Error getting subscription: {e}")
            raise e
            
    def format_amount_to_naira(self, amount_in_kobo):
        """Convert kobo to naira for display"""
        return amount_in_kobo / 100
        
    def format_amount_to_kobo(self, amount_in_naira):
        """Convert naira to kobo for API calls"""
        return int(amount_in_naira * 100)
