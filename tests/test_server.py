#!/usr/bin/env python3
"""
Comprehensive test suite for Kolb's MCP Server.

Tests all 12 tools, 2 resources, workflows, and edge cases.
Includes performance metrics and database verification.
Cleans up all test data at the end.
"""

import asyncio
import sys
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Set environment variables
os.environ['DATABASE_URL'] = 'postgresql://ruben@localhost:5432/knowledge_mcp'
os.environ['LOG_LEVEL'] = 'INFO'

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import server modules
from kolb_mcp.models.pattern import PatternCreate, PatternUpdate
from kolb_mcp.models.experiment import ExperimentCreate, ObservationCreate
from kolb_mcp.models.insight import InsightCreate
from kolb_mcp.database.pool import DatabasePool, get_db_pool

# Import server tools
import kolb_mcp.server as server

# Test tracking
test_results = []
created_ids = {
    'patterns': [],
    'experiments': [],
    'insights': []
}
timing_results = []


def print_header(text: str):
    """Print formatted section header."""
    print(f"\n{'='*80}")
    print(f"  {text}")
    print(f"{'='*80}\n")


def print_test(name: str, passed: bool, details: str = ""):
    """Print test result."""
    symbol = "✓" if passed else "✗"
    status = "PASS" if passed else "FAIL"
    result_line = f"  {symbol} {name}: {status}"
    if details:
        result_line += f" - {details}"
    print(result_line)
    test_results.append((name, passed, details))


def measure_time(func):
    """Decorator to measure execution time."""
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        elapsed = (time.time() - start) * 1000  # Convert to ms
        timing_results.append((func.__name__, elapsed))
        return result, elapsed
    return wrapper


# ============================================================================
# TEST SUITE 1: PATTERN MANAGEMENT TOOLS
# ============================================================================

@measure_time
async def test_store_pattern():
    """Test storing a new behavioral pattern."""
    pattern_data = PatternCreate(
        description="Procrastinate on tasks requiring >2 hours of uninterrupted focus",
        pattern_type="behavioral",
        domains=["work"],
        triggers=["complex tasks", "uncertainty", "fatigue"],
        frequency="daily",
        confidence=0.3
    )

    result = await server.store_pattern.fn(pattern_data)
    return result


@measure_time
async def test_store_pattern_multi_domain():
    """Test storing pattern with multiple domains."""
    pattern_data = PatternCreate(
        description="Overthink decisions when outcome is uncertain",
        pattern_type="cognitive",
        domains=["work", "personal"],
        triggers=["high stakes", "ambiguity"],
        frequency="situational",
        confidence=0.3
    )

    result = await server.store_pattern.fn(pattern_data)
    return result


@measure_time
async def test_store_pattern_health():
    """Test storing health-related pattern."""
    pattern_data = PatternCreate(
        description="Skip morning workouts when feeling stressed or anxious",
        pattern_type="behavioral",
        domains=["health"],
        triggers=["stress", "poor sleep", "anxiety"],
        frequency="weekly",
        confidence=0.3
    )

    result = await server.store_pattern.fn(pattern_data)
    return result


@measure_time
async def test_get_patterns_by_domain():
    """Test retrieving patterns by domain."""
    result = await server.get_patterns_by_domain.fn(
        domain="work",
        min_confidence=0.0,
        limit=50
    )
    return result


@measure_time
async def test_update_pattern_confidence():
    """Test updating pattern confidence with evidence."""
    if not created_ids['patterns']:
        return {"success": False, "error": "No patterns to update"}

    pattern_id = created_ids['patterns'][0]
    update_data = PatternUpdate(
        pattern_id=pattern_id,
        new_confidence=0.7,
        evidence="Observed pattern 5 times this week in different contexts",
        evidence_type="observation"
    )

    result = await server.update_pattern_confidence.fn(update_data)
    return result


@measure_time
async def test_find_related_patterns():
    """Test finding related patterns across domains."""
    if not created_ids['patterns']:
        return {"success": False, "error": "No patterns to query"}

    pattern_id = created_ids['patterns'][0]
    result = await server.find_related_patterns.fn(
        pattern_id=pattern_id,
        threshold=0.0  # Low threshold for testing
    )
    return result


# ============================================================================
# TEST SUITE 2: EXPERIMENT MANAGEMENT TOOLS
# ============================================================================

