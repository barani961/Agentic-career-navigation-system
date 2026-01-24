"""
Standalone Streamlit App for Career Agent System
All features work without backend API
"""

import streamlit as st
import json
from datetime import datetime
import sys
import os
from dotenv import load_dotenv
import threading
from concurrent.futures import ThreadPoolExecutor

# Load environment variables from .env file
load_dotenv()

# Add to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm.llm_client import LLMClient
from orchestrator import load_data_files, CareerAgentOrchestrator

# ========== PAGE CONFIG ==========
st.set_page_config(
    page_title="Career Navigation Agent",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== CUSTOM CSS ==========
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .step-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #1f77b4;
    }
    .completed-step {
        border-left-color: #2ecc71;
        background-color: #e8f8f5;
    }
    .blocked-step {
        border-left-color: #e74c3c;
        background-color: #fadbd8;
    }
    .in-progress-step {
        border-left-color: #f39c12;
        background-color: #fef5e7;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .alternative-card {
        border: 2px solid #dee2e6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        transition: all 0.3s;
    }
    .alternative-card:hover {
        border-color: #1f77b4;
        box-shadow: 0 4px 12px rgba(31,119,180,0.2);
    }
    .skill-badge {
        display: inline-block;
        background-color: #1f77b4;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 1rem;
        margin: 0.2rem;
        font-size: 0.9rem;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffc107;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        color: #000 !important;
    }
    .warning-box h4 {
        color: #000 !important;
    }
    .warning-box h3 {
        color: #000 !important;
    }
    .warning-box p {
        color: #000 !important;
    }
    .warning-box ul {
        color: #000 !important;
    }
    .warning-box li {
        color: #000 !important;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #28a745;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        color: #000 !important;
    }
    .success-box h3 {
        color: #000 !important;
    }
    .success-box p {
        color: #000 !important;
    }
