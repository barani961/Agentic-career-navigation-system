# 📬 Postman Testing Guide - Career Agent API

## Quick Start

1. **Import this guide into Postman**
2. **Set variables in Postman:**
   - `base_url` = `http://localhost:8000`
   - `api_key` = (optional, if needed)
3. **Follow the flow from Test 1 → Test 9**

---

## Prerequisites

- Backend running: `python api/main.py`
- Database initialized with schema
- Environment variables set (GROQ_API_KEY, DB credentials)

---

## Test 1: Health Check ✅

**Purpose:** Verify API is running

**Method:** `GET`

**URL:**
```
http://localhost:8000/health
```

**Headers:** None

**Body:** None

**Expected Response (200):**
```json
{
  "status": "ok",
  "timestamp": "2024-01-15T10:30:00",
  "message": "API is running"
}
```

---

## Test 2: Initial Career Assessment 🎯

**Purpose:** User submits career goal and receives roadmap

**Method:** `POST`

**URL:**
```
http://localhost:8000/api/assess
```

**Headers:**
```
Content-Type: application/json
```

**Body (Raw JSON):**
```json
{
  "user_id": "user_123",
  "user_name": "John Doe",
  "desired_role": "Data Analyst",
  "current_skills": "Python, Excel, Basic SQL",
  "education": "Bachelor's in Business",
  "experience": "2 years in Finance",
  "projects": "Created budget tracking dashboard",
  "available_duration_weeks": 12
}
```

**Expected Response (200):**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user_123",
  "target_role": "Data Analyst",
  "feasibility_verdict": "FEASIBLE",
  "student_profile": {
    "skill_level": "Intermediate",
    "education_background": "Bachelor's in Business",
    "experience_summary": "2 years Finance sector experience",
    "key_strengths": ["Analytical thinking", "Excel proficiency"],
    "growth_areas": ["Advanced SQL", "Data visualization"]
  },
  "market_snapshot": {
    "role_name": "Data Analyst",
    "market_demand": "High",
    "median_salary": 75000,
    "required_skills": ["SQL", "Python", "Tableau", "Statistical Analysis"],
    "job_growth_rate": "18%",
    "fresher_friendly": true,
    "avg_interview_difficulty": "Medium"
  },
  "roadmap": [
    {
      "step_number": 1,
      "title": "Master SQL Fundamentals",
      "description": "Learn SQL queries, joins, aggregations",
      "estimated_hours": 40,
      "resources": [
        {"name": "LeetCode SQL", "link": "https://leetcode.com/problemset/database/"},
        {"name": "SQL Tutorial", "link": "https://www.w3schools.com/sql/"}
      ],
      "skills_gained": ["SQL", "Database Design"],
      "proficiency_level": "intermediate",
      "milestone": "Write complex joins and window functions"
    },
    {
      "step_number": 2,
      "title": "Python for Data Analysis",
      "description": "Learn pandas, numpy, matplotlib",
      "estimated_hours": 50,
      "resources": [...],
      "skills_gained": ["Python", "Data Manipulation", "Visualization"],
      "proficiency_level": "intermediate",
      "milestone": "Build complete data analysis pipeline"
    }
  ],
  "alternatives": [],
  "message": "You're well-positioned for this role! Follow the roadmap to upskill."
}
```

---

## Test 3: Start a Step ▶️

**Purpose:** User indicates they're starting work on a step

**Method:** `POST`

**URL:**
```
http://localhost:8000/api/journey/{session_id}/steps/start
```

**URL Example:**
```
http://localhost:8000/api/journey/550e8400-e29b-41d4-a716-446655440000/steps/start
```

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "step_number": 1
}
```

**Expected Response (200):**
```json
{
  "success": true,
  "message": "Step 1 started",
  "step": {
    "step_number": 1,
    "title": "Master SQL Fundamentals",
    "status": "in_progress",
    "started_at": "2024-01-15T10:35:00"
  }
}
```

---

## Test 4: Complete a Step ✅

**Purpose:** User marks a step as completed with time spent

**Method:** `POST`

**URL:**
```
http://localhost:8000/api/progress
```

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "step_number": 1,
  "status": "completed",
  "time_spent_hours": 42.5
}
```

**Expected Response (200):**
```json
{
  "success": true,
  "message": "Step completed successfully",
  "step": {
    "step_number": 1,
    "title": "Master SQL Fundamentals",
    "status": "completed",
    "completed_at": "2024-01-15T10:45:00",
    "time_spent_hours": 42.5
  },
  "skills_added": ["SQL", "Database Design"],
  "progress_percentage": 25,
  "next_step": {
    "step_number": 2,
    "title": "Python for Data Analysis"
  },
  "should_reevaluate": false,
  "reevaluation": null,
  "message": "Excellent! You've completed step 1. Well done!"
}
```

---

## Test 5: Report a Blocker 🚫

**Purpose:** User reports being blocked on a step and requests help

**Method:** `POST`

**URL:**
```
http://localhost:8000/api/progress
```

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "step_number": 2,
  "status": "blocked",
  "blocker_reason": "Struggling with complex pandas operations - groupby and pivot tables not clear",
  "time_spent_hours": 8.0
}
```

