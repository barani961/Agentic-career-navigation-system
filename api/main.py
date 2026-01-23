"""
FastAPI Backend for Career Agent System
Provides REST API endpoints for frontend integration
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import modules from root
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from database.db_manager import DatabaseManager
from llm.llm_client import LLMClient
from orchestrator import CareerAgentOrchestrator, load_data_files


# ========== PYDANTIC MODELS (Request/Response schemas) ==========

class AssessmentRequest(BaseModel):
    user_id: str
    desired_role: str
    skills_text: Optional[str] = None
    resume_text: Optional[str] = None
    education: Optional[str] = None
    experience: Optional[str] = None
    projects: Optional[List[str]] = None
    duration_weeks: int = 12

class ProgressUpdateRequest(BaseModel):
    session_id: str
    step_number: int
    status: str  # "completed", "blocked", or "in_progress"
    time_spent_hours: Optional[float] = None
    blocker_reason: Optional[str] = None

class RerouteRequest(BaseModel):
    session_id: str
    reevaluation_id: int
    chosen_role: str
    reason: str

class JourneySummaryResponse(BaseModel):
    journey: Dict
    progress: Dict
    steps: List[Dict]
    blockers: List[Dict]
    reevaluations: List[Dict]
    reroutes: List[Dict]
    skills_learned: List[Dict]


# ========== FASTAPI APP ==========

app = FastAPI(
    title="Career Agent API",
    description="AI-powered career guidance system",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== DEPENDENCIES ==========

def get_db():
    """Dependency: Get database manager"""
    db = DatabaseManager()
    try:
        yield db
    finally:
        db.close_all()

def get_orchestrator():
    """Dependency: Get career agent orchestrator"""
    llm = LLMClient()
    job_market, career_paths, skills_taxonomy, learning_resources = load_data_files()
    
    return CareerAgentOrchestrator(
        llm_client=llm,
        job_market_data=job_market,
        career_paths_data=career_paths,
        skills_taxonomy=skills_taxonomy,
        learning_resources=learning_resources
    )


# ========== API ENDPOINTS ==========

@app.get("/")
def root():
    """Health check"""
    return {
        "status": "ok",
        "service": "Career Agent API",
        "version": "1.0.0"
    }


@app.post("/api/assess")
def assess_career_goal(
    request: AssessmentRequest,
    db: DatabaseManager = Depends(get_db),
    orch: CareerAgentOrchestrator = Depends(get_orchestrator)
):
    """
    Initial career assessment
    
    Process:
    1. Analyze student profile
    2. Get market intelligence
    3. Evaluate feasibility
    4. Generate roadmap or suggest alternatives
    5. Save to database
    
    Returns: Complete assessment with roadmap
    """
    
    try:
        # Generate or use provided user_id
        user_id = request.user_id if '-' in request.user_id else str(uuid.uuid4())
        
        # Ensure user exists in database
        try:
            db.create_user(user_id, request.user_id)
        except:
            pass  # User might already exist
        
        # Run complete assessment
        result = orch.process_student_query(
            desired_role=request.desired_role,
            skills_text=request.skills_text,
            resume_text=request.resume_text,
            education=request.education,
            experience=request.experience,
            projects=request.projects,
            duration_weeks=request.duration_weeks
        )
        
        # Check for error response from orchestrator
        if result.get("status") == "error":
            raise HTTPException(
                status_code=400,
                detail=result.get("message"),
            )
        
        # Extract components
        verdict = result.get("verdict")
        target_role = result.get("target_role") or request.desired_role
        student_profile = result.get("profile")
        market_analysis = result.get("market_analysis")
        feasibility = result.get("feasibility")
        roadmap_data = result.get("roadmap")
        
        # Handle different verdicts
        if verdict == "FEASIBLE":
            roadmap = roadmap_data.get("roadmap", [])
        elif verdict == "NOT_FEASIBLE":
            # Use first alternative's roadmap
            alternatives = result.get("recommended_alternatives", [])
            if alternatives:
                target_role = alternatives[0]["role"]
                roadmap = alternatives[0].get("roadmap", {}).get("roadmap", [])
            else:
                raise HTTPException(status_code=400, detail="No suitable alternatives found")
        else:  # CHALLENGING
            # For CHALLENGING, we have direct_path in the response
            direct_path = result.get("direct_path", {})
            roadmap = direct_path.get("roadmap", {}).get("roadmap", []) if direct_path else []
        
        # Save to database
        session_id = db.create_journey(
            user_id=user_id,
            desired_role=request.desired_role,
            target_role=target_role,
            student_profile=student_profile,
            market_snapshot=market_analysis,
            roadmap=roadmap,
            feasibility_verdict=verdict
        )
        
        # Return result with session_id
        return {
            "session_id": session_id,
            "verdict": verdict,
            "target_role": target_role,
            "desired_role": request.desired_role,
            "assessment": result,
            "roadmap": roadmap,
            "message": _get_verdict_message(verdict, target_role, request.desired_role)
        }
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"ASSESS ERROR: {error_trace}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/progress")
def update_progress(
    request: ProgressUpdateRequest,
    db: DatabaseManager = Depends(get_db),
    orch: CareerAgentOrchestrator = Depends(get_orchestrator)
):
    """
    Update step progress
    
    Handles:
    - Step completion
    - Blocker reporting
    - Automatic re-evaluation triggers
    """
    
    try:
        # Handle status updates
        if request.status == "in_progress":
            # Update step status to in_progress
            db.update_step_status(
                session_id=request.session_id,
                step_number=request.step_number,
                status="in_progress"
            )
            
            summary = db.get_journey_summary(request.session_id)
            return {
                "success": True,
                "progress": summary["progress"]
            }
        
        elif request.status == "completed":
            # Record completion
            db.record_step_completion(
                session_id=request.session_id,
                step_number=request.step_number,
                time_spent_hours=request.time_spent_hours
            )
            
            # Add skills from this step
            journey = db.get_journey(request.session_id)
            roadmap = journey['roadmap']
            if request.step_number <= len(roadmap):
                step = roadmap[request.step_number - 1]
                skills_covered = step.get("skills_covered", [])
                for skill in skills_covered:
                    db.add_skill_learned(
                        session_id=request.session_id,
                        skill_name=skill,
                        proficiency_level="beginner",
                        learned_from_step=request.step_number
                    )
            
        elif request.status == "blocked":
            # Record blocker
            if not request.blocker_reason:
                raise HTTPException(status_code=400, detail="blocker_reason required for blocked status")
            
            # Generate alternate paths for this blocker
            alternate_paths = _generate_alternate_paths_for_blocker(
                db, orch, request.session_id, request.step_number, request.blocker_reason
            )
            
            blocker_id = db.record_blocker(
                session_id=request.session_id,
                step_number=request.step_number,
                reason=request.blocker_reason,
                category="skill_difficulty",
                alternate_paths=alternate_paths
            )
        
        # Check if re-evaluation needed
        should_reevaluate, triggers = _should_reevaluate(db, request.session_id)
        
        reevaluation_result = None
        if should_reevaluate:
            # Trigger re-evaluation
            reevaluation_result = _perform_reevaluation(
                db, orch, request.session_id, triggers
            )
        
        # Get updated summary
        summary = db.get_journey_summary(request.session_id)
        
        # Get blocker info if status was blocked
        blocker_info = None
        if request.status == "blocked":
            blocker = db.get_blocker_by_step(request.session_id, request.step_number)
            if blocker:
                blocker_info = {
                    "blocker_id": blocker['id'],
                    "alternate_paths": blocker.get('alternate_paths', [])
                }
        
        return {
            "success": True,
            "progress": summary["progress"],
            "should_reevaluate": should_reevaluate,
            "reevaluation": reevaluation_result,
            "blocker_info": blocker_info
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/reroute")
def accept_reroute(
    request: RerouteRequest,
    db: DatabaseManager = Depends(get_db),
    orch: CareerAgentOrchestrator = Depends(get_orchestrator)
):
    """
    Execute a path reroute
    
    When student accepts an alternative role suggested by re-evaluation
    """
    
    try:
        # Get journey
        journey = db.get_journey(request.session_id)
        if not journey:
            raise HTTPException(status_code=404, detail="Journey not found")
        
        current_role = journey['target_role']
        
        # Generate new roadmap for chosen role
        student_profile = journey['student_profile']
        
        # Get updated skills
        skills_learned = db.get_skills_learned(request.session_id)
        learned_skill_names = [s['skill_name'] for s in skills_learned]
        
        # Update profile with learned skills
        if "technical_skills" not in student_profile:
            student_profile["technical_skills"] = {}
        if "learned" not in student_profile["technical_skills"]:
            student_profile["technical_skills"]["learned"] = []
        student_profile["technical_skills"]["learned"].extend(learned_skill_names)
        
        # Get fresh market analysis
        all_skills = []
        for category, skills in student_profile.get("technical_skills", {}).items():
            all_skills.extend(skills)
        
        market_analysis = orch.market_intelligence.analyze_role_market(
            role_name=request.chosen_role,
            student_skills=all_skills
        )["market_analysis"]
        
        # Generate new roadmap
        roadmap_result = orch.roadmap_generator.generate_roadmap(
            target_role=request.chosen_role,
            student_profile=student_profile,
            market_analysis=market_analysis,
            duration_weeks=12
        )
        
        new_roadmap = roadmap_result["roadmap"]
        
        # Save reroute to database
        reroute_id = db.create_reroute(
            session_id=request.session_id,
            from_role=current_role,
            to_role=request.chosen_role,
            reason_type=request.reason,
            reason_details=f"Student chose to switch from {current_role} to {request.chosen_role}",
            new_roadmap=new_roadmap,
            new_market_snapshot=market_analysis
        )
        
        # Update re-evaluation with decision
        db.update_reevaluation_decision(
            reevaluation_id=request.reevaluation_id,
            student_decision="switch_role"
        )
        
        # Get updated journey
        updated_journey = db.get_journey_summary(request.session_id)
        
        return {
            "success": True,
            "reroute_id": reroute_id,
            "message": f"Successfully switched to {request.chosen_role}!",
            "new_target_role": request.chosen_role,
            "new_roadmap": new_roadmap,
            "journey": updated_journey
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/journey/{session_id}/summary")
def get_journey_summary(
    session_id: str,
    db: DatabaseManager = Depends(get_db)
):
    """
    Get complete journey summary
    
    Returns all data needed for dashboard view
    """
    
    try:
        summary = db.get_journey_summary(session_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/user/{user_id}/journeys")
def get_user_journeys(
    user_id: str,
    status: Optional[str] = None,
    db: DatabaseManager = Depends(get_db)
):
    """
    Get all journeys for a user
    
    Optional filter by status: active, paused, completed, abandoned
    """
    
    try:
        journeys = db.get_user_journeys(user_id, status)
        return {
            "user_id": user_id,
            "count": len(journeys),
            "journeys": journeys
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/journey/{session_id}/pause")
def pause_journey(
    session_id: str,
    db: DatabaseManager = Depends(get_db)
):
    """Pause a learning journey"""
    try:
        db.update_journey_status(session_id, "paused")
        return {"success": True, "status": "paused"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/journey/{session_id}/resume")
def resume_journey(
    session_id: str,
    db: DatabaseManager = Depends(get_db)
):
    """Resume a paused journey"""
    try:
        db.update_journey_status(session_id, "active")
        return {"success": True, "status": "active"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/blocker/{blocker_id}/alternate-paths")
def get_blocker_alternate_paths(
    blocker_id: int,
    db: DatabaseManager = Depends(get_db)
):
    """Get alternate paths for a specific blocker"""
    try:
        blocker = db.get_blocker(blocker_id)
        if not blocker:
            raise HTTPException(status_code=404, detail="Blocker not found")
        
        return {
            "blocker_id": blocker_id,
            "step_number": blocker['step_number'],
            "reason": blocker['reason'],
            "alternate_paths": blocker.get('alternate_paths', [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/journey/{session_id}/step/{step_number}/blocker")
def get_step_blocker(
    session_id: str,
    step_number: int,
    db: DatabaseManager = Depends(get_db)
):
    """Get blocker information for a specific step"""
    try:
        blocker = db.get_blocker_by_step(session_id, step_number)
        if not blocker:
            raise HTTPException(status_code=404, detail="No active blocker found for this step")
        
        return {
            "blocker": blocker,
            "alternate_paths": blocker.get('alternate_paths', [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/blocker/{blocker_id}/generate-alternates")
def generate_alternate_paths(
    blocker_id: int,
    db: DatabaseManager = Depends(get_db),
    orch: CareerAgentOrchestrator = Depends(get_orchestrator)
):
    """Generate alternate paths for a blocker"""
    try:
        blocker = db.get_blocker(blocker_id)
        if not blocker:
            raise HTTPException(status_code=404, detail="Blocker not found")
        
        # Generate alternate paths
        alternate_paths = _generate_alternate_paths_for_blocker(
            db, orch, blocker['session_id'], blocker['step_number'], blocker['reason']
        )
        
        # Update blocker with new paths
        db.update_blocker_alternate_paths(blocker_id, alternate_paths)
        
        return {
            "success": True,
            "blocker_id": blocker_id,
            "alternate_paths": alternate_paths
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== HELPER FUNCTIONS ==========

def _should_reevaluate(db: DatabaseManager, session_id: str) -> tuple:
    """
    Check if re-evaluation should be triggered
    
    Returns: (should_reevaluate, triggers)
    """
    triggers = []
    
    # Get journey data
    journey = db.get_journey(session_id)
    blockers = db.get_active_blockers(session_id)
    
    # Trigger 1: Multiple blockers
    if len(blockers) >= 2:
        triggers.append({
            "type": "performance",
            "severity": "high",
            "reason": f"Multiple blockers detected ({len(blockers)})",
            "details": {"blocker_count": len(blockers)}
        })
    
    # Trigger 2: Same step blocked 3+ times
    for blocker in blockers:
        if blocker['attempts'] >= 3:
            triggers.append({
                "type": "performance",
                "severity": "critical",
                "reason": f"Step {blocker['step_number']} blocked {blocker['attempts']} times",
                "details": {"step": blocker['step_number'], "attempts": blocker['attempts']}
            })
    
    # Trigger 3: Low motivation
    motivation = float(journey['motivation_level'])
    if motivation < 0.5:
        triggers.append({
            "type": "slow_progress",
            "severity": "medium",
            "reason": f"Motivation dropped to {motivation:.1f}",
            "details": {"motivation": motivation}
        })
    
    # Trigger 4: Every 3 completed steps (regular check)
    completed_count = len(journey['completed_steps'])
    if completed_count > 0 and completed_count % 3 == 0:
        # Check if already re-evaluated recently
        recent_reevals = db.get_reevaluations(session_id)
        if not recent_reevals or completed_count > len(recent_reevals) * 3:
            triggers.append({
                "type": "periodic_check",
                "severity": "low",
                "reason": "Regular progress check",
                "details": {"completed_steps": completed_count}
            })
    
    return len(triggers) > 0, triggers


def _perform_reevaluation(
    db: DatabaseManager,
    orch: CareerAgentOrchestrator,
    session_id: str,
    triggers: List[Dict]
) -> Dict:
    """
    Perform re-evaluation and find alternatives if needed
    """
    
    # Get journey
    journey = db.get_journey(session_id)
    target_role = journey['target_role']
    student_profile = journey['student_profile']
    original_market = journey['market_snapshot']
    
    # Get updated skills
    skills_learned = db.get_skills_learned(session_id)
    learned_skill_names = [s['skill_name'] for s in skills_learned]
    
    # Update profile
    if "technical_skills" not in student_profile:
        student_profile["technical_skills"] = {}
    if "learned" not in student_profile["technical_skills"]:
        student_profile["technical_skills"]["learned"] = []
    student_profile["technical_skills"]["learned"].extend(learned_skill_names)
    
    # Get current market data
    all_skills = []
    for category, skills in student_profile.get("technical_skills", {}).items():
        all_skills.extend(skills)
    
    current_market = orch.market_intelligence.analyze_role_market(
        role_name=target_role,
        student_skills=all_skills
    )["market_analysis"]
    
    # Compare markets
    market_comparison = {
        "original": {
            "demand_score": original_market.get("demand_score"),
            "active_jobs": original_market.get("active_jobs"),
            "skill_match": original_market.get("skill_match")
        },
        "current": {
            "demand_score": current_market.get("demand_score"),
            "active_jobs": current_market.get("active_jobs"),
            "skill_match": current_market.get("skill_match")
        }
    }
    
    # Determine action
    high_severity = any(t["severity"] in ["high", "critical"] for t in triggers)
    
    if high_severity:
        # Find alternatives
        alternatives_result = orch.reroute_agent.find_alternatives(
            student_profile=student_profile,
            failed_role=target_role,
            failed_market_analysis=current_market,
            top_n=3
        )
        
        alternatives = alternatives_result["reroute_recommendations"]["alternatives"]
        action_taken = "suggest_reroute"
    else:
        alternatives = []
        action_taken = "continue"
    
    # Save re-evaluation
    reevaluation_id = db.create_reevaluation(
        session_id=session_id,
        trigger_type=triggers[0]["type"],
        trigger_severity=triggers[0]["severity"],
        trigger_details={"triggers": triggers},
        action_taken=action_taken,
        market_comparison=market_comparison,
        alternatives_suggested=alternatives if alternatives else None
    )
    
    return {
        "reevaluation_id": reevaluation_id,
        "triggers": triggers,
        "action": action_taken,
        "market_comparison": market_comparison,
        "alternatives": alternatives,
        "message": _get_reevaluation_message(action_taken, len(triggers))
    }


def _get_verdict_message(verdict: str, target_role: str, desired_role: str) -> str:
    """Generate appropriate message based on verdict"""
    if verdict == "FEASIBLE":
        return f"Great news! {target_role} is a realistic goal for you. Let's get started!"
    elif verdict == "CHALLENGING":
        return f"{target_role} is achievable but will require significant effort. We also have some easier alternatives if you'd like."
    else:
        if target_role != desired_role:
            return f"{desired_role} isn't feasible right now, but {target_role} is a better fit and can lead you there!"
        return f"We found some better alternatives to {desired_role} based on your profile."


def _get_reevaluation_message(action: str, trigger_count: int) -> str:
    """Generate re-evaluation message"""
    if action == "suggest_reroute":
        return f"We've detected {trigger_count} concern(s) with your current path. Here are some alternatives that might work better."
    else:
        return "Regular progress check - you're doing well! Keep going."


def _generate_alternate_paths_for_blocker(
    db: DatabaseManager,
    orch: CareerAgentOrchestrator,
    session_id: str,
    step_number: int,
    blocker_reason: str
) -> List[Dict]:
    """
    Generate alternate paths/approaches when a step is blocked
    
    Returns:
        List of alternate path suggestions
    """
    try:
        # Get journey and current step
        journey = db.get_journey(session_id)
        roadmap = journey['roadmap']
        
        if step_number > len(roadmap):
            return []
        
        current_step = roadmap[step_number - 1]
        student_profile = journey['student_profile']
        
        # Get skills learned so far
        skills_learned = db.get_skills_learned(session_id)
        learned_skill_names = [s['skill_name'] for s in skills_learned]
        
        # Update profile with learned skills
        if "technical_skills" not in student_profile:
            student_profile["technical_skills"] = {}
        if "learned" not in student_profile["technical_skills"]:
            student_profile["technical_skills"]["learned"] = []
        student_profile["technical_skills"]["learned"].extend(learned_skill_names)
        
        # Generate alternate approaches using LLM
        # This could be enhanced to use the reroute agent or a dedicated alternate path generator
        alternate_paths = []
        
        # Approach 1: Suggest prerequisite steps or easier alternatives
        # Approach 2: Suggest different learning resources
        # Approach 3: Suggest breaking down the step into smaller parts
        
        # For now, create rule-based alternatives
        step_title = current_step.get('title', '')
        step_description = current_step.get('description', '')
        
        # Alternative 1: Break into smaller steps
        alternate_paths.append({
            "type": "breakdown",
            "title": f"Break down '{step_title}' into smaller steps",
            "description": f"Instead of tackling this step all at once, we can break it into 3-4 smaller, more manageable sub-steps.",
            "steps": [
                f"Review fundamentals related to {step_title}",
                f"Practice basic exercises for {step_title}",
                f"Build a small project using {step_title}",
                f"Complete the full {step_title} step"
            ],
            "estimated_weeks": current_step.get('duration_weeks', 2) + 1,
            "difficulty": "easier"
        })
        
        # Alternative 2: Prerequisite learning
        if blocker_reason.lower() in ['difficult', 'hard', 'complex', 'confusing', 'don\'t understand']:
            alternate_paths.append({
                "type": "prerequisites",
                "title": f"Learn prerequisites for '{step_title}'",
                "description": f"Before tackling this step, let's strengthen your foundation in related concepts.",
                "steps": [
                    "Review foundational concepts",
                    "Complete prerequisite tutorials",
                    "Practice with simpler examples",
                    "Return to the original step"
                ],
                "estimated_weeks": current_step.get('duration_weeks', 2),
                "difficulty": "easier"
            })
        
        # Alternative 3: Different learning approach
        alternate_paths.append({
            "type": "alternative_approach",
            "title": f"Try a different learning approach for '{step_title}'",
            "description": f"Sometimes a different teaching style or resource can make all the difference.",
            "steps": [
                "Try video tutorials instead of text",
                "Join a study group or community",
                "Find hands-on projects",
                "Get mentorship or tutoring"
            ],
            "estimated_weeks": current_step.get('duration_weeks', 2),
            "difficulty": "similar"
        })
        
        # Alternative 4: Skip and come back (if not critical)
        if step_number > 1:  # Don't suggest skipping the first step
            alternate_paths.append({
                "type": "skip_and_return",
                "title": f"Skip '{step_title}' temporarily",
                "description": f"You can move forward to the next steps and come back to this one later with more experience.",
                "steps": [
                    "Mark this step as 'skip for now'",
                    "Continue with next steps",
                    "Return to this step after gaining more experience"
                ],
                "estimated_weeks": 0,  # No additional time
                "difficulty": "easier",
                "warning": "Only skip if this step is not a prerequisite for future steps"
            })
        
        return alternate_paths
        
    except Exception as e:
        print(f"Error generating alternate paths: {e}")
        return []


# ========== RUN SERVER ==========

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)