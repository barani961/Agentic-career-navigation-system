# 🎓 Career Agent System - Complete Workflow Guide

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Streamlit)                     │
│                  http://localhost:8501                       │
│  [Assessment] → [Dashboard] → [Progress] → [Re-evaluation]  │
└────────────────────────┬────────────────────────────────────┘
                         │
              ┌──────────┴──────────┐
              │                     │
        ┌─────▼──────────┐    ┌────▼────────────┐
        │  Backend API   │    │   PostgreSQL    │
        │  (FastAPI)     │◄──►│   Database      │
        │  :8000         │    │                 │
        └────────────────┘    └─────────────────┘
              ▲
              │
        ┌─────┴──────────┐
        │                │
   ┌────▼──────┐   ┌────▼──────┐
   │  AI Agents│   │ Groq API   │
   │  (Local)  │   │ (LLM)      │
   └───────────┘   └────────────┘
```

---

## Complete User Journey

### **Phase 1: Initial Assessment** 🎯
**Location:** Home Page

```
User Input:
├─ Target Career Role (e.g., "Data Analyst")
├─ Current Skills (e.g., "Python, SQL")
├─ Education Background
├─ Work Experience
├─ Projects
└─ Available Time (4-24 weeks)

↓

AI Processing:
1. Profile Analysis Agent
   - Extracts skills
   - Assesses experience level
   - Identifies strengths/weaknesses
   
2. Market Intelligence Agent
   - Analyzes job market for role
   - Checks demand, salary, skills needed
   - Calculates skill match
   
3. Feasibility Evaluator
   - Compares profile vs market needs
   - Calculates feasibility score
   - Returns: FEASIBLE / CHALLENGING / NOT_FEASIBLE
   
4. Roadmap Generator
   - Creates personalized learning path
   - Breaks down into manageable steps
   - Adds resources for each step

↓

Output:
├─ Verdict (FEASIBLE/CHALLENGING/NOT_FEASIBLE)
├─ Target Role
├─ Personalized Roadmap
├─ Market Insights
├─ Alternative Paths (if not feasible)
└─ Session ID (for tracking)

↓

Database Storage:
- Journey created
- Roadmap saved
- Profile captured
- Market snapshot recorded
```

---

### **Phase 2: Learning Progress** 📚
**Location:** Dashboard → Roadmap Tab

#### **Step Status Flow:**

```
NOT_STARTED
     │
     ▼
IN_PROGRESS ◄──────────────┐
     │                     │
     ├─► COMPLETED         │
     │        │            │
     │        ▼            │
     │    Progress Update  │
     │    - Time tracked   │
     │    - Skills earned  │
     │                     │
     └─► BLOCKED ──────────┘
              │
              ▼
        Report Blocker
        - Issue reason
        - Time spent
        - Triggers AI Review
```

#### **Completing a Step:**

1. **Click "Mark Done"** on in-progress step
2. **Enter time spent** (hours dedicated)
3. **API Call:** `POST /api/progress`
   ```json
   {
     "session_id": "uuid",
     "step_number": 1,
     "status": "completed",
     "time_spent_hours": 10.5
   }
   ```
4. **Database Updates:**
   - Records completion timestamp
   - Adds learned skills
   - Updates progress percentage
   - Checks re-evaluation triggers

#### **Reporting a Blocker:**

1. **Click "Report Issue"** on in-progress step
2. **Describe the problem** (text area)
3. **Enter time spent** before getting blocked
4. **API Call:** `POST /api/progress`
   ```json
   {
     "session_id": "uuid",
     "step_number": 2,
     "status": "blocked",
     "blocker_reason": "Struggling with SQL joins...",
     "time_spent_hours": 5.0
   }
   ```
5. **Database Updates:**
   - Records blocker
   - Increments attempt counter
   - Flags for re-evaluation if needed

---

### **Phase 3: Re-Evaluation & Rerouting** 🔄
**Location:** Re-evaluation Page (Auto-triggered)

#### **When is Re-evaluation Triggered?**

```
1. PERFORMANCE Issues:
   ├─ Multiple blockers (2+)
   └─ Same step blocked 3+ times

2. MOTIVATION Issues:
   └─ Motivation drops below 50%

3. PERIODIC CHECK:
   └─ Every 3 completed steps

4. TIME-BASED:
   └─ Regular progress reviews
```

#### **Re-evaluation Process:**

```
Trigger Event
    │
    ▼
AI Re-evaluation Analysis:
    ├─ Compare current skills vs target role needs
    ├─ Check market trends
    ├─ Assess feasibility of continuing
    ├─ Identify better alternatives
    └─ Calculate match scores
    
    ▼
    
