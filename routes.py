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

@app.route('/dream/<int:dream_id>/reanalyze', methods=['POST'])
@login_required
def reanalyze_dream(dream_id):
    """Reanalyze a dream using AI."""
    dream = Dream.query.get_or_404(dream_id)
    
    # Verify ownership
    if dream.user_id != current_user.id:
        flash('You can only reanalyze your own dreams.')
        return redirect(url_for('dream_view', dream_id=dream_id))
    
    # Check AI analysis quota for free users
    if current_user.subscription_type == 'free':
        if current_user.monthly_ai_analysis_count >= 3:
            flash('You have reached your monthly AI analysis limit. Upgrade to Premium for unlimited analyses!')
            return redirect(url_for('subscription'))
            
        # Reset counter if it's a new month
        last_reset = current_user.last_analysis_reset
        if last_reset and (datetime.utcnow() - last_reset).days >= 30:
            current_user.monthly_ai_analysis_count = 0
            current_user.last_analysis_reset = datetime.utcnow()
    
    try:
        # Perform AI analysis
        is_premium = current_user.subscription_type == 'premium'
        dream.ai_analysis = analyze_dream(dream.content, is_premium=is_premium)
        
        # Update counter for free users
        if current_user.subscription_type == 'free':
            current_user.monthly_ai_analysis_count += 1
        
        db.session.commit()
        flash('Dream analysis updated successfully!')
        
    except Exception as e:
        logger.error(f"Error reanalyzing dream: {str(e)}")
        db.session.rollback()
        flash('An error occurred while reanalyzing your dream.')
        
    return redirect(url_for('dream_view', dream_id=dream_id))

# ... [rest of the existing routes.py content] ...
