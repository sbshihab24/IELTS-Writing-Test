import streamlit as st
import time
import backend  # Importing our custom backend file
import streamlit.components.v1 as components
import os
from dotenv import load_dotenv

# --- LOAD ENVIRONMENT VARIABLES ---
load_dotenv()

# --- CONFIGURATION ---
st.set_page_config(page_title="IELTS Writing Exam", layout="wide", page_icon="📝")

# --- CUSTOM CSS (To match Figma Styles) ---
st.markdown("""
<style>
    .stApp { background-color: #F8F9FA; }
    
    /* Blue Header Card for Score */
    .score-card {
        background: linear-gradient(90deg, #2563EB 0%, #1D4ED8 100%);
        padding: 30px;
        border-radius: 15px;
        color: white;
        display: flex;
        justify_content: space-between;
        align-items: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 25px;
    }
    .score-circle {
        background-color: white;
        color: #2563EB;
        width: 80px;
        height: 80px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify_content: center;
        font-size: 32px;
        font-weight: bold;
    }
    
    /* Criteria Bars */
    .criteria-box {
        background: white;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
        border: 1px solid #E5E7EB;
        display: flex;
        justify_content: space-between;
        align-items: center;
    }
    
    /* Strengths & Weaknesses */
    .feedback-section {
        background: white;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #E5E7EB;
        height: 100%;
    }
    .strength-item { color: #059669; margin-bottom: 8px; font-size: 14px;}
    .weakness-item { color: #D97706; margin-bottom: 8px; font-size: 14px;}
    
    /* Task 2 Question Box */
    .task2-box {
        background-color: #EEF2FF; 
        border-left: 5px solid #2563EB; 
        padding: 20px; 
        border-radius: 5px; 
        margin-bottom: 20px;
    }
    .task2-text {
        color: #1F2937;
        font-size: 18px;
        font-weight: 700;
        margin: 0;
    }

    /* Timer Style */
    .timer-box {
        font-family: monospace;
        font-size: 24px;
        font-weight: bold;
        color: #ff4b4b;
        padding: 10px;
        background: #ffebeb;
        border-radius: 5px;
        text-align: center;
        margin-bottom: 10px;
    }

    /* Feedback Analysis Card */
    .analysis-card {
        background-color: white;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #E5E7EB;
        margin-bottom: 15px;
    }
    .quote-text {
        font-style: italic;
        color: #4B5563;
        border-left: 3px solid #D97706;
        padding-left: 10px;
        margin-bottom: 8px;
        background-color: #FFFBEB;
        padding: 8px;
        border-radius: 0 4px 4px 0;
    }
    
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if 'exam_state' not in st.session_state:
    st.session_state.exam_state = 'ready' # ready, running, submitted

if 'current_question' not in st.session_state:
    st.session_state.current_question = None
if 'feedback' not in st.session_state:
    st.session_state.feedback = None

# Track individual task states: 'idle', 'running', 'completed'
if 't1_state' not in st.session_state:
    st.session_state.t1_state = 'idle'
if 't1_start_time' not in st.session_state:
    st.session_state.t1_start_time = 0

if 't2_state' not in st.session_state:
    st.session_state.t2_state = 'idle'
if 't2_start_time' not in st.session_state:
    st.session_state.t2_start_time = 0

if 'task1_ans' not in st.session_state:
    st.session_state.task1_ans = ""
if 'task2_ans' not in st.session_state:
    st.session_state.task2_ans = ""

# --- JAVASCRIPT TIMER COMPONENT ---
def render_task_timer(total_seconds, time_left_seconds, timer_id):
    """
    Renders a countdown timer. 
    Crucially, it takes 'time_left_seconds' to ensure the timer 
    doesn't reset to full duration when Streamlit re-runs on typing.
    """
    if time_left_seconds < 0:
        time_left_seconds = 0

    timer_html = f"""
    <div style="
        font-family: monospace;
        font-size: 20px;
        font-weight: bold;
        color: #d93025;
        background-color: #fce8e6;
        padding: 8px 15px;
        border-radius: 5px;
        display: inline-block;
        border: 1px solid #d93025;
    ">
        ⏱️ <span id="{timer_id}">--:--</span>
    </div>
    <script>
    var timeLeft = {int(time_left_seconds)};
    var timerId = "{timer_id}";
    
    function updateTimer() {{
        var minutes = Math.floor(timeLeft / 60);
        var seconds = timeLeft % 60;
        
        minutes = minutes < 10 ? "0" + minutes : minutes;
        seconds = seconds < 10 ? "0" + seconds : seconds;
        
        var element = document.getElementById(timerId);
        if(element) {{
            element.innerHTML = minutes + ":" + seconds;
        }}
        
        if (timeLeft <= 0) {{
            clearInterval(interval);
            if(element) element.innerHTML = "00:00";
        }}
        timeLeft--;
    }}
    
    // Run once immediately, then every second
    updateTimer();
    var interval = setInterval(updateTimer, 1000);
    </script>
    """
    components.html(timer_html, height=50)

# --- APP LOGIC ---

# 1. START SCREEN
if st.session_state.exam_state == 'ready':
    st.title("IELTS Writing Mock Test")
    st.info("⏱️ This exam consists of two parts. You will start each part individually.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("### Task 1")
        st.write("Academic Report (20 Minutes)")
    with col2:
        st.write("### Task 2")
        st.write("Essay (40 Minutes)")

    st.markdown("---")

    if st.button("Load Exam Questions", type="primary"):
        st.session_state.current_question = backend.get_random_test_questions()
        if st.session_state.current_question:
            st.session_state.exam_state = 'running'
            # Reset task states
            st.session_state.t1_state = 'idle'
            st.session_state.t2_state = 'idle'
            st.session_state.task1_ans = ""
            st.session_state.task2_ans = ""
            st.rerun()
        else:
            st.error("Error loading questions. Check backend.")

# 2. EXAM INTERFACE (RUNNING)
elif st.session_state.exam_state == 'running':
    q_data = st.session_state.current_question
    
    st.title("Writing Exam In Progress")
    
    # ==========================
    # TASK 1 SECTION
    # ==========================
    st.markdown("## Task 1: Academic Report")
    
    # Container for Task 1
    t1_container = st.container(border=True)
    
    with t1_container:
        # STATE: IDLE
        if st.session_state.t1_state == 'idle':
            st.info("You have 20 minutes to complete this task.")
            if st.button("Start Task 1 (20:00)", key="btn_start_t1", type="primary"):
                st.session_state.t1_state = 'running'
                st.session_state.t1_start_time = time.time()
                st.rerun()
        
        # STATE: RUNNING or COMPLETED
        else:
            # Calculate Time
            T1_DURATION = 20 * 60 # 20 minutes
            elapsed = time.time() - st.session_state.t1_start_time
            remaining = T1_DURATION - elapsed
            
            # Header with Timer (if running)
            c1, c2 = st.columns([3, 1])
            with c1:
                if st.session_state.t1_state == 'running':
                    st.caption("Writing Task 1")
            with c2:
                if st.session_state.t1_state == 'running':
                    render_task_timer(T1_DURATION, remaining, "t1_timer")
                    
            # Check for Time Expiry
            if st.session_state.t1_state == 'running' and remaining <= 0:
                st.session_state.t1_state = 'completed'
                st.rerun()

            # Content Layout (Prompt ABOVE Image)
            col_content, col_input = st.columns([1, 1])
            
            with col_content:
                # 1. PROMPT (Moved Upper)
                st.markdown(f"""
                <div style="margin-bottom: 15px; padding: 15px; background-color: #fff; border-radius: 8px; border: 1px solid #e5e7eb;">
                    <p style="font-size: 16px; line-height: 1.5; color: #374151; font-weight: 500;">
                        {q_data['task1_prompt']}
                    </p>
                </div>
                """, unsafe_allow_html=True)

                # 2. IMAGE
                st.image(q_data['task1_image'], caption="Task 1 Visual", use_container_width=True)

            with col_input:
                is_disabled = (st.session_state.t1_state == 'completed')
                st.session_state.task1_ans = st.text_area(
                    "Your Answer:", 
                    value=st.session_state.task1_ans,
                    height=450, 
                    key="t1_input",
                    disabled=is_disabled,
                    placeholder="Start typing your report here..."
                )
                
                if st.session_state.t1_state == 'running':
                    if st.button("Finish Task 1", key="finish_t1"):
                        st.session_state.t1_state = 'completed'
                        st.rerun()
                elif st.session_state.t1_state == 'completed':
                    st.success("Task 1 Completed")

    st.markdown("---")

    # ==========================
    # TASK 2 SECTION
    # ==========================
    st.markdown("## Task 2: Essay")
    
    t2_container = st.container(border=True)
    with t2_container:
        # STATE: IDLE
        if st.session_state.t2_state == 'idle':
            st.info("You have 40 minutes to complete this task.")
            if st.button("Start Task 2 (40:00)", key="btn_start_t2", type="primary"):
                st.session_state.t2_state = 'running'
                st.session_state.t2_start_time = time.time()
                st.rerun()
        
        # STATE: RUNNING or COMPLETED
        else:
            # Calculate Time
            T2_DURATION = 40 * 60 # 40 minutes
            elapsed = time.time() - st.session_state.t2_start_time
            remaining = T2_DURATION - elapsed
            
            # Header
            c1, c2 = st.columns([3, 1])
            with c1:
                pass
            with c2:
                if st.session_state.t2_state == 'running':
                    render_task_timer(T2_DURATION, remaining, "t2_timer")

            # Check for Time Expiry
            if st.session_state.t2_state == 'running' and remaining <= 0:
                st.session_state.t2_state = 'completed'
                st.rerun()

            # Question Layout
            st.markdown(f"""
            <div class="task2-box">
                <p class="task2-text">{q_data['task2_question']}</p>
                <p style="margin-top: 10px; font-size: 14px; color: #4B5563;">
                    Give reasons for your answer and include any relevant examples from your own knowledge or experience.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            is_disabled_t2 = (st.session_state.t2_state == 'completed')
            st.session_state.task2_ans = st.text_area(
                "Your Essay:", 
                value=st.session_state.task2_ans,
                height=450, 
                key="t2_input",
                disabled=is_disabled_t2,
                placeholder="Start typing your essay here..."
            )
            
            if st.session_state.t2_state == 'running':
                if st.button("Finish Task 2", key="finish_t2"):
                    st.session_state.t2_state = 'completed'
                    st.rerun()
            elif st.session_state.t2_state == 'completed':
                st.success("Task 2 Completed")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # ==========================
    # FINAL SUBMISSION
    # ==========================
    # Only allow submission if at least one task is attempted/completed
    can_submit = (st.session_state.t1_state == 'completed' or st.session_state.t2_state == 'completed')
    
    if st.button("✅ Submit Exam & Get Feedback", type="primary", disabled=not can_submit, use_container_width=True):
        if len(st.session_state.task1_ans) < 50 and len(st.session_state.task2_ans) < 50:
            st.warning("Your answers seem very short. Please ensure you have attempted the tasks.")
        else:
            with st.spinner("Analyzing your writing..."):
                feedback = backend.generate_ielts_feedback(st.session_state.task1_ans, st.session_state.task2_ans, q_data)
                st.session_state.feedback = feedback
                st.session_state.exam_state = 'submitted'
                st.rerun()

# 3. FEEDBACK INTERFACE (MATCHING FIGMA)
elif st.session_state.exam_state == 'submitted':
    fb = st.session_state.feedback
    
    if not fb:
        st.error("Failed to generate feedback. Please try again.")
    else:
        # --- HEADER (Blue Card) ---
        st.markdown(f"""
        <div class="score-card">
            <div>
                <h2 style="margin:0; font-size: 24px;">Overall IELTS Band Score</h2>
                <p style="margin:0; opacity: 0.9;">Based on your writing performance</p>
            </div>
            <div class="score-circle">{fb['overall_score']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.subheader("Estimated Band Score Breakdown")
        
        # --- CRITERIA SCORES ---
        scores = fb.get('scores', {'task_achievement':0, 'coherence_cohesion':0, 'lexical_resource':0, 'grammar_accuracy':0})
        criteria_list = [
            ("Task Achievement", scores.get('task_achievement', 0)),
            ("Coherence & Cohesion", scores.get('coherence_cohesion', 0)),
            ("Lexical Resource", scores.get('lexical_resource', 0)),
            ("Grammar & Accuracy", scores.get('grammar_accuracy', 0))
        ]
        
        for name, score in criteria_list:
            st.markdown(f"""
            <div class="criteria-box">
                <span style="font-weight:500;">{name}</span>
                <span style="background:#EEF2FF; color:#2563EB; padding: 2px 8px; border-radius:4px; font-weight:bold;">{score}</span>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)

        # --- STRENGTHS & WEAKNESSES ---
        col_str, col_weak = st.columns(2)
        
        with col_str:
            st.markdown("### 🟢 Strengths")
            st.markdown('<div class="feedback-section">', unsafe_allow_html=True)
            for item in fb.get('strengths', []):
                st.markdown(f'<div class="strength-item">✓ {item}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col_weak:
            st.markdown("### 🟠 Areas for Improvement")
            st.markdown('<div class="feedback-section">', unsafe_allow_html=True)
            for item in fb.get('weaknesses', []):
                st.markdown(f'<div class="weakness-item">! {item}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        # --- DETAILED ANALYSIS (NEW FEATURE) ---
        st.subheader("👁️ Detailed Line-by-Line Analysis")
        
        # Detailed Feedback for Task 1
        with st.expander("Expand Task 1 Analysis", expanded=False):
            if 'detailed_analysis' in fb and 'task1_feedback' in fb['detailed_analysis']:
                for item in fb['detailed_analysis']['task1_feedback']:
                    st.markdown(f"""
                    <div class="analysis-card">
                        <div class="quote-text">"{item['original']}"</div>
                        <p style="color: #B91C1C; margin: 5px 0;"><strong>❌ Issue:</strong> {item['comment']}</p>
                        <p style="color: #047857; margin: 5px 0;"><strong>✅ Improvement:</strong> {item['correction']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No detailed analysis available for Task 1.")

        # Detailed Feedback for Task 2
        with st.expander("Expand Task 2 Analysis", expanded=False):
            if 'detailed_analysis' in fb and 'task2_feedback' in fb['detailed_analysis']:
                for item in fb['detailed_analysis']['task2_feedback']:
                    st.markdown(f"""
                    <div class="analysis-card">
                        <div class="quote-text">"{item['original']}"</div>
                        <p style="color: #B91C1C; margin: 5px 0;"><strong>❌ Issue:</strong> {item['comment']}</p>
                        <p style="color: #047857; margin: 5px 0;"><strong>✅ Improvement:</strong> {item['correction']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No detailed analysis available for Task 2.")
        
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("Take Another Test", use_container_width=True):
            st.session_state.exam_state = 'ready'
            st.session_state.current_question = None
            st.session_state.feedback = None
            st.session_state.t1_state = 'idle'
            st.session_state.t2_state = 'idle'
            st.session_state.task1_ans = ""
            st.session_state.task2_ans = ""
            st.rerun()