from app import app
from models import Dream, User
from datetime import datetime, timedelta
import random
from extensions import db
import logging

logger = logging.getLogger(__name__)

def add_sample_dreams():
    with app.app_context():
        try:
            # Get or create test user
            test_user = User.query.filter_by(username='test_user').first()
            
            if not test_user:
                test_user = User(username='test_user', email='test@example.com')
                test_user.set_password('test123')
                db.session.add(test_user)
                db.session.commit()
                logger.info("Created new test user")
            else:
                logger.info("Using existing test user")

            # Sample dreams data with more varied timestamps
            dreams_added = 0
            for i in range(15):  # Create 15 sample dreams for better pagination testing
                created_at = datetime.utcnow() - timedelta(days=i)
                
                # Check if dream already exists
                existing_dream = Dream.query.filter_by(
                    user_id=test_user.id,
                    title=f"Sample Dream #{i+1}"
                ).first()
                
                if not existing_dream:
                    dream = Dream(
                        user_id=test_user.id,
                        title=f"Sample Dream #{i+1}",
                        content=f"This is a sample dream content for testing pagination. Dream number {i+1} with some additional text to make it more realistic.",
                        mood="peaceful" if i % 2 == 0 else "excited",
                        tags="sample,test,pagination",
                        is_public=True,
                        created_at=created_at
                    )
                    db.session.add(dream)
                    dreams_added += 1

            if dreams_added > 0:
                db.session.commit()
                print(f"Added {dreams_added} new sample dreams successfully!")
            else:
                print("No new dreams needed to be added.")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error adding sample dreams: {str(e)}")
            raise

if __name__ == "__main__":
    add_sample_dreams()
