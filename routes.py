from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import User, Dream, Comment, DreamGroup, GroupMembership
from datetime import datetime
import logging
import os
import hashlib
from google_ads_helper import track_premium_conversion, show_premium_ads, validate_google_ads_credentials
from ai_helper import analyze_dream, analyze_dream_patterns
from stripe_webhook_handler import handle_stripe_webhook
import stripe

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route('/')
def index():
    """Home page."""
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('index'))

        flash('Invalid username or password')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration."""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return render_template('register.html')

        user = User(username=username,
                    email=email,
                    subscription_type='free',
                    monthly_ai_analysis_count=0,
                    last_analysis_reset=datetime.utcnow())
        user.set_password(password)

        try:
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please login.')
            return redirect(url_for('login'))
        except Exception as e:
            logger.error(f"Error during registration: {str(e)}")
            db.session.rollback()
            flash('An error occurred during registration. Please try again.')
            return render_template('register.html')

    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    """User logout."""
    logout_user()
    return redirect(url_for('index'))


@app.route('/dream/<int:dream_id>')
@login_required
def dream_view(dream_id):
    """View individual dream."""
    dream = Dream.query.get_or_404(dream_id)
    if dream.user_id != current_user.id and not dream.is_public:
        flash('You do not have permission to view this dream.')
        return redirect(url_for('index'))
    return render_template('dream_view.html', dream=dream)


@app.route('/dream/new', methods=['GET', 'POST'])
@login_required
def dream_new():
    """Create a new dream entry."""
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        mood = request.form.get('mood')
        tags = request.form.get('tags')
        is_public = bool(request.form.get('is_public'))
        is_anonymous = bool(request.form.get('is_anonymous'))

        dream = Dream(title=title,
                      content=content,
                      mood=mood,
                      tags=tags,
                      is_public=is_public,
                      is_anonymous=is_anonymous,
                      user_id=current_user.id)

        try:
            # Perform AI analysis if user has available analyses
            if current_user.subscription_type == 'premium' or current_user.monthly_ai_analysis_count < 3:
                dream.ai_analysis = analyze_dream(content)
                if current_user.subscription_type == 'free':
                    current_user.monthly_ai_analysis_count += 1

            db.session.add(dream)
            db.session.commit()
            flash('Dream logged successfully!')
            return redirect(url_for('dream_view', dream_id=dream.id))

        except Exception as e:
            logger.error(f"Error creating dream: {str(e)}")
            db.session.rollback()
            flash('An error occurred while saving your dream.')
            return render_template('dream_new.html')

    return render_template('dream_new.html')


@app.route('/dream_patterns')
@login_required
def dream_patterns():
    """View dream patterns."""
    dreams = current_user.dreams.all()
    patterns = analyze_dream_patterns(dreams) if dreams else None
    return render_template('dream_patterns.html', patterns=patterns)


@app.route('/subscription')
@login_required
def subscription():
    """Subscription management page."""
    stripe_publishable_key = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    return render_template('subscription.html',
                           stripe_publishable_key=stripe_publishable_key)


@app.route('/community_dreams')
def community_dreams():
    """View community dreams."""
    dreams = Dream.query.filter_by(is_public=True).all()
    return render_template('community_dreams.html', dreams=dreams)


@app.route('/dream_groups')
@login_required
def dream_groups():
    """View all dream groups."""
    groups = DreamGroup.query.all()
    return render_template('dream_groups.html', groups=groups)


@app.route('/dream/<int:dream_id>/comment', methods=['POST'])
@login_required
def add_comment(dream_id):
    """Add a comment to a dream."""
    dream = Dream.query.get_or_404(dream_id)

    if not dream.is_public and dream.user_id != current_user.id:
        flash('You cannot comment on this dream.')
        return redirect(url_for('index'))

    content = request.form.get('content')
    if not content:
        flash('Comment cannot be empty.')
        return redirect(url_for('dream_view', dream_id=dream_id))

    try:
        comment = Comment(content=content,
                          user_id=current_user.id,
                          dream_id=dream_id,
                          created_at=datetime.utcnow())

        db.session.add(comment)
        db.session.commit()
        flash('Comment added successfully!')

    except Exception as e:
        logger.error(f"Error adding comment: {str(e)}")
        db.session.rollback()
        flash('An error occurred while adding your comment.')

    return redirect(url_for('dream_view', dream_id=dream_id))


@app.route('/dream/<int:dream_id>/comment/<int:comment_id>/delete',
           methods=['POST'])
@login_required
def delete_comment(dream_id, comment_id):
    """Delete a comment."""
    try:
        comment = Comment.query.get_or_404(comment_id)
        dream = Dream.query.get_or_404(dream_id)

        if comment.user_id != current_user.id and dream.user_id != current_user.id:
            flash('You do not have permission to delete this comment.')
            return redirect(url_for('dream_view', dream_id=dream_id))

        db.session.delete(comment)
        db.session.commit()
        flash('Comment deleted successfully!')

    except Exception as e:
        logger.error(f"Error deleting comment: {str(e)}")
        db.session.rollback()
        flash('An error occurred while deleting the comment.')

    return redirect(url_for('dream_view', dream_id=dream_id))