@measure_time
async def test_create_experiment():
    """Test creating a new experiment."""
    if not created_ids['patterns']:
        return {"success": False, "error": "No patterns to target"}

    experiment_data = ExperimentCreate(
        domain="work",
        hypothesis="Working in 90-minute focused blocks will increase deep work completion by 30%",
        intervention="Set timer for 90 min, disable all notifications, close email/slack",
        primary_metrics=["deep work hours completed", "task completion rate"],
        guardrail_metrics=["stress level", "energy at end of day"],
        duration_days=7,
        target_pattern_id=created_ids['patterns'][0]
    )

    result = await server.create_experiment.fn(experiment_data)
    return result


@measure_time
async def test_create_experiment_health():
    """Test creating health experiment."""
    if len(created_ids['patterns']) < 3:
        return {"success": False, "error": "Not enough patterns"}

    experiment_data = ExperimentCreate(
        domain="health",
        hypothesis="Morning workouts before 8am will reduce stress and improve energy by 20%",
        intervention="Wake at 6:30am, 30-min workout before breakfast",
        primary_metrics=["workout completion", "energy level"],
        guardrail_metrics=["sleep quality", "recovery time"],
        duration_days=3,  # Short duration for testing auto-completion
        target_pattern_id=created_ids['patterns'][2]
    )

    result = await server.create_experiment.fn(experiment_data)
    return result


@measure_time
async def test_get_active_experiments():
    """Test retrieving active experiments."""
    result = await server.get_active_experiments.fn()
    return result


@measure_time
async def test_record_daily_observation():
    """Test recording daily observation for experiment."""
    if not created_ids['experiments']:
        return {"success": False, "error": "No experiments to observe"}

    experiment_id = created_ids['experiments'][0]
    observation_data = ObservationCreate(
        experiment_id=experiment_id,
        observation="Completed 2 focused blocks today. Felt more productive, less context switching.",
        metrics={
            "deep_work_hours": 3.0,
            "task_completion_rate": 0.75,
            "stress_level": 4,
            "energy_at_end": 7
        },
        energy_level=7,
        notes="Surprisingly easier than expected to maintain focus"
    )

    result = await server.record_daily_observation.fn(observation_data)
    return result


@measure_time
async def test_recommend_experiments():
    """Test experiment recommendations."""
    result = await server.recommend_experiments.fn(
        current_patterns=created_ids['patterns'][:2] if len(created_ids['patterns']) >= 2 else [],
        focus_domain="work"
    )
    return result


# ============================================================================
# TEST SUITE 3: ANALYTICS TOOLS
# ============================================================================

@measure_time
async def test_create_insight():
    """Test creating an insight."""
    if not created_ids['patterns'] or not created_ids['experiments']:
        return {"success": False, "error": "Need patterns and experiments"}

    insight_data = InsightCreate(
        type="connection",
        description="Procrastination and overthinking are linked - both triggered by uncertainty",
        supporting_patterns=created_ids['patterns'][:2],
        supporting_experiments=created_ids['experiments'][:1],
        actionable_recommendations=[
            "Break down uncertain tasks into smaller, concrete steps",
            "Set 5-minute decision timer for overthinking moments"
        ],
        expected_impact="30% reduction in decision paralysis when breaking down complex tasks",
        importance_score=8
    )

    result = await server.create_insight.fn(insight_data)
    return result


@measure_time
async def test_calculate_compound_gains():
    """Test compound gains calculation."""
    result = await server.calculate_compound_gains.fn(days=30)
    return result


@measure_time
async def test_get_session_summary():
    """Test session summary retrieval."""
    today = datetime.now().date().isoformat()
    result = await server.get_session_summary.fn(target_date=today)
    return result


# ============================================================================
# TEST SUITE 4: RESOURCES
# ============================================================================

async def test_pattern_resource():
    """Test pattern:// resource URI."""
    if not created_ids['patterns']:
        return {"success": False, "error": "No patterns"}

    pattern_id = created_ids['patterns'][0]
    try:
        result = await server.get_pattern_resource(pattern_id)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def test_experiment_resource():
    """Test experiment:// resource URI."""
    if not created_ids['experiments']:
        return {"success": False, "error": "No experiments"}

    experiment_id = created_ids['experiments'][0]
    try:
        result = await server.get_experiment_resource(experiment_id)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================================
# TEST SUITE 5: WORKFLOWS
# ============================================================================

