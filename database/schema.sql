-- Career Agent System - PostgreSQL Database Schema
-- This stores all student journeys, progress, and re-evaluations

-- Table 1: Users (optional - if you have user authentication)
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE,
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Table 2: Student Journeys (main table)
CREATE TABLE IF NOT EXISTS journeys (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- Role information
    desired_role VARCHAR(255) NOT NULL,  -- What student originally wanted
    target_role VARCHAR(255) NOT NULL,   -- What they're currently pursuing
    
    -- Student data (stored as JSONB for flexibility)
    student_profile JSONB NOT NULL,      -- Full profile from ProfileAnalyzer
    market_snapshot JSONB NOT NULL,      -- Market data when journey started
    roadmap JSONB NOT NULL,              -- Array of roadmap steps
    
    -- Progress tracking
    total_steps INTEGER NOT NULL,
    current_step INTEGER DEFAULT 0,
    completed_steps INTEGER[] DEFAULT '{}',  -- Array of completed step numbers
    
    -- Status
    status VARCHAR(50) DEFAULT 'active',  -- active, paused, completed, abandoned
    feasibility_verdict VARCHAR(50),      -- FEASIBLE, CHALLENGING, NOT_FEASIBLE
    
    -- Motivation tracking
    motivation_level DECIMAL(3,2) DEFAULT 1.0,  -- 0.0 to 1.0
    
    -- Timestamps
    start_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completion_date TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 3: Step Progress
CREATE TABLE IF NOT EXISTS step_progress (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES journeys(session_id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    
    -- Status: not_started, in_progress, completed, blocked, skipped
    status VARCHAR(50) NOT NULL DEFAULT 'not_started',
    
    -- Time tracking
    time_spent_hours DECIMAL(10,2) DEFAULT 0.0,
    estimated_hours DECIMAL(10,2),
    
    -- Timestamps
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Metadata
    notes TEXT,  -- Student's notes on this step
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(session_id, step_number)
);

-- Table 4: Blockers
CREATE TABLE IF NOT EXISTS blockers (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES journeys(session_id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    
    -- Blocker details
    reason TEXT NOT NULL,
    category VARCHAR(100),  -- skill_difficulty, time_constraint, motivation, technical
    attempts INTEGER DEFAULT 1,
    
    -- Alternate paths (stored as JSONB)
    alternate_paths JSONB,  -- Array of alternative approaches/roadmaps for this blocker
    
    -- Status
    resolved BOOLEAN DEFAULT FALSE,
    resolution_note TEXT,
    
    -- Timestamps
    first_reported TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_reported TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 5: Re-evaluations (when system checks if path is still optimal)
CREATE TABLE IF NOT EXISTS reevaluations (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES journeys(session_id) ON DELETE CASCADE,
    
    -- What triggered re-evaluation
    trigger_type VARCHAR(100) NOT NULL,  -- performance, market_decline, new_opportunities, slow_progress
    trigger_severity VARCHAR(50),        -- low, medium, high, critical
    trigger_details JSONB,               -- Detailed trigger information
    
    -- Re-evaluation results
    action_taken VARCHAR(100) NOT NULL,  -- continue, suggest_reroute, adjust_timeline
    market_comparison JSONB,             -- Old vs new market data
    alternatives_suggested JSONB,        -- Array of alternative roles
    
    -- Student response
    student_decision VARCHAR(100),       -- continue_current, switch_role, pause, null (pending)
    decision_date TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 6: Reroutes (when student actually changes their target role)
CREATE TABLE IF NOT EXISTS reroutes (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES journeys(session_id) ON DELETE CASCADE,
    
    -- Path change
    from_role VARCHAR(255) NOT NULL,
    to_role VARCHAR(255) NOT NULL,
    
    -- Why reroute happened
    reason_type VARCHAR(100) NOT NULL,  -- infeasible, struggling, better_opportunity, student_choice
    reason_details TEXT,
    
    -- New path
    new_roadmap JSONB NOT NULL,
    new_market_snapshot JSONB,
    
    -- Timestamps
    reroute_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 7: Skills Learned (track what student has actually learned)
CREATE TABLE IF NOT EXISTS skills_learned (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES journeys(session_id) ON DELETE CASCADE,
    
    skill_name VARCHAR(255) NOT NULL,
    proficiency_level VARCHAR(50),  -- beginner, intermediate, advanced
    
    -- Evidence
    learned_from_step INTEGER,
    project_proof TEXT,  -- Link to GitHub, portfolio, etc.
    
    -- Verification
    self_assessed BOOLEAN DEFAULT TRUE,
    verified_by VARCHAR(100),  -- Could be quiz, project review, etc.
    
    learned_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(session_id, skill_name)
);

-- Table 8: Market Data Snapshots (track how market changes over time)
CREATE TABLE IF NOT EXISTS market_snapshots (
    id SERIAL PRIMARY KEY,
    role_name VARCHAR(255) NOT NULL,
    
    -- Market metrics
    total_jobs INTEGER,
    demand_score INTEGER,
    trend VARCHAR(50),
    growth_rate DECIMAL(5,2),
    entry_barrier DECIMAL(3,2),
    
    -- Timestamp
    snapshot_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Full data
    full_data JSONB
);

-- Table 9: Activity Log (audit trail)
CREATE TABLE IF NOT EXISTS activity_log (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES journeys(session_id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    
    action VARCHAR(255) NOT NULL,  -- journey_started, step_completed, blocker_reported, etc.
    details JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_journeys_user_id ON journeys(user_id);
CREATE INDEX IF NOT EXISTS idx_journeys_status ON journeys(status);
CREATE INDEX IF NOT EXISTS idx_journeys_target_role ON journeys(target_role);
CREATE INDEX IF NOT EXISTS idx_step_progress_session ON step_progress(session_id);
CREATE INDEX IF NOT EXISTS idx_blockers_session ON blockers(session_id);
CREATE INDEX IF NOT EXISTS idx_blockers_resolved ON blockers(resolved);
CREATE INDEX IF NOT EXISTS idx_reevaluations_session ON reevaluations(session_id);
CREATE INDEX IF NOT EXISTS idx_reroutes_session ON reroutes(session_id);
CREATE INDEX IF NOT EXISTS idx_skills_learned_session ON skills_learned(session_id);
CREATE INDEX IF NOT EXISTS idx_market_snapshots_role ON market_snapshots(role_name);
CREATE INDEX IF NOT EXISTS idx_activity_log_session ON activity_log(session_id);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_journeys_updated_at BEFORE UPDATE ON journeys
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_step_progress_updated_at BEFORE UPDATE ON step_progress
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();