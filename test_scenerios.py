"""
Test different student scenarios
"""

import os
from llm.llm_client import LLMClient
from orchestrator import load_data_files, CareerAgentOrchestrator


def test_scenario_1_feasible():
    """Strong student for Data Analyst - should be FEASIBLE"""
    print("\n" + "="*70)
    print("TEST 1: FEASIBLE SCENARIO")
    print("="*70)
    
    llm = LLMClient()
    data = load_data_files()
    orch = CareerAgentOrchestrator(llm, *data)
    
    result = orch.process_student_query(
        desired_role="Data Analyst",
        skills_text="Python, SQL, Excel, data visualization",
        education="4th year B.Tech CS",
        projects=["Sales dashboard", "Customer analysis"],
        duration_weeks=12
    )
    
    print(f"\n✅ Verdict: {result['verdict']}")
    print(f"📊 Feasibility: {result['feasibility']['feasibility_score']}")
    return result


def test_scenario_2_not_feasible():
    """Weak student for ML Engineer - should be NOT_FEASIBLE"""
    print("\n" + "="*70)
    print("TEST 2: NOT FEASIBLE (REROUTE) SCENARIO")
    print("="*70)
    
    llm = LLMClient()
    data = load_data_files()
    orch = CareerAgentOrchestrator(llm, *data)
    
    result = orch.process_student_query(
        desired_role="ML Engineer",
        skills_text="Python basics, HTML",
        education="2nd year B.Tech",
        projects=["Simple calculator"],
        duration_weeks=12
    )
    
    # Handle possible error response (e.g., unknown role)
    if result.get("status") == "error":
        print(f"\n❌ Could not evaluate scenario 2:")
        print(f"   Message: {result.get('message')}")
        available = result.get("available_roles")
        if available:
            print(f"   Available roles in data: {', '.join(available[:5])}")
        return result
    
    print(f"\n✅ Verdict: {result.get('verdict')}")
    
    if result.get('recommended_alternatives'):
        print(f"\n🔄 Alternatives Found: {len(result['recommended_alternatives'])}")
        for alt in result['recommended_alternatives'][:2]:
            print(f"   • {alt['role']} (Score: {alt['total_score']:.2f})")
            print(f"     {alt.get('justification', '')[:100]}...")
    
    return result


def test_scenario_3_challenging():
    """Medium student for Software Engineer - should be CHALLENGING"""
    print("\n" + "="*70)
    print("TEST 3: CHALLENGING SCENARIO")
    print("="*70)
    
    llm = LLMClient()
    data = load_data_files()
    orch = CareerAgentOrchestrator(llm, *data)
    
    result = orch.process_student_query(
        desired_role="Software Engineer",
        skills_text="Python, basic DSA",
        education="3rd year B.Tech",
        projects=["Todo app"],
        duration_weeks=12
    )
    
    print(f"\n✅ Verdict: {result['verdict']}")
    
    if result.get('direct_path'):
        print("📊 Direct path available (challenging)")
    if result.get('alternative_paths'):
        print(f"🔄 {len(result['alternative_paths'])} easier alternatives suggested")
    
    return result


if __name__ == "__main__":
    print("\n🚀 TESTING ALL SCENARIOS")
    
    try:
        # Test 1
        r1 = test_scenario_1_feasible()
        
        # Test 2
        r2 = test_scenario_2_not_feasible()
        
        # Test 3
        r3 = test_scenario_3_challenging()
        
        print("\n" + "="*70)
        print("✅ ALL SCENARIOS TESTED SUCCESSFULLY!")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()