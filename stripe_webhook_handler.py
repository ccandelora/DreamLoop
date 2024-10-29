import os
import stripe
from datetime import datetime, timedelta
from app import db
from models import User
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Set Stripe API key
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')

def handle_subscription_created(event):
    """Handle subscription.created event"""
    subscription = event.data.object
    customer_email = subscription.customer_email or subscription.metadata.get('user_email')
    
    if not customer_email:
        logger.error(f"No customer email found for subscription {subscription.id}")
        return
        
    user = User.query.filter_by(email=customer_email).first()
    if not user:
        logger.error(f"User not found for subscription {subscription.id}")
        return
        
    try:
        user.subscription_type = 'premium'
        user.subscription_end_date = datetime.fromtimestamp(subscription.current_period_end)
        db.session.commit()
        logger.info(f"Successfully upgraded user {user.id} to premium")
    except Exception as e:
        logger.error(f"Error processing subscription.created: {str(e)}")
        db.session.rollback()

def handle_subscription_deleted(event):
    """Handle subscription.deleted event"""
    subscription = event.data.object
    customer_email = subscription.customer_email or subscription.metadata.get('user_email')
    
    if not customer_email:
        logger.error(f"No customer email found for subscription {subscription.id}")
        return
        
    user = User.query.filter_by(email=customer_email).first()
    
    if not user:
        logger.error(f"User not found for subscription {subscription.id}")
        return
        
    try:
        user.subscription_type = 'free'
        user.subscription_end_date = None
        db.session.commit()
        logger.info(f"Successfully processed subscription.deleted for user {user.id}")
    except Exception as e:
        logger.error(f"Error processing subscription.deleted: {str(e)}")
        db.session.rollback()

def handle_subscription_updated(event):
    """Handle subscription.updated event"""
    subscription = event.data.object
    customer_email = subscription.customer_email or subscription.metadata.get('user_email')
    
    if not customer_email:
        logger.error(f"No customer email found for subscription {subscription.id}")
        return
        
    user = User.query.filter_by(email=customer_email).first()
    
    if not user:
        logger.error(f"User not found for subscription {subscription.id}")
        return
        
    try:
        # Update subscription end date
        user.subscription_end_date = datetime.fromtimestamp(subscription.current_period_end)
        
        # Handle status changes
        if subscription.status == 'active':
            user.subscription_type = 'premium'
        elif subscription.status in ['canceled', 'unpaid', 'past_due']:
            user.subscription_type = 'free'
            user.subscription_end_date = None
            
        db.session.commit()
        logger.info(f"Successfully processed subscription.updated for user {user.id}")
    except Exception as e:
        logger.error(f"Error processing subscription.updated: {str(e)}")
        db.session.rollback()

def handle_payment_failed(event):
    """Handle payment_failed event"""
    invoice = event.data.object
    customer_email = invoice.customer_email or invoice.metadata.get('user_email')
    
    if not customer_email:
        logger.error(f"No customer email found for invoice {invoice.id}")
        return
        
    user = User.query.filter_by(email=customer_email).first()
    
    if not user:
        logger.error(f"User not found for invoice {invoice.id}")
        return
        
    try:
        # Add a grace period before downgrading
        if user.subscription_end_date and user.subscription_end_date < datetime.utcnow():
            user.subscription_type = 'free'
            user.subscription_end_date = None
            db.session.commit()
            logger.info(f"Downgraded user {user.id} to free plan due to payment failure")
    except Exception as e:
        logger.error(f"Error processing payment_failed: {str(e)}")
        db.session.rollback()

EVENT_HANDLERS = {
    'customer.subscription.created': handle_subscription_created,
    'customer.subscription.updated': handle_subscription_updated,
    'customer.subscription.deleted': handle_subscription_deleted,
    'invoice.payment_failed': handle_payment_failed,
}

def handle_stripe_webhook(payload, sig_header):
    """Main webhook handler"""
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        logger.error("Invalid payload")
        return False, "Invalid payload"
    except stripe.error.SignatureVerificationError as e:
        logger.error("Invalid signature")
        return False, "Invalid signature"
        
    try:
        if event.type in EVENT_HANDLERS:
            EVENT_HANDLERS[event.type](event)
            return True, "Webhook handled successfully"
        else:
            logger.info(f"Unhandled event type {event.type}")
            return True, "Unhandled event type"
    except Exception as e:
        logger.error(f"Error handling webhook: {str(e)}")
        return False, str(e)
