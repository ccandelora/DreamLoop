from app import app, db
from models import User, Dream, Comment, DreamGroup, GroupMembership, ForumPost, ForumReply
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
import random
import json

# Sample data for dream generation
THEMES = [
    "flying", "falling", "chase", "test-taking", "being late", "supernatural",
    "adventure", "childhood", "family", "work", "romance", "nature"
]

MOODS = ["happy", "sad", "scared", "peaceful", "anxious", "excited"]

DREAM_TEMPLATES = [
    "I was {action} in {location}. {detail}",
    "Found myself {action}. {detail}",
    "Had a dream about {subject}. {detail}",
    "Was with {subject} when suddenly {action}. {detail}"
]

ACTIONS = [
    "flying", "running", "swimming", "exploring", "searching", "hiding",
    "dancing", "climbing", "falling", "discovering", "meeting someone",
    "trying to escape"
]

LOCATIONS = [
    "a mysterious forest", "an ancient city", "my childhood home",
    "a futuristic metropolis", "underwater ruins", "a mountain peak",
    "a magical garden", "a maze-like building", "outer space",
    "a desert oasis"
]

SUBJECTS = [
    "an old friend", "a mystical creature", "my family",
    "a talking animal", "a famous person", "a stranger",
    "my younger self", "a wise teacher", "a group of people"
]

DETAILS = [
    "The colors were incredibly vivid.",
    "Everything felt so real and meaningful.",
    "Time seemed to move differently.",
    "I had a strong feeling of déjà vu.",
    "The atmosphere was surreal.",
    "I felt completely transformed.",
    "The experience was both frightening and exciting.",
    "I woke up with a profound sense of insight.",
    "The symbolism was very clear.",
    "It left me with many questions."
]

GROUP_THEMES = [
    "Lucid Dreams", "Nightmares", "Flying Dreams", "Adventure",
    "Spiritual", "Recurring Dreams", "Prophetic Dreams", "Nature Dreams"
]

def generate_dream_content():
    template = random.choice(DREAM_TEMPLATES)
    return template.format(
        action=random.choice(ACTIONS),
        location=random.choice(LOCATIONS),
        subject=random.choice(SUBJECTS),
        detail=random.choice(DETAILS)
    )

def create_ai_analysis():
    return json.dumps({
        "symbols": "Analysis of dream symbols and their meanings in context.",
        "interpretation": "Overall interpretation of the dream narrative.",
        "emotions": "Analysis of emotional elements present in the dream.",
        "guidance": "Suggestions for personal growth based on dream content."
    })

def create_user(username, email, password, subscription_type="free", is_admin=False):
    """Helper function to create a user with proper error handling"""
    try:
        # Check for existing user
        if User.query.filter_by(username=username).first():
            print(f"Warning: Username {username} already exists, skipping...")
            return None
        if User.query.filter_by(email=email).first():
            print(f"Warning: Email {email} already exists, skipping...")
            return None
            
        user = User()
        user.username = username
        user.email = email
        user.set_password(password)
        user.subscription_type = subscription_type
        if subscription_type == "premium":
            user.subscription_end_date = datetime.utcnow() + timedelta(days=30)
        
        db.session.add(user)
        db.session.flush()  # Get the ID without committing
        print(f"Created user: {username} (ID: {user.id})")
        return user
    except Exception as e:
        print(f"Error creating user {username}: {str(e)}")
        db.session.rollback()
        return None

def create_dream(user_id, group_members_map=None):
    """Helper function to create a dream with proper error handling"""
    try:
        dream = Dream()
        dream.user_id = user_id
        dream.title = f"{random.choice(THEMES).title()} Dream"
        dream.content = generate_dream_content()
        dream.mood = random.choice(MOODS)
        dream.tags = ",".join(random.sample(THEMES, random.randint(1, 3)))
        dream.is_public = random.random() < 0.7  # 70% chance of being public
        dream.date = datetime.utcnow() - timedelta(days=random.randint(0, 90))
        dream.ai_analysis = create_ai_analysis()
        
        # Randomly assign to group if user is a member
        if group_members_map and random.random() < 0.3:  # 30% chance
            user_groups = group_members_map.get(user_id, [])
            if user_groups:
                dream.dream_group_id = random.choice(user_groups)
        
        db.session.add(dream)
        db.session.flush()  # Get the ID without committing
        return dream
    except Exception as e:
        print(f"Error creating dream for user {user_id}: {str(e)}")
        return None

def create_comment(dream_id, author_id, dream_date):
    """Helper function to create a comment with proper error handling"""
    try:
        if not dream_id or not author_id:
            print(f"Skipping comment creation - Invalid dream_id: {dream_id} or author_id: {author_id}")
            return None
            
        comment = Comment()
        comment.dream_id = dream_id
        comment.author_id = author_id
        comment.content = random.choice([
            "Fascinating dream! Thanks for sharing.",
            "I've had similar experiences in my dreams.",
            "The symbolism here is really interesting.",
            "This reminds me of a recurring dream I have.",
            "Have you considered what the symbols might mean?",
            "The emotions in this dream are very powerful."
        ])
        comment.date = dream_date + timedelta(hours=random.randint(1, 48))
        
        db.session.add(comment)
        db.session.flush()  # Get the ID without committing
        return comment
    except Exception as e:
        print(f"Error creating comment for dream {dream_id}: {str(e)}")
        return None

