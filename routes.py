from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import User, Dream, Comment, DreamGroup, GroupMembership, ForumPost, ForumReply
from datetime import datetime, timedelta
import logging
import os
import hashlib
import json
from collections import Counter, defaultdict
import statistics
from google_ads_helper import track_premium_conversion, show_premium_ads, validate_google_ads_credentials
from ai_helper import analyze_dream, analyze_dream_patterns
from stripe_webhook_handler import handle_stripe_webhook
import stripe
import markdown
from sqlalchemy import desc, func, extract

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app.jinja_env.filters['markdown'] = lambda text: markdown.markdown(text) if text else ''

@app.route('/')
def index():
    """Home page."""
    if current_user.is_authenticated:
        return render_template('index.html', Dream=Dream)
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
        
        # Get new fields
        try:
            lucidity_level = int(request.form.get('lucidity_level', 0))
            sleep_quality = int(request.form.get('sleep_quality', 1))
            dream_clarity = int(request.form.get('dream_clarity', 1))
        except (ValueError, TypeError):
            flash('Invalid values provided for lucidity, sleep quality, or clarity')
            return render_template('dream_new.html')

        # Validate ranges
        if not (0 <= lucidity_level <= 5 and 1 <= sleep_quality <= 5 and 1 <= dream_clarity <= 5):
            flash('Invalid range for lucidity, sleep quality, or clarity')
            return render_template('dream_new.html')

        dream = Dream(
            title=title,
            content=content,
            mood=mood,
            tags=tags,
            is_public=is_public,
            is_anonymous=is_anonymous,
            user_id=current_user.id,
            lucidity_level=lucidity_level,
            sleep_quality=sleep_quality,
            dream_clarity=dream_clarity
        )

        try:
            if current_user.subscription_type == 'premium' or current_user.monthly_ai_analysis_count < 3:
                is_premium = current_user.subscription_type == 'premium'
                ai_analysis = analyze_dream(content, is_premium=is_premium)
                dream.ai_analysis = ai_analysis
                
                # Analyze emotional tone and extract themes
                if isinstance(ai_analysis, dict):
                    dream.emotional_tone = ai_analysis.get('emotional_tone', 0)
                    dream.dream_symbols = json.dumps(ai_analysis.get('symbols', []))
                    dream.recurring_elements = json.dumps(ai_analysis.get('themes', []))
                    dream.dream_archetypes = json.dumps(ai_analysis.get('archetypes', []))
                
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
    """View dream patterns with enhanced analysis for premium users."""
    dreams = current_user.dreams.order_by(Dream.date.desc()).all()
    
    if not dreams:
        return render_template('dream_patterns.html', patterns=None)
        
    try:
        # Basic statistics
        dream_count = len(dreams)
        lucid_dreams = sum(1 for dream in dreams if dream.lucidity_level and dream.lucidity_level > 0)
        
        # Calculate average clarity safely
        valid_clarity_values = [d.dream_clarity for d in dreams if d.dream_clarity is not None]
        avg_clarity = sum(valid_clarity_values) / len(valid_clarity_values) if valid_clarity_values else 0
        
        # Mood distribution with safe handling
        mood_distribution = Counter(dream.mood for dream in dreams if dream.mood)
        
        # Dream frequency over time
        date_counts = defaultdict(int)
        for dream in dreams:
            date_str = dream.date.strftime('%Y-%m-%d')
            date_counts[date_str] += 1
        
        # Sort dates and prepare frequency data
        sorted_dates = sorted(date_counts.keys())
        dream_frequency = {date: date_counts[date] for date in sorted_dates}
        
        # Emotional tone analysis with safe handling
        emotional_tone = {}
        for dream in dreams:
            if dream.emotional_tone is not None:
                emotional_tone[dream.date.strftime('%Y-%m-%d')] = dream.emotional_tone
        
        # Common themes and symbols with safe handling
        all_themes = []
        for dream in dreams:
            if dream.recurring_elements:
                try:
                    elements = json.loads(dream.recurring_elements or '[]')
                    all_themes.extend(elements)
                except (json.JSONDecodeError, TypeError):
                    continue
        
        common_themes = dict(Counter(all_themes).most_common(10))
        
        # Sleep quality correlation with safe handling
        sleep_quality = []
        for dream in dreams:
            if dream.sleep_quality is not None and dream.dream_clarity is not None:
                sleep_quality.append({
                    'x': dream.sleep_quality,
                    'y': dream.dream_clarity
                })
        
        # Archetype analysis with safe handling
        all_archetypes = []
        for dream in dreams:
            if dream.dream_archetypes:
                try:
                    archetypes = json.loads(dream.dream_archetypes or '[]')
                    all_archetypes.extend(archetypes)
                except (json.JSONDecodeError, TypeError):
                    continue
        
        archetype_frequency = dict(Counter(all_archetypes).most_common(8))
        
        # Prepare comprehensive pattern analysis
        patterns = {
            'dream_count': dream_count,
            'lucid_count': lucid_dreams,
            'avg_clarity': round(avg_clarity, 1),
            'mood_distribution': dict(mood_distribution),
            'dream_frequency': dream_frequency,
            'emotional_tone': emotional_tone,
            'common_themes': common_themes,
            'sleep_quality': sleep_quality,
            'archetypes': archetype_frequency
        }
        
        # Add AI analysis for premium users
        if current_user.subscription_type == 'premium':
            patterns['ai_analysis'] = analyze_dream_patterns(dreams, is_premium=True)
        else:
            patterns['ai_analysis'] = analyze_dream_patterns(dreams, is_premium=False)
        
        return render_template('dream_patterns.html', patterns=patterns)
        
    except Exception as e:
        logging.error(f"Error analyzing dream patterns: {str(e)}")
        flash('An error occurred while analyzing dream patterns.')
        return render_template('dream_patterns.html', patterns=None)