async def test_experiment_completion_workflow():
    """Test full experiment lifecycle with auto-completion."""
    print_header("Workflow: Experiment Completion (3-day cycle)")

    # Get the short-duration experiment
    if len(created_ids['experiments']) < 2:
        print_test("Experiment Completion Workflow", False, "Not enough experiments")
        return

    experiment_id = created_ids['experiments'][1]  # The 3-day health experiment

    # Record observations for days 2 and 3 (we already did day 1)
    for day in [2, 3]:
        obs_data = ObservationCreate(
            experiment_id=experiment_id,
            observation=f"Day {day} observation - workout completed",
            metrics={"workout_completion": 1, "energy_level": 8},
            energy_level=8,
            notes=f"Day {day} complete"
        )

        result = await server.record_daily_observation.fn(obs_data)

        if day == 3:
            # Should auto-complete after day 3
            if result.get('completed'):
                print_test(f"  Day {day} observation recorded", True, "Experiment auto-completed")
            else:
                print_test(f"  Day {day} observation recorded", False, "Did not auto-complete")
        else:
            print_test(f"  Day {day} observation recorded", result.get('success', False))

    # Verify experiment is now completed
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        status = await conn.fetchval(
            "SELECT status FROM experiments WHERE experiment_id = $1",
            experiment_id
        )
        print_test("Experiment status updated to 'completed'", status == 'completed', f"Status: {status}")

        # Check it's removed from active_experiments
        active_count = await conn.fetchval(
            "SELECT COUNT(*) FROM active_experiments WHERE experiment_id = $1",
            experiment_id
        )
        print_test("Removed from active_experiments", active_count == 0, f"Count: {active_count}")


async def test_cross_domain_analysis_workflow():
    """Test finding related patterns across domains."""
    print_header("Workflow: Cross-Domain Pattern Analysis")

    if len(created_ids['patterns']) < 2:
        print_test("Cross-Domain Analysis", False, "Not enough patterns")
        return

    # Find patterns related to the work pattern (which has procrastination)
    pattern_id = created_ids['patterns'][0]
    related = await server.find_related_patterns.fn(pattern_id, threshold=0.0)

    if isinstance(related, list):
        print_test("Related patterns found", len(related) > 0, f"Found {len(related)} related patterns")

        # Verify the multi-domain pattern (overthinking) is in results
        found_overthinking = any(
            'overthink' in p.get('description', '').lower()
            for p in related
        )
        print_test("Found cross-domain connection", found_overthinking, "Overthinking pattern detected")
    else:
        print_test("Related patterns query", False, "Invalid response format")


# ============================================================================
# TEST SUITE 6: EDGE CASES
# ============================================================================

async def test_edge_cases():
    """Test edge cases and error handling."""
    print_header("Edge Case Tests")

    # Test 1: Update non-existent pattern
    fake_update = PatternUpdate(
        pattern_id="pat_2099_01_01_fake123",
        new_confidence=0.8,
        evidence="test evidence string for validation",
        evidence_type="observation"
    )
    result = await server.update_pattern_confidence.fn(fake_update)
    print_test("Update non-existent pattern", not result.get('success', True), "Should return success=False")

    # Test 2: Get patterns from empty domain
    result = await server.get_patterns_by_domain.fn(domain="relationships", min_confidence=0.0)
    print_test("Query empty domain", isinstance(result, list) and len(result) == 0, "Should return empty list")

    # Test 3: Record observation for non-existent experiment
    fake_obs = ObservationCreate(
        experiment_id="exp_2099_01_01_fake",
        observation="test observation for validation",
        metrics={},
        energy_level=5
    )
    result = await server.record_daily_observation.fn(fake_obs)
    print_test("Observe non-existent experiment", not result.get('success', True), "Should return success=False")


# ============================================================================
# DATABASE VERIFICATION
# ============================================================================

async def verify_database_state():
    """Verify database contains expected data."""
    print_header("Database State Verification")

    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Count patterns
        pattern_count = await conn.fetchval("SELECT COUNT(*) FROM behavioral_patterns")
        print_test("Patterns in database", pattern_count >= 3, f"Count: {pattern_count}")

        # Count experiments
        exp_count = await conn.fetchval("SELECT COUNT(*) FROM experiments")
        print_test("Experiments in database", exp_count >= 2, f"Count: {exp_count}")

        # Count insights
        insight_count = await conn.fetchval("SELECT COUNT(*) FROM insights")
        print_test("Insights in database", insight_count >= 1, f"Count: {insight_count}")

        # Check pattern-experiment relationships
        pe_count = await conn.fetchval("SELECT COUNT(*) FROM pattern_experiments")
        print_test("Pattern-experiment links", pe_count >= 1, f"Count: {pe_count}")

        # Verify JSONB fields are valid JSON
        triggers = await conn.fetchval(
            "SELECT triggers FROM behavioral_patterns WHERE pattern_id = $1",
            created_ids['patterns'][0] if created_ids['patterns'] else 'fake'
        )
        print_test("JSONB triggers valid", isinstance(triggers, list), f"Type: {type(triggers)}")


