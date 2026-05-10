import json
from google import genai
from google.genai import types
import config

def generate_final_report(interview_history, aggregated_metrics):
    client = genai.Client()
    
    prompt = f"""
    You are an expert career coach grading a mock technical interview.
    
    Interview Transcript (Verbal Q&A):
    {json.dumps(interview_history, indent=2)}
    
    Candidate Metrics (Includes Audio, Video, Tech Q&A, and optional Coding Evals):
    {json.dumps(aggregated_metrics, indent=2)}
    
    Generate a highly actionable feedback report based heavily on the provided metrics. 
    If 'coding_evals' is present and not empty, incorporate their coding performance (scores, time complexity, bugs) into the 'technical_gaps' and heavily weight it into the 'overall_score'.
    
    Output a JSON object with exactly these keys:
    1. "overall_score": integer from 0 to 100.
    2. "technical_gaps": A paragraph summarizing technical strengths/gaps (include coding round feedback if available).
    3. "communication_improvements": A paragraph on vocal confidence, pitch, etc.
    4. "behavioural_insights": A paragraph on posture, eye contact, etc.
    5. "action_items": A list of 3 specific things to practice.
    """
    
    try:
        response = client.models.generate_content(
            model=config.DEFAULT_TEXT_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            )
        )
        
        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text.replace("```json", "", 1)
        if raw_text.endswith("```"):
            raw_text = raw_text[:raw_text.rfind("```")]
            
        return json.loads(raw_text.strip())
    except Exception as e:
        print(f"[ERROR] Feedback generation failed: {e}")
        return {
            "overall_score": 0,
            "technical_gaps": "Failed to generate technical report. Please check API logs.",
            "communication_improvements": "Failed to generate communication report. Please check API logs.",
            "behavioural_insights": "Failed to generate behavioural report. Please check API logs.",
            "action_items": []
        }