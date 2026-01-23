"""
Roadmap Generator Agent
Purpose: Create actionable, market-aligned learning paths
Uses: 🤖 LLM for generation, 📊 Logic for formatting and prioritization
"""

import json
from typing import Dict, List, Any
import re


class RoadmapGenerator:
    """
    Generates personalized learning roadmaps using market data and LLM
    """
    
    def __init__(self, llm_client, learning_resources: Dict):
        """
        Initialize with LLM client and learning resources
        
        Args:
            llm_client: LLM client for roadmap generation
            learning_resources: Loaded learning_resources.json data
        """
        self.llm = llm_client
        self.resources = learning_resources
    
    def generate_roadmap(self,
                        target_role: str,
                        student_profile: Dict,
                        market_analysis: Dict,
                        duration_weeks: int = 12) -> Dict[str, Any]:
        """
        Generate complete learning roadmap
        
        Args:
            target_role: Target job role
            student_profile: Student's profile from ProfileAnalyzer
            market_analysis: Market analysis from MarketIntelligenceAgent
            duration_weeks: Available time in weeks
            
        Returns:
            Complete roadmap with steps, resources, timeline
        """
        
        # Identify and prioritize skill gaps (rule-based)
        prioritized_skills = self._prioritize_skills(
            market_analysis.get("missing_skills", []),
            market_analysis.get("required_skills", {}),
            student_profile
        )
        
        # Generate roadmap using LLM
        roadmap_steps = self._generate_roadmap_llm(
            target_role=target_role,
            prioritized_skills=prioritized_skills,
            current_skills=self._extract_current_skills(student_profile),
            duration_weeks=duration_weeks,
            market_context=market_analysis
        )
        
        # Enrich with resources (rule-based)
        enriched_roadmap = self._enrich_with_resources(roadmap_steps)
        
        # Add portfolio project (rule-based)
        final_roadmap = self._add_portfolio_project(
            enriched_roadmap,
            target_role,
            prioritized_skills
        )
        
        # Calculate totals (rule-based)
        total_weeks = sum(step.get("duration_weeks", 0) for step in final_roadmap)
        market_alignment = self._calculate_market_alignment(
            final_roadmap,
            market_analysis
        )
        
        return {
            "roadmap": final_roadmap,
            "total_duration_weeks": total_weeks,
            "total_duration_months": round(total_weeks / 4, 1),
            "market_alignment_score": market_alignment,
            "skills_covered": len(prioritized_skills),
            "target_role": target_role
        }
    
    def _prioritize_skills(self,
                          missing_skills: List[str],
                          required_skills: Dict,
                          student_profile: Dict) -> List[Dict[str, Any]]:
        """
        📊 RULE-BASED: Prioritize skills by demand and difficulty
        """
        must_have = required_skills.get("must_have", [])
        
        prioritized = []
        
        for skill in missing_skills:
            # Find in must_have to get metadata
            skill_data = None
            for item in must_have:
                if isinstance(item, dict):
                    if item.get("name") == skill:
                        skill_data = item
                        break
                elif item == skill:
                    skill_data = {"name": skill, "frequency": 0.5, "avg_learning_weeks": 4}
                    break
            
            if not skill_data:
                skill_data = {"name": skill, "frequency": 0.3, "avg_learning_weeks": 4}
            
            # Calculate priority score
            demand = skill_data.get("frequency", 0.5)
            difficulty = self._estimate_difficulty(skill)
            learning_weeks = skill_data.get("avg_learning_weeks", 4)
            
            # Priority = high demand + low difficulty (learn high-impact easy skills first)
            priority_score = (demand * 0.7) + ((1 - difficulty) * 0.3)
            
            prioritized.append({
                "skill": skill,
                "demand": demand,
                "difficulty": difficulty,
                "learning_weeks": learning_weeks,
                "priority_score": priority_score
            })
        
        # Sort by priority (high to low)
        prioritized.sort(key=lambda x: x["priority_score"], reverse=True)
        
        return prioritized
    
    def _estimate_difficulty(self, skill: str) -> float:
        """
        📊 RULE-BASED: Estimate skill difficulty (0-1)
        """
        skill_lower = skill.lower()
        
        # Hard skills
        hard_skills = ["machine learning", "deep learning", "system design", 
                      "algorithms", "data structures", "cloud architecture"]
        if any(hard in skill_lower for hard in hard_skills):
            return 0.9
        
        # Medium skills
        medium_skills = ["python", "java", "react", "node.js", "statistics"]
        if any(med in skill_lower for med in medium_skills):
            return 0.6
        
        # Easy skills
        easy_skills = ["git", "excel", "html", "css", "sql basics"]
        if any(easy in skill_lower for easy in easy_skills):
            return 0.3
        
        return 0.5  # Default medium
    
    def _extract_current_skills(self, student_profile: Dict) -> List[str]:
        """
        📊 RULE-BASED: Extract list of current skills
        """
        technical_skills = student_profile.get("technical_skills", {})
        
        all_skills = []
        for category, skills in technical_skills.items():
            all_skills.extend(skills)
        
        return all_skills
    
    def _generate_roadmap_llm(self,
                             target_role: str,
                             prioritized_skills: List[Dict],
                             current_skills: List[str],
                             duration_weeks: int,
                             market_context: Dict) -> List[Dict[str, Any]]:
        """
        🤖 LLM CALL: Generate step-by-step learning roadmap
        """
        
        # Prepare skills list for prompt
        skills_to_learn = [s["skill"] for s in prioritized_skills[:8]]  # Top 8 skills
        skills_with_weeks = {s["skill"]: s["learning_weeks"] for s in prioritized_skills[:8]}
        
        prompt = f"""Create a detailed learning roadmap to become a {target_role}.

CURRENT SKILLS: {', '.join(current_skills) if current_skills else 'None'}

SKILLS TO LEARN (in priority order):
{chr(10).join([f'{i+1}. {skill} ({skills_with_weeks[skill]} weeks)' for i, skill in enumerate(skills_to_learn)])}

CONSTRAINTS:
- Total duration: {duration_weeks} weeks
- Must include hands-on projects
- Each step needs clear success metrics

MARKET CONTEXT:
- Required by {market_context.get('active_jobs', 0)} jobs
- Entry barrier: {market_context.get('entry_barrier', 0)*100:.0f}%
- Demand score: {market_context.get('demand_score', 0)}/100

Generate a step-by-step roadmap. For each step, provide:
1. What to learn (specific and actionable)
2. Duration in weeks
3. Success metric (how to know you've mastered it)
4. Why this step matters (brief market justification)

Output ONLY valid JSON in this exact format:
{{
  "steps": [
    {{
      "step_number": 1,
      "title": "Master SQL Fundamentals",
      "description": "Learn SELECT, JOIN, WHERE, GROUP BY, and basic database design",
      "duration_weeks": 3,
      "success_metric": "Complete 50 SQL problems on HackerRank, build 2 database schemas",
      "why_important": "Required by 95% of Data Analyst roles",
      "skills_covered": ["SQL"]
    }}
  ]
}}

Create {min(len(skills_to_learn), 6)} learning steps. Ensure logical progression (fundamentals before advanced)."""

        try:
            response = self.llm.generate(prompt)
            
            # Clean and parse JSON
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r'^```(?:json)?\s*\n', '', cleaned)
                cleaned = re.sub(r'\n```\s*$', '', cleaned)
            
            parsed = json.loads(cleaned)
            steps = parsed.get("steps", [])
            
            return steps
            
        except json.JSONDecodeError as e:
            print(f"LLM roadmap parsing error: {e}")
            # Fallback to rule-based roadmap
            return self._generate_fallback_roadmap(prioritized_skills, duration_weeks)
    
    def _generate_fallback_roadmap(self,
                                   prioritized_skills: List[Dict],
                                   duration_weeks: int) -> List[Dict[str, Any]]:
        """
        📊 RULE-BASED: Generate basic roadmap if LLM fails
        """
        steps = []
        week_counter = 0
        
        for i, skill_obj in enumerate(prioritized_skills[:6]):
            skill = skill_obj["skill"]
            weeks = min(skill_obj["learning_weeks"], duration_weeks - week_counter)
            
            if weeks <= 0:
                break
            
            steps.append({
                "step_number": i + 1,
                "title": f"Learn {skill}",
                "description": f"Master {skill} through online courses and practice",
                "duration_weeks": weeks,
                "success_metric": f"Complete {weeks * 2} practice exercises in {skill}",
                "why_important": f"Required skill for target role",
                "skills_covered": [skill]
            })
            
            week_counter += weeks
        
        return steps
    
    def _enrich_with_resources(self, roadmap_steps: List[Dict]) -> List[Dict[str, Any]]:
        """
        📊 RULE-BASED: Add learning resources to each step
        """
        enriched = []
        
        for step in roadmap_steps:
            skills_covered = step.get("skills_covered", [])
            
            # Find resources for these skills
            resources = []
            for skill in skills_covered:
                skill_resources = self._find_resources_for_skill(skill)
                resources.extend(skill_resources[:2])  # Top 2 per skill
            
            # Remove duplicates
            unique_resources = []
            seen_urls = set()
            for res in resources:
                url = res.get("url", "")
                if url not in seen_urls:
                    unique_resources.append(res)
                    seen_urls.add(url)
            
            step["resources"] = unique_resources[:3]  # Max 3 resources per step
            enriched.append(step)
        
        return enriched
    
    def _find_resources_for_skill(self, skill: str) -> List[Dict[str, Any]]:
        """
        📊 RULE-BASED: Find learning resources for a skill
        """
        skill_lower = skill.lower()
        
        # Check exact match
        if skill in self.resources.get("resources", {}):
            return self.resources["resources"][skill]
        
        # Check case-insensitive match
        for resource_key, resource_list in self.resources.get("resources", {}).items():
            if resource_key.lower() == skill_lower:
                return resource_list
        
        # Check partial match
        for resource_key, resource_list in self.resources.get("resources", {}).items():
            if skill_lower in resource_key.lower() or resource_key.lower() in skill_lower:
                return resource_list
        
        # Return empty if not found
        return []
    
    def _add_portfolio_project(self,
                              roadmap: List[Dict],
                              target_role: str,
                              skills: List[Dict]) -> List[Dict[str, Any]]:
        """
        📊 RULE-BASED: Add portfolio project as final step
        """
        # Find relevant project ideas
        project_ideas = self.resources.get("project_ideas", {}).get(target_role, [])
        
        if project_ideas:
            project = project_ideas[0]  # Take first project
            portfolio_step = {
                "step_number": len(roadmap) + 1,
                "title": f"Build Portfolio Project: {project.get('title', 'Capstone Project')}",
                "description": project.get("description", "Build a comprehensive project showcasing all learned skills"),
                "duration_weeks": 2,
                "success_metric": "Complete project, deploy to GitHub, write documentation",
                "why_important": "Portfolio projects are mentioned in 94% of job postings",
                "skills_covered": [s["skill"] for s in skills[:5]],
                "resources": [
                    {
                        "title": "GitHub Repository Guide",
                        "url": "https://guides.github.com/",
                        "type": "documentation"
                    }
                ],
                "project_details": project
            }
        else:
            # Generic portfolio project
            portfolio_step = {
                "step_number": len(roadmap) + 1,
                "title": "Build Portfolio Project",
                "description": f"Create a comprehensive {target_role} project showcasing your skills",
                "duration_weeks": 2,
                "success_metric": "Deploy project, add to GitHub, prepare case study",
                "why_important": "Demonstrates practical skills to employers",
                "skills_covered": [s["skill"] for s in skills[:5]],
                "resources": []
            }
        
        roadmap.append(portfolio_step)
        return roadmap
    
    def _calculate_market_alignment(self,
                                   roadmap: List[Dict],
                                   market_analysis: Dict) -> float:
        """
        📊 RULE-BASED: Calculate how well roadmap aligns with market needs
        """
        # Get all skills covered in roadmap
        roadmap_skills = set()
        for step in roadmap:
            skills = step.get("skills_covered", [])
            roadmap_skills.update([s.lower() for s in skills])
        
        # Get required skills from market
        required = market_analysis.get("required_skills", {})
        must_have = required.get("must_have", [])
        must_have_skills = set([
            (s.get("name") if isinstance(s, dict) else s).lower() 
            for s in must_have
        ])
        
        # Calculate overlap
        if len(must_have_skills) == 0:
            return 0.5
        
        overlap = len(roadmap_skills & must_have_skills)
        alignment = overlap / len(must_have_skills)
        
        return round(alignment, 2)
    
    def generate_quick_wins_roadmap(self,
                                    student_profile: Dict,
                                    market_analysis: Dict) -> List[Dict[str, Any]]:
        """
        📊 RULE-BASED: Generate "quick wins" - easy skills to learn first
        """
        missing_skills = market_analysis.get("missing_skills", [])
        
        # Find easy skills (low difficulty, high impact)
        easy_skills = []
        for skill in missing_skills:
            difficulty = self._estimate_difficulty(skill)
            if difficulty < 0.5:
                easy_skills.append({
                    "skill": skill,
                    "difficulty": difficulty,
                    "weeks": 2
                })
        
        # Create mini roadmap
        quick_wins = []
        for i, skill_obj in enumerate(easy_skills[:3]):
            quick_wins.append({
                "step_number": i + 1,
                "title": f"Quick Win: Learn {skill_obj['skill']}",
                "duration_weeks": skill_obj["weeks"],
                "difficulty": "easy",
                "impact": "immediate"
            })
        
        return quick_wins