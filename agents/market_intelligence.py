"""
Job Market Intelligence Agent
Purpose: Real-time market analysis for career viability
Uses: 📊 Pure logic (query database)
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime


class MarketIntelligenceAgent:
    """
    Analyzes job market data to assess career viability
    All operations are rule-based (no LLM calls)
    """
    
    def __init__(self, job_market_data: Dict, skills_taxonomy: Dict):
        """
        Initialize with hardcoded market data
        
        Args:
            job_market_data: Loaded job_market.json data
            skills_taxonomy: Loaded skills_taxonomy.json data
        """
        self.market_data = job_market_data
        self.skills_taxonomy = skills_taxonomy
    
    def analyze_role_market(self, 
                           role_name: str,
                           student_skills: List[str]) -> Dict[str, Any]:
        """
        Complete market analysis for a target role
        
        Args:
            role_name: Target job role (e.g., "Data Analyst")
            student_skills: List of student's current skills
            
        Returns:
            Comprehensive market analysis dict
        """
        
        # Get role data
        role_data = self._get_role_data(role_name)
        
        if not role_data:
            return {
                "error": f"Role '{role_name}' not found in market data",
                "available_roles": list(self.market_data.get("roles", {}).keys())
            }
        
        # Perform all analyses
        demand_analysis = self._analyze_demand(role_data)
        skill_gap_analysis = self._analyze_skill_gap(role_data, student_skills)
        salary_analysis = self._analyze_salary(role_data)
        competition_analysis = self._analyze_competition(role_data, student_skills)
        
        # Calculate time to job
        time_to_job = self._estimate_time_to_job(
            skill_gap_analysis["skill_match"],
            skill_gap_analysis["missing_skills_count"],
            role_data
        )
        
        return {
            "market_analysis": {
                "role": role_name,
                "demand_score": demand_analysis["demand_score"],
                "active_jobs": demand_analysis["active_jobs"],
                "trend": demand_analysis["trend"],
                "growth_rate": demand_analysis["growth_rate"],
                
                "avg_salary_range": salary_analysis["avg_salary_range"],
                "entry_salary_min": salary_analysis["entry_min"],
                "entry_salary_max": salary_analysis["entry_max"],
                
                "entry_barrier": competition_analysis["entry_barrier"],
                "entry_barrier_label": competition_analysis["barrier_label"],
                
                "required_skills": skill_gap_analysis["required_skills"],
                "skill_match": skill_gap_analysis["skill_match"],
                "missing_skills": skill_gap_analysis["missing_skills"],
                "missing_skills_count": skill_gap_analysis["missing_skills_count"],
                
                "competition_level": competition_analysis["competition_level"],
                "freshers_accepted": competition_analysis["freshers_accepted"],
                
                "estimated_time_to_job": time_to_job,
                
                "data_source": role_data.get("market_data", {}).get("data_source", "Unknown"),
                "last_updated": role_data.get("market_data", {}).get("last_updated", "Unknown")
            }
        }
    
    def _get_role_data(self, role_name: str) -> Optional[Dict]:
        """
        📊 RULE-BASED: Retrieve role data from market database
        """
        roles = self.market_data.get("roles", {})
        
        # Exact match first
        if role_name in roles:
            return roles[role_name]
        
        # Case-insensitive match
        for key, value in roles.items():
            if key.lower() == role_name.lower():
                return value
        
        # Partial match
        for key, value in roles.items():
            if role_name.lower() in key.lower() or key.lower() in role_name.lower():
                return value
        
        return None
    
    def _analyze_demand(self, role_data: Dict) -> Dict[str, Any]:
        """
        📊 RULE-BASED: Analyze market demand
        """
        market_data = role_data.get("market_data", {})
        
        total_jobs = market_data.get("total_jobs", 0)
        trend = market_data.get("trend", "unknown")
        growth_rate = market_data.get("growth_rate_yoy", 0)
        
        # Calculate demand score (0-100)
        # Based on: job count, trend, growth rate
        demand_score = self._calculate_demand_score(total_jobs, trend, growth_rate)
        
        return {
            "demand_score": demand_score,
            "active_jobs": total_jobs,
            "trend": trend,
            "growth_rate": growth_rate
        }
    
    def _calculate_demand_score(self, 
                                job_count: int,
                                trend: str,
                                growth_rate: float) -> int:
        """
        📊 RULE-BASED: Calculate demand score (0-100)
        """
        # Base score from job count (0-60 points)
        # Normalize: 5000+ jobs = 60 points
        base_score = min((job_count / 5000) * 60, 60)
        
        # Trend bonus (0-25 points)
        trend_scores = {
            "growing": 25,
            "stable": 15,
            "declining": 5,
            "unknown": 10
        }
        trend_score = trend_scores.get(trend, 10)
        
        # Growth rate bonus (0-15 points)
        # 20%+ = 15, 10-20% = 10, 0-10% = 5, negative = 0
        if growth_rate >= 20:
            growth_score = 15
        elif growth_rate >= 10:
            growth_score = 10
        elif growth_rate >= 0:
            growth_score = 5
        else:
            growth_score = 0
        
        total_score = int(base_score + trend_score + growth_score)
        return min(total_score, 100)
    
    def _analyze_skill_gap(self, 
                          role_data: Dict,
                          student_skills: List[str]) -> Dict[str, Any]:
        """
        📊 RULE-BASED: Analyze skill gaps
        """
        # Get required skills
        skills_data = role_data.get("skills", {})
        must_have = skills_data.get("must_have", [])
        nice_to_have = skills_data.get("nice_to_have", [])
        
        # Extract skill names
        must_have_skills = [s["name"] if isinstance(s, dict) else s for s in must_have]
        nice_to_have_skills = [s["name"] if isinstance(s, dict) else s for s in nice_to_have]
        
        # Normalize student skills
        normalized_student_skills = [self._normalize_skill(s) for s in student_skills]
        normalized_required = [self._normalize_skill(s) for s in must_have_skills]
        
        # Calculate matches
        matched_skills = []
        for req_skill in normalized_required:
            if any(self._skills_match(req_skill, student_skill) 
                   for student_skill in normalized_student_skills):
                matched_skills.append(req_skill)
        
        # Calculate missing skills
        missing_skills = [s for s in must_have_skills if s not in matched_skills]
        
        # Calculate match percentage
        if len(must_have_skills) > 0:
            skill_match = len(matched_skills) / len(must_have_skills)
        else:
            skill_match = 0.0
        
        return {
            "required_skills": {
                "must_have": must_have_skills,
                "nice_to_have": nice_to_have_skills
            },
            "skill_match": round(skill_match, 2),
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "missing_skills_count": len(missing_skills)
        }
    
    def _normalize_skill(self, skill: str) -> str:
        """
        📊 RULE-BASED: Normalize skill name
        """
        skill_lower = skill.lower().strip()
        
        # Check taxonomy
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
        📊 RULE-BASED: Check if two skills match (with fuzzy logic)
        """
        s1 = skill1.lower().strip()
        s2 = skill2.lower().strip()
        
        # Exact match
        if s1 == s2:
            return True
        
        # Contains match (e.g., "Python" matches "Python/Java")
        if s1 in s2 or s2 in s1:
            return True
        
        # Check if both map to same canonical skill
        norm1 = self._normalize_skill(skill1)
        norm2 = self._normalize_skill(skill2)
        if norm1.lower() == norm2.lower():
            return True
        
        return False
    
    def _analyze_salary(self, role_data: Dict) -> Dict[str, Any]:
        """
        📊 RULE-BASED: Analyze salary data
        """
        salary_data = role_data.get("salary", {})
        entry_level = salary_data.get("entry_level", {})
        mid_level = salary_data.get("mid_level", {})
        
        entry_min = entry_level.get("min", 0)
        entry_max = entry_level.get("max", 0)
        currency = entry_level.get("currency", "INR")
        
        # Format salary range
        if currency == "INR":
            # Convert to LPA (Lakhs Per Annum)
            entry_min_lpa = entry_min / 100000
            entry_max_lpa = entry_max / 100000
            avg_salary_range = f"₹{entry_min_lpa:.1f}-{entry_max_lpa:.1f} LPA"
        else:
            avg_salary_range = f"{currency} {entry_min:,}-{entry_max:,}"
        
        return {
            "avg_salary_range": avg_salary_range,
            "entry_min": entry_min,
            "entry_max": entry_max,
            "currency": currency,
            "mid_level_exists": bool(mid_level)
        }
    
    def _analyze_competition(self, 
                            role_data: Dict,
                            student_skills: List[str]) -> Dict[str, Any]:
        """
        📊 RULE-BASED: Analyze competition and entry barriers
        """
        requirements = role_data.get("requirements", {})
        
        entry_barrier = requirements.get("entry_barrier", 0.5)
        freshers_accepted = requirements.get("freshers_accepted", False)
        typical_experience = requirements.get("experience", "Unknown")
        
        # Determine barrier label
        if entry_barrier >= 0.8:
            barrier_label = "very_high"
            competition_level = "very_high"
        elif entry_barrier >= 0.6:
            barrier_label = "high"
            competition_level = "high"
        elif entry_barrier >= 0.4:
            barrier_label = "medium"
            competition_level = "medium"
        else:
            barrier_label = "low"
            competition_level = "low"
        
        return {
            "entry_barrier": entry_barrier,
            "barrier_label": barrier_label,
            "competition_level": competition_level,
            "freshers_accepted": freshers_accepted,
            "typical_experience": typical_experience
        }
    
    def _estimate_time_to_job(self,
                             skill_match: float,
                             missing_skills_count: int,
                             role_data: Dict) -> str:
        """
        📊 RULE-BASED: Estimate time to get job-ready
        """
        # Get learning time for missing skills
        skills_data = role_data.get("skills", {})
        must_have = skills_data.get("must_have", [])
        
        total_learning_weeks = 0
        for skill_obj in must_have:
            if isinstance(skill_obj, dict):
                total_learning_weeks += skill_obj.get("avg_learning_weeks", 4)
            else:
                total_learning_weeks += 4  # Default
        
        # Adjust based on current skill match
        remaining_learning_weeks = int(total_learning_weeks * (1 - skill_match))
        
        # Add buffer for projects and practice
        project_weeks = 2
        practice_weeks = 2
        
        total_weeks = remaining_learning_weeks + project_weeks + practice_weeks
        
        # Convert to months
        if total_weeks <= 4:
            return "1 month"
        elif total_weeks <= 8:
            return "2 months"
        elif total_weeks <= 12:
            return "3 months"
        elif total_weeks <= 24:
            return f"{total_weeks // 4} months"
        else:
            months = total_weeks // 4
            return f"{months}-{months + 3} months"
    
    def compare_roles(self, role1: str, role2: str) -> Dict[str, Any]:
        """
        📊 RULE-BASED: Compare two roles side-by-side
        """
        data1 = self._get_role_data(role1)
        data2 = self._get_role_data(role2)
        
        if not data1 or not data2:
            return {"error": "One or both roles not found"}
        
        return {
            "comparison": {
                role1: {
                    "jobs": data1.get("market_data", {}).get("total_jobs", 0),
                    "trend": data1.get("market_data", {}).get("trend", "unknown"),
                    "entry_barrier": data1.get("requirements", {}).get("entry_barrier", 0.5),
                    "salary_min": data1.get("salary", {}).get("entry_level", {}).get("min", 0)
                },
                role2: {
                    "jobs": data2.get("market_data", {}).get("total_jobs", 0),
                    "trend": data2.get("market_data", {}).get("trend", "unknown"),
                    "entry_barrier": data2.get("requirements", {}).get("entry_barrier", 0.5),
                    "salary_min": data2.get("salary", {}).get("entry_level", {}).get("min", 0)
                }
            }
        }
    
    def get_trending_roles(self, top_n: int = 5) -> List[Dict[str, Any]]:
        """
        📊 RULE-BASED: Get top trending roles
        """
        roles = self.market_data.get("roles", {})
        
        # Score each role by demand
        scored_roles = []
        for role_name, role_data in roles.items():
            market_data = role_data.get("market_data", {})
            demand_score = self._calculate_demand_score(
                market_data.get("total_jobs", 0),
                market_data.get("trend", "unknown"),
                market_data.get("growth_rate_yoy", 0)
            )
            
            scored_roles.append({
                "role": role_name,
                "demand_score": demand_score,
                "total_jobs": market_data.get("total_jobs", 0),
                "trend": market_data.get("trend", "unknown")
            })
        
        # Sort by demand score
        scored_roles.sort(key=lambda x: x["demand_score"], reverse=True)
        
        return scored_roles[:top_n]
    
    def get_roles_for_skills(self, student_skills: List[str], min_match: float = 0.3) -> List[Dict[str, Any]]:
        """
        📊 RULE-BASED: Find roles matching student's skills
        """
        roles = self.market_data.get("roles", {})
        
        matching_roles = []
        for role_name, role_data in roles.items():
            analysis = self._analyze_skill_gap(role_data, student_skills)
            skill_match = analysis["skill_match"]
            
            if skill_match >= min_match:
                matching_roles.append({
                    "role": role_name,
                    "skill_match": skill_match,
                    "matched_skills": analysis["matched_skills"],
                    "missing_skills_count": analysis["missing_skills_count"]
                })
        
        # Sort by skill match
        matching_roles.sort(key=lambda x: x["skill_match"], reverse=True)
        
        return matching_roles