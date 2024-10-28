import os
import google.generativeai as genai
from typing import List, Dict
import json
from collections import Counter

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

def analyze_dream(dream_content: str) -> str:
    prompt = f"""Analyze this dream and provide insights about its potential meaning, 
    common symbols, and psychological interpretation. Return the analysis in this JSON format:
    {{
        "symbols": "Key symbols and their meanings",
        "interpretation": "Overall dream interpretation",
        "emotions": "Emotional significance",
        "guidance": "Actionable insights or guidance"
    }}
    
    Dream: {dream_content}"""
    
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        
        try:
            # Clean the response text and ensure it's proper JSON
            clean_response = response.text.strip()
            if not clean_response.startswith('{'): 
                clean_response = '{' + clean_response.split('{', 1)[1]
            if not clean_response.endswith('}'): 
                clean_response = clean_response.rsplit('}', 1)[0] + '}'
            
            json_response = json.loads(clean_response)
            return json.dumps(json_response)
        except json.JSONDecodeError:
            return json.dumps({
                "symbols": "Unable to analyze symbols at this time",
                "interpretation": response.text[:500],
                "emotions": "Analysis unavailable",
                "guidance": "Please try again later"
            })
            
    except Exception as e:
        return json.dumps({
            "error": "Could not analyze dream at this time.",
            "details": str(e)
        })

def extract_dream_stats(dreams: List[dict]) -> dict:
    """Extract statistical patterns from dreams."""
    moods = Counter(dream['mood'] for dream in dreams)
    all_tags = []
    for dream in dreams:
        if dream['tags']:
            all_tags.extend([tag.strip() for tag in dream['tags'].split(',')])
    tags = Counter(all_tags)
    
    return {
        'most_common_mood': moods.most_common(1)[0] if moods else None,
        'most_common_tags': tags.most_common(5),
        'total_dreams': len(dreams),
        'mood_distribution': dict(moods)
    }

def analyze_dream_patterns(dreams: List[dict]) -> str:
    if not dreams:
        return json.dumps({
            "error": "No dreams available for analysis",
            "details": "Please log some dreams first to see patterns."
        })
    
    # Extract statistical patterns
    stats = extract_dream_stats(dreams)
    
    # Prepare the dreams data for analysis
    dreams_text = "\n".join([
        f"Dream {i+1}:\nDate: {dream['date']}\nTitle: {dream['title']}\n"
        f"Content: {dream['content']}\nMood: {dream['mood']}\n"
        f"Tags: {dream['tags']}\n"
        for i, dream in enumerate(dreams)
    ])
    
    prompt = f"""Analyze these dreams and identify deep psychological patterns, recurring themes, and provide meaningful insights. 
    Consider the following statistics while analyzing:
    - Most common mood: {stats['most_common_mood'][0] if stats['most_common_mood'] else 'N/A'}
    - Top tags: {', '.join(tag for tag, _ in stats['most_common_tags'])}
    - Total dreams analyzed: {stats['total_dreams']}
    
    Return the analysis in this exact JSON format:
    {{
        "Common Symbols and Themes": "Detailed analysis of recurring symbols, their psychological significance, and how they interconnect across dreams",
        "Emotional Patterns": "In-depth analysis of emotional patterns, mood transitions, and their potential connection to daily life",
        "Life Events and Concerns": "Analysis of how dreams might reflect current life situations, challenges, and subconscious concerns",
        "Personal Growth Indicators": "Identification of patterns suggesting personal development, psychological growth, or areas needing attention",
        "Actionable Insights": "Specific recommendations based on dream patterns for personal development and emotional well-being"
    }}
    
    Dreams to analyze:
    {dreams_text}"""
    
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        
        try:
            # Clean the response text and ensure it's proper JSON
            clean_response = response.text.strip()
            if not clean_response.startswith('{'): 
                clean_response = '{' + clean_response.split('{', 1)[1]
            if not clean_response.endswith('}'): 
                clean_response = clean_response.rsplit('}', 1)[0] + '}'
            
            # Parse and re-serialize to ensure valid JSON
            json_response = json.loads(clean_response)
            return json.dumps(json_response, ensure_ascii=False)
        except json.JSONDecodeError:
            # Create a structured response with available analysis
            return json.dumps({
                "Common Symbols and Themes": response.text[:500],
                "Emotional Patterns": "Analyzing emotional patterns...",
                "Life Events and Concerns": "Processing dream content...",
                "Personal Growth Indicators": "Identifying growth patterns...",
                "Actionable Insights": "Generating personalized insights..."
            }, ensure_ascii=False)
            
    except Exception as e:
        return json.dumps({
            "error": "Could not analyze dream patterns at this time.",
            "details": str(e)
        }, ensure_ascii=False)
