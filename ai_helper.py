import os
import google.generativeai as genai
import logging
import json
from collections import Counter
from datetime import datetime, timedelta

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
            prompt = f"""As an expert dream analyst, provide a comprehensive analysis of the following dream:

            Dream Content: {content}

            # Symbolism Analysis
            * Detailed interpretation of key symbols
            * Historical and mythological connections
            * Personal and cultural significance
            * Archetypal meanings and universal patterns

            # Emotional Patterns
            * Core emotional themes and their origins
            * Subconscious feelings revealed
            * Connection to current life situations
            * Impact on waking emotional state

            # Psychological Insights
            * Jungian archetypal analysis
            * Shadow aspects and integration
            * Personal growth opportunities
            * Relationship dynamics revealed

            # Life Connections
            * Current life situations reflected
            * Past experiences influencing the dream
            * Future possibilities indicated
            * Relationships and interactions highlighted

            # Growth & Development
            * Personal development opportunities
            * Areas for psychological exploration
            * Potential challenges to address
            * Skills or qualities to develop

            # Action Steps
            * Specific recommendations for growth
            * Daily practices to implement
            * Journal prompts for deeper exploration
            * Mindfulness exercises related to dream themes

            Format the response in markdown with clear sections and bullet points."""
        else:
            # Basic prompt for free users with upgrade message
            prompt = f"""Provide a very brief analysis of this dream (3-4 sentences maximum):

            Dream Content: {content}

            Include only:
            1. One key symbol and its basic meaning
            2. The main emotional theme
            3. A single practical insight

            End with: "💫 *Unlock deeper insights with Premium: Get comprehensive symbolism analysis, personal growth recommendations, and detailed psychological patterns.*"

            Keep it clear and concise."""

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
        tags = [
            tag.strip() for dream in dreams for tag in dream.tags.split(',')
            if dream.tags
        ]

        # Calculate dream frequency
        dream_dates = {}
        for dream in dreams:
            date_str = dream.date.strftime('%Y-%m-%d')
            dream_dates[date_str] = dream_dates.get(date_str, 0) + 1

        # Sort dates for the chart
        sorted_dates = dict(sorted(dream_dates.items()))

        # Basic pattern analysis
        mood_frequency = Counter(moods)
        tag_frequency = Counter(tags)

        if is_premium:
            # Enhanced analysis for premium users
            model = genai.GenerativeModel('gemini-pro')
            combined_dreams = "\n---\n".join(
                dream_texts[-10:])  # Analyze last 10 dreams

            prompt = f"""As an expert dream analyst, analyze these recent dreams for deep patterns and insights:

            Dreams:
            {combined_dreams}

            # Dream Evolution Patterns
            * Major themes and their progression
            * Symbol transformations over time
            * Narrative pattern development

            # Psychological Growth
            * Personal development indicators
            * Recurring challenges and resolutions
            * Integration of shadow aspects

            # Emotional Journey
            * Emotional pattern progression
            * Relationship dynamics evolution
            * Conflict resolution patterns

            # Symbol Network
            * Interconnected symbol meanings
            * Personal symbol dictionary
            * Cultural and archetypal significance

            # Growth Recommendations
            * Key areas for conscious work
            * Specific journaling exercises
            * Meditation and mindfulness practices

            Format the response in markdown with clear sections."""

            response = model.generate_content(prompt)
            ai_pattern_analysis = response.text
        else:
            # Basic analysis for free users with upgrade message
            model = genai.GenerativeModel('gemini-pro')
            combined_dreams = "\n---\n".join(
                dream_texts[-3:])  # Analyze last 3 dreams
            prompt = f"""As an expert dream analyst, analyze these recent dreams for deep patterns and insights:

            Dreams:
            {combined_dreams}
            Include only:
            # Basic Pattern Summary
            * A simple overview of your most common dream themes
            * Basic mood patterns across your dreams

            End with: 💫 **Upgrade to Premium to Unlock:**
                        * Deep psychological pattern analysis
                        * Personal growth recommendations
                        * Symbol network insights
                        * Customized journaling prompts
                        * Comprehensive emotional journey tracking"""
            response = model.generate_content(prompt)
            ai_pattern_analysis = response.text

        # Construct the analysis result
        analysis = {
            'mood_patterns': dict(mood_frequency),
            'common_themes': dict(tag_frequency.most_common(5)),
            'dream_count': len(dreams),
            'time_span': {
                'start':
                min(dream.date for dream in dreams).strftime('%Y-%m-%d'),
                'end': max(dream.date for dream in dreams).strftime('%Y-%m-%d')
            },
            'dream_dates': sorted_dates,
            'ai_analysis': ai_pattern_analysis,
            'is_premium': is_premium
        }

        return analysis
    except Exception as e:
        logger.error(f"Error in pattern analysis: {str(e)}")
        return None
