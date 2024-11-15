from flask import Flask
from extensions import db
from models import User, Dream, Comment, DreamGroup, GroupMembership
from datetime import datetime, timedelta
import random
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """Create a minimal Flask app for database initialization."""
    app = Flask(__name__)
    
    # Configure database URL
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        db_url = f"postgresql://{os.environ['PGUSER']}:{os.environ['PGPASSWORD']}@{os.environ['PGHOST']}:{os.environ['PGPORT']}/{os.environ['PGDATABASE']}"
    
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    db.init_app(app)
    return app

def create_users(num_users=5):
    """Create sample users with a mix of free and premium subscriptions."""
    users = []
    for i in range(num_users):
        username = f"user_{i+1}"
        email = f"user{i+1}@example.com"
        subscription_type = 'premium' if random.random() < 0.2 else 'free'

        user = User(
            username=username,
            email=email,
            subscription_type=subscription_type
        )
        user.set_password('password123')

        if subscription_type == 'premium':
            user.subscription_end_date = datetime.utcnow() + timedelta(days=30)

        users.append(user)

    db.session.add_all(users)
    db.session.commit()
    return users

def create_dreams(users):
    """Create sample dreams for each user."""
    dreams = []
    dream_templates = [
        ("Flying Dream", "I was flying over the city, feeling completely free."),
        ("Chase Dream", "Someone was chasing me through dark alleys."),
        ("Water Dream", "I was swimming in a crystal clear ocean."),
        ("Forest Dream", "Walking through an enchanted forest with glowing trees."),
        ("Space Dream", "Floating in space, watching Earth from above.")
    ]

    moods = ['happy', 'scared', 'peaceful', 'anxious', 'excited']
    tags = ['flying', 'adventure', 'nature', 'space', 'water', 'chase', 'forest']

    for user in users:
        num_dreams = random.randint(3, 5)
        for _ in range(num_dreams):
            title, content = random.choice(dream_templates)
            content = f"{content} {random.randint(1, 50)}"  # Make content unique
            selected_tags = ','.join(random.sample(tags, random.randint(1, 3)))

            dream = Dream(
                user_id=user.id,
                title=title,
                content=content
            )
            # Set additional attributes after creation
            dream.mood = random.choice(moods)
            dream.tags = selected_tags
            dream.is_public = random.random() < 0.7
            dream.is_anonymous = random.random() < 0.3
            dream.sentiment_score = random.uniform(-1, 1)
            dream.sentiment_magnitude = random.uniform(0, 2)
            dream.lucidity_level = random.randint(1, 5)
            dream.sleep_quality = random.randint(1, 10)
            dream.sleep_duration = random.uniform(4, 10)
            dream.sleep_interruptions = random.randint(0, 3)
            dreams.append(dream)

    db.session.add_all(dreams)
    db.session.commit()
    return dreams

def create_comments(users, dreams):
    """Create sample comments on dreams."""
    comments = []
    comment_templates = [
        "This reminds me of a similar dream I had!",
        "The symbolism here is fascinating.",
        "Have you experienced this dream before?",
        "I can relate to this feeling.",
        "What do you think triggered this dream?"
    ]

    for dream in dreams:
        if dream.is_public:
            num_comments = random.randint(0, 3)
            for _ in range(num_comments):
                commenter = random.choice([u for u in users if u.id != dream.user_id])
                comment = Comment(
                    content=random.choice(comment_templates),
                    user_id=commenter.id,
                    dream_id=dream.id
                )
                comments.append(comment)

    db.session.add_all(comments)
    db.session.commit()
    return comments

def create_groups(users):
    """Create sample dream groups."""
    groups = []
    group_templates = [
        ("Lucid Dreams Explorers", "A group dedicated to exploring and understanding lucid dreams."),
        ("Nightmare Support", "A safe space to discuss and cope with nightmares."),
        ("Dream Interpreters", "Share and interpret the symbolism in your dreams."),
        ("Flying Dreams", "For those who experience flying in their dreams."),
        ("Prophetic Dreams", "Discuss potentially prophetic or precognitive dreams.")
    ]

    for name, description in group_templates:
        creator = random.choice(users)
        group = DreamGroup(
            name=name,
            description=description,
            created_by=creator.id
        )
        groups.append(group)

    db.session.add_all(groups)
    db.session.commit()
    return groups

def create_memberships(users, groups):
    """Create sample group memberships."""
    memberships = []

    for group in groups:
        # Add creator as admin
        creator_membership = GroupMembership(
            user_id=group.created_by,
            group_id=group.id,
            is_admin=True
        )
        memberships.append(creator_membership)

        # Add random members
        num_members = random.randint(2, 4)
        potential_members = [u for u in users if u.id != group.created_by]
        selected_members = random.sample(potential_members, min(num_members, len(potential_members)))

        for user in selected_members:
            membership = GroupMembership(
                user_id=user.id,
                group_id=group.id,
                is_admin=False
            )
            memberships.append(membership)

    db.session.add_all(memberships)
    db.session.commit()
    return memberships

def seed_database():
    """Main function to seed the database with sample data."""
    print("Starting database seeding...")

    try:
        # Clear existing data
        db.session.query(GroupMembership).delete()
        db.session.query(Comment).delete()
        db.session.query(Dream).delete()
        db.session.query(DreamGroup).delete()
        db.session.query(User).delete()
        db.session.commit()

        # Create data in order of dependencies
        print("Creating users...")
        users = create_users(5)
        print(f"Created {len(users)} users")

        print("Creating dreams...")
        dreams = create_dreams(users)
        print(f"Created {len(dreams)} dreams")

        print("Creating comments...")
        comments = create_comments(users, dreams)
        print(f"Created {len(comments)} comments")

        print("Creating groups...")
        groups = create_groups(users)
        print(f"Created {len(groups)} groups")

        print("Creating group memberships...")
        memberships = create_memberships(users, groups)
        print(f"Created {len(memberships)} group memberships")

        print("Database seeding completed successfully!")
        return True

    except Exception as e:
        print(f"Error during database seeding: {str(e)}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        success = seed_database()
        if not success:
            exit(1)
