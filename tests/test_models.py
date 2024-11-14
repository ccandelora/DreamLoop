import pytest
from models import User, Dream, Comment, DreamGroup, GroupMembership, ForumPost, ForumReply
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)

def test_user_creation(app, session):
    """Test user model creation and password hashing."""
    with app.app_context():
        try:
            user = User(username='testuser', email='test@example.com')
            user.set_password('testpass')
            session.add(user)
            session.commit()
            
            assert user.username == 'testuser'
            assert user.email == 'test@example.com'
            assert user.check_password('testpass')
            assert not user.check_password('wrongpass')
            assert user.subscription_type == 'free'
            assert user.monthly_ai_analysis_count == 0
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error in test_user_creation: {str(e)}")
            pytest.fail(f"Database error: {str(e)}")

def test_dream_creation(app, session, test_user):
    """Test dream model creation and relationships."""
    with app.app_context():
        try:
            dream = Dream(
                user_id=test_user.id,
                title='Test Dream',
                content='Test content'
            )
            dream.date = datetime.utcnow()
            dream.mood = 'happy'
            dream.tags = 'test,dream'
            dream.is_public = True
            dream.lucidity_level = 3
            dream.sleep_quality = 4
            dream.sleep_position = 'back'
            
            session.add(dream)
            session.commit()
            session.refresh(dream)
            
            # Verify dream was created correctly
            retrieved_dream = session.query(Dream).filter_by(title='Test Dream').first()
            assert retrieved_dream is not None
            assert retrieved_dream.title == 'Test Dream'
            assert retrieved_dream.content == 'Test content'
            assert retrieved_dream.user_id == test_user.id
            assert retrieved_dream.mood == 'happy'
            assert retrieved_dream.tags == 'test,dream'
            assert retrieved_dream.is_public is True
            assert retrieved_dream.lucidity_level == 3
            
            # Test relationship with user
            user_dreams = test_user.dreams.all()
            assert dream in user_dreams
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error in test_dream_creation: {str(e)}")
            pytest.fail(f"Database error: {str(e)}")

def test_comment_creation(app, session, test_user, test_dream):
    """Test comment model creation and relationships."""
    with app.app_context():
        try:
            comment = Comment(
                content='Test comment',
                user_id=test_user.id,
                dream_id=test_dream.id
            )
            session.add(comment)
            session.commit()
            session.refresh(comment)
            
            # Verify comment was created correctly
            retrieved_comment = session.query(Comment).filter_by(content='Test comment').first()
            assert retrieved_comment is not None
            assert retrieved_comment.content == 'Test comment'
            assert retrieved_comment.user_id == test_user.id
            assert retrieved_comment.dream_id == test_dream.id
            
            # Test relationship with dream
            dream_comments = test_dream.comments.all()
            assert comment in dream_comments
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error in test_comment_creation: {str(e)}")
            pytest.fail(f"Database error: {str(e)}")

def test_group_creation(app, session, test_user):
    """Test dream group model creation and relationships."""
    with app.app_context():
        try:
            group = DreamGroup(
                name='Test Group',
                description='Test description',
                created_by=test_user.id
            )
            session.add(group)
            session.commit()
            session.refresh(group)
            
            membership = GroupMembership(
                user_id=test_user.id,
                group_id=group.id,
                is_admin=True
            )
            session.add(membership)
            session.commit()
            session.refresh(membership)
            
            # Verify group was created correctly
            retrieved_group = session.query(DreamGroup).filter_by(name='Test Group').first()
            assert retrieved_group is not None
            assert retrieved_group.name == 'Test Group'
            assert retrieved_group.description == 'Test description'
            assert retrieved_group.created_by == test_user.id
            
            # Test relationships
            assert test_user in retrieved_group.members
            membership = session.query(GroupMembership).filter_by(
                user_id=test_user.id, 
                group_id=retrieved_group.id
            ).first()
            assert membership is not None
            assert membership.is_admin is True
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error in test_group_creation: {str(e)}")
            pytest.fail(f"Database error: {str(e)}")

def test_forum_post_creation(app, session, test_user, test_group):
    """Test forum post model creation and relationships."""
    with app.app_context():
        try:
            post = ForumPost(
                title='Test Post',
                content='Test content',
                user_id=test_user.id,
                group_id=test_group.id
            )
            session.add(post)
            session.commit()
            session.refresh(post)
            
            # Verify post was created correctly
            retrieved_post = session.query(ForumPost).filter_by(title='Test Post').first()
            assert retrieved_post is not None
            assert retrieved_post.title == 'Test Post'
            assert retrieved_post.content == 'Test content'
            assert retrieved_post.user_id == test_user.id
            assert retrieved_post.group_id == test_group.id
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error in test_forum_post_creation: {str(e)}")
            pytest.fail(f"Database error: {str(e)}")

def test_forum_reply_creation(app, session, test_user, test_forum_post):
    """Test forum reply model creation and relationships."""
    with app.app_context():
        try:
            reply = ForumReply(
                content='Test reply',
                user_id=test_user.id,
                post_id=test_forum_post.id
            )
            session.add(reply)
            session.commit()
            session.refresh(reply)
            
            # Verify reply was created correctly
            retrieved_reply = session.query(ForumReply).filter_by(content='Test reply').first()
            assert retrieved_reply is not None
            assert retrieved_reply.content == 'Test reply'
            assert retrieved_reply.user_id == test_user.id
            assert retrieved_reply.post_id == test_forum_post.id
            
            # Test relationship with post
            post_replies = test_forum_post.replies.all()
            assert reply in post_replies
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error in test_forum_reply_creation: {str(e)}")
            pytest.fail(f"Database error: {str(e)}")