Two Paths:

PATH A: Switch Career
├─ Show ranked alternatives
├─ Display market data for each
├─ Show preview roadmaps
└─ User clicks "Switch to [Role]"
       │
       ▼
   Reroute Agent activates:
   ├─ Generates new roadmap
   ├─ Incorporates learned skills
   ├─ Preserves progress
   └─ Updates target role
       │
       ▼
   Database Updates:
   ├─ Creates reroute record
   ├─ Links to re-evaluation
   ├─ Resets step progress
   └─ Saves new roadmap

PATH B: Continue Current
└─ User clicks "Continue Current Path"
     │
     ▼
 Return to Dashboard
 Resume learning
```

#### **Reroute API Call:**

```json
POST /api/reroute
{
  "session_id": "uuid",
  "reevaluation_id": 1,
  "chosen_role": "Data Engineer",
  "reason": "better_fit"
}
```

**Response:**
```json
{
  "success": true,
  "reroute_id": "uuid",
  "message": "Successfully switched to Data Engineer!",
  "new_target_role": "Data Engineer",
  "new_roadmap": [...],
  "journey": {...}
}
```

---

## Feature Implementation Details

### **1. Step Completion Workflow** ✅

```python
# Frontend Actions:
1. User clicks "Mark Done" button
2. Input form appears asking for hours spent
3. User confirms with "Confirm Complete" button
4. complete_step_api() called

# Backend Processing:
1. API receives POST /api/progress with status="completed"
2. Database records completion
3. Adds skills from this step to user's learned_skills
4. Checks re-evaluation triggers
5. Returns should_reevaluate flag

# Frontend Handling:
1. If should_reevaluate=true:
   - Store reevaluation data in session state
   - Set page to "reevaluation"
   - Show re-evaluation page
2. Else:
   - Show success message
   - Refresh dashboard
   - Update step status to "completed"
```

### **2. Blocker Reporting Workflow** 🚫

```python
# Frontend Actions:
1. User clicks "Report Issue" button
2. Form appears with:
   - Text area for problem description
   - Number input for hours spent
3. User submits form
4. report_blocker_api() called

# Backend Processing:
1. API receives POST /api/progress with status="blocked"
2. Database records blocker with:
   - Reason/description
   - Attempt count
   - Timestamp
3. Checks re-evaluation triggers:
   - If attempts >= 3: TRIGGER re-evaluation
   - If multiple blockers: TRIGGER re-evaluation
4. Returns should_reevaluate flag

# Frontend Handling:
1. If should_reevaluate=true:
   - Warn user: "Re-evaluation triggered!"
   - Store reevaluation data
   - Show re-evaluation page
2. Else:
   - Show warning: "Blocker recorded"
   - Refresh dashboard
   - Update step status to "blocked"
```

### **3. Re-evaluation & Rerouting Workflow** 🔄

```python
# Trigger Event → Re-evaluation Page

# AI Agent Processing:
orch.reroute_agent.find_alternatives():
  ├─ Analyze student profile
  ├─ Get current skills
  ├─ Compare with market data
  ├─ Rank alternative roles
  └─ Generate roadmaps for top 3 alternatives

# Frontend Display:
For each alternative:
  ├─ Role name with match score
  ├─ Justification for recommendation
  ├─ Market insights
  │  ├─ Active job count
  │  ├─ Entry barrier
  │  └─ Fresher-friendly status
  ├─ Preview roadmap
  └─ "Switch to [Role]" button

# User Selection → Switch to Alternative

# Reroute API Processing:
1. Receives chosen_role and reevaluation_id
2. Generates new roadmap for chosen_role
3. Incorporates learned skills
4. Saves reroute record to database
5. Updates journey target_role
6. Resets step progress
7. Returns updated roadmap

# Frontend Confirmation:
1. Show success message
2. Display "Switched to [Role]"
3. Show balloons animation
4. Return to dashboard with new roadmap
```

---

## Database Schema Impact

### **Tables Updated During Workflow:**

```sql
-- Phase 1: Initial Assessment
INSERT INTO journeys (
  user_id, desired_role, target_role,
  student_profile, market_snapshot, roadmap,
  feasibility_verdict, status
);
INSERT INTO users (user_id); -- If new

-- Phase 2: Learning Progress
INSERT INTO steps (session_id, step_number, status, ...);
INSERT INTO skills_learned (session_id, skill_name, ...);
INSERT INTO blockers (session_id, step_number, reason, ...);

