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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')


@app.route('/')
def index():
    """Landing page route."""
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login route."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('index'))

        flash('Invalid username or password')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route."""
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
    """User logout route."""
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('index'))


@app.route('/dream/new', methods=['GET', 'POST'])
@login_required
def dream_new():
    """Dream logging route."""
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        mood = request.form.get('mood')
        tags = request.form.get('tags')
        is_public = request.form.get('is_public') == 'true'

        dream = Dream()
        dream.user_id = current_user.id
        dream.title = title
        dream.content = content
        dream.mood = mood
        dream.tags = tags
        dream.is_public = is_public
        dream.date = datetime.utcnow()

        if current_user.subscription_type == 'premium' or current_user.monthly_ai_analysis_count < 3:
            dream.ai_analysis = analyze_dream(content)
            if current_user.subscription_type == 'free':
                current_user.monthly_ai_analysis_count += 1

        db.session.add(dream)
        db.session.commit()
        flash('Dream logged successfully!')
        return redirect(url_for('dream_view', dream_id=dream.id))

    return render_template('dream_new.html')


@app.route('/dream/<int:dream_id>')
@login_required
def dream_view(dream_id):
    """View individual dream."""
    dream = Dream.query.get_or_404(dream_id)
    if dream.user_id != current_user.id and not dream.is_public:
        flash('You do not have permission to view this dream.')
        return redirect(url_for('index'))
    return render_template('dream_view.html', dream=dream)


@app.route('/dream/patterns')
@login_required
def dream_patterns():
    """Dream patterns analysis route."""
    user_dreams = current_user.dreams.all()
    patterns = analyze_dream_patterns(user_dreams) if user_dreams else {}
    return render_template('dream_patterns.html',
                           dreams=user_dreams,
                           patterns=patterns)


@app.route('/groups')
@login_required
def dream_groups():
    """Dream groups listing route."""
    groups = DreamGroup.query.all()
    return render_template('dream_groups.html', groups=groups)


@app.route('/subscription')
@login_required
def subscription():
    """View and manage subscription."""
    stripe_publishable_key = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    if not stripe_publishable_key:
        flash(
            'Payment system is currently unavailable. Please try again later.')
        return redirect(url_for('index'))
    return render_template('subscription.html',
                           stripe_publishable_key=stripe_publishable_key)


@app.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """Create Stripe checkout session."""
    try:
        # Create the product and price
        product = stripe.Product.create(
            name='DreamLoop Premium Subscription',
            description='Unlimited AI dream analysis and advanced features')

        price = stripe.Price.create(
            unit_amount=999,  # $9.99 in cents
            currency='usd',
            recurring={'interval': 'month'},
            product=product.id)

        # Create the checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price.id,
                'quantity': 1
            }],
            mode='subscription',
            success_url=url_for('subscription', success='true',
                                _external=True),
            cancel_url=url_for('subscription', canceled='true',
                               _external=True),
            customer_email=current_user.email,
            metadata={
                'user_email': current_user.email,
                'user_id': str(current_user.id)
            })

        return jsonify({
            'url': checkout_session.url,
            'sessionId': checkout_session.id
        })
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        return jsonify({'error': str(e)}), 400


@app.route('/subscription/cancel', methods=['POST'])
@login_required
def subscription_cancel():
    """Cancel user's premium subscription."""
    try:
        if current_user.subscription_type != 'premium':
            flash('No active subscription found.')
            return redirect(url_for('subscription'))

        current_user.subscription_type = 'free'
        current_user.subscription_end_date = None
        db.session.commit()

        flash('Your subscription has been canceled.')
        return redirect(url_for('subscription'))

    except Exception as e:
        logger.error(f"Error canceling subscription: {str(e)}")
        flash(
            'An error occurred while canceling your subscription. Please try again.'
        )
        return redirect(url_for('subscription'))


@app.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')

    if not sig_header:
        return "No Stripe signature header", 400

    success, message = handle_stripe_webhook(payload, sig_header)

    if success:
        return message, 200
    else:
        return message, 400


@app.context_processor
def utility_processor():

    def validate_google_ads_credentials():
        return True

    def hash_email(email):
        return hashlib.md5(email.lower().encode()).hexdigest()

    def should_show_premium_ads():
        return show_premium_ads(
            current_user) if current_user.is_authenticated else False

    return dict(
        validate_google_ads_credentials=validate_google_ads_credentials,
        hash_email=hash_email,
        should_show_premium_ads=should_show_premium_ads)
