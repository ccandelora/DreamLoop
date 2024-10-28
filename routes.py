from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import User, Dream, Comment, DreamGroup, GroupMembership, ForumPost, ForumReply
from ai_helper import analyze_dream, analyze_dream_patterns
from google_ads_helper import track_premium_conversion, show_premium_ads, validate_google_ads_credentials
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@app.route('/subscription/upgrade', methods=['POST'])
@login_required
def upgrade_subscription():
    try:
        if current_user.subscription_type == 'premium':
            flash('You are already a premium member!')
            return redirect(url_for('subscription'))
        
        # Update user subscription
        current_user.subscription_type = 'premium'
        current_user.subscription_end_date = datetime.utcnow() + timedelta(days=30)
        db.session.commit()
        
        # Track the conversion in Google Ads
        if validate_google_ads_credentials():
            if track_premium_conversion(current_user.id):
                logger.info(f"Successfully tracked premium conversion for user {current_user.id}")
            else:
                logger.warning(f"Failed to track premium conversion for user {current_user.id}")
        else:
            logger.info("Skipping conversion tracking due to missing credentials")
        
        flash('Successfully upgraded to premium! Enjoy unlimited AI analysis.')
        return redirect(url_for('subscription'))
        
    except Exception as e:
        logger.error(f"Error during subscription upgrade: {str(e)}")
        db.session.rollback()
        flash('An error occurred during the upgrade. Please try again or contact support.')
        return redirect(url_for('subscription'))

@app.context_processor
def inject_ad_context():
    def should_show_premium_ads():
        return show_premium_ads(current_user) if current_user.is_authenticated else False
    
    return {
        'should_show_premium_ads': should_show_premium_ads,
        'validate_google_ads_credentials': validate_google_ads_credentials
    }
