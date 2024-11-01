from app import app, db
from models import User, Dream
from datetime import datetime, timedelta
import random
import json
from werkzeug.security import generate_password_hash
import pytz

def create_sample_data():
    with app.app_context():
        try:
            # Create test users with different subscription types
            test_users = [
                {
                    'username': 'dreamer_pro',
                    'email': 'dreamer_pro@example.com',
                    'subscription': 'premium'
                },
                {
                    'username': 'dream_explorer',
                    'email': 'explorer@example.com',
                    'subscription': 'free'
                },
                {
                    'username': 'lucid_master',
                    'email': 'lucid@example.com',
                    'subscription': 'premium'
                },
                {
                    'username': 'dream_novice',
                    'email': 'novice@example.com',
                    'subscription': 'free'
                },
                {
                    'username': 'sleep_walker',
                    'email': 'walker@example.com',
                    'subscription': 'premium'
                }
            ]

            # Dream themes and content templates
            dream_themes = [
                {
                    'title': 'Flying Over Mountains',
                    'content': 'I found myself soaring over snow-capped peaks, feeling the crisp air against my skin. The sense of freedom was overwhelming.',
                    'tags': 'flying,mountains,freedom,nature',
                    'mood': 'excited',
                    'symbols': ['wings', 'mountains', 'sky', 'clouds'],
                    'archetypes': ['explorer', 'free spirit']
                },
                {
                    'title': 'Chase Through Ancient City',
                    'content': 'Running through narrow cobblestone streets of an ancient city, being pursued by shadowy figures. The streets kept changing direction.',
                    'tags': 'chase,city,mystery,fear',
                    'mood': 'scared',
                    'symbols': ['maze', 'shadows', 'pursuit', 'ancient walls'],
                    'archetypes': ['fugitive', 'shadow']
                },
                {
                    'title': 'Underwater Palace',
                    'content': 'Discovered a luminescent palace beneath the ocean waves. Could breathe underwater and communicate with sea creatures.',
                    'tags': 'water,magic,discovery,palace',
                    'mood': 'peaceful',
                    'symbols': ['water', 'palace', 'light', 'communication'],
                    'archetypes': ['explorer', 'mystic']
                },
                {
                    'title': 'Time Travel Mishap',
                    'content': 'Found an old pocket watch that transported me through different time periods. Each tick brought me to a new era.',
                    'tags': 'time,history,adventure,magic',
                    'mood': 'anxious',
                    'symbols': ['clock', 'spiral', 'doors', 'time'],
                    'archetypes': ['traveler', 'seeker']
                },
                {
                    'title': 'Garden of Speaking Trees',
                    'content': 'Wandered into a garden where trees spoke in riddles and shared ancient wisdom. Their leaves turned into books.',
                    'tags': 'nature,wisdom,magic,transformation',
                    'mood': 'happy',
                    'symbols': ['tree', 'book', 'garden', 'wisdom'],
                    'archetypes': ['sage', 'nature spirit']
                }
            ]

            created_users = []
            
            # Create users
            for user_data in test_users:
                user = User(
                    username=user_data['username'],
                    email=user_data['email'],
                    subscription_type=user_data['subscription'],
                    subscription_end_date=datetime.utcnow() + timedelta(days=30) if user_data['subscription'] == 'premium' else None
                )
                user.set_password('password123')
                db.session.add(user)
                db.session.flush()
                created_users.append(user)

            # Create dreams for each user
            for user in created_users:
                # Generate 3-5 dreams per user
                num_dreams = random.randint(3, 5)
                for _ in range(num_dreams):
                    # Select random dream theme
                    theme = random.choice(dream_themes)
                    
                    # Generate random date within last month
                    days_ago = random.randint(0, 30)
                    dream_date = datetime.utcnow() - timedelta(days=days_ago)
                    
                    # Random sleep metrics
                    sleep_duration = round(random.uniform(5.0, 9.0), 1)
                    bedtime = dream_date.replace(
                        hour=random.randint(21, 23),
                        minute=random.randint(0, 59)
                    ).time()
                    
                    # Create dream entry
                    dream = Dream(
                        user_id=user.id,
                        title=theme['title'],
                        content=theme['content'],
                        date=dream_date,
                        mood=theme['mood'],
                        tags=theme['tags'],
                        is_public=random.choice([True, False]),
                        is_anonymous=random.choice([True, False]),
                        ai_analysis="Sample AI analysis for dream pattern testing",
                        lucidity_level=random.randint(0, 5),
                        sleep_quality=random.randint(1, 5),
                        dream_clarity=random.randint(1, 5),
                        recurring_elements=json.dumps(['flying', 'falling', 'running', 'water']),
                        emotional_tone=round(random.uniform(-1.0, 1.0), 2),
                        dream_symbols=json.dumps(theme['symbols']),
                        dream_archetypes=json.dumps(theme['archetypes']),
                        sleep_duration=sleep_duration,
                        bedtime=bedtime,
                        environmental_factors=json.dumps({
                            'stress_level': random.randint(1, 5),
                            'room_temperature': round(random.uniform(18.0, 24.0), 1),
                            'noise_level': random.choice(['quiet', 'moderate', 'noisy']),
                            'moon_phase': random.choice(['new', 'waxing', 'full', 'waning'])
                        })
                    )
                    db.session.add(dream)

            db.session.commit()
            print("Successfully created sample users and dreams!")
            
        except Exception as e:
            print(f"Error creating sample data: {str(e)}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    create_sample_data()