**Expected Response (200) - No Reevaluation Trigger:**
```json
{
  "success": true,
  "message": "Blocker recorded. Don't worry, we've noted your challenge!",
  "step": {
    "step_number": 2,
    "status": "blocked",
    "blocker_reason": "Struggling with complex pandas operations...",
    "attempt_count": 1,
    "blocked_at": "2024-01-15T11:00:00"
  },
  "should_reevaluate": false,
  "suggestion": "Consider revisiting basic pandas operations. Try DataCamp's Pandas course.",
  "reevaluation": null
}
```

**Expected Response (200) - With Reevaluation Trigger:**
```json
{
  "success": true,
  "message": "Blocker recorded and re-evaluation triggered",
  "step": {
    "step_number": 2,
    "status": "blocked",
    "attempt_count": 3,
    "blocked_at": "2024-01-15T11:00:00"
  },
  "should_reevaluate": true,
  "reevaluation": {
    "reevaluation_id": 1,
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "trigger_type": "repeated_blocking",
    "trigger_severity": "high",
    "message": "We noticed you're struggling with this skill. Let's explore alternatives!",
    "current_role": "Data Analyst",
    "alternatives": [
      {
        "role": "Business Analyst",
        "match_score": 85,
        "justification": "Leverages your Finance background better",
        "market_data": {
          "active_jobs": 8500,
          "entry_barrier": "Low",
          "fresher_friendly": true
        }
      },
      {
        "role": "Financial Analyst",
        "match_score": 88,
        "justification": "Perfect fit for your experience",
        "market_data": {
          "active_jobs": 6200,
          "entry_barrier": "Low",
          "fresher_friendly": true
        }
      }
    ]
  }
}
```

---

## Test 6: Get Journey Summary 📊

**Purpose:** Retrieve complete journey details and progress

**Method:** `GET`

**URL:**
```
http://localhost:8000/api/journey/{session_id}/summary
```

**URL Example:**
```
http://localhost:8000/api/journey/550e8400-e29b-41d4-a716-446655440000/summary
```

**Headers:** None

**Body:** None

**Expected Response (200):**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user_123",
  "target_role": "Data Analyst",
  "desired_role": "Data Analyst",
  "feasibility_verdict": "FEASIBLE",
  "status": "in_progress",
  "created_at": "2024-01-15T10:30:00",
  "progress_percentage": 25,
  "completed_steps": 1,
  "total_steps": 8,
  "steps": [
    {
      "step_number": 1,
      "title": "Master SQL Fundamentals",
      "status": "completed",
      "completed_at": "2024-01-15T10:45:00",
      "time_spent_hours": 42.5,
      "resources": [...]
    },
    {
      "step_number": 2,
      "title": "Python for Data Analysis",
      "status": "blocked",
      "blocked_at": "2024-01-15T11:00:00",
      "blocker_reason": "Struggling with complex pandas operations",
      "attempt_count": 2
    },
    {
      "step_number": 3,
      "title": "Data Visualization",
      "status": "not_started"
    }
  ],
  "skills_learned": [
    {
      "skill_name": "SQL",
      "proficiency_level": "intermediate",
      "date_learned": "2024-01-15T10:45:00"
    },
    {
      "skill_name": "Database Design",
      "proficiency_level": "beginner",
      "date_learned": "2024-01-15T10:45:00"
    }
  ],
  "active_blockers": [
    {
      "step_number": 2,
      "blocker_reason": "Struggling with complex pandas operations",
      "attempts": 2,
      "first_blocked_at": "2024-01-15T11:00:00"
    }
  ],
  "reevaluations": []
}
```

---

## Test 7: Accept Reroute 🔄

**Purpose:** User switches to alternative career path

**Method:** `POST`

**URL:**
```
http://localhost:8000/api/reroute
```

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "reevaluation_id": 1,
  "chosen_role": "Business Analyst",
  "reason": "better_fit"
}
```

**Expected Response (200):**
```json
{
  "success": true,
  "reroute_id": "550e8400-e29b-41d4-a716-446656440001",
  "message": "Successfully switched to Business Analyst!",
  "journey": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "old_target_role": "Data Analyst",
    "new_target_role": "Business Analyst",
    "reason": "better_fit",
    "rerouted_at": "2024-01-15T11:15:00"
  },
  "new_roadmap": [
    {
      "step_number": 1,
      "title": "Business Analysis Fundamentals",
      "description": "Learn BA concepts, requirements gathering",
      "estimated_hours": 35,
      "skills_gained": ["Business Analysis", "Requirements Gathering"]
    },
    {
      "step_number": 2,
      "title": "Stakeholder Management",
      "description": "Master communication and stakeholder engagement",
      "estimated_hours": 40,
      "skills_gained": ["Communication", "Stakeholder Management"]
    }
  ],
  "retained_skills": ["SQL", "Database Design"],
  "message": "New roadmap generated incorporating your learned skills!"
}
```

