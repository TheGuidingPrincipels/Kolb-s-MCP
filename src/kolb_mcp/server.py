"""Kolb's Cycle MCP Server - Main Application.

This server implements Dr. Justin Sung's Modified Kolb's Cycle methodology
for systematic self-improvement through daily pattern tracking and experimentation.
"""

import os
import sys
import json
import logging
import asyncio
from datetime import datetime, timedelta, date
from typing import Dict, Any, List, Optional

from fastmcp import FastMCP
from dotenv import load_dotenv
import asyncpg

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/kolb_mcp.log'),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

# Import local modules
from kolb_mcp.database.pool import DatabasePool, is_db_available
from kolb_mcp.database import queries as Q
from kolb_mcp.models.pattern import PatternCreate, PatternUpdate, PatternResponse
from kolb_mcp.models.experiment import ExperimentCreate, ObservationCreate, ExperimentResponse, ExperimentRecommendation
from kolb_mcp.models.insight import InsightCreate, InsightResponse

# Initialize FastMCP server
mcp = FastMCP(os.getenv("MCP_SERVER_NAME", "KolbKnowledgeServer"))

# Global state
_db_available = False


# ============================================================================
# LIFECYCLE MANAGEMENT
# ============================================================================

async def initialize_database():
    """Initialize database connection on server startup."""
    global _db_available

    try:
        pool = await DatabasePool.get_pool()

        # Test connection
        async with pool.acquire() as conn:
            await conn.fetchval('SELECT 1')

        _db_available = True
        logger.info("✓ Database connection pool initialized successfully")
        logger.info("✓ Kolb's MCP Server ready for daily reflection sessions")

    except Exception as e:
        logger.error(f"✗ Database initialization failed: {e}")
        logger.warning("⚠ Server starting in degraded mode - tools will return errors")
        _db_available = False


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _check_db_available() -> Optional[Dict[str, Any]]:
    """Check if database is available, return error dict if not."""
    if not _db_available:
        return {
            "success": False,
            "error": "Database unavailable",
            "error_type": "database_unavailable",
            "message": "Please check DATABASE_URL and ensure PostgreSQL is running"
        }
    return None


def _generate_pattern_id() -> str:
    """Generate unique pattern ID."""
    return f"pat_{datetime.now().strftime('%Y_%m_%d')}_{os.urandom(4).hex()}"


def _generate_experiment_id(domain: str) -> str:
    """Generate unique experiment ID."""
    return f"exp_{datetime.now().strftime('%Y_%m_%d')}_{domain[:3]}"


def _generate_insight_id(type: str) -> str:
    """Generate unique insight ID."""
    return f"ins_{datetime.now().strftime('%Y_%m_%d')}_{type[:3]}"


# ============================================================================
# PATTERN MANAGEMENT TOOLS
# ============================================================================

@mcp.tool()
async def store_pattern(pattern: PatternCreate) -> Dict[str, Any]:
    """
    Store a new behavioral pattern discovered during daily reflection.

    Args:
        pattern: Pattern details including type, domains, triggers, and frequency

    Returns:
        Success status with pattern_id and initial confidence
    """
    # Check database availability
    if error := _check_db_available():
        return error

    try:
        pool = await DatabasePool.get_pool()
        pattern_id = _generate_pattern_id()

        async with pool.acquire() as conn:
            result = await conn.fetchrow(
                Q.INSERT_PATTERN,
                pattern_id,
                datetime.now(),
                pattern.pattern_type,
                pattern.domains,
                pattern.description,
                pattern.frequency,
                json.dumps(pattern.triggers),
                pattern.confidence
            )

        logger.info(f"✓ Stored new pattern: {pattern_id}")

        return {
            "success": True,
            "pattern_id": result['pattern_id'],
            "initial_confidence": float(result['confidence_score']),
            "domains_affected": pattern.domains
        }

    except asyncpg.PostgresError as e:
        logger.error(f"Database error in store_pattern: {e}")
        return {
            "success": False,
            "error": f"Database error: {str(e)}",
            "error_type": "database"
        }
    except Exception as e:
        logger.error(f"Unexpected error in store_pattern: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Server error: {str(e)}",
            "error_type": "server"
        }


