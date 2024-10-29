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
from werkzeug.security import check_password_hash, generate_password_hash

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set Stripe API key
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('index'))
        
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
            
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))
            
        user = User()
        user.username = username
        user.email = email
        user.set_password(password)
        user.subscription_type = 'free'
        user.monthly_ai_analysis_count = 0
        user.last_analysis_reset = datetime.utcnow()
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('index'))

@app.route('/dream/new', methods=['GET'])
@login_required
def dream_log():
    return render_template('dream_log.html')

@app.route('/dream/patterns')
@login_required
def dream_patterns():
    dreams = current_user.dreams.order_by(Dream.date.desc()).all()
    patterns = analyze_dream_patterns(dreams) if dreams else None
    return render_template('dream_patterns.html', dreams=dreams, patterns=patterns)

@app.route('/dream/groups')
@login_required
def dream_groups():
    groups = DreamGroup.query.all()
    return render_template('dream_groups.html', groups=groups)

@app.route('/community')
@login_required
def community():
    public_dreams = Dream.query.filter_by(is_public=True).order_by(Dream.date.desc()).all()
    return render_template('community.html', dreams=public_dreams)

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
            success_url=request.host_url + 'subscription?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.host_url + 'subscription',
            metadata={
                'user_email': current_user.email,
                'user_id': str(current_user.id)
            }
        )
        
        return jsonify({'id': checkout_session.id})
        
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        return jsonify({'error': str(e)}), 400

@app.route('/subscription/session-status/<session_id>')
@login_required
def check_session_status(session_id):
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        return jsonify({
            'status': session.payment_status
        })
    except Exception as e:
        logger.error(f"Error checking session status: {str(e)}")
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

# Context processor for template functions
@app.context_processor
def utility_processor():
    def validate_google_ads_credentials():
        return True  # Simplified for now
    def hash_email(email):
        return hashlib.md5(email.lower().encode()).hexdigest()
    def should_show_premium_ads():
        return show_premium_ads(current_user) if current_user.is_authenticated else False
    return dict(
        validate_google_ads_credentials=validate_google_ads_credentials,
        hash_email=hash_email,
        should_show_premium_ads=should_show_premium_ads
    )
