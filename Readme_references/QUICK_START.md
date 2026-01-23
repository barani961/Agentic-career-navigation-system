# 🚀 Quick Start Guide

## System Overview

Your Career Agent System is a **complete AI-powered learning platform** that:
1. **Assesses** your current skills and goals using AI
2. **Generates** personalized learning roadmaps
3. **Tracks** your progress step-by-step
4. **Detects** when you're struggling
5. **Re-evaluates** your path automatically
6. **Reroutes** to better-fit careers when needed

---

## Architecture At a Glance

```
Streamlit UI (Port 8501)
        ↓
    FastAPI (Port 8000)
        ↓
  AI Agents + PostgreSQL
```

---

## What Each Component Does

### **Frontend (Streamlit)**
- 🏠 **Home Page:** Initial assessment form
- 📊 **Dashboard:** Progress tracking, roadmap, skills, blockers
- 🔄 **Re-evaluation Page:** Alternative paths when you're struggling
- ⚙️ **Navigation:** Switch between pages, start new journey

### **Backend (FastAPI)**
- `/api/assess` → Process assessment, create journey, generate roadmap
- `/api/progress` → Update step status (completed/blocked)
- `/api/reroute` → Switch to alternative career path
- `/api/journey/{id}/summary` → Get complete journey data
- `GET /api/user/{id}/journeys` → View all journeys

### **Database (PostgreSQL)**
- **users** → User profiles
- **journeys** → Learning paths with roadmaps
- **steps** → Roadmap steps with resources
- **blockers** → Issues encountered
- **reevaluations** → When system suggests alternatives
- **reroutes** → Career path switches
- **skills_learned** → Skills acquired

### **AI Agents**
- **Profile Analyzer** → Extract your strengths/weaknesses
- **Market Intelligence** → Research job market
- **Feasibility Evaluator** → Check if goal is achievable
- **Roadmap Generator** → Create personalized learning steps
- **Reroute Agent** → Find better alternative paths

---

## Complete User Journey (Step-by-Step)

### **1️⃣ Start Assessment**
```
User clicks "Analyze My Career Path"
    ↓
AI analyzes:
  • Your skills
  • Market demand
  • Career feasibility
    ↓
System shows:
  • Verdict (FEASIBLE/CHALLENGING/NOT_FEASIBLE)
  • Personalized roadmap (8-12 steps)
  • Market insights
  • Learning resources
```

### **2️⃣ Learn and Track Progress**
```
User clicks "Start Step" on roadmap
    ↓
User studies resources for the step
    ↓
User clicks "Mark Done" when complete
    ↓
System:
  • Records time spent
  • Adds skill to profile
  • Updates progress %
  • Checks if reevaluation needed
```

### **3️⃣ Report Problems**
```
User gets stuck on a step
    ↓
User clicks "Report Issue"
    ↓
System:
  • Records the problem
  • Increases attempt count
  • Offers suggestions
  • If 3+ attempts: trigger re-evaluation
```

### **4️⃣ Get Re-evaluated**
```
System detects you're struggling
  (Multiple blockers OR same blocker 3+ times)
    ↓
Shows "Re-evaluation" page with:
  • Why system suggests re-evaluation
  • Alternative career paths
  • Market data for each path
  • Roadmap preview
    ↓
User chooses:
  A) Continue current path → Back to dashboard
  B) Switch to alternative → New roadmap generated
```

### **5️⃣ Switch Careers (Rerouting)**
```
User clicks "Switch to [Role]"
    ↓
System:
  • Generates new roadmap for role
  • Keeps learned skills
  • Resets progress
  • Updates target role
    ↓
User continues learning from Step 1
```

---

## Key Features Explained

### **✅ Step Completion**
- Click "Mark Done" when you finish a step
- System asks: "How many hours did you spend?"
- Time is recorded for analytics
- Learned skills are added to your profile
- Progress percentage updates
- Next step unlocks

### **🚫 Blocker Reporting**
- Click "Report Issue" when stuck
- System asks: "What's the problem?" and "How long did you struggle?"
- First time: System offers tips and resources
- Second time: Warning sent, suggestions refined
- Third time: **Re-evaluation triggered automatically**

### **🔄 Re-evaluation Triggers**
Your system auto-checks when:
1. You block on same step **3+ times**
2. You have **2+ active blockers** at once
3. **Every 3 completed steps** (periodic check)
4. Your motivation **drops below 50%**

### **💡 Rerouting**
When re-evaluation is triggered:
- AI finds **top 3 alternative roles** matching your skills
- Shows market demand and entry barriers
- Shows roadmap preview
- You can **switch with 1 click**
- New roadmap keeps your learned skills

---

## Testing Checklist

Test the system completely by following this order:

```
□ Start backend: python api/main.py
□ Start frontend: streamlit run streamlit_app.py
□ Open http://localhost:8501

□ Submit assessment form
□ View roadmap
□ Start Step 1
□ Mark Step 1 complete (10 hours)
□ View updated progress %
□ Start Step 2
□ Report blocker on Step 2
□ Report blocker again (2nd time)
□ Report blocker again (3rd time) → Should trigger re-evaluation
□ View re-evaluation page
□ Click "Switch to [Alternative]"
□ Verify new roadmap generated
□ View dashboard with new target role
```

---

