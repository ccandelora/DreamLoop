import os
import google.generativeai as genai
from typing import List, Dict
import json

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
        
        # Ensure response is valid JSON
        try:
            json_response = json.loads(response.text)
            return json.dumps(json_response)
        except json.JSONDecodeError:
            return json.dumps({
                "symbols": "Unable to analyze symbols at this time",
                "interpretation": response.text,
                "emotions": "Analysis unavailable",
                "guidance": "Please try again later"
            })
            
    except Exception as e:
        return json.dumps({
            "error": "Could not analyze dream at this time.",
            "details": str(e)
        })

def analyze_dream_patterns(dreams: List[dict]) -> str:
    if not dreams:
        return json.dumps({
            "error": "No dreams available for analysis",
            "details": "Please log some dreams first to see patterns."
        })
    
    # Prepare the dreams data for analysis
    dreams_text = "\n".join([
        f"Dream {i+1}:\nDate: {dream['date']}\nTitle: {dream['title']}\n"
        f"Content: {dream['content']}\nMood: {dream['mood']}\n"
        f"Tags: {dream['tags']}\n"
        for i, dream in enumerate(dreams)
    ])
    
    prompt = f"""Analyze these dreams and identify patterns, recurring themes, and psychological insights. 
    Return the analysis in this exact JSON format:
    {{
        "Common Symbols and Themes": "List and analysis of recurring symbols and themes",
        "Emotional Patterns": "Analysis of emotional patterns and mood trends",
        "Life Events and Concerns": "Potential life events or concerns reflected",
        "Personal Growth Indicators": "Signs of personal growth or development",
        "Actionable Insights": "Practical steps or insights based on the patterns"
    }}
    
    Dreams to analyze:
    {dreams_text}"""
    
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        
        # Ensure response is valid JSON
        try:
            json_response = json.loads(response.text)
            return json.dumps(json_response)
        except json.JSONDecodeError:
            # If the response isn't valid JSON, structure it into our expected format
            return json.dumps({
                "Common Symbols and Themes": "Analysis in progress",
                "Emotional Patterns": response.text,
                "Life Events and Concerns": "Pattern analysis unavailable",
                "Personal Growth Indicators": "Please try again later",
                "Actionable Insights": "System is learning from your dreams"
            })
            
    except Exception as e:
        return json.dumps({
            "error": "Could not analyze dream patterns at this time.",
            "details": str(e)
        })
