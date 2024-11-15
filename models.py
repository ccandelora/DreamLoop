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
    dreams = db.relationship('Dream', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    forum_posts = db.relationship('ForumPost', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    forum_replies = db.relationship('ForumReply', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    groups = db.relationship('DreamGroup', secondary='group_membership', backref=db.backref('members', lazy='dynamic'))
    activities = db.relationship('UserActivity', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, username=None, email=None, subscription_type='free'):
        self.username = username
        self.email = email
        self.subscription_type = subscription_type
        self.monthly_ai_analysis_count = 0
        self.last_analysis_reset = datetime.utcnow()
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class UserActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    activity_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    target_type = db.Column(db.String(50))  # e.g., 'dream', 'comment', 'group'
    target_id = db.Column(db.Integer)  # ID of the related object
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))  # IPv6 addresses can be up to 45 chars
    user_agent = db.Column(db.String(256))

    def __init__(self, user_id, activity_type, description=None, target_type=None, target_id=None, ip_address=None, user_agent=None):
        self.user_id = user_id
        self.activity_type = activity_type
        self.description = description
        self.target_type = target_type
        self.target_id = target_id
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.created_at = datetime.utcnow()

class Dream(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Added created_at column
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

    def __init__(self, user_id=None, title=None, content=None, is_public=False):
        self.user_id = user_id
        self.title = title
        self.content = content
        self.date = datetime.utcnow()
        self.created_at = datetime.utcnow()
        self.is_public = is_public

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    dream_id = db.Column(db.Integer, db.ForeignKey('dream.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, content=None, user_id=None, dream_id=None):
        self.content = content
        self.user_id = user_id
        self.dream_id = dream_id
        self.created_at = datetime.utcnow()

class DreamGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    forum_posts = db.relationship('ForumPost', backref='group', lazy='dynamic', cascade='all, delete-orphan')
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_groups')

    def __init__(self, name=None, description=None, created_by=None):
        self.name = name
        self.description = description
        self.created_by = created_by
        self.created_at = datetime.utcnow()

class GroupMembership(db.Model):
    __tablename__ = 'group_membership'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('dream_group.id'), primary_key=True)
    is_admin = db.Column(db.Boolean, default=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, user_id=None, group_id=None, is_admin=False):
        self.user_id = user_id
        self.group_id = group_id
        self.is_admin = is_admin
        self.joined_at = datetime.utcnow()

class ForumPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('dream_group.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    replies = db.relationship('ForumReply', backref='post', lazy='dynamic', cascade='all, delete-orphan')

    def __init__(self, title=None, content=None, user_id=None, group_id=None):
        self.title = title
        self.content = content
        self.user_id = user_id
        self.group_id = group_id
        self.created_at = datetime.utcnow()

class ForumReply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_post.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, content=None, user_id=None, post_id=None):
        self.content = content
        self.user_id = user_id
        self.post_id = post_id
        self.created_at = datetime.utcnow()
