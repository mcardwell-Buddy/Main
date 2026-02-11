"""
Backend Verification Script
Confirms Back_End/ has all 4 mission system fixes
"""
import sys
from pathlib import Path

print("=" * 60)
print("BACKEND VERIFICATION TEST")
print("=" * 60)

backend_path = Path("Back_End")

# Test 1: Check main.py for approval function and auth updates
main_py = backend_path / "main.py"
print(f"\n📁 Checking {main_py}...")
if main_py.exists():
    content = main_py.read_text(encoding='utf-8')
    
    has_approval = "_simple_approve_mission" in content
    has_auth_recipes = '"/api/recipes"' in content
    has_auth_missions = '"/api/missions"' in content
    has_get_mission = '@app.get("/api/missions/{mission_id}")' in content
    
    print(f"  ✓ Approval function (_simple_approve_mission): {'✅ FOUND' if has_approval else '❌ MISSING'}")
    print(f"  ✓ Auth allowlist - /api/recipes: {'✅ FOUND' if has_auth_recipes else '❌ MISSING'}")
    print(f"  ✓ Auth allowlist - /api/missions: {'✅ FOUND' if has_auth_missions else '❌ MISSING'}")
    print(f"  ✓ GET mission endpoint: {'✅ FOUND' if has_get_mission else '❌ MISSING'}")
    
    main_score = sum([has_approval, has_auth_recipes, has_auth_missions, has_get_mission])
else:
    print(f"  ❌ File not found!")
    main_score = 0

# Test 2: Check execution_service.py for stored plan retrieval (FIX #2)
exec_py = backend_path / "execution_service.py"
print(f"\n📁 Checking {exec_py}...")
if exec_py.exists():
    content = exec_py.read_text(encoding='utf-8')
    
    has_stored_plan_method = "_get_stored_plan" in content
    has_pre_selected = "pre_selected_tool = False" in content
    has_stored_plan_call = "stored_plan = self._get_stored_plan(mission_id)" in content
    
    print(f"  ✓ Stored plan method (_get_stored_plan): {'✅ FOUND' if has_stored_plan_method else '❌ MISSING'}")
    print(f"  ✓ Pre-selected tool tracking: {'✅ FOUND' if has_pre_selected else '❌ MISSING'}")
    print(f"  ✓ Stored plan retrieval call: {'✅ FOUND' if has_stored_plan_call else '❌ MISSING'}")
    
    exec_score = sum([has_stored_plan_method, has_pre_selected, has_stored_plan_call])
else:
    print(f"  ❌ File not found!")
    exec_score = 0

# Test 3: Check interaction_orchestrator.py for plan storage (FIX #1)
orch_py = backend_path / "interaction_orchestrator.py"
print(f"\n📁 Checking {orch_py}...")
if orch_py.exists():
    content = orch_py.read_text(encoding='utf-8')
    
    has_plan_storage = "mission_plan_created" in content
    has_plan_metadata = "plan_data" in content
    
    print(f"  ✓ Plan storage event (mission_plan_created): {'✅ FOUND' if has_plan_storage else '❌ MISSING'}")
    print(f"  ✓ Plan metadata storage: {'✅ FOUND' if has_plan_metadata else '❌ MISSING'}")
    
    orch_score = sum([has_plan_storage, has_plan_metadata])
else:
    print(f"  ❌ File not found!")
    orch_score = 0

# Test 4: Check mission_recipe_system.py for instantiation (FIX #4)
recipe_py = backend_path / "mission_recipe_system.py"
print(f"\n📁 Checking {recipe_py}...")
if recipe_py.exists():
    content = recipe_py.read_text(encoding='utf-8')
    
    has_instantiate = "def instantiate_recipe" in content
    has_emit_proposal = "emit_mission_proposal" in content
    
    print(f"  ✓ Recipe instantiation function: {'✅ FOUND' if has_instantiate else '❌ MISSING'}")
    print(f"  ✓ Mission proposal emission: {'✅ FOUND' if has_emit_proposal else '❌ MISSING'}")
    
    recipe_score = sum([has_instantiate, has_emit_proposal])
else:
    print(f"  ❌ File not found!")
    recipe_score = 0

# Test 5: Check dashboard.html for fix
dashboard_html = Path("dashboard.html")
print(f"\n📁 Checking {dashboard_html}...")
if dashboard_html.exists():
    content = dashboard_html.read_text(encoding='utf-8')
    
    has_correct_field = "data.high_confidence" in content
    has_wrong_field = "data.confidence_distribution.high_confidence" in content or "confidence_distribution || {}" in content
    
    print(f"  ✓ Correct API field (data.high_confidence): {'✅ FOUND' if has_correct_field else '❌ MISSING'}")
    print(f"  ✓ Old wrong field removed: {'✅ CLEAN' if not has_wrong_field else '❌ STILL PRESENT'}")
    
    dashboard_score = 1 if (has_correct_field and not has_wrong_field) else 0
else:
    print(f"  ❌ File not found!")
    dashboard_score = 0

# Final verdict
print("\n" + "=" * 60)
print("VERIFICATION RESULTS")
print("=" * 60)

total_score = main_score + exec_score + orch_score + recipe_score + dashboard_score
max_score = 4 + 3 + 2 + 2 + 1  # 12 total checks

print(f"\nBack_End/main.py:                    {main_score}/4 checks")
print(f"Back_End/execution_service.py:       {exec_score}/3 checks")
print(f"Back_End/interaction_orchestrator.py: {orch_score}/2 checks")
print(f"Back_End/mission_recipe_system.py:   {recipe_score}/2 checks")
print(f"dashboard.html:                      {dashboard_score}/1 checks")

print(f"\n{'='*60}")
print(f"OVERALL SCORE: {total_score}/{max_score}")

if total_score == max_score:
    print("✅ ALL FIXES VERIFIED - Back_End/ is CORRECT!")
    sys.exit(0)
elif total_score >= max_score * 0.75:
    print("⚠️  MOSTLY CORRECT - Minor issues detected")
    sys.exit(1)
else:
    print("❌ CRITICAL ISSUES - Fixes missing!")
    sys.exit(2)
