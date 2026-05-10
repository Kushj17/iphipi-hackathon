import os
import json
from datetime import datetime

def export_session_data(chat_history, metrics, report, role):
    """Dumps all raw metrics and transcripts into a new JSON file."""
    
    # Create the 'results' directory in the root folder if it doesn't exist
    os.makedirs("results", exist_ok=True)
    
    # Generate a unique filename using the current timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_role = role.replace(' ', '_').replace('/', '_')
    filename = f"results/raw_eval_data_{safe_role}_{timestamp}.json"
    
    # Assemble the massive data dictionary
    full_log = {
        "metadata": {
            "timestamp": timestamp,
            "target_role": role,
        },
        "transcript_and_agent_prompts": chat_history,
        "raw_multimodal_metrics": metrics, # Captures all audio, video, and code eval dictionaries
        "final_coaching_report": report
    }
    
    # Write to the new file
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(full_log, f, indent=4)
        
    return filename