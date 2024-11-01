from app import app, db
from models import User, Dream, Comment, DreamGroup, GroupMembership, ForumPost, ForumReply
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
import random
import json
from datetime import time

def generate_dream_content():
    """Generate rich dream narrative from predefined realistic dreams"""
    dreams = [
        """I found myself soaring high above an ancient city, its ruins bathed in golden sunlight. The sensation was incredibly vivid - the cool wind rushing past my face, the gentle resistance against my outstretched arms. Below, I could see intricate stone structures, their shadows casting mysterious patterns on the desert floor. As I flew lower, I noticed hieroglyphs beginning to glow with an ethereal blue light. The air hummed with an energy I could feel in my bones, and each movement through the sky felt as natural as walking. When I passed through a beam of sunlight, I became aware I was dreaming but maintained the flight, deliberately exploring the ruins from angles impossible in waking life.""",
        
        """Heart pounding, I ran through endless hospital corridors that kept shifting and changing. The fluorescent lights above flickered ominously, casting strange shadows that seemed to move independently. Behind me, I could hear the steady footsteps of my pursuer, never speeding up but never falling behind. The sound of my own breathing was deafening in my ears. Every time I turned a corner, the corridor ahead would stretch impossibly long or twist into spiral patterns. The walls pulsed with a faint red glow, and I could feel waves of dread washing over me. Medical equipment on wheeled stands would move on their own, blocking my path, forcing me to constantly change direction.""",
        
        """In this dream, I stood in a vast library that extended infinitely in all directions. Each book contained memories - some mine, some belonging to others. The air was thick with the scent of old paper and leather bindings. As I walked between the towering shelves, I could hear whispered conversations from different time periods echoing softly. I knew I was dreaming and began deliberately pulling books from shelves, each one revealing vivid scenes from possible futures. The pages glowed with their own inner light, and the words would float off the pages, forming 3D scenes I could step into and explore.""",
        
        """Standing in a forest made entirely of crystalline trees, each leaf a delicate prism catching and refracting rainbow light. The ground beneath my feet resonated with each step, creating musical tones that harmonized with the wind passing through the crystal branches. In the distance, I could see my deceased grandfather tending to a garden of flowers made from stained glass. The air itself seemed to shimmer with particles of light, and each breath filled me with a sense of profound peace and healing. When I touched one of the trees, ripples of color spread out from my fingertips, changing the hues of the entire forest.""",
        
        """The dream began in my childhood home, but everything was slightly off. The stairs had twice as many steps, and family photos on the walls showed impossible events. I walked into the kitchen to find it opened onto a vast ocean, waves gently lapping at the linoleum floor. The refrigerator hummed a familiar lullaby, and when I opened it, instead of food, I found doorways to other rooms of the house. The dream shifted and flowed between locations - one moment I was in the ocean-kitchen, the next in an upside-down version of my bedroom where gravity pulled towards the ceiling.""",
        
        """I was inside a clock mechanism the size of a city. Massive gears turned overhead, their teeth interlocking with mathematical precision. Oil rained upward, defying gravity, lubricating the endless machine. Time moved differently here - I could see the past and future simultaneously, manifesting as layers of translucent images overlapping reality. Every tick of the mechanism sent vibrations through my body, and I understood that each gear movement represented a decision point in time. Clock hands the size of buildings swept past, and I knew with dream-certainty that I was witnessing the machinery of time itself.""",
        
        """In this recurring dream, I descended a spiral staircase that wound through different epochs of history. Each full turn brought me to a new era, complete with period-appropriate architecture and inhabitants who seemed to be expecting me. The air changed with each level - from the smoky atmosphere of industrial London to the incense-laden winds of ancient Egypt. I recognized certain characters from previous iterations of this dream, but they played different roles each time. The deeper I went, the more the boundaries between times began to blur, until I reached a chamber where all epochs existed simultaneously."""
    ]
    return random.choice(dreams)

def generate_dream_symbols():
    """Generate a list of common dream symbols"""
    symbols = [
        "water", "flying", "falling", "teeth", "house", "door", "key", "mountain",
        "bridge", "snake", "bird", "tree", "fire", "clock", "mirror", "stairs",
        "school", "car", "train", "ocean", "moon", "sun", "storm", "garden",
        "child", "elder", "animal", "book", "phone", "computer", "forest", "city",
        "crystal", "machine", "time", "portal", "library", "hospital", "chase",
        "light", "darkness", "transformation", "spiral", "ancestor", "healing"
    ]
    return random.sample(symbols, random.randint(3, 7))

def generate_archetypes():
    """Generate a list of Jungian archetypes"""
    archetypes = [
        "Hero", "Shadow", "Anima", "Animus", "Mentor", "Trickster", "Child",
        "Great Mother", "Wise Old Man", "Explorer", "Creator", "Ruler", "Sage",
        "Innocent", "Magician", "Caregiver", "Everyman", "Lover", "Jester", "Outlaw"
    ]
    return random.sample(archetypes, random.randint(2, 4))

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
        "sleep_position": random.choice(["back", "side", "stomach"]),
        "moon_phase": random.choice(["new", "waxing", "full", "waning"]),
        "weather": random.choice(["clear", "stormy", "cloudy", "rain"]),
        "last_meal": random.choice(["light", "heavy", "spicy", "none"]),
        "emotional_state": random.choice(["calm", "anxious", "excited", "neutral"])
    }
    return json.dumps(factors)

def generate_recurring_elements():
    """Generate recurring elements in dreams"""
    elements = [
        "chase sequence", "being late", "lost in familiar place", "unprepared for test",
        "flying sensation", "falling sensation", "meeting deceased relative",
        "supernatural abilities", "being trapped", "discovering new rooms",
        "time travel", "transformation", "parallel universe", "underwater breathing",
        "shifting gravity", "impossible architecture", "living machinery",
        "crystalline structures", "infinite spaces", "temporal anomalies",
        "healing light", "ancient wisdom", "cosmic understanding"
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
            "Hospital Labyrinth Chase",
            "The Infinite Library of Time",
            "Crystal Forest Healing",
            "The Shifting House",
            "City-sized Clock Mechanism",
            "Spiral Staircase Through Time"
        ]

        moods = ["mystical", "fearful", "enlightened", "peaceful", "confused", "awestruck", "contemplative"]
        total_dreams = 0

        for i, title in enumerate(dream_titles):
            # Match mood to dream content
            mood = moods[i]
            is_lucid = title in ["Flying Over Ancient Ruins", "The Infinite Library of Time"]
            sleep_quality = random.randint(3, 5)  # Better sleep quality for more vivid dreams
            clarity = random.randint(4, 5)  # High clarity for these detailed dreams
            emotional_tone = {
                "mystical": 0.8,
                "fearful": -0.7,
                "enlightened": 0.9,
                "peaceful": 0.6,
                "confused": -0.3,
                "awestruck": 0.7,
                "contemplative": 0.4
            }[mood]

            dream = Dream(
                user_id=user.id,
                title=title,
                content=generate_dream_content(),
                date=datetime.utcnow() - timedelta(days=random.randint(0, 30)),
                mood=mood,
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
                sleep_duration=round(random.uniform(7.0, 9.0), 1),  # Better sleep duration for vivid dreams
                bedtime=time(hour=random.randint(21, 23), minute=random.randint(0, 59)),
                environmental_factors=generate_environmental_factors()
            )
            db.session.add(dream)
            total_dreams += 1

        db.session.commit()
        print(f"Created {total_dreams} dreams for Chris with rich metadata")

if __name__ == "__main__":
    create_chris_dreams()
