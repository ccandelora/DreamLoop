from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import User, Dream, Comment
from ai_helper import analyze_dream
from werkzeug.security import generate_password_hash

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
            
        user = User(
            username=request.form['username'],
            email=request.form['email']
        )
        user.set_password(request.form['password'])
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('dream_log'))
    return render_template('register.html')

@app.route('/dream/new', methods=['GET', 'POST'])
@login_required
def dream_log():
    if request.method == 'POST':
        dream = Dream(
            title=request.form['title'],
            content=request.form['content'],
            mood=request.form['mood'],
            tags=request.form['tags'],
            is_public=bool(request.form.get('is_public')),
            user_id=current_user.id
        )
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
        
    comment = Comment(
        content=request.form['content'],
        dream_id=dream_id,
        author_id=current_user.id
    )
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('dream_view', dream_id=dream_id))
