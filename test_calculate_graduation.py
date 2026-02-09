import sys
import json
import uuid
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, '.')

# Step: Create mission directly for calculate tool
mission_id = f"mission_calc_{uuid.uuid4().hex[:8]}"
mission_record = {
    "mission_id": mission_id,
    "status": "proposed",
    "intent": "calculation",
    "raw_chat_message": "Calculate 999 * 888 + 777",
    "tool_selected": "calculate",
    "tool_input": "999 * 888 + 777",
    "objective_description": "Perform the calculation: 999 * 888 + 777",
    "created_at": datetime.now(timezone.utc).isoformat(),
    "created_by": "test_graduation_checklist"
}

missions_file = Path("outputs/phase25/missions.jsonl")
missions_file.parent.mkdir(parents=True, exist_ok=True)

# Write mission record
with open(missions_file, "a", encoding="utf-8") as f:
    f.write(json.dumps(mission_record) + "\n")

print(f"✅ Created mission: {mission_id}")
print(f"   Intent: {mission_record['intent']}")
print(f"   Tool: {mission_record['tool_selected']}")
print(f"   Expression: {mission_record['tool_input']}")
print()

# Now test approval
from backend.mission_approval_service import approve_mission

print("=" * 60)
print("STEP 2: APPROVAL & EXECUTION")
print("=" * 60)

# Approve mission
approval_result = approve_mission(mission_id)
print(f"✅ Approval Result: {approval_result}")
print()

# Execute mission  
from backend.execution_service import ExecutionService

execution_service = ExecutionService()
execution_result = execution_service.execute_mission(mission_id)

print(f"✅ Execution Result (FULL):")
print(json.dumps(execution_result, indent=2, default=str))
print()

# Check for artifacts
print("=" * 60)
print("STEP 3: ARTIFACT CREATION CHECK")
print("=" * 60)

artifacts_file = Path("outputs/phase25/artifacts.jsonl")
if artifacts_file.exists():
    with open(artifacts_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    # Look for our mission's artifact
    found_artifact = False
    last_artifact = None
    for line in lines:
        try:
            artifact = json.loads(line.strip())
            if artifact.get("mission_id") == mission_id:
                found_artifact = True
                last_artifact = artifact
        except:
            pass
    
    if found_artifact:
        print(f"✅ ARTIFACT FOUND for mission {mission_id}")
        print(f"   Artifact Type: {last_artifact.get('artifact_type')}")
        print(f"   Full Artifact:")
        print(json.dumps(last_artifact, indent=2))
    else:
        print(f"❌ NO ARTIFACT FOUND for mission {mission_id}")
        print(f"   Total artifacts in file: {len(lines)}")
else:
    print(f"❌ Artifacts file does not exist: {artifacts_file}")

