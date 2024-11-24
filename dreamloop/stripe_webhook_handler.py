import stripe
import os
from datetime import datetime
import logging
from .models import Users
from .extensions import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handle_stripe_webhook(payload, sig_header):
    """Handle incoming Stripe webhooks."""
    try:
        # Set your Stripe API key
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        endpoint_secret = os.getenv('STRIPE_WEBHOOK_SECRET')

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError as e:
            logger.error(f"Invalid payload: {str(e)}")
            return "Invalid payload", 400
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {str(e)}")
            return "Invalid signature", 400

        # Handle the event
        if event.type == 'checkout.session.completed':
            session = event.data.object
            handle_successful_payment(session)
        elif event.type == 'customer.subscription.deleted':
            subscription = event.data.object
            handle_subscription_cancelled(subscription)
        elif event.type == 'customer.subscription.updated':
            subscription = event.data.object
            handle_subscription_updated(subscription)
        else:
            logger.info(f'Unhandled event type {event.type}')

        return "Success", 200

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return f"Error processing webhook: {str(e)}", 500

def handle_successful_payment(session):
    """Handle successful payment completion."""
    try:
        # Get customer email from session
        customer_email = session.customer_details.email
        
        # Find user by email
        user = Users.query.filter_by(email=customer_email).first()
        
        if not user:
            logger.error(f"User not found for email: {customer_email}")
            return
        
        # Update user subscription status
        user.subscription_type = 'premium'
        user.stripe_customer_id = session.customer
        user.subscription_start_date = datetime.utcnow()
        
        db.session.commit()
        logger.info(f"Successfully updated subscription for user {user.id}")

    except Exception as e:
        logger.error(f"Error handling successful payment: {str(e)}")
        db.session.rollback()

def handle_subscription_cancelled(subscription):
    """Handle subscription cancellation."""
    try:
        # Find user by Stripe customer ID
        user = Users.query.filter_by(stripe_customer_id=subscription.customer).first()
        
        if not user:
            logger.error(f"User not found for Stripe customer: {subscription.customer}")
            return
        
        # Update user subscription status
        user.subscription_type = 'free'
        user.subscription_end_date = datetime.utcnow()
        
        db.session.commit()
        logger.info(f"Successfully cancelled subscription for user {user.id}")

    except Exception as e:
        logger.error(f"Error handling subscription cancellation: {str(e)}")
        db.session.rollback()

def handle_subscription_updated(subscription):
    """Handle subscription updates."""
    try:
        # Find user by Stripe customer ID
        user = Users.query.filter_by(stripe_customer_id=subscription.customer).first()
        
        if not user:
            logger.error(f"User not found for Stripe customer: {subscription.customer}")
            return
        
        # Update subscription details
        if subscription.status == 'active':
            user.subscription_type = 'premium'
        else:
            user.subscription_type = 'free'
        
        db.session.commit()
        logger.info(f"Successfully updated subscription status for user {user.id}")

    except Exception as e:
        logger.error(f"Error handling subscription update: {str(e)}")
        db.session.rollback()
