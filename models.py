from extensions import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    subscription_type = db.Column(db.String(20), default='free')
    subscription_end_date = db.Column(db.DateTime)
    monthly_ai_analysis_count = db.Column(db.Integer, default=0)
    last_analysis_reset = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    dreams = db.relationship('Dream', backref='user', lazy='dynamic')
    comments = db.relationship('Comment', backref='user', lazy='dynamic')
    forum_posts = db.relationship('ForumPost', backref='user', lazy='dynamic')
    forum_replies = db.relationship('ForumReply', backref='user', lazy='dynamic')
    groups = db.relationship('DreamGroup', secondary='group_membership', backref=db.backref('members', lazy='dynamic'))
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Dream(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    mood = db.Column(db.String(50))
    sentiment_score = db.Column(db.Float, nullable=True)
    sentiment_magnitude = db.Column(db.Float, nullable=True)
    dominant_emotions = db.Column(db.String(200), nullable=True)
    lucidity_level = db.Column(db.Integer, nullable=True)
    tags = db.Column(db.String(200))
    is_public = db.Column(db.Boolean, default=False)
    is_anonymous = db.Column(db.Boolean, default=False)
    ai_analysis = db.Column(db.Text)
    
    # Sleep metrics
    sleep_duration = db.Column(db.Float, nullable=True)
    sleep_quality = db.Column(db.Integer, nullable=True)
    bed_time = db.Column(db.DateTime, nullable=True)
    wake_time = db.Column(db.DateTime, nullable=True)
    sleep_interruptions = db.Column(db.Integer, default=0)
    sleep_position = db.Column(db.String(50), nullable=True)
    
    # Relationships
    comments = db.relationship('Comment', backref='dream', lazy='dynamic', cascade='all, delete-orphan')

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    dream_id = db.Column(db.Integer, db.ForeignKey('dream.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    edited_at = db.Column(db.DateTime, nullable=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    
    # Add relationship for replies
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]),
                            cascade='all, delete-orphan', lazy='dynamic')
    
    def get_replies(self):
        """Get all replies for this comment ordered by creation date."""
        return Comment.query.filter_by(parent_id=self.id).order_by(Comment.created_at.asc()).all()

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'comment', 'reply', etc.
    reference_id = db.Column(db.Integer)  # ID of the related item (dream, comment, etc.)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)

class DreamGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    forum_posts = db.relationship('ForumPost', backref='group', lazy='dynamic', cascade='all, delete-orphan')

class GroupMembership(db.Model):
    __tablename__ = 'group_membership'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('dream_group.id'), primary_key=True)
    is_admin = db.Column(db.Boolean, default=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

class ForumPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('dream_group.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    replies = db.relationship('ForumReply', backref='post', lazy='dynamic', cascade='all, delete-orphan')

class ForumReply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_post.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
