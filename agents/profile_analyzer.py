"""
Profile Analyzer Agent
Purpose: Extract and understand student capabilities
Uses: 🤖 LLM for parsing, 📊 Logic for categorization
"""

import json
from typing import Dict, List, Any, Optional
import re


class ProfileAnalyzer:
    """
    Analyzes student profiles to extract structured skill information
    """
    
    def __init__(self, llm_client, skills_taxonomy: Dict):
        """
        Initialize with LLM client and skills taxonomy
        
        Args:
            llm_client: LLM client (Groq/Ollama/Gemini)
            skills_taxonomy: Loaded skills_taxonomy.json data
        """
        self.llm = llm_client
        self.skills_taxonomy = skills_taxonomy
        
    def analyze_profile(self, 
                       skills_text: str = None,
                       resume_text: str = None,
                       education: str = None,
                       experience: str = None,
                       projects: List[str] = None) -> Dict[str, Any]:
        """
        Main entry point - analyze complete student profile
        
        Args:
            skills_text: Free-text description of skills
            resume_text: Full resume/CV text
            education: Education background
            experience: Work experience description
            projects: List of project descriptions
            
        Returns:
            Structured profile dict
        """
        
        # Extract skills using LLM
        extracted_skills = self._extract_skills_llm(
            skills_text=skills_text,
            resume_text=resume_text,
            projects=projects
        )
        
        # Categorize skills (rule-based)
        categorized_skills = self._categorize_skills(extracted_skills)
        
        # Assess proficiency levels (rule-based)
        proficiency_map = self._assess_proficiency(
            extracted_skills,
            projects or [],
            experience
        )
        
        # Calculate strength scores (rule-based)
        strength_scores = self._calculate_strength_scores(categorized_skills)
        
        # Determine experience level (rule-based)
        experience_level = self._determine_experience_level(
            education,
            experience,
            projects or []
        )
        
        # Identify strength and weakness areas (rule-based)
        strengths, weaknesses = self._identify_strength_weakness_areas(
            categorized_skills,
            strength_scores
        )
        
        # Assess learning capacity (rule-based heuristic)
        learning_capacity = self._assess_learning_capacity(
            projects or [],
            proficiency_map
        )
        
        return {
            "student_profile": {
                "technical_skills": categorized_skills,
                "proficiency_map": proficiency_map,
                "soft_skills": extracted_skills.get("soft_skills", []),
                "experience_level": experience_level,
                "strength_areas": strengths,
                "weakness_areas": weaknesses,
                "learning_capacity": learning_capacity,
                "education": education,
                "projects_count": len(projects) if projects else 0,
                "raw_extracted_skills": extracted_skills
            }
        }
    
    def _extract_skills_llm(self,
                           skills_text: str = None,
                           resume_text: str = None,
                           projects: List[str] = None) -> Dict[str, Any]:
        """
        🤖 LLM CALL: Extract structured skills from unstructured text
        """
        
        # Combine all available text
        combined_text = ""
        if skills_text:
            combined_text += f"Skills: {skills_text}\n\n"
        if resume_text:
            combined_text += f"Resume: {resume_text}\n\n"
        if projects:
            combined_text += f"Projects: {json.dumps(projects)}\n\n"
        
        if not combined_text.strip():
            return {
                "programming_languages": [],
                "frameworks": [],
                "libraries": [],
                "tools": [],
                "databases": [],
                "domains": [],
                "soft_skills": [],
                "proficiency_estimates": {}
            }
        
        # LLM Prompt
        prompt = f"""Extract skills from the following student information and output ONLY valid JSON.

STUDENT INFORMATION:
{combined_text}

Extract and categorize skills into:
- programming_languages (e.g., Python, Java, JavaScript)
- frameworks (e.g., React, Django, Flask)
- libraries (e.g., Pandas, NumPy, TensorFlow)
- tools (e.g., Git, Docker, VS Code)
- databases (e.g., SQL, MongoDB, PostgreSQL)
- domains (e.g., Web Development, Data Analysis, Machine Learning)
- soft_skills (e.g., Communication, Problem-solving, Teamwork)
- proficiency_estimates (estimate beginner/intermediate/advanced for each technical skill)

Output ONLY this JSON structure with NO additional text:
{{
  "programming_languages": ["Python"],
  "frameworks": ["Django"],
  "libraries": ["Pandas"],
  "tools": ["Git"],
  "databases": ["SQL"],
  "domains": ["Web Development"],
  "soft_skills": ["Problem-solving"],
  "proficiency_estimates": {{
    "Python": "intermediate",
    "Django": "beginner"
  }}
}}"""

        try:
            response = self.llm.generate(prompt)
            
            # Parse JSON response
            # Remove markdown code blocks if present
            cleaned_response = response.strip()
            if cleaned_response.startswith("```"):
                # Remove ```json and ``` markers
                cleaned_response = re.sub(r'^```(?:json)?\s*\n', '', cleaned_response)
                cleaned_response = re.sub(r'\n```\s*$', '', cleaned_response)
            
            extracted = json.loads(cleaned_response)
            return extracted
            
        except json.JSONDecodeError as e:
            print(f"LLM response parsing error: {e}")
            print(f"Raw response: {response}")
            # Return empty structure
            return {
                "programming_languages": [],
                "frameworks": [],
                "libraries": [],
                "tools": [],
                "databases": [],
                "domains": [],
                "soft_skills": [],
                "proficiency_estimates": {}
            }
    
    def _categorize_skills(self, extracted_skills: Dict) -> Dict[str, List[str]]:
        """
        📊 RULE-BASED: Categorize and normalize skills using taxonomy
        """
        categorized = {
            "programming": [],
            "web_development": [],
            "databases": [],
            "data_science": [],
            "devops": [],
            "ai_ml": [],
            "tools": [],
            "other": []
        }
        
        # Flatten all technical skills
        all_skills = []
        for key in ["programming_languages", "frameworks", "libraries", "tools", "databases"]:
            all_skills.extend(extracted_skills.get(key, []))
        
        # Normalize and categorize using taxonomy
        for skill in all_skills:
            normalized_skill = self._normalize_skill(skill)
            category = self._get_skill_category(normalized_skill)
            
            if category and category in categorized:
                if normalized_skill not in categorized[category]:
                    categorized[category].append(normalized_skill)
            else:
                if normalized_skill not in categorized["other"]:
                    categorized["other"].append(normalized_skill)
        
        # Remove empty categories
        return {k: v for k, v in categorized.items() if v}
    
    def _normalize_skill(self, skill: str) -> str:
        """
        📊 RULE-BASED: Normalize skill name using taxonomy
        """
        skill_lower = skill.lower().strip()
        
        # Check taxonomy for canonical name
        for skill_key, skill_data in self.skills_taxonomy.get("skills", {}).items():
            # Check if skill matches canonical name
            if skill_lower == skill_data.get("canonical_name", "").lower():
                return skill_data["canonical_name"]
            
            # Check aliases
            aliases = skill_data.get("aliases", [])
            if skill_lower in [alias.lower() for alias in aliases]:
                return skill_data["canonical_name"]
        
        # If not found in taxonomy, return original (title case)
        return skill.title()
    
    def _get_skill_category(self, skill: str) -> Optional[str]:
        """
        📊 RULE-BASED: Get category for a normalized skill
        """
        # Check in taxonomy
        for skill_key, skill_data in self.skills_taxonomy.get("skills", {}).items():
            if skill.lower() == skill_data.get("canonical_name", "").lower():
                category_map = {
                    "Programming Language": "programming",
                    "Web Development": "web_development",
                    "Database": "databases",
                    "Data & Analytics": "data_science",
                    "Cloud & DevOps": "devops",
                    "AI/ML": "ai_ml",
                    "Tools": "tools"
                }
                return category_map.get(skill_data.get("category"), "other")
        
        return None
    
    def _assess_proficiency(self,
                           extracted_skills: Dict,
                           projects: List[str],
                           experience: str = None) -> Dict[str, str]:
        """
        📊 RULE-BASED: Assess proficiency levels for each skill
        """
        proficiency_map = {}
        
        # Start with LLM estimates if available
        llm_estimates = extracted_skills.get("proficiency_estimates", {})
        proficiency_map.update(llm_estimates)
        
        # Adjust based on projects and experience (heuristics)
        project_count = len(projects)
        has_experience = experience and len(experience) > 50
        
        # Upgrade proficiency if multiple projects
        if project_count >= 3:
            for skill in proficiency_map:
                if proficiency_map[skill] == "beginner":
                    proficiency_map[skill] = "intermediate"
        
        # Upgrade if has work experience
        if has_experience:
            for skill in proficiency_map:
                if proficiency_map[skill] == "beginner":
                    proficiency_map[skill] = "intermediate"
                elif proficiency_map[skill] == "intermediate":
                    proficiency_map[skill] = "advanced"
        
        return proficiency_map
    
    def _calculate_strength_scores(self, categorized_skills: Dict) -> Dict[str, float]:
        """
        📊 RULE-BASED: Calculate strength score per category (0-1)
        """
        scores = {}
        
        for category, skills in categorized_skills.items():
            # Score based on number of skills in category
            skill_count = len(skills)
            
            # Get max possible skills in this category from taxonomy
            max_skills = self._get_max_skills_in_category(category)
            
            # Calculate score (normalized)
            if max_skills > 0:
                score = min(skill_count / max_skills, 1.0)
            else:
                score = min(skill_count / 5.0, 1.0)  # Default max 5
            
            scores[category] = round(score, 2)
        
        return scores
    
    def _get_max_skills_in_category(self, category: str) -> int:
        """
        📊 RULE-BASED: Get max expected skills in a category
        """
        # Estimate based on taxonomy
        category_map = {
            "programming": "Programming Languages",
            "web_development": "Web Development",
            "databases": "Data & Analytics",
            "data_science": "Data & Analytics",
            "devops": "Cloud & DevOps",
            "ai_ml": "AI/ML",
            "tools": "Tools"
        }
        
        taxonomy_category = category_map.get(category)
        if taxonomy_category:
            skills_in_category = self.skills_taxonomy.get("skill_categories", {}).get(taxonomy_category, [])
            return len(skills_in_category)
        
        return 5  # Default
    
    def _determine_experience_level(self,
                                    education: str = None,
                                    experience: str = None,
                                    projects: List[str] = None) -> str:
        """
        📊 RULE-BASED: Determine overall experience level
        """
        score = 0
        
        # Education points
        if education:
            if "3rd year" in education.lower() or "4th year" in education.lower():
                score += 2
            elif "2nd year" in education.lower():
                score += 1
            elif any(degree in education.lower() for degree in ["ms", "master", "phd"]):
                score += 3
        
        # Experience points
        if experience and len(experience) > 100:
            if any(term in experience.lower() for term in ["years", "yr", "internship"]):
                score += 2
        
        # Projects points
        project_count = len(projects) if projects else 0
        if project_count >= 5:
            score += 3
        elif project_count >= 3:
            score += 2
        elif project_count >= 1:
            score += 1
        
        # Determine level
        if score >= 6:
            return "advanced"
        elif score >= 3:
            return "intermediate"
        else:
            return "beginner"
    
    def _identify_strength_weakness_areas(self,
                                         categorized_skills: Dict,
                                         strength_scores: Dict) -> tuple:
        """
        📊 RULE-BASED: Identify strength and weakness areas
        """
        strengths = []
        weaknesses = []
        
        # Sort categories by score
        sorted_categories = sorted(strength_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Top 2 are strengths (if score >= 0.5)
        for category, score in sorted_categories[:2]:
            if score >= 0.5:
                strengths.append(category.replace("_", " ").title())
        
        # Bottom categories with score < 0.3 are weaknesses
        common_categories = ["programming", "databases", "web_development", "data_science"]
        for category in common_categories:
            if category not in strength_scores or strength_scores[category] < 0.3:
                weakness_name = category.replace("_", " ").title()
                if weakness_name not in strengths:
                    weaknesses.append(weakness_name)
        
        return strengths, weaknesses
    
    def _assess_learning_capacity(self,
                                  projects: List[str],
                                  proficiency_map: Dict) -> str:
        """
        📊 RULE-BASED: Assess learning capacity (heuristic)
        """
        # Based on project complexity and proficiency diversity
        project_count = len(projects)
        skill_count = len(proficiency_map)
        
        # Count advanced skills
        advanced_count = sum(1 for level in proficiency_map.values() if level == "advanced")
        
        score = 0
        
        if project_count >= 5:
            score += 2
        elif project_count >= 3:
            score += 1
        
        if skill_count >= 10:
            score += 2
        elif skill_count >= 5:
            score += 1
        
        if advanced_count >= 3:
            score += 2
        elif advanced_count >= 1:
            score += 1
        
        if score >= 4:
            return "high"
        elif score >= 2:
            return "medium"
        else:
            return "low"
    
    def get_skill_vector(self, profile: Dict) -> Dict[str, float]:
        """
        📊 RULE-BASED: Create skill vector representation for matching
        """
        vector = {}
        
        technical_skills = profile["student_profile"]["technical_skills"]
        proficiency_map = profile["student_profile"]["proficiency_map"]
        
        # Create vector with proficiency weights
        proficiency_weights = {
            "beginner": 0.33,
            "intermediate": 0.66,
            "advanced": 1.0
        }
        
        for category, skills in technical_skills.items():
            for skill in skills:
                # Get proficiency weight
                proficiency = proficiency_map.get(skill, "beginner")
                weight = proficiency_weights.get(proficiency, 0.33)
                
                vector[skill.lower()] = weight
        
        return vector