"""
Streamlit UI for Career Agent System
Complete testing interface with all features
"""

import streamlit as st
import requests
import json
from datetime import datetime
import os

# ========== CONFIGURATION ==========

API_BASE = os.getenv("API_BASE", "http://localhost:8000")

# Page config
st.set_page_config(
    page_title="Career Agent System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
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
        padding: 1rem;
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
    .progress-metric {
        background-color: #1f77b4;
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .blocker-alert {
        background-color: #fff3cd;
        border: 1px solid #ffc107;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .alternative-card {
        border: 2px solid #dee2e6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        cursor: pointer;
        transition: all 0.3s;
    }
    .alternative-card:hover {
        border-color: #1f77b4;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
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
</style>
""", unsafe_allow_html=True)

# ========== SESSION STATE INITIALIZATION ==========

if 'session_id' not in st.session_state:
    st.session_state.session_id = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = "test_user_" + datetime.now().strftime("%Y%m%d%H%M%S")
if 'page' not in st.session_state:
    st.session_state.page = "home"
if 'reevaluation_data' not in st.session_state:
    st.session_state.reevaluation_data = None

# ========== HELPER FUNCTIONS ==========

def check_api_health():
    """Check if API is running"""
    try:
        response = requests.get(f"{API_BASE}/")
        return response.status_code == 200
    except:
        return False

def call_api(endpoint, method="GET", data=None):
    """Generic API caller with error handling"""
    try:
        url = f"{API_BASE}{endpoint}"
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"Error {response.status_code}: {response.text}"
    except Exception as e:
        return None, f"Connection error: {str(e)}"

def format_duration(weeks):
    """Format weeks into human-readable duration"""
    if weeks < 4:
        return f"{weeks} weeks"
    else:
        months = weeks / 4
        return f"{months:.1f} months ({weeks} weeks)"

def get_status_emoji(status):
    """Get emoji for step status"""
    if status == "completed":
        return "✅"
    elif status == "blocked":
        return "🚫"
    elif status == "in_progress":
        return "🔄"
    else:
        return "⏳"

# ========== PAGES ==========

def home_page():
    """Initial assessment page"""
    st.markdown('<p class="main-header">🎓 Career Path Analyzer</p>', unsafe_allow_html=True)
    
    # Check API health
    if not check_api_health():
        st.error(f"⚠️ Cannot connect to API at {API_BASE}")
        st.info("Make sure the backend server is running: `cd api && python main.py`")
        return
    
    st.success(f"✅ Connected to API at {API_BASE}")
    
    st.markdown("### Tell us about yourself")
    
    col1, col2 = st.columns(2)
    
    with col1:
        desired_role = st.text_input(
            "🎯 Target Career Role",
            value="Data Analyst",
            help="What role do you want to achieve?"
        )
        
        skills_text = st.text_area(
            "💻 Your Current Skills",
            value="Python, SQL, Excel",
            help="List your technical skills (comma-separated)"
        )
        
        education = st.text_input(
            "🎓 Education",
            value="3rd year B.Tech Computer Science",
            help="Your current or highest education"
        )
    
    with col2:
        experience = st.text_area(
            "💼 Experience (Optional)",
            value="",
            help="Work experience, internships, etc."
        )
        
        projects = st.text_area(
            "🚀 Projects (Optional)",
            value="Data visualization dashboard",
            help="One project per line"
        )
        
        duration_weeks = st.slider(
            "⏱️ Available Time",
            min_value=4,
            max_value=24,
            value=12,
            help="How many weeks can you dedicate?"
        )
    
    if st.button("🔍 Analyze My Career Path", type="primary", use_container_width=True):
        with st.spinner("🤖 AI agents are analyzing your profile..."):
            # Prepare data
            assessment_data = {
                "user_id": st.session_state.user_id,
                "desired_role": desired_role,
                "skills_text": skills_text if skills_text else None,
                "education": education if education else None,
                "experience": experience if experience else None,
                "projects": [p.strip() for p in projects.split("\n") if p.strip()],
                "duration_weeks": duration_weeks
            }
            
            # Call API
            result, error = call_api("/api/assess", method="POST", data=assessment_data)
            
            if error:
                st.error(f"❌ Assessment failed: {error}")
                return
            
            # Save session
            st.session_state.session_id = result['session_id']
            st.session_state.page = "dashboard"
            
            st.success(f"✅ Assessment complete! Session ID: {result['session_id']}")
            st.rerun()

def dashboard_page():
    """Main dashboard with progress"""
    
    # Fetch journey summary
    result, error = call_api(f"/api/journey/{st.session_state.session_id}/summary")
    
    if error:
        st.error(f"❌ Failed to load dashboard: {error}")
        if st.button("← Back to Home"):
            st.session_state.page = "home"
            st.rerun()
        return
    
    journey = result['journey']
    progress = result['progress']
    steps = result['steps']
    blockers = result['blockers']
    reevaluations = result['reevaluations']
    reroutes = result['reroutes']
    skills_learned = result['skills_learned']
    
    # Header
    st.markdown('<p class="main-header">📊 Your Learning Journey</p>', unsafe_allow_html=True)
    
    # Show reroute history if exists
    if reroutes:
        with st.expander("📜 Journey History", expanded=False):
            for reroute in reroutes:
                st.info(f"🔄 Rerouted from **{reroute['from_role']}** to **{reroute['to_role']}** on {reroute['reroute_date'][:10]}")
    
    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="progress-metric">
            <h3>{progress['progress_percentage']:.0f}%</h3>
            <p>Progress</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="progress-metric">
            <h3>{progress['completed_steps']}/{progress['total_steps']}</h3>
            <p>Steps Completed</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        motivation_color = "#2ecc71" if progress['motivation_level'] >= 0.7 else "#f39c12" if progress['motivation_level'] >= 0.5 else "#e74c3c"
        st.markdown(f"""
        <div class="progress-metric" style="background-color: {motivation_color}">
            <h3>{progress['motivation_level']*100:.0f}%</h3>
            <p>Motivation</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="progress-metric" style="background-color: #8e44ad">
            <h3>{len(skills_learned)}</h3>
            <p>Skills Learned</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Active blockers alert
    if blockers:
        st.markdown(f"""
        <div class="blocker-alert">
            <h4>⚠️ Active Blockers: {len(blockers)}</h4>
            <p>You have {len(blockers)} step(s) that need attention</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📚 Roadmap", "🎓 Skills Learned", "🚫 Blockers", "📈 Analytics"])
    
    with tab1:
        roadmap_tab(journey, steps)
    
    with tab2:
        skills_tab(skills_learned)
    
    with tab3:
        blockers_tab(blockers, steps)
    
    with tab4:
        analytics_tab(result)

def roadmap_tab(journey, steps):
    """Display roadmap with step cards"""
    st.markdown(f"### 🎯 Target Role: **{journey['target_role']}**")
    
    roadmap = journey['roadmap']
    
    if not roadmap:
        st.warning("No roadmap available")
        return
    
    for i, step_data in enumerate(roadmap):
        # Get corresponding step progress
        step_progress = None
        for sp in steps:
            if sp['step_number'] == step_data['step_number']:
                step_progress = sp
                break
        
        status = step_progress['status'] if step_progress else 'not_started'
        emoji = get_status_emoji(status)
        
        # Card styling based on status
        card_class = "step-card"
        if status == "completed":
            card_class += " completed-step"
        elif status == "blocked":
            card_class += " blocked-step"
        
        with st.container():
            st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"### {emoji} Step {step_data['step_number']}: {step_data['title']}")
                st.markdown(f"**Description:** {step_data['description']}")
                st.markdown(f"**Duration:** {step_data['duration_weeks']} weeks")
                st.markdown(f"**Why Important:** {step_data.get('why_important', 'N/A')}")
                
                # Skills covered
                if step_data.get('skills_covered'):
                    st.markdown("**Skills:** " + ", ".join([
                        f'<span class="skill-badge">{skill}</span>' 
                        for skill in step_data['skills_covered']
                    ]), unsafe_allow_html=True)
                
                # Resources
                if step_data.get('resources'):
                    with st.expander(f"📚 Resources ({len(step_data['resources'])})"):
                        for resource in step_data['resources']:
                            st.markdown(f"- [{resource['title']}]({resource['url']}) - {resource.get('type', 'N/A')} ({resource.get('duration_hours', 'N/A')} hours)")
            
            with col2:
                st.markdown(f"**Status:** {status.replace('_', ' ').title()}")
                
                if step_progress and step_progress.get('time_spent_hours'):
                    st.markdown(f"**Time Spent:** {step_progress['time_spent_hours']:.1f}h")
                
                # Action buttons
                if status == "not_started":
                    if st.button(f"▶️ Start", key=f"start_{i}"):
                        st.info("In real app, mark as in_progress")
                
                elif status == "in_progress":
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("✅", key=f"complete_{i}", help="Mark Complete"):
                            mark_step_complete(step_data['step_number'])
                    with col_b:
                        if st.button("🚫", key=f"block_{i}", help="Report Blocker"):
                            st.session_state[f'show_blocker_form_{i}'] = True
                    
                    # Blocker form
                    if st.session_state.get(f'show_blocker_form_{i}', False):
                        with st.form(f"blocker_form_{i}"):
                            reason = st.text_area("What's blocking you?", key=f"reason_{i}")
                            hours = st.number_input("Hours spent so far", min_value=0.0, key=f"hours_{i}")
                            
                            col_x, col_y = st.columns(2)
                            with col_x:
                                if st.form_submit_button("Submit"):
                                    report_blocker(step_data['step_number'], reason, hours)
                            with col_y:
                                if st.form_submit_button("Cancel"):
                                    st.session_state[f'show_blocker_form_{i}'] = False
                                    st.rerun()
                
                elif status == "completed":
                    st.success("✅ Completed")
                    if step_progress.get('completed_at'):
                        st.caption(f"{step_progress['completed_at'][:10]}")
                
                elif status == "blocked":
                    st.error("🚫 Blocked")
            
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("---")

def skills_tab(skills_learned):
    """Display learned skills"""
    if not skills_learned:
        st.info("No skills learned yet. Complete steps to earn skills!")
        return
    
    st.markdown("### 🎓 Skills You've Acquired")
    
    # Group by proficiency
    beginner = [s for s in skills_learned if s['proficiency_level'] == 'beginner']
    intermediate = [s for s in skills_learned if s['proficiency_level'] == 'intermediate']
    advanced = [s for s in skills_learned if s['proficiency_level'] == 'advanced']
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### Beginner")
        for skill in beginner:
            st.markdown(f'<span class="skill-badge" style="background-color: #3498db">{skill["skill_name"]}</span>', unsafe_allow_html=True)
    
    with col2:
        st.markdown("#### Intermediate")
        for skill in intermediate:
            st.markdown(f'<span class="skill-badge" style="background-color: #2ecc71">{skill["skill_name"]}</span>', unsafe_allow_html=True)
    
    with col3:
        st.markdown("#### Advanced")
        for skill in advanced:
            st.markdown(f'<span class="skill-badge" style="background-color: #9b59b6">{skill["skill_name"]}</span>', unsafe_allow_html=True)

def blockers_tab(blockers, steps):
    """Display and manage blockers"""
    if not blockers:
        st.success("🎉 No active blockers! You're doing great!")
        return
    
    st.markdown("### 🚫 Active Blockers")
    
    for idx, blocker in enumerate(blockers):
        with st.expander(f"Step {blocker['step_number']} - {blocker['reason'][:50]}...", expanded=True):
            st.markdown(f"**Reason:** {blocker['reason']}")
            st.markdown(f"**Attempts:** {blocker['attempts']}")
            st.markdown(f"**First Reported:** {blocker['first_reported'][:10]}")
            st.markdown(f"**Last Reported:** {blocker['last_reported'][:10]}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"✅ Mark Resolved", key=f"blockers_tab_resolve_{blocker['id']}_{idx}"):
                    # In real app: call API to resolve blocker
                    st.success("Blocker resolved!")
            
            with col2:
                if st.button(f"🔄 Update", key=f"blockers_tab_update_{blocker['id']}_{idx}"):
                    # In real app: report blocker again
                    st.info("Report blocker again to increment attempts")

def analytics_tab(summary):
    """Show analytics and insights"""
    st.markdown("### 📈 Journey Analytics")
    
    journey = summary['journey']
    progress = summary['progress']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Journey Details")
        st.json({
            "Session ID": journey['session_id'],
            "Target Role": journey['target_role'],
            "Desired Role": journey['desired_role'],
            "Status": journey['status'],
            "Verdict": journey['feasibility_verdict'],
            "Started": journey['start_date'][:10],
            "Last Activity": journey['last_activity'][:10]
        })
    
    with col2:
        st.markdown("#### Progress Metrics")
        st.json({
            "Completion": f"{progress['progress_percentage']:.1f}%",
            "Steps": f"{progress['completed_steps']}/{progress['total_steps']}",
            "Motivation": f"{progress['motivation_level']*100:.0f}%",
            "Current Step": progress['current_step']
        })
    
    # Timeline
    if summary['reevaluations']:
        st.markdown("#### Re-evaluation History")
        for reeval in summary['reevaluations']:
            st.info(f"**{reeval['trigger_type']}** ({reeval['trigger_severity']}) - {reeval['action_taken']} - {reeval['created_at'][:10]}")

def mark_step_complete(step_number):
    """Mark a step as completed"""
    # Get time spent
    hours = st.number_input("Hours spent on this step", min_value=0.0, value=20.0, key="hours_complete")
    
    if st.button("Confirm Completion", type="primary"):
        data = {
            "session_id": st.session_state.session_id,
            "step_number": step_number,
            "status": "completed",
            "time_spent_hours": hours
        }
        
        result, error = call_api("/api/progress", method="POST", data=data)
        
        if error:
            st.error(f"Failed to mark complete: {error}")
            return
        
        # Check for re-evaluation
        if result.get('should_reevaluate') and result.get('reevaluation'):
            st.session_state.reevaluation_data = result['reevaluation']
            st.session_state.page = "reevaluation"
            st.success(f"✅ Step {step_number} completed!")
            st.info("🔄 Re-evaluation triggered! Check the Re-evaluation tab.")
            st.rerun()
        else:
            st.success(f"✅ Step {step_number} completed!")
            st.rerun()

def report_blocker(step_number, reason, hours):
    """Report a blocker on a step"""
    data = {
        "session_id": st.session_state.session_id,
        "step_number": step_number,
        "status": "blocked",
        "blocker_reason": reason,
        "time_spent_hours": hours
    }
    
    result, error = call_api("/api/progress", method="POST", data=data)
    
    if error:
        st.error(f"Failed to report blocker: {error}")
        return
    
    # Check for re-evaluation
    if result.get('should_reevaluate') and result.get('reevaluation'):
        st.session_state.reevaluation_data = result['reevaluation']
        st.session_state.page = "reevaluation"
        st.warning("⚠️ Blocker reported! Re-evaluation triggered.")
        st.rerun()
    else:
        st.warning(f"⚠️ Blocker reported for step {step_number}")
        st.rerun()

def reevaluation_page():
    """Show re-evaluation results and alternatives"""
    st.markdown('<p class="main-header">🔄 Path Re-evaluation</p>', unsafe_allow_html=True)
    
    reeval = st.session_state.reevaluation_data
    
    if not reeval:
        st.error("No re-evaluation data available")
        if st.button("← Back to Dashboard"):
            st.session_state.page = "dashboard"
            st.rerun()
        return
    
    # Show triggers
    st.markdown("### ⚠️ Concerns Detected")
    
    for trigger in reeval['triggers']:
        severity_color = {
            'low': '#3498db',
            'medium': '#f39c12',
            'high': '#e67e22',
            'critical': '#e74c3c'
        }.get(trigger['severity'], '#95a5a6')
        
        st.markdown(f"""
        <div style="background-color: {severity_color}; color: white; padding: 1rem; border-radius: 0.5rem; margin: 0.5rem 0;">
            <strong>{trigger['type'].upper()}:</strong> {trigger['reason']}
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown(f"### 💬 {reeval['message']}")
    
    # Show alternatives
    if reeval.get('alternatives') and len(reeval['alternatives']) > 0:
        st.markdown("### 🎯 Recommended Alternative Paths")
        
        for i, alt in enumerate(reeval['alternatives']):
            with st.container():
                st.markdown(f"""
                <div class="alternative-card">
                    <h3>{alt['role']} - {alt['score']*100:.0f}% Match</h3>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Why this is a better fit:**")
                    st.markdown(alt['justification'])
                    
                    st.markdown("**Market Data:**")
                    market = alt['market_data']
                    st.markdown(f"- 📊 Active Jobs: **{market['active_jobs']}**")
                    st.markdown(f"- 🎯 Skill Match: **{market['skill_match']*100:.0f}%**")
                    st.markdown(f"- 🚪 Entry Barrier: **{market['entry_barrier']*100:.0f}%**")
                
                with col2:
                    if st.button(f"🔄 Switch to {alt['role']}", key=f"switch_{i}", type="primary"):
                        accept_reroute(alt['role'])
                
                # Show roadmap preview
                with st.expander(f"👁️ Preview Roadmap for {alt['role']}"):
                    if alt.get('roadmap') and alt['roadmap'].get('roadmap'):
                        for step in alt['roadmap']['roadmap'][:3]:
                            st.markdown(f"**{step['step_number']}. {step['title']}** ({step['duration_weeks']} weeks)")
                            st.caption(step['description'][:100] + "...")
                    else:
                        st.info("Roadmap preview not available")
                
                st.markdown("---")
    
    # Option to continue
    st.markdown("### 💪 Or Continue Current Path")
    
    if reeval.get('current_path'):
        current = reeval['current_path']
        if current.get('can_continue'):
            difficulty = current.get('difficulty', 'medium')
            st.warning(f"⚠️ Continuing will be **{difficulty}** difficulty. Make sure you're ready!")
            
            if st.button("➡️ Continue Current Path", type="secondary"):
                st.session_state.page = "dashboard"
                st.session_state.reevaluation_data = None
                st.success("Continuing with current path. Good luck!")
                st.rerun()

def accept_reroute(new_role):
    """Accept a reroute to new role"""
    reeval = st.session_state.reevaluation_data
    
    data = {
        "session_id": st.session_state.session_id,
        "reevaluation_id": reeval['reevaluation_id'],
        "chosen_role": new_role,
        "reason": "struggling"
    }
    
    with st.spinner(f"🔄 Switching to {new_role}..."):
        result, error = call_api("/api/reroute", method="POST", data=data)
        
        if error:
            st.error(f"Failed to reroute: {error}")
            return
        
        st.success(f"✅ Successfully switched to {new_role}!")
        st.balloons()
        
        st.session_state.page = "dashboard"
        st.session_state.reevaluation_data = None
        
        st.info("Your progress has been reset and you have a new roadmap. Let's start fresh!")
        
        st.rerun()

# ========== SIDEBAR ==========

with st.sidebar:
    st.markdown("### 🎓 Career Agent")
    
    if st.session_state.session_id:
        st.success(f"✅ Active Session")
        st.caption(f"ID: {st.session_state.session_id[:8]}...")
        
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
        
        if st.button("🏠 New Assessment", use_container_width=True):
            st.session_state.session_id = None
            st.session_state.page = "home"
            st.session_state.reevaluation_data = None
            st.rerun()
    
    else:
        st.info("No active session")
    
    st.markdown("---")
    
    st.markdown("### ⚙️ Settings")
    api_url = st.text_input("API URL", value=API_BASE)
    if api_url != API_BASE:
        st.warning("API URL changed (restart to apply)")
    
    st.markdown("---")
    st.caption("Made with ❤️ using Streamlit")

# ========== MAIN APP ==========

def main():
    # Route to appropriate page
    if st.session_state.page == "home":
        home_page()
    elif st.session_state.page == "dashboard":
        if st.session_state.session_id:
            dashboard_page()
        else:
            st.error("No active session. Please start a new assessment.")
            st.session_state.page = "home"
            st.rerun()
    elif st.session_state.page == "reevaluation":
        reevaluation_page()

if __name__ == "__main__":
    main()