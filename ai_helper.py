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
            # If JSON parsing fails, create a structured response
            return json.dumps({
                "Common Symbols and Themes": response.text[:500],
                "Emotional Patterns": "Analysis in progress",
                "Life Events and Concerns": "Processing patterns",
                "Personal Growth Indicators": "Analyzing growth trends",
                "Actionable Insights": "Generating insights"
            })
            
    except Exception as e:
        return json.dumps({
            "error": "Could not analyze dream patterns at this time.",
            "details": str(e)
        })
