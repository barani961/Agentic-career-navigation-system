# 🚀 SETUP GUIDE - Career Agent System

## Step 1: Install Dependencies

```bash
pip install groq
```

That's it! Only one dependency needed.

---

## Step 2: Get Groq API Key

### 🔑 Where to get your API key:

1. **Go to**: https://console.groq.com/keys
2. **Sign up** (free account)
3. **Create new API key**
4. **Copy the key** (looks like: `gsk_xxxxxxxxxxxxx`)

### Free Tier Limits:
- ✅ **14,400 requests per day**
- ✅ **30 requests per minute**
- ✅ **More than enough for testing and demos!**

---

## Step 3: Set Your API Key

### Option A: Environment Variable (Recommended)

**Linux/Mac:**
```bash
export GROQ_API_KEY='your_api_key_here'
```

**Windows (Command Prompt):**
```cmd
set GROQ_API_KEY=your_api_key_here
```

**Windows (PowerShell):**
```powershell
$env:GROQ_API_KEY = "your_api_key_here"
```

### Option B: Pass Directly in Code

```python
from llm.llm_client import LLMClient

# Pass API key directly
llm = LLMClient(api_key="your_api_key_here")
```

---

## Step 4: Test Your Setup

```bash
# Test the LLM client
python llm/llm_client.py
```

**Expected output:**
```
==================================================
GROQ LLM CLIENT TEST
==================================================

✅ API key found!
✅ Client initialized successfully!

📤 Sending test prompt...

✅ Response received:
{
  "skills": ["SQL", "Excel", "Python"]
}

==================================================
✅ ALL TESTS PASSED!
==================================================
```

---

## Step 5: Run the Full System Test

```bash
python test_agents.py
```

This will run 3 test scenarios:
1. ✅ Feasible career path (Data Analyst)
2. 🔄 Reroute scenario (ML Engineer → Data Analyst)
3. 📊 Progress tracking

---

## 📁 Project Structure

```
career_agent/
├── agents/                    # All 6 agent files
│   ├── profile_analyzer.py
│   ├── market_intelligence.py
│   ├── feasibility_evaluator.py
│   ├── roadmap_generator.py
│   ├── reroute_agent.py
│   └── progress_tracker.py
│
├── data/                      # Your hardcoded JSON data
│   ├── job_market.json        ✅ Already created!
│   ├── career_paths.json      ✅ Already created!
│   ├── skills_taxonomy.json   ✅ Already created!
│   └── learning_resources.json ✅ Already created!
│
├── llm/
│   └── llm_client.py          # Groq client
│
├── orchestrator.py            # Main coordinator
├── test_agents.py             # Test script
└── requirements.txt           # Just: groq
```

---

## 🎯 Quick Start Example

```python
from llm.llm_client import LLMClient
from orchestrator import CareerAgentOrchestrator, load_data_files

# 1. Initialize LLM
llm = LLMClient()  # Uses GROQ_API_KEY from environment

# 2. Load data
job_market, career_paths, skills_taxonomy, learning_resources = load_data_files()

# 3. Create orchestrator
orchestrator = CareerAgentOrchestrator(
    llm_client=llm,
    job_market_data=job_market,
    career_paths_data=career_paths,
    skills_taxonomy=skills_taxonomy,
    learning_resources=learning_resources
)

# 4. Get career guidance
result = orchestrator.process_student_query(
    desired_role="Data Analyst",
    skills_text="I know Python basics and SQL",
    education="3rd year B.Tech Computer Science",
    projects=["Data visualization dashboard"],
    duration_weeks=12
)

print(f"Verdict: {result['verdict']}")
print(f"Roadmap steps: {len(result['roadmap']['roadmap'])}")
```

---

## 🐛 Troubleshooting

### Error: "Groq API key not found"
**Fix**: Set your API key (see Step 3)

### Error: "groq library not installed"
**Fix**: `pip install groq`

### Error: "Role not found in market data"
**Fix**: Check that the role name exists in `data/job_market.json`

### LLM returns invalid JSON
**Fix**: This is rare but can happen. The code has fallback logic to handle this.

---

## 📊 Data Files

All 4 JSON files are already created with your data structure:

### ✅ job_market.json
- Contains 16 roles (Data Analyst, Software Engineer, ML Engineer, etc.)
- Skills, salary, market trends, entry barriers

### ✅ career_paths.json
- Career progression paths
- Stepping stones between roles
- Transition probabilities

### ✅ skills_taxonomy.json
- Standardized skill names
- Aliases for matching
- Learning weeks and difficulty

### ✅ learning_resources.json
- Free learning resources
- Project ideas for each role
- Curated links

---

## 🎓 For Your Hackathon

### Time Estimate:
- ✅ Data creation: **Already done!**
- ⏱️ Testing: **15-30 minutes**
- 🎨 Building UI: **2-4 hours** (if needed)

### Recommended Demo Flow:
1. **Persona 1**: Beginner student → Data Analyst (Feasible)
2. **Persona 2**: Beginner student → ML Engineer (Reroute to Data Analyst)
3. **Persona 3**: Show progress tracking with blocker

### Next Steps:
- Test with `python test_agents.py`
- Build a Streamlit UI (optional)
- Add more roles to data files (optional)

---

## 🔥 Key Features to Highlight

✅ **Market-driven decisions** - Real job market data
✅ **Intelligent rerouting** - Not just "No" but "Here's a better path"
✅ **Personalized roadmaps** - Step-by-step with resources
✅ **Progress tracking** - Adaptive re-evaluation
✅ **Minimal LLM usage** - Only 3-6 API calls per journey

---

## 📧 Support

All code is ready to run. Just:
1. Set your Groq API key
2. Run `python test_agents.py`
3. Start building!

**Good luck with your hackathon! 🚀**