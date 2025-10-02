"""SQL query constants for all database operations.

All queries use parameterized statements to prevent SQL injection.
Parameters are marked with $1, $2, etc. for asyncpg.
"""

# ============================================================================
# PATTERN QUERIES
# ============================================================================

INSERT_PATTERN = """
INSERT INTO behavioral_patterns
(pattern_id, discovered_date, pattern_type, domains_affected,
 description, frequency, triggers, confidence_score)
VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8)
RETURNING pattern_id, confidence_score
"""

GET_PATTERNS_BY_DOMAIN = """
SELECT pattern_id, description, confidence_score,
       pattern_type, frequency, triggers, domains_affected, status
FROM behavioral_patterns
WHERE $1 = ANY(domains_affected)
AND status IN ('hypothesis', 'testing', 'validated')
AND confidence_score >= $2
ORDER BY confidence_score DESC
LIMIT $3
"""

GET_PATTERN_BY_ID = """
SELECT *
FROM behavioral_patterns
WHERE pattern_id = $1
"""

UPDATE_PATTERN_CONFIDENCE = """
UPDATE behavioral_patterns
SET confidence_score = $2,
    evolution_history = evolution_history || $3::jsonb,
    last_validated = $4,
    status = CASE
        WHEN $2 >= 0.8 THEN 'validated'
        WHEN $2 >= 0.5 THEN 'testing'
        ELSE 'hypothesis'
    END,
    updated_at = NOW()
WHERE pattern_id = $1
RETURNING status, confidence_score
"""

FIND_RELATED_PATTERNS = """
SELECT p.pattern_id, p.description, p.confidence_score,
       p.domains_affected, p.pattern_type
FROM behavioral_patterns p
WHERE p.pattern_id != $1
AND (
    p.domains_affected && $2::text[]  -- Array overlap
    OR p.pattern_type = $3
)
AND p.confidence_score >= $4
AND p.status IN ('testing', 'validated')
ORDER BY p.confidence_score DESC
LIMIT 10
"""

# ============================================================================
# EXPERIMENT QUERIES
# ============================================================================

INSERT_EXPERIMENT = """
INSERT INTO experiments
(experiment_id, start_date, end_date, status, domain,
 hypothesis, intervention, metrics)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb)
RETURNING experiment_id
"""

GET_ACTIVE_EXPERIMENTS = """
SELECT e.*, ae.current_day, ae.target_days, ae.last_observation_date
FROM experiments e
JOIN active_experiments ae ON e.experiment_id = ae.experiment_id
WHERE e.status = 'active'
ORDER BY e.start_date DESC
"""

GET_EXPERIMENT_BY_ID = """
SELECT *
FROM experiments
WHERE experiment_id = $1
"""

UPDATE_EXPERIMENT_OBSERVATIONS = """
UPDATE experiments
SET daily_observations = $1::jsonb,
    updated_at = NOW()
WHERE experiment_id = $2
RETURNING experiment_id
"""

ACTIVATE_EXPERIMENT = """
UPDATE experiments
SET status = 'active', updated_at = NOW()
WHERE experiment_id = $1
AND status = 'planned'
RETURNING experiment_id, domain, start_date, end_date
"""

INSERT_ACTIVE_EXPERIMENT_TRACKING = """
INSERT INTO active_experiments
(experiment_id, activated_date, target_days, current_day)
VALUES ($1, NOW(), $2, 1)
"""

UPDATE_ACTIVE_EXPERIMENT_PROGRESS = """
UPDATE active_experiments
SET current_day = current_day + 1,
    last_observation_date = $1
WHERE experiment_id = $2
RETURNING current_day, target_days
"""

COMPLETE_EXPERIMENT = """
UPDATE experiments
SET status = 'completed',
    end_date = NOW()::date,
    updated_at = NOW()
WHERE experiment_id = $1
"""

REMOVE_ACTIVE_EXPERIMENT = """
DELETE FROM active_experiments
WHERE experiment_id = $1
"""

# ============================================================================
# PATTERN-EXPERIMENT RELATIONSHIP QUERIES
# ============================================================================

LINK_PATTERN_TO_EXPERIMENT = """
INSERT INTO pattern_experiments
(pattern_id, experiment_id, relationship_type, strength)
VALUES ($1, $2, $3, $4)
ON CONFLICT (pattern_id, experiment_id)
DO UPDATE SET strength = $4, relationship_type = $3
"""

GET_EXPERIMENT_PATTERNS = """
SELECT bp.*, pe.relationship_type, pe.strength
FROM behavioral_patterns bp
JOIN pattern_experiments pe ON bp.pattern_id = pe.pattern_id
WHERE pe.experiment_id = $1
"""

# ============================================================================
# INSIGHT QUERIES
# ============================================================================

INSERT_INSIGHT = """
INSERT INTO insights
(insight_id, date, type, description, supporting_patterns,
 supporting_experiments, actionable_recommendations, expected_impact, importance_score)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
RETURNING insight_id
"""

GET_RECENT_INSIGHTS = """
SELECT *
FROM insights
WHERE date >= NOW() - INTERVAL '$1 days'
ORDER BY importance_score DESC, date DESC
LIMIT $2
"""

# ============================================================================
# ANALYTICS QUERIES
# ============================================================================

GET_SUCCESSFUL_EXPERIMENTS = """
SELECT domain, outcome, start_date
FROM experiments
WHERE start_date >= $1
AND outcome IN ('success', 'partial')
ORDER BY start_date DESC
"""

GET_SESSION_SUMMARY = """
SELECT
    COUNT(DISTINCT bp.pattern_id) as patterns_discovered,
    COUNT(DISTINCT obs.experiment_id) as observations_recorded
FROM behavioral_patterns bp
LEFT JOIN LATERAL (
    SELECT e.experiment_id
    FROM experiments e,
    jsonb_array_elements(e.daily_observations) obs
    WHERE DATE((obs->>'date')::timestamp) = $1
) obs ON true
WHERE DATE(bp.discovered_date) = $1
"""

COUNT_ACTIVE_EXPERIMENTS = """
SELECT COUNT(*) as count
FROM experiments
WHERE status = 'active'
"""

GET_DOMAIN_PATTERN_STATS = """
SELECT
    unnest(domains_affected) as domain,
    COUNT(*) as pattern_count,
    AVG(confidence_score) as avg_confidence,
    AVG(intervention_success_rate) as avg_success_rate
FROM behavioral_patterns
WHERE status IN ('testing', 'validated')
GROUP BY unnest(domains_affected)
ORDER BY pattern_count DESC
"""

# ============================================================================
# RECOMMENDATION QUERIES
# ============================================================================

GET_PROBLEMATIC_PATTERNS = """
SELECT pattern_id, description, domains_affected, confidence_score
FROM behavioral_patterns
WHERE intervention_success_rate < 0.5
AND confidence_score >= 0.6
AND status IN ('testing', 'validated')
ORDER BY confidence_score DESC
LIMIT 1
"""

GET_UNDEREXPLORED_DOMAIN = """
SELECT domain, COUNT(*) as exp_count
FROM experiments
WHERE status IN ('completed', 'active')
GROUP BY domain
ORDER BY exp_count ASC
LIMIT 1
"""

INSERT_RECOMMENDATION_HISTORY = """
INSERT INTO experiment_recommendations
(session_date, presented_experiments, selected_experiment, selection_reasoning)
VALUES ($1, $2::jsonb, $3, $4)
"""
