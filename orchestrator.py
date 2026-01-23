"""
Career Agent Orchestrator
Coordinates all agents to provide complete career guidance
"""

import json
from typing import Dict, List, Any, Optional
import uuid

from agents.profile_analyzer import ProfileAnalyzer
from agents.market_intelligence import MarketIntelligenceAgent
from agents.feasibility_evaluator import FeasibilityEvaluator
from agents.roadmap_generator import RoadmapGenerator
from agents.reroute_agent import RerouteAgent
from agents.progress_tracker import ProgressTracker
from llm.llm_client import LLMClient


class CareerAgentOrchestrator:
    """
    Main orchestrator that coordinates all career guidance agents
    """
    
    def __init__(self,
                 llm_client: LLMClient,
                 job_market_data: Dict,
                 career_paths_data: Dict,
                 skills_taxonomy: Dict,
                 learning_resources: Dict):
        """
        Initialize orchestrator with all required data
        
        Args:
            llm_client: LLM client for AI operations
            job_market_data: Job market data (job_market.json)
            career_paths_data: Career paths data (career_paths.json)
            skills_taxonomy: Skills taxonomy (skills_taxonomy.json)
            learning_resources: Learning resources (learning_resources.json)
        """
        
        # Initialize all agents
        self.profile_analyzer = ProfileAnalyzer(llm_client, skills_taxonomy)
        self.market_intelligence = MarketIntelligenceAgent(job_market_data, skills_taxonomy)
        self.feasibility_evaluator = FeasibilityEvaluator(llm_client)
        self.roadmap_generator = RoadmapGenerator(llm_client, learning_resources)
        self.reroute_agent = RerouteAgent(
            llm_client,
            job_market_data,
            career_paths_data,
            skills_taxonomy
        )
        self.progress_tracker = ProgressTracker(
            self.market_intelligence,
            self.reroute_agent
        )
        
        self.llm = llm_client
    
    def process_student_query(self,
                             desired_role: str,
                             skills_text: str = None,
                             resume_text: str = None,
                             education: str = None,
                             experience: str = None,
                             projects: List[str] = None,
                             duration_weeks: int = 12) -> Dict[str, Any]:
        """
        Complete end-to-end career guidance workflow
        
        Args:
            desired_role: Target career role
            skills_text: Student's skills description
            resume_text: Resume/CV text
            education: Education background
            experience: Work experience
            projects: List of projects
            duration_weeks: Available learning time
            
        Returns:
            Complete guidance including profile, feasibility, and roadmap
        """
        
        # STEP 1: Profile Analysis
        print("📊 Step 1: Analyzing student profile...")
        profile_result = self.profile_analyzer.analyze_profile(
            skills_text=skills_text,
            resume_text=resume_text,
            education=education,
            experience=experience,
            projects=projects
        )
        student_profile = profile_result["student_profile"]
        
        # STEP 2: Market Intelligence
        print("📊 Step 2: Gathering market intelligence...")
        student_skills = self._extract_skills_list(student_profile)
        market_analysis = self.market_intelligence.analyze_role_market(
            role_name=desired_role,
            student_skills=student_skills
        )
        
        if "error" in market_analysis:
            return {
                "status": "error",
                "message": market_analysis["error"],
                "available_roles": market_analysis.get("available_roles", [])
            }
        
        market_analysis = market_analysis["market_analysis"]
        
        # STEP 3: Feasibility Evaluation
        print("🤖 Step 3: Evaluating feasibility...")
        feasibility_result = self.feasibility_evaluator.evaluate(
            student_profile=student_profile,
            market_analysis=market_analysis,
            desired_role=desired_role
        )
        
        feasibility = feasibility_result["feasibility_evaluation"]
        verdict = feasibility["verdict"]
        
        # STEP 4: Decision Branch
        if verdict == "FEASIBLE":
            print("✅ Goal is feasible! Generating roadmap...")
            return self._handle_feasible_path(
                desired_role=desired_role,
                student_profile=student_profile,
                market_analysis=market_analysis,
                feasibility=feasibility,
                duration_weeks=duration_weeks
            )
        
        elif verdict == "CHALLENGING":
            print("⚠️ Goal is challenging. Offering choice...")
            return self._handle_challenging_path(
                desired_role=desired_role,
                student_profile=student_profile,
                market_analysis=market_analysis,
                feasibility=feasibility,
                duration_weeks=duration_weeks
            )
        
        else:  # NOT_FEASIBLE
            print("🔄 Goal not feasible. Finding alternatives...")
            return self._handle_reroute_path(
                desired_role=desired_role,
                student_profile=student_profile,
                market_analysis=market_analysis,
                feasibility=feasibility,
                duration_weeks=duration_weeks
            )
    
    def _handle_feasible_path(self,
                             desired_role: str,
                             student_profile: Dict,
                             market_analysis: Dict,
                             feasibility: Dict,
                             duration_weeks: int) -> Dict[str, Any]:
        """
        Handle feasible career path - generate direct roadmap
        """
        
        # Generate roadmap
        print("🤖 Generating learning roadmap...")
        roadmap_result = self.roadmap_generator.generate_roadmap(
            target_role=desired_role,
            student_profile=student_profile,
            market_analysis=market_analysis,
            duration_weeks=duration_weeks
        )
        
        return {
            "status": "success",
            "verdict": "FEASIBLE",
            "path_type": "direct",
            "target_role": desired_role,
            "profile": student_profile,
            "market_analysis": market_analysis,
            "feasibility": feasibility,
            "roadmap": roadmap_result,
            "message": f"Great news! {desired_role} is a realistic goal for you. Here's your personalized roadmap."
        }
    
    def _handle_challenging_path(self,
                                 desired_role: str,
                                 student_profile: Dict,
                                 market_analysis: Dict,
                                 feasibility: Dict,
                                 duration_weeks: int) -> Dict[str, Any]:
        """
        Handle challenging path - offer both direct and alternative
        """
        
        # Generate direct roadmap (will require more effort)
        print("🤖 Generating challenging roadmap...")
        direct_roadmap = self.roadmap_generator.generate_roadmap(
            target_role=desired_role,
            student_profile=student_profile,
            market_analysis=market_analysis,
            duration_weeks=duration_weeks
        )
        
        # Also find alternatives
        print("🔄 Finding easier alternatives...")
        alternatives_result = self.reroute_agent.find_alternatives(
            student_profile=student_profile,
            failed_role=desired_role,
            failed_market_analysis=market_analysis,
            top_n=2
        )
        
        alternatives = alternatives_result["reroute_recommendations"]["alternatives"]
        
        # Generate roadmap for top alternative
        if alternatives:
            top_alt = alternatives[0]
            alt_market = top_alt["market_analysis"]
            
            # Create simplified market analysis for roadmap generator
            alt_market_full = self.market_intelligence.analyze_role_market(
                role_name=top_alt["role"],
                student_skills=self._extract_skills_list(student_profile)
            )["market_analysis"]
            
            alt_roadmap = self.roadmap_generator.generate_roadmap(
                target_role=top_alt["role"],
                student_profile=student_profile,
                market_analysis=alt_market_full,
                duration_weeks=duration_weeks // 2  # Shorter timeline
            )
            
            top_alt["roadmap"] = alt_roadmap
        
        return {
            "status": "success",
            "verdict": "CHALLENGING",
            "path_type": "choice",
            "target_role": desired_role,
            "profile": student_profile,
            "market_analysis": market_analysis,
            "feasibility": feasibility,
            "direct_path": {
                "roadmap": direct_roadmap,
                "difficulty": "high",
                "warning": feasibility.get("recommendation")
            },
            "alternative_paths": alternatives,
            "message": f"{desired_role} is achievable but challenging. Consider these options:"
        }
    
    def _handle_reroute_path(self,
                            desired_role: str,
                            student_profile: Dict,
                            market_analysis: Dict,
                            feasibility: Dict,
                            duration_weeks: int) -> Dict[str, Any]:
        """
        Handle not feasible path - suggest alternatives
        """
        
        # Find alternatives
        print("🤖 Finding optimal alternative careers...")
        alternatives_result = self.reroute_agent.find_alternatives(
            student_profile=student_profile,
            failed_role=desired_role,
            failed_market_analysis=market_analysis,
            top_n=3
        )
        
        alternatives = alternatives_result["reroute_recommendations"]["alternatives"]
        
        # Generate roadmaps for top 2 alternatives
        for i, alt in enumerate(alternatives[:2]):
            print(f"🤖 Generating roadmap for alternative {i+1}: {alt['role']}...")
            
            # Get full market analysis
            alt_market_full = self.market_intelligence.analyze_role_market(
                role_name=alt["role"],
                student_skills=self._extract_skills_list(student_profile)
            )["market_analysis"]
            
            # Generate roadmap
            alt_roadmap = self.roadmap_generator.generate_roadmap(
                target_role=alt["role"],
                student_profile=student_profile,
                market_analysis=alt_market_full,
                duration_weeks=duration_weeks
            )
            
            alt["roadmap"] = alt_roadmap
            alt["full_market_analysis"] = alt_market_full
        
        return {
            "status": "success",
            "verdict": "NOT_FEASIBLE",
            "path_type": "reroute",
            "original_role": desired_role,
            "profile": student_profile,
            "original_market_analysis": market_analysis,
            "feasibility": feasibility,
            "recommended_alternatives": alternatives,
            "message": f"Based on current market conditions and your profile, consider these strategic alternatives to {desired_role}:"
        }
    
    def _extract_skills_list(self, student_profile: Dict) -> List[str]:
        """
        Extract flat list of skills from profile
        """
        technical_skills = student_profile.get("technical_skills", {})
        
        all_skills = []
        for category, skills in technical_skills.items():
            all_skills.extend(skills)
        
        return all_skills
    
    def start_learning_journey(self,
                              student_profile: Dict,
                              roadmap: List[Dict],
                              target_role: str,
                              market_analysis: Dict) -> Dict[str, Any]:
        """
        Initialize progress tracking for a learning journey
        
        Returns:
            Session information for tracking progress
        """
        
        session_id = str(uuid.uuid4())
        
        result = self.progress_tracker.initialize_journey(
            session_id=session_id,
            student_profile=student_profile,
            roadmap=roadmap,
            target_role=target_role,
            market_snapshot=market_analysis
        )
        
        return result
    
    def track_progress(self,
                      session_id: str,
                      step_number: int,
                      status: str,
                      time_spent_hours: float = None,
                      blocker_reason: str = None) -> Dict[str, Any]:
        """
        Track student progress on a step
        
        Args:
            session_id: Journey session ID
            step_number: Step number being tracked
            status: "completed" or "blocked"
            time_spent_hours: Hours spent on step
            blocker_reason: Reason if blocked
            
        Returns:
            Progress update with potential re-evaluation
        """
        
        if status == "completed":
            return self.progress_tracker.record_step_completion(
                session_id=session_id,
                step_number=step_number,
                time_spent_hours=time_spent_hours
            )
        elif status == "blocked":
            return self.progress_tracker.record_blocker(
                session_id=session_id,
                step_number=step_number,
                reason=blocker_reason or "No reason provided"
            )
        else:
            return {"error": f"Invalid status: {status}"}
    
    def get_progress(self, session_id: str) -> Dict[str, Any]:
        """
        Get complete progress summary
        """
        return self.progress_tracker.get_progress_summary(session_id)
    
    def get_next_step(self, session_id: str) -> Dict[str, Any]:
        """
        Get next step to work on
        """
        return self.progress_tracker.get_next_step(session_id)


