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
    is_moderator = db.Column(db.Boolean, default=False)
    
    # Relationships
    dreams = db.relationship('Dream', backref='user', lazy='dynamic')
    authored_comments = db.relationship('Comment', 
                             foreign_keys='Comment.user_id',
                             backref='author',
                             lazy='dynamic')
    moderated_comments = db.relationship('Comment',
                                     foreign_keys='Comment.moderated_by',
                                     backref='moderator',
                                     lazy='dynamic')
    forum_posts = db.relationship('ForumPost', backref='user', lazy='dynamic')
    forum_replies = db.relationship('ForumReply', backref='user', lazy='dynamic')
    groups = db.relationship('DreamGroup', secondary='group_membership', backref=db.backref('members', lazy='dynamic'))
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def can_moderate(self):
        return self.is_moderator

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
    
    # Moderation fields
    is_hidden = db.Column(db.Boolean, default=False)
    moderation_reason = db.Column(db.String(200), nullable=True)
    moderated_at = db.Column(db.DateTime, nullable=True)
    moderated_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Add relationship for replies
    replies = db.relationship(
        'Comment',
        backref=db.backref('parent', remote_side=[id]),
        cascade='all, delete-orphan',
        lazy='dynamic'
    )
    
    def hide(self, moderator, reason):
        """Hide a comment with moderation reason."""
        if not moderator.can_moderate():
            raise ValueError("User does not have moderator privileges")
            
        self.is_hidden = True
        self.moderation_reason = reason
        self.moderated_at = datetime.utcnow()
        self.moderated_by = moderator.id
        
        # Create a notification for the comment author
        notification = Notification(
            user_id=self.user_id,
            title="Your comment has been hidden",
            content=f"A moderator has hidden your comment. Reason: {reason}",
            type='moderation',
            reference_id=self.dream_id
        )
        db.session.add(notification)
        
        # If this is a parent comment, cascade hide to all replies
        if self.parent_id is None:
            for reply in self.replies:
                if not reply.is_hidden:
                    cascade_reason = f"Parent comment hidden: {reason}"
                    reply.is_hidden = True
                    reply.moderation_reason = cascade_reason
                    reply.moderated_at = datetime.utcnow()
                    reply.moderated_by = moderator.id
                    
                    reply_notification = Notification(
                        user_id=reply.user_id,
                        title="Your reply has been hidden",
                        content=f"Your reply has been hidden because the parent comment was hidden. Reason: {reason}",
                        type='moderation',
                        reference_id=self.dream_id
                    )
                    db.session.add(reply_notification)

    def unhide(self, moderator):
        """Restore a hidden comment."""
        if not moderator.can_moderate():
            raise ValueError("User does not have moderator privileges")
            
        self.is_hidden = False
        self.moderation_reason = None
        self.moderated_at = None
        self.moderated_by = None
        
        notification = Notification(
            user_id=self.user_id,
            title="Your comment has been restored",
            content="A moderator has restored your previously hidden comment.",
            type='moderation',
            reference_id=self.dream_id
        )
        db.session.add(notification)
        
        # If this is a parent comment, restore replies that were hidden due to parent
        if self.parent_id is None:
            for reply in self.replies:
                if reply.is_hidden and reply.moderation_reason and reply.moderation_reason.startswith("Parent comment hidden:"):
                    reply.is_hidden = False
                    reply.moderation_reason = None
                    reply.moderated_at = None
                    reply.moderated_by = None
                    
                    reply_notification = Notification(
                        user_id=reply.user_id,
                        title="Your reply has been restored",
                        content="Your reply has been restored because the parent comment was restored.",
                        type='moderation',
                        reference_id=self.dream_id
                    )
                    db.session.add(reply_notification)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    reference_id = db.Column(db.Integer)
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
