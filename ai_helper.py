from collections import Counter
from datetime import datetime, timedelta
import os
import google.generativeai as genai
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-pro')

def analyze_dream(content):
    """Analyze a dream using Gemini AI."""
    try:
        prompt = f"""
        Analyze this dream and provide insights about its potential meaning:
        {content}
        
        Please include:
        1. Key symbols and their possible interpretations
        2. Overall theme or message
        3. Emotional undertones
        4. Potential connections to real life
        
        Format the response in a clear, structured way.
        """
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        logger.error(f"Error analyzing dream: {str(e)}")
        return "Unable to analyze dream at this time. Please try again later."

def extract_dream_stats(dreams):
    """Extract statistical information from dreams."""
    try:
        # Access mood as an attribute instead of dictionary key
        moods = Counter(dream.mood for dream in dreams if dream.mood)
        tags = Counter()
        for dream in dreams:
            if dream.tags:
                dream_tags = [tag.strip() for tag in dream.tags.split(',')]
                tags.update(dream_tags)
                
        # Get the most common elements
        common_moods = dict(moods.most_common(5))
        common_tags = dict(tags.most_common(10))
        
        return {
            'moods': common_moods,
            'tags': common_tags
        }
    except Exception as e:
        logger.error(f"Error extracting dream stats: {str(e)}")
        return {'moods': {}, 'tags': {}}

def analyze_dream_patterns(dreams):
    """Analyze patterns across multiple dreams."""
    try:
        if not dreams:
            return {}
            
        stats = extract_dream_stats(dreams)
        
        # Prepare summary text for Gemini analysis
        summary_text = f"""
        Analyze these dream patterns:
        
        Most common moods: {', '.join(f'{mood} ({count} times)' for mood, count in stats['moods'].items())}
        Most common themes/tags: {', '.join(f'{tag} ({count} times)' for tag, count in stats['tags'].items())}
        Total dreams analyzed: {len(dreams)}
        Time span: {min(dream.date for dream in dreams).strftime('%Y-%m-%d')} to {max(dream.date for dream in dreams).strftime('%Y-%m-%d')}
        """
        
        prompt = f"""
        {summary_text}
        
        Please provide:
        1. Overall pattern analysis
        2. Recurring themes and their significance
        3. Mood trends and their potential meaning
        4. Suggestions for personal growth based on these patterns
        
        Format the response in a clear, structured way.
        """
        
        response = model.generate_content(prompt)
        
        return {
            'statistics': stats,
            'analysis': response.text
        }
        
    except Exception as e:
        logger.error(f"Error analyzing dream patterns: {str(e)}")
        return {
            'statistics': {'moods': {}, 'tags': {}},
            'analysis': "Unable to analyze patterns at this time. Please try again later."
        }
