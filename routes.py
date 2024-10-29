from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import User, Dream, Comment, DreamGroup, GroupMembership, ForumPost, ForumReply
from datetime import datetime, timedelta
import logging
import os
import hashlib
from google_ads_helper import track_premium_conversion, show_premium_ads, validate_google_ads_credentials
from ai_helper import analyze_dream, analyze_dream_patterns
from stripe_webhook_handler import handle_stripe_webhook
import stripe

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set Stripe API key
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

@app.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """Create Stripe checkout session for premium subscription."""
    try:
        checkout_session = stripe.checkout.Session.create(
            customer_email=current_user.email,
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'DreamLoop Premium',
                        'description': 'Unlimited AI dream analysis and advanced features',
                    },
                    'unit_amount': 999,  # $9.99 in cents
                    'recurring': {
                        'interval': 'month',
                    },
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.host_url + url_for('subscription') + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.host_url + url_for('subscription'),
            metadata={
                'user_email': current_user.email,
                'user_id': str(current_user.id)
            }
        )
        
        return jsonify({'id': checkout_session.id})
        
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        return jsonify({'error': str(e)}), 400

@app.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events"""
    if request.content_length > 65535:
        logger.warning("Request payload too large")
        return "Request payload too large", 400
        
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    if not sig_header:
        logger.warning("No Stripe signature header")
        return "No Stripe signature header", 400
        
    success, message = handle_stripe_webhook(payload, sig_header)
    
    if success:
        return message, 200
    else:
        return message, 400

@app.route('/subscription/cancel', methods=['POST'])
@login_required
def subscription_cancel():
    """Cancel user's premium subscription."""
    try:
        # Get the customer's subscription
        subscriptions = stripe.Subscription.list(
            customer=current_user.stripe_customer_id,
            limit=1,
            status='active'
        )
        
        if not subscriptions.data:
            flash('No active subscription found.')
            return redirect(url_for('subscription'))
            
        subscription = subscriptions.data[0]
        stripe.Subscription.modify(
            subscription.id,
            cancel_at_period_end=True
        )
        
        flash('Your subscription will be canceled at the end of the billing period.')
        return redirect(url_for('subscription'))
        
    except Exception as e:
        logger.error(f"Error canceling subscription: {str(e)}")
        flash('An error occurred while canceling your subscription. Please try again.')
        return redirect(url_for('subscription'))

@app.route('/subscription')
@login_required
def subscription():
    """View and manage subscription."""
    stripe_publishable_key = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    if not stripe_publishable_key:
        flash('Payment system is currently unavailable. Please try again later.')
        return redirect(url_for('index'))
    return render_template('subscription.html', stripe_publishable_key=stripe_publishable_key)
