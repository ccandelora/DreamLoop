from app import app, db
from models import User, Dream, Comment, DreamGroup, GroupMembership
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
import random
from ai_helper import analyze_dream

def create_users(num_users=100):
    """Create sample users with a mix of free and premium subscriptions."""
    users = []
    for i in range(num_users):
        username = f"user_{i+1}"
        email = f"user{i+1}@example.com"
        subscription_type = 'premium' if random.random() < 0.2 else 'free'
        
        user = User(
            username=username,
            email=email,
            subscription_type=subscription_type,
            monthly_ai_analysis_count=random.randint(0, 3),
            last_analysis_reset=datetime.utcnow()
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
    
    for user in users:
        num_dreams = random.randint(3, 10)
        for _ in range(num_dreams):
            title, content = random.choice(dream_templates)
            content = f"{content} {random.randint(1, 1000)}"  # Make content unique
            
            dream = Dream(
                user_id=user.id,
                title=title,
                content=content,
                date=datetime.utcnow() - timedelta(days=random.randint(0, 30)),
                mood=random.choice(moods),
                tags="flying,adventure,nature",
                is_public=random.random() < 0.7,
                ai_analysis=analyze_dream(content)
            )
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
            num_comments = random.randint(0, 5)
            for _ in range(num_comments):
                commenter = random.choice(users)
                comment = Comment(
                    content=random.choice(comment_templates),
                    user_id=commenter.id,
                    dream_id=dream.id,
                    created_at=datetime.utcnow() - timedelta(hours=random.randint(1, 24))
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
        ("Prophetic Dreams", "Discuss potentially prophetic or precognitive dreams."),
        ("Nature Dreams", "Share dreams involving nature and wildlife.")
    ]
    
    for name, description in group_templates:
        creator = random.choice(users)
        group = DreamGroup(
            name=name,
            description=description,
            created_by=creator.id,
            created_at=datetime.utcnow() - timedelta(days=random.randint(0, 30))
        )
        groups.append(group)
        
    try:
        db.session.add_all(groups)
        db.session.commit()
    except Exception as e:
        print(f"Error creating groups: {str(e)}")
        db.session.rollback()
        return []
        
    return groups

def create_memberships(users, groups):
    """Create sample group memberships."""
    memberships = []
    
    for group in groups:
        # Add creator as admin
        creator_membership = GroupMembership(
            user_id=group.created_by,
            group_id=group.id,
            is_admin=True,
            joined_at=group.created_at
        )
        memberships.append(creator_membership)
        
        # Add random members
        num_members = random.randint(5, 15)
        potential_members = [u for u in users if u.id != group.created_by]
        selected_members = random.sample(potential_members, min(num_members, len(potential_members)))
        
        for user in selected_members:
            membership = GroupMembership(
                user_id=user.id,
                group_id=group.id,
                is_admin=False,
                joined_at=datetime.utcnow() - timedelta(days=random.randint(0, 30))
            )
            memberships.append(membership)
            
    db.session.add_all(memberships)
    db.session.commit()
    return memberships

def seed_database():
    """Main function to seed the database."""
    print("Starting database seeding...")
    
    # Clear existing data
    db.session.query(GroupMembership).delete()
    db.session.query(Comment).delete()
    db.session.query(Dream).delete()
    db.session.query(DreamGroup).delete()
    db.session.query(User).delete()
    db.session.commit()
    
    try:
        # Create data in order of dependencies
        print("Creating users...")
        users = create_users(100)
        
        print("Creating dreams...")
        dreams = create_dreams(users)
        
        print("Creating comments...")
        comments = create_comments(users, dreams)
        
        print("Creating groups...")
        groups = create_groups(users)
        
        print("Creating group memberships...")
        memberships = create_memberships(users, groups)
        
        print("Database seeding completed successfully!")
        
    except Exception as e:
        print(f"Error during database seeding: {str(e)}")
        db.session.rollback()
        return False
    
    return True

if __name__ == "__main__":
    with app.app_context():
        seed_database()