---

## Test 8: Get All User Journeys 📚

**Purpose:** Retrieve all journeys for a user

**Method:** `GET`

**URL:**
```
http://localhost:8000/api/user/{user_id}/journeys
```

**URL Example:**
```
http://localhost:8000/api/user/user_123/journeys
```

**Headers:** None

**Body:** None

**Expected Response (200):**
```json
{
  "user_id": "user_123",
  "total_journeys": 2,
  "journeys": [
    {
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "target_role": "Business Analyst",
      "status": "in_progress",
      "progress_percentage": 25,
      "created_at": "2024-01-15T10:30:00",
      "last_updated": "2024-01-15T11:15:00",
      "completed_steps": 1,
      "total_steps": 8
    },
    {
      "session_id": "550e8400-e29b-41d4-a716-446655440001",
      "target_role": "Data Scientist",
      "status": "completed",
      "progress_percentage": 100,
      "created_at": "2024-01-10T08:00:00",
      "last_updated": "2024-01-14T15:30:00",
      "completed_steps": 12,
      "total_steps": 12
    }
  ]
}
```

---

## Test 9: Pause/Resume Journey ⏸️

### 9A. Pause Journey

**Method:** `POST`

**URL:**
```
http://localhost:8000/api/journey/{session_id}/pause
```

**Body:**
```json
{
  "reason": "Taking a break for personal reasons"
}
```

**Expected Response (200):**
```json
{
  "success": true,
  "message": "Journey paused",
  "journey": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "paused",
    "paused_at": "2024-01-15T11:30:00",
    "pause_reason": "Taking a break for personal reasons"
  }
}
```

### 9B. Resume Journey

**Method:** `POST`

**URL:**
```
http://localhost:8000/api/journey/{session_id}/resume
```

**Body:**
```json
{
  "reason": "Ready to continue learning"
}
```

**Expected Response (200):**
```json
{
  "success": true,
  "message": "Journey resumed",
  "journey": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "in_progress",
    "resumed_at": "2024-01-15T12:00:00",
    "total_paused_duration_hours": 0.5
  }
}
```

---

## Complete Testing Workflow (Sequential)

### Order of Tests for Full Flow:

1. **Test 1:** Health Check (verify API alive)
2. **Test 2:** Initial Assessment (get session_id and roadmap)
3. **Test 3:** Start Step 1 (mark as in_progress)
4. **Test 4:** Complete Step 1 (mark as completed, should_reevaluate=false)
5. **Test 3:** Start Step 2 (mark as in_progress)
6. **Test 5:** Report Blocker Step 2 × 3 times (trigger reevaluation on 3rd)
7. **Test 6:** Get Journey Summary (verify all changes)
8. **Test 7:** Accept Reroute (switch to Business Analyst)
9. **Test 6:** Get Journey Summary Again (verify new roadmap)
10. **Test 8:** Get All Journeys (see history)
11. **Test 9A:** Pause Journey (take break)
12. **Test 9B:** Resume Journey (continue)

---

## Common Error Responses

### Invalid Session ID
```json
{
  "detail": "Session not found",
  "error_code": "SESSION_NOT_FOUND"
}
```

### Missing Required Field
```json
{
  "detail": [
    {
      "loc": ["body", "desired_role"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Database Error
```json
{
  "detail": "Database error: Could not record step completion",
  "error_code": "DB_ERROR"
}
```

### API Rate Limit
```json
{
  "detail": "API rate limit exceeded",
  "error_code": "RATE_LIMIT"
}
```

---

## Postman Environment Variables

Create a Postman environment with these variables:

```json
{
  "base_url": "http://localhost:8000",
  "session_id": "{{from Test 2 response}}",
  "user_id": "user_123",
  "reevaluation_id": "{{from Test 5 response if triggered}}"
}
```

Then use in requests like:
```
{{base_url}}/api/progress
{{base_url}}/api/journey/{{session_id}}/summary
```

---

## Performance Benchmarks

| Endpoint | Typical Response Time | Max Response Size |
|----------|----------------------|-------------------|
| Health Check | <50ms | <1KB |
| Assessment | 3-8 seconds | ~50KB |
| Step Completion | <500ms | <5KB |
| Blocker Report | <500ms | <10KB |
| Journey Summary | <300ms | ~30KB |
| Get Journeys | <500ms | ~50KB |
| Reroute | 2-5 seconds | ~40KB |

---

## Notes

- All timestamps are in ISO 8601 format (UTC)
- Session IDs are UUIDs generated on initial assessment
- Progress percentage calculates as: (completed_steps / total_steps) × 100
- Re-evaluation triggers on: 3rd blocker on same step, 2+ active blockers, periodic check, or low motivation
- Rerouting preserves learned skills and links them to new roadmap
