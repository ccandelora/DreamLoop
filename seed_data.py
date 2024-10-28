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
        return None

def seed_database():
    with app.app_context():
        print("Clearing existing data...")
        try:
            # Clear existing data in reverse order of dependencies
            ForumReply.query.delete()
            ForumPost.query.delete()
            Comment.query.delete()
            GroupMembership.query.delete()
            Dream.query.delete()
            DreamGroup.query.delete()
            User.query.delete()
            db.session.commit()
            print("Existing data cleared successfully!")
        except Exception as e:
            print(f"Error clearing data: {str(e)}")
            db.session.rollback()
            return

        print("\nCreating known test user...")
        test_user = create_user(
            username="testuser",
            email="testuser@example.com",
            password="password123",
            subscription_type="premium"
        )
        if not test_user:
            print("Failed to create test user!")
            return

        print("\nCreating random users...")
        users = []
        if test_user:
            users.append(test_user)

        for i in range(99):  # Create 99 more users for a total of 100
            is_premium = random.random() < 0.3  # 30% chance of being premium
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

        print("\nCreating dream groups...")
        groups = []
        for theme in GROUP_THEMES:
            try:
                group = DreamGroup(
                    name=f"{theme} Explorers",
                    description=f"A group dedicated to exploring and understanding {theme.lower()}.",
                    theme=theme
                )
                db.session.add(group)
                groups.append(group)
            except Exception as e:
                print(f"Error creating group {theme}: {str(e)}")
                continue

        try:
            db.session.commit()
            print(f"Created {len(groups)} dream groups")
        except Exception as e:
            print(f"Error committing groups: {str(e)}")
            db.session.rollback()
            return

        print("\nAdding group memberships...")
        membership_count = 0
        for user in users:
            # Each user joins 1-3 random groups
            for group in random.sample(groups, random.randint(1, 3)):
                try:
                    is_admin = random.random() < 0.2  # 20% chance of being admin
                    membership = GroupMembership(
                        user_id=user.id,
                        group_id=group.id,
                        is_admin=is_admin
                    )
                    db.session.add(membership)
                    membership_count += 1
                except Exception as e:
                    print(f"Error creating membership for user {user.username}: {str(e)}")
                    continue

        try:
            db.session.commit()
            print(f"Created {membership_count} group memberships")
        except Exception as e:
            print(f"Error committing memberships: {str(e)}")
            db.session.rollback()
            return

        print("\nCreating dreams and comments...")
        dream_count = 0
        comment_count = 0
        for user in users:
            # Create 3-10 dreams per user
            for _ in range(random.randint(3, 10)):
                try:
                    dream = Dream(
                        user_id=user.id,
                        title=f"{random.choice(THEMES).title()} Dream",
                        content=generate_dream_content(),
                        mood=random.choice(MOODS),
                        tags=",".join(random.sample(THEMES, random.randint(1, 3))),
                        is_public=random.random() < 0.7,  # 70% chance of being public
                        date=datetime.utcnow() - timedelta(days=random.randint(0, 90)),
                        ai_analysis=create_ai_analysis()
                    )
                    
                    # Randomly assign some dreams to groups
                    if random.random() < 0.3:  # 30% chance
                        group = random.choice(groups)
                        if user in [m.user for m in group.members]:
                            dream.dream_group_id = group.id
                    
                    db.session.add(dream)
                    dream_count += 1

                    # Add 0-5 comments per public dream
                    if dream.is_public:
                        for _ in range(random.randint(0, 5)):
                            commenter = random.choice(users)
                            if commenter.id != dream.user_id:
                                comment = Comment(
                                    dream_id=dream.id,
                                    author_id=commenter.id,
                                    content=random.choice([
                                        "Fascinating dream! Thanks for sharing.",
                                        "I've had similar experiences in my dreams.",
                                        "The symbolism here is really interesting.",
                                        "This reminds me of a recurring dream I have.",
                                        "Have you considered what the symbols might mean?",
                                        "The emotions in this dream are very powerful."
                                    ]),
                                    date=dream.date + timedelta(hours=random.randint(1, 48))
                                )
                                db.session.add(comment)
                                comment_count += 1
                except Exception as e:
                    print(f"Error creating dream/comments for user {user.username}: {str(e)}")
                    continue

        try:
            db.session.commit()
            print(f"Created {dream_count} dreams and {comment_count} comments")
        except Exception as e:
            print(f"Error committing dreams and comments: {str(e)}")
            db.session.rollback()
            return

        print("\nCreating forum posts and replies...")
        post_count = 0
        reply_count = 0
        for group in groups:
            # Create 3-7 forum posts per group
            for _ in range(random.randint(3, 7)):
                try:
                    group_members = [m.user for m in group.members]
                    if not group_members:
                        continue
                        
                    author = random.choice(group_members)
                    post = ForumPost(
                        title=random.choice([
                            "Interpreting recurring symbols",
                            "Dream journaling techniques",
                            "Understanding dream patterns",
                            "Shared dream experiences",
                            "Dream analysis methods",
                            "Lucid dreaming tips"
                        ]),
                        content=f"Let's discuss our experiences with {group.theme.lower()} and share insights.",
                        author_id=author.id,
                        group_id=group.id,
                        created_at=datetime.utcnow() - timedelta(days=random.randint(0, 30))
                    )
                    db.session.add(post)
                    post_count += 1

                    # Add 2-8 replies per post
                    for _ in range(random.randint(2, 8)):
                        if not group_members:
                            continue
                        replier = random.choice(group_members)
                        reply = ForumReply(
                            content=random.choice([
                                "Great insights! Thanks for sharing.",
                                "I've had similar experiences.",
                                "This is really helpful information.",
                                "Interesting perspective on this topic.",
                                "Would love to hear more about this.",
                                "Thanks for starting this discussion."
                            ]),
                            author_id=replier.id,
                            post_id=post.id,
                            created_at=post.created_at + timedelta(hours=random.randint(1, 72))
                        )
                        db.session.add(reply)
                        reply_count += 1
                except Exception as e:
                    print(f"Error creating forum post/replies for group {group.name}: {str(e)}")
                    continue

        try:
            db.session.commit()
            print(f"Created {post_count} forum posts and {reply_count} replies")
            print("\nDatabase seeding completed successfully!")
        except Exception as e:
            print(f"Error committing forum posts and replies: {str(e)}")
            db.session.rollback()
            return

if __name__ == "__main__":
    seed_database()
