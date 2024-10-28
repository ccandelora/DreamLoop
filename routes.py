from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import User, Dream, Comment, DreamGroup, GroupMembership, ForumPost, ForumReply
from ai_helper import analyze_dream, analyze_dream_patterns
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
from add_sample_dreams import add_sample_dreams
import json

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dream_log'))
    return redirect(url_for('login'))

@app.route('/subscription')
@login_required
def subscription():
    return render_template('subscription.html')

@app.route('/subscription/upgrade', methods=['POST'])
@login_required
def upgrade_subscription():
    if current_user.subscription_type == 'premium':
        flash('You are already a premium member!')
        return redirect(url_for('subscription'))
    
    current_user.subscription_type = 'premium'
    current_user.subscription_end_date = datetime.utcnow() + timedelta(days=30)
    db.session.commit()
    flash('Successfully upgraded to premium! Enjoy unlimited AI analysis.')
    return redirect(url_for('subscription'))

@app.route('/subscription/cancel', methods=['POST'])
@login_required
def cancel_subscription():
    if current_user.subscription_type != 'premium':
        flash('You are not currently subscribed to premium.')
        return redirect(url_for('subscription'))
    
    current_user.subscription_type = 'free'
    current_user.subscription_end_date = None
    db.session.commit()
    flash('Your premium subscription has been canceled. You can resubscribe at any time.')
    return redirect(url_for('subscription'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            return redirect(url_for('dream_log'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if User.query.filter_by(username=request.form['username']).first():
            flash('Username already exists')
            return redirect(url_for('register'))
            
        user = User()
        user.username = request.form['username']
        user.email = request.form['email']
        user.set_password(request.form['password'])
        
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('dream_log'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dream/new', methods=['GET', 'POST'])
@login_required
def dream_log():
    if request.method == 'POST':
        if not current_user.can_use_ai_analysis():
            flash('You have reached your monthly limit for AI analysis. Upgrade to premium for unlimited analysis!')
            return redirect(url_for('subscription'))
            
        dream = Dream()
        dream.title = request.form['title']
        dream.content = request.form['content']
        dream.mood = request.form['mood']
        dream.tags = request.form['tags']
        dream.is_public = bool(request.form.get('is_public'))
        dream.user_id = current_user.id
        
        dream.ai_analysis = analyze_dream(request.form['content'])
        current_user.increment_ai_analysis_count()
        
        db.session.add(dream)
        db.session.commit()
        return redirect(url_for('dream_view', dream_id=dream.id))
    return render_template('dream_log.html')

@app.route('/dream/<int:dream_id>')
@login_required
def dream_view(dream_id):
    dream = Dream.query.get_or_404(dream_id)
    if not dream.is_public and dream.user_id != current_user.id:
        flash('Access denied')
        return redirect(url_for('dream_log'))
    return render_template('dream_view.html', dream=dream)

@app.route('/community')
@login_required
def community():
    public_dreams = Dream.query.filter_by(is_public=True).order_by(Dream.date.desc()).all()
    return render_template('community.html', dreams=public_dreams)

@app.route('/dream/<int:dream_id>/comment', methods=['POST'])
@login_required
def add_comment(dream_id):
    dream = Dream.query.get_or_404(dream_id)
    if not dream.is_public and dream.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
        
    comment = Comment()
    comment.content = request.form['content']
    comment.dream_id = dream_id
    comment.author_id = current_user.id
    
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('dream_view', dream_id=dream_id))

@app.route('/groups')
@login_required
def dream_groups():
    theme = request.args.get('theme')
    if theme:
        groups = DreamGroup.query.filter_by(theme=theme).all()
    else:
        groups = DreamGroup.query.all()
    themes = db.session.query(DreamGroup.theme).distinct().all()
    themes = [t[0] for t in themes]
    return render_template('dream_groups.html', groups=groups, themes=themes, theme=theme)

@app.route('/groups/create', methods=['GET', 'POST'])
@login_required
def create_group():
    if request.method == 'POST':
        group = DreamGroup()
        group.name = request.form['name']
        group.description = request.form['description']
        group.theme = request.form['theme']
        
        db.session.add(group)
        db.session.flush()
        
        membership = GroupMembership()
        membership.user_id = current_user.id
        membership.group_id = group.id
        membership.is_admin = True
        
        db.session.add(membership)
        db.session.commit()
        
        return redirect(url_for('group_detail', group_id=group.id))
    return render_template('create_group.html')

@app.route('/groups/<int:group_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_group(group_id):
    group = DreamGroup.query.get_or_404(group_id)
    if not group.members.filter_by(user_id=current_user.id, is_admin=True).first():
        flash('Only group admins can edit group details')
        return redirect(url_for('group_detail', group_id=group_id))
    
    if request.method == 'POST':
        group.name = request.form['name']
        group.description = request.form['description']
        group.theme = request.form['theme']
        db.session.commit()
        flash('Group details updated successfully')
        return redirect(url_for('group_detail', group_id=group_id))
    
    return render_template('edit_group.html', group=group)

@app.route('/groups/<int:group_id>')
@login_required
def group_detail(group_id):
    group = DreamGroup.query.get_or_404(group_id)
    is_member = group.members.filter_by(user_id=current_user.id).first() is not None
    is_admin = is_member and group.members.filter_by(user_id=current_user.id).first().is_admin
    user_dreams = current_user.dreams if is_member else []
    return render_template('group_detail.html', group=group, is_member=is_member, 
                         is_admin=is_admin, user_dreams=user_dreams)

@app.route('/groups/<int:group_id>/join', methods=['POST'])
@login_required
def join_group(group_id):
    group = DreamGroup.query.get_or_404(group_id)
    if not group.members.filter_by(user_id=current_user.id).first():
        membership = GroupMembership()
        membership.user_id = current_user.id
        membership.group_id = group_id
        db.session.add(membership)
        db.session.commit()
    return redirect(url_for('group_detail', group_id=group_id))

@app.route('/groups/<int:group_id>/share-dream', methods=['POST'])
@login_required
def share_dream(group_id):
    group = DreamGroup.query.get_or_404(group_id)
    if not group.members.filter_by(user_id=current_user.id).first():
        flash('You must be a member to share dreams')
        return redirect(url_for('group_detail', group_id=group_id))
    
    dream_id = request.form.get('dream_id')
    dream = Dream.query.get_or_404(dream_id)
    
    if dream.user_id != current_user.id:
        flash('You can only share your own dreams')
        return redirect(url_for('group_detail', group_id=group_id))
    
    dream.dream_group_id = group_id
    dream.is_public = True
    db.session.commit()
    
    flash('Dream shared with the group')
    return redirect(url_for('group_detail', group_id=group_id))

@app.route('/groups/<int:group_id>/forum/create', methods=['GET', 'POST'])
@login_required
def create_forum_post(group_id):
    group = DreamGroup.query.get_or_404(group_id)
    if not group.members.filter_by(user_id=current_user.id).first():
        flash('You must be a member to create discussions')
        return redirect(url_for('group_detail', group_id=group_id))
    
    if request.method == 'POST':
        post = ForumPost()
        post.title = request.form['title']
        post.content = request.form['content']
        post.author_id = current_user.id
        post.group_id = group_id
        
        db.session.add(post)
        db.session.commit()
        
        return redirect(url_for('forum_post', post_id=post.id))
    return render_template('create_forum_post.html', group=group)

@app.route('/forum/post/<int:post_id>')
@login_required
def forum_post(post_id):
    post = ForumPost.query.get_or_404(post_id)
    is_member = post.dream_group.members.filter_by(user_id=current_user.id).first() is not None
    return render_template('forum_post.html', post=post, is_member=is_member)

@app.route('/forum/post/<int:post_id>/reply', methods=['POST'])
@login_required
def add_forum_reply(post_id):
    post = ForumPost.query.get_or_404(post_id)
    if not post.dream_group.members.filter_by(user_id=current_user.id).first():
        flash('You must be a member to reply')
        return redirect(url_for('forum_post', post_id=post_id))
    
    reply = ForumReply()
    reply.content = request.form['content']
    reply.author_id = current_user.id
    reply.post_id = post_id
    
    db.session.add(reply)
    db.session.commit()
    
    return redirect(url_for('forum_post', post_id=post_id))

@app.route('/dream/patterns')
@login_required
def dream_patterns():
    dreams = Dream.query.filter_by(user_id=current_user.id).order_by(Dream.date.desc()).all()
    
    if not dreams:
        flash('You need to log some dreams first to see patterns!')
        return redirect(url_for('dream_log'))
    
    dreams_data = [{
        'date': dream.date.strftime('%Y-%m-%d'),
        'title': dream.title,
        'content': dream.content,
        'mood': dream.mood,
        'tags': dream.tags
    } for dream in dreams]
    
    if current_user.subscription_type == 'premium':
        patterns = analyze_dream_patterns(dreams_data)
    else:
        patterns = json.dumps({
            "Common Symbols and Themes": "Upgrade to premium for detailed symbol analysis!",
            "Emotional Patterns": "Basic mood tracking available. Premium users get detailed emotional pattern analysis.",
            "Life Events and Concerns": "Upgrade to premium to unlock deep insights about life patterns.",
            "Personal Growth Indicators": "Premium feature: Track your personal growth through dream patterns.",
            "Actionable Insights": "Get personalized recommendations with premium subscription."
        })
    
    return render_template('dream_patterns.html', dreams=dreams, patterns=patterns)