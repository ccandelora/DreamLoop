import os
import google.generativeai as genai

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

def analyze_dream(dream_content: str) -> str:
    prompt = f"""Analyze this dream and provide insights about its potential meaning, 
    common symbols, and psychological interpretation in JSON format. Dream: {dream_content}"""
    
    try:
        # Initialize the model
        model = genai.GenerativeModel('gemini-pro')
        
        # Generate the response
        response = model.generate_content(prompt)
        
        # Get the text from the response
        return response.text
    except Exception as e:
        return '{"error": "Could not analyze dream at this time."}'