## API Endpoints Quick Reference

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Check API status |
| POST | `/api/assess` | Initial assessment |
| POST | `/api/progress` | Complete step / Report blocker |
| POST | `/api/reroute` | Switch career path |
| GET | `/api/journey/{id}/summary` | Get journey details |
| GET | `/api/user/{id}/journeys` | Get all user journeys |
| POST | `/api/journey/{id}/pause` | Pause learning |
| POST | `/api/journey/{id}/resume` | Resume learning |

---

## Data Structures

### **Assessment Request**
```json
{
  "user_id": "user_123",
  "user_name": "John Doe",
  "desired_role": "Data Analyst",
  "current_skills": "Python, SQL",
  "education": "Bachelor's",
  "experience": "2 years",
  "projects": "Built dashboards",
  "available_duration_weeks": 12
}
```

### **Step Completion Request**
```json
{
  "session_id": "uuid",
  "step_number": 1,
  "status": "completed",
  "time_spent_hours": 10.5
}
```

### **Blocker Report Request**
```json
{
  "session_id": "uuid",
  "step_number": 2,
  "status": "blocked",
  "blocker_reason": "Struggling with SQL joins",
  "time_spent_hours": 5.0
}
```

### **Reroute Request**
```json
{
  "session_id": "uuid",
  "reevaluation_id": 1,
  "chosen_role": "Business Analyst",
  "reason": "better_fit"
}
```

---

## Workflow Diagram

```
START
  │
  ├─→ [Assessment] ──→ Verdict + Roadmap
  │
  ├─→ [Learning Loop]
  │   ├─ Start Step
  │   ├─ Study Resources
  │   ├─ Mark Complete OR Report Blocker
  │   └─ Update Progress
  │
  ├─→ [Blocker Detection]
  │   └─ If 3+ attempts: Trigger Re-eval
  │
  ├─→ [Re-evaluation Page]
  │   ├─ Option A: Continue Current
  │   └─ Option B: Switch to Alternative
  │        └─ New Roadmap Generated
  │
  └─→ Continue Learning OR Start New Journey
```

---

## Status Indicators

### **Step Status Colors:**
- ⚪ **Not Started** - Gray
- 🔵 **In Progress** - Blue with play button
- 🟢 **Completed** - Green with checkmark
- 🔴 **Blocked** - Red with warning

### **Progress Percentage:**
- 0-25% → "Just getting started!"
- 25-50% → "Good progress!"
- 50-75% → "Halfway there!"
- 75-100% → "Almost done!"

### **Blocker Severity:**
- 1-2 attempts → Low (suggestions offered)
- 3+ attempts → High (re-evaluation triggered)
- 2+ different steps → High (re-evaluation triggered)

---

## Troubleshooting

### **"API Connection Failed"**
```bash
# Check backend is running
python api/main.py

# Should output:
# INFO:     Uvicorn running on http://127.0.0.1:8000
```

### **"Database Error"**
```bash
# Check PostgreSQL is running
# Check DB credentials in .env or API code
# Check schema is initialized
```

### **"Session Not Found"**
- Make sure you completed the assessment first
- Copy session_id from assessment response

### **"Re-evaluation Not Triggering"**
- You need exactly **3 blockers on same step** OR **2+ active blockers**
- Or complete 3 steps (periodic check)

### **"Can't Switch Careers"**
- Make sure re-evaluation is on the page
- Refresh dashboard after reroute
- Check new roadmap loaded

---

## Environment Variables

Create `.env` in `/Users/abdullah/AI Ignite/`:
```
GROQ_API_KEY=your_groq_api_key
DB_HOST=localhost
DB_NAME=career_agent
DB_USER=your_db_user
DB_PASSWORD=your_db_password
```

---

## Files Structure

```
/Users/abdullah/AI Ignite/
├── api/
│   └── main.py              # FastAPI application
├── agents/
│   ├── profile_analyzer.py  # AI agent
│   ├── market_intelligence.py
│   ├── feasibility_evaluator.py
│   ├── roadmap_generator.py
│   └── reroute_agent.py
├── database/
│   ├── db_manager.py        # Database operations
│   └── schema.sql
├── llm/
│   └── llm_client.py        # Groq API client
├── streamlit_app.py         # Frontend UI
├── orchestrator.py          # AI workflow coordinator
└── POSTMAN_GUIDE.md         # This file
```

---

## Performance Tips

1. **First assessment takes 3-8 seconds** (AI processing)
2. **Re-evaluations take 2-5 seconds**
3. **Step completion is instant** (<500ms)
4. **Blocker reports are instant** (<500ms)

---

## Next Steps

1. **Start both servers:**
   ```bash
   # Terminal 1
   python api/main.py
   
   # Terminal 2
   streamlit run streamlit_app.py
   ```

2. **Test the complete workflow** (see Testing Checklist above)

3. **Try different scenarios:**
   - Switch between career paths
   - Complete 3 steps to trigger periodic re-evaluation
   - Block on same step 3 times

4. **Check Postman Guide** for detailed API testing

5. **Read Workflow Guide** for architectural details

---

## Questions?

Refer to:
- `WORKFLOW_GUIDE.md` - Complete architecture & detailed flows
- `POSTMAN_GUIDE.md` - API endpoint examples & test sequences
- `api/main.py` - API code with docstrings
- `streamlit_app.py` - Frontend code with comments