def seed_database():
    with app.app_context():
        print("\n=== Starting Database Seeding ===")
        
        # Step 1: Clear existing data
        print("\n--- Clearing existing data ---")
        try:
            tables = [ForumReply, ForumPost, Comment, GroupMembership, Dream, DreamGroup, User]
            for table in tables:
                count = table.query.delete()
                print(f"Deleted {count} records from {table.__name__}")
            db.session.commit()
            print("Successfully cleared all existing data")
        except Exception as e:
            print(f"Error clearing data: {str(e)}")
            db.session.rollback()
            return

        # Step 2: Create users
        print("\n--- Creating users ---")
        users = []
        test_user = create_user(
            username="testuser",
            email="testuser@example.com",
            password="password123",
            subscription_type="premium"
        )
        if test_user:
            users.append(test_user)
            print("Created test user successfully")
        
        for i in range(99):
            is_premium = random.random() < 0.3
            user = create_user(
                username=f"user_{i+1}",
                email=f"user{i+1}@example.com",
                password=f"password{i+1}",
                subscription_type="premium" if is_premium else "free"
            )
            if user:
                users.append(user)
                
        try:
            db.session.commit()
            print(f"Successfully created {len(users)} users")
        except Exception as e:
            print(f"Error committing users: {str(e)}")
            db.session.rollback()
            return

        # Step 3: Create dream groups
        print("\n--- Creating dream groups ---")
        groups = []
        group_members_map = {}  # user_id -> list of group_ids
        
        for theme in GROUP_THEMES:
            try:
                group = DreamGroup()
                group.name = f"{theme} Explorers"
                group.description = f"A group dedicated to exploring and understanding {theme.lower()}."
                group.theme = theme
                db.session.add(group)
                db.session.flush()
                groups.append(group)
                
                # Create memberships
                for user in users:
                    if random.random() < 0.3:  # 30% chance to join
                        membership = GroupMembership()
                        membership.user_id = user.id
                        membership.group_id = group.id
                        membership.is_admin = random.random() < 0.2
                        db.session.add(membership)
                        
                        # Update membership map
                        if user.id not in group_members_map:
                            group_members_map[user.id] = []
                        group_members_map[user.id].append(group.id)
                        
            except Exception as e:
                print(f"Error creating group {theme}: {str(e)}")
                continue
                
        try:
            db.session.commit()
            print(f"Created {len(groups)} groups and their memberships")
        except Exception as e:
            print(f"Error committing groups: {str(e)}")
            db.session.rollback()
            return

        # Step 4: Create dreams (in batches)
        print("\n--- Creating dreams ---")
        all_dreams = []
        batch_size = 50
        dreams_created = 0
        
        for user in users:
            user_dreams = []
            for _ in range(random.randint(3, 10)):
                dream = create_dream(user.id, group_members_map)
                if dream:
                    user_dreams.append(dream)
                    dreams_created += 1
                
                # Commit in batches
                if len(user_dreams) >= batch_size:
                    try:
                        db.session.commit()
                        all_dreams.extend(user_dreams)
                        print(f"Committed batch of {len(user_dreams)} dreams")
                        user_dreams = []
                    except Exception as e:
                        print(f"Error committing dream batch: {str(e)}")
                        db.session.rollback()
                        continue
            
            # Commit remaining dreams
            if user_dreams:
                try:
                    db.session.commit()
                    all_dreams.extend(user_dreams)
                    print(f"Committed final batch of {len(user_dreams)} dreams for user")
                except Exception as e:
                    print(f"Error committing final dream batch: {str(e)}")
                    db.session.rollback()
                    continue
                    
        print(f"Successfully created {dreams_created} dreams")

        # Step 5: Create comments (in separate transaction)
        print("\n--- Creating comments ---")
        comments_created = 0
        
        for dream in all_dreams:
            if not dream.is_public:
                continue
                
            # Add 0-5 comments per public dream
            for _ in range(random.randint(0, 5)):
                commenter = random.choice(users)
                if commenter.id == dream.user_id:
                    continue
                    
                comment = create_comment(dream.id, commenter.id, dream.date)
                if comment:
                    comments_created += 1
                    
                # Commit every 100 comments
                if comments_created % 100 == 0:
                    try:
                        db.session.commit()
                        print(f"Committed batch of 100 comments (Total: {comments_created})")
                    except Exception as e:
                        print(f"Error committing comment batch: {str(e)}")
                        db.session.rollback()
                        continue
        
        # Commit remaining comments
        try:
            db.session.commit()
            print(f"Successfully created {comments_created} comments")
        except Exception as e:
            print(f"Error committing final comments: {str(e)}")
            db.session.rollback()
            return

        print("\n=== Database seeding completed successfully! ===")
        print(f"Created:\n- {len(users)} users\n- {len(groups)} groups\n- {dreams_created} dreams\n- {comments_created} comments")

if __name__ == "__main__":
    seed_database()
