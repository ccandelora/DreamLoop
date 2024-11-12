from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import User, Dream, Comment, DreamGroup, GroupMembership, ForumPost, ForumReply
from datetime import datetime
import logging
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc
import os
import stripe
from ai_helper import analyze_dream, analyze_dream_patterns

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def register_routes(app):
    @app.route('/')
    def index():
        """Landing page and user dashboard."""
        try:
            if current_user.is_authenticated:
                dreams = Dream.query\
                    .filter_by(user_id=current_user.id)\
                    .order_by(Dream.date.desc())\
                    .limit(5)\
                    .all()
                logger.info(f"Successfully fetched {len(dreams) if dreams else 0} dreams for user {current_user.id}")
                return render_template('index.html', dreams=dreams)
            return render_template('index.html')
        except SQLAlchemyError as e:
            logger.error(f"Database error in index: {str(e)}")
            db.session.rollback()
            flash('An error occurred while loading your dreams')
            return render_template('index.html', dreams=[])

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """User login."""
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        if request.method == 'POST':
            try:
                username = request.form.get('username')
                password = request.form.get('password')
                
                if not username or not password:
                    flash('Please provide both username and password')
                    return render_template('login.html')
                
                user = User.query.filter_by(username=username).first()
                
                if user and user.check_password(password):
                    login_user(user, remember=True)
                    next_page = request.args.get('next')
                    if not next_page or not next_page.startswith('/'):
                        next_page = url_for('index')
                    return redirect(next_page)
                
                flash('Invalid username or password')
                return render_template('login.html')
            except SQLAlchemyError as e:
                logger.error(f"Database error during login: {str(e)}")
                db.session.rollback()
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
                existing_user = User.query.filter_by(username=username).first()
                if existing_user:
                    flash('Username already exists')
                    return render_template('register.html')
                
                existing_email = User.query.filter_by(email=email).first()
                if existing_email:
                    flash('Email already registered')
                    return render_template('register.html')
                
                user = User(username=username, email=email)
                user.set_password(password)
                
                db.session.add(user)
                db.session.commit()
                login_user(user)
                flash('Registration successful! Welcome to DreamLoop!')
                return redirect(url_for('index'))
            except SQLAlchemyError as e:
                logger.error(f"Database error registering user: {str(e)}")
                db.session.rollback()
                flash('An error occurred during registration')
                return render_template('register.html')
        
        return render_template('register.html')

    @app.route('/dream_patterns')
    @login_required
    def dream_patterns():
        """View and analyze dream patterns."""
        try:
            logger.info(f"Fetching dreams for pattern analysis - user {current_user.id}")
            dreams = Dream.query\
                .filter_by(user_id=current_user.id)\
                .order_by(Dream.date.desc())\
                .all()
            
            if not dreams:
                logger.info("No dreams found for pattern analysis")
                return render_template('dream_patterns.html', patterns=None)
            
            try:
                patterns = analyze_dream_patterns(dreams)
                if not patterns:
                    flash('Unable to analyze dream patterns. Please try again.')
                    return render_template('dream_patterns.html', patterns=None)
                    
                logger.info("Successfully analyzed dream patterns")
                return render_template('dream_patterns.html', patterns=patterns)
                
            except Exception as e:
                logger.error(f"Error analyzing dream patterns: {str(e)}")
                flash('An error occurred while analyzing dream patterns')
                return render_template('dream_patterns.html', patterns=None)
                
        except SQLAlchemyError as e:
            logger.error(f"Database error in dream patterns: {str(e)}")
            db.session.rollback()
            flash('An error occurred while loading your dreams')
            return render_template('dream_patterns.html', patterns=None)

    @app.route('/community')
    @login_required
    def community_dreams():
        """View all public dreams from the community."""
        try:
            public_dreams = Dream.query\
                .filter_by(is_public=True)\
                .order_by(Dream.date.desc())\
                .all()
            return render_template('community_dreams.html', dreams=public_dreams)
        except SQLAlchemyError as e:
            logger.error(f"Database error in community dreams: {str(e)}")
            db.session.rollback()
            flash('An error occurred while loading community dreams')
            return redirect(url_for('index'))

    @app.route('/groups')
    @login_required
    def dream_groups():
        """View all dream groups."""
        try:
            groups = DreamGroup.query.all()
            return render_template('dream_groups.html', groups=groups)
        except SQLAlchemyError as e:
            logger.error(f"Database error in dream groups: {str(e)}")
            db.session.rollback()
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
                db.session.flush()
                
                membership = GroupMembership(user_id=current_user.id, group_id=group.id, is_admin=True)
                db.session.add(membership)
                
                db.session.commit()
                flash('Group created successfully!')
                return redirect(url_for('dream_groups'))
            except SQLAlchemyError as e:
                logger.error(f"Error creating group: {str(e)}")
                db.session.rollback()
                flash('An error occurred while creating the group')
                return render_template('create_group.html')
        
        return render_template('create_group.html')

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
            except SQLAlchemyError as e:
                logger.error(f"Error creating dream: {str(e)}")
                db.session.rollback()
                flash('An error occurred while saving your dream')
                return render_template('dream_new.html')
        
        return render_template('dream_new.html')

    @app.route('/dream/<int:dream_id>')
    @login_required
    def dream_view(dream_id):
        """View a dream entry."""
        try:
            dream = Dream.query.get_or_404(dream_id)
            if dream.user_id != current_user.id and not dream.is_public:
                flash('You do not have permission to view this dream')
                return redirect(url_for('index'))
            return render_template('dream_view.html', dream=dream)
        except SQLAlchemyError as e:
            logger.error(f"Database error viewing dream: {str(e)}")
            db.session.rollback()
            flash('An error occurred while loading the dream')
            return redirect(url_for('index'))

    @app.route('/group/<int:group_id>')
    @login_required
    def group_view(group_id):
        """View a dream group."""
        try:
            group = DreamGroup.query.get_or_404(group_id)
            return render_template('group_view.html', group=group)
        except SQLAlchemyError as e:
            logger.error(f"Database error viewing group: {str(e)}")
            db.session.rollback()
            flash('An error occurred while loading the group')
            return redirect(url_for('index'))

    @app.route('/group/<int:group_id>/join', methods=['POST'])
    @login_required
    def join_group(group_id):
        """Join a dream group."""
        try:
            group = DreamGroup.query.get_or_404(group_id)
            
            membership = GroupMembership.query.filter_by(user_id=current_user.id, group_id=group_id).first()
            if membership:
                flash('You are already a member of this group')
                return redirect(url_for('group_view', group_id=group_id))
            
            membership = GroupMembership(user_id=current_user.id, group_id=group_id)
            db.session.add(membership)
            db.session.commit()
            flash('You have successfully joined the group!')
            return redirect(url_for('group_view', group_id=group_id))
        except SQLAlchemyError as e:
            logger.error(f"Database error joining group: {str(e)}")
            db.session.rollback()
            flash('An error occurred while joining the group')
            return redirect(url_for('group_view', group_id=group_id))

    @app.route('/group/<int:group_id>/leave', methods=['POST'])
    @login_required
    def leave_group(group_id):
        """Leave a dream group."""
        try:
            group = DreamGroup.query.get_or_404(group_id)
            membership = GroupMembership.query.filter_by(user_id=current_user.id, group_id=group_id).first()
            if not membership:
                flash('You are not a member of this group')
                return redirect(url_for('group_view', group_id=group_id))
            
            db.session.delete(membership)
            db.session.commit()
            flash('You have successfully left the group')
            return redirect(url_for('group_view', group_id=group_id))
        except SQLAlchemyError as e:
            logger.error(f"Database error leaving group: {str(e)}")
            db.session.rollback()
            flash('An error occurred while leaving the group')
            return redirect(url_for('group_view', group_id=group_id))

    @app.route('/group/<int:group_id>/dreams')
    @login_required
    def group_dreams(group_id):
        """View dreams shared in a group."""
        try:
            group = DreamGroup.query.get_or_404(group_id)
            
            # Get all dreams shared in this group
            group_dreams = Dream.query.filter(Dream.user_id.in_([m.user_id for m in group.members])).all()
            
            return render_template('group_dreams.html', group=group, dreams=group_dreams)
        except SQLAlchemyError as e:
            logger.error(f"Database error loading group dreams: {str(e)}")
            db.session.rollback()
            flash('An error occurred while loading group dreams')
            return redirect(url_for('group_view', group_id=group_id))

    @app.route('/dream/<int:dream_id>/comment', methods=['POST'])
    @login_required
    def add_comment(dream_id):
        """Add a comment to a dream."""
        try:
            dream = Dream.query.get_or_404(dream_id)
            comment_text = request.form.get('comment_text')
            if not comment_text:
                flash('Please enter a comment')
                return redirect(url_for('dream_view', dream_id=dream_id))
            
            comment = Comment(
                dream_id=dream_id,
                user_id=current_user.id,
                content=comment_text
            )
            db.session.add(comment)
            db.session.commit()
            flash('Comment added successfully!')
            return redirect(url_for('dream_view', dream_id=dream_id))
        except SQLAlchemyError as e:
            logger.error(f"Database error adding comment: {str(e)}")
            db.session.rollback()
            flash('An error occurred while adding the comment')
            return redirect(url_for('dream_view', dream_id=dream_id))

    @app.route('/forum')
    @login_required
    def forum():
        """View the forum."""
        try:
            posts = ForumPost.query.order_by(ForumPost.created_at.desc()).all()
            return render_template('forum.html', posts=posts)
        except SQLAlchemyError as e:
            logger.error(f"Database error loading forum posts: {str(e)}")
            db.session.rollback()
            flash('An error occurred while loading forum posts')
            return redirect(url_for('index'))

    @app.route('/forum/create', methods=['GET', 'POST'])
    @login_required
    def create_forum_post():
        """Create a new forum post."""
        if request.method == 'POST':
            try:
                title = request.form.get('title')
                content = request.form.get('content')
                if not title or not content:
                    flash('Please provide both a title and content for your post')
                    return render_template('create_forum_post.html')
                
                post = ForumPost(
                    user_id=current_user.id,
                    title=title,
                    content=content
                )
                db.session.add(post)
                db.session.commit()
                flash('Forum post created successfully!')
                return redirect(url_for('forum'))
            except SQLAlchemyError as e:
                logger.error(f"Database error creating forum post: {str(e)}")
                db.session.rollback()
                flash('An error occurred while creating the forum post')
                return render_template('create_forum_post.html')
        
        return render_template('create_forum_post.html')

    @app.route('/forum/<int:post_id>')
    @login_required
    def forum_post(post_id):
        """View a forum post."""
        try:
            post = ForumPost.query.get_or_404(post_id)
            replies = ForumReply.query.filter_by(post_id=post_id).order_by(ForumReply.created_at.desc()).all()
            return render_template('forum_post.html', post=post, replies=replies)
        except SQLAlchemyError as e:
            logger.error(f"Database error loading forum post: {str(e)}")
            db.session.rollback()
            flash('An error occurred while loading the forum post')
            return redirect(url_for('forum'))

    @app.route('/forum/<int:post_id>/reply', methods=['POST'])
    @login_required
    def add_forum_reply(post_id):
        """Add a reply to a forum post."""
        try:
            post = ForumPost.query.get_or_404(post_id)
            reply_content = request.form.get('reply_content')
            if not reply_content:
                flash('Please enter a reply')
                return redirect(url_for('forum_post', post_id=post_id))
            
            reply = ForumReply(
                post_id=post_id,
                user_id=current_user.id,
                content=reply_content
            )
            db.session.add(reply)
            db.session.commit()
            flash('Reply added successfully!')
            return redirect(url_for('forum_post', post_id=post_id))
        except SQLAlchemyError as e:
            logger.error(f"Database error adding forum reply: {str(e)}")
            db.session.rollback()
            flash('An error occurred while adding the reply')
            return redirect(url_for('forum_post', post_id=post_id))

    return app