import os
import streamlit as st
import streamlit.components.v1 as components
import base64
import concurrent.futures
import config
import threading

from utils.document_processor import extract_text_from_pdf
from utils.logger import export_session_data
from agents.context_parser import parse_resume_and_infer_role
from agents.orchestrator import InterviewOrchestrator, InterviewState
from agents.job_recommender import fetch_live_jobs, rank_and_explain_jobs

import json
from datetime import datetime

# --- NEW FEATURE: History Management Helpers ---
HISTORY_FILE = "interview_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

def save_history(record):
    history = load_history()
    history.append(record)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)


# --- FIX: Added initial_sidebar_state="expanded" ---
st.set_page_config(
    page_title="Intelligent Mock Interview Agent", 
    layout="wide",
    initial_sidebar_state="expanded" 
)

st.title(" Intelligent Mock Interview Agent")


# ==========================================
# 1. Initialize Session State Variables
# ==========================================
if 'interview_state' not in st.session_state:
    st.session_state.interview_state = None
if 'orchestrator' not in st.session_state:
    st.session_state.orchestrator = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'audio_key' not in st.session_state:       
    st.session_state.audio_key = 0            
if 'session_metrics' not in st.session_state:
    st.session_state.session_metrics = {
        "technical_evals": [], 
        "audio_evals": [], 
        "video_evals": []
    }
if 'job_search_status' not in st.session_state:
    st.session_state.job_search_status = {"jobs": [], "completed": False}

if 'interview_rounds' not in st.session_state:
    st.session_state.interview_rounds = [] 
if 'current_q_index' not in st.session_state:
    st.session_state.current_q_index = 0   
if 'highest_q_index' not in st.session_state:
    st.session_state.highest_q_index = 0   
if 'interview_complete' not in st.session_state:
    st.session_state.interview_complete = False

# Coding variables
if 'in_coding_round' not in st.session_state:
    st.session_state.in_coding_round = False
if 'coding_questions' not in st.session_state:
    st.session_state.coding_questions = [] 
if 'current_coding_index' not in st.session_state:
    st.session_state.current_coding_index = 0
if 'coding_evals' not in st.session_state.session_metrics:
    st.session_state.session_metrics["coding_evals"] = []
if 'history_saved' not in st.session_state:
    st.session_state.history_saved = False
if 'viewing_history' not in st.session_state:
    st.session_state.viewing_history = False


# ==========================================
# NEW FEATURE: Dedicated History Page View
# ==========================================
if st.session_state.viewing_history:
    st.markdown("## 📈 Historical Performance Tracking")
    
    if st.button("🔙 Back to Home", type="secondary"):
        st.session_state.viewing_history = False
        st.rerun()
        
    st.markdown("---")
        
    history_data = load_history()
    if history_data:
        st.write(f"**Total Mock Interviews:** {len(history_data)}")
        
        # Draw a line chart of their scores over time
        chart_data = [{"Interview": i + 1, "Score": entry['score']} for i, entry in enumerate(history_data)]
        st.line_chart(chart_data, x="Interview", y="Score")
        
        st.markdown("### Past Interviews")
        total_interviews = len(history_data)
        for i, entry in enumerate(reversed(history_data)):
            interview_num = total_interviews - i 
            
            with st.expander(f"Interview {interview_num} | {entry['date']} - {entry['role']}"):
                st.metric("Score", f"{entry['score']}/100")
                st.write("**Top Action Items:**")
                for item in entry.get('action_items', [])[:2]: 
                    st.caption(f"- {item}")
    else:
        st.info("No past interviews found. Complete your first interview to see your progress here!")