</style>
""", unsafe_allow_html=True)

# ========== SESSION STATE INITIALIZATION ==========

def init_session_state():
    """Initialize all session state variables"""
    if 'page' not in st.session_state:
        st.session_state.page = "home"
    
    if 'journey' not in st.session_state:
        st.session_state.journey = None
    
    if 'roadmap' not in st.session_state:
        st.session_state.roadmap = []
    
    if 'step_status' not in st.session_state:
        st.session_state.step_status = {}  # {step_num: {status, time_spent, blockers}}
    
    if 'learned_skills' not in st.session_state:
        st.session_state.learned_skills = []
    
    if 'completed_steps' not in st.session_state:
        st.session_state.completed_steps = []
    
    if 'blockers' not in st.session_state:
        st.session_state.blockers = {}  # {step_num: [blocker1, blocker2...]}
    
    if 'reevaluation_data' not in st.session_state:
        st.session_state.reevaluation_data = None
    
    if 'original_goal' not in st.session_state:
        st.session_state.original_goal = None
    
    if 'reroute_history' not in st.session_state:
        st.session_state.reroute_history = []
    
    if 'current_target' not in st.session_state:
        st.session_state.current_target = None
    
    if 'assessment_result' not in st.session_state:
        st.session_state.assessment_result = None
    
    if 'pending_reevaluation' not in st.session_state:
        st.session_state.pending_reevaluation = None
    
    if 'completion_alternatives' not in st.session_state:
        st.session_state.completion_alternatives = None

init_session_state()

# ========== INITIALIZE ORCHESTRATOR ==========

@st.cache_resource
def get_orchestrator():
    """Initialize orchestrator (cached)"""
    try:
        llm = LLMClient()
        job_market, career_paths, skills_taxonomy, learning_resources = load_data_files()
        
        return CareerAgentOrchestrator(
            llm_client=llm,
            job_market_data=job_market,
            career_paths_data=career_paths,
            skills_taxonomy=skills_taxonomy,
            learning_resources=learning_resources
        )
    except Exception as e:
        st.error(f"Failed to initialize system: {e}")
        return None

# ========== HELPER FUNCTIONS ==========

def calculate_progress():
    """Calculate overall progress percentage"""
    if not st.session_state.roadmap:
        return 0
    total = len(st.session_state.roadmap)
    completed = len(st.session_state.completed_steps)
    return (completed / total * 100) if total > 0 else 0

def calculate_motivation():
    """Calculate motivation based on blockers"""
    total_blockers = sum(len(b) for b in st.session_state.blockers.values())
    return max(1.0 - (total_blockers * 0.2), 0.1)

def check_reevaluation_needed():
    """Check if re-evaluation should be triggered"""
    # Trigger 1: Multiple blockers (2+)
    if len(st.session_state.blockers) >= 2:
        return True, "multiple_blockers"
    
    # Trigger 2: Same step blocked 3+ times
    for step_num, blocker_list in st.session_state.blockers.items():
        if len(blocker_list) >= 3:
            return True, "repeated_blocker"
    
    # Trigger 3: Every 3 completed steps
    if len(st.session_state.completed_steps) > 0 and len(st.session_state.completed_steps) % 3 == 0:
        # Check if we already re-evaluated at this checkpoint
        if not hasattr(st.session_state, 'last_reevaluation_at'):
            st.session_state.last_reevaluation_at = 0
        
        if len(st.session_state.completed_steps) > st.session_state.last_reevaluation_at:
            return True, "periodic_check"
    
    # Trigger 4: Low motivation
    if calculate_motivation() < 0.5:
        return True, "low_motivation"
    
    return False, None

def get_step_status(step_num):
    """Get status of a step"""
    if step_num in st.session_state.completed_steps:
        return "completed"
    elif step_num in st.session_state.blockers:
        return "blocked"
    elif step_num in st.session_state.step_status:
        return st.session_state.step_status[step_num].get("status", "not_started")
    else:
        return "not_started"

def get_status_emoji(status):
    """Get emoji for status"""
    emojis = {
        "not_started": "⏳",
        "in_progress": "🔄",
        "completed": "✅",
        "blocked": "🚫"
    }
    return emojis.get(status, "⏳")

def check_roadmap_completion():
    """Check if entire roadmap is completed"""
    if not st.session_state.roadmap:
        return False
    total_steps = len(st.session_state.roadmap)
    completed_steps = len(st.session_state.completed_steps)
    return completed_steps == total_steps and total_steps > 0

# ========== PAGES ==========

def home_page():
    """Initial assessment page"""
    st.markdown('<p class="main-header">🎓 AI Career Navigation Agent</p>', unsafe_allow_html=True)
    
    st.markdown("""
    ### Welcome to Your Career Journey!
    
    Our AI-powered system will:
    - ✅ Analyze your current skills and profile
    - 📊 Evaluate market demand for your target role
    - 🎯 Assess feasibility and readiness
    - 🗺️ Generate a personalized learning roadmap
    - 🔄 Dynamically reroute if you face challenges
    """)
    
    st.markdown("---")
    st.markdown("### 📝 Tell Us About Yourself")
    
    col1, col2 = st.columns(2)
    
    with col1:
        desired_role = st.text_input(
            "🎯 What career role do you want?",
            value="Data Analyst",
            help="Examples: Data Analyst, Software Engineer, ML Engineer"
        )
        
        skills_text = st.text_area(
            "💻 What skills do you have?",
            value="Python basics, SQL",
            help="List your technical skills, separated by commas",
            height=100
        )
        
        education = st.text_input(
            "🎓 Education Background",
            value="3rd year B.Tech Computer Science",
            help="Your current or highest education"
        )
    
    with col2:
        experience = st.text_area(
            "💼 Work Experience (Optional)",
            value="",
            help="Any internships, jobs, or work experience",
            height=60
        )
        
        projects = st.text_area(
            "🚀 Projects (One per line)",
            value="Data visualization dashboard",
            help="List your projects, one per line",
            height=100
        )
        
        duration_weeks = st.slider(
            "⏱️ How many weeks can you dedicate?",
            min_value=4,
            max_value=24,
            value=12,
            help="Total time you can invest in learning"
        )
    
    st.markdown("---")
    
    if st.button("🚀 Analyze My Career Path", type="primary", use_container_width=True):
        orchestrator = get_orchestrator()
        
        if not orchestrator:
            st.error("System not initialized. Please check Groq API key.")
            return
        
        with st.spinner("🤖 AI Agents are analyzing your profile..."):
            try:
                # Process query
                project_list = [p.strip() for p in projects.split("\n") if p.strip()]
                
                result = orchestrator.process_student_query(
                    desired_role=desired_role,
                    skills_text=skills_text,
                    education=education,
                    experience=experience if experience else None,
                    projects=project_list if project_list else None,
                    duration_weeks=duration_weeks
                )
                
                # Save to session state
                st.session_state.assessment_result = result
                st.session_state.original_goal = desired_role
                st.session_state.current_target = result.get("target_role", desired_role)
                
                # Extract roadmap
                if result.get("verdict") == "FEASIBLE":
                    st.session_state.roadmap = result["roadmap"]["roadmap"]
                elif result.get("verdict") == "NOT_FEASIBLE":
                    # Use first alternative's roadmap
                    alts = result.get("recommended_alternatives", [])
                    if alts:
                        st.session_state.roadmap = alts[0].get("roadmap", {}).get("roadmap", [])
                        st.session_state.current_target = alts[0]["role"]
                else:  # CHALLENGING
                    st.session_state.roadmap = result.get("direct_path", {}).get("roadmap", {}).get("roadmap", [])
                
                # Initialize step status
                for i in range(len(st.session_state.roadmap)):
                    st.session_state.step_status[i+1] = {"status": "not_started", "time_spent": 0}
                
                st.session_state.page = "dashboard"
                st.success("✅ Assessment Complete!")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error during assessment: {e}")
                import traceback
                st.code(traceback.format_exc())

def dashboard_page():
    """Main dashboard with roadmap and progress"""
    result = st.session_state.assessment_result
    
    if not result:
        st.error("No assessment data. Please start a new assessment.")
        if st.button("← Start New Assessment"):
            st.session_state.page = "home"
            st.rerun()
        return
    
    # Check for pending reevaluation
    if st.session_state.get('pending_reevaluation'):
        trigger_reevaluation_with_analysis(st.session_state.pending_reevaluation)
        st.session_state.pending_reevaluation = None
        return
    
    st.markdown('<p class="main-header">📊 Your Learning Journey</p>', unsafe_allow_html=True)
    
    # Show reroute history if exists
    if st.session_state.reroute_history:
        with st.expander("📜 Journey History", expanded=False):
            for reroute in st.session_state.reroute_history:
                st.info(f"🔄 {reroute['from_role']} → {reroute['to_role']} ({reroute['reason']})")
    
    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    
    progress_pct = calculate_progress()
    motivation = calculate_motivation()
    total_steps = len(st.session_state.roadmap)
    completed_count = len(st.session_state.completed_steps)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h2>{progress_pct:.0f}%</h2>
            <p>Progress</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h2>{completed_count}/{total_steps}</h2>
            <p>Steps Done</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        motivation_color = "#2ecc71" if motivation >= 0.7 else "#f39c12" if motivation >= 0.5 else "#e74c3c"
        st.markdown(f"""
        <div class="metric-card" style="background: {motivation_color}">
            <h2>{motivation*100:.0f}%</h2>
            <p>Motivation</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h2>{len(st.session_state.learned_skills)}</h2>
            <p>Skills Learned</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Show current target vs original goal
    if st.session_state.current_target != st.session_state.original_goal:
        st.markdown(f"""
        <div class="warning-box">
            <strong>🎯 Current Target:</strong> {st.session_state.current_target}<br>
            <strong>🌟 Original Goal:</strong> {st.session_state.original_goal}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"### 🎯 Target Role: **{st.session_state.current_target}**")
    
    # Active blockers warning
    if st.session_state.blockers:
        blocker_count = sum(len(b) for b in st.session_state.blockers.values())
        st.markdown(f"""
        <div class="warning-box">
            <h4>⚠️ Active Blockers: {blocker_count}</h4>
            <p>You have blockers on {len(st.session_state.blockers)} step(s)</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Show market insights if cached
    if 'market_analysis_cache' in st.session_state and st.session_state.current_target in st.session_state.market_analysis_cache:
        cached = st.session_state.market_analysis_cache[st.session_state.current_target]
        market_data = cached.get('analysis', {})
        
        with st.expander("📊 Current Market Insight"):
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                st.metric("Active Jobs", market_data.get('active_jobs', 'N/A'))
            with col_m2:
                st.metric("Your Match", f"{market_data.get('skill_match', 0)*100:.0f}%")
            with col_m3:
                st.metric("Entry Barrier", f"{market_data.get('entry_barrier', 0)*100:.0f}%")
            
            if market_data.get('salary_range'):
                st.markdown(f"**💰 Salary Range:** {market_data['salary_range']}")
            if market_data.get('growth_rate'):
                st.markdown(f"**📈 Growth Rate:** {market_data['growth_rate']}")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["🗺️ Roadmap", "🎓 Skills Learned", "📈 Progress Summary"])
    
    with tab1:
        roadmap_view()
    
    with tab2:
        skills_view()
    
    with tab3:
        summary_view()

