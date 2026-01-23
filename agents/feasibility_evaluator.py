"""
Feasibility Evaluator Agent
Purpose: Decide if goal is realistic or needs rerouting
Uses: 📊 Logic for calculations + 🤖 LLM for explanation
"""

import json
from typing import Dict, List, Any
import re


class FeasibilityEvaluator:
    """
    Evaluates feasibility of career goals using multi-factor analysis
    """
    
    # Decision thresholds
    FEASIBLE_THRESHOLD = 0.65
    CHALLENGING_THRESHOLD = 0.45
    
    def __init__(self, llm_client):
        """
        Initialize with LLM client for explanations
        
        Args:
            llm_client: LLM client for generating natural language explanations
        """
        self.llm = llm_client
    
    def evaluate(self,
                 student_profile: Dict,
                 market_analysis: Dict,
                 desired_role: str) -> Dict[str, Any]:
        """
        Complete feasibility evaluation
        
        Args:
            student_profile: From ProfileAnalyzer
            market_analysis: From MarketIntelligenceAgent
            desired_role: Target role name
            
        Returns:
            Feasibility decision with detailed breakdown
        """
        
        # Extract key metrics
        skill_match = market_analysis.get("skill_match", 0.0)
        demand_score = market_analysis.get("demand_score", 0) / 100.0
        entry_barrier = market_analysis.get("entry_barrier", 0.5)
        experience_level = student_profile.get("experience_level", "beginner")
        learning_capacity = student_profile.get("learning_capacity", "medium")
        missing_skills_count = market_analysis.get("missing_skills_count", 0)
        
        # Calculate individual factor scores
        skill_score = self._calculate_skill_score(skill_match)
        market_score = self._calculate_market_score(demand_score)
        barrier_score = self._calculate_barrier_score(entry_barrier, experience_level)
        time_score = self._calculate_time_score(
            learning_capacity,
            missing_skills_count,
            market_analysis.get("required_skills", {})
        )
        
        # Calculate overall feasibility score (weighted)
        feasibility_score = (
            skill_score * 0.4 +
            market_score * 0.3 +
            barrier_score * 0.2 +
            time_score * 0.1
        )
        
        # Make decision
        decision = self._make_decision(feasibility_score)
        
        # Generate reasons (rule-based)
        reasons = self._generate_reasons(
            skill_score=skill_score,
            market_score=market_score,
            barrier_score=barrier_score,
            time_score=time_score,
            skill_match=skill_match,
            demand_score=demand_score * 100,
            entry_barrier=entry_barrier,
            experience_level=experience_level,
            missing_skills_count=missing_skills_count,
            market_analysis=market_analysis
        )
        
        # Generate natural language explanation (LLM)
        if decision["verdict"] != "FEASIBLE":
            explanation = self._generate_explanation_llm(
                desired_role=desired_role,
                decision=decision,
                reasons=reasons,
                market_analysis=market_analysis,
                student_profile=student_profile
            )
        else:
            explanation = f"Great news! {desired_role} is a feasible career goal for you."
        
        return {
            "feasibility_evaluation": {
                "verdict": decision["verdict"],
                "confidence": decision["confidence"],
                "action": decision["action"],
                "feasibility_score": round(feasibility_score, 2),
                
                "factor_scores": {
                    "skill_match": round(skill_score, 2),
                    "market_demand": round(market_score, 2),
                    "entry_barrier": round(barrier_score, 2),
                    "time_to_competency": round(time_score, 2)
                },
                
                "reasons": reasons,
                "explanation": explanation,
                
                "recommendation": decision.get("warning") or decision.get("action")
            }
        }
    
    def _calculate_skill_score(self, skill_match: float) -> float:
        """
        📊 RULE-BASED: Calculate skill match score (0-1)
        """
        # Skill match is already 0-1, but we can apply a curve
        # to penalize very low matches more heavily
        
        if skill_match >= 0.7:
            return 1.0
        elif skill_match >= 0.5:
            return 0.8
        elif skill_match >= 0.3:
            return 0.6
        elif skill_match >= 0.15:
            return 0.4
        else:
            return 0.2
    
    def _calculate_market_score(self, demand_score: float) -> float:
        """
        📊 RULE-BASED: Calculate market demand score (0-1)
        """
        # demand_score is already normalized 0-1 from demand_score/100
        
        if demand_score >= 0.8:
            return 1.0
        elif demand_score >= 0.6:
            return 0.85
        elif demand_score >= 0.4:
            return 0.65
        elif demand_score >= 0.2:
            return 0.45
        else:
            return 0.25
    
    def _calculate_barrier_score(self, entry_barrier: float, experience_level: str) -> float:
        """
        📊 RULE-BASED: Calculate barrier score based on mismatch
        
        Higher barrier + lower experience = lower score
        """
        experience_levels = {
            "beginner": 0.2,
            "intermediate": 0.5,
            "advanced": 0.9
        }
        
        student_level = experience_levels.get(experience_level, 0.2)
        
        # Calculate mismatch
        # If barrier is 0.8 and student is 0.2 = big mismatch = low score
        # If barrier is 0.3 and student is 0.5 = good match = high score
        
        if entry_barrier <= student_level:
            # Student exceeds requirement - excellent
            return 1.0
        else:
            # Calculate how far behind student is
            gap = entry_barrier - student_level
            
            if gap <= 0.2:
                return 0.8
            elif gap <= 0.4:
                return 0.6
            elif gap <= 0.6:
                return 0.4
            else:
                return 0.2
    
    def _calculate_time_score(self,
                             learning_capacity: str,
                             missing_skills_count: int,
                             required_skills: Dict) -> float:
        """
        📊 RULE-BASED: Calculate time feasibility score
        """
        # Estimate total learning time needed
        capacity_multipliers = {
            "high": 1.0,
            "medium": 1.3,
            "low": 1.6
        }
        
        multiplier = capacity_multipliers.get(learning_capacity, 1.3)
        
        # Estimate weeks needed (rough heuristic)
        base_weeks_per_skill = 4
        total_weeks = missing_skills_count * base_weeks_per_skill * multiplier
        
        # Score based on time
        if total_weeks <= 12:  # 3 months
            return 1.0
        elif total_weeks <= 24:  # 6 months
            return 0.8
        elif total_weeks <= 36:  # 9 months
            return 0.6
        elif total_weeks <= 48:  # 12 months
            return 0.4
        else:
            return 0.2
    
    def _make_decision(self, feasibility_score: float) -> Dict[str, str]:
        """
        📊 RULE-BASED: Make verdict based on thresholds
        """
        if feasibility_score >= self.FEASIBLE_THRESHOLD:
            return {
                "verdict": "FEASIBLE",
                "confidence": "high",
                "action": "generate_direct_roadmap"
            }
        elif feasibility_score >= self.CHALLENGING_THRESHOLD:
            return {
                "verdict": "CHALLENGING",
                "confidence": "medium",
                "action": "offer_choice",
                "warning": "High effort required - consider alternatives or commit to intensive learning"
            }
        else:
            return {
                "verdict": "NOT_FEASIBLE",
                "confidence": "high",
                "action": "suggest_reroute"
            }
    
    def _generate_reasons(self,
                         skill_score: float,
                         market_score: float,
                         barrier_score: float,
                         time_score: float,
                         skill_match: float,
                         demand_score: float,
                         entry_barrier: float,
                         experience_level: str,
                         missing_skills_count: int,
                         market_analysis: Dict) -> List[Dict[str, str]]:
        """
        📊 RULE-BASED: Generate structured reasons for infeasibility
        """
        reasons = []
        
        # Reason 1: Skill Gap
        if skill_score < 0.5:
            severity = "critical" if skill_score < 0.3 else "high"
            reasons.append({
                "type": "skill_gap",
                "severity": severity,
                "title": "Significant Skill Gap",
                "explanation": f"You currently have only {skill_match*100:.0f}% of the required skills. "
                              f"Missing {missing_skills_count} critical skills.",
                "impact": "Would require 6-12 months of intensive learning",
                "missing_skills": market_analysis.get("missing_skills", [])
            })
        
        # Reason 2: Market Demand
        if market_score < 0.5:
            severity = "critical" if market_score < 0.3 else "high"
            active_jobs = market_analysis.get("active_jobs", 0)
            reasons.append({
                "type": "low_market_demand",
                "severity": severity,
                "title": "Limited Market Opportunities",
                "explanation": f"Only {active_jobs} active job postings found. "
                              f"Market demand score: {demand_score:.0f}/100.",
                "impact": "Very competitive job market with limited openings"
            })
        
        # Reason 3: Entry Barrier
        if barrier_score < 0.5:
            severity = "critical" if barrier_score < 0.3 else "medium"
            reasons.append({
                "type": "high_entry_barrier",
                "severity": severity,
                "title": "High Entry Requirements",
                "explanation": f"This role has an entry barrier of {entry_barrier*100:.0f}%, "
                              f"but you're at {experience_level} level.",
                "impact": "Most positions require significant prior experience or advanced qualifications",
                "typical_requirements": market_analysis.get("requirements", {})
            })
        
        # Reason 4: Time Investment
        if time_score < 0.5:
            severity = "medium"
            reasons.append({
                "type": "long_learning_path",
                "severity": severity,
                "title": "Extended Learning Timeline",
                "explanation": f"Given {missing_skills_count} skills to learn, "
                              f"estimated time: {market_analysis.get('estimated_time_to_job', 'Unknown')}",
                "impact": "Requires sustained long-term commitment"
            })
        
        return reasons
    
    def _generate_explanation_llm(self,
                                  desired_role: str,
                                  decision: Dict,
                                  reasons: List[Dict],
                                  market_analysis: Dict,
                                  student_profile: Dict) -> str:
        """
        🤖 LLM CALL: Generate empathetic, natural explanation
        """
        
        # Prepare context for LLM
        reasons_text = "\n".join([
            f"- {r['title']}: {r['explanation']}"
            for r in reasons
        ])
        
        missing_skills = market_analysis.get("missing_skills", [])
        skill_match_pct = market_analysis.get("skill_match", 0) * 100
        
        prompt = f"""Generate a brief, empathetic explanation for why pursuing {desired_role} may not be the best immediate path.

VERDICT: {decision['verdict']}

KEY CHALLENGES:
{reasons_text}

STUDENT'S CURRENT SITUATION:
- Skill match: {skill_match_pct:.0f}%
- Missing skills: {', '.join(missing_skills[:5])}
- Experience level: {student_profile.get('experience_level', 'beginner')}

MARKET REALITY:
- Active jobs: {market_analysis.get('active_jobs', 0)}
- Entry barrier: {market_analysis.get('entry_barrier', 0)*100:.0f}%
- Estimated learning time: {market_analysis.get('estimated_time_to_job', 'Unknown')}

Write a SHORT (2-3 sentences) explanation that:
1. Acknowledges their goal
2. Explains the main challenge
3. Suggests there are better paths forward

Be empathetic but honest. Don't use bullet points. Output ONLY the explanation text."""

        try:
            explanation = self.llm.generate(prompt)
            return explanation.strip()
        except Exception as e:
            # Fallback to template
            return (f"While {desired_role} is an exciting career goal, the current job market "
                   f"and skill requirements present significant challenges. With only {skill_match_pct:.0f}% "
                   f"skill match and {market_analysis.get('active_jobs', 0)} active positions, "
                   f"there are more strategic paths to explore that align better with your current profile.")
    
    def calculate_success_probability(self,
                                     student_profile: Dict,
                                     market_analysis: Dict) -> float:
        """
        📊 RULE-BASED: Calculate probability of success (0-1)
        """
        skill_match = market_analysis.get("skill_match", 0.0)
        demand_score = market_analysis.get("demand_score", 0) / 100.0
        entry_barrier = market_analysis.get("entry_barrier", 0.5)
        
        # Simple probability model
        # P(success) = skill_match * market_demand * (1 - entry_barrier) * experience_factor
        
        experience_factors = {
            "beginner": 0.7,
            "intermediate": 0.85,
            "advanced": 1.0
        }
        
        exp_level = student_profile.get("experience_level", "beginner")
        exp_factor = experience_factors.get(exp_level, 0.7)
        
        probability = skill_match * demand_score * (1 - entry_barrier * 0.5) * exp_factor
        
        return round(probability, 2)