-- Phase 3: Re-evaluation & Rerouting
INSERT INTO reevaluations (
  session_id, trigger_type, trigger_severity,
  action_taken, alternatives_suggested, ...
);
INSERT INTO reroutes (
  session_id, from_role, to_role,
  reason_type, new_roadmap, ...
);
UPDATE journeys SET
  target_role = new_role,
  feasibility_verdict = new_verdict
WHERE session_id = ?;
```

---

## UI Flow & Components

### **Home Page Components:**
- Role input field
- Skills text area
- Education input
- Experience text area
- Projects list
- Duration slider
- "Analyze My Career Path" button

### **Dashboard Components:**
- Progress metrics (4 cards)
- Active blockers alert
- Tabs:
  1. **Roadmap Tab**
     - Step cards (color-coded)
     - Status badges
     - Action buttons (Start/Mark Done/Report Issue)
     - Inline forms for completion/blockers
     - Resource links
  
  2. **Skills Learned Tab**
     - Skills grouped by proficiency level
     - Skill badges
  
  3. **Blockers Tab**
     - Active blocker list
     - Blocker details
     - Resolution options
  
  4. **Analytics Tab**
     - Journey metrics
     - Progress timeline
     - Re-evaluation history

### **Re-evaluation Page Components:**
- Issue alerts (color-coded by severity)
- Message from AI
- Alternative paths cards:
  - Role name & match score
  - Justification
  - Market metrics
  - "Switch" button
  - Roadmap preview
- "Continue Current Path" option

### **Sidebar Navigation:**
- Session ID display
- Navigation buttons
- New assessment option
- Settings (API URL)

---

## Status Codes & Error Handling

### **Success States:**
- ✅ Step completed → Success message + refresh
- 🚫 Blocker reported → Warning + refresh
- 🔄 Reroute successful → Success + balloons + redirect
- ⚠️ Re-evaluation triggered → Warning + navigate

### **Error States:**
- ❌ API connection failed → Error message + retry
- ❌ Invalid input → Field validation error
- ❌ Session expired → Redirect to home
- ❌ Database error → User-friendly error message

---

## Testing Checklist

### **Assessment Phase:**
- [ ] Submit assessment form
- [ ] Verify session_id created
- [ ] Check roadmap generated
- [ ] Verify verdict displayed

### **Progress Tracking:**
- [ ] Mark step as completed
- [ ] Verify time recorded
- [ ] Check skills updated
- [ ] Report blocker on step
- [ ] Verify blocker recorded

### **Re-evaluation:**
- [ ] Complete 3 steps to trigger periodic check
- [ ] Report multiple blockers to trigger re-evaluation
- [ ] Verify re-evaluation page shows
- [ ] View alternative paths
- [ ] Switch to alternative role
- [ ] Verify new roadmap generated
- [ ] Continue current path

### **Navigation:**
- [ ] Switch between Dashboard/Re-evaluation tabs
- [ ] Start new assessment
- [ ] Session state persists correctly
- [ ] API health check works

---

## Environment Setup

### **Terminal 1 - Backend API:**
```bash
cd "/Users/abdullah/AI Ignite/api"
export GROQ_API_KEY='your_key'
export DB_HOST=localhost
export DB_NAME=career_agent
export DB_USER=abdullah
export DB_PASSWORD=''
python main.py
```

### **Terminal 2 - Frontend:**
```bash
cd "/Users/abdullah/AI Ignite"
export API_BASE='http://localhost:8000'
streamlit run streamlit_app.py
```

### **Access:**
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:8501

---

## Complete Feature Summary

| Feature | Status | API Endpoint | Trigger |
|---------|--------|--------------|---------|
| **Assessment** | ✅ | POST /api/assess | Home page button |
| **Step Completion** | ✅ | POST /api/progress | Mark Done button |
| **Blocker Reporting** | ✅ | POST /api/progress | Report Issue button |
| **Re-evaluation** | ✅ | Internal | Auto-triggered |
| **Rerouting** | ✅ | POST /api/reroute | Switch button |
| **Progress Tracking** | ✅ | GET /api/journey/{id}/summary | Auto-refresh |
| **Skills Tracking** | ✅ | Database | Step completion |
| **Analytics** | ✅ | GET /api/journey/{id}/summary | Dashboard tab |

---

## Next Steps for Production

1. **Authentication:** Add user login/signup
2. **Notifications:** Email/SMS for milestones
3. **Mobile App:** React Native version
4. **Advanced Analytics:** Dashboard with charts
5. **Mentor Integration:** Connect with mentors
6. **Certificate System:** Issue completion certificates
7. **Social Features:** Share progress, leaderboards
8. **Content Recommendations:** ML-based resource suggestions
