from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    subscription_type = db.Column(db.String(20), default='free')  # free, premium
    subscription_end_date = db.Column(db.DateTime)
    dreams = db.relationship('Dream', backref='author', lazy='dynamic')
    group_memberships = db.relationship('GroupMembership', backref='user', lazy='dynamic')
    forum_posts = db.relationship('ForumPost', backref='author', lazy='dynamic')
    monthly_ai_analysis_count = db.Column(db.Integer, default=0)
    last_analysis_reset = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def can_use_ai_analysis(self):
        if self.subscription_type == 'premium':
            return True
        # Free users get 3 analyses per month
        if self.last_analysis_reset is None or (datetime.utcnow() - self.last_analysis_reset).days >= 30:
            self.monthly_ai_analysis_count = 0
            self.last_analysis_reset = datetime.utcnow()
            db.session.commit()
        return self.monthly_ai_analysis_count < 3
        
    def increment_ai_analysis_count(self):
        if self.subscription_type != 'premium':
            self.monthly_ai_analysis_count += 1
            db.session.commit()

class Dream(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    title = db.Column(db.String(200))
    content = db.Column(db.Text, nullable=False)
    mood = db.Column(db.String(50))
    tags = db.Column(db.String(200))
    is_public = db.Column(db.Boolean, default=False)
    ai_analysis = db.Column(db.Text)
    comments = db.relationship('Comment', backref='dream', lazy='dynamic')
    dream_group_id = db.Column(db.Integer, db.ForeignKey('dream_group.id'), nullable=True)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dream_id = db.Column(db.Integer, db.ForeignKey('dream.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class DreamGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    theme = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    dreams = db.relationship('Dream', backref='dream_group', lazy='dynamic')
    members = db.relationship('GroupMembership', backref='dream_group', lazy='dynamic')
    forum_posts = db.relationship('ForumPost', backref='dream_group', lazy='dynamic')

class GroupMembership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('dream_group.id'), nullable=False)
    join_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)

class ForumPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('dream_group.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    replies = db.relationship('ForumReply', backref='post', lazy='dynamic')

class ForumReply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_post.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
