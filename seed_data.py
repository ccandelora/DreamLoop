from app import app, db
from models import User, Dream, Comment, DreamGroup, GroupMembership, ForumPost, ForumReply
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
import random
import json
import lorem
from datetime import time

def generate_dream_content():
    """Generate rich dream narrative with 200-500 words"""
    paragraphs = lorem.paragraphs(3, 6)
    return paragraphs

def generate_dream_symbols():
    """Generate a list of common dream symbols"""
    symbols = [
        "water", "flying", "falling", "teeth", "house", "door", "key", "mountain",
        "bridge", "snake", "bird", "tree", "fire", "clock", "mirror", "stairs",
        "school", "car", "train", "ocean", "moon", "sun", "storm", "garden",
        "child", "elder", "animal", "book", "phone", "computer", "forest", "city"
    ]
    return random.sample(symbols, random.randint(2, 6))

def generate_archetypes():
    """Generate a list of Jungian archetypes"""
    archetypes = [
        "Hero", "Shadow", "Anima", "Animus", "Mentor", "Trickster", "Child",
        "Great Mother", "Wise Old Man", "Explorer", "Creator", "Ruler", "Sage",
        "Innocent", "Magician", "Caregiver", "Everyman", "Lover", "Jester", "Outlaw"
    ]
    return random.sample(archetypes, random.randint(1, 4))

def generate_environmental_factors():
    """Generate environmental factors that might affect dreams"""
    factors = {
        "stress_level": random.randint(1, 5),
        "exercise": random.choice([True, False]),
        "caffeine": random.choice([True, False]),
        "screen_time": random.randint(0, 5),
        "meditation": random.choice([True, False]),
        "room_temperature": round(random.uniform(18.0, 24.0), 1),
        "noise_level": random.choice(["quiet", "moderate", "noisy"]),
        "sleep_position": random.choice(["back", "side", "stomach"])
    }
    return json.dumps(factors)

def generate_recurring_elements():
    """Generate recurring elements in dreams"""
    elements = [
        "chase sequence", "being late", "lost in familiar place", "unprepared for test",
        "flying sensation", "falling sensation", "meeting deceased relative",
        "supernatural abilities", "being trapped", "discovering new rooms",
        "time travel", "transformation", "parallel universe", "underwater breathing"
    ]
    return json.dumps(random.sample(elements, random.randint(2, 5)))