# ==========================================
# Step 1: Resume Upload & Context Extraction
# ==========================================
elif st.session_state.interview_state is None:
    
    # --- UI Layout: Title and History Button ---
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("### Step 1: Upload Resume")
    with col2:
        if st.button(" View History", use_container_width=True):
            st.session_state.viewing_history = True
            st.rerun()
            
    upload_method = st.radio("Choose input method:", ("Upload PDF", "Paste Text"))
    
    resume_text = ""
    # ... (The rest of your Step 1 code continues normally below this) ...
    if upload_method == "Upload PDF":
        uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
        if uploaded_file: 
            resume_text = extract_text_from_pdf(uploaded_file)
    else:
        resume_text = st.text_area("Paste your resume content here:")

    st.markdown("###  Select Interview Track")
    interview_track = st.selectbox(
        "Choose your interview domain (or let AI decide):", 
        [
            "Auto-Detect from Resume", 
            "Backend Engineer", 
            "Machine Learning Engineer", 
            "Embedded Systems Engineer", 
            "Frontend Engineer", 
            "Data Scientist",
            "Full Stack Engineer",
            "Quantum Engineer"
        ]
    )

    if st.button("Start Interview", type="primary"):
        if resume_text:
            with st.status("Analyzing Profile & Scanning Job Market...", expanded=True) as status:
                
                st.write(" Step 1: Extracting deep context from resume...")
                profile = parse_resume_and_infer_role(resume_text)
                
                if interview_track == "Auto-Detect from Resume":
                    target_role = profile['inferred_roles'][0] if profile['inferred_roles'] else "Software Engineer"
                else:
                    target_role = interview_track
                    
                st.write(" Step 2: Scanning live jobs in the background...")
                
                # Create a worker function for the thread
                def background_job_search(role, cand_profile, status_dict):
                    try:
                        live = fetch_live_jobs(role, config.RAPIDAPI_KEY)
                        status_dict["jobs"] = rank_and_explain_jobs(live, cand_profile)
                    except Exception as e:
                        print(f"Background thread failed: {e}")
                    finally:
                        status_dict["completed"] = True

                # Fire off the thread and let it run independently!
                job_thread = threading.Thread(
                    target=background_job_search,
                    args=(target_role, profile['candidate_profile'], st.session_state.job_search_status)
                )
                job_thread.start()
                
                st.write(" Step 3: Configuring AI Agent Strategy...")
                st.session_state.interview_state = InterviewState(
                    target_role=target_role, 
                    candidate_profile=profile['candidate_profile'],
                    focus_areas=profile['focus_areas']
                )
                st.session_state.orchestrator = InterviewOrchestrator(st.session_state.interview_state)
                
                st.write(" Step 4: Generating your first personalized question...")
                first_q = st.session_state.orchestrator.generate_next_question() 
                first_hint = st.session_state.orchestrator.generate_hint(first_q)
                
                st.session_state.interview_rounds.append({
                    "question": first_q, 
                    "answered": False, 
                    "logs": [],
                    "hint": first_hint,
                    "hint_revealed": False
                })
                st.session_state.chat_history.append({"role": "agent", "content": first_q})
                
                status.update(label="Interview Ready!", state="complete", expanded=False)
                
            st.rerun()

