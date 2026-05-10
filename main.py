import os
import json

# Import from our custom modules
from agents.context_parser import parse_resume_and_infer_role, get_job_recommendations
from agents.orchestrator import InterviewOrchestrator, InterviewState
from agents.evaluator import evaluate_answer
from agents.feedback import generate_final_report
from perception.audio_processor import AudioIntelligence
from perception.video_processor import VideoIntelligence

# --- CONFIGURATION ---
# The new SDK automatically detects the GEMINI_API_KEY environment variable.
# If you haven't set it in your terminal, it will fallback to this line:

def run_demo():
    print("--- 🤖 Intelligent Mock Interview Agent Starting ---")
    
    # 1. Parsing Context
    resume = "Student focusing on Software Engineering, DSA, DBMS, and OS. Project: Smart energy monitoring."
    print("\n[Step 1] Parsing Resume...")
    profile = parse_resume_and_infer_role(resume)
    role = profile['inferred_roles'][0]
    print(f"🎯 Target Role Identified: {role}")

    # 2. Job Discovery (Bonus feature)
    print("\n[Step 2] Discovering Best-Fit Jobs...")
    for job in get_job_recommendations(role):
        print(f"   -> {job['title']} at {job['company']} ({job['match']}% Match)")

    # 3. Setup the Interview Orchestrator
    state = InterviewState(role, profile['core_skills'])
    orchestrator = InterviewOrchestrator(state)
    
    print("\n--- 🎙️ Interview Start ---")
    
    # --- ROUND 1 ---
    q1 = orchestrator.generate_next_question()
    print(f"\nAgent: {q1}")
    
    # Simulate a candidate struggling 
    simulated_transcript = "Uh, I am like basically not really sure how that architecture works."
    print(f"You [Transcribed]: {simulated_transcript}")
    
    # Score the answer technically
    eval_score_1 = evaluate_answer(q1, simulated_transcript)
    state.history.append({"user": simulated_transcript, "evaluation": eval_score_1})
    
    # Simulate Audio Perception heuristics 
    audio_intel = AudioIntelligence()
    mock_audio_metrics = audio_intel._analyze_speech_patterns(simulated_transcript, duration_seconds=5)
    
    print(f"\n[System Log] Tech Correctness: {eval_score_1.get('correctness', 0)}% | Confidence Score: {mock_audio_metrics['confidence_score']}")
    
    # --- ROUND 2 (Agent Adapts) ---
    print("\n[Agent Intelligence] Detecting struggle... adapting difficulty...")
    q2 = orchestrator.generate_next_question(last_eval=eval_score_1, multimodal_metrics=mock_audio_metrics)
    print(f"\nAgent: {q2}")
    
    simulated_transcript_2 = "A relational database uses tables, while non-relational uses documents like JSON."
    print(f"You [Transcribed]: {simulated_transcript_2}")
    
    eval_score_2 = evaluate_answer(q2, simulated_transcript_2)
    state.history.append({"user": simulated_transcript_2, "evaluation": eval_score_2})

    # 4. Final Coaching Report
    print("\n--- 📊 Final Feedback & Coaching ---")
    
    # Aggregate data for the feedback agent
    final_metrics = {
        "average_confidence": mock_audio_metrics['confidence_score'], 
        "video_engagement": "High (Simulated)"
    }
    
    report = generate_final_report(state.history, final_metrics)
    print(f"Overall Score: {report.get('overall_score')}/100")
    print(f"\nTechnical Feedback:\n{report.get('technical_feedback')}")
    print(f"\nCommunication Feedback:\n{report.get('communication_feedback')}")
    print("\nAction Items:")
    for item in report.get('action_items', []):
        print(f"- {item}")

if __name__ == "__main__":
    run_demo()