def roadmap_view():
    """Display roadmap with step cards"""
    st.markdown("### 📚 Your Learning Roadmap")
    
    for i, step in enumerate(st.session_state.roadmap):
        step_num = i + 1
        status = get_step_status(step_num)
        emoji = get_status_emoji(status)
        
        # Card styling
        card_class = "step-card"
        if status == "completed":
            card_class += " completed-step"
        elif status == "blocked":
            card_class += " blocked-step"
        elif status == "in_progress":
            card_class += " in-progress-step"
        
        with st.container():
            st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"### {emoji} Step {step_num}: {step.get('title', 'Unnamed Step')}")
                st.markdown(f"**Description:** {step.get('description', 'No description')}")
                st.markdown(f"**Duration:** {step.get('duration_weeks', 0)} weeks")
                
                if step.get('why_important'):
                    st.markdown(f"**💡 Why Important:** {step['why_important']}")
                
                # Skills covered
                if step.get('skills_covered'):
                    st.markdown("**Skills You'll Learn:**")
                    for skill in step['skills_covered']:
                        st.markdown(f'<span class="skill-badge">{skill}</span>', unsafe_allow_html=True)
                
                # Resources
                if step.get('resources'):
                    with st.expander(f"📚 Learning Resources ({len(step['resources'])})"):
                        for resource in step['resources']:
                            st.markdown(f"- **[{resource.get('title', 'Resource')}]({resource.get('url', '#')})**")
                            st.caption(f"Type: {resource.get('type', 'N/A')} | Duration: {resource.get('duration_hours', 'N/A')} hours")
            
            with col2:
                st.markdown(f"**Status:** {status.replace('_', ' ').title()}")
                
                # Show time spent if available
                if step_num in st.session_state.step_status:
                    time_spent = st.session_state.step_status[step_num].get("time_spent", 0)
                    if time_spent > 0:
                        st.markdown(f"**Time:** {time_spent:.1f}h")
                
                # Action buttons based on status
                if status == "not_started":
                    if st.button("▶️ Start", key=f"start_{step_num}", use_container_width=True):
                        st.session_state.step_status[step_num]["status"] = "in_progress"
                        st.rerun()
                
                elif status == "in_progress":
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("✅", key=f"complete_{step_num}", help="Mark Complete"):
                            st.session_state[f'show_complete_dialog_{step_num}'] = True
                            st.rerun()
                    with col_b:
                        if st.button("🚫", key=f"block_{step_num}", help="Report Issue"):
                            st.session_state[f'show_blocker_form_{step_num}'] = True
                            st.rerun()
                    
                    # Completion dialog
                    if st.session_state.get(f'show_complete_dialog_{step_num}', False):
                        st.markdown("---")
                        mark_complete(step_num, step)
                        st.markdown("---")
                    
                    # Blocker form
                    if st.session_state.get(f'show_blocker_form_{step_num}', False):
                        st.markdown("---")
                        with st.form(f"blocker_form_{step_num}"):
                            st.markdown("**Report Issue:**")
                            reason = st.text_area("What's blocking you?", key=f"reason_{step_num}")
                            hours = st.number_input("Hours spent struggling:", min_value=0.0, value=5.0, step=0.5, key=f"hours_{step_num}")
                            
                            col_x, col_y = st.columns(2)
                            with col_x:
                                if st.form_submit_button("Submit", type="primary"):
                                    report_blocker(step_num, reason, hours, step)
                            with col_y:
                                if st.form_submit_button("Cancel"):
                                    st.session_state[f'show_blocker_form_{step_num}'] = False
                                    st.rerun()
                        st.markdown("---")
                
                elif status == "completed":
                    st.success("✅ Completed")
                
                elif status == "blocked":
                    st.error("🚫 Blocked")
                    blocker_count = len(st.session_state.blockers.get(step_num, []))
                    st.caption(f"Attempts: {blocker_count}")
            
            st.markdown('</div>', unsafe_allow_html=True)