# ==========================================
# Step 2: The Multimodal Interview Loop
# ==========================================
elif not st.session_state.interview_complete:
    
    if st.session_state.in_coding_round:
        # --- NEW FEATURE: Exit Back to Interview Button ---
        col_title, col_exit = st.columns([4, 1])
        with col_title:
            st.markdown(f"###  Technical Coding Round: {st.session_state.interview_state.target_role}")
        with col_exit:
            if st.button("🔙 Return to Q&A", use_container_width=True):
                st.session_state.in_coding_round = False
                st.rerun()
                
        st.info("This is an optional coding round. You can attempt up to 2 problems.")
        
        # Initialize the first problem if empty
        if len(st.session_state.coding_questions) == 0:
            with st.spinner("Generating role-specific coding problem..."):
                st.session_state.coding_questions.append({
                    "problem": st.session_state.orchestrator.generate_coding_problem(),
                    "answered": False,
                    "code": "",
                    "eval": None
                })
                
        # --- NEW FEATURE: Switch Between Coding Questions ---
        num_coding_qs = len(st.session_state.coding_questions)
        nav_cols = st.columns(min(num_coding_qs + 1, 2)) 
        
        # Render tabs for existing questions
        for i in range(num_coding_qs):
            with nav_cols[i]:
                btn_type = "primary" if i == st.session_state.current_coding_index else "secondary"
                if st.button(f"Problem {i+1}", type=btn_type, use_container_width=True, key=f"switch_prob_{i}"):
                    st.session_state.current_coding_index = i
                    st.rerun()
                    
        # Render button to add the 2nd question if it doesn't exist yet
        if num_coding_qs < 2:
            with nav_cols[num_coding_qs]:
                if st.button(" 2nd Problem", use_container_width=True):
                    with st.spinner("Generating 2nd problem..."):
                        st.session_state.coding_questions.append({
                            "problem": st.session_state.orchestrator.generate_coding_problem(),
                            "answered": False, "code": "", "eval": None
                        })
                        st.session_state.current_coding_index = 1 # Jump to new problem
                    st.rerun()

        st.markdown("---")
        
        curr_code_idx = st.session_state.current_coding_index
        current_prob = st.session_state.coding_questions[curr_code_idx]
        
        st.markdown(f"#### Problem {curr_code_idx + 1} Statement")
        st.write(current_prob["problem"])
        st.markdown("---")
        
        if current_prob["answered"]:
            st.success(" Code Submitted!")
            eval_data = current_prob["eval"]
            col1, col2, col3 = st.columns(3)
            col1.metric("Logic Score", f"{eval_data.get('score', 0)}/100")
            col2.metric("Time Complexity", eval_data.get('time_complexity', 'N/A'))
            col3.metric("Space Complexity", eval_data.get('space_complexity', 'N/A'))
            st.write(f"**AI Code Review:** {eval_data.get('feedback', '')}")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(" Finish Entire Interview & View Results", type="primary", key=f"finish_int_{curr_code_idx}"):
                st.session_state.interview_complete = True
                st.rerun()
                    
        else:
            # Code Editor UI
            # Using dynamic keys ensures Streamlit remembers the typed code if they switch tabs and come back!
            selected_lang = st.selectbox("Select Language", ["Python", "JavaScript", "C++", "Java", "Go", "Rust"], key=f"lang_{curr_code_idx}")
            candidate_code = st.text_area("Write your code here:", height=300, key=f"code_input_{curr_code_idx}")
            
            if st.button(" Run & Submit Code", type="primary", key=f"submit_btn_{curr_code_idx}"):
                if candidate_code.strip() == "":
                    st.error("Please write some code before submitting!")
                else:
                    with st.spinner("AI is reviewing your code..."):
                        from agents.evaluator import evaluate_code_submission
                        code_eval = evaluate_code_submission(current_prob["problem"], candidate_code, selected_lang)
                        
                        st.session_state.coding_questions[curr_code_idx]["answered"] = True
                        st.session_state.coding_questions[curr_code_idx]["eval"] = code_eval
                        st.session_state.coding_questions[curr_code_idx]["code"] = candidate_code
                        st.session_state.session_metrics["coding_evals"].append(code_eval)
                    st.rerun()


    else:
        max_q = st.session_state.interview_state.max_questions
        st.markdown(f"###  Target Role: {st.session_state.interview_state.target_role}")
        
        # Top Navigation Bar
        nav_cols = st.columns([1, 1, 1, 1, 2, 2.5])
        
        for i in range(max_q):
            with nav_cols[i]: 
                is_disabled = i > st.session_state.highest_q_index
                if st.button(f"Q {i+1}", disabled=is_disabled, use_container_width=True, key=f"nav_q_{i}"):
                    st.session_state.current_q_index = i
                    st.session_state.in_coding_round = False 
                    st.rerun()
                    
        with nav_cols[4]:
            if st.button(" Coding Round", type="secondary", use_container_width=True):
                st.session_state.in_coding_round = True
                st.rerun()
                
        with nav_cols[5]:      
            if st.button("⏭ Skip to Results", type="primary", use_container_width=True):
                st.session_state.interview_complete = True
                st.rerun()
                    
        st.markdown("---")
        
        curr_i = st.session_state.current_q_index
        current_round = st.session_state.interview_rounds[curr_i]
        
        st.info(f" **Question {curr_i + 1} of {max_q}**")
        with st.chat_message("assistant"):
            st.write(current_round["question"])

        
        if current_round["answered"]:
            st.markdown("### Your Answer Analysis")
            for log in current_round["logs"]:
                with st.chat_message("user"):
                    st.write(log)
                    
            st.markdown("<br>", unsafe_allow_html=True)
            
            if curr_i < max_q - 1:
                if st.button(" Go to Next Question", type="primary", use_container_width=True):
                    st.session_state.current_q_index += 1
                    st.rerun()
            elif curr_i == max_q - 1:
                if st.button(" Finish Interview", type="primary", use_container_width=True):
                    st.session_state.interview_complete = True
                    st.rerun()
        else:
            st.markdown("### Your Turn to Answer")
            
            # Instant Hint Reveal UI
            if not current_round.get("hint_revealed", False):
                if st.button("💡 I'm stuck, can I get a hint?", type="secondary"):
                    st.session_state.interview_rounds[curr_i]["hint_revealed"] = True
                    st.rerun() 
            else:
                st.info(f" Coach's Hint: {current_round.get('hint', 'Break the problem down into smaller steps.')}")
                
            st.markdown("<br>", unsafe_allow_html=True)
            
            input_method = st.radio("Choose input method:", [
                "🎥 Live Video", 
                "🎙️ Live Audio", 
                "📁 Upload File"
            ], horizontal=True)
            
            media_bytes_to_process = None
            mime_type_to_process = None
            is_audio_only = False
            
            if input_method == "🎥 Live Video":
                video_recorder = components.declare_component("video_recorder", path="video_recorder")
                base64_video = video_recorder(key=f"recorder_{st.session_state.audio_key}")
                
                if base64_video:
                    header, encoded = base64_video.split(",", 1)
                    media_bytes_to_process = base64.b64decode(encoded)
                    mime_type_to_process = header.split(":")[1].split(";")[0]
                    
            elif input_method == "🎙️ Live Audio":
                audio_file = st.audio_input("Record your spoken answer", key=f"audio_recorder_{st.session_state.audio_key}")
                if audio_file:
                    if st.button(" Submit Audio Answer", type="primary", use_container_width=True):
                        media_bytes_to_process = audio_file.read()
                        mime_type_to_process = "audio/wav"
                        is_audio_only = True
                    
            else:
                uploaded_file = st.file_uploader("Upload an answer (.mp4, .webm, .mp3, .wav)", type=["mp4", "webm", "mp3", "wav"])
                if uploaded_file and st.button("Submit Uploaded Answer", type="primary", use_container_width=True):
                    media_bytes_to_process = uploaded_file.read()
                    mime_type_to_process = uploaded_file.type
                    if "audio" in mime_type_to_process or uploaded_file.name.endswith(('mp3', 'wav')):
                        is_audio_only = True

            # Process Media & Evaluate
            if media_bytes_to_process:
                with st.spinner(" Analyzing Answer..."):
                    from agents.evaluator import evaluate_answer
                    from perception.audio_processor import analyze_candidate_audio
                    
                    if is_audio_only:
                        cv_metrics = {"engagement_score": 0.5, "posture_alignment": "N/A", "facial_expression": "Neutral"}
                        audio_metrics = analyze_candidate_audio(media_bytes_to_process, mime_type=mime_type_to_process)
                    else:
                        from perception.video_processor import analyze_candidate_video 
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            video_future = executor.submit(analyze_candidate_video, media_bytes_to_process)
                            audio_future = executor.submit(analyze_candidate_audio, media_bytes_to_process, mime_type_to_process) 
                            cv_metrics = video_future.result()
                            audio_metrics = audio_future.result()
                    
                    candidate_transcript = audio_metrics.get("transcript", "Transcription failed.")
                    candidate_core_skills = st.session_state.interview_state.focus_areas.get('core_skills', [])
                    technical_eval = evaluate_answer(current_round["question"], candidate_transcript, candidate_core_skills)
                    
                    combined_metrics = {
                        "confidence_score": audio_metrics.get("confidence_score", 0.5),
                        "engagement_score": cv_metrics.get("engagement_score", 0.5),
                        "facial_expression": cv_metrics.get("facial_expression", "Neutral")
                    }
                    
                    st.session_state.session_metrics["technical_evals"].append(technical_eval)
                    st.session_state.session_metrics["audio_evals"].append(audio_metrics)
                    st.session_state.session_metrics["video_evals"].append(cv_metrics)
                    
                    if is_audio_only:
                        log_1 = " **Visual Logs:** None (Audio Only)"
                    else:
                        log_1 = f" **Visual Logs:** Engagement: {cv_metrics.get('engagement_score', 0)} | Emotion: {cv_metrics.get('facial_expression', 'Unknown').capitalize()}"
                    log_2 = f" **Answer evaluation:** Correctness Score: {technical_eval['correctness']}/100 | Depth: {technical_eval['depth']}"
                    
                    st.session_state.interview_rounds[curr_i]["answered"] = True
                    st.session_state.interview_rounds[curr_i]["logs"] = [log_1, log_2]
                    st.session_state.chat_history.append({"role": "user", "content": log_1})
                    st.session_state.chat_history.append({"role": "user", "content": log_2})
                    
                    st.session_state.audio_key += 1 

                    # Instant Background Pre-Fetching
                    if curr_i < max_q - 1:
                        next_q = st.session_state.orchestrator.generate_next_question(
                            last_eval=technical_eval, 
                            multimodal_metrics=combined_metrics
                        )
                        next_hint = st.session_state.orchestrator.generate_hint(next_q)
                        
                        st.session_state.chat_history.append({"role": "agent", "content": next_q})
                        st.session_state.interview_rounds.append({
                            "question": next_q, 
                            "answered": False, 
                            "logs": [],
                            "hint": next_hint,
                            "hint_revealed": False
                        })
                        st.session_state.highest_q_index += 1
                    else:
                        st.session_state.highest_q_index += 1

                st.rerun()

