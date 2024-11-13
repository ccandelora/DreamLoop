import pytest
from models import User, Dream, Comment, DreamGroup, GroupMembership, ForumPost, ForumReply
from extensions import db
from datetime import datetime

def test_user_creation(app):
    """Test user model creation and password hashing."""
    with app.app_context():
        user = User(username='testuser', email='test@example.com')
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()
        
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.check_password('testpass')
        assert not user.check_password('wrongpass')
        assert user.subscription_type == 'free'
        assert user.monthly_ai_analysis_count == 0

def test_dream_creation(app, test_user):
    """Test dream model creation and relationships."""
    with app.app_context():
        dream = Dream(
            user_id=test_user.id,
            title='Test Dream',
            content='Test content',
            date=datetime.utcnow(),
            mood='happy',
            tags='test,dream',
            is_public=True,
            lucidity_level=3,
            sleep_quality=4,
            sleep_position='back'
        )
        db.session.add(dream)
        db.session.commit()
        
        retrieved_dream = Dream.query.filter_by(title='Test Dream').first()
        assert retrieved_dream is not None
        assert retrieved_dream.title == 'Test Dream'
        assert retrieved_dream.content == 'Test content'
        assert retrieved_dream.user_id == test_user.id
        assert retrieved_dream.mood == 'happy'
        assert retrieved_dream.tags == 'test,dream'
        assert retrieved_dream.is_public is True
        assert retrieved_dream.lucidity_level == 3
        
        user_dreams = test_user.dreams.all()
        assert dream in user_dreams

def test_comment_creation(app, test_user, test_dream):
    """Test comment model creation and relationships."""
    with app.app_context():
        comment = Comment(
            content='Test comment',
            user_id=test_user.id,
            dream_id=test_dream.id
        )
        db.session.add(comment)
        db.session.commit()
        
        retrieved_comment = Comment.query.filter_by(content='Test comment').first()
        assert retrieved_comment is not None
        assert retrieved_comment.content == 'Test comment'
        assert retrieved_comment.user_id == test_user.id
        assert retrieved_comment.dream_id == test_dream.id
        
        dream_comments = test_dream.comments.all()
        assert comment in dream_comments

def test_group_creation(app, test_user):
    """Test dream group model creation and relationships."""
    with app.app_context():
        group = DreamGroup(
            name='Test Group',
            description='Test description',
            created_by=test_user.id,
            created_at=datetime.utcnow()
        )
        db.session.add(group)
        db.session.commit()
        
        membership = GroupMembership(
            user_id=test_user.id,
            group_id=group.id,
            is_admin=True
        )
        db.session.add(membership)
        db.session.commit()
        
        retrieved_group = DreamGroup.query.filter_by(name='Test Group').first()
        assert retrieved_group is not None
        assert retrieved_group.name == 'Test Group'
        assert retrieved_group.description == 'Test description'
        assert retrieved_group.created_by == test_user.id
        
        # Test relationships
        assert test_user in retrieved_group.members
        membership = GroupMembership.query.filter_by(
            user_id=test_user.id, 
            group_id=retrieved_group.id
        ).first()
        assert membership is not None
        assert membership.is_admin is True

def test_forum_post_creation(app, test_user, test_group):
    """Test forum post model creation and relationships."""
    with app.app_context():
        post = ForumPost(
            title='Test Post',
            content='Test content',
            user_id=test_user.id,
            group_id=test_group.id,
            created_at=datetime.utcnow()
        )
        db.session.add(post)
        db.session.commit()
        
        retrieved_post = ForumPost.query.filter_by(title='Test Post').first()
        assert retrieved_post is not None
        assert retrieved_post.title == 'Test Post'
        assert retrieved_post.content == 'Test content'
        assert retrieved_post.user_id == test_user.id
        assert retrieved_post.group_id == test_group.id

def test_forum_reply_creation(app, test_user, test_forum_post):
    """Test forum reply model creation and relationships."""
    with app.app_context():
        reply = ForumReply(
            content='Test reply',
            user_id=test_user.id,
            post_id=test_forum_post.id,
            created_at=datetime.utcnow()
        )
        db.session.add(reply)
        db.session.commit()
        
        retrieved_reply = ForumReply.query.filter_by(content='Test reply').first()
        assert retrieved_reply is not None
        assert retrieved_reply.content == 'Test reply'
        assert retrieved_reply.user_id == test_user.id
        assert retrieved_reply.post_id == test_forum_post.id
        
        post_replies = test_forum_post.replies.all()
        assert reply in post_replies
