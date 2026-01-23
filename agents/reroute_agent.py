"""
Reroute Agent
Purpose: Find best alternative careers based on market + student fit
Uses: 📊 Logic for scoring + 🤖 LLM for justification
"""

import json
from typing import Dict, List, Any, Optional
import re


class RerouteAgent:
    """
    Finds optimal alternative career paths when original goal is not feasible
    """
    
    def __init__(self, 
                 llm_client,
                 job_market_data: Dict,
                 career_paths_data: Dict,
                 skills_taxonomy: Dict):
        """
        Initialize with LLM and data
        
        Args:
            llm_client: LLM for generating justifications
            job_market_data: Market data for all roles
            career_paths_data: Career progression data
            skills_taxonomy: Skills taxonomy
        """
        self.llm = llm_client
        self.market_data = job_market_data
        self.career_paths = career_paths_data
        self.skills_taxonomy = skills_taxonomy
    
    def find_alternatives(self,
                         student_profile: Dict,
                         failed_role: str,
                         failed_market_analysis: Dict,
                         top_n: int = 3) -> Dict[str, Any]:
        """
        Find best alternative careers
        
        Args:
            student_profile: Student's profile
            failed_role: Original target role that wasn't feasible
            failed_market_analysis: Market analysis of failed role
            top_n: Number of alternatives to return
            
        Returns:
            Top alternative roles with justifications
        """
        
        # Get student skills
        student_skills = self._extract_student_skills(student_profile)
        
        # Score all possible alternative roles (rule-based)
        scored_alternatives = self._score_all_roles(
            student_skills=student_skills,
            failed_role=failed_role,
            student_profile=student_profile
        )
        
        # Get top N alternatives
        top_alternatives = scored_alternatives[:top_n]
        
        # Generate justifications for each (LLM)
        alternatives_with_justifications = []
        for alt in top_alternatives:
            justification = self._generate_justification_llm(
                original_role=failed_role,
                alternative_role=alt["role"],
                original_analysis=failed_market_analysis,
                alternative_analysis=alt["market_analysis"],
                score_breakdown=alt["breakdown"],
                student_profile=student_profile
            )
            
            alt["justification"] = justification
            alternatives_with_justifications.append(alt)
        
        return {
            "reroute_recommendations": {
                "original_role": failed_role,
                "alternatives": alternatives_with_justifications,
                "total_alternatives_evaluated": len(scored_alternatives)
            }
        }
    
    def _extract_student_skills(self, student_profile: Dict) -> List[str]:
        """
        📊 RULE-BASED: Extract flattened list of skills
        """
        technical_skills = student_profile.get("technical_skills", {})
        
        all_skills = []
        for category, skills in technical_skills.items():
            all_skills.extend(skills)
        
        return all_skills
    
    def _score_all_roles(self,
                        student_skills: List[str],
                        failed_role: str,
                        student_profile: Dict) -> List[Dict[str, Any]]:
        """
        📊 RULE-BASED: Score all roles as alternatives
        """
        roles = self.market_data.get("roles", {})
        scored_roles = []
        
        for role_name, role_data in roles.items():
            # Skip the failed role
            if role_name.lower() == failed_role.lower():
                continue
            
            # Calculate multi-criteria score
            score_breakdown = self._calculate_role_score(
                role_name=role_name,
                role_data=role_data,
                student_skills=student_skills,
                failed_role=failed_role,
                student_profile=student_profile
            )
            
            # Get market analysis for this role
            market_analysis = self._get_market_summary(role_data)
            
            scored_roles.append({
                "role": role_name,
                "total_score": score_breakdown["total_score"],
                "breakdown": score_breakdown,
                "market_analysis": market_analysis
            })
        
        # Sort by total score (descending)
        scored_roles.sort(key=lambda x: x["total_score"], reverse=True)
        
        return scored_roles
    
    def _calculate_role_score(self,
                             role_name: str,
                             role_data: Dict,
                             student_skills: List[str],
                             failed_role: str,
                             student_profile: Dict) -> Dict[str, float]:
        """
        📊 RULE-BASED: Calculate multi-criteria score for a role
        
        Criteria:
        1. Skill overlap (35%)
        2. Market demand (30%)
        3. Career progression potential (20%)
        4. Entry barrier (15%)
        """
        
        # Criterion 1: Skill Overlap
        skill_overlap = self._calculate_skill_overlap(
            student_skills,
            role_data.get("skills", {})
        )
        
        # Criterion 2: Market Demand
        market_data = role_data.get("market_data", {})
        total_jobs = market_data.get("total_jobs", 0)
        trend = market_data.get("trend", "stable")
        growth_rate = market_data.get("growth_rate_yoy", 0)
        
        market_score = self._calculate_market_demand_score(
            total_jobs, trend, growth_rate
        )
        
        # Criterion 3: Career Progression
        progression_score = self._calculate_progression_potential(
            role_name,
            failed_role
        )
        
        # Criterion 4: Entry Barrier (lower is better)
        entry_barrier = role_data.get("requirements", {}).get("entry_barrier", 0.5)
        experience_level = student_profile.get("experience_level", "beginner")
        barrier_score = self._calculate_barrier_score(entry_barrier, experience_level)
        
        # Weighted total score
        total_score = (
            skill_overlap * 0.35 +
            market_score * 0.30 +
            progression_score * 0.20 +
            barrier_score * 0.15
        )
        
        return {
            "total_score": round(total_score, 3),
            "skill_overlap": round(skill_overlap, 3),
            "market_demand": round(market_score, 3),
            "progression_potential": round(progression_score, 3),
            "ease_of_entry": round(barrier_score, 3)
        }
    
    def _calculate_skill_overlap(self,
                                student_skills: List[str],
                                role_skills: Dict) -> float:
        """
        📊 RULE-BASED: Calculate skill overlap score (0-1)
        """
        must_have = role_skills.get("must_have", [])
        
        # Extract skill names
        required_skills = []
        for skill in must_have:
            if isinstance(skill, dict):
                required_skills.append(skill.get("name", ""))
            else:
                required_skills.append(skill)
        
        if not required_skills:
            return 0.0
        
        # Normalize skills
        student_normalized = [self._normalize_skill(s) for s in student_skills]
        required_normalized = [self._normalize_skill(s) for s in required_skills]
        
        # Count matches
        matches = 0
        for req_skill in required_normalized:
            if any(self._skills_match(req_skill, st_skill) for st_skill in student_normalized):
                matches += 1
        
        overlap = matches / len(required_skills)
        return overlap
    
    def _normalize_skill(self, skill: str) -> str:
        """
        📊 RULE-BASED: Normalize skill name
        """
        skill_lower = skill.lower().strip()
        
        for skill_key, skill_data in self.skills_taxonomy.get("skills", {}).items():
            canonical = skill_data.get("canonical_name", "").lower()
            if skill_lower == canonical:
                return skill_data["canonical_name"]
            
            aliases = skill_data.get("aliases", [])
            if skill_lower in [a.lower() for a in aliases]:
                return skill_data["canonical_name"]
        
        return skill.title()
    
    def _skills_match(self, skill1: str, skill2: str) -> bool:
        """
        📊 RULE-BASED: Check if two skills match
        """
        s1 = skill1.lower()
        s2 = skill2.lower()
        
        if s1 == s2:
            return True
        
        if s1 in s2 or s2 in s1:
            return True
        
        return False
    
    def _calculate_market_demand_score(self,
                                      job_count: int,
                                      trend: str,
                                      growth_rate: float) -> float:
        """
        📊 RULE-BASED: Calculate normalized market demand score (0-1)
        """
        # Base score from job count
        base = min(job_count / 5000, 1.0)
        
        # Trend multiplier
        trend_multipliers = {
            "growing": 1.2,
            "stable": 1.0,
            "declining": 0.8
        }
        multiplier = trend_multipliers.get(trend, 1.0)
        
        # Growth bonus
        growth_bonus = min(growth_rate / 100, 0.2)
        
        score = min((base * multiplier) + growth_bonus, 1.0)
        return score
    
    def _calculate_progression_potential(self,
                                        alternative_role: str,
                                        original_role: str) -> float:
        """
        📊 RULE-BASED: Calculate career progression potential (0-1)
        
        How likely can this alternative lead to original goal?
        """
        # Check career paths data
        career_graph = self.career_paths.get("career_graph", {})
        stepping_stones = self.career_paths.get("stepping_stones", {})
        
        # Check if alternative is a stepping stone to original
        if original_role in stepping_stones:
            stones = stepping_stones[original_role]
            for stone in stones:
                if stone.get("intermediate_role", "").lower() == alternative_role.lower():
                    if stone.get("recommended", False):
                        return 0.9
                    else:
                        return 0.7
        
        # Check if there's a path in career graph
        if alternative_role in career_graph:
            next_roles = career_graph[alternative_role].get("typical_next_roles", [])
            for next_role in next_roles:
                if isinstance(next_role, dict):
                    if next_role.get("role", "").lower() == original_role.lower():
                        return next_role.get("transition_probability", 0.5)
        
        # Check skill similarity
        alt_data = self.market_data.get("roles", {}).get(alternative_role, {})
        orig_data = self.market_data.get("roles", {}).get(original_role, {})
        
        if alt_data and orig_data:
            alt_skills = set([
                s.get("name", "") if isinstance(s, dict) else s
                for s in alt_data.get("skills", {}).get("must_have", [])
            ])
            orig_skills = set([
                s.get("name", "") if isinstance(s, dict) else s
                for s in orig_data.get("skills", {}).get("must_have", [])
            ])
            
            if alt_skills and orig_skills:
                overlap = len(alt_skills & orig_skills) / len(orig_skills)
                return overlap * 0.6  # Max 0.6 from skill similarity
        
        # Default: some potential exists
        return 0.3
    
    def _calculate_barrier_score(self,
                                 entry_barrier: float,
                                 experience_level: str) -> float:
        """
        📊 RULE-BASED: Calculate barrier score (lower barrier = higher score)
        """
        experience_map = {
            "beginner": 0.2,
            "intermediate": 0.5,
            "advanced": 0.9
        }
        
        student_level = experience_map.get(experience_level, 0.2)
        
        # If barrier is low and student is beginner = good match (high score)
        # If barrier is high and student is beginner = bad match (low score)
        
        if entry_barrier <= student_level:
            return 1.0  # Easy entry
        else:
            gap = entry_barrier - student_level
            return max(1.0 - (gap * 1.5), 0.0)
    
    def _get_market_summary(self, role_data: Dict) -> Dict[str, Any]:
        """
        📊 RULE-BASED: Extract market summary for a role
        """
        market_data = role_data.get("market_data", {})
        salary_data = role_data.get("salary", {}).get("entry_level", {})
        requirements = role_data.get("requirements", {})
        
        return {
            "total_jobs": market_data.get("total_jobs", 0),
            "trend": market_data.get("trend", "unknown"),
            "growth_rate": market_data.get("growth_rate_yoy", 0),
            "salary_range": self._format_salary_range(salary_data),
            "entry_barrier": requirements.get("entry_barrier", 0.5),
            "freshers_accepted": requirements.get("freshers_accepted", False)
        }
    
    def _format_salary_range(self, salary_data: Dict) -> str:
        """
        📊 RULE-BASED: Format salary range
        """
        min_sal = salary_data.get("min", 0)
        max_sal = salary_data.get("max", 0)
        currency = salary_data.get("currency", "INR")
        
        if currency == "INR" and min_sal > 0:
            min_lpa = min_sal / 100000
            max_lpa = max_sal / 100000
            return f"₹{min_lpa:.1f}-{max_lpa:.1f} LPA"
        
        return "Not specified"
    
    def _generate_justification_llm(self,
                                   original_role: str,
                                   alternative_role: str,
                                   original_analysis: Dict,
                                   alternative_analysis: Dict,
                                   score_breakdown: Dict,
                                   student_profile: Dict) -> str:
        """
        🤖 LLM CALL: Generate data-driven justification for alternative
        """
        
        # Prepare comparison data
        orig_jobs = original_analysis.get("active_jobs", 0)
        alt_jobs = alternative_analysis.get("total_jobs", 0)
        
        orig_barrier = original_analysis.get("entry_barrier", 0.5)
        alt_barrier = alternative_analysis.get("entry_barrier", 0.5)
        
        skill_overlap = score_breakdown.get("skill_overlap", 0) * 100
        progression_potential = score_breakdown.get("progression_potential", 0)
        
        prompt = f"""Generate a brief, persuasive justification for why {alternative_role} is a better career path than {original_role} for this student.

ORIGINAL GOAL: {original_role}
- Active jobs: {orig_jobs}
- Entry barrier: {orig_barrier*100:.0f}%
- Student's skill match: {original_analysis.get('skill_match', 0)*100:.0f}%

ALTERNATIVE: {alternative_role}
- Active jobs: {alt_jobs}
- Entry barrier: {alt_barrier*100:.0f}%
- Student's skill match: {skill_overlap:.0f}%
- Salary: {alternative_analysis.get('salary_range', 'Not specified')}
- Trend: {alternative_analysis.get('trend', 'stable')}
- Can lead back to {original_role}: {progression_potential*100:.0f}% probability

STUDENT PROFILE:
- Experience level: {student_profile.get('experience_level', 'beginner')}
- Strength areas: {', '.join(student_profile.get('strength_areas', []))}

Write 3-4 sentences that:
1. Highlight key advantages (more jobs, easier entry, good pay)
2. Use specific numbers from the data
3. Show path back to original goal if possible
4. Sound encouraging and strategic (not like a downgrade)

Output ONLY the justification text, no headers or labels."""

        try:
            justification = self.llm.generate(prompt)
            return justification.strip()
        except Exception as e:
            # Fallback to template
            job_diff = ((alt_jobs - orig_jobs) / orig_jobs * 100) if orig_jobs > 0 else 0
            
            fallback = (
                f"{alternative_role} offers {alt_jobs:,} active jobs "
                f"({abs(job_diff):.0f}% {'more' if job_diff > 0 else 'fewer'} than {original_role}), "
                f"with a lower entry barrier ({alt_barrier*100:.0f}% vs {orig_barrier*100:.0f}%). "
                f"You already have {skill_overlap:.0f}% of required skills. "
            )
            
            if progression_potential > 0.5:
                fallback += f"This is a natural stepping stone to {original_role} later."
            
            return fallback
    
    def generate_comparison_table(self,
                                 original_role: str,
                                 alternatives: List[Dict]) -> Dict[str, Any]:
        """
        📊 RULE-BASED: Generate structured comparison table
        """
        original_data = self.market_data.get("roles", {}).get(original_role, {})
        original_summary = self._get_market_summary(original_data)
        
        comparison = {
            "original": {
                "role": original_role,
                **original_summary
            },
            "alternatives": []
        }
        
        for alt in alternatives[:3]:
            comparison["alternatives"].append({
                "role": alt["role"],
                "total_score": alt["total_score"],
                **alt["market_analysis"]
            })
        
        return comparison