# ==========================================
# Step 3: Final Results & Job Recommendations
# ==========================================
else:
    st.success("🎉 Interview Complete! View your results and suitable job postings below.")
    
    with st.spinner("Compiling multi-modal feedback..."):
        from agents.feedback import generate_final_report
        
        final_report = generate_final_report(
            interview_history=st.session_state.chat_history, 
            aggregated_metrics=st.session_state.session_metrics
        )

        if not st.session_state.history_saved:
            record = {
                "date": datetime.now().strftime("%b %d, %H:%M"),
                "role": st.session_state.interview_state.target_role,
                "score": final_report.get('overall_score', 0),
                "action_items": final_report.get('action_items', [])
            }
            save_history(record)
            st.session_state.history_saved = True # Prevent duplicate saves
        
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            st.markdown("##  Interview Report")
            st.metric(label="Overall Readiness Score", value=f"{final_report.get('overall_score', 0)}/100")
            
            st.markdown("###  Technical Feedback")
            st.write(final_report.get('technical_gaps', final_report.get('technical_feedback', 'No technical feedback generated.')))
            
            st.markdown("###  Communication Insights")
            st.write(final_report.get('communication_improvements', final_report.get('communication_feedback', 'No communication feedback generated.')))
            
            st.markdown("###  Behavioural Insights")
            st.write(final_report.get('behavioural_insights', 'No behavioural feedback generated.'))
            
            st.markdown("###  Action Items")
            for item in final_report.get('action_items', []):
                st.markdown(f"- {item}")    
        
        with col_right:
            st.markdown("## 💼 Recommended Jobs")
            
            # Check if the background thread is done
            if not st.session_state.job_search_status["completed"]:
                st.info("🔄 Still compiling your best job matches... check back in a few seconds!")
                
            elif st.session_state.job_search_status["jobs"]:
                for job in st.session_state.job_search_status["jobs"]:
                    with st.container(border=True):
                        score = job.get('match_score', 0)
                        color = "green" if score >= 80 else "orange" if score >= 60 else "red"
                        
                        st.markdown(f"#### {job.get('title', 'Role')}")
                        st.markdown(f"**{job.get('company', 'Company')}**")
                        st.markdown(f"Match: <span style='color:{color}; font-weight:bold;'>{score}%</span>", unsafe_allow_html=True)
                        st.write(job.get('why_it_fits', ''))
                        st.markdown(f"[Apply Now]({job.get('apply_link', '#')})")
            else:
                st.write("No direct matches found. Try refining your resume context.")
                
    st.markdown("---")

    st.markdown("### Save Output")
    st.info("Click below to dump all raw scoring metrics, transcripts, and model evaluations into a JSON file.")
    if st.button("Export valuation Data", type="secondary"):
        saved_filepath = export_session_data(
            chat_history=st.session_state.chat_history,
            metrics=st.session_state.session_metrics,
            report=final_report,
            role=st.session_state.interview_state.target_role
        )
        st.success(f"✅ Raw data successfully saved to: `{saved_filepath}`")

    st.markdown("---")
    
    col_space1, col_btn, col_space2 = st.columns([1, 2, 1])
    with col_btn:
        if st.button("🔄 Start a New Interview", type="primary", use_container_width=True):
            st.session_state.interview_state = None
            st.session_state.orchestrator = None
            st.session_state.chat_history = []
            st.session_state.session_metrics = {"technical_evals": [], "audio_evals": [], "video_evals": []}
            st.session_state.ranked_jobs = []
            st.session_state.interview_rounds = []
            st.session_state.current_q_index = 0
            st.session_state.highest_q_index = 0
            st.session_state.interview_complete = False
            st.session_state.audio_key = 0
            st.session_state.in_coding_round = False
            st.session_state.coding_questions = []
            st.session_state.current_coding_index = 0
            st.session_state.history_saved = False
            st.rerun()