# 🎓 Career Agent System - Complete Documentation

> **AI-Powered Career Guidance Platform with Real-time Progress Tracking and Adaptive Path Rerouting**

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Features](#features)
4. [Getting Started](#getting-started)
5. [Complete Workflow](#complete-workflow)
6. [API Reference](#api-reference)
7. [Troubleshooting](#troubleshooting)
8. [Project Structure](#project-structure)

---

## 📌 Overview

Career Agent is a **three-tier application** that uses AI to help users find and achieve their ideal career goals:

### **The Problem It Solves:**
- Users don't know if a career switch is realistic for them
- Career planning is vague and unmeasurable
- When users get stuck, they don't get personalized guidance
- Career paths need to adapt as users discover new interests

### **The Solution:**
A system that:
1. **Analyzes** your profile against market demands
2. **Creates** step-by-step learning roadmaps
3. **Detects** when you're struggling
4. **Suggests** better paths if needed
5. **Tracks** your complete journey

### **Key Statistics:**
- **8-12 learning steps** per career path
- **Auto re-evaluation** when 3+ blockers detected
- **AI-powered alternatives** when goal not feasible
- **Skill preservation** when switching careers
- **Real-time progress tracking** with time accounting

---

## 🏗️ System Architecture

### **Technology Stack:**

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Frontend** | Streamlit | Interactive web UI |
| **Backend** | FastAPI | REST API server |
| **Database** | PostgreSQL | Data persistence |
| **AI/LLM** | Groq API | Career analysis & suggestions |
| **Language** | Python 3.11+ | All services |

### **Service Architecture:**

```
┌─────────────────────────────────────────────────────────────┐
│                    STREAMLIT FRONTEND                        │
│                    Port 8501                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Home │ Dashboard │ Re-evaluation │ Analytics         │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬─────────────────────────────────────┘
                         │ HTTP REST API
        ┌────────────────┴──────────────────┐
        │                                   │
┌───────▼──────────────────────┐  ┌────────▼───────────────┐
│   FASTAPI BACKEND            │  │  POSTGRESQL DATABASE   │
│   Port 8000                  │  │  Port 5432             │
│                              │  │                        │
│ ┌────────────────────────┐   │  │ Tables:                │
│ │ Routes:                │   │  │ - users                │
│ │ /api/assess            │   │◄─┤ - journeys             │
│ │ /api/progress          │   │  │ - steps                │
│ │ /api/reroute           │   │  │ - blockers             │
│ │ /api/journey/{id}      │   │  │ - reevaluations        │
│ │ /api/user/{id}/journeys│   │  │ - reroutes             │
│ │ /api/journey/{id}/pause │  │  │ - skills_learned       │
│ │ /api/journey/{id}/resume│  │  │                        │
│ └────────────────────────┘   │  │                        │
│                              │  │                        │
│ ┌────────────────────────┐   │  │                        │
│ │ AI Orchestrator:       │   │  │                        │
│ │ - Profile Analyzer     │   │  │                        │
│ │ - Market Intelligence  │   │  │                        │
│ │ - Feasibility          │   │  │                        │
│ │ - Roadmap Generator    │   │  │                        │
│ │ - Reroute Agent        │   │  │                        │
│ └────────────────────────┘   │  │                        │
│                              │  │                        │
│ LLM Client (Groq API)        │  │                        │
└───────┬──────────────────────┘  └────────────────────────┘
        │
        │ HTTP(S)
        ▼
┌─────────────────────────────┐
│   GROQ LLM API              │
│   Claude/Llama Models       │
│   Remote Service            │
└─────────────────────────────┘
```

### **Data Flow:**

```
User Assessment → Profile Analysis → Market Intelligence
                       │                      │
                       ▼                      ▼
               User Profile Summary ← Market Demand Analysis
                       │
                       ▼
          Feasibility Evaluator
                  (VERDICT)
                   /  |  \
            FEASIBLE  CHALLENGING  NOT_FEASIBLE
               │         │              │
               ▼         ▼              ▼
           Roadmap  Roadmap +    Alternatives +
           Only     Alternatives  Roadmaps

                ↓ User Learning ↓

        Step Completion / Blocker Report
                   │
          ┌────────┼────────┐
          │        │        │
       Update  Trigger  Check Reevaluation
       Skills  Analysis  Conditions
```

---

## ✨ Features

### **1. Career Assessment** 🎯

**What it does:**
- Analyzes your skills, education, and experience
- Researches market demand for your target role
- Evaluates feasibility based on realistic factors
- Generates personalized learning roadmap

**Input:**
- Target career role
- Current skills
- Education & experience
- Available time

**Output:**
- Feasibility verdict (FEASIBLE/CHALLENGING/NOT_FEASIBLE)
- Personalized roadmap (8-12 steps)
- Market insights
- Learning resources per step

**AI Processing:**
```
Input Profile
    ↓
Profile Analyzer
    (Extracts strengths/weaknesses)
    ↓
Market Intelligence Agent
    (Researches job market)
    ↓
Feasibility Evaluator
    (Compares profile vs market)
    ↓
Roadmap Generator
    (Creates learning path)
    ↓
Output: Complete Career Plan
```

---

### **2. Progress Tracking** 📊

**What it does:**
- Records each step completion
- Tracks time spent learning
- Accumulates learned skills
- Calculates progress percentage

**Step Status Flow:**

```
NOT_STARTED
    │
    ├─ Click "Start Step"
    ▼
IN_PROGRESS
    │
    ├─ Study Resources (1-40 hours)
    │
    ├─ Option A: "Mark Done"
    │              ▼
    │          COMPLETED ✅
    │          (Skills added)
    │
    └─ Option B: "Report Issue"
                  ▼
              BLOCKED 🚫
              (Trigger help)
```

**Data Recorded:**
- Step completion timestamp
- Time spent learning
- Skills learned with proficiency level
- Resources used
- Difficulty rating

**Progress Calculation:**
```
Progress % = (Completed Steps / Total Steps) × 100

0-25%:   "Just getting started!"
25-50%:  "Good progress!"
50-75%:  "Halfway there!"
75-100%: "Almost done!"
```

---

### **3. Blocker Detection & Help** 🚫

**What it does:**
- Records when you get stuck
- Provides contextualized suggestions
- Triggers re-evaluation after multiple failures
- Offers alternative paths if needed

**Blocker Flow:**

```
User Gets Stuck on Step 2
    │
    ├─ 1st Attempt Blocked
    │   └─ System: "Here are resources to help"
    │
    ├─ 2nd Attempt Blocked
    │   └─ System: "Let me refine suggestions"
    │
    └─ 3rd Attempt Blocked
        └─ SYSTEM TRIGGERS RE-EVALUATION
            │
            ├─ "You might be better suited for..."
            ├─ Show alternatives
            └─ Offer career switch
```

**Blocker Data:**
- Problem description
- Attempt count
- Time before blocking
- Timestamp
- Suggested resources

---

### **4. Automatic Re-evaluation** 🔄

**What triggers it:**

```
1. PERFORMANCE (Same step blocked 3+ times)
2. MOTIVATION (Multiple different blockers)
3. PERIODIC (Every 3 completed steps)
4. TIME-BASED (Regular milestone checks)
```

**What happens:**

```
Re-evaluation Triggered
    │
    ├─ AI analyzes current situation
    ├─ Reviews learned skills
    ├─ Checks market trends
    ├─ Evaluates goal feasibility
    └─ Generates alternatives
    
    ▼
    
Display Options:
├─ Alternative 1: Role + Fit Score + Market Data
├─ Alternative 2: Role + Fit Score + Market Data
├─ Alternative 3: Role + Fit Score + Market Data
└─ Continue Current Path Option
```

---

### **5. Career Rerouting** 🎯➡️🎯

**What it does:**
- Generates new roadmap for alternative role
- Preserves learned skills
- Resets progress tracking
- Maintains learning history

**Reroute Process:**

```
User Clicks "Switch to Business Analyst"
    │
    ├─ Remove: Data Analyst roadmap
    ├─ Preserve: Learned skills (SQL, Python, etc.)
    ├─ Generate: Business Analyst roadmap
    ├─ Incorporate: Learned skills into new path
    ├─ Reset: Step progress to 0%
    └─ Record: Reroute in journey history
    
    ▼
    
New Dashboard Shows:
├─ Target Role: Business Analyst (Updated)
├─ Roadmap: 8 new steps
├─ Retained Skills: SQL, Python
├─ Progress: 0% (New journey)
└─ History: All previous learning preserved
```

**Skill Retention:**
- Previously learned skills appear in new roadmap
- Skips redundant learning steps
- Accelerates path to new role
- Calculates revised timeline

---

## 🚀 Getting Started

### **Prerequisites**

```bash
# Python 3.11+
python --version

# PostgreSQL 12+
psql --version

# Groq API Key (free)
# Get from: https://console.groq.com
```

### **Installation**

1. **Clone/Download Project**
   ```bash
   cd "/Users/abdullah/AI Ignite"
   ```

2. **Create Environment File**
   ```bash
   cat > .env << EOF
   GROQ_API_KEY=your_groq_api_key_here
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=career_agent
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   EOF
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize Database**
   ```bash
   psql -U your_db_user -d career_agent < database/schema.sql
   ```

5. **Verify Setup**
   ```bash
   # Check imports work
   python -c "from api.main import app; print('✅ Setup successful')"
   ```

### **Running the System**

**Terminal 1 - Backend API:**
```bash
cd "/Users/abdullah/AI Ignite"
python api/main.py

# Output:
# INFO:     Uvicorn running on http://127.0.0.1:8000
# INFO:     Application startup complete
```

**Terminal 2 - Frontend:**
```bash
cd "/Users/abdullah/AI Ignite"
streamlit run streamlit_app.py

# Output:
# You can now view your Streamlit app in your browser.
# Network URL: http://192.168.x.x:8501
# External URL: http://your-ip:8501
```

**Access:**
- 🌐 Frontend: http://localhost:8501
- 📡 API Docs: http://localhost:8000/docs
- 🔍 API ReDoc: http://localhost:8000/redoc

---

## 📖 Complete Workflow

### **Step 1: Initial Assessment** (3-8 seconds)

1. Open http://localhost:8501
2. Click "Analyze My Career Path"
3. Fill form:
   ```
   Target Role:          Data Analyst
   Current Skills:       Python, Excel, Basic SQL
   Education:            Bachelor's in Business
   Experience:           2 years in Finance
   Projects:             Created budget dashboard
   Available Duration:   12 weeks
   ```
4. Click "Analyze My Career"

5. **System outputs:**
   - ✅ Verdict: FEASIBLE / CHALLENGING / NOT_FEASIBLE
   - 📋 Personalized roadmap (8-12 steps)
   - 📊 Market insights
   - 📚 Learning resources per step
   - 🆔 Session ID created

### **Step 2: Learning Loop** (Multiple iterations)

For each step:

1. **Click "Start Step"**
   - Button changes to blue/in-progress
   - Study recommended resources
   - Track your time

2. **Option A: Mark Complete** ✅
   - Click "Mark Done"
   - Enter hours spent
   - System records:
     - Completion timestamp
     - Skills learned
     - Progress percentage
   - Move to next step

3. **Option B: Report Blocker** 🚫
   - Click "Report Issue"
   - Describe problem
   - Enter hours before blocking
   - System:
     - Records attempt
     - Shows suggestions
     - Checks if re-eval needed

### **Step 3: Re-evaluation Check** 🔄

**Automatic triggers:**
- 3rd blocker on same step
- 2+ active blockers
- Every 3 completed steps
- Periodic milestone check

**When triggered:**

1. System shows "Re-evaluation Page" banner
2. Click "View Re-evaluation"
3. See analysis:
   - Current situation assessment
   - Market conditions
   - Why system recommends re-eval
4. View alternatives:
   - Top 3 alternative roles
   - Match score for each
   - Market data (jobs, difficulty, fresher-friendly)
   - Roadmap preview

### **Step 4: Rerouting Decision** 🎯

**Option A: Switch Career** 🔄
1. Click "Switch to [Role]"
2. System generates new roadmap
3. Learned skills preserved
4. Progress resets (new journey)
5. Continue learning from Step 1

**Option B: Continue Current Path** ▶️
1. Click "Continue Current Path"
2. Return to dashboard
3. Resume learning from next step

---

## 📡 API Reference

### **Base URL:** `http://localhost:8000`

### **1. Health Check**
```
GET /health
```
**Response:**
```json
{
  "status": "ok",
  "timestamp": "2024-01-15T10:30:00",
  "message": "API is running"
}
```

### **2. Initial Assessment**
```
POST /api/assess
```
**Request:**
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
**Response:** Complete journey with roadmap
- `session_id`: UUID for tracking
- `target_role`: Confirmed target
- `feasibility_verdict`: FEASIBLE/CHALLENGING/NOT_FEASIBLE
- `student_profile`: Analyzed profile
- `market_snapshot`: Job market data
- `roadmap`: Array of learning steps
- `alternatives`: If not feasible

### **3. Update Progress**
```
POST /api/progress
```
**Request (Complete Step):**
```json
{
  "session_id": "uuid",
  "step_number": 1,
  "status": "completed",
  "time_spent_hours": 10.5
}
```
**Request (Report Blocker):**
```json
{
  "session_id": "uuid",
  "step_number": 2,
  "status": "blocked",
  "blocker_reason": "Struggling with SQL joins",
  "time_spent_hours": 5.0
}
```
**Response:**
```json
{
  "success": true,
  "step": {...},
  "should_reevaluate": false/true,
  "reevaluation": null or {...},
  "message": "..."
}
```

### **4. Accept Reroute**
```
POST /api/reroute
```
**Request:**
```json
{
  "session_id": "uuid",
  "reevaluation_id": 1,
  "chosen_role": "Business Analyst",
  "reason": "better_fit"
}
```
**Response:**
```json
{
  "success": true,
  "reroute_id": "uuid",
  "new_target_role": "Business Analyst",
  "new_roadmap": [...],
  "retained_skills": ["SQL", "Python"],
  "message": "Switched successfully!"
}
```

### **5. Get Journey Summary**
```
GET /api/journey/{session_id}/summary
```
**Response:**
```json
{
  "session_id": "uuid",
  "target_role": "Data Analyst",
  "progress_percentage": 25,
  "completed_steps": 1,
  "total_steps": 8,
  "steps": [...],
  "skills_learned": [...],
  "active_blockers": [...]
}
```

### **6. Get All Journeys**
```
GET /api/user/{user_id}/journeys
```
**Response:**
```json
{
  "user_id": "user_123",
  "total_journeys": 2,
  "journeys": [...]
}
```

### **7. Pause Journey**
```
POST /api/journey/{session_id}/pause
```
**Request:**
```json
{
  "reason": "Taking a break"
}
```

### **8. Resume Journey**
```
POST /api/journey/{session_id}/resume
```
**Request:**
```json
{
  "reason": "Ready to continue"
}
```

---

## 🔧 Troubleshooting

### **"API Connection Failed"**

**Check 1:** Backend is running?
```bash
ps aux | grep "python api/main.py"
```
If not running:
```bash
python api/main.py
```

**Check 2:** Correct port (8000)?
```bash
lsof -i :8000
```

**Check 3:** Firewall blocking?
```bash
# Allow port 8000
sudo ufw allow 8000
```

---

### **"Database Connection Error"**

**Check 1:** PostgreSQL running?
```bash
# macOS
brew services list | grep postgres

# Linux
sudo systemctl status postgresql

# Windows
services.msc (look for PostgreSQL)
```

**Check 2:** Database exists?
```bash
psql -l | grep career_agent
```

Create if missing:
```bash
createdb career_agent
psql career_agent < database/schema.sql
```

**Check 3:** Correct credentials?
```bash
psql -U your_db_user -d career_agent -c "SELECT 1"
```

---

### **"Session Not Found"**

- Check session_id copied correctly from assessment response
- Create new assessment if session expired
- Check database for `SELECT * FROM journeys WHERE session_id='...'`

---

### **"Re-evaluation Not Triggering"**

Re-evaluation needs:
- **3 blockers on SAME step** OR
- **2+ blockers on DIFFERENT steps** OR
- **3 steps completed** (periodic) OR
- **Motivation < 50%**

Test by reporting blockers multiple times on same step.

---

### **"Can't Switch Careers"**

- Make sure re-evaluation was triggered
- Check "Re-evaluation" page shows alternatives
- Refresh dashboard after clicking "Switch"
- Check new roadmap in /api/journey/{id}/summary

---

## 📁 Project Structure

```
/Users/abdullah/AI Ignite/
│
├── api/
│   ├── main.py              # FastAPI app (9 endpoints)
│   └── __pycache__/
│
├── agents/
│   ├── __init__.py
│   ├── profile_analyzer.py  # Analyzes user profile
│   ├── market_intelligence.py # Research job market
│   ├── feasibility_evaluator.py # Check goal feasibility
│   ├── roadmap_generator.py  # Create learning path
│   ├── reroute_agent.py      # Find alternatives
│   ├── progress_tracker.py   # Track learning progress
│   └── __pycache__/
│
├── database/
│   ├── db_manager.py         # Database operations
│   ├── schema.sql            # Database schema
│   └── __pycache__/
│
├── llm/
│   ├── llm_client.py         # Groq API wrapper
│   ├── SETUP.md              # LLM setup guide
│   └── __pycache__/
│
├── data/
│   ├── job_market.json       # Job market data
│   ├── career_paths.json     # Career descriptions
│   ├── learning_resources.json # Resource links
│   └── skills_taxonomy.json  # Skill categories
│
├── streamlit_app.py          # Streamlit UI
├── orchestrator.py           # AI workflow coordinator
├── requirements.txt          # Python dependencies
├── test_scenarios.py         # Test cases
├── simple_test.py            # Quick test
│
├── WORKFLOW_GUIDE.md         # Complete workflow doc
├── POSTMAN_GUIDE.md          # API testing guide
├── QUICK_START.md            # Quick reference
└── README.md                 # This file
```

---

## 📊 Database Schema

### **users**
```sql
id, user_id (PK), user_name, email, created_at
```

### **journeys**
```sql
session_id (PK), user_id (FK), desired_role, target_role,
student_profile, market_snapshot, roadmap, feasibility_verdict,
status, created_at, updated_at
```

### **steps**
```sql
id, session_id (FK), step_number, title, description,
estimated_hours, resources, skills_gained,
status, started_at, completed_at, time_spent_hours
```

### **blockers**
```sql
id, session_id (FK), step_number, blocker_reason,
attempt_count, first_blocked_at, last_blocked_at
```

### **reevaluations**
```sql
id, session_id (FK), trigger_type, trigger_severity,
action_taken, alternatives_suggested, created_at
```

### **reroutes**
```sql
id, session_id (FK), from_role, to_role, reason_type,
new_roadmap, created_at
```

### **skills_learned**
```sql
id, session_id (FK), skill_name, proficiency_level, date_learned
```

---

## 📚 Additional Resources

- **[Quick Start Guide](./QUICK_START.md)** - Fast reference
- **[Workflow Guide](./WORKFLOW_GUIDE.md)** - Detailed flows & diagrams
- **[Postman Guide](./POSTMAN_GUIDE.md)** - API testing examples

---

## 🎯 Use Cases

### **Career Switcher**
```
Goal: Become a Data Analyst
Timeline: 12 weeks
Result: Personalized roadmap, progress tracking, support
```

### **Early Career Professional**
```
Goal: Transition to Tech Management
Timeline: 6 months
Result: Skill gaps identified, rerouted to better path
```

### **Upskilling**
```
Goal: Add AI/ML skills
Timeline: 3 months
Result: Focused learning plan, blocker support
```

### **Career Exploration**
```
Goal: Explore multiple paths
Timeline: Open-ended
Result: Compare feasibility, find best fit
```

---

## 🚢 Production Deployment

### **Recommended Setup:**

1. **Frontend:** Deploy Streamlit to cloud (Heroku, Streamlit Cloud, AWS)
2. **Backend:** Deploy FastAPI to cloud (AWS, DigitalOcean, Heroku)
3. **Database:** Managed PostgreSQL (AWS RDS, DigitalOcean, Azure)
4. **API Keys:** Use environment variables (AWS Secrets Manager, GitHub Secrets)

### **Docker Deployment:**

```dockerfile
# Backend Dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "api/main.py"]
```

```dockerfile
# Frontend Dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["streamlit", "run", "streamlit_app.py"]
```

---

## 📝 License

This project is for educational purposes. Free to use and modify.

---

## ✅ Checklist Before Production

- [ ] All endpoints tested with Postman
- [ ] Database schema initialized
- [ ] Environment variables set
- [ ] Error handling implemented
- [ ] API rate limiting added
- [ ] Logging configured
- [ ] Security headers enabled
- [ ] CORS configured properly
- [ ] Database backups automated
- [ ] Monitoring set up

---

**Built with ❤️ for career development**

Last Updated: January 2024
Version: 1.0.0
