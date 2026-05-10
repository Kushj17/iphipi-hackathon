import json
import re
from google import genai
from google.genai import types
import config

def parse_resume_and_infer_role(resume_text):
    """Extracts skills and infers target roles with hackathon-proof error handling."""
    print("[Debug] Sending request to Gemini...") 
    
    client = genai.Client()
    
    # UPDATED PROMPT: Capturing all PS requirements
    prompt = f"""
    Analyze this resume text as an expert tech recruiter and technical interviewer. 
    Output a JSON object with exactly these keys:
    1. "candidate_profile": object containing "seniority_signal" (e.g., Junior, Mid, Senior), "domain_exposure" (e.g., Fintech, E-commerce), and "key_projects" (list of brief project summaries).
    2. "inferred_roles": list of top 3 realistic job titles based on market patterns.
    3. "focus_areas": object containing:
        - "core_skills": list of top 5 technical skills to validate.
        - "weak_areas": list of 2 areas or gaps to probe.
        - "project_deep_dives": list of 2 specific questions to verify project impact and technical depth.
    Resume: {resume_text}
    """
    
    try:
        response = client.models.generate_content(
            model=config.DEFAULT_TEXT_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            )
        )
        print("[Debug] Received response from Gemini!")
        
        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text.replace("```json", "", 1)
        if raw_text.endswith("```"):
            raw_text = raw_text[:raw_text.rfind("```")]
            
        return json.loads(raw_text.strip())
        
    except Exception as e:
        print(f"[CRITICAL ERROR] Failed to parse resume: {e}")
        
        # UPDATED FALLBACK: Match the new JSON structure so the app doesn't crash
        return {
            "candidate_profile": {
                "seniority_signal": "Mid-Level",
                "domain_exposure": "General Software Development",
                "key_projects": ["Full-stack web application"]
            },
            "inferred_roles": ["Software Engineer (Fallback)"],
            "focus_areas": {
                "core_skills": ["Python", "Problem Solving", "System Design"],
                "weak_areas": ["API latency optimization", "Advanced CI/CD"],
                "project_deep_dives": ["Can you explain the architecture of your full-stack app?"]
            }
        }