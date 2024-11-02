import os
import google.generativeai as genai
import re
from datetime import datetime

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)

def analyze_dream(content, is_premium=False):
    """Analyze dream content using Gemini AI."""
    try:
        model = genai.GenerativeModel('gemini-pro')
        
        # Base prompt for all users
        prompt = f"""Analyze this dream and provide insights. Dream content: {content}

Please analyze this dream and provide the following:
1. Key Themes and Symbols
2. Emotional Analysis (including sentiment score from -1 to 1, and magnitude from 0 to 5)
3. Most prominent emotions (comma-separated list)
4. Dream lucidity level (1-5 scale)
5. Psychological Interpretation

Format the response in markdown with appropriate headers. For the emotional analysis, strictly use this format:
Sentiment Score: [number between -1 and 1]
Sentiment Magnitude: [number between 0 and 5]
Dominant Emotions: [comma-separated list]"""

        if is_premium:
            prompt += """

Also provide:
6. Personal Growth Recommendations
7. Pattern Recognition Suggestions
8. Archetypal Analysis
9. Cultural Symbolism
10. Action Steps for Integration"""

        response = model.generate_content(prompt)
        analysis = response.text

        # Extract sentiment information
        sentiment_info = extract_sentiment_info(analysis)
        
        return analysis, sentiment_info
    except Exception as e:
        return f"Error analyzing dream: {str(e)}", None

def extract_sentiment_info(analysis):
    """Extract sentiment information from the AI analysis."""
    try:
        # Extract sentiment score (-1 to 1)
        score_match = re.search(r'Sentiment Score:\s*([-+]?\d*\.?\d+)', analysis)
        sentiment_score = float(score_match.group(1)) if score_match else 0.0

        # Extract sentiment magnitude (0 to 5)
        magnitude_match = re.search(r'Sentiment Magnitude:\s*(\d*\.?\d+)', analysis)
        sentiment_magnitude = float(magnitude_match.group(1)) if magnitude_match else 0.0

        # Extract dominant emotions
        emotions_match = re.search(r'Dominant Emotions:\s*([^#\n]+)', analysis)
        dominant_emotions = emotions_match.group(1).strip() if emotions_match else ''

        # Extract lucidity level (1-5)
        lucidity_match = re.search(r'Dream lucidity level.*?(\d+)', analysis)
        lucidity_level = int(lucidity_match.group(1)) if lucidity_match else 1

        return {
            'sentiment_score': sentiment_score,
            'sentiment_magnitude': sentiment_magnitude,
            'dominant_emotions': dominant_emotions,
            'lucidity_level': lucidity_level
        }
    except Exception as e:
        return None

def analyze_dream_patterns(dreams, is_premium=False):
    """Analyze patterns across multiple dreams."""
    if not dreams:
        return None

    try:
        # Collect all dream content
        dream_texts = [dream.content for dream in dreams]
        model = genai.GenerativeModel('gemini-pro')
        
        # Base prompt for pattern analysis
        prompt = f"""Analyze these {len(dreams)} dreams and identify patterns. Dreams: {dream_texts}

Please provide:
1. Common themes
2. Emotional patterns
3. Recurring symbols
4. Dream type distribution

Format the response in markdown."""

        if is_premium:
            prompt += """
Also analyze:
5. Long-term pattern evolution
6. Psychological growth indicators
7. Life event correlations
8. Detailed archetype analysis
9. Personalized recommendations"""

        response = model.generate_content(prompt)
        pattern_analysis = response.text

        # Process dream dates for timeline
        dream_dates = {dream.date.strftime('%Y-%m-%d'): 1 for dream in dreams}
        
        # Calculate mood patterns
        mood_patterns = {}
        for dream in dreams:
            mood = dream.mood or 'unspecified'
            mood_patterns[mood] = mood_patterns.get(mood, 0) + 1

        # Extract common themes
        common_themes = extract_common_themes(pattern_analysis)

        return {
            'dream_count': len(dreams),
            'mood_patterns': mood_patterns,
            'dream_dates': dream_dates,
            'common_themes': common_themes,
            'ai_analysis': pattern_analysis
        }

    except Exception as e:
        return None

def extract_common_themes(analysis):
    """Extract common themes from the pattern analysis."""
    try:
        themes_match = re.search(r'Common themes:(.*?)(?=\#|\Z)', analysis, re.DOTALL | re.IGNORECASE)
        if themes_match:
            themes_text = themes_match.group(1).strip()
            # Extract bullet points or numbered items
            themes = re.findall(r'[-*\d.]\s*([^\n]+)', themes_text)
            return {theme.strip(): 1 for theme in themes}
        return {'No themes found': 0}
    except Exception:
        return {'Error extracting themes': 0}
