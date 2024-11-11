from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import User, Dream, Comment, DreamGroup, GroupMembership, ForumPost, ForumReply
from datetime import datetime, timedelta
from sqlalchemy import desc, text
import logging
import os
import stripe
from ai_helper import analyze_dream, analyze_dream_patterns
from sqlalchemy.exc import SQLAlchemyError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def handle_stripe_webhook(payload, sig_header):
    """Handle Stripe webhook events."""
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        logger.error(f"Invalid payload: {str(e)}")
        return False, "Invalid payload"
    except Exception as e:
        logger.error(f"Invalid signature: {str(e)}")
        return False, "Invalid signature"

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = session.get('client_reference_id')
        
        if user_id:
            try:
                user = db.session.get(User, int(user_id))
                if user:
                    user.subscription_type = 'premium'
                    user.subscription_end_date = datetime.utcnow() + timedelta(days=30)
                    db.session.commit()
                    logger.info(f"User {user_id} upgraded to premium")
                    return True, "Subscription updated"
            except Exception as e:
                logger.error(f"Error updating user subscription: {str(e)}")
                return False, "Error updating subscription"
    
    return True, "Webhook processed"

def register_routes(app):
    @app.route('/')
    def index():
        """Landing page and user dashboard."""
        try:
            if current_user.is_authenticated:
                dreams = Dream.query.filter_by(user_id=current_user.id)\
                    .order_by(Dream.date.desc())\
                    .limit(5)\
                    .all()
                return render_template('index.html', dreams=dreams)
            return render_template('index.html')
        except Exception as e:
            logger.error(f"Error rendering index page: {str(e)}")
            flash('An error occurred while loading the dashboard')
            return render_template('index.html')

    @app.route('/dream_patterns')
    @login_required
    def dream_patterns():
        """View and analyze dream patterns."""
        try:
            dreams = Dream.query.filter_by(user_id=current_user.id)\
                .order_by(Dream.date.desc())\
                .all()
            patterns = analyze_dream_patterns(dreams) if dreams else None
            return render_template('dream_patterns.html', dreams=dreams, patterns=patterns)
        except Exception as e:
            logger.error(f"Database error in dream patterns: {str(e)}")
            flash('An error occurred while analyzing dream patterns')
            return redirect(url_for('index'))

    @app.route('/subscription')
    @login_required
    def subscription():
        """Subscription management page."""
        try:
            return render_template('subscription.html')
        except Exception as e:
            logger.error(f"Error loading subscription page: {str(e)}")
            flash('An error occurred while loading the subscription page')
            return redirect(url_for('index'))

    @app.route('/group/<int:group_id>/join', methods=['POST'])
    @login_required
    def join_group(group_id):
        """Join a dream group."""
        try:
            group = DreamGroup.query.get(group_id)
            if not group:
                flash('Group not found')
                return redirect(url_for('dream_groups'))
            
            if current_user not in group.members:
                membership = GroupMembership(user_id=current_user.id, group_id=group.id)
                db.session.add(membership)
                db.session.commit()
                flash('Successfully joined the group!')
            else:
                flash('You are already a member of this group')
            return redirect(url_for('dream_group', group_id=group_id))
        except Exception as e:
            logger.error(f"Database error joining group: {str(e)}")
            db.session.rollback()
            flash('An error occurred while joining the group')
            return redirect(url_for('dream_groups'))

    @app.route('/group/<int:group_id>')
    @login_required
    def dream_group(group_id):
        """View a specific dream group."""
        try:
            group = DreamGroup.query.get(group_id)
            if not group:
                flash('Group not found')
                return redirect(url_for('dream_groups'))
                
            is_member = current_user in group.members
            if not is_member:
                flash('You must be a member to view this group')
                return redirect(url_for('dream_groups'))
            return render_template('dream_group.html', group=group)
        except Exception as e:
            logger.error(f"Database error viewing group: {str(e)}")
            flash('An error occurred while loading the group')
            return redirect(url_for('dream_groups'))

    @app.route('/community')
    @login_required
    def community_dreams():
        """View all public dreams from the community."""
        try:
            public_dreams = Dream.query.filter_by(is_public=True)\
                .order_by(Dream.date.desc())\
                .all()
            return render_template('community_dreams.html', dreams=public_dreams)
        except Exception as e:
            logger.error(f"Database error in community dreams: {str(e)}")
            flash('An error occurred while loading community dreams')
            return redirect(url_for('index'))

    @app.route('/groups')
    @login_required
    def dream_groups():
        """View all dream groups."""
        try:
            groups = DreamGroup.query.all()
            return render_template('dream_groups.html', groups=groups)
        except Exception as e:
            logger.error(f"Database error in dream groups: {str(e)}")
            flash('An error occurred while loading dream groups')
            return redirect(url_for('index'))

    @app.route('/group/create', methods=['GET', 'POST'])
    @login_required
    def create_group():
        """Create a new dream group."""
        if request.method == 'POST':
            name = request.form.get('name')
            description = request.form.get('description')
            
            if not name:
                flash('Group name is required')
                return render_template('create_group.html')
            
            try:
                group = DreamGroup(name=name, description=description, created_by=current_user.id)
                db.session.add(group)
                
                membership = GroupMembership(user_id=current_user.id, group_id=group.id, is_admin=True)
                db.session.add(membership)
                
                db.session.commit()
                flash('Group created successfully!')
                return redirect(url_for('dream_groups'))
            except Exception as e:
                logger.error(f"Error creating group: {str(e)}")
                db.session.rollback()
                flash('An error occurred while creating the group')
        
        return render_template('create_group.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """User login."""
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            if not username or not password:
                flash('Please provide both username and password')
                return render_template('login.html')
            
            try:
                user = User.query.filter_by(username=username).first()
                if user and user.check_password(password):
                    login_user(user)
                    next_page = request.args.get('next')
                    if not next_page or not next_page.startswith('/'):
                        next_page = url_for('index')
                    return redirect(next_page)
                
                flash('Invalid username or password')
            except Exception as e:
                logger.error(f"Error during login: {str(e)}")
                flash('An error occurred during login')
            
            return render_template('login.html')
        
        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        """User logout."""
        logout_user()
        return redirect(url_for('index'))

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        """User registration."""
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            
            if not all([username, email, password]):
                flash('All fields are required')
                return render_template('register.html')
            
            try:
                if User.query.filter_by(username=username).first():
                    flash('Username already exists')
                    return render_template('register.html')
                
                if User.query.filter_by(email=email).first():
                    flash('Email already registered')
                    return render_template('register.html')
                
                user = User(username=username, email=email)
                user.set_password(password)
                
                db.session.add(user)
                db.session.commit()
                login_user(user)
                return redirect(url_for('index'))
            except Exception as e:
                logger.error(f"Error registering user: {str(e)}")
                db.session.rollback()
                flash('An error occurred during registration')
        
        return render_template('register.html')

    @app.route('/dream/new', methods=['GET', 'POST'])
    @login_required
    def dream_new():
        """Create a new dream entry."""
        if request.method == 'POST':
            try:
                dream = Dream(
                    user_id=current_user.id,
                    title=request.form.get('title'),
                    content=request.form.get('content')
                )
                dream.mood = request.form.get('mood')
                dream.tags = request.form.get('tags')
                dream.is_public = bool(request.form.get('is_public'))
                dream.is_anonymous = bool(request.form.get('is_anonymous'))
                dream.lucidity_level = int(request.form.get('lucidity_level', 1))
                
                sleep_quality = request.form.get('sleep_quality')
                if sleep_quality and sleep_quality.isdigit():
                    dream.sleep_quality = int(sleep_quality)
                
                interruptions = request.form.get('sleep_interruptions', '0')
                if interruptions.isdigit():
                    dream.sleep_interruptions = int(interruptions)
                    
                dream.sleep_position = request.form.get('sleep_position')
                
                bed_time = request.form.get('bed_time')
                wake_time = request.form.get('wake_time')
                if bed_time and wake_time:
                    try:
                        dream.bed_time = datetime.fromisoformat(bed_time)
                        dream.wake_time = datetime.fromisoformat(wake_time)
                        dream.sleep_duration = (dream.wake_time - dream.bed_time).total_seconds() / 3600
                    except ValueError:
                        logger.warning("Invalid date format for bed_time or wake_time")
                
                if current_user.subscription_type == 'premium' or current_user.monthly_ai_analysis_count < 3:
                    is_premium = current_user.subscription_type == 'premium'
                    analysis, sentiment_info = analyze_dream(dream.content, is_premium=is_premium)
                    dream.ai_analysis = analysis
                    
                    if sentiment_info:
                        dream.sentiment_score = sentiment_info.get('sentiment_score')
                        dream.sentiment_magnitude = sentiment_info.get('sentiment_magnitude')
                        dream.dominant_emotions = sentiment_info.get('dominant_emotions')
                        dream.lucidity_level = sentiment_info.get('lucidity_level')
                    
                    if current_user.subscription_type == 'free':
                        current_user.monthly_ai_analysis_count += 1
                
                db.session.add(dream)
                db.session.commit()
                flash('Dream logged successfully!')
                return redirect(url_for('dream_view', dream_id=dream.id))
            except Exception as e:
                logger.error(f"Error creating dream: {str(e)}")
                db.session.rollback()
                flash('An error occurred while saving your dream')
        
        return render_template('dream_new.html')

    @app.route('/dream/<int:dream_id>')
    @login_required
    def dream_view(dream_id):
        """View a dream entry."""
        try:
            dream = Dream.query.get(dream_id)
            if not dream:
                flash('Dream not found')
                return redirect(url_for('index'))
                
            if dream.user_id != current_user.id and not dream.is_public:
                flash('You do not have permission to view this dream')
                return redirect(url_for('index'))
            return render_template('dream_view.html', dream=dream)
        except Exception as e:
            logger.error(f"Database error viewing dream: {str(e)}")
            flash('An error occurred while loading the dream')
            return redirect(url_for('index'))

    @app.route('/webhook', methods=['POST'])
    def stripe_webhook():
        """Handle Stripe webhook events."""
        payload = request.get_data()
        sig_header = request.headers.get('Stripe-Signature')

        success, message = handle_stripe_webhook(payload, sig_header)
        if success:
            return jsonify({'status': 'success', 'message': message}), 200
        return jsonify({'status': 'error', 'message': message}), 400

    return app