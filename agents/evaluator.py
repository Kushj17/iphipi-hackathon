import json
from google import genai
from google.genai import types
import config

def evaluate_answer(question, answer_transcript, core_skills):
    print("[Debug] Running Technical Evaluation Engine...")
    
    # Layer 1: Keyword/Intent Matching 
    normalized_answer = answer_transcript.lower()
    matched_keywords = [skill for skill in core_skills if skill.lower() in normalized_answer]
    keyword_score = min(len(matched_keywords) * 25, 100) 
    
    # Layer 2: LLM-based Semantic Scoring 
    client = genai.Client()
    prompt = f"""
    Evaluate this technical interview response for a {question}.
    Candidate Answer: "{answer_transcript}"
    
    Focus on technical accuracy and depth. Ignore speech-to-text errors.
    Output JSON:
    1. "semantic_score": integer (0-100)
    2. "depth_of_knowledge": string (e.g., "Surface Level", "Practical", "Deep Systems Level")
    3. "gaps": string (identified missing concepts)
    """
    
    try:
        response = client.models.generate_content(
            model=config.DEFAULT_TEXT_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        llm_eval = json.loads(response.text.strip())
    except Exception as e:
        print(f"[ERROR] Semantic evaluation failed: {e}")
        llm_eval = {"semantic_score": 50, "depth_of_knowledge": "Unknown", "gaps": "Evaluation error."}
        
    # Layer 3: Weighted Aggregation 
    final_correctness = int((keyword_score * 0.3) + (llm_eval["semantic_score"] * 0.7))
    
    return {
        "correctness": final_correctness,  
        "depth": llm_eval["depth_of_knowledge"], 
        "keywords": matched_keywords,
        "gaps": llm_eval["gaps"]
    }

def evaluate_code_submission(problem_description, candidate_code, language):
    print(f"[Debug] Evaluating {language} code submission...")
    client = genai.Client()
    
    prompt = f"""
    You are an expert technical interviewer evaluating a coding round.
    Problem: {problem_description}
    Language Used: {language}
    Candidate Code:
    ```
    {candidate_code}
    ```
    
    Evaluate the code and output a JSON object with EXACTLY these keys:
    1. "score": integer (0-100) based on logic correctness and syntax.
    2. "time_complexity": string (e.g., "O(N)", "O(N^2)")
    3. "space_complexity": string (e.g., "O(1)", "O(N)")
    4. "feedback": A short 2-sentence review highlighting bugs, optimizations, or praising the logic.
    """
    
    try:
        response = client.models.generate_content(
            model=config.DEFAULT_TEXT_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        return json.loads(response.text.strip())
    except Exception as e:
        print(f"[ERROR] Code evaluation failed: {e}")
        return {"score": 0, "time_complexity": "Unknown", "space_complexity": "Unknown", "feedback": "Code evaluation failed due to API error."}