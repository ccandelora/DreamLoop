from .extensions import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class Users(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    dreams = db.relationship('Dream', backref='author', lazy=True)
    group_memberships = db.relationship(
        'GroupMembership',
        back_populates='user',
        overlaps="groups,members"
    )
    groups = db.relationship(
        'DreamGroup',
        secondary='group_membership',
        back_populates='members',
        overlaps="group_memberships"
    )
    # Notifications relationship
    user_notifications = db.relationship(
        'Notification',
        foreign_keys='Notification.user_id',
        backref=db.backref('user', lazy=True),
        lazy=True
    )
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Notification(db.Model):
    __tablename__ = 'notification'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notification_type = db.Column(db.String(50))
    related_id = db.Column(db.Integer)

class Dream(db.Model):
    __tablename__ = 'dream'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_private = db.Column(db.Boolean, default=False)

class DreamGroup(db.Model):
    __tablename__ = 'dream_group'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    memberships = db.relationship(
        'GroupMembership',
        back_populates='group',
        overlaps="members"
    )
    members = db.relationship(
        'Users',
        secondary='group_membership',
        back_populates='groups',
        overlaps="memberships"
    )

class GroupMembership(db.Model):
    __tablename__ = 'group_membership'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('dream_group.id'), nullable=False)
    role = db.Column(db.String(20), default='member')
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship(
        'Users',
        back_populates='group_memberships',
        overlaps="groups,members"
    )
    group = db.relationship(
        'DreamGroup',
        back_populates='memberships',
        overlaps="members"
    )