def mark_complete(step_num, step):
    """Mark a step as complete with simultaneous market analysis"""
    # Check if showing time input dialog
    if f'show_complete_dialog_{step_num}' not in st.session_state:
        st.session_state[f'show_complete_dialog_{step_num}'] = False
    
    if not st.session_state[f'show_complete_dialog_{step_num}']:
        # Show button to open dialog
        if st.button(f"Open Completion Form", key=f"open_complete_{step_num}"):
            st.session_state[f'show_complete_dialog_{step_num}'] = True
            st.rerun()
    else:
        # Show the completion dialog
        st.markdown(f"### ✅ Completing Step {step_num}")
        st.markdown(f"**{step.get('title')}**")
        
        hours = st.slider(
            "How many hours did you spend on this step?",
            min_value=0.0,
            max_value=100.0,
            value=20.0,
            step=0.5,
            help="Be honest - this helps improve recommendations"
        )
        
        col_submit, col_cancel = st.columns(2)
        
        with col_submit:
            if st.button("✅ Confirm Completion", type="primary", use_container_width=True, key=f"confirm_complete_{step_num}"):
                # Immediately update state BEFORE any async operations
                if step_num not in st.session_state.completed_steps:
                    st.session_state.completed_steps.append(step_num)
                
                st.session_state.step_status[step_num] = {
                    "status": "completed",
                    "time_spent": hours
                }
                
                # Add skills
                skills = step.get('skills_covered', [])
                for skill in skills:
                    if skill not in st.session_state.learned_skills:
                        st.session_state.learned_skills.append(skill)
                
                # Remove from blockers if present
                if step_num in st.session_state.blockers:
                    del st.session_state.blockers[step_num]
                
                # Close dialog
                st.session_state[f'show_complete_dialog_{step_num}'] = False
                
                # Show immediate feedback
                st.success(f"🎉 Great job! You completed Step {step_num}!")
                if skills:
                    st.info(f"✨ You've learned: {', '.join(skills)}")
                
                # Start background market analysis
                analyze_market_progress_async()
                
                # Start concurrent market analysis if not already triggered for re-eval
                needs_reeval, trigger_type = check_reevaluation_needed()
                
                if needs_reeval:
                    st.session_state.last_reevaluation_at = len(st.session_state.completed_steps)
                    st.session_state.pending_reevaluation = trigger_type
                
                st.balloons()
                st.rerun()
        
        with col_cancel:
            if st.button("Cancel", use_container_width=True, key=f"cancel_complete_{step_num}"):
                st.session_state[f'show_complete_dialog_{step_num}'] = False
                st.rerun()

def report_blocker(step_num, reason, hours, step):
    """Report a blocker on a step"""
    if not reason:
        st.error("Please describe what's blocking you")
        return
    
    # Add blocker
    if step_num not in st.session_state.blockers:
        st.session_state.blockers[step_num] = []
    
    st.session_state.blockers[step_num].append({
        "reason": reason,
        "hours": hours,
        "timestamp": datetime.now().isoformat()
    })
    
    # Update status
    st.session_state.step_status[step_num] = {
        "status": "blocked",
        "time_spent": st.session_state.step_status[step_num].get("time_spent", 0) + hours
    }
    
    # Clear form flag
    st.session_state[f'show_blocker_form_{step_num}'] = False
    
    blocker_count = len(st.session_state.blockers[step_num])
    
    # Check what to do based on attempt count
    if blocker_count == 1:
        st.warning(f"⚠️ Blocker recorded. Don't worry - here are some tips!")
        st.info("💡 Try reviewing the resources again, or break down the skill into smaller parts.")
    
    elif blocker_count == 2:
        st.warning(f"⚠️ Second blocker on this step. You might need a different approach.")
        st.info("💡 Consider: 1) Finding alternative tutorials, 2) Asking for help online, 3) Taking a short break and coming back")
    
    elif blocker_count >= 3:
        st.error(f"🚨 You've struggled {blocker_count} times on this step. Time to re-evaluate!")
        trigger_reevaluation("repeated_blocker")
        return
    
    # Check for general re-evaluation
    needs_reeval, trigger_type = check_reevaluation_needed()
    
    if needs_reeval and blocker_count < 3:
        trigger_reevaluation(trigger_type)
    else:
        st.rerun()

def analyze_market_progress_async():
    """Background market analysis as student progresses"""
    try:
        if 'market_analysis_cache' not in st.session_state:
            st.session_state.market_analysis_cache = {}
        
        def background_analysis():
            try:
                orchestrator = get_orchestrator()
                if not orchestrator:
                    return
                
                # Store current target before thread execution
                current_target = st.session_state.get('current_target')
                if not current_target:
                    return
                
                # Get all skills as flat list
                all_skills = []
                assessment = st.session_state.get('assessment_result', {})
                current_skills = assessment.get("profile", {}).get("technical_skills", {})
                for category, skills in current_skills.items():
                    all_skills.extend(skills)
                all_skills.extend(st.session_state.get('learned_skills', []))
                
                # Analyze current role
                analysis = orchestrator.market_intelligence.analyze_role_market(
                    role_name=current_target,
                    student_skills=all_skills
                )
                
                st.session_state.market_analysis_cache[current_target] = {
                    "timestamp": datetime.now().isoformat(),
                    "analysis": analysis["market_analysis"]
                }
            except Exception:
                # Silent fail - don't interrupt user experience
                pass
        
        # Run in background thread
        thread = threading.Thread(target=background_analysis, daemon=True)
        thread.start()
    except Exception as e:
        # Silent fail - don't interrupt user experience
        pass

