# Intelligent Mock Interview Agent

An Agentic AI mock interview platform that uses a candidate's resume to infer roles, suggest live jobs, and simulate a dynamic, multimodal interview adapting to technical skills and behavioral confidence. The platform leverages multiple AI agents for evaluation, dynamic question generation, and real-time feedback.

---

## Prerequisites

Before setting up the project, ensure you have the following installed:
- **Python 3.9+**
- **pip** (Python package installer)
- A valid **Gemini API Key** (for orchestration and multi-modal feedback)
- A valid **RapidAPI Key** (for JSearch API to fetch live job recommendations, set in `config.py`)

## Setup and Configuration

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Kushj17/iphipi-hackathon.git
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API Keys:**
   Create a `.env` file in the root directory based on the `.env.example` (or simply add your keys). Alternatively, set them as environment variables:
   
   **Linux/macOS**
   ```bash
   export GEMINI_API_KEY="your_gemini_api_key"
   export RAPIDAPI_KEY="your_rapidapi_key"
   ```

   **Windows (Command Prompt)**
   ```cmd
   set GEMINI_API_KEY=your_gemini_api_key
   set RAPIDAPI_KEY=your_rapidapi_key
   ```
   
   **Windows (PowerShell)**
   ```powershell
   $env:GEMINI_API_KEY="your_gemini_api_key"
   $env:RAPIDAPI_KEY="your_rapidapi_key"
   ```

## Running the Solution

You can run the web-based interactive Streamlit app using a single command:

```bash
streamlit run app.py
```

*(Note: The app will open automatically in your default web browser).*

Alternatively, if you want to run the terminal-based demo simulation:
```bash
python main.py
```

---

## Project Structure Overview

```text
.
├── agents/                 # Core AI agents driving the interview logic
│   ├── context_parser.py   # Extracts context from resume & infers target role
│   ├── evaluator.py        # Evaluates technical answers and coding submissions
│   ├── feedback.py         # Generates final reports and coaching insights
│   ├── job_recommender.py  # Fetches and ranks live job postings
│   └── orchestrator.py     # Manages interview state, generates questions and hints
├── data/                   # Data storage for assets or temporary files
├── perception/             # Multimodal processing modules
│   ├── audio_processor.py  # Analyzes audio transcripts and speech confidence
│   └── video_processor.py  # Analyzes facial expressions and engagement via DeepFace/OpenCV
├── results/                # Output directory for saved session data
├── utils/                  # Helper utilities
│   ├── document_processor.py # PDF extraction logic
│   └── logger.py           # Logging and session export functionality
├── video_recorder/         # Custom Streamlit component for live video capture
├── app.py                  # Main Streamlit application (Web UI)
├── config.py               # Global configuration and model selection
├── main.py                 # CLI demo for testing agent interactions
└── requirements.txt        # Python dependencies
```

## How the Agents & Modules Interact

1. **Initialization (`app.py`, `context_parser.py`):** 
   The candidate uploads their resume via the UI (`app.py`). The `context_parser.py` agent extracts key skills, projects, and experiences to infer a specific role (e.g., Backend Engineer).
2. **Job Recommendation (`job_recommender.py`):**
   Simultaneously, `job_recommender.py` queries the JSearch API (via RapidAPI) to find live jobs matching the inferred role, and ranks them against the candidate's profile.
3. **Interview Orchestration (`orchestrator.py`):**
   The `orchestrator.py` initializes an `InterviewState`. It uses the parsed context to dynamically generate the first question and a hint.
4. **Multimodal Perception (`perception/`):**
   When the user answers (via live video, audio, or uploaded file), `app.py` passes the media payload to `audio_processor.py` (transcription and audio metrics) and `video_processor.py` (facial engagement, using DeepFace/OpenCV).
5. **Evaluation & Adaptation (`evaluator.py`, `orchestrator.py`):**
   The `evaluator.py` agent evaluates the transcribed answer against expected core skills or evaluates code submissions if in the coding round. The Orchestrator receives the technical correctness score and multimodal metrics, dynamically adapting the next question's difficulty and tone.
6. **Final Coaching (`feedback.py`):**
   Once the rounds conclude, `feedback.py` synthesizes the chat history, coding evaluations, and perceptual metrics to deliver a comprehensive actionable report, logging data via `logger.py`.

---

## Sample Evaluation Data

For quick evaluation and testing, you can find sample inputs and expected outputs in the `results/` folder:
- **Sample Inputs:** `results/example_1_resume.pdf` and `results/example_2_resume.pdf` 
- **Expected Outputs:** `results/example_1.json` and `results/example_2.json` (contains raw multimodal metrics, LLM semantic scores, and the final coaching report).