def create_sample_data():
    with app.app_context():
        print("Starting data seeding...")
        
        # Create users
        users = []
        for i in range(100):
            subscription = random.choice(['free'] * 7 + ['premium'] * 3)  # 70% free, 30% premium
            user = User(
                username=f"dreamer{i+1}",
                email=f"dreamer{i+1}@dreamloop.com",
                subscription_type=subscription,
                subscription_end_date=(datetime.utcnow() + timedelta(days=365)) if subscription == 'premium' else None,
                monthly_ai_analysis_count=random.randint(0, 3) if subscription == 'free' else 0
            )
            user.set_password(f"password{i+1}")
            db.session.add(user)
            users.append(user)
        
        db.session.commit()
        print(f"Created {len(users)} users")

        # Create dreams for each user
        moods = ["happy", "sad", "scared", "peaceful", "anxious", "excited", "confused", "nostalgic"]
        total_dreams = 0
        
        for user in users:
            dream_count = random.randint(3, 10)
            for _ in range(dream_count):
                # Generate base dream data
                is_lucid = random.random() < 0.3  # 30% chance of lucid dream
                sleep_quality = random.randint(1, 5)
                clarity = random.randint(1, 5)
                emotional_tone = round(random.uniform(-1.0, 1.0), 2)
                
                # Create dream entry
                dream = Dream(
                    user_id=user.id,
                    title=lorem.sentence()[:100],
                    content=generate_dream_content(),
                    date=datetime.utcnow() - timedelta(days=random.randint(0, 365)),
                    mood=random.choice(moods),
                    tags=",".join(generate_dream_symbols()),
                    is_public=random.random() < 0.4,  # 40% public
                    is_anonymous=random.random() < 0.2,  # 20% anonymous
                    lucidity_level=random.randint(3, 5) if is_lucid else random.randint(0, 2),
                    sleep_quality=sleep_quality,
                    dream_clarity=clarity,
                    recurring_elements=generate_recurring_elements(),
                    emotional_tone=emotional_tone,
                    dream_symbols=json.dumps(generate_dream_symbols()),
                    dream_archetypes=json.dumps(generate_archetypes()),
                    sleep_duration=round(random.uniform(5.0, 9.0), 1),
                    bedtime=time(hour=random.randint(21, 23), minute=random.randint(0, 59)),
                    environmental_factors=generate_environmental_factors()
                )
                db.session.add(dream)
                total_dreams += 1
                
                # Add comments to public dreams
                if dream.is_public:
                    comment_count = random.randint(0, 5)
                    for _ in range(comment_count):
                        commenter = random.choice(users)
                        comment = Comment(
                            content=lorem.sentence(),
                            user_id=commenter.id,
                            dream_id=dream.id,
                            created_at=dream.date + timedelta(days=random.randint(1, 30))
                        )
                        db.session.add(comment)
        
        db.session.commit()
        print(f"Created {total_dreams} dreams with rich metadata")

        # Create dream groups
        groups = []
        group_themes = [
            "Lucid Dreamers Circle", "Dream Interpretation Workshop",
            "Nightmare Support Group", "Flying Dreams Club",
            "Spiritual Dreams Community", "Dream Journaling Practice",
            "Shared Dreams Research", "Prophetic Dreams Discussion",
            "Dream Control Techniques", "Dream Psychology Study"
        ]
        
        for theme in group_themes:
            creator = random.choice(users)
            group = DreamGroup(
                name=theme,
                description=lorem.paragraph(),
                created_by=creator.id,
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 180))
            )
            db.session.add(group)
            groups.append(group)
            
            # Add creator as admin member
            membership = GroupMembership(
                user_id=creator.id,
                group_id=group.id,
                is_admin=True,
                joined_at=group.created_at
            )
            db.session.add(membership)
            
            # Add random members
            member_count = random.randint(5, 20)
            for _ in range(member_count):
                member = random.choice(users)
                if member.id != creator.id:
                    membership = GroupMembership(
                        user_id=member.id,
                        group_id=group.id,
                        is_admin=False,
                        joined_at=group.created_at + timedelta(days=random.randint(1, 90))
                    )
                    db.session.add(membership)

        db.session.commit()
        print(f"Created {len(groups)} dream groups with members")

        # Add forum posts and replies
        total_posts = 0
        total_replies = 0
        
        for group in groups:
            post_count = random.randint(3, 10)
            for _ in range(post_count):
                member_ids = [m.user_id for m in group.members]
                author_id = random.choice(member_ids)
                
                post = ForumPost(
                    title=lorem.sentence()[:200],
                    content=lorem.paragraph(),
                    author_id=author_id,
                    group_id=group.id,
                    created_at=datetime.utcnow() - timedelta(days=random.randint(0, 90))
                )
                db.session.add(post)
                total_posts += 1
                
                # Add replies
                reply_count = random.randint(0, 8)
                for _ in range(reply_count):
                    replier_id = random.choice(member_ids)
                    reply = ForumReply(
                        content=lorem.paragraph(),
                        author_id=replier_id,
                        post_id=post.id,
                        created_at=post.created_at + timedelta(days=random.randint(1, 30))
                    )
                    db.session.add(reply)
                    total_replies += 1
        
        db.session.commit()
        print(f"Created {total_posts} forum posts and {total_replies} replies")
        print("Data seeding completed successfully!")

if __name__ == "__main__":
    create_sample_data()
