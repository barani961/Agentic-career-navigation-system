"""
Progress Tracker & Re-Evaluation Agent
Purpose: Monitor progress and trigger market-based reroutes
Uses: 📊 Pure logic (state management, condition checking)
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict


class ProgressTracker:
    """
    Tracks student progress through learning roadmap and triggers re-evaluations
    All operations are rule-based (no LLM calls in this agent)
    """
    
    def __init__(self, market_intelligence_agent, reroute_agent):
        """
        Initialize progress tracker
        
        Args:
            market_intelligence_agent: For fetching latest market data
            reroute_agent: For finding alternatives if reroute needed
        """
        self.market_agent = market_intelligence_agent
        self.reroute_agent = reroute_agent
        
        # Student state storage
        self.student_states = {}  # session_id -> state
    
    def initialize_journey(self,
                          session_id: str,
                          student_profile: Dict,
                          roadmap: List[Dict],
                          target_role: str,
                          market_snapshot: Dict) -> Dict[str, Any]:
        """
        📊 RULE-BASED: Initialize tracking for a new learning journey
        """
        
        self.student_states[session_id] = {
            "session_id": session_id,
            "target_role": target_role,
            "roadmap": roadmap,
            "total_steps": len(roadmap),
            "current_step": 0,
            "completed_steps": [],
            "blocked_steps": [],
            "time_spent": {},  # step_id -> hours
            "start_date": datetime.now().isoformat(),
            "market_snapshot": market_snapshot,
            "student_profile": student_profile,
            "reroute_count": 0,
            "motivation_level": 1.0,  # 0-1 scale
            "last_activity": datetime.now().isoformat()
        }
        
        return {
            "status": "initialized",
            "session_id": session_id,
            "total_steps": len(roadmap),
            "estimated_completion_weeks": sum(s.get("duration_weeks", 0) for s in roadmap)
        }
    
    def record_step_completion(self,
                              session_id: str,
                              step_number: int,
                              time_spent_hours: float = None) -> Dict[str, Any]:
        """
        📊 RULE-BASED: Record completion of a roadmap step
        """
        
        if session_id not in self.student_states:
            return {"error": "Session not found"}
        
        state = self.student_states[session_id]
        
        # Validate step number
        if step_number < 1 or step_number > state["total_steps"]:
            return {"error": f"Invalid step number: {step_number}"}
        
        # Check if already completed
        if step_number in state["completed_steps"]:
            return {"status": "already_completed", "step": step_number}
        
        # Record completion
        state["completed_steps"].append(step_number)
        state["current_step"] = step_number + 1
        
        # Record time spent
        if time_spent_hours:
            state["time_spent"][str(step_number)] = time_spent_hours
        
        # Update last activity
        state["last_activity"] = datetime.now().isoformat()
        
        # Calculate progress
        progress_pct = len(state["completed_steps"]) / state["total_steps"] * 100
        
        # Check if should re-evaluate
        should_reevaluate = self._should_reevaluate(state)
        
        response = {
            "status": "completed",
            "step_number": step_number,
            "progress_percentage": round(progress_pct, 1),
            "completed_steps": len(state["completed_steps"]),
            "remaining_steps": state["total_steps"] - len(state["completed_steps"]),
            "should_reevaluate": should_reevaluate
        }
        
        # Trigger re-evaluation if needed
        if should_reevaluate:
            reevaluation = self.reevaluate_path(session_id)
            response["reevaluation"] = reevaluation
        
        return response
    
    def record_blocker(self,
                      session_id: str,
                      step_number: int,
                      reason: str,
                      attempts: int = 1) -> Dict[str, Any]:
        """
        📊 RULE-BASED: Record when student is blocked on a step
        """
        
        if session_id not in self.student_states:
            return {"error": "Session not found"}
        
        state = self.student_states[session_id]
        
        # Find if blocker already exists
        existing_blocker = None
        for blocker in state["blocked_steps"]:
            if blocker["step"] == step_number:
                existing_blocker = blocker
                break
        
        if existing_blocker:
            # Increment attempts
            existing_blocker["attempts"] += 1
            existing_blocker["last_reported"] = datetime.now().isoformat()
        else:
            # Add new blocker
            state["blocked_steps"].append({
                "step": step_number,
                "reason": reason,
                "attempts": attempts,
                "first_reported": datetime.now().isoformat(),
                "last_reported": datetime.now().isoformat()
            })
        
        # Update motivation (multiple blockers = lower motivation)
        blocker_count = len(state["blocked_steps"])
        state["motivation_level"] = max(1.0 - (blocker_count * 0.2), 0.1)
        
        # Check if should re-evaluate
        should_reevaluate = self._should_reevaluate(state)
        
        response = {
            "status": "blocker_recorded",
            "step_number": step_number,
            "total_blockers": blocker_count,
            "motivation_level": state["motivation_level"],
            "should_reevaluate": should_reevaluate
        }
        
        # Trigger re-evaluation if critical
        if blocker_count >= 2 or (existing_blocker and existing_blocker["attempts"] >= 3):
            reevaluation = self.reevaluate_path(session_id)
            response["reevaluation"] = reevaluation
            response["recommendation"] = "Consider alternative path"
        
        return response
    
    def _should_reevaluate(self, state: Dict) -> bool:
        """
        📊 RULE-BASED: Determine if re-evaluation is needed
        """
        
        # Trigger 1: Multiple blockers
        if len(state["blocked_steps"]) >= 2:
            return True
        
        # Trigger 2: Single blocker with many attempts
        for blocker in state["blocked_steps"]:
            if blocker["attempts"] >= 3:
                return True
        
        # Trigger 3: Every 3 completed steps
        if len(state["completed_steps"]) > 0 and len(state["completed_steps"]) % 3 == 0:
            return True
        
        # Trigger 4: Time significantly exceeds estimate
        total_time_spent = sum(state["time_spent"].values())
        completed_count = len(state["completed_steps"])
        
        if completed_count > 0:
            roadmap = state["roadmap"]
            expected_time = sum(
                step.get("duration_weeks", 0) * 40  # 40 hours per week
                for i, step in enumerate(roadmap)
                if (i + 1) in state["completed_steps"]
            )
            
            if expected_time > 0 and total_time_spent > expected_time * 1.5:
                return True
        
        # Trigger 5: Low motivation
        if state["motivation_level"] < 0.5:
            return True
        
        return False
    
    def reevaluate_path(self, session_id: str) -> Dict[str, Any]:
        """
        📊 RULE-BASED: Re-evaluate if current path is still optimal
        """
        
        if session_id not in self.student_states:
            return {"error": "Session not found"}
        
        state = self.student_states[session_id]
        
        # Get current market data
        target_role = state["target_role"]
        student_profile = state["student_profile"]
        
        # Update student profile with newly learned skills
        updated_profile = self._update_profile_with_learned_skills(state)
        
        # Get fresh market analysis
        current_skills = self._extract_current_skills(updated_profile)
        current_market_analysis = self.market_agent.analyze_role_market(
            target_role,
            current_skills
        ).get("market_analysis", {})
        
        # Compare with original snapshot
        original_market = state["market_snapshot"]
        market_shift = self._calculate_market_shift(original_market, current_market_analysis)
        
        # Detect re-route triggers
        reroute_triggers = []
        
        # Trigger 1: Student struggling
        if len(state["blocked_steps"]) >= 2:
            reroute_triggers.append({
                "type": "performance",
                "severity": "high",
                "reason": f"Blocked on {len(state['blocked_steps'])} steps",
                "details": state["blocked_steps"]
            })
        
        # Trigger 2: Market demand dropped
        if market_shift.get("demand_change_pct", 0) < -20:
            reroute_triggers.append({
                "type": "market_decline",
                "severity": "high",
                "reason": f"Job market decreased by {abs(market_shift['demand_change_pct']):.0f}%",
                "details": market_shift
            })
        
        # Trigger 3: Skills unlocked new opportunities
        skills_learned = self._get_skills_learned(state)
        if len(skills_learned) >= 3:
            newly_accessible = self._find_newly_accessible_careers(
                updated_profile,
                current_skills
            )
            
            if newly_accessible:
                reroute_triggers.append({
                    "type": "new_opportunities",
                    "severity": "low",
                    "reason": f"Your skills now qualify for {len(newly_accessible)} additional roles",
                    "details": newly_accessible
                })
        
        # Trigger 4: Progress is too slow
        if state["motivation_level"] < 0.5:
            reroute_triggers.append({
                "type": "slow_progress",
                "severity": "medium",
                "reason": "Progress is slower than expected",
                "motivation_level": state["motivation_level"]
            })
        
        # Make decision
        if reroute_triggers:
            # Get alternative recommendations
            alternatives = self.reroute_agent.find_alternatives(
                student_profile=updated_profile,
                failed_role=target_role,
                failed_market_analysis=current_market_analysis,
                top_n=3
            )
            
            return {
                "action": "suggest_reroute",
                "triggers": reroute_triggers,
                "current_market_analysis": current_market_analysis,
                "alternatives": alternatives.get("reroute_recommendations", {}).get("alternatives", []),
                "recommendation": self._generate_recommendation(reroute_triggers)
            }
        else:
            return {
                "action": "continue",
                "status": "on_track",
                "progress": len(state["completed_steps"]) / state["total_steps"] * 100,
                "message": "You're making good progress. Keep going!"
            }
    
    def _update_profile_with_learned_skills(self, state: Dict) -> Dict:
        """
        📊 RULE-BASED: Update profile with skills learned so far
        """
        profile = state["student_profile"].copy()
        
        # Get skills from completed steps
        learned_skills = self._get_skills_learned(state)
        
        # Add to technical skills
        if "technical_skills" not in profile:
            profile["technical_skills"] = {}
        
        if "learned" not in profile["technical_skills"]:
            profile["technical_skills"]["learned"] = []
        
        profile["technical_skills"]["learned"].extend(learned_skills)
        
        return profile
    
    def _get_skills_learned(self, state: Dict) -> List[str]:
        """
        📊 RULE-BASED: Extract skills from completed steps
        """
        roadmap = state["roadmap"]
        completed = state["completed_steps"]
        
        learned_skills = []
        for step_num in completed:
            if step_num - 1 < len(roadmap):
                step = roadmap[step_num - 1]
                skills = step.get("skills_covered", [])
                learned_skills.extend(skills)
        
        return list(set(learned_skills))  # Unique skills
    
    def _extract_current_skills(self, profile: Dict) -> List[str]:
        """
        📊 RULE-BASED: Extract all current skills from profile
        """
        technical_skills = profile.get("technical_skills", {})
        
        all_skills = []
        for category, skills in technical_skills.items():
            all_skills.extend(skills)
        
        return list(set(all_skills))
    
    def _calculate_market_shift(self,
                               original: Dict,
                               current: Dict) -> Dict[str, Any]:
        """
        📊 RULE-BASED: Calculate market changes
        """
        orig_jobs = original.get("active_jobs", 0)
        curr_jobs = current.get("active_jobs", 0)
        
        if orig_jobs > 0:
            demand_change_pct = ((curr_jobs - orig_jobs) / orig_jobs) * 100
        else:
            demand_change_pct = 0
        
        orig_demand_score = original.get("demand_score", 0)
        curr_demand_score = current.get("demand_score", 0)
        
        return {
            "demand_change_pct": round(demand_change_pct, 1),
            "original_jobs": orig_jobs,
            "current_jobs": curr_jobs,
            "original_demand_score": orig_demand_score,
            "current_demand_score": curr_demand_score,
            "trend_change": curr_demand_score - orig_demand_score
        }
    
    def _find_newly_accessible_careers(self,
                                      updated_profile: Dict,
                                      current_skills: List[str]) -> List[Dict]:
        """
        📊 RULE-BASED: Find roles that are now accessible with new skills
        """
        # Use market agent to find roles matching skills
        matching_roles = self.market_agent.get_roles_for_skills(
            current_skills,
            min_match=0.5
        )
        
        # Return roles with good match
        return matching_roles[:3]
    
    def _generate_recommendation(self, triggers: List[Dict]) -> str:
        """
        📊 RULE-BASED: Generate recommendation based on triggers
        """
        high_severity = [t for t in triggers if t["severity"] == "high"]
        
        if high_severity:
            if high_severity[0]["type"] == "performance":
                return "Consider switching to an easier role that better matches your current skills"
            elif high_severity[0]["type"] == "market_decline":
                return "Market conditions have changed - explore growing career fields"
        
        return "Review alternative paths that might be better suited to your progress"
    
    def get_progress_summary(self, session_id: str) -> Dict[str, Any]:
        """
        📊 RULE-BASED: Get comprehensive progress summary
        """
        
        if session_id not in self.student_states:
            return {"error": "Session not found"}
        
        state = self.student_states[session_id]
        
        # Calculate metrics
        total_steps = state["total_steps"]
        completed = len(state["completed_steps"])
        progress_pct = (completed / total_steps * 100) if total_steps > 0 else 0
        
        # Time metrics
        total_time = sum(state["time_spent"].values())
        expected_time = sum(
            step.get("duration_weeks", 0) * 40
            for i, step in enumerate(state["roadmap"])
            if (i + 1) in state["completed_steps"]
        )
        
        time_efficiency = (expected_time / total_time * 100) if total_time > 0 else 100
        
        return {
            "session_id": session_id,
            "target_role": state["target_role"],
            "progress": {
                "completed_steps": completed,
                "total_steps": total_steps,
                "progress_percentage": round(progress_pct, 1),
                "remaining_steps": total_steps - completed
            },
            "time": {
                "total_hours_spent": round(total_time, 1),
                "expected_hours": round(expected_time, 1),
                "efficiency_percentage": round(time_efficiency, 1)
            },
            "blockers": {
                "count": len(state["blocked_steps"]),
                "details": state["blocked_steps"]
            },
            "motivation_level": state["motivation_level"],
            "start_date": state["start_date"],
            "last_activity": state["last_activity"],
            "reroute_count": state["reroute_count"]
        }
    
    def get_next_step(self, session_id: str) -> Dict[str, Any]:
        """
        📊 RULE-BASED: Get next step to work on
        """
        
        if session_id not in self.student_states:
            return {"error": "Session not found"}
        
        state = self.student_states[session_id]
        current_step_num = state["current_step"]
        
        if current_step_num > state["total_steps"]:
            return {
                "status": "completed",
                "message": "Congratulations! You've completed all steps."
            }
        
        # Get next step from roadmap
        next_step = state["roadmap"][current_step_num - 1]
        
        return {
            "status": "in_progress",
            "next_step": next_step,
            "step_number": current_step_num,
            "total_steps": state["total_steps"]
        }