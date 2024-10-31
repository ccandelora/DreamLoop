from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

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
    dreams = db.relationship('Dream', backref='author', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    forum_posts = db.relationship('ForumPost', backref='author', lazy='dynamic', foreign_keys='ForumPost.author_id')
    forum_replies = db.relationship('ForumReply', backref='author', lazy='dynamic')
    groups = db.relationship('DreamGroup', secondary='group_membership', backref=db.backref('members', lazy='dynamic'))
    
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
    tags = db.Column(db.String(200))
    is_public = db.Column(db.Boolean, default=False)
    is_anonymous = db.Column(db.Boolean, default=False)
    ai_analysis = db.Column(db.Text)
    comments = db.relationship('Comment', backref='dream', lazy='dynamic', cascade='all, delete-orphan')

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    dream_id = db.Column(db.Integer, db.ForeignKey('dream.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_comment_dream_id', 'dream_id'),
        db.Index('idx_comment_user_id', 'user_id')
    )

class DreamGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    forum_posts = db.relationship('ForumPost', backref='group', lazy='dynamic', cascade='all, delete-orphan')
    
    __table_args__ = (
        db.Index('idx_dreamgroup_created_by', 'created_by'),
    )

class GroupMembership(db.Model):
    __tablename__ = 'group_membership'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('dream_group.id'), primary_key=True)
    is_admin = db.Column(db.Boolean, default=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_groupmembership_user_group', 'user_id', 'group_id'),
    )

class ForumPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('dream_group.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    replies = db.relationship('ForumReply', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    
    __table_args__ = (
        db.Index('idx_forumpost_author_id', 'author_id'),
        db.Index('idx_forumpost_group_id', 'group_id'),
        db.Index('idx_forumpost_created_at', 'created_at')
    )

class ForumReply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_post.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_forumreply_post_id', 'post_id'),
        db.Index('idx_forumreply_user_id', 'user_id'),
        db.Index('idx_forumreply_created_at', 'created_at')
    )
