import json
from google import genai
from google.genai import types
import config # Using your new centralized config!

def analyze_candidate_audio(video_bytes, mime_type="video/webm"):
    """Analyzes the audio track of a video file for transcription, tone, and confidence."""
    print("[Debug] Sending media to Gemini for audio analysis...")
    
    client = genai.Client()
    
    # Updated prompt to acknowledge it's a video file, but focus on audio
    prompt = """
    You are an expert AI speech analyst evaluating a candidate's interview response.
    Listen to the audio track of the provided video file and output a JSON object with exactly these keys:
    1. "transcript": The exact speech-to-text transcription of what the candidate said.
    2. "tone": A short string describing the vocal tone (e.g., "Professional", "Nervous", "Enthusiastic").
    3. "pitch_variation": A short string assessing pitch (e.g., "Monotone", "Expressive").
    4. "hesitations_pauses": A string describing the flow (e.g., "Frequent 'um's and long pauses", "Smooth delivery").
    5. "confidence_score": A float between 0.0 and 1.0.
    6. "communication_clarity_score": A float between 0.0 and 1.0.
    """
    
    try:
        response = client.models.generate_content(
            model=config.MULTIMODAL_AUDIO_MODEL,
            contents=[
                types.Part.from_bytes(data=video_bytes, mime_type=mime_type),
                prompt
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            )
        )
        
        clean_content = response.text.strip()
        if clean_content.startswith("```"):
            clean_content = clean_content.split("```")[1]
            if clean_content.startswith("json"):
                clean_content = clean_content[4:]
        
        return json.loads(clean_content)
        
    except Exception as e:
        error_msg = str(e)
        print(f"[CRITICAL ERROR] Audio processing failed: {error_msg}")
        
        # Inject the actual error into the UI so we can see what went wrong!
        return {
            "transcript": f"⚠️ API Error: {error_msg[:150]}",
            "tone": "Neutral",
            "pitch_variation": "Normal",
            "hesitations_pauses": "None",
            "confidence_score": 0.5,
            "communication_clarity_score": 0.5
        }