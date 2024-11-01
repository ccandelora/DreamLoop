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
    paragraphs = []
    for _ in range(random.randint(3, 6)):
        paragraphs.append(lorem.paragraph())
    return "\n\n".join(paragraphs)

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

def create_chris_dreams():
    """Create sample dreams for user Chris"""
    with app.app_context():
        # Create or get Chris user
        user = User.query.filter_by(username='Chris').first()
        if not user:
            user = User(
                username='Chris',
                email='chris@dreamloop.com',
                subscription_type='premium',
                subscription_end_date=datetime.utcnow() + timedelta(days=365)
            )
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            print("Created user Chris")

        # Create dreams for Chris
        dream_titles = [
            "Flying Over Ancient Ruins",
            "The Infinite Library",
            "Underwater City Discovery",
            "Time-traveling Train Journey",
            "Crystal Forest Meditation",
            "Shadow Self Confrontation",
            "Cosmic Dance of Planets"
        ]

        moods = ["happy", "anxious", "peaceful", "excited", "confused", "nostalgic", "mystical"]
        total_dreams = 0

        for title in dream_titles:
            is_lucid = random.random() < 0.4  # 40% chance of lucid dream
            sleep_quality = random.randint(1, 5)
            clarity = random.randint(1, 5)
            emotional_tone = round(random.uniform(-1.0, 1.0), 2)

            dream = Dream(
                user_id=user.id,
                title=title,
                content=generate_dream_content(),
                date=datetime.utcnow() - timedelta(days=random.randint(0, 30)),
                mood=random.choice(moods),
                tags=",".join(generate_dream_symbols()),
                is_public=random.random() < 0.6,  # 60% public
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

        db.session.commit()
        print(f"Created {total_dreams} dreams for Chris with rich metadata")

if __name__ == "__main__":
    create_chris_dreams()
