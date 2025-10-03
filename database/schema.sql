-- Kolb's Cycle MCP Server Database Schema
-- PostgreSQL 15+ Required for JSONB and Advanced Features

-- Drop existing tables if they exist (for clean reinstall)
DROP TABLE IF EXISTS experiment_recommendations CASCADE;
DROP TABLE IF EXISTS active_experiments CASCADE;
DROP TABLE IF EXISTS pattern_experiments CASCADE;
DROP TABLE IF EXISTS insights CASCADE;
DROP TABLE IF EXISTS experiments CASCADE;
DROP TABLE IF EXISTS behavioral_patterns CASCADE;

-- ============================================================================
-- TABLE 1: BEHAVIORAL_PATTERNS
-- Stores discovered patterns with evolving confidence scores
-- ============================================================================

CREATE TABLE behavioral_patterns (
    id SERIAL PRIMARY KEY,
    pattern_id VARCHAR(50) UNIQUE NOT NULL,
    discovered_date TIMESTAMP NOT NULL DEFAULT NOW(),
    pattern_type VARCHAR(20) NOT NULL CHECK (pattern_type IN ('behavioral', 'cognitive', 'emotional', 'systemic', 'temporal')),
    domains_affected TEXT[] NOT NULL,
    description TEXT NOT NULL,
    frequency VARCHAR(20) CHECK (frequency IN ('daily', 'weekly', 'situational', 'triggered')),

    -- JSONB for flexible nested data
    triggers JSONB DEFAULT '[]'::jsonb,
    consequences JSONB DEFAULT '{"positive": [], "negative": []}'::jsonb,

    -- Confidence tracking
    confidence_score NUMERIC(3,2) DEFAULT 0.30 CHECK (confidence_score BETWEEN 0 AND 1),
    evolution_history JSONB DEFAULT '[]'::jsonb,

    -- Relationships
    cross_references TEXT[],

    -- Analysis fields
    root_cause_hypothesis TEXT,
    intervention_success_rate NUMERIC(3,2) DEFAULT 0.00 CHECK (intervention_success_rate BETWEEN 0 AND 1),
    last_validated TIMESTAMP,
    status VARCHAR(20) DEFAULT 'hypothesis' CHECK (status IN ('hypothesis', 'testing', 'validated', 'refuted', 'dormant')),

    -- Extensibility
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- TABLE 2: EXPERIMENTS
-- Tracks experiments with daily observations
-- ============================================================================

CREATE TABLE experiments (
    id SERIAL PRIMARY KEY,
    experiment_id VARCHAR(50) UNIQUE NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'planned' CHECK (status IN ('planned', 'active', 'completed', 'paused', 'abandoned')),
    domain VARCHAR(20) NOT NULL CHECK (domain IN ('work', 'health', 'relationships', 'learning', 'personal')),

    -- Experiment design
    hypothesis TEXT NOT NULL,
    intervention TEXT NOT NULL,
    metrics JSONB DEFAULT '{"primary": [], "guardrail": []}'::jsonb,

    -- Daily tracking
    daily_observations JSONB DEFAULT '[]'::jsonb,

    -- Results
    outcome VARCHAR(20) CHECK (outcome IN ('success', 'partial', 'failure', 'ongoing')),
    confidence_gained TEXT,
    next_experiments TEXT[],
    success_probability NUMERIC(3,2) CHECK (success_probability BETWEEN 0 AND 1),
    actual_vs_expected TEXT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- TABLE 3: PATTERN_EXPERIMENTS
-- Many-to-many relationship between patterns and experiments
-- ============================================================================

CREATE TABLE pattern_experiments (
    pattern_id VARCHAR(50) REFERENCES behavioral_patterns(pattern_id) ON DELETE CASCADE,
    experiment_id VARCHAR(50) REFERENCES experiments(experiment_id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) CHECK (relationship_type IN ('discovered_from', 'targets', 'validates', 'refutes')),
    strength NUMERIC(3,2) CHECK (strength BETWEEN 0 AND 1),
    discovered_date TIMESTAMP DEFAULT NOW(),
    notes TEXT,
    PRIMARY KEY (pattern_id, experiment_id)
);

-- ============================================================================
-- TABLE 4: INSIGHTS
-- Breakthrough connections and key learnings
-- ============================================================================

CREATE TABLE insights (
    id SERIAL PRIMARY KEY,
    insight_id VARCHAR(50) UNIQUE NOT NULL,
    date TIMESTAMP NOT NULL DEFAULT NOW(),
    type VARCHAR(20) NOT NULL CHECK (type IN ('breakthrough', 'connection', 'refinement', 'warning')),
    description TEXT NOT NULL,

    -- Supporting evidence
    supporting_patterns TEXT[],
    supporting_experiments TEXT[],

    -- Actionability
    actionable_recommendations TEXT[],
    expected_impact TEXT,
    validation_status VARCHAR(20) DEFAULT 'hypothesis' CHECK (validation_status IN ('hypothesis', 'testing', 'validated', 'refuted')),
    importance_score INTEGER CHECK (importance_score >= 1 AND importance_score <= 10),

    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- TABLE 5: ACTIVE_EXPERIMENTS
-- Tracks currently running experiments for quick daily access
-- ============================================================================

CREATE TABLE active_experiments (
    user_id VARCHAR(255) DEFAULT 'default',
    experiment_id VARCHAR(50) REFERENCES experiments(experiment_id) ON DELETE CASCADE,
    activated_date TIMESTAMP DEFAULT NOW(),
    target_days INTEGER DEFAULT 7,
    current_day INTEGER DEFAULT 1,
    last_observation_date DATE,
    PRIMARY KEY (user_id, experiment_id)
);

-- ============================================================================
-- TABLE 6: EXPERIMENT_RECOMMENDATIONS
-- History of experiment recommendations for learning
-- ============================================================================

CREATE TABLE experiment_recommendations (
    id SERIAL PRIMARY KEY,
    session_date DATE NOT NULL,
    presented_experiments JSONB NOT NULL,
    selected_experiment VARCHAR(50),
    selection_reasoning TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- TABLE 7: SESSIONS
-- Tracks daily reflection sessions for consistency and gamification
-- ============================================================================

CREATE TABLE sessions (
    id SERIAL PRIMARY KEY,
    session_date DATE NOT NULL UNIQUE,
    session_number INTEGER NOT NULL,
    streak_day INTEGER NOT NULL,
    patterns_discovered INTEGER DEFAULT 0,
    patterns_updated INTEGER DEFAULT 0,
    observations_recorded INTEGER DEFAULT 0,
    experiments_created INTEGER DEFAULT 0,
    insights_created INTEGER DEFAULT 0,
    reflection_type VARCHAR(20) DEFAULT 'standard' CHECK (reflection_type IN ('standard', 'quick')),
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- Sub-second query performance requirement
-- ============================================================================

-- Behavioral Patterns Indexes
CREATE INDEX idx_patterns_confidence ON behavioral_patterns(confidence_score DESC);
CREATE INDEX idx_patterns_domains ON behavioral_patterns USING GIN(domains_affected);
CREATE INDEX idx_patterns_status ON behavioral_patterns(status) WHERE status IN ('validated', 'testing');
CREATE INDEX idx_patterns_triggers ON behavioral_patterns USING GIN(triggers);
CREATE INDEX idx_patterns_consequences ON behavioral_patterns USING GIN(consequences);
CREATE INDEX idx_patterns_metadata ON behavioral_patterns USING GIN(metadata);
CREATE INDEX idx_patterns_type_domain ON behavioral_patterns(pattern_type, domains_affected);

-- Experiments Indexes
CREATE INDEX idx_experiments_active ON experiments(status) WHERE status = 'active';
CREATE INDEX idx_experiments_domain ON experiments(domain, start_date DESC);
CREATE INDEX idx_experiments_status ON experiments(status, end_date DESC);
CREATE INDEX idx_daily_observations ON experiments USING GIN(daily_observations);
CREATE INDEX idx_experiments_date_range ON experiments(start_date, end_date) WHERE status IN ('active', 'completed');

-- Pattern-Experiment Relationships
CREATE INDEX idx_pattern_exp_pattern ON pattern_experiments(pattern_id);
CREATE INDEX idx_pattern_exp_experiment ON pattern_experiments(experiment_id);
CREATE INDEX idx_pattern_exp_type ON pattern_experiments(relationship_type);

-- Insights Indexes
CREATE INDEX idx_insights_date ON insights(date DESC);
CREATE INDEX idx_insights_type ON insights(type);
CREATE INDEX idx_insights_importance ON insights(importance_score DESC);
CREATE INDEX idx_insights_status ON insights(validation_status);

-- Active Experiments Indexes
CREATE INDEX idx_active_exp_user ON active_experiments(user_id);
CREATE INDEX idx_active_exp_last_obs ON active_experiments(last_observation_date);

-- Recommendations Indexes
CREATE INDEX idx_recommendations_date ON experiment_recommendations(session_date DESC);

-- Sessions Indexes
CREATE INDEX idx_sessions_date ON sessions(session_date DESC);
CREATE INDEX idx_sessions_number ON sessions(session_number DESC);
CREATE INDEX idx_sessions_streak ON sessions(streak_day DESC);

-- ============================================================================
-- TRIGGERS FOR AUTO-UPDATES
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for behavioral_patterns
CREATE TRIGGER update_patterns_updated_at
BEFORE UPDATE ON behavioral_patterns
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger for experiments
CREATE TRIGGER update_experiments_updated_at
BEFORE UPDATE ON experiments
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- HELPER VIEWS
-- ============================================================================

-- View for quick pattern summary
CREATE OR REPLACE VIEW pattern_summary AS
SELECT
    pattern_id,
    pattern_type,
    domains_affected,
    description,
    confidence_score,
    status,
    discovered_date,
    (SELECT COUNT(*) FROM pattern_experiments WHERE pattern_id = bp.pattern_id) as experiment_count
FROM behavioral_patterns bp
WHERE status IN ('hypothesis', 'testing', 'validated')
ORDER BY confidence_score DESC, discovered_date DESC;

-- View for active experiment dashboard
CREATE OR REPLACE VIEW active_experiment_dashboard AS
SELECT
    e.experiment_id,
    e.domain,
    e.hypothesis,
    e.intervention,
    ae.current_day,
    ae.target_days,
    (ae.target_days - ae.current_day) as days_remaining,
    ae.last_observation_date,
    CASE
        WHEN ae.last_observation_date < CURRENT_DATE THEN 'NEEDS_OBSERVATION'
        ELSE 'UP_TO_DATE'
    END as observation_status
FROM experiments e
JOIN active_experiments ae ON e.experiment_id = ae.experiment_id
WHERE e.status = 'active';

-- ============================================================================
-- INITIAL DATA / SEED (OPTIONAL)
-- ============================================================================

-- No seed data for fresh start

-- ============================================================================
-- SCHEMA VALIDATION
-- ============================================================================

-- Verify all tables were created
DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_type = 'BASE TABLE';

    RAISE NOTICE 'Created % tables', table_count;

    IF table_count < 7 THEN
        RAISE EXCEPTION 'Schema creation incomplete. Expected 7 tables, found %', table_count;
    END IF;
END $$;

RAISE NOTICE 'Kolb MCP Database Schema created successfully!';
RAISE NOTICE 'Tables: behavioral_patterns, experiments, pattern_experiments, insights, active_experiments, experiment_recommendations, sessions';
RAISE NOTICE 'Views: pattern_summary, active_experiment_dashboard';
RAISE NOTICE 'Indexes: Optimized for sub-second queries';
