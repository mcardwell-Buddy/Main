"""
End-to-End Mission Integration Test

Tests all 4 critical fixes:
1. Store mission plan with mission
2. Use stored plan in execution
3. Persist progress to Firebase
4. Wire recipe instantiation

Run: python test_mission_integration.py
"""

import sys
import json
import time
import logging
from pathlib import Path

# Add Back_End to path
sys.path.insert(0, str(Path(__file__).parent / "Back_End"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_recipe_instantiation():
    """Test FIX #4: Recipe creates actual mission."""
    logger.info("\n" + "="*80)
    logger.info("TEST 1: Recipe Instantiation")
    logger.info("="*80)
    
    try:
        from mission_recipe_system import get_recipe_system
        
        recipe_system = get_recipe_system()
        
        # List available recipes
        recipes = recipe_system.list_recipes()
        logger.info(f"✓ Found {len(recipes)} recipes")
        
        if not recipes:
            logger.error("✗ No recipes found - recipe system not initialized")
            return None
        
        # Use first recipe for testing
        test_recipe = recipes[0]
        logger.info(f"✓ Using recipe: {test_recipe.name} ({test_recipe.recipe_id})")
        
        # Instantiate with test parameters
        parameters = {}
        for example in test_recipe.examples:
            if 'parameters' in example:
                parameters = example['parameters']
                break
        
        if not parameters:
            # Default parameters for common recipes
            parameters = {
                'search_query': 'Python async programming',
                'url': 'https://example.com',
                'count': 10
            }
        
        logger.info(f"✓ Using parameters: {parameters}")
        
        # Instantiate recipe
        mission = recipe_system.instantiate_recipe(
            recipe_id=test_recipe.recipe_id,
            parameters=parameters
        )
        
        if not mission:
            logger.error("✗ Recipe instantiation returned None")
            return None
        
        mission_id = mission.get('mission_id')
        if not mission_id:
            logger.error("✗ No mission_id in instantiated mission")
            return None
        
        logger.info(f"✓ Mission created: {mission_id}")
        logger.info(f"✓ Status: {mission.get('status')}")
        logger.info(f"✓ Message: {mission.get('message')}")
        
        # Verify mission exists in mission_store
        from mission_store import get_mission_store
        store = get_mission_store()
        
        mission_record = store.find_mission(mission_id)
        if not mission_record:
            logger.error(f"✗ Mission {mission_id} not found in mission_store")
            return None
        
        logger.info(f"✓ Mission verified in Firebase")
        logger.info(f"✓ Mission status: {mission_record.status}")
        
        return mission_id
        
    except Exception as e:
        logger.error(f"✗ Recipe instantiation test failed: {e}", exc_info=True)
        return None


def test_mission_approval(mission_id: str):
    """Test mission approval process."""
    logger.info("\n" + "="*80)
    logger.info("TEST 2: Mission Approval")
    logger.info("="*80)
    
    try:
        from mission_approval_service import approve_mission
        
        logger.info(f"✓ Approving mission: {mission_id}")
        
        result = approve_mission(mission_id)
        
        if not result.get('success'):
            logger.error(f"✗ Approval failed: {result.get('message')}")
            return False
        
        logger.info(f"✓ Mission approved successfully")
        
        # Verify status changed
        from mission_store import get_mission_store
        store = get_mission_store()
        
        status = store.get_current_status(mission_id)
        if status != 'approved':
            logger.error(f"✗ Status is '{status}', expected 'approved'")
            return False
        
        logger.info(f"✓ Mission status confirmed: {status}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Approval test failed: {e}", exc_info=True)
        return False


def test_mission_planning(mission_id: str):
    """Test FIX #1: Mission plan storage."""
    logger.info("\n" + "="*80)
    logger.info("TEST 3: Mission Plan Storage")
    logger.info("="*80)
    
    try:
        from mission_store import get_mission_store
        from execution_service import ExecutionService
        
        store = get_mission_store()
        service = ExecutionService()
        
        # Check if mission has a stored plan
        stored_plan = service._get_stored_plan(mission_id)
        
        if stored_plan:
            logger.info(f"✓ Found stored plan for mission {mission_id}")
            logger.info(f"✓ Plan has {len(stored_plan.get('steps', []))} steps")
            logger.info(f"✓ Total cost: ${stored_plan.get('total_cost_usd', 0):.4f}")
            logger.info(f"✓ Estimated time: {stored_plan.get('estimated_total_time_minutes', 0)} min")
            
            # Show first step details
            if stored_plan.get('steps'):
                first_step = stored_plan['steps'][0]
                logger.info(f"✓ First step tool: {first_step.get('selected_tool')}")
                logger.info(f"✓ Tool confidence: {first_step.get('tool_confidence', 0):.2f}")
            
            return stored_plan
        else:
            logger.warning("⚠ No stored plan found - mission may not have been planned")
            logger.info("  (This is OK for recipe-based missions)")
            return None
        
    except Exception as e:
        logger.error(f"✗ Plan storage test failed: {e}", exc_info=True)
        return None


def test_mission_execution(mission_id: str, expected_plan: dict = None):
    """Test FIX #2: Use stored plan in execution."""
    logger.info("\n" + "="*80)
    logger.info("TEST 4: Mission Execution with Planned Tools")
    logger.info("="*80)
    
    try:
        from execution_service import execute_mission
        
        logger.info(f"✓ Executing mission: {mission_id}")
        
        if expected_plan and expected_plan.get('steps'):
            expected_tool = expected_plan['steps'][0].get('selected_tool')
            logger.info(f"✓ Expected tool from plan: {expected_tool}")
        
        # Execute mission
        result = execute_mission(mission_id)
        
        if not result:
            logger.error("✗ Execution returned None")
            return None
        
        success = result.get('success')
        tool_used = result.get('tool_used')
        
        logger.info(f"{'✓' if success else '✗'} Execution {'succeeded' if success else 'failed'}")
        logger.info(f"✓ Tool used: {tool_used}")
        logger.info(f"✓ Tool confidence: {result.get('tool_confidence', 0):.2f}")
        
        # Verify tool matches plan
        if expected_plan and expected_plan.get('steps'):
            expected_tool = expected_plan['steps'][0].get('selected_tool')
            if tool_used == expected_tool:
                logger.info(f"✓ Tool matches plan! ({tool_used} == {expected_tool})")
            else:
                logger.warning(f"⚠ Tool mismatch: used {tool_used}, expected {expected_tool}")
        
        # Show result summary
        if result.get('result_summary'):
            logger.info(f"✓ Result: {result['result_summary'][:100]}...")
        
        if result.get('error'):
            logger.error(f"✗ Error: {result['error']}")
        
        return result
        
    except Exception as e:
        logger.error(f"✗ Execution test failed: {e}", exc_info=True)
        return None


def test_progress_persistence(mission_id: str):
    """Test FIX #3: Progress persisted to Firebase."""
    logger.info("\n" + "="*80)
    logger.info("TEST 5: Progress Persistence")
    logger.info("="*80)
    
    try:
        from mission_store import get_mission_store
        
        store = get_mission_store()
        
        logger.info(f"✓ Retrieving progress for mission: {mission_id}")
        
        # Get stored progress
        progress = store.get_mission_progress(mission_id)
        
        if progress.get('error'):
            logger.error(f"✗ Error retrieving progress: {progress['error']}")
            return False
        
        if not progress:
            logger.error("✗ No progress data found")
            return False
        
        logger.info(f"✓ Progress data retrieved from Firebase")
        
        # Show progress details
        if progress.get('current_step'):
            logger.info(f"✓ Current step: {progress['current_step'].get('step_name')}")
        
        if progress.get('completed_steps'):
            logger.info(f"✓ Completed steps: {len(progress['completed_steps'])}")
        
        logger.info(f"✓ Progress percent: {progress.get('progress_percent', 0)}%")
        logger.info(f"✓ Status: {progress.get('status', 'unknown')}")
        
        elapsed = progress.get('elapsed_seconds', 0)
        if elapsed:
            logger.info(f"✓ Elapsed time: {elapsed:.1f}s")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Progress persistence test failed: {e}", exc_info=True)
        return False


def run_full_integration_test():
    """Run complete end-to-end integration test."""
    logger.info("\n" + "="*80)
    logger.info("BUDDY MISSION INTEGRATION TEST SUITE")
    logger.info("Testing all 4 critical fixes")
    logger.info("="*80)
    
    results = {
        'recipe_instantiation': False,
        'mission_approval': False,
        'plan_storage': False,
        'mission_execution': False,
        'progress_persistence': False,
    }
    
    # Test 1: Recipe Instantiation
    mission_id = test_recipe_instantiation()
    results['recipe_instantiation'] = mission_id is not None
    
    if not mission_id:
        logger.error("\n✗ STOPPING: Recipe instantiation failed")
        return results
    
    # Test 2: Mission Approval
    results['mission_approval'] = test_mission_approval(mission_id)
    
    if not results['mission_approval']:
        logger.error("\n✗ STOPPING: Mission approval failed")
        return results
    
    # Test 3: Plan Storage
    stored_plan = test_mission_planning(mission_id)
    results['plan_storage'] = stored_plan is not None
    
    # Test 4: Mission Execution
    execution_result = test_mission_execution(mission_id, stored_plan)
    results['mission_execution'] = execution_result is not None and execution_result.get('success')
    
    if not results['mission_execution']:
        logger.warning("\n⚠ Execution failed or incomplete - progress test may fail")
    
    # Wait a moment for progress to persist
    time.sleep(1)
    
    # Test 5: Progress Persistence
    results['progress_persistence'] = test_progress_persistence(mission_id)
    
    # Final Report
    logger.info("\n" + "="*80)
    logger.info("FINAL RESULTS")
    logger.info("="*80)
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{status}: {test_name.replace('_', ' ').title()}")
    
    logger.info("-"*80)
    logger.info(f"TOTAL: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        logger.info("🎉 ALL TESTS PASSED! Mission system fully integrated!")
    elif passed_tests >= 4:
        logger.info("✓ Most tests passed - system functional with minor issues")
    else:
        logger.error("✗ Multiple tests failed - system needs fixes")
    
    logger.info("="*80 + "\n")
    
    return results


if __name__ == '__main__':
    try:
        results = run_full_integration_test()
        sys.exit(0 if all(results.values()) else 1)
    except KeyboardInterrupt:
        logger.info("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n\nTest suite failed with error: {e}", exc_info=True)
        sys.exit(1)
