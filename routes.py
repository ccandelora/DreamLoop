from flask import render_template, redirect, url_for, flash, request, abort, jsonify, send_file, make_response
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db, session_manager
from models import User, Dream, Comment, DreamGroup, GroupMembership, ForumPost, ForumReply
from datetime import datetime
import logging
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc, text, or_, func
import os
import stripe
from ai_helper import analyze_dream, analyze_dream_patterns
from activity_tracker import (
    track_user_activity, 
    track_premium_feature_usage,
    ACTIVITY_TYPES
)
import csv
from io import StringIO
import json

logger = logging.getLogger(__name__)

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def check_existing_user(username, email):
    """Check if a user with given username or email already exists."""
    try:
        with session_manager.session_scope() as session:
            existing_user = session.query(User).filter(
                (User.username == username) | (User.email == email)
            ).first()
            return existing_user
    except Exception as e:
        logger.error(f"Error checking existing user: {str(e)}")
        return None

def create_user(username, email, password):
    """Create a new user in a separate transaction."""
    try:
        with session_manager.session_scope() as session:
            user = User(username=username, email=email)
            user.set_password(password)
            session.add(user)
            session.flush()  # Get the user ID
            return user.id  # Return the user ID instead of user object
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        return None

def handle_user_login(user_id):
    """Handle user login in a separate transaction."""
    try:
        with session_manager.session_scope() as session:
            user = session.query(User).get(user_id)
            if user:
                if login_user(user):
                    track_user_activity(
                        user.id,
                        ACTIVITY_TYPES['LOGIN'],
                        extra_data={'login_method': 'registration'}
                    )
                    return True
        return False
    except Exception as e:
        logger.error(f"Error during login after registration: {str(e)}")
        return False

