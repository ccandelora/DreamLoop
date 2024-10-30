import os
import google.generativeai as genai
import logging
import json
from collections import Counter
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini AI
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)

def analyze_dream(content, is_premium=False):
    """Analyze a dream with different depth based on subscription type."""
    try:
        model = genai.GenerativeModel('gemini-pro')
        
        if is_premium:
            # Enhanced prompt for premium users
            prompt = f"""As an expert dream analyst, provide a comprehensive analysis of the following dream. 
            Include these sections:
            
            # Core Symbolism
            * Deep analysis of key symbols and their personal/cultural significance
            * Historical and mythological connections
            * Potential archetypal meanings
            
            # Emotional Landscape
            * Detailed emotional patterns and their real-life connections
            * Subconscious feelings and their manifestations
            * Impact on waking emotional state
            
            # Psychological Insights
            * Jungian psychological perspectives
            * Personal growth opportunities
            * Shadow aspects and integration
            
            # Action Recommendations
            * Specific steps for personal growth
            * Journal prompts for deeper exploration
            * Mindfulness exercises related to dream themes
            
            # Pattern Recognition
            * Universal archetypes present
            * Common dream motifs
            * Personal symbol dictionary suggestions
            
            Dream Content: {content}
            
            Format the response in markdown with clear sections and bullet points."""
        else:
            # Basic prompt for free users
            prompt = f"""Provide a brief analysis of this dream:
            
            Dream Content: {content}
            
            Include:
            * Key symbols and their basic meaning
            * Main emotional theme
            * One practical insight
            
            Keep it concise and clear."""

        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Error in dream analysis: {str(e)}")
        return "Unable to analyze dream at this time. Please try again later."

def analyze_dream_patterns(dreams, is_premium=False):
    """Analyze patterns across multiple dreams with enhanced insights for premium users."""
    try:
        if not dreams:
            return None

        # Collect dream data
        dream_texts = [dream.content for dream in dreams]
        moods = [dream.mood for dream in dreams]
        tags = [tag.strip() for dream in dreams for tag in dream.tags.split(',') if dream.tags]
        
        # Basic pattern analysis
        mood_frequency = Counter(moods)
        tag_frequency = Counter(tags)
        
        if is_premium:
            # Enhanced analysis for premium users
            model = genai.GenerativeModel('gemini-pro')
            combined_dreams = "\n---\n".join(dream_texts[-10:])  # Analyze last 10 dreams
            
            prompt = f"""As an expert dream analyst, analyze these recent dreams for deep patterns and insights:

            Dreams:
            {combined_dreams}

            Provide a comprehensive pattern analysis including:
            
            # Recurring Themes and Evolution
            * Major themes and their progression
            * Symbol patterns and transformations
            * Narrative arcs across dreams
            
            # Psychological Development
            * Signs of personal growth or challenges
            * Integration of shadow aspects
            * Areas of psychological focus
            
            # Emotional Patterns
            * Dominant emotional currents
            * Emotional processing patterns
            * Relationship dynamics
            
            # Symbol Networks
            * Interconnected symbol systems
            * Personal symbol dictionary
            * Cultural and archetypal connections
            
            # Growth Recommendations
            * Specific areas for conscious work
            * Journaling prompts and exercises
            * Mindfulness practices
            
            Format the response in markdown with clear sections."""
            
            response = model.generate_content(prompt)
            ai_pattern_analysis = response.text
        else:
            # Basic analysis for free users
            ai_pattern_analysis = """### Basic Pattern Analysis
* Upgrade to premium for in-depth pattern analysis across your dreams
* Premium analysis includes psychological insights, symbol networks, and personalized recommendations
* Track your dream patterns more effectively with our advanced AI analysis"""

        # Construct the analysis result
        analysis = {
            'mood_patterns': dict(mood_frequency),
            'common_themes': dict(tag_frequency.most_common(5)),
            'dream_count': len(dreams),
            'time_span': {
                'start': min(dream.date for dream in dreams).strftime('%Y-%m-%d'),
                'end': max(dream.date for dream in dreams).strftime('%Y-%m-%d')
            },
            'ai_analysis': ai_pattern_analysis,
            'is_premium': is_premium
        }
        
        return analysis
    except Exception as e:
        logger.error(f"Error in pattern analysis: {str(e)}")
        return None
