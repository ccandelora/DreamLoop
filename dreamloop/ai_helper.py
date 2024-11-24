import os
import openai
from .models import Users, Dream
from .extensions import db
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_dream(dream_text, user=None):
    """Analyze a single dream using OpenAI's GPT model."""
    try:
        # Set OpenAI API key
        openai.api_key = os.getenv('OPENAI_API_KEY')
        
        if not openai.api_key:
            logger.error("OpenAI API key not found")
            return "Error: OpenAI API key not configured"

        # Check if user has exceeded their monthly limit
        if user and not user.can_use_ai_analysis():
            logger.warning(f"User {user.id} has exceeded monthly AI analysis limit")
            return "Monthly AI analysis limit reached"

        # Construct the prompt
        prompt = f"""Analyze this dream and provide insights about its potential meaning, 
        psychological significance, and any recurring symbols or themes:

        Dream: {dream_text}

        Please provide the analysis in the following format:
        1. Key Symbols and Their Meanings
        2. Emotional Themes
        3. Possible Interpretations
        4. Psychological Significance
        5. Action Steps or Reflections"""

        # Make API call to OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-4",  # or "gpt-3.5-turbo" depending on your needs
            messages=[
                {"role": "system", "content": "You are a knowledgeable dream analyst combining insights from psychology and dream interpretation."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )

        # Extract the analysis from the response
        analysis = response.choices[0].message.content

        # Update user's AI analysis count if user is provided
        if user:
            user.increment_ai_analysis_count()
            db.session.commit()

        return analysis

    except Exception as e:
        logger.error(f"Error in dream analysis: {str(e)}")
        return f"Error analyzing dream: {str(e)}"

def analyze_dream_patterns(dreams, user=None):
    """Analyze patterns across multiple dreams."""
    try:
        # Set OpenAI API key
        openai.api_key = os.getenv('OPENAI_API_KEY')
        
        if not openai.api_key:
            logger.error("OpenAI API key not found")
            return "Error: OpenAI API key not configured"

        # Check if user has exceeded their monthly limit
        if user and not user.can_use_ai_analysis():
            logger.warning(f"User {user.id} has exceeded monthly AI analysis limit")
            return "Monthly AI analysis limit reached"

        # Prepare dreams for analysis
        dream_texts = [f"Dream {i+1}: {dream.content}" for i, dream in enumerate(dreams)]
        dreams_combined = "\n\n".join(dream_texts)

        # Construct the prompt
        prompt = f"""Analyze these dreams and identify patterns, recurring themes, and psychological insights:

        {dreams_combined}

        Please provide the analysis in the following format:
        1. Recurring Symbols and Themes
        2. Pattern Analysis
        3. Psychological Insights
        4. Personal Growth Indicators
        5. Recommendations for Further Reflection"""

        # Make API call to OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-4",  # or "gpt-3.5-turbo" depending on your needs
            messages=[
                {"role": "system", "content": "You are a knowledgeable dream analyst specializing in pattern recognition and psychological interpretation."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.7
        )

        # Extract the analysis from the response
        analysis = response.choices[0].message.content

        # Update user's AI analysis count if user is provided
        if user:
            user.increment_ai_analysis_count()
            db.session.commit()

        return analysis

    except Exception as e:
        logger.error(f"Error in dream pattern analysis: {str(e)}")
        return f"Error analyzing dream patterns: {str(e)}"