def register_routes(app):
    @app.route('/')
    def index():
        """Landing page and user dashboard."""
        try:
            if current_user.is_authenticated:
                success, error = track_user_activity(
                    current_user.id,
                    ACTIVITY_TYPES['DREAM_VIEW'],
                    description="Viewed dashboard",
                    extra_data={'page': 'dashboard'}
                )
                if error:
                    logger.warning(f"Failed to track dashboard view: {error}")
                
                dreams = Dream.query.filter_by(user_id=current_user.id)\
                    .order_by(Dream.date.desc())\
                    .limit(5)\
                    .all()
                return render_template('index.html', dreams=dreams if dreams else [])
            return render_template('index.html')
        except Exception as e:
            logger.error(f"Error in index route: {str(e)}")
            return render_template('index.html', dreams=[])

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        """Handle user registration with separate transactions."""
        if current_user.is_authenticated:
            return redirect(url_for('index'))
            
        if request.method == 'POST':
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']

            try:
                # Check for existing user outside transaction
                existing_user = check_existing_user(username, email)
                
                if existing_user:
                    if existing_user.username == username:
                        flash('Username already exists')
                    else:
                        flash('Email already registered')
                    return render_template('register.html')

                # Create user in separate transaction and get user_id
                user_id = create_user(username, email, password)
                if not user_id:
                    flash('An error occurred during registration')
                    return render_template('register.html')

                # Handle login in separate transaction using user_id
                if handle_user_login(user_id):
                    # Track successful registration
                    track_user_activity(
                        user_id,
                        ACTIVITY_TYPES['REGISTRATION'],
                        extra_data={'registration_method': 'email'}
                    )
                    return redirect(url_for('index'))
                else:
                    flash('Registration successful but login failed. Please try logging in.')
                    return redirect(url_for('login'))

            except Exception as e:
                logger.error(f"Registration error: {str(e)}")
                flash('An error occurred during registration')
                return render_template('register.html')

        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        if request.method == 'POST':
            try:
                with session_manager.session_scope() as session:
                    user = session.query(User).filter_by(username=request.form['username']).first()
                    if user and user.check_password(request.form['password']):
                        if login_user(user):
                            success, error = track_user_activity(
                                user.id, 
                                ACTIVITY_TYPES['LOGIN'],
                                extra_data={'login_method': 'password'}
                            )
                            if error:
                                logger.warning(f"Failed to track login: {error}")
                            
                            next_page = request.args.get('next')
                            return redirect(next_page if next_page else url_for('index'))
                    flash('Invalid username or password')
                    if user:
                        track_user_activity(
                            user.id,
                            ACTIVITY_TYPES['LOGIN'],
                            description="Failed login attempt",
                            extra_data={'reason': 'invalid_credentials'}
                        )
            except Exception as e:
                logger.error(f"Login error: {str(e)}")
                flash('An error occurred during login')
        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        if current_user.is_authenticated:
            success, error = track_user_activity(
                current_user.id,
                ACTIVITY_TYPES['LOGOUT']
            )
            if error:
                logger.warning(f"Failed to track logout: {error}")
        logout_user()
        return redirect(url_for('index'))

    @app.route('/dream/new', methods=['GET', 'POST'])
    @login_required
    def dream_new():
        """Create a new dream entry."""
        if request.method == 'POST':
            try:
                with session_manager.session_scope() as session:
                    dream = Dream(
                        user_id=current_user.id,
                        title=request.form['title'],
                        content=request.form['content'],
                        mood=request.form.get('mood'),
                        tags=request.form.get('tags'),
                        is_public=bool(request.form.get('is_public')),
                        is_anonymous=bool(request.form.get('is_anonymous')),
                        lucidity_level=int(request.form.get('lucidity_level', 0)),
                        sleep_quality=int(request.form.get('sleep_quality', 0)),
                        sleep_position=request.form.get('sleep_position'),
                        sleep_interruptions=int(request.form.get('sleep_interruptions', 0))
                    )
                    session.add(dream)
                    session.flush()

                    track_user_activity(
                        current_user.id,
                        ACTIVITY_TYPES['DREAM_CREATE'],
                        target_id=dream.id,
                        description=f"Created new dream: {dream.title}"
                    )

                    flash('Dream logged successfully!')
                    return redirect(url_for('index'))
            except Exception as e:
                logger.error(f"Error creating dream: {str(e)}")
                flash('An error occurred while saving your dream')
                
        return render_template('dream_new.html')

    @app.route('/dream/<int:dream_id>')
    @login_required
    def dream_view(dream_id):
        """View an individual dream and its comments."""
        try:
            with session_manager.session_scope() as session:
                dream = session.query(Dream).get_or_404(dream_id)
                
                # Check if user has permission to view this dream
                if dream.user_id != current_user.id and not dream.is_public:
                    abort(403)
                
                track_user_activity(
                    current_user.id,
                    ACTIVITY_TYPES['DREAM_VIEW'],
                    target_id=dream.id,
                    description=f"Viewed dream: {dream.title}"
                )
                
                return render_template('dream_view.html', dream=dream)
        except Exception as e:
            logger.error(f"Error viewing dream {dream_id}: {str(e)}")
            flash('An error occurred while loading the dream')
            return redirect(url_for('index'))

    @app.route('/dream/<int:dream_id>/edit', methods=['GET', 'POST'])
    @login_required
    def dream_edit(dream_id):
        """Edit an existing dream."""
        try:
            with session_manager.session_scope() as session:
                dream = session.query(Dream).get_or_404(dream_id)
                
                # Check if user owns this dream
                if dream.user_id != current_user.id:
                    abort(403)
                
                if request.method == 'POST':
                    dream.title = request.form['title']
                    dream.content = request.form['content']
                    dream.mood = request.form.get('mood')
                    dream.tags = request.form.get('tags')
                    dream.is_public = bool(request.form.get('is_public'))
                    dream.is_anonymous = bool(request.form.get('is_anonymous'))
                    dream.lucidity_level = int(request.form.get('lucidity_level', 0))
                    dream.sleep_quality = int(request.form.get('sleep_quality', 0))
                    dream.sleep_position = request.form.get('sleep_position')
                    dream.sleep_interruptions = int(request.form.get('sleep_interruptions', 0))
                    
                    track_user_activity(
                        current_user.id,
                        ACTIVITY_TYPES['DREAM_EDIT'],
                        target_id=dream.id,
                        description=f"Edited dream: {dream.title}"
                    )
                    
                    flash('Dream updated successfully!')
                    return redirect(url_for('dream_view', dream_id=dream.id))
                    
                return render_template('dream_edit.html', dream=dream)
        except Exception as e:
            logger.error(f"Error editing dream {dream_id}: {str(e)}")
            flash('An error occurred while updating the dream')
            return redirect(url_for('dream_view', dream_id=dream_id))

    @app.route('/dream/<int:dream_id>/delete', methods=['POST'])
    @login_required
    def dream_delete(dream_id):
        """Delete a dream."""
        try:
            with session_manager.session_scope() as session:
                dream = session.query(Dream).get_or_404(dream_id)
                
                # Check if user owns this dream
                if dream.user_id != current_user.id:
                    abort(403)
                
                title = dream.title
                session.delete(dream)
                
                track_user_activity(
                    current_user.id,
                    ACTIVITY_TYPES['DREAM_DELETE'],
                    description=f"Deleted dream: {title}"
                )
                
                flash('Dream deleted successfully!')
                return redirect(url_for('index'))
        except Exception as e:
            logger.error(f"Error deleting dream {dream_id}: {str(e)}")
            flash('An error occurred while deleting the dream')
            return redirect(url_for('dream_view', dream_id=dream_id))

    @app.route('/dream/<int:dream_id>/comment', methods=['POST'])
    @login_required
    def add_comment(dream_id):
        """Add a comment to a dream."""
        try:
            with session_manager.session_scope() as session:
                dream = session.query(Dream).get_or_404(dream_id)
                
                # Check if dream is public or user owns it
                if not dream.is_public and dream.user_id != current_user.id:
                    abort(403)
                
                comment = Comment(
                    content=request.form['content'],
                    user_id=current_user.id,
                    dream_id=dream_id
                )
                session.add(comment)
                
                track_user_activity(
                    current_user.id,
                    ACTIVITY_TYPES['COMMENT_CREATE'],
                    target_id=dream_id,
                    description=f"Commented on dream: {dream.title}"
                )
                
                flash('Comment added successfully!')
                return redirect(url_for('dream_view', dream_id=dream_id))
        except Exception as e:
            logger.error(f"Error adding comment to dream {dream_id}: {str(e)}")
            flash('An error occurred while adding the comment')
            return redirect(url_for('dream_view', dream_id=dream_id))

    @app.route('/comment/<int:comment_id>/delete', methods=['POST'])
    @login_required
    def delete_comment(comment_id):
        """Delete a comment."""
        try:
            with session_manager.session_scope() as session:
                comment = session.query(Comment).get_or_404(comment_id)
                dream = session.query(Dream).get(comment.dream_id)
                
                # Check if user owns the comment or the dream
                if comment.user_id != current_user.id and dream.user_id != current_user.id:
                    abort(403)
                
                session.delete(comment)
                
                track_user_activity(
                    current_user.id,
                    ACTIVITY_TYPES['COMMENT_DELETE'],
                    target_id=dream.id,
                    description=f"Deleted comment on dream: {dream.title}"
                )
                
                flash('Comment deleted successfully!')
                return redirect(url_for('dream_view', dream_id=comment.dream_id))
        except Exception as e:
            logger.error(f"Error deleting comment {comment_id}: {str(e)}")
            flash('An error occurred while deleting the comment')
            return redirect(url_for('index'))

    @app.route('/dreams/categories')
    @login_required
    def dream_categories():
        """View dream categories and statistics."""
        try:
            with session_manager.session_scope() as session:
                # Get all unique moods and their counts
                categories = session.query(
                    Dream.mood,
                    func.count(Dream.id).label('dream_count'),
                    func.max(Dream.date).label('last_updated')
                ).filter(
                    or_(Dream.user_id == current_user.id, Dream.is_public == True),
                    Dream.mood.isnot(None)
                ).group_by(Dream.mood).all()
                
                formatted_categories = [
                    {
                        'name': category.mood,
                        'dream_count': category.dream_count,
                        'last_updated': category.last_updated
                    }
                    for category in categories
                ]
                
                track_user_activity(
                    current_user.id,
                    ACTIVITY_TYPES['VIEW'],
                    description="Viewed dream categories"
                )
                
                return render_template('dream_categories.html', categories=formatted_categories)
        except Exception as e:
            logger.error(f"Error viewing dream categories: {str(e)}")
            flash('An error occurred while loading dream categories')
            return redirect(url_for('index'))

    @app.route('/dreams/category/<category>')
    @login_required
    def dreams_by_category(category):
        """View dreams filtered by category/mood."""
        try:
            with session_manager.session_scope() as session:
                dreams = session.query(Dream).filter(
                    or_(Dream.user_id == current_user.id, Dream.is_public == True),
                    Dream.mood == category
                ).order_by(Dream.date.desc()).all()
                
                track_user_activity(
                    current_user.id,
                    ACTIVITY_TYPES['VIEW'],
                    description=f"Viewed dreams in category: {category}"
                )
                
                return render_template('dream_search.html', dreams=dreams, category=category)
        except Exception as e:
            logger.error(f"Error viewing dreams by category: {str(e)}")
            flash('An error occurred while loading dreams')
            return redirect(url_for('dream_categories'))

    @app.route('/dream/<int:dream_id>/export')
    @login_required
    def export_dream(dream_id):
        """Export a dream in various formats."""
        try:
            with session_manager.session_scope() as session:
                dream = session.query(Dream).get_or_404(dream_id)
                
                # Check if user has permission to export this dream
                if dream.user_id != current_user.id:
                    abort(403)
                
                export_format = request.args.get('format', 'json')
                
                if export_format == 'json':
                    data = {
                        'title': dream.title,
                        'content': dream.content,
                        'date': dream.date.isoformat(),
                        'mood': dream.mood,
                        'tags': dream.tags,
                        'lucidity_level': dream.lucidity_level,
                        'sleep_quality': dream.sleep_quality,
                        'sleep_position': dream.sleep_position,
                        'ai_analysis': dream.ai_analysis
                    }
                    
                    response = make_response(json.dumps(data, indent=2))
                    response.headers['Content-Type'] = 'application/json'
                    response.headers['Content-Disposition'] = f'attachment; filename=dream_{dream_id}.json'
                    
                elif export_format == 'csv':
                    output = StringIO()
                    writer = csv.writer(output)
                    writer.writerow(['Field', 'Value'])
                    writer.writerow(['Title', dream.title])
                    writer.writerow(['Content', dream.content])
                    writer.writerow(['Date', dream.date.isoformat()])
                    writer.writerow(['Mood', dream.mood])
                    writer.writerow(['Tags', dream.tags])
                    writer.writerow(['Lucidity Level', dream.lucidity_level])
                    writer.writerow(['Sleep Quality', dream.sleep_quality])
                    writer.writerow(['Sleep Position', dream.sleep_position])
                    writer.writerow(['AI Analysis', dream.ai_analysis])
                    
                    response = make_response(output.getvalue())
                    response.headers['Content-Type'] = 'text/csv'
                    response.headers['Content-Disposition'] = f'attachment; filename=dream_{dream_id}.csv'
                else:
                    abort(400, "Unsupported export format")
                
                track_user_activity(
                    current_user.id,
                    ACTIVITY_TYPES['EXPORT'],
                    target_id=dream.id,
                    description=f"Exported dream: {dream.title} ({export_format})"
                )
                
                return response
                
        except Exception as e:
            logger.error(f"Error exporting dream {dream_id}: {str(e)}")
            flash('An error occurred while exporting the dream')
            return redirect(url_for('dream_view', dream_id=dream_id))

    @app.route('/dream/search')
    @login_required
    def dream_search():
        """Enhanced search with pagination and advanced filtering."""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            
            with session_manager.session_scope() as session:
                query = session.query(Dream).filter(
                    or_(Dream.user_id == current_user.id, Dream.is_public == True)
                )
                
                # Apply filters
                if search_term := request.args.get('q', '').strip():
                    query = query.filter(
                        or_(
                            Dream.title.ilike(f'%{search_term}%'),
                            Dream.content.ilike(f'%{search_term}%'),
                            Dream.tags.ilike(f'%{search_term}%')
                        )
                    )
                
                if mood := request.args.get('mood'):
                    query = query.filter(Dream.mood == mood)
                
                if lucidity := request.args.get('lucidity_level', type=int):
                    query = query.filter(Dream.lucidity_level == lucidity)
                
                if sleep_quality := request.args.get('sleep_quality', type=int):
                    query = query.filter(Dream.sleep_quality == sleep_quality)
                
                if date_from := request.args.get('date_from'):
                    query = query.filter(Dream.date >= date_from)
                
                if date_to := request.args.get('date_to'):
                    query = query.filter(Dream.date <= date_to)
                
                # Apply sorting
                sort_by = request.args.get('sort_by', 'date')
                sort_order = request.args.get('sort_order', 'desc')
                
                if sort_by == 'title':
                    query = query.order_by(desc(Dream.title) if sort_order == 'desc' else Dream.title)
                elif sort_by == 'date':
                    query = query.order_by(desc(Dream.date) if sort_order == 'desc' else Dream.date)
                
                # Paginate results
                dreams = query.paginate(page=page, per_page=per_page, error_out=False)
                
                track_user_activity(
                    current_user.id,
                    ACTIVITY_TYPES['SEARCH'],
                    description=f"Searched dreams with query: {search_term}"
                )
                
                return render_template(
                    'dream_search.html',
                    dreams=dreams.items,
                    pagination=dreams,
                    search_term=search_term,
                    current_filters={
                        'mood': mood,
                        'lucidity_level': lucidity,
                        'sleep_quality': sleep_quality,
                        'date_from': date_from,
                        'date_to': date_to,
                        'sort_by': sort_by,
                        'sort_order': sort_order
                    }
                )
                
        except Exception as e:
            logger.error(f"Error searching dreams: {str(e)}")
            flash('An error occurred while searching dreams')
            return redirect(url_for('index'))

    @app.route('/dream/patterns')
    @login_required
    def dream_patterns():
        """View dream patterns and analytics."""
        try:
            with session_manager.session_scope() as session:
                dreams = session.query(Dream).filter_by(user_id=current_user.id).all()
                patterns = analyze_dream_patterns(dreams) if dreams else None

                track_user_activity(
                    current_user.id,
                    ACTIVITY_TYPES['PATTERNS_VIEW'],
                    description="Viewed dream patterns"
                )

                return render_template('dream_patterns.html', 
                                    patterns=patterns,
                                    dreams=dreams)
        except Exception as e:
            logger.error(f"Error viewing patterns: {str(e)}")
            flash('An error occurred while analyzing dream patterns')
            return redirect(url_for('index'))

    @app.route('/groups')
    @login_required
    def dream_groups():
        """View and manage dream groups."""
        try:
            with session_manager.session_scope() as session:
                groups = session.query(DreamGroup)\
                    .join(GroupMembership)\
                    .filter(GroupMembership.user_id == current_user.id)\
                    .all()

                track_user_activity(
                    current_user.id,
                    ACTIVITY_TYPES['GROUPS_VIEW'],
                    description="Viewed dream groups"
                )

                return render_template('dream_groups.html', groups=groups)
        except Exception as e:
            logger.error(f"Error viewing groups: {str(e)}")
            flash('An error occurred while loading dream groups')
            return redirect(url_for('index'))

    @app.route('/subscription')
    @login_required
    def subscription():
        """View and manage subscription settings."""
        try:
            track_user_activity(
                current_user.id,
                ACTIVITY_TYPES['SUBSCRIPTION_VIEW'],
                description="Viewed subscription page"
            )
            return render_template('subscription.html',
                                stripe_publishable_key=os.getenv('STRIPE_PUBLISHABLE_KEY'))
        except Exception as e:
            logger.error(f"Error viewing subscription: {str(e)}")
            flash('An error occurred while loading subscription information')
            return redirect(url_for('index'))

    @app.route('/community')
    def community_dreams():
        """View public dreams from the community."""
        try:
            with session_manager.session_scope() as session:
                dreams = session.query(Dream)\
                    .filter(Dream.is_public == True)\
                    .order_by(Dream.date.desc())\
                    .limit(20)\
                    .all()

                if current_user.is_authenticated:
                    track_user_activity(
                        current_user.id,
                        ACTIVITY_TYPES['COMMUNITY_VIEW'],
                        description="Viewed community dreams"
                    )

                return render_template('community_dreams.html', dreams=dreams)
        except Exception as e:
            logger.error(f"Error viewing community dreams: {str(e)}")
            flash('An error occurred while loading community dreams')
            return redirect(url_for('index'))

    return app