@mcp.tool()
async def get_patterns_by_domain(
    domain: str,
    min_confidence: float = 0.5,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Retrieve all patterns affecting a specific domain.

    Args:
        domain: Life domain (work, health, relationships, learning, personal)
        min_confidence: Minimum confidence threshold (default 0.5)
        limit: Maximum number of results (default 50)

    Returns:
        List of pattern summaries matching criteria
    """
    # Check database availability
    if error := _check_db_available():
        return [error]

    try:
        pool = await DatabasePool.get_pool()

        async with pool.acquire() as conn:
            rows = await conn.fetch(
                Q.GET_PATTERNS_BY_DOMAIN,
                domain,
                min_confidence,
                limit
            )

        patterns = [dict(row) for row in rows]
        logger.info(f"✓ Retrieved {len(patterns)} patterns for domain: {domain}")

        return patterns

    except Exception as e:
        logger.error(f"Error in get_patterns_by_domain: {e}", exc_info=True)
        return [{"error": str(e)}]


@mcp.tool()
async def update_pattern_confidence(update: PatternUpdate) -> Dict[str, Any]:
    """
    Update pattern confidence based on new evidence.

    Args:
        update: Pattern ID, new confidence score, and supporting evidence

    Returns:
        Success status with updated confidence and status
    """
    # Check database availability
    if error := _check_db_available():
        return error

    try:
        pool = await DatabasePool.get_pool()

        async with pool.acquire() as conn:
            # Get current confidence
            current = await conn.fetchrow(
                Q.GET_PATTERN_BY_ID,
                update.pattern_id
            )

            if not current:
                return {
                    "success": False,
                    "error": "Pattern not found",
                    "error_type": "not_found"
                }

            # Calculate confidence change
            change_delta = update.new_confidence - float(current['confidence_score'])

            # Create evolution entry
            evolution_entry = json.dumps([{
                "date": datetime.now().isoformat(),
                "insight": update.evidence,
                "confidence_change": change_delta,
                "evidence": update.evidence
            }])

            # Update pattern
            result = await conn.fetchrow(
                Q.UPDATE_PATTERN_CONFIDENCE,
                update.pattern_id,
                update.new_confidence,
                evolution_entry,
                datetime.now()
            )

        logger.info(f"✓ Updated pattern {update.pattern_id}: {current['confidence_score']} → {update.new_confidence}")

        return {
            "success": True,
            "pattern_id": update.pattern_id,
            "old_confidence": float(current['confidence_score']),
            "new_confidence": float(result['confidence_score']),
            "change_delta": change_delta,
            "new_status": result['status']
        }

    except Exception as e:
        logger.error(f"Error in update_pattern_confidence: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "error_type": "server"
        }


@mcp.tool()
async def find_related_patterns(
    pattern_id: str,
    threshold: float = 0.6
) -> List[Dict[str, Any]]:
    """
    Find patterns that relate to the specified pattern (cross-domain detection).

    Args:
        pattern_id: Target pattern ID
        threshold: Minimum confidence threshold for related patterns (default 0.6)

    Returns:
        List of related patterns with overlap information
    """
    # Check database availability
    if error := _check_db_available():
        return [error]

    try:
        pool = await DatabasePool.get_pool()

        async with pool.acquire() as conn:
            # Get target pattern details
            target = await conn.fetchrow(
                Q.GET_PATTERN_BY_ID,
                pattern_id
            )

            if not target:
                return [{"error": "Pattern not found"}]

            # Find related patterns
            rows = await conn.fetch(
                Q.FIND_RELATED_PATTERNS,
                pattern_id,
                target['domains_affected'],
                target['pattern_type'],
                threshold
            )

        related = [dict(row) for row in rows]
        logger.info(f"✓ Found {len(related)} related patterns for {pattern_id}")

        return related

    except Exception as e:
        logger.error(f"Error in find_related_patterns: {e}", exc_info=True)
        return [{"error": str(e)}]


# ============================================================================
# EXPERIMENT MANAGEMENT TOOLS
# ============================================================================

@mcp.tool()
async def create_experiment(experiment: ExperimentCreate) -> Dict[str, Any]:
    """
    Create a new experiment for tomorrow's session.

    Args:
        experiment: Experiment details including hypothesis, intervention, and metrics

    Returns:
        Success status with experiment_id and start date
    """
    # Check database availability
    if error := _check_db_available():
        return error

    try:
        pool = await DatabasePool.get_pool()
        experiment_id = _generate_experiment_id(experiment.domain)

        start_date = (datetime.now() + timedelta(days=1)).date()
        end_date = start_date + timedelta(days=experiment.duration_days)

        async with pool.acquire() as conn:
            async with conn.transaction():
                # Create experiment
                await conn.execute(
                    Q.INSERT_EXPERIMENT,
                    experiment_id,
                    start_date,
                    end_date,
                    'planned',
                    experiment.domain,
                    experiment.hypothesis,
                    experiment.intervention,
                    json.dumps({
                        "primary": experiment.primary_metrics,
                        "guardrail": experiment.guardrail_metrics
                    })
                )

                # Link to target pattern if specified
                if experiment.target_pattern_id:
                    await conn.execute(
                        Q.LINK_PATTERN_TO_EXPERIMENT,
                        experiment.target_pattern_id,
                        experiment_id,
                        'targets',
                        0.8
                    )

        logger.info(f"✓ Created experiment: {experiment_id}")

        return {
            "success": True,
            "experiment_id": experiment_id,
            "domain": experiment.domain,
            "start_date": str(start_date),
            "duration_days": experiment.duration_days,
            "status": "planned"
        }

    except Exception as e:
        logger.error(f"Error in create_experiment: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "error_type": "server"
        }


@mcp.tool()
async def get_active_experiments() -> List[Dict[str, Any]]:
    """
    Get all currently active experiments.

    Returns:
        List of active experiments with progress tracking
    """
    # Check database availability
    if error := _check_db_available():
        return [error]

    try:
        pool = await DatabasePool.get_pool()

        async with pool.acquire() as conn:
            rows = await conn.fetch(Q.GET_ACTIVE_EXPERIMENTS)

        experiments = []
        for row in rows:
            exp_dict = dict(row)
            exp_dict['days_remaining'] = exp_dict['target_days'] - exp_dict['current_day']
            experiments.append(exp_dict)

        logger.info(f"✓ Retrieved {len(experiments)} active experiments")

        return experiments

    except Exception as e:
        logger.error(f"Error in get_active_experiments: {e}", exc_info=True)
        return [{"error": str(e)}]


@mcp.tool()
async def record_daily_observation(observation: ObservationCreate) -> Dict[str, Any]:
    """
    Record today's observation for an active experiment.

    Args:
        observation: Daily observation including metrics and energy level

    Returns:
        Success status with current day and days remaining
    """
    # Check database availability
    if error := _check_db_available():
        return error

    try:
        pool = await DatabasePool.get_pool()

        async with pool.acquire() as conn:
            async with conn.transaction():
                # Get experiment
                exp = await conn.fetchrow(
                    Q.GET_EXPERIMENT_BY_ID,
                    observation.experiment_id
                )

                if not exp or exp['status'] != 'active':
                    return {
                        "success": False,
                        "error": "Experiment not found or not active",
                        "error_type": "not_found"
                    }

                # Parse and append observation
                observations = json.loads(exp['daily_observations']) if exp['daily_observations'] else []

                new_obs = {
                    "date": datetime.now().isoformat(),
                    "observation": observation.observation,
                    "metric_values": observation.metrics,
                    "energy_level": observation.energy_level,
                    "notes": observation.notes
                }

                observations.append(new_obs)

                # Update experiment
                await conn.execute(
                    Q.UPDATE_EXPERIMENT_OBSERVATIONS,
                    json.dumps(observations),
                    observation.experiment_id
                )

                # Update tracking
                tracking = await conn.fetchrow(
                    Q.UPDATE_ACTIVE_EXPERIMENT_PROGRESS,
                    datetime.now().date(),
                    observation.experiment_id
                )

                # Auto-complete if target reached
                if tracking['current_day'] >= tracking['target_days']:
                    await conn.execute(Q.COMPLETE_EXPERIMENT, observation.experiment_id)
                    await conn.execute(Q.REMOVE_ACTIVE_EXPERIMENT, observation.experiment_id)

                    logger.info(f"✓ Experiment {observation.experiment_id} auto-completed")

                    return {
                        "success": True,
                        "experiment_id": observation.experiment_id,
                        "day_recorded": tracking['current_day'],
                        "status": "completed",
                        "message": "Experiment completed - target days reached"
                    }

        logger.info(f"✓ Recorded observation for {observation.experiment_id} (day {tracking['current_day']})")

        return {
            "success": True,
            "experiment_id": observation.experiment_id,
            "day_recorded": tracking['current_day'],
            "days_remaining": tracking['target_days'] - tracking['current_day'],
            "status": "active"
        }

    except Exception as e:
        logger.error(f"Error in record_daily_observation: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "error_type": "server"
        }


@mcp.tool()
async def recommend_experiments(
    current_patterns: List[str] = [],
    focus_domain: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Generate 3 experiment recommendations with success probabilities.

    Args:
        current_patterns: List of pattern IDs to consider
        focus_domain: Optional domain to focus on

    Returns:
        List of 3 experiment recommendations with reasoning
    """
    # Check database availability
    if error := _check_db_available():
        return [error]

    recommendations = []

    try:
        pool = await DatabasePool.get_pool()

        async with pool.acquire() as conn:
            # 1. High confidence: Target most problematic pattern
            if current_patterns:
                problem_pattern = await conn.fetchrow(Q.GET_PROBLEMATIC_PATTERNS)

                if problem_pattern:
                    recommendations.append({
                        "type": "pattern_intervention",
                        "domain": problem_pattern['domains_affected'][0],
                        "hypothesis": f"Addressing pattern: {problem_pattern['description'][:50]}...",
                        "intervention": "Design specific intervention to disrupt this pattern",
                        "success_probability": 0.7,
                        "reasoning": f"Targets high-confidence problematic pattern (confidence: {float(problem_pattern['confidence_score']):.2f})",
                        "target_pattern_id": problem_pattern['pattern_id']
                    })

            # 2. Medium confidence: Explore underexplored domain
            underexplored = await conn.fetchrow(Q.GET_UNDEREXPLORED_DOMAIN)

            if underexplored:
                recommendations.append({
                    "type": "exploration",
                    "domain": underexplored['domain'],
                    "hypothesis": f"Optimize {underexplored['domain']} through systematic experimentation",
                    "intervention": f"Identify and test one improvement in {underexplored['domain']}",
                    "success_probability": 0.5,
                    "reasoning": f"Underexplored domain with potential ({int(underexplored['exp_count'])} experiments so far)"
                })

            # 3. Ambitious: Cross-domain intervention
            if len(recommendations) < 3:
                recommendations.append({
                    "type": "systemic",
                    "domain": "personal",
                    "hypothesis": "Morning routine optimization creates cascade effects across all domains",
                    "intervention": "Design and test optimized morning routine for 7 days",
                    "success_probability": 0.3,
                    "reasoning": "High-risk, high-reward systemic intervention with potential cross-domain benefits"
                })

        logger.info(f"✓ Generated {len(recommendations)} experiment recommendations")

        return recommendations

    except Exception as e:
        logger.error(f"Error in recommend_experiments: {e}", exc_info=True)
        return [{"error": str(e)}]


# ============================================================================
# INSIGHT AND ANALYTICS TOOLS
# ============================================================================

@mcp.tool()
async def create_insight(insight: InsightCreate) -> Dict[str, Any]:
    """
    Create an insight from pattern analysis and experimentation.

    Args:
        insight: Insight details including description, type, and recommendations

    Returns:
        Success status with insight_id and importance
    """
    # Check database availability
    if error := _check_db_available():
        return error

    try:
        pool = await DatabasePool.get_pool()
        insight_id = _generate_insight_id(insight.type)

        async with pool.acquire() as conn:
            await conn.execute(
                Q.INSERT_INSIGHT,
                insight_id,
                datetime.now(),
                insight.type,
                insight.description,
                insight.supporting_patterns,
                insight.supporting_experiments,
                insight.actionable_recommendations,
                insight.expected_impact,
                insight.importance_score
            )

        logger.info(f"✓ Created insight: {insight_id} (importance: {insight.importance_score})")

        return {
            "success": True,
            "insight_id": insight_id,
            "type": insight.type,
            "importance": insight.importance_score
        }

    except Exception as e:
        logger.error(f"Error in create_insight: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "error_type": "server"
        }


@mcp.tool()
async def calculate_compound_gains(days: int = 30) -> Dict[str, Any]:
    """
    Calculate compound improvement rate across all domains (1% daily gains methodology).

    Args:
        days: Number of days to analyze (default 30)

    Returns:
        Compound gains by domain and overall with annual projection
    """
    # Check database availability
    if error := _check_db_available():
        return error

    try:
        pool = await DatabasePool.get_pool()

        async with pool.acquire() as conn:
            # Get successful experiments
            rows = await conn.fetch(
                Q.GET_SUCCESSFUL_EXPERIMENTS,
                datetime.now() - timedelta(days=days)
            )

        # Calculate domain-specific gains
        domain_gains = {}
        for row in rows:
            domain = row['domain']
            if domain not in domain_gains:
                domain_gains[domain] = []

            # 1% for success, 0.5% for partial
            improvement = 0.01 if row['outcome'] == 'success' else 0.005
            domain_gains[domain].append(improvement)

        # Calculate compound effect per domain
        results = {}
        for domain, gains in domain_gains.items():
            compound_factor = 1.0
            for gain in gains:
                compound_factor *= (1 + gain)

            results[domain] = {
                "compound_factor": round(compound_factor, 4),
                "percentage_gain": round((compound_factor - 1) * 100, 2),
                "experiments_count": len(gains)
            }

        # Overall compound
        total_compound = 1.0
        for gain_list in domain_gains.values():
            for gain in gain_list:
                total_compound *= (1 + gain)

        # Project to annual
        if days > 0:
            projection_annual = total_compound ** (365 / days)
        else:
            projection_annual = 1.0

        logger.info(f"✓ Calculated compound gains: {round((total_compound - 1) * 100, 2)}% over {days} days")

        return {
            "success": True,
            "domains": results,
            "overall_compound": round(total_compound, 4),
            "overall_percentage": round((total_compound - 1) * 100, 2),
            "days_tracked": days,
            "annual_projection": {
                "factor": round(projection_annual, 4),
                "percentage": round((projection_annual - 1) * 100, 2),
                "interpretation": f"{round(projection_annual, 1)}x improvement over baseline"
            }
        }

    except Exception as e:
        logger.error(f"Error in calculate_compound_gains: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "error_type": "server"
        }


@mcp.tool()
async def get_session_summary(target_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Get summary of a specific day's session or today.

    Args:
        target_date: ISO date string (YYYY-MM-DD), defaults to today

    Returns:
        Summary of patterns discovered, observations recorded, and activity stats
    """
    # Check database availability
    if error := _check_db_available():
        return error

    try:
        if target_date:
            summary_date = datetime.fromisoformat(target_date).date()
        else:
            summary_date = datetime.now().date()

        pool = await DatabasePool.get_pool()

        async with pool.acquire() as conn:
            # Get session stats
            stats = await conn.fetchrow(
                Q.GET_SESSION_SUMMARY,
                summary_date
            )

            # Get active experiment count
            active_count = await conn.fetchval(Q.COUNT_ACTIVE_EXPERIMENTS)

        logger.info(f"✓ Generated session summary for {summary_date}")

        return {
            "success": True,
            "date": str(summary_date),
            "patterns_discovered": stats['patterns_discovered'] if stats else 0,
            "observations_recorded": stats['observations_recorded'] if stats else 0,
            "active_experiments": active_count or 0,
            "session_completed": (stats['patterns_discovered'] > 0 or stats['observations_recorded'] > 0) if stats else False
        }

    except Exception as e:
        logger.error(f"Error in get_session_summary: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)}


# ============================================================================
# MCP RESOURCES
# ============================================================================

@mcp.resource("pattern://{pattern_id}")
async def get_pattern_resource(pattern_id: str) -> str:
    """
    Retrieve complete pattern details as a resource.

    Args:
        pattern_id: Unique pattern identifier

    Returns:
        JSON string of pattern details
    """
    if not _db_available:
        return json.dumps({"error": "Database unavailable"})

    try:
        pool = await DatabasePool.get_pool()

        async with pool.acquire() as conn:
            pattern = await conn.fetchrow(
                Q.GET_PATTERN_BY_ID,
                pattern_id
            )

        if not pattern:
            return json.dumps({"error": "Pattern not found"})

        return json.dumps(dict(pattern), default=str, indent=2)

    except Exception as e:
        logger.error(f"Error in get_pattern_resource: {e}", exc_info=True)
        return json.dumps({"error": str(e)})


@mcp.resource("experiment://{experiment_id}")
async def get_experiment_resource(experiment_id: str) -> str:
    """
    Retrieve complete experiment details as a resource.

    Args:
        experiment_id: Unique experiment identifier

    Returns:
        JSON string of experiment details
    """
    if not _db_available:
        return json.dumps({"error": "Database unavailable"})

    try:
        pool = await DatabasePool.get_pool()

        async with pool.acquire() as conn:
            experiment = await conn.fetchrow(
                Q.GET_EXPERIMENT_BY_ID,
                experiment_id
            )

        if not experiment:
            return json.dumps({"error": "Experiment not found"})

        return json.dumps(dict(experiment), default=str, indent=2)

    except Exception as e:
        logger.error(f"Error in get_experiment_resource: {e}", exc_info=True)
        return json.dumps({"error": str(e)})


# ============================================================================
# SERVER ENTRY POINT
# ============================================================================

async def main():
    """Main entry point with database initialization."""
    logger.info("="* 60)
    logger.info("Kolb's Cycle MCP Server Starting...")
    logger.info("="* 60)

    # Initialize database
    await initialize_database()

    # Run server (this blocks)
    await mcp.run_async()


if __name__ == "__main__":
    asyncio.run(main())
