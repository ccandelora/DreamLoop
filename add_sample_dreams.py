from app import app, db
from models import Dream
from flask_login import current_user
from datetime import datetime

def add_sample_dreams():
    with app.app_context():
        # Sample dreams data
        dreams_data = [
            {
                "title": "Soaring Over Mountains",
                "content": "I was flying over snow-capped mountains, feeling completely free and weightless. The air was crisp, and I could see for miles.",
                "mood": "peaceful",
                "tags": "flying, nature, freedom",
                "is_public": True
            },
            {
                "title": "Running Through Maze",
                "content": "I was being chased through an endless maze of corridors. Every turn led to another identical hallway. The footsteps behind me kept getting closer.",
                "mood": "anxious",
                "tags": "chase, maze, stress",
                "is_public": True
            },
            {
                "title": "Deep Ocean Discovery",
                "content": "I found myself swimming in deep ocean waters, discovering ancient ruins. The water was crystal clear and I could breathe underwater.",
                "mood": "happy",
                "tags": "ocean, adventure, discovery",
                "is_public": True
            }
        ]

        # Get the first user from the database
        from models import User
        user = User.query.first()
        
        if not user:
            print("No user found in the database")
            return

        # Add dreams
        for dream_data in dreams_data:
            # Create dream instance
            dream = Dream()
            # Set attributes
            dream.user_id = user.id
            dream.title = dream_data["title"]
            dream.content = dream_data["content"]
            dream.mood = dream_data["mood"]
            dream.tags = dream_data["tags"]
            dream.is_public = dream_data["is_public"]
            dream.date = datetime.utcnow()
            
            db.session.add(dream)
        
        # Commit the changes
        db.session.commit()
        print("Sample dreams added successfully!")

if __name__ == "__main__":
    add_sample_dreams()
