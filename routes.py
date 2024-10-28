from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import User, Dream, Comment
from ai_helper import analyze_dream, analyze_dream_patterns
from werkzeug.security import generate_password_hash
from add_sample_dreams import add_sample_dreams
import json

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dream_log'))
    return redirect(url_for('login'))

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
        dream = Dream()
        dream.title = request.form['title']
        dream.content = request.form['content']
        dream.mood = request.form['mood']
        dream.tags = request.form['tags']
        dream.is_public = bool(request.form.get('is_public'))
        dream.user_id = current_user.id
        
        # Get AI analysis
        dream.ai_analysis = analyze_dream(request.form['content'])
        
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

@app.route('/add_sample_dreams')
@login_required
def add_samples():
    add_sample_dreams()
    flash('Sample dreams added successfully!')
    return redirect(url_for('dream_patterns'))

@app.route('/dream/patterns')
@login_required
def dream_patterns():
    # Get user's dreams ordered by date
    dreams = Dream.query.filter_by(user_id=current_user.id).order_by(Dream.date.desc()).all()
    
    if not dreams:
        flash('You need to log some dreams first to see patterns!')
        return redirect(url_for('dream_log'))
    
    # Prepare dreams data for analysis
    dreams_data = [{
        'date': dream.date.strftime('%Y-%m-%d'),
        'title': dream.title,
        'content': dream.content,
        'mood': dream.mood,
        'tags': dream.tags
    } for dream in dreams]
    
    # Get pattern analysis and ensure it's valid JSON
    patterns = analyze_dream_patterns(dreams_data)
    
    return render_template('dream_patterns.html', dreams=dreams, patterns=patterns)
