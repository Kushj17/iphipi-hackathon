# File: agents/job_recommender.py
import requests
import json
from google import genai
from google.genai import types
import config

def fetch_live_jobs(target_role, rapidapi_key):
    """Fetches live job postings using the JSearch API (RapidAPI)."""
    if not rapidapi_key:
        print("[Warning] No RapidAPI key provided. Returning fallback data.")
        return _get_fallback_jobs(target_role)

    url = "https://jsearch.p.rapidapi.com/search"
    querystring = {"query": f"{target_role}", "page": "1", "num_pages": "1"}
    headers = {
        "x-rapidapi-key": rapidapi_key,
        "x-rapidapi-host": "jsearch.p.rapidapi.com"
    }

    try:
        response = requests.get(url, headers=headers, params=querystring)
        data = response.json()
        jobs = data.get('data', [])[:3] # Grab the top 3 jobs
        
        formatted_jobs = []
        for job in jobs:
            formatted_jobs.append({
                "title": job.get("job_title", "Unknown Role"),
                "company": job.get("employer_name", "Unknown Company"),
                "location": job.get("job_city", "") + ", " + job.get("job_country", ""),
                "description": job.get("job_description", "")[:500] + "...", # Truncate for the LLM
                "apply_link": job.get("job_apply_link", "#")
            })
        return formatted_jobs if formatted_jobs else _get_fallback_jobs(target_role)
    except Exception as e:
        print(f"[ERROR] Job search failed: {e}")
        return _get_fallback_jobs(target_role)

def rank_and_explain_jobs(live_jobs, candidate_profile):
    """Uses Gemini to score the jobs against the candidate's profile."""
    client = genai.Client()
    
    prompt = f"""
    You are an expert technical recruiter matching a candidate to live job postings.
    
    Candidate Profile (Extracted from Resume):
    {json.dumps(candidate_profile, indent=2)}
    
    Live Job Postings:
    {json.dumps(live_jobs, indent=2)}
    
    Task: For each job, generate a match score (0-100%) and a 1-2 sentence explanation of WHY it fits the candidate based on their skills and seniority.
    
    Output a JSON array of objects with exactly these keys:
    "company", "title", "match_score" (integer), "why_it_fits" (string), "apply_link" (string)
    
    Rank the array from highest match_score to lowest.
    """
    
    try:
        response = client.models.generate_content(
            model=config.DEFAULT_TEXT_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        
        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text.replace("```json", "", 1)
        if raw_text.endswith("```"):
            raw_text = raw_text[:raw_text.rfind("```")]
            
        return json.loads(raw_text.strip())
    except Exception as e:
        print(f"[ERROR] Match scoring failed: {e}")
        return []

def _get_fallback_jobs(target_role):
    """Hackathon-proof fallback just in case the API rate limits during a demo."""
    return [
        {
            "title": target_role,
            "company": "TechNova Solutions",
            "location": "Remote",
            "description": f"We are looking for a {target_role} to join our fast-paced backend team...",
            "apply_link": "https://linkedin.com/jobs"
        },
        {
            "title": f"Junior {target_role}",
            "company": "DataFlow Industries",
            "location": "New York, NY",
            "description": f"Great entry-level opportunity for a {target_role} with Python and cloud experience...",
            "apply_link": "https://indeed.com"
        }
    ]