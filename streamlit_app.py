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
if 'show_reevaluation' not in st.session_state:
    st.session_state.show_reevaluation = False

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

def complete_step_api(step_number, hours):
    """API call to mark step as completed"""
    data = {
        "session_id": st.session_state.session_id,
        "step_number": step_number,
        "status": "completed",
        "time_spent_hours": hours
    }
    
    result, error = call_api("/api/progress", method="POST", data=data)
    
    if error:
        st.error(f"❌ Failed to mark complete: {error}")
        return False
    
    st.success(f"✅ Step {step_number} marked as completed!")
    
    # Check for re-evaluation
    if result.get('should_reevaluate') and result.get('reevaluation'):
        st.warning("🔄 Re-evaluation triggered based on your progress!")
        st.session_state.reevaluation_data = result['reevaluation']
        st.session_state.show_reevaluation = True
    
    # Clear form state
    st.session_state[f'show_complete_form_{step_number}'] = False
    st.rerun()

def report_blocker_api(step_number, reason, hours):
    """API call to report a blocker"""
    if not reason or reason.strip() == "":
        st.error("❌ Please describe what's blocking you")
        return False
    
    data = {
        "session_id": st.session_state.session_id,
        "step_number": step_number,
        "status": "blocked",
        "blocker_reason": reason,
        "time_spent_hours": hours
    }
    
    result, error = call_api("/api/progress", method="POST", data=data)
    
    if error:
        st.error(f"❌ Failed to report blocker: {error}")
        return False
    
    st.error(f"🚫 Blocker reported for Step {step_number}")
    
    # Check for re-evaluation
    if result.get('should_reevaluate') and result.get('reevaluation'):
        st.warning("🔄 Re-evaluation triggered due to blocker!")
        st.session_state.reevaluation_data = result['reevaluation']
        st.session_state.show_reevaluation = True
    
    # Clear form state
    st.session_state[f'show_blocker_form_{step_number}'] = False
    st.rerun()

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
    """Display roadmap with step cards - with complete workflow"""
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
                
                # Action buttons based on status
                if status == "not_started":
                    if st.button(f"▶️ Start Step", key=f"start_{step_data['step_number']}", use_container_width=True):
                        st.session_state[f'step_action_{step_data["step_number"]}'] = 'in_progress'
                        st.rerun()
                
                elif status == "in_progress":
                    st.markdown("**What do you want to do?**")
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        if st.button("✅ Mark Done", key=f"complete_{step_data['step_number']}", use_container_width=True):
                            st.session_state[f'step_action_{step_data["step_number"]}'] = 'complete'
                            st.session_state[f'show_complete_form_{step_data["step_number"]}'] = True
                            st.rerun()
                    
                    with col_b:
                        if st.button("🚫 Report Issue", key=f"block_{step_data['step_number']}", use_container_width=True):
                            st.session_state[f'step_action_{step_data["step_number"]}'] = 'blocked'
                            st.session_state[f'show_blocker_form_{step_data["step_number"]}'] = True
                            st.rerun()
                    
                    # Completion form
                    if st.session_state.get(f'show_complete_form_{step_data["step_number"]}', False):
                        st.markdown("---")
                        with st.form(f"complete_form_{step_data['step_number']}"):
                            st.markdown(f"**Completing Step {step_data['step_number']}: {step_data['title']}**")
                            hours = st.number_input(
                                "How many hours did you spend on this step?", 
                                min_value=0.0, 
                                value=10.0,
                                key=f"hours_complete_{step_data['step_number']}"
                            )
                            
                            col_x, col_y = st.columns(2)
                            with col_x:
                                if st.form_submit_button("✅ Confirm Complete", use_container_width=True):
                                    complete_step_api(step_data['step_number'], hours)
                            with col_y:
                                if st.form_submit_button("Cancel", use_container_width=True):
                                    st.session_state[f'show_complete_form_{step_data["step_number"]}'] = False
                                    st.rerun()
                    
                    # Blocker form
                    if st.session_state.get(f'show_blocker_form_{step_data["step_number"]}', False):
                        st.markdown("---")
                        with st.form(f"blocker_form_{step_data['step_number']}"):
                            st.markdown(f"**Reporting Issue on Step {step_data['step_number']}: {step_data['title']}**")
                            reason = st.text_area(
                                "What's blocking you? Describe the issue:",
                                key=f"reason_{step_data['step_number']}",
                                height=100
                            )
                            hours = st.number_input(
                                "Hours spent before getting blocked", 
                                min_value=0.0, 
                                value=5.0,
                                key=f"hours_blocker_{step_data['step_number']}"
                            )
                            
                            col_x, col_y = st.columns(2)
                            with col_x:
                                if st.form_submit_button("🚫 Report Blocker", use_container_width=True):
                                    report_blocker_api(step_data['step_number'], reason, hours)
                            with col_y:
                                if st.form_submit_button("Cancel", use_container_width=True):
                                    st.session_state[f'show_blocker_form_{step_data["step_number"]}'] = False
                                    st.rerun()
                
                elif status == "completed":
                    st.success("✅ Completed")
                    if step_progress and step_progress.get('completed_at'):
                        st.caption(f"Completed: {step_progress['completed_at'][:10]}")
                
                elif status == "blocked":
                    st.error("🚫 Blocked")
                    if step_progress and step_progress.get('last_reported'):
                        st.caption(f"Blocked on: {step_progress['last_reported'][:10]}")
                    if st.button("🔄 Retry Step", key=f"retry_{step_data['step_number']}", use_container_width=True):
                        st.session_state[f'step_action_{step_data["step_number"]}'] = 'in_progress'
                        st.rerun()
            
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
    
    for blocker in blockers:
        with st.expander(f"Step {blocker['step_number']} - {blocker['reason'][:50]}...", expanded=True):
            st.markdown(f"**Reason:** {blocker['reason']}")
            st.markdown(f"**Attempts:** {blocker['attempts']}")
            st.markdown(f"**First Reported:** {blocker['first_reported'][:10]}")
            st.markdown(f"**Last Reported:** {blocker['last_reported'][:10]}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"✅ Mark Resolved", key=f"resolve_{blocker['id']}"):
                    # In real app: call API to resolve blocker
                    st.success("Blocker resolved!")
            
            with col2:
                if st.button(f"🔄 Update", key=f"update_{blocker['id']}"):
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
    """Show re-evaluation results and alternatives with working rerouting"""
    st.markdown('<p class="main-header">🔄 Path Re-evaluation</p>', unsafe_allow_html=True)
    
    reeval = st.session_state.reevaluation_data
    
    if not reeval:
        st.error("No re-evaluation data available")
        if st.button("← Back to Dashboard"):
            st.session_state.page = "dashboard"
            st.session_state.show_reevaluation = False
            st.rerun()
        return
    
    st.markdown("---")
    
    # Show triggers
    st.markdown("### ⚠️ Issues Detected")
    
    for trigger in reeval.get('triggers', []):
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
    
    st.markdown(f"### 💬 {reeval.get('message', 'Your path needs re-evaluation')}")
    
    st.markdown("---")
    
    # Show action
    action = reeval.get('action', 'continue')
    
    if action == "suggest_reroute":
        st.markdown("### 🎯 **Recommended Alternative Paths**")
        st.info("Based on your progress, these paths might be better suited for you:")
        
        alternatives = reeval.get('alternatives', [])
        
        if alternatives:
            for i, alt in enumerate(alternatives):
                with st.container():
                    col1, col2 = st.columns([2.5, 1.5])
                    
                    with col1:
                        st.markdown(f"""
                        <div class="alternative-card">
                            <h3>🎯 {alt['role']}</h3>
                            <p style="color: #666; font-size: 0.9rem;">Match Score: <strong>{alt.get('total_score', 0)*100:.0f}%</strong></p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown(f"**Why this is better:**")
                        st.markdown(alt.get('justification', 'No details available'))
                        
                        st.markdown("**Market Insights:**")
                        market = alt.get('market_data', {})
                        col_m1, col_m2, col_m3 = st.columns(3)
                        
                        with col_m1:
                            st.metric("Active Jobs", f"{market.get('total_jobs', 0):,}")
                        with col_m2:
                            st.metric("Entry Barrier", f"{market.get('entry_barrier', 0)*100:.0f}%")
                        with col_m3:
                            st.metric("Fresher Friendly", "Yes" if market.get('freshers_accepted') else "No")
                    
                    with col2:
                        if st.button(f"🔄 Switch to {alt['role']}", key=f"switch_{i}", type="primary", use_container_width=True):
                            switch_career_path(alt['role'], reeval['reevaluation_id'])
                    
                    # Roadmap preview
                    if alt.get('roadmap') and alt['roadmap'].get('roadmap'):
                        with st.expander(f"📋 View Roadmap for {alt['role']}"):
                            for step in alt['roadmap']['roadmap']:
                                st.markdown(f"**Step {step['step_number']}. {step['title']}** ({step['duration_weeks']} weeks)")
                                st.caption(step['description'][:150] + ("..." if len(step['description']) > 150 else ""))
                                if step.get('skills_covered'):
                                    st.caption(f"Skills: {', '.join(step['skills_covered'][:3])}")
                    
                    st.markdown("---")
        
        # Option to continue
        st.markdown("### 💪 Continue Current Path?")
        st.warning("⚠️ You can continue with your current path, but be aware of the challenges ahead.")
        
        if st.button("➡️ Continue Current Path", use_container_width=True, type="secondary"):
            st.session_state.page = "dashboard"
            st.session_state.show_reevaluation = False
            st.success("Continuing with current path. Good luck! 💪")
            st.rerun()
    
    else:  # action == "continue"
        st.markdown("### ✅ Keep Going!")
        st.success("Your current path looks good. Keep making progress!")
        
        if st.button("← Back to Dashboard", use_container_width=True):
            st.session_state.page = "dashboard"
            st.session_state.show_reevaluation = False
            st.rerun()

def switch_career_path(new_role, reevaluation_id):
    """Switch to a new career path"""
    with st.spinner(f"🔄 Switching to {new_role}..."):
        data = {
            "session_id": st.session_state.session_id,
            "reevaluation_id": reevaluation_id,
            "chosen_role": new_role,
            "reason": "better_fit"
        }
        
        result, error = call_api("/api/reroute", method="POST", data=data)
        
        if error:
            st.error(f"❌ Failed to switch: {error}")
            return
        
        st.success(f"✅ Successfully switched to {new_role}!")
        st.balloons()
        
        st.info(f"""
        **Your career path has been updated!**
        - New target role: **{new_role}**
        - Your previous progress is preserved
        - You have a fresh roadmap optimized for your current skills
        
        Let's start with the new path!
        """)
        
        st.session_state.page = "dashboard"
        st.session_state.show_reevaluation = False
        st.session_state.reevaluation_data = None
        
        st.rerun()

# ========== SIDEBAR ==========

with st.sidebar:
    st.markdown("### 🎓 Career Agent")
    
    if st.session_state.session_id:
        st.success(f"✅ Active Session")
        st.caption(f"ID: {st.session_state.session_id[:8]}...")
        
        # Navigation
        st.markdown("### 📍 Navigation")
        
        if st.button("📊 Dashboard", use_container_width=True, key="nav_dashboard"):
            st.session_state.page = "dashboard"
            st.session_state.show_reevaluation = False
            st.rerun()
        
        if st.session_state.reevaluation_data and st.session_state.get('show_reevaluation', False):
            if st.button("🔄 Re-evaluation", use_container_width=True, key="nav_reevaluation"):
                st.session_state.page = "reevaluation"
                st.rerun()
        
        st.markdown("---")
        
        if st.button("🏠 New Assessment", use_container_width=True, key="nav_home"):
            st.session_state.session_id = None
            st.session_state.page = "home"
            st.session_state.reevaluation_data = None
            st.session_state.show_reevaluation = False
            st.rerun()
    
    else:
        st.info("👤 No active session")
    
    st.markdown("---")
    
    st.markdown("### ⚙️ Settings")
    api_url = st.text_input("API URL", value=API_BASE, key="api_url_setting")
    if api_url != API_BASE:
        st.info("💡 Tip: Set API_BASE environment variable to change this")
    
    st.markdown("---")
    st.caption("Built with ❤️ using Streamlit + FastAPI")

# ========== MAIN APP ==========

def main():
    # Route to appropriate page
    if st.session_state.page == "home":
        home_page()
    elif st.session_state.page == "dashboard":
        if st.session_state.session_id:
            dashboard_page()
        else:
            st.error("❌ No active session. Please start a new assessment.")
            st.session_state.page = "home"
            st.rerun()
    elif st.session_state.page == "reevaluation":
        reevaluation_page()
    else:
        st.session_state.page = "home"
        st.rerun()

if __name__ == "__main__":
    main()