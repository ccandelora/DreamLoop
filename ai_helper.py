import os
import google.generativeai as genai
from typing import List
import json

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

def analyze_dream(dream_content: str) -> str:
    prompt = f"""Analyze this dream and provide insights about its potential meaning, 
    common symbols, and psychological interpretation in JSON format. Dream: {dream_content}"""
    
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return '{"error": "Could not analyze dream at this time."}'

def analyze_dream_patterns(dreams: List[dict]) -> str:
    if not dreams:
        return json.dumps({"error": "No dreams available for analysis"})
    
    # Prepare the dreams data for analysis
    dreams_text = "\n".join([
        f"Dream {i+1}:\nDate: {dream['date']}\nTitle: {dream['title']}\n"
        f"Content: {dream['content']}\nMood: {dream['mood']}\n"
        f"Tags: {dream['tags']}\n"
        for i, dream in enumerate(dreams)
    ])
    
    prompt = f"""Analyze these dreams and identify patterns, recurring themes, and psychological insights. 
    Focus on:
    1. Common symbols or themes
    2. Emotional patterns and mood trends
    3. Potential life events or concerns reflected
    4. Personal growth indicators
    5. Actionable insights
    
    Return the analysis in JSON format with these sections.
    Dreams to analyze:
    {dreams_text}"""
    
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return json.dumps({"error": "Could not analyze dream patterns at this time."})
