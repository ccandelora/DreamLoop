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

def seed_database():
    with app.app_context():
        # Clear existing data
        db.drop_all()
        db.create_all()
        
        print("Creating users...")
        users = []
        for i in range(100):
            is_premium = random.random() < 0.3  # 30% chance of being premium
            user = User(
                username=f"user_{i+1}",
                email=f"user{i+1}@example.com",
                subscription_type="premium" if is_premium else "free",
                subscription_end_date=datetime.utcnow() + timedelta(days=30) if is_premium else None,
                monthly_ai_analysis_count=random.randint(0, 3) if not is_premium else 0
            )
            user.set_password(f"password{i+1}")
            db.session.add(user)
            users.append(user)
        
        db.session.commit()
        print("Users created successfully!")

        print("Creating dream groups...")
        groups = []
        for theme in GROUP_THEMES:
            group = DreamGroup(
                name=f"{theme} Explorers",
                description=f"A group dedicated to exploring and understanding {theme.lower()}.",
                theme=theme
            )
            db.session.add(group)
            groups.append(group)
        
        db.session.commit()

        print("Adding group memberships...")
        for user in users:
            # Each user joins 1-3 random groups
            for group in random.sample(groups, random.randint(1, 3)):
                is_admin = random.random() < 0.2  # 20% chance of being admin
                membership = GroupMembership(
                    user_id=user.id,
                    group_id=group.id,
                    is_admin=is_admin
                )
                db.session.add(membership)
        
        db.session.commit()

        print("Creating dreams and comments...")
        all_dreams = []
        for user in users:
            # Create 3-10 dreams per user
            for _ in range(random.randint(3, 10)):
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
                    dream.dream_group_id = random.choice(groups).id
                
                db.session.add(dream)
                all_dreams.append(dream)
        
        db.session.commit()

        print("Adding comments to public dreams...")
        for dream in all_dreams:
            if dream.is_public:
                # Add 0-5 comments per public dream
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

        print("Creating forum posts and replies...")
        for group in groups:
            # Create 3-7 forum posts per group
            for _ in range(random.randint(3, 7)):
                author = random.choice([m.user for m in group.members])
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
                db.session.flush()

                # Add 2-8 replies per post
                for _ in range(random.randint(2, 8)):
                    replier = random.choice([m.user for m in group.members])
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

        db.session.commit()
        print("Database seeding completed successfully!")

if __name__ == "__main__":
    seed_database()