def load_data_files(data_dir: str = None) -> tuple:
    """
    Load all required data files
    
    Returns:
        (job_market, career_paths, skills_taxonomy, learning_resources)
    """
    from pathlib import Path
    
    # Use absolute path based on this file's location if data_dir not provided
    if data_dir is None:
        data_dir = str(Path(__file__).parent / "data")
    
    with open(f"{data_dir}/job_market.json", "r") as f:
        job_market = json.load(f)
    
    with open(f"{data_dir}/career_paths.json", "r") as f:
        career_paths = json.load(f)
    
    with open(f"{data_dir}/skills_taxonomy.json", "r") as f:
        skills_taxonomy = json.load(f)
    
    with open(f"{data_dir}/learning_resources.json", "r") as f:
        learning_resources = json.load(f)
    
    return job_market, career_paths, skills_taxonomy, learning_resources


# Example usage
if __name__ == "__main__":
    # Initialize LLM
    llm = LLMClient()
    
    # Load data
    job_market, career_paths, skills_taxonomy, learning_resources = load_data_files()
    
    # Create orchestrator
    orchestrator = CareerAgentOrchestrator(
        llm_client=llm,
        job_market_data=job_market,
        career_paths_data=career_paths,
        skills_taxonomy=skills_taxonomy,
        learning_resources=learning_resources
    )
    
    # Test query
    result = orchestrator.process_student_query(
        desired_role="Machine Learning Engineer",
        skills_text="I know Python basics and have done some web scraping",
        education="3rd year Computer Science",
        projects=["Built a Django website", "Web scraping project"],
        duration_weeks=12
    )
    
    print("\n" + "="*80)
    print("RESULT:")
    print(json.dumps(result, indent=2))