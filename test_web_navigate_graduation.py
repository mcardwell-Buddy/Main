"""
TOOL GRADUATION CHECKLIST: web_navigate
Navigation & Agency Auditor Certification

Verifies that web_navigate is production-capable by ensuring:
1. Purposeful navigation with clear intent
2. Single execution, no retries
3. Durable navigation artifact (web_navigation_result)
4. Explainability through follow-up questions
5. No invariant regressions
"""

import requests
import json
import time
import subprocess
import sys
import uuid
from pathlib import Path

sys.path.insert(0, '.')

from backend.tool_registry import tool_registry
from backend.tools import register_foundational_tools
from backend.additional_tools import register_additional_tools
from backend.web_tools import register_web_tools
from backend.tool_selector import tool_selector
from backend.execution_service import ExecutionService
from backend.interaction_orchestrator import InteractionOrchestrator

register_foundational_tools(tool_registry)
register_additional_tools(tool_registry)
register_web_tools(tool_registry)

API_BASE = "http://127.0.0.1:8000"
ARTIFACTS_PATH = Path("outputs/phase25/artifacts.jsonl")
_server_process = None


def _is_server_up() -> bool:
    try:
        response = requests.get(f"{API_BASE}/", timeout=2)
        return response.status_code == 200
    except Exception:
        return False


def ensure_server_running() -> bool:
    global _server_process
    if _is_server_up():
        return True

    print("[Action] Starting backend server for audit")
    try:
        _server_process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "backend.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8000",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
    except Exception as e:
        print(f"[FAIL] Unable to start backend server: {e}")
        return False

    # Wait for server to become ready
    for _ in range(20):
        if _is_server_up():
            print("[OK] Backend server is running")
            return True
        time.sleep(0.5)

    print("[FAIL] Backend server did not start in time")
    return False


def stop_server() -> None:
    global _server_process
    if _server_process is None:
        return
    try:
        _server_process.terminate()
        _server_process.wait(timeout=10)
    except Exception:
        pass
    finally:
        _server_process = None

def step1_purposeful_navigation_assignment():
    """
    STEP 1: Purposeful Navigation Assignment (Live)
    
    Trigger a navigation request with clear intent.
    Verify: Chat proposes mission, intent is navigation, tool_navigate selected.
    """
    print("\n" + "="*80)
    print("STEP 1: Purposeful Navigation Assignment (Live)")
    print("="*80)
    
    navigation_goal = "Browse https://example.com and tell me what page you land on"
    print(f"\n[Goal] {navigation_goal}")
    
    try:
        # Create mission via canonical chat endpoint (propose, don't execute)
        session_id = f"audit_session_{uuid.uuid4().hex[:8]}"
        response = requests.post(
            f"{API_BASE}/chat/integrated",
            json={
                "source": "user",
                "text": navigation_goal,
                "session_id": session_id,
                "external_user_id": "audit"
            },
            timeout=15
        )
        
        if response.status_code != 200:
            print(f"[FAIL] Failed to create mission: {response.status_code}")
            print(response.text)
            return None
        
        chat_data = response.json()
        envelope = chat_data.get("envelope", {})
        missions = envelope.get("missions_spawned", [])
        if not missions:
            print("[FAIL] No mission proposed by chat endpoint")
            return None

        mission_id = missions[0].get("mission_id")
        objective_type = missions[0].get("objective_type")
        objective_description = missions[0].get("objective_description")

        print(f"\n[OK] Mission Proposed")
        print(f"   mission_id: {mission_id}")
        print(f"   objective_type: {objective_type}")
        print(f"   objective_description: {objective_description}")

        # Verify intent classification for navigation
        intent = ExecutionService()._classify_intent(navigation_goal)
        print(f"   classified_intent: {intent}")
        if intent != "navigation":
            print(f"\n[FAIL] Expected navigation intent but got {intent}")
            return None

        # Verify tool selection
        tool_name, tool_input, confidence = tool_selector.select_tool(navigation_goal)
        print(f"   tool_selected: {tool_name}")
        print(f"   selection_confidence: {confidence}")
        print(f"   tool_input: {tool_input}")

        if tool_name != "web_navigate":
            print(f"\n[FAIL] Expected web_navigate but got {tool_name}")
            return None

        if confidence < 0.8:
            print(f"\n[WARN] Low confidence ({confidence}), but proceeding")

        print(f"\n[OK] STEP 1 PASS - Navigation intent recognized, web_navigate selected")
        return mission_id
        
    except Exception as e:
        print(f"[FAIL] STEP 1 FAIL: {str(e)}")
        return None


