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
        
        # Enhanced base prompt for all users with better pattern recognition
        prompt = f"""Analyze this dream with advanced pattern recognition and symbolism interpretation. Dream content: {content}

Please provide a comprehensive analysis including:

1. Key Themes and Symbols:
   - Primary symbols and their cultural/psychological significance
   - Recurring patterns and motifs
   - Archetypal elements present

2. Pattern Recognition:
   - Symbolic connections and relationships
   - Time and space patterns
   - Environmental and contextual patterns

3. Emotional Analysis:
   - Detailed emotional landscape
   - Sentiment score (from -1 to 1)
   - Sentiment magnitude (from 0 to 5)
   - Emotional transitions and patterns
   - Most prominent emotions (comma-separated list)

4. Dream Lucidity Analysis:
   - Lucidity level (1-5 scale)
   - Dream awareness indicators
   - Reality check moments

5. Psychological Interpretation:
   - Core psychological themes
   - Personal growth indicators
   - Subconscious patterns revealed

Format the response in markdown with appropriate headers. For the emotional analysis, strictly use this format:
Sentiment Score: [number between -1 and 1]
Sentiment Magnitude: [number between 0 and 5]
Dominant Emotions: [comma-separated list]"""

        if is_premium:
            prompt += """

6. Advanced Pattern Recognition:
   - Cross-cultural symbol analysis
   - Jungian archetype identification
   - Shadow aspects and integration
   - Personal mythology elements

7. Deep Symbolism Analysis:
   - Multi-layered symbol interpretation
   - Historical and mythological connections
   - Personal symbol dictionary suggestions

8. Growth and Integration:
   - Personal development opportunities
   - Shadow work suggestions
   - Integration exercises
   - Action steps for conscious integration

9. Predictive Pattern Analysis:
   - Potential future patterns
   - Personal growth trajectory
   - Suggested areas for dream work

10. Advanced Recommendations:
    - Personalized dreamwork exercises
    - Symbol meditation practices
    - Integration techniques
    - Journal prompts for deeper exploration"""

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

        # Extract dominant emotions with improved pattern matching
        emotions_match = re.search(r'Dominant Emotions:\s*([^#\n]+)', analysis)
        dominant_emotions = emotions_match.group(1).strip() if emotions_match else ''

        # Extract lucidity level (1-5) with improved pattern matching
        lucidity_match = re.search(r'(?:Dream lucidity level|Lucidity level).*?(\d+)', analysis, re.IGNORECASE)
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
    """Analyze patterns across multiple dreams with enhanced pattern recognition."""
    if not dreams:
        return None

    try:
        # Collect all dream content with metadata
        dream_data = [{
            'content': dream.content,
            'date': dream.date.strftime('%Y-%m-%d'),
            'mood': dream.mood,
            'tags': dream.tags,
            'lucidity_level': dream.lucidity_level
        } for dream in dreams]
        
        model = genai.GenerativeModel('gemini-pro')
        
        # Enhanced prompt for pattern analysis
        prompt = f"""Analyze these {len(dreams)} dreams with advanced pattern recognition and symbolism interpretation. Dream data: {dream_data}

Please provide comprehensive pattern analysis including:

1. Symbol Evolution:
   - Recurring symbols and their transformations
   - Symbol frequency and significance
   - Pattern development over time

2. Emotional Patterns:
   - Emotional themes and progressions
   - Mood correlations and cycles
   - Emotional intensity patterns

3. Thematic Analysis:
   - Major recurring themes
   - Theme interconnections
   - Theme evolution over time

4. Dream Type Patterns:
   - Dream category distribution
   - Lucidity level progression
   - Environmental patterns

Format the response in markdown with clear sections."""

        if is_premium:
            prompt += """

5. Advanced Pattern Recognition:
   - Long-term symbol evolution
   - Cross-dream narrative patterns
   - Archetypal journey mapping
   - Personal mythology development

6. Psychological Growth Indicators:
   - Development milestones
   - Integration patterns
   - Shadow work progression
   - Individuation process markers

7. Predictive Analysis:
   - Pattern trajectory prediction
   - Potential future themes
   - Growth opportunity indicators
   - Suggested focus areas

8. Integration Recommendations:
   - Pattern-specific exercises
   - Symbol work suggestions
   - Personal growth practices
   - Dream journal prompts"""

        response = model.generate_content(prompt)
        pattern_analysis = response.text

        # Process dream dates for timeline
        dream_dates = {dream.date.strftime('%Y-%m-%d'): 1 for dream in dreams}
        
        # Calculate mood patterns with improved categorization
        mood_patterns = {}
        for dream in dreams:
            mood = dream.mood or 'unspecified'
            mood_patterns[mood] = mood_patterns.get(mood, 0) + 1

        # Extract common themes with enhanced pattern recognition
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
    """Extract common themes from the pattern analysis with improved recognition."""
    try:
        # Look for themes section with various possible headers
        themes_match = re.search(r'(?:Common themes|Thematic Analysis|Major Themes):(.*?)(?=\#|\Z)', 
                               analysis, re.DOTALL | re.IGNORECASE)
        if themes_match:
            themes_text = themes_match.group(1).strip()
            # Extract both bullet points and numbered items
            themes = re.findall(r'(?:[-*]|\d+\.)\s*([^\n]+)', themes_text)
            # Create a frequency dictionary for the themes
            theme_dict = {}
            for theme in themes:
                clean_theme = theme.strip()
                if clean_theme:
                    theme_dict[clean_theme] = theme_dict.get(clean_theme, 0) + 1
            return theme_dict
        return {'No themes found': 0}
    except Exception:
        return {'Error extracting themes': 0}
