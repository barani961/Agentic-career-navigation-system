"""
Interactive test script that runs agents one-by-one:
- ProfileAnalyzer
- MarketIntelligenceAgent
- FeasibilityEvaluator
- RoadmapGenerator

It asks for inputs, then prints 4 JSON blobs:
one per agent, each with its output + a short reasoning string.
"""

import os
import json
from dotenv import load_dotenv
from llm.llm_client import LLMClient
from orchestrator import load_data_files, CareerAgentOrchestrator


def _extract_skills_from_profile(student_profile: dict) -> list:
    """Helper to flatten technical skills from profile into a skill list."""
    technical_skills = student_profile.get("technical_skills", {})
    skills = []
    for _, vals in technical_skills.items():
        skills.extend(vals)
    return skills


def run_interactive_agents():
    print("\n" + "=" * 70)
    print("🚀 CAREER AGENT SYSTEM - INTERACTIVE AGENT TEST")
    print("=" * 70)

    # Load environment variables
    load_dotenv()

    # 1) Check API key
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("\n❌ GROQ_API_KEY not found.")
        print("Set it with: export GROQ_API_KEY='your_key'")
        return

    # 2) Initialize LLM
    try:
        llm = LLMClient()
    except Exception as e:
        print(f"\n❌ Failed to initialize LLMClient: {e}")
        return

    # 3) Load data
    try:
        job_market, career_paths, skills_taxonomy, learning_resources = load_data_files()
    except Exception as e:
        print(f"\n❌ Failed to load data files: {e}")
        return

    # 4) Initialize orchestrator and agents
    try:
        orch = CareerAgentOrchestrator(
            llm_client=llm,
            job_market_data=job_market,
            career_paths_data=career_paths,
            skills_taxonomy=skills_taxonomy,
            learning_resources=learning_resources,
        )
    except Exception as e:
        print(f"\n❌ Failed to initialize agents: {e}")
        return

    profile_agent = orch.profile_analyzer
    market_agent = orch.market_intelligence
    feasibility_agent = orch.feasibility_evaluator
    roadmap_agent = orch.roadmap_generator

    # ========== COLLECT INPUTS ==========
    print("\nProvide student details (press Enter to skip optional fields).\n")

    desired_role = input("Target role (e.g., Data Analyst): ").strip() or "Data Analyst"
    skills_text = input("Skills (free text): ").strip()
    education = input("Education (e.g., 3rd year B.Tech CS): ").strip()
    experience = input("Experience (optional description): ").strip()
    projects_raw = input("Projects (separate by ';', optional): ").strip()
    duration_raw = input("Available duration in weeks (default 12): ").strip()

    projects = [p.strip() for p in projects_raw.split(";") if p.strip()] if projects_raw else []
    try:
        duration_weeks = int(duration_raw) if duration_raw else 12
    except ValueError:
        duration_weeks = 12

    # ========== AGENT 1: PROFILE ANALYZER ==========
    profile_result = profile_agent.analyze_profile(
        skills_text=skills_text or None,
        resume_text=None,
        education=education or None,
        experience=experience or None,
        projects=projects or None,
    )
    student_profile = profile_result["student_profile"]

    profile_reasoning = (
        f"Detected experience level as '{student_profile.get('experience_level')}', "
        f"strength areas: {student_profile.get('strength_areas', [])}, "
        f"weakness areas: {student_profile.get('weakness_areas', [])}, "
        f"learning_capacity estimated as '{student_profile.get('learning_capacity')}'."
    )

    profile_json = {
        "agent": "ProfileAnalyzer",
        "output": profile_result,
        "reasoning": profile_reasoning,
    }

    # ========== AGENT 2: MARKET INTELLIGENCE ==========
    student_skills = _extract_skills_from_profile(student_profile)
    market_result = market_agent.analyze_role_market(
        role_name=desired_role,
        student_skills=student_skills,
    )

    if "error" in market_result:
        market_output = market_result
        market_reasoning = (
            f"Could not find market data for role '{desired_role}'. "
            f"Available roles: {market_result.get('available_roles', [])}."
        )
    else:
        market_analysis = market_result["market_analysis"]
        market_output = market_result
        market_reasoning = (
            f"Demand score {market_analysis.get('demand_score')}/100 with "
            f"{market_analysis.get('active_jobs')} active jobs, "
            f"entry barrier {market_analysis.get('entry_barrier')*100:.0f}%, "
            f"skill_match {market_analysis.get('skill_match')*100:.0f}%."
        )

    market_json = {
        "agent": "MarketIntelligenceAgent",
        "output": market_output,
        "reasoning": market_reasoning,
    }

    # ========== AGENT 3: FEASIBILITY EVALUATOR ==========
    feasibility_json = None
    roadmap_json = None

    if "error" not in market_result:
        market_analysis = market_result["market_analysis"]
        feasibility_result = feasibility_agent.evaluate(
            student_profile=student_profile,
            market_analysis=market_analysis,
            desired_role=desired_role,
        )
        feas = feasibility_result["feasibility_evaluation"]

        feasibility_reasoning = feas.get(
            "explanation",
            f"Verdict '{feas.get('verdict')}' with feasibility_score "
            f"{feas.get('feasibility_score')}, action '{feas.get('action')}'.",
        )

        feasibility_json = {
            "agent": "FeasibilityEvaluator",
            "output": feasibility_result,
            "reasoning": feasibility_reasoning,
        }

        # ========== AGENT 4: ROADMAP GENERATOR ==========
        roadmap_result = roadmap_agent.generate_roadmap(
            target_role=desired_role,
            student_profile=student_profile,
            market_analysis=market_analysis,
            duration_weeks=duration_weeks,
        )

        roadmap_reasoning = (
            f"Generated roadmap covering {roadmap_result.get('skills_covered')} key skills "
            f"over {roadmap_result.get('total_duration_weeks')} weeks "
            f"with market_alignment_score {roadmap_result.get('market_alignment_score')}."
        )

        roadmap_json = {
            "agent": "RoadmapGenerator",
            "output": roadmap_result,
            "reasoning": roadmap_reasoning,
        }

    # ========== PRINT FINAL JSONS ==========
    print("\n\n==================== AGENT OUTPUTS (JSON) ====================\n")

    print(json.dumps(profile_json, indent=2))
    print()
    print(json.dumps(market_json, indent=2))

    if feasibility_json:
        print()
        print(json.dumps(feasibility_json, indent=2))

    if roadmap_json:
        print()
        print(json.dumps(roadmap_json, indent=2))


if __name__ == "__main__":
    run_interactive_agents()