# ============================================================================
# CLEANUP
# ============================================================================

async def cleanup_test_data():
    """Clean up all test data from database."""
    print_header("Cleanup: Removing Test Data")

    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # TRUNCATE all tables in correct order (respecting foreign keys)
        tables = [
            'active_experiments',
            'pattern_experiments',
            'experiment_recommendations',
            'insights',
            'experiments',
            'behavioral_patterns'
        ]

        for table in tables:
            await conn.execute(f"TRUNCATE TABLE {table} CASCADE")
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
            print_test(f"Truncated {table}", count == 0, f"Remaining: {count}")


async def verify_clean_database():
    """Verify database is completely clean."""
    print_header("Final Verification: Pristine Database")

    pool = await get_db_pool()
    async with pool.acquire() as conn:
        tables = [
            'behavioral_patterns',
            'experiments',
            'insights',
            'pattern_experiments',
            'active_experiments',
            'experiment_recommendations'
        ]

        all_clean = True
        for table in tables:
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
            is_clean = count == 0
            all_clean = all_clean and is_clean
            print_test(f"{table} is empty", is_clean, f"Count: {count}")

        return all_clean


# ============================================================================
# PERFORMANCE REPORTING
# ============================================================================

def print_performance_report():
    """Print performance metrics."""
    print_header("Performance Metrics")

    if not timing_results:
        print("  No timing data collected")
        return

    print(f"  {'Tool Name':<45} {'Time (ms)':>10} {'Status':>10}")
    print(f"  {'-'*67}")

    total_time = 0
    over_500ms = 0

    for tool_name, elapsed_ms in timing_results:
        status = "✓" if elapsed_ms < 500 else "⚠"
        print(f"  {tool_name:<45} {elapsed_ms:>9.2f}ms {status:>9}")
        total_time += elapsed_ms
        if elapsed_ms >= 500:
            over_500ms += 1

    print(f"  {'-'*67}")
    print(f"  {'TOTAL':<45} {total_time:>9.2f}ms")
    print(f"  {'AVERAGE':<45} {total_time/len(timing_results):>9.2f}ms")
    print()
    print(f"  Tools over 500ms: {over_500ms}/{len(timing_results)}")
    print(f"  Performance target: <500ms (p95)")


def print_final_summary():
    """Print final test summary."""
    print_header("Final Test Summary")

    passed = sum(1 for _, p, _ in test_results if p)
    total = len(test_results)

    print(f"  Total Tests: {total}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {total - passed}")
    print(f"  Success Rate: {passed/total*100:.1f}%")

    if passed == total:
        print(f"\n  🎉 All tests passed!")
    else:
        print(f"\n  ⚠️  {total - passed} test(s) failed")
        print(f"\n  Failed tests:")
        for name, passed, details in test_results:
            if not passed:
                print(f"    ✗ {name}: {details}")


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