def trigger_reevaluation_with_analysis(trigger_type):
    """Trigger re-evaluation with concurrent market analysis"""
    orchestrator = get_orchestrator()
    
    if not orchestrator:
        st.error("System not available")
        return
    
    with st.spinner("🤖 Re-evaluating your path and analyzing market..."):
        try:
            # Update student profile with learned skills
            current_skills = st.session_state.assessment_result["profile"]["technical_skills"]
            
            # Add learned skills
            if "learned" not in current_skills:
                current_skills["learned"] = []
            current_skills["learned"].extend(st.session_state.learned_skills)
            
            # Get all skills as flat list
            all_skills = []
            for category, skills in current_skills.items():
                all_skills.extend(skills)
            
            # Get fresh market analysis for current role
            current_target = st.session_state.current_target
            market_analysis = orchestrator.market_intelligence.analyze_role_market(
                role_name=current_target,
                student_skills=all_skills
            )["market_analysis"]
            
            # Find alternatives
            alternatives_result = orchestrator.reroute_agent.find_alternatives(
                student_profile=st.session_state.assessment_result["profile"],
                failed_role=current_target,
                failed_market_analysis=market_analysis,
                top_n=3
            )
            
            alternatives = alternatives_result["reroute_recommendations"]["alternatives"]
            
            # Generate roadmaps and market analysis for alternatives in parallel
            def analyze_alternative(alt):
                try:
                    alt_market = orchestrator.market_intelligence.analyze_role_market(
                        role_name=alt["role"],
                        student_skills=all_skills
                    )["market_analysis"]
                    
                    alt_roadmap = orchestrator.roadmap_generator.generate_roadmap(
                        target_role=alt["role"],
                        student_profile=st.session_state.assessment_result["profile"],
                        market_analysis=alt_market,
                        duration_weeks=12
                    )
                    
                    alt["roadmap"] = alt_roadmap
                    alt["market_data"] = alt_market
                except Exception as e:
                    st.warning(f"Could not analyze {alt['role']}: {e}")
            
            # Use thread pool for concurrent analysis
            with ThreadPoolExecutor(max_workers=3) as executor:
                list(executor.map(analyze_alternative, alternatives))
            
            # Save re-evaluation data
            st.session_state.reevaluation_data = {
                "trigger_type": trigger_type,
                "alternatives": alternatives,
                "current_market": market_analysis
            }
            
            # Cache market analysis
            if 'market_analysis_cache' not in st.session_state:
                st.session_state.market_analysis_cache = {}
            st.session_state.market_analysis_cache[current_target] = {
                "timestamp": datetime.now().isoformat(),
                "analysis": market_analysis
            }
            
            # Go to re-evaluation page
            st.session_state.page = "reevaluation"
            st.rerun()
            
        except Exception as e:
            st.error(f"Re-evaluation failed: {e}")
            import traceback
            st.code(traceback.format_exc())

def trigger_reevaluation(trigger_type):
    """Trigger re-evaluation and show alternatives"""
    orchestrator = get_orchestrator()
    
    if not orchestrator:
        st.error("System not available")
        return
    
    with st.spinner("🤖 Re-evaluating your path..."):
        try:
            # Update student profile with learned skills
            current_skills = st.session_state.assessment_result["profile"]["technical_skills"]
            
            # Add learned skills
            if "learned" not in current_skills:
                current_skills["learned"] = []
            current_skills["learned"].extend(st.session_state.learned_skills)
            
            # Get all skills as flat list
            all_skills = []
            for category, skills in current_skills.items():
                all_skills.extend(skills)
            
            # Get fresh market analysis
            current_target = st.session_state.current_target
            market_analysis = orchestrator.market_intelligence.analyze_role_market(
                role_name=current_target,
                student_skills=all_skills
            )["market_analysis"]
            
            # Find alternatives
            alternatives_result = orchestrator.reroute_agent.find_alternatives(
                student_profile=st.session_state.assessment_result["profile"],
                failed_role=current_target,
                failed_market_analysis=market_analysis,
                top_n=3
            )
            
            alternatives = alternatives_result["reroute_recommendations"]["alternatives"]
            
            # Generate roadmaps for alternatives
            for alt in alternatives:
                alt_market = orchestrator.market_intelligence.analyze_role_market(
                    role_name=alt["role"],
                    student_skills=all_skills
                )["market_analysis"]
                
                alt_roadmap = orchestrator.roadmap_generator.generate_roadmap(
                    target_role=alt["role"],
                    student_profile=st.session_state.assessment_result["profile"],
                    market_analysis=alt_market,
                    duration_weeks=12
                )
                
                alt["roadmap"] = alt_roadmap
                alt["market_data"] = alt_market
            
            # Save re-evaluation data
            st.session_state.reevaluation_data = {
                "trigger_type": trigger_type,
                "alternatives": alternatives,
                "current_market": market_analysis
            }
            
            # Go to re-evaluation page
            st.session_state.page = "reevaluation"
            st.rerun()
            
        except Exception as e:
            st.error(f"Re-evaluation failed: {e}")
            import traceback
            st.code(traceback.format_exc())

def skills_view():
    """Display learned skills"""
    if not st.session_state.learned_skills:
        st.info("🎓 No skills learned yet. Complete steps to earn skills!")
        return
    
    st.markdown("### ✨ Skills You've Acquired")
    
    for skill in st.session_state.learned_skills:
        st.markdown(f'<span class="skill-badge">{skill}</span>', unsafe_allow_html=True)

def summary_view():
    """Show progress summary"""
    st.markdown("### 📊 Journey Summary")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Journey Details:**")
        st.json({
            "Original Goal": st.session_state.original_goal,
            "Current Target": st.session_state.current_target,
            "Started": "Assessment Complete",
            "Reroutes": len(st.session_state.reroute_history)
        })
    
    with col2:
        st.markdown("**Progress Metrics:**")
        st.json({
            "Completion": f"{calculate_progress():.1f}%",
            "Steps Done": f"{len(st.session_state.completed_steps)}/{len(st.session_state.roadmap)}",
            "Motivation": f"{calculate_motivation()*100:.0f}%",
            "Skills Learned": len(st.session_state.learned_skills),
            "Active Blockers": len(st.session_state.blockers)
        })

