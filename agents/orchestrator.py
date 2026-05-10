from google import genai
import config 

class InterviewState:
    def __init__(self, target_role, candidate_profile, focus_areas):
        self.target_role = target_role
        self.candidate_profile = candidate_profile
        self.focus_areas = focus_areas
        self.difficulty_level = "medium"
        self.consecutive_failures = 0
        self.history = []
        self.max_questions = 4  

class InterviewOrchestrator:
    def __init__(self, state: InterviewState):
        self.state = state
        self.client = genai.Client()

    def generate_next_question(self, last_eval=None, multimodal_metrics=None, stream=False):
        # 1. Base instruction based on performance
        instruction = "Keep the interview steady and professional."
        
        if last_eval and multimodal_metrics:
            correctness = last_eval.get('correctness', 100)
            confidence = multimodal_metrics.get('confidence_score', 1.0)
            
            # --- IMPLEMENTATION: Confidence Drop & Gradual Ramp ---
            if correctness < 50 or confidence < 0.5:
                self.state.difficulty_level = "easy"
                self.state.consecutive_failures += 1
                instruction = "The candidate's confidence or performance has dropped. Provide warm encouragement, reassure them it's okay to get stuck, and ask a noticeably easier foundational question to build their confidence back up."
            elif correctness >= 80 and confidence >= 0.6:
                self.state.consecutive_failures = 0
                if self.state.difficulty_level == "easy":
                    self.state.difficulty_level = "medium"
                    instruction = "The candidate answered the easy question well and their confidence is recovering. Acknowledge their good answer and gradually step up the difficulty to a medium-level question."
                elif self.state.difficulty_level == "medium":
                    self.state.difficulty_level = "hard"
                    instruction = "The candidate is performing exceptionally well. Push their technical boundaries with a hard-level scenario."
            else:
                self.state.consecutive_failures = 0
                instruction = f"Maintain the current {self.state.difficulty_level} difficulty."

            # --- Emotion Integration ---
            emotion = multimodal_metrics.get('facial_expression', 'Neutral').lower()
            if emotion in ['fear', 'sad', 'angry', 'disgust']:
                instruction += f" Note: The candidate's facial expression indicates {emotion} and high stress. Take a brief moment to validate their feelings and de-escalate the stress before asking the next question."

        # 2. Strict 4-Stage Interview Plan
        history_len = len(self.state.history)
        
        if history_len == 0:
            focus = f"validating their core skills: {', '.join(self.state.focus_areas.get('core_skills', []))}"
        elif history_len == 1:
            focus = f"probing their weak areas: {', '.join(self.state.focus_areas.get('weak_areas', []))}"
        elif history_len == 2:
            focus = f"a deep-dive into one of their projects: {self.state.candidate_profile.get('key_projects', [])}"
        else:
            focus = f"a scenario testing their domain exposure ({self.state.candidate_profile.get('domain_exposure', 'General')}) appropriate for their seniority level ({self.state.candidate_profile.get('seniority_signal', 'Mid')})"

        # --- FEATURE: Role-Specific Routing ---
        role_lower = self.state.target_role.lower()
        if "backend" in role_lower:
            role_guideline = "DOMAIN FOCUS: Emphasize system design, microservices, API latency, database scaling (SQL vs NoSQL), and concurrency."
        elif "ml" in role_lower or "machine learning" in role_lower:
            role_guideline = "DOMAIN FOCUS: Emphasize model deployment (MLOps), handling overfitting, data pipelines, and evaluating model metrics in production."
        elif "embedded" in role_lower:
            role_guideline = "DOMAIN FOCUS: Emphasize memory management, hardware constraints, C/C++ pointers, RTOS, and low-level system interactions."
        elif "frontend" in role_lower:
            role_guideline = "DOMAIN FOCUS: Emphasize state management, DOM manipulation performance, browser APIs, and component lifecycles."
        elif "data" in role_lower:
            role_guideline = "DOMAIN FOCUS: Emphasize ETL/ELT pipelines, complex SQL window functions, and distributed computing (Spark/Hadoop)."
        elif "full stack" in role_lower:
            role_guideline = "DOMAIN FOCUS: Emphasize end-to-end architecture, API integration, balancing frontend performance with backend scalability, and database design."
        elif "quantum" in role_lower:
            role_guideline = "DOMAIN FOCUS: Emphasize quantum mechanics principles, qubits, quantum circuits/gates, error correction, and quantum algorithms (like Shor's or Grover's)."
        else:
            role_guideline = "DOMAIN FOCUS: Frame questions specifically around the daily technical challenges and architecture of this specific role."

        # 3. Generate the specific prompt
        prompt = f"""
        You are a supportive technical interviewer for a {self.state.target_role} role.
        
        Candidate Context:
        - Seniority: {self.state.candidate_profile.get('seniority_signal', 'Unknown')}
        - Domain Exposure: {self.state.candidate_profile.get('domain_exposure', 'Unknown')}
        
        Current Difficulty: {self.state.difficulty_level}
        Agent Instruction: {instruction}
        {role_guideline}
        
        Your ONLY Goal for this turn: Formulate ONE interview question focused entirely on {focus}.
        
        Generate the question. Do not use stage directions. Speak directly to the candidate. Make it conversational.
        """
        
        if stream:
            response = self.client.models.generate_content_stream(model=config.DEFAULT_TEXT_MODEL, contents=prompt)
            def stream_generator():
                full_text = ""
                for chunk in response:
                    if chunk.text:
                        full_text += chunk.text
                        yield chunk.text
                self.state.history.append({"agent": full_text})
            return stream_generator()
        else:
            response = self.client.models.generate_content(model=config.DEFAULT_TEXT_MODEL, contents=prompt)
            question = response.text.strip()
            self.state.history.append({"agent": question})
            return question
    
    def generate_coding_problem(self):
        prompt = f"""
        Generate ONE medium-difficulty coding interview problem tailored specifically for a {self.state.target_role}.
        Do not provide the solution. Only provide the problem statement, input/output format, and constraints.
        Make it realistic to a day-to-day challenge in this role (e.g., Data parsing for ML, state management for Frontend, algorithm optimization for Backend).
        """
        response = self.client.models.generate_content(model=config.DEFAULT_TEXT_MODEL, contents=prompt)
        return response.text.strip()
    
    def generate_hint(self, current_question):
        prompt = f"""
        You are a supportive technical interviewer and coach for a {self.state.target_role}.
        You just asked the candidate this question: "{current_question}"
        
        The candidate is stuck and has asked for a hint. 
        Provide a short, encouraging hint that points them in the right direction, gives them a structural framework, or reminds them of a core concept. 
        CRITICAL: DO NOT give away the actual answer. Limit the hint to 2-3 sentences.
        """
        response = self.client.models.generate_content(model=config.DEFAULT_TEXT_MODEL, contents=prompt)
        return response.text.strip()