async def main():
    """Run all tests."""
    print_header("Kolb's MCP Server - Comprehensive Test Suite")
    print(f"  Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Database: knowledge_mcp")

    try:
        # Initialize database via server (sets global _db_available flag)
        await server.initialize_database()
        print_test("Database connection", True, "Connected successfully")

        # Clean database before testing
        print_header("Pre-Test Cleanup")
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            tables = [
                'active_experiments',
                'pattern_experiments',
                'experiment_recommendations',
                'insights',
                'experiments',
                'behavioral_patterns'
            ]
            for table in tables:
                await conn.execute(f"TRUNCATE TABLE {table} CASCADE")
            print_test("Database cleaned", True, "All tables truncated")

        # ====================================================================
        # SUITE 1: PATTERN MANAGEMENT
        # ====================================================================
        print_header("Test Suite 1: Pattern Management Tools (4 tools)")

        # Test store_pattern
        result, elapsed = await test_store_pattern()
        print_test("store_pattern (procrastination)", result.get('success', False), f"{elapsed:.2f}ms")
        if result.get('success'):
            created_ids['patterns'].append(result['pattern_id'])

        # Test store_pattern (multi-domain)
        result, elapsed = await test_store_pattern_multi_domain()
        print_test("store_pattern (overthinking)", result.get('success', False), f"{elapsed:.2f}ms")
        if result.get('success'):
            created_ids['patterns'].append(result['pattern_id'])

        # Test store_pattern (health)
        result, elapsed = await test_store_pattern_health()
        print_test("store_pattern (skip workouts)", result.get('success', False), f"{elapsed:.2f}ms")
        if result.get('success'):
            created_ids['patterns'].append(result['pattern_id'])

        # Test get_patterns_by_domain
        result, elapsed = await test_get_patterns_by_domain()
        print_test("get_patterns_by_domain", isinstance(result, list), f"{elapsed:.2f}ms - Found {len(result)} patterns")

        # Test update_pattern_confidence
        result, elapsed = await test_update_pattern_confidence()
        print_test("update_pattern_confidence", result.get('success', False), f"{elapsed:.2f}ms - Confidence: {result.get('new_confidence', 'N/A')}")

        # Test find_related_patterns
        result, elapsed = await test_find_related_patterns()
        count = len(result) if isinstance(result, list) else 0
        print_test("find_related_patterns", isinstance(result, list), f"{elapsed:.2f}ms - Found {count} related")

        # ====================================================================
        # SUITE 2: EXPERIMENT MANAGEMENT
        # ====================================================================
        print_header("Test Suite 2: Experiment Management Tools (4 tools)")

        # Test create_experiment
        result, elapsed = await test_create_experiment()
        print_test("create_experiment (focus blocks)", result.get('success', False), f"{elapsed:.2f}ms")
        if result.get('success'):
            created_ids['experiments'].append(result['experiment_id'])

        # Test create_experiment (health)
        result, elapsed = await test_create_experiment_health()
        print_test("create_experiment (morning workout)", result.get('success', False), f"{elapsed:.2f}ms")
        if result.get('success'):
            created_ids['experiments'].append(result['experiment_id'])

        # Test get_active_experiments
        result, elapsed = await test_get_active_experiments()
        count = len(result) if isinstance(result, list) else 0
        print_test("get_active_experiments", isinstance(result, list), f"{elapsed:.2f}ms - Found {count} active")

        # Test record_daily_observation
        result, elapsed = await test_record_daily_observation()
        print_test("record_daily_observation", result.get('success', False), f"{elapsed:.2f}ms")

        # Test recommend_experiments
        result, elapsed = await test_recommend_experiments()
        count = len(result) if isinstance(result, list) else 0
        print_test("recommend_experiments", isinstance(result, list), f"{elapsed:.2f}ms - Got {count} recommendations")

        # ====================================================================
        # SUITE 3: ANALYTICS
        # ====================================================================
        print_header("Test Suite 3: Analytics Tools (4 tools)")

        # Test create_insight
        result, elapsed = await test_create_insight()
        print_test("create_insight", result.get('success', False), f"{elapsed:.2f}ms")
        if result.get('success'):
            created_ids['insights'].append(result['insight_id'])

        # Test calculate_compound_gains
        result, elapsed = await test_calculate_compound_gains()
        print_test("calculate_compound_gains", result.get('success', False), f"{elapsed:.2f}ms")

        # Test get_session_summary
        result, elapsed = await test_get_session_summary()
        print_test("get_session_summary", result.get('success', False), f"{elapsed:.2f}ms")

        # ====================================================================
        # SUITE 4: RESOURCES
        # ====================================================================
        print_header("Test Suite 4: MCP Resources (2 resources)")

        # Test pattern resource
        result = await test_pattern_resource()
        print_test("pattern:// resource", result.get('success', False))

        # Test experiment resource
        result = await test_experiment_resource()
        print_test("experiment:// resource", result.get('success', False))

        # ====================================================================
        # SUITE 5: WORKFLOWS
        # ====================================================================
        await test_experiment_completion_workflow()
        await test_cross_domain_analysis_workflow()

        # ====================================================================
        # SUITE 6: EDGE CASES
        # ====================================================================
        await test_edge_cases()

        # ====================================================================
        # DATABASE VERIFICATION
        # ====================================================================
        await verify_database_state()

        # ====================================================================
        # PERFORMANCE REPORT
        # ====================================================================
        print_performance_report()

        # ====================================================================
        # CLEANUP
        # ====================================================================
        await cleanup_test_data()

        # ====================================================================
        # FINAL VERIFICATION
        # ====================================================================
        clean = await verify_clean_database()

        # ====================================================================
        # FINAL SUMMARY
        # ====================================================================
        print_final_summary()

        # Close database
        await DatabasePool.close()
        print_test("Database connection closed", True)

        print(f"\n  End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Exit with appropriate code
        failed = sum(1 for _, p, _ in test_results if not p)
        sys.exit(0 if failed == 0 and clean else 1)

    except Exception as e:
        print(f"\n✗ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