def reevaluation_page():
    """Re-evaluation page with alternatives"""
    st.markdown('<p class="main-header">🔄 Path Re-Evaluation</p>', unsafe_allow_html=True)
    
    reeval = st.session_state.reevaluation_data
    
    if not reeval:
        st.error("No re-evaluation data")
        if st.button("← Back to Dashboard"):
            st.session_state.page = "dashboard"
            st.rerun()
        return
    
    # Explain why re-evaluation was triggered
    trigger_messages = {
        "repeated_blocker": "You've struggled with the same step multiple times",
        "multiple_blockers": "You have blockers on multiple steps",
        "periodic_check": "Regular progress checkpoint reached",
        "low_motivation": "Your motivation level has dropped"
    }
    
    trigger_type = reeval["trigger_type"]
    st.markdown(f"""
    <div class="warning-box">
        <h3>⚠️ Re-evaluation Triggered</h3>
        <p><strong>Reason:</strong> {trigger_messages.get(trigger_type, 'Unknown')}</p>
        <p>Don't worry - this is normal! Let's find a path that works better for you.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")

    # Show alternatives
    alternatives = reeval["alternatives"]

    if alternatives:
        st.markdown("### 🎯 Recommended Alternative Paths")
        
        for i, alt in enumerate(alternatives):
            with st.container():
                st.markdown(f"""
                <div class="alternative-card">
                    <h3>{i+1}. {alt['role']} - Match Score: {alt['total_score']*100:.0f}%</h3>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown("**Why this is a better fit:**")
                    st.markdown(alt['justification'])
                    
                    st.markdown("**Market Data:**")
                    market = alt.get('market_data', {})
                    st.markdown(f"- 📊 Active Jobs: **{market.get('active_jobs', 'N/A')}**")
                    st.markdown(f"- 🎯 Your Skill Match: **{market.get('skill_match', 0)*100:.0f}%**")
                    st.markdown(f"- 💰 Salary: **{market.get('avg_salary_range', 'N/A')}**")
                    st.markdown(f"- 🚪 Entry Barrier: **{market.get('entry_barrier', 0)*100:.0f}%**")
                
                with col2:
                    if st.button(f"🔄 Switch to {alt['role']}", key=f"switch_{i}", type="primary", use_container_width=True):
                        switch_to_alternative(alt)
                
                # Show roadmap preview
                with st.expander(f"👁️ Preview Roadmap ({len(alt.get('roadmap', {}).get('roadmap', []))} steps)"):
                    roadmap_preview = alt.get('roadmap', {}).get('roadmap', [])
                    for step in roadmap_preview[:5]:  # Show first 5
                        st.markdown(f"**{step.get('step_number')}. {step.get('title')}** ({step.get('duration_weeks')} weeks)")
                        st.caption(step.get('description', '')[:100] + "...")
                
                st.markdown("---")

    # Option to continue
    st.markdown("### 💪 Or Continue Your Current Path")

    current_target = st.session_state.current_target
    st.warning(f"⚠️ Continuing with **{current_target}** will be challenging. Are you sure?")

    col_a, col_b = st.columns(2)

    with col_a:
        if st.button("➡️ Continue Current Path", type="secondary", use_container_width=True):
            st.session_state.page = "dashboard"
            st.session_state.reevaluation_data = None
            st.success("Continuing with current path. Good luck! 💪")
            st.rerun()

    with col_b:
        if st.button("🏠 Start Fresh Assessment", use_container_width=True):
            # Reset everything
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            init_session_state()
            st.rerun()

def roadmap_completion_page():
    """Page shown when user completes entire roadmap"""
    st.markdown('<p class="main-header">🎓 Path Completed!</p>', unsafe_allow_html=True)
    
    current_target = st.session_state.current_target
    original_goal = st.session_state.original_goal
    has_switched = current_target != original_goal
    
    st.markdown(f"""
    <div class="success-box">
        <h3>🎉 Congratulations!</h3>
        <p>You've successfully completed the <strong>{current_target}</strong> learning path!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Summary of journey
    st.markdown("### 📊 Your Journey Summary")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Steps Completed", len(st.session_state.completed_steps))
    with col2:
        st.metric("Skills Acquired", len(st.session_state.learned_skills))
    with col3:
        total_hours = sum(status.get('time_spent', 0) for status in st.session_state.step_status.values())
        st.metric("Hours Invested", f"{total_hours:.1f}h")
    
    # Show learned skills
    st.markdown("#### ✨ Skills You've Mastered:")
    for skill in st.session_state.learned_skills:
        st.markdown(f'<span class="skill-badge">{skill}</span>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 🚀 What's Next?")
    
    # Option 1: Continue in same domain with advanced role
    st.markdown("#### Option 1: 📈 Level Up in the Same Domain")
    st.markdown("""
    You've proven yourself in **{}**. Now advance to a more senior role in the same domain:
    - **Why?** Your existing skills provide a strong foundation
    - **What's different?** Higher complexity, leadership, specialization
    - **Time needed?** Usually 8-12 weeks
    """.format(current_target))
    
    if st.button("🚀 Advance to Senior Role", type="primary", use_container_width=True, key="advance_role"):
        generate_advanced_path()
    
    # Show alternative roles for advancing
    with st.expander("👀 See Alternative Advanced Roles"):
        completion_show_alternatives()
    
    st.markdown("---")
    
    # Option 2: Return to original goal if they switched
    if has_switched:
        st.markdown("#### Option 2: 🔄 Return to Your Original Goal")
        st.markdown(f"""
        <div class="warning-box">
            <h4>💡 Why You Can Return Now:</h4>
            <p>Your journey changed from <strong>{original_goal}</strong> to <strong>{current_target}</strong>, but now you're ready:</p>
            <ul>
                <li>✅ You've completed a full career path</li>
                <li>✅ You've gained {len(st.session_state.learned_skills)} valuable skills</li>
                <li>✅ Many skills from **{current_target}** transfer to **{original_goal}**</li>
                <li>✅ Your skill gap is now much smaller</li>
            </ul>
            <p><strong>Result:</strong> The original **{original_goal}** path will be faster and easier now!</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("➡️ Switch Back to Original Goal", use_container_width=True, key="return_original"):
            return_to_original_goal()
    
    st.markdown("---")
    
    # Option 3: Explore entirely new path
    st.markdown("#### Option 3: 🌟 Explore a Completely New Career Path")
    st.markdown("""
    You've completed one path successfully! Start fresh with:
    - A new role in a different domain
    - New set of challenges and skills
    - All your current skills as a head start
    """)
    
    if st.button("🏠 Start Fresh Assessment", use_container_width=True, key="fresh_assessment"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        init_session_state()
        st.rerun()

def completion_show_alternatives():
    """Show alternative advanced roles during completion"""
    orchestrator = get_orchestrator()
    
    if not orchestrator:
        st.error("System not available")
        return
    
    # Check if we already generated these
    if st.session_state.completion_alternatives is None:
        with st.spinner("🤖 Analyzing alternative advanced roles..."):
            try:
                current_target = st.session_state.current_target
                
                # Get all skills learned
                all_skills = []
                current_skills = st.session_state.assessment_result["profile"]["technical_skills"]
                for category, skills in current_skills.items():
                    all_skills.extend(skills)
                all_skills.extend(st.session_state.learned_skills)
                
                # Get market analysis for current role
                current_market = orchestrator.market_intelligence.analyze_role_market(
                    role_name=current_target,
                    student_skills=all_skills
                )["market_analysis"]
                
                # Find alternatives (will suggest different advanced paths)
                alternatives_result = orchestrator.reroute_agent.find_alternatives(
                    student_profile=st.session_state.assessment_result["profile"],
                    failed_role=current_target,
                    failed_market_analysis=current_market,
                    top_n=3
                )
                
                alternatives = alternatives_result["reroute_recommendations"]["alternatives"]
                
                # Generate roadmaps and market analysis in parallel
                def analyze_alternative(alt):
                    try:
                        alt_market = orchestrator.market_intelligence.analyze_role_market(
                            role_name=alt["role"],
                            student_skills=all_skills
                        )["market_analysis"]
                        
                        alt_roadmap = orchestrator.roadmap_generator.generate_roadmap(
                            target_role=alt["role"],
                            student_profile=st.session_state.assessment_result["profile"],
                            market_analysis=alt_market,
                            duration_weeks=10
                        )
                        
                        alt["roadmap"] = alt_roadmap
                        alt["market_data"] = alt_market
                    except Exception as e:
                        st.warning(f"Could not analyze {alt['role']}: {e}")
                
                # Use thread pool for concurrent analysis
                with ThreadPoolExecutor(max_workers=3) as executor:
                    list(executor.map(analyze_alternative, alternatives))
                
                # Cache alternatives
                st.session_state.completion_alternatives = alternatives
                
            except Exception as e:
                st.error(f"Failed to analyze alternatives: {e}")
                import traceback
                st.code(traceback.format_exc())
                return
    
    # Display alternatives
    alternatives = st.session_state.get('completion_alternatives', [])
    
    if not alternatives:
        st.info("No alternative roles found")
        return
    
    st.markdown("**🎯 Alternative Advanced Roles:**")
    
    for i, alt in enumerate(alternatives):
        with st.container():
            st.markdown(f"""
            <div class="alternative-card">
                <h4>{i+1}. {alt['role']} - Match: {alt['total_score']*100:.0f}%</h4>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**Why this role:** {alt['justification']}")
                
                market = alt.get('market_data', {})
                st.markdown(f"- 📊 Jobs: {market.get('active_jobs', 'N/A')} | 🎯 Match: {market.get('skill_match', 0)*100:.0f}% | 💰 {market.get('avg_salary_range', 'N/A')}")
            
            with col2:
                if st.button(f"🔄 Switch to", key=f"comp_switch_{i}", type="primary", use_container_width=True):
                    switch_to_alternative(alt)
            
            st.caption(f"Roadmap: {len(alt.get('roadmap', {}).get('roadmap', []))} steps")
            st.markdown("---")

def generate_advanced_path():
    """Generate advanced/senior path in same domain"""
    orchestrator = get_orchestrator()
    if not orchestrator:
        st.error("System not available")
        return
    
    with st.spinner("🤖 Generating advanced path..."):
        try:
            current_role = st.session_state.current_target
            
            # Get all skills learned so far
            all_skills = []
            current_skills = st.session_state.assessment_result["profile"]["technical_skills"]
            for category, skills in current_skills.items():
                all_skills.extend(skills)
            all_skills.extend(st.session_state.learned_skills)
            
            # Create advanced role name
            advanced_role = f"Senior {current_role}"
            
            # Analyze market for advanced role
            advanced_market = orchestrator.market_intelligence.analyze_role_market(
                role_name=advanced_role,
                student_skills=all_skills
            )["market_analysis"]
            
            # Generate advanced roadmap
            advanced_roadmap = orchestrator.roadmap_generator.generate_roadmap(
                target_role=advanced_role,
                student_profile=st.session_state.assessment_result["profile"],
                market_analysis=advanced_market,
                duration_weeks=10
            )
            
            # Update session state
            st.session_state.roadmap = advanced_roadmap["roadmap"]
            st.session_state.completed_steps = []
            st.session_state.blockers = {}
            st.session_state.step_status = {}
            
            # Initialize new steps (but keep learned skills!)
            for i in range(len(st.session_state.roadmap)):
                st.session_state.step_status[i+1] = {"status": "not_started", "time_spent": 0}
            
            # Record progression
            if 'progression_history' not in st.session_state:
                st.session_state.progression_history = []
            
            st.session_state.progression_history.append({
                "from_role": current_role,
                "to_role": advanced_role,
                "type": "advancement",
                "timestamp": datetime.now().isoformat(),
                "skills_at_progression": st.session_state.learned_skills.copy()
            })
            
            st.session_state.current_target = advanced_role
            st.session_state.page = "dashboard"
            
            st.success(f"✅ Advanced path to {advanced_role} created!")
            st.info(f"Your {len(st.session_state.learned_skills)} existing skills will help you move faster!")
            st.balloons()
            st.rerun()
            
        except Exception as e:
            st.error(f"Failed to generate advanced path: {e}")
            import traceback
            st.code(traceback.format_exc())

def return_to_original_goal():
    """Return to original goal with enhanced profile"""
    orchestrator = get_orchestrator()
    if not orchestrator:
        st.error("System not available")
        return
    
    with st.spinner("🤖 Regenerating path to your original goal..."):
        try:
            original_role = st.session_state.original_goal
            
            # Get all skills learned so far
            all_skills = []
            current_skills = st.session_state.assessment_result["profile"]["technical_skills"]
            for category, skills in current_skills.items():
                all_skills.extend(skills)
            all_skills.extend(st.session_state.learned_skills)
            
            # Analyze market for original role
            market_analysis = orchestrator.market_intelligence.analyze_role_market(
                role_name=original_role,
                student_skills=all_skills
            )["market_analysis"]
            
            # Generate new roadmap (will be much shorter now with existing skills)
            new_roadmap = orchestrator.roadmap_generator.generate_roadmap(
                target_role=original_role,
                student_profile=st.session_state.assessment_result["profile"],
                market_analysis=market_analysis,
                duration_weeks=8
            )
            
            # Update session state
            st.session_state.roadmap = new_roadmap["roadmap"]
            st.session_state.completed_steps = []
            st.session_state.blockers = {}
            st.session_state.step_status = {}
            
            # Initialize new steps (but keep learned skills!)
            for i in range(len(st.session_state.roadmap)):
                st.session_state.step_status[i+1] = {"status": "not_started", "time_spent": 0}
            
            # Record reroute
            st.session_state.reroute_history.append({
                "from_role": st.session_state.current_target,
                "to_role": original_role,
                "reason": "Returned to original goal after completing alternate path",
                "timestamp": datetime.now().isoformat(),
                "skills_at_reroute": st.session_state.learned_skills.copy()
            })
            
            st.session_state.current_target = original_role
            st.session_state.page = "dashboard"
            
            st.success(f"✅ You're returning to {original_role}!")
            st.info(f"With your {len(st.session_state.learned_skills)} acquired skills, this path will be much faster!")
            st.balloons()
            st.rerun()
            
        except Exception as e:
            st.error(f"Failed to generate path: {e}")
            import traceback
            st.code(traceback.format_exc())

def switch_to_alternative(alt):
    """Switch to an alternative career path"""
    orchestrator = get_orchestrator()
    if not orchestrator:
        st.error("System not available")
        return

    from_role = st.session_state.current_target
    to_role = alt["role"]

    with st.spinner(f"🔄 Switching to {to_role}..."):
        # Record reroute in history
        reason = "Career path switch"
        if st.session_state.reevaluation_data and 'trigger_type' in st.session_state.reevaluation_data:
            reason = f"Re-evaluated due to {st.session_state.reevaluation_data['trigger_type']}"
        
        st.session_state.reroute_history.append({
            "from_role": from_role,
            "to_role": to_role,
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
            "skills_at_reroute": st.session_state.learned_skills.copy()
        })
        
        # Update target
        st.session_state.current_target = to_role
        
        # Set new roadmap - handle both structures
        roadmap_data = alt.get("roadmap", {})
        if isinstance(roadmap_data, list):
            # Direct list structure
            st.session_state.roadmap = roadmap_data
        else:
            # Dict structure with "roadmap" key
            st.session_state.roadmap = roadmap_data.get("roadmap", [])
        
        # PRESERVE learned skills (don't reset!)
        # Reset progress but KEEP skills
        st.session_state.completed_steps = []
        st.session_state.blockers = {}
        st.session_state.step_status = {}
        
        # Initialize new steps
        for i in range(len(st.session_state.roadmap)):
            st.session_state.step_status[i+1] = {"status": "not_started", "time_spent": 0}
        
        # Clear re-evaluation data
        st.session_state.reevaluation_data = None
        
        # Go back to dashboard
        st.session_state.page = "dashboard"
        
        st.success(f"✅ Successfully switched to {to_role}!")
        st.balloons()
        
        # Show what was preserved
        if st.session_state.learned_skills:
            st.info(f"✨ Your learned skills have been preserved: {', '.join(st.session_state.learned_skills)}")
        
        st.rerun()
###========== SIDEBAR ==========
with st.sidebar:
    st.markdown("### 🎓 Career Agent")
    if st.session_state.page != "home":
        st.success("✅ Journey Active")
        
        # Navigation
        st.markdown("### 📍 Navigation")
        
        if st.button("📊 Dashboard", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()
        
        if st.session_state.reevaluation_data:
            if st.button("🔄 Re-evaluation", use_container_width=True):
                st.session_state.page = "reevaluation"
                st.rerun()
        
        st.markdown("---")
        
        # Quick stats
        st.markdown("### 📈 Quick Stats")
        st.metric("Progress", f"{calculate_progress():.0f}%")
        st.metric("Skills", len(st.session_state.learned_skills))
        st.metric("Blockers", len(st.session_state.blockers))
        
        st.markdown("---")
        
        if st.button("🏠 New Assessment", use_container_width=True):
            # Confirm before resetting
            if st.button("⚠️ Confirm Reset?", type="secondary"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                init_session_state()
                st.rerun()

    st.markdown("---")
    st.caption("Made with ❤️ for your career growth.")
##========== MAIN ROUTING ==========
def main():
    """Main app routing"""
    # Check for roadmap completion before rendering dashboard
    if st.session_state.page == "dashboard" and check_roadmap_completion():
        st.session_state.page = "completion"
    
    page = st.session_state.page
    if page == "home":
        home_page()
    elif page == "dashboard":
        dashboard_page()
    elif page == "completion":
        roadmap_completion_page()
    elif page == "reevaluation":
        reevaluation_page()
    else:
        st.error(f"Unknown page: {page}")
if __name__ == "__main__":
    main()