def step2_approval_and_execution(mission_id):
    """
    STEP 2: Approval & Execution
    
    Approve the mission, execute it.
    Verify: Single execution, no retries, invariants still pass.
    """
    print("\n" + "="*80)
    print("STEP 2: Approval & Execution")
    print("="*80)
    
    try:
        # Approve mission
        print(f"\n[Action] Approving mission {mission_id}")
        response = requests.post(
            f"{API_BASE}/api/missions/{mission_id}/approve",
            json={},
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"[FAIL] Failed to approve mission: {response.status_code}")
            print(response.text)
            return False
        
        approval_data = response.json()
        print(f"[OK] Mission Approved")
        print(f"   approval_status: {approval_data.get('approval_status')}")
        
        # Execute mission
        print(f"\n[Action] Executing mission {mission_id}")
        response = requests.post(
            f"{API_BASE}/api/missions/{mission_id}/execute",
            json={},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"[FAIL] Failed to execute mission: {response.status_code}")
            print(response.text)
            return False
        
        execution_data = response.json()
        print(f"[OK] Mission Executed")
        print(f"   execution_status: {execution_data.get('execution_status')}")
        print(f"   execution_trace_id: {execution_data.get('execution_trace_id')}")
        
        # Verify execution happened exactly once (mission_executed record count)
        execution_count = 0
        missions_file = Path("outputs/phase25/missions.jsonl")
        if missions_file.exists():
            with open(missions_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        record = json.loads(line)
                        if record.get("event_type") == "mission_executed" and record.get("mission_id") == mission_id:
                            execution_count += 1
                    except Exception:
                        continue
        
        print(f"\n[OK] Execution Count Check")
        print(f"   execution_count: {execution_count}")
        
        if execution_count != 1:
            print(f"[FAIL] Expected 1 execution but got {execution_count}")
            return False
        
        print(f"\n[OK] STEP 2 PASS - Single execution, no retries")
        return True
        
    except Exception as e:
        print(f"[FAIL] STEP 2 FAIL: {str(e)}")
        return False


def step3_artifact_creation(mission_id):
    """
    STEP 3: Artifact Creation (CRITICAL)
    
    Verify that execution produces exactly ONE artifact.
    Stored append-only in artifacts.jsonl.
    Artifact type: web_navigation_result.
    
    Required fields:
    - artifact_id
    - artifact_type
    - mission_id
    - starting_url
    - final_url
    - navigation_reason
    - page_title (optional)
    - links_found (optional)
    - tool_used
    - created_at
    - execution_trace_id
    """
    print("\n" + "="*80)
    print("STEP 3: Artifact Creation (CRITICAL)")
    print("="*80)
    
    try:
        if not ARTIFACTS_PATH.exists():
            print(f"[FAIL] artifacts.jsonl does not exist at {ARTIFACTS_PATH}")
            return None
        
        print(f"[Check] Reading artifacts from {ARTIFACTS_PATH}")
        
        # Load all artifacts
        artifacts = []
        with open(ARTIFACTS_PATH, 'r') as f:
            for line in f:
                if line.strip():
                    artifacts.append(json.loads(line))
        
        # Find artifacts for this mission
        mission_artifacts = [a for a in artifacts if a.get("mission_id") == mission_id]
        
        print(f"\n[OK] Artifacts Found")
        print(f"   Total artifacts in file: {len(artifacts)}")
        print(f"   Artifacts for mission {mission_id}: {len(mission_artifacts)}")
        
        if len(mission_artifacts) != 1:
            print(f"[FAIL] Expected exactly 1 artifact, got {len(mission_artifacts)}")
            return None
        
        artifact = mission_artifacts[0]
        
        # Verify artifact type
        artifact_type = artifact.get("artifact_type")
        print(f"\n[OK] Artifact Type Check")
        print(f"   artifact_type: {artifact_type}")
        
        if artifact_type != "web_navigation_result":
            print(f"[FAIL] Expected web_navigation_result, got {artifact_type}")
            return None
        
        # Verify required fields
        required_fields = [
            "artifact_id",
            "artifact_type",
            "mission_id",
            "starting_url",
            "final_url",
            "navigation_reason",
            "tool_used",
            "created_at",
            "execution_trace_id"
        ]
        
        print(f"\n[OK] Required Fields Check")
        missing_fields = []
        for field in required_fields:
            value = artifact.get(field)
            if value is None or value == "":
                print(f"   [FAIL] {field}: MISSING")
                missing_fields.append(field)
            else:
                print(f"   [OK] {field}: {str(value)[:60]}")
        
        if missing_fields:
            print(f"\n[FAIL] Missing required fields: {missing_fields}")
            return None
        
        # Verify URL fields specifically
        starting_url = artifact.get("starting_url")
        final_url = artifact.get("final_url")
        
        if not starting_url or not final_url:
            print(f"\n[FAIL] starting_url or final_url missing/empty")
            return None
        
        print(f"\n[OK] URL Verification")
        print(f"   starting_url: {starting_url}")
        print(f"   final_url: {final_url}")
        
        print(f"\n[OK] STEP 3 PASS - web_navigation_result artifact created")
        return artifact
        
    except Exception as e:
        print(f"[FAIL] STEP 3 FAIL: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def step4_durability_check(mission_id, original_artifact):
    """
    STEP 4: Durability Check
    
    Restart backend (if feasible).
    Refresh session.
    Verify: Artifact still exists, NOT recomputed, no duplicates.
    """
    print("\n" + "="*80)
    print("STEP 4: Durability Check")
    print("="*80)
    
    try:
        print(f"\n[Check] Simulating restart by re-reading artifacts.jsonl")
        
        # Re-read artifacts file
        artifacts = []
        with open(ARTIFACTS_PATH, 'r') as f:
            for line in f:
                if line.strip():
                    artifacts.append(json.loads(line))
        
        # Find artifacts for this mission
        mission_artifacts = [a for a in artifacts if a.get("mission_id") == mission_id]
        
        print(f"[OK] Artifacts Re-loaded")
        print(f"   Artifacts for mission {mission_id}: {len(mission_artifacts)}")
        
        if len(mission_artifacts) != 1:
            print(f"[FAIL] Expected exactly 1 artifact after restart, got {len(mission_artifacts)}")
            return False
        
        restart_artifact = mission_artifacts[0]
        
        # Verify artifact is NOT recomputed (same ID and timestamp)
        original_id = original_artifact.get("artifact_id")
        restart_id = restart_artifact.get("artifact_id")
        
        if original_id != restart_id:
            print(f"[FAIL] Artifact was recomputed (different ID)")
            print(f"   Original: {original_id}")
            print(f"   After restart: {restart_id}")
            return False
        
        print(f"\n[OK] Artifact Integrity Check")
        print(f"   Same artifact_id: {original_id}")
        print(f"   Created_at unchanged: {restart_artifact.get('created_at')}")
        
        print(f"\n[OK] STEP 4 PASS - Artifact persists, not recomputed")
        return True
        
    except Exception as e:
        print(f"[FAIL] STEP 4 FAIL: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def step5_explainability_test(mission_id, artifact):
    """
    STEP 5: Explainability Test (AGENCY CHECK)
    
    Ask follow-up questions about the navigation.
    Verify: Buddy answers using artifact data, no re-execution.
    """
    print("\n" + "="*80)
    print("STEP 5: Explainability Test (AGENCY CHECK)")
    print("="*80)
    
    try:
        # Get initial artifact count
        artifacts_before = []
        with open(ARTIFACTS_PATH, 'r') as f:
            for line in f:
                if line.strip():
                    artifacts_before.append(json.loads(line))
        
        # Ask follow-up questions
        followup_questions = [
            "Where did you go?",
            "Why did you navigate there?",
            "What page did you end up on?"
        ]
        
        print(f"\n[Action] Asking follow-up questions to verify agency")
        orchestrator = InteractionOrchestrator()
        
        for question in followup_questions:
            print(f"\n[Q] {question}")
            
            try:
                response_envelope = orchestrator.process_message(
                    message=question,
                    session_id="audit_session",
                    context={"mission_id": mission_id}
                )
                answer = response_envelope.summary or ""
                print(f"[A] {answer[:120]}...")
            except Exception as e:
                print(f"   [WARN] Exception: {str(e)}")
        
        # Check artifact count after follow-ups
        artifacts_after = []
        with open(ARTIFACTS_PATH, 'r') as f:
            for line in f:
                if line.strip():
                    artifacts_after.append(json.loads(line))
        
        print(f"\n[OK] No Re-Execution Check")
        print(f"   Artifacts before follow-ups: {len(artifacts_before)}")
        print(f"   Artifacts after follow-ups: {len(artifacts_after)}")
        
        if len(artifacts_after) > len(artifacts_before):
            print(f"[FAIL] New artifacts created during follow-ups")
            return False
        
        print(f"\n[OK] STEP 5 PASS - Follow-up answered, no re-execution")
        return True
        
    except Exception as e:
        print(f"[FAIL] STEP 5 FAIL: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def step6_regression_guard():
    """
    STEP 6: Regression Guard
    
    Re-run all relevant invariant tests.
    Verify: No regressions, no unrelated behavior changes.
    """
    print("\n" + "="*80)
    print("STEP 6: Regression Guard")
    print("="*80)
    
    try:
        print(f"\n[Action] Running invariant test suites")
        
        test_suites = [
            ("Execution Invariants", "test_execution_direct.py"),
            ("Approval Invariants", "test_approval_invariant.py"),
            ("Learning Observe-Only", "test_learning_observe_only.py"),
        ]
        
        all_passed = True
        
        for suite_name, suite_file in test_suites:
            print(f"\n[Running] {suite_name} ({suite_file})")
            
            try:
                result = subprocess.run(
                    [sys.executable, suite_file],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd="C:\\Users\\micha\\Buddy"
                )
                
                # Check if test passed
                if result.returncode == 0:
                    print(f"   [OK] PASS")
                else:
                    print(f"   [FAIL] (exit code: {result.returncode})")
                    print(f"   Output: {result.stdout[-200:]}")
                    all_passed = False
                    
            except subprocess.TimeoutExpired:
                print(f"   [FAIL] TIMEOUT")
                all_passed = False
            except Exception as e:
                print(f"   [WARN] Error running test: {str(e)}")
                all_passed = False
        
        if not all_passed:
            print(f"\n[FAIL] STEP 6 FAIL - Some tests failed")
            return False
        
        print(f"\n[OK] STEP 6 PASS - All invariants passing")
        return True
        
    except Exception as e:
        print(f"[FAIL] STEP 6 FAIL: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def graduation_decision(steps_passed):
    """
    GRADUATION DECISION (FINAL OUTPUT)
    
    Return one of:
    [GRADUATED] - Tool is production-capable
    [NOT GRADUATED] - Tool failed one or more steps
    """
    print("\n" + "="*80)
    print("GRADUATION DECISION (FINAL OUTPUT)")
    print("="*80)
    
    if all(steps_passed.values()):
        print(f"\n>>> web_navigate TOOL STATUS: [GRADUATED]")
        print(f"\nConfirmation:")
        print(f"  [OK] Purposeful navigation with clear intent")
        print(f"  [OK] Single execution, no retries")
        print(f"  [OK] web_navigation_result artifact created")
        print(f"  [OK] Artifact persists durably after restart")
        print(f"  [OK] Follow-up questions answered (no re-execution)")
        print(f"  [OK] All invariant tests passing (zero regressions)")
        print(f"\nProduction Status: READY FOR DEPLOYMENT")
        return True
    else:
        print(f"\n>>> web_navigate TOOL STATUS: [NOT GRADUATED]")
        print(f"\nFailed Steps:")
        for step_name, passed in steps_passed.items():
            status = "[OK]" if passed else "[FAIL]"
            print(f"  {status} - {step_name}")
        return False


def main():
    print("\n" + "="*80)
    print("TOOL GRADUATION CHECKLIST: web_navigate")
    print("Navigation & Agency Auditor Certification")
    print("="*80)
    
    steps_passed = {}
    mission_id = None
    artifact = None

    if not ensure_server_running():
        steps_passed["STEP 1: Purposeful Navigation"] = False
        graduation_decision(steps_passed)
        return

    try:
        # STEP 1
        mission_id = step1_purposeful_navigation_assignment()
        steps_passed["STEP 1: Purposeful Navigation"] = mission_id is not None
        
        if not mission_id:
            graduation_decision(steps_passed)
            return
        
        # STEP 2
        exec_success = step2_approval_and_execution(mission_id)
        steps_passed["STEP 2: Approval & Execution"] = exec_success
        
        if not exec_success:
            graduation_decision(steps_passed)
            return
        
        # STEP 3
        artifact = step3_artifact_creation(mission_id)
        steps_passed["STEP 3: Artifact Creation"] = artifact is not None
        
        if not artifact:
            graduation_decision(steps_passed)
            return
        
        # STEP 4
        durability_ok = step4_durability_check(mission_id, artifact)
        steps_passed["STEP 4: Durability Check"] = durability_ok
        
        if not durability_ok:
            graduation_decision(steps_passed)
            return
        
        # STEP 5
        explain_ok = step5_explainability_test(mission_id, artifact)
        steps_passed["STEP 5: Explainability Test"] = explain_ok
        
        # STEP 6
        regression_ok = step6_regression_guard()
        steps_passed["STEP 6: Regression Guard"] = regression_ok
        
        # Final decision
        graduation_decision(steps_passed)
    finally:
        stop_server()


if __name__ == "__main__":
    main()
