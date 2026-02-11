"""
Live test: web extraction → artifact → follow-up answer
"""

from Back_End.interaction_orchestrator import orchestrate_message
from Back_End.mission_approval_service import approve_mission
from Back_End.execution_service import execute_mission
from Back_End.artifact_reader import get_latest_artifact
import json
from pathlib import Path
from Back_End.tool_registry import tool_registry
from backend import tools, web_tools


def run():
    # Ensure tools are registered for this standalone test
    tools.register_foundational_tools(tool_registry)
    web_tools.register_web_tools(tool_registry)

    # 1) Ask Buddy
    response = orchestrate_message(
        message="Extract the title from https://example.com",
        session_id="artifact_test_session",
        user_id="tester",
        context=None,
        trace_id="trace_artifact_test"
    )

    if not response.missions_spawned:
        print("❌ No mission created")
        return

    mission_id = response.missions_spawned[0].mission_id
    print(f"✅ Mission created: {mission_id}")

    # 2) Approve manually
    approval = approve_mission(mission_id)
    print(f"✅ Mission approved: {approval}")

    # 3) Execute
    result = execute_mission(mission_id)
    print(f"✅ Execution result: {result}")

    # Capture execution record count before follow-up
    missions_file = Path("outputs/phase25/missions.jsonl")
    execution_count_before = 0
    if missions_file.exists():
        with missions_file.open("r", encoding="utf-8") as handle:
            for line in handle:
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if record.get("event_type") == "mission_executed" and record.get("mission_id") == mission_id:
                    execution_count_before += 1

    # 4) Verify artifact
    artifact = get_latest_artifact(mission_id=mission_id)
    if artifact:
        print("✅ Artifact written to artifacts.jsonl")
        print(f"Artifact ID: {artifact.get('artifact_id')}")
        print(f"Artifact Type: {artifact.get('artifact_type')}")
    else:
        print("❌ No artifact found for mission")

    # 5) Ask follow-up
    follow_up = orchestrate_message(
        message="What did you find?",
        session_id="artifact_test_session",
        user_id="tester",
        context={"mission_id": mission_id},
        trace_id="trace_artifact_followup"
    )

    print("✅ Follow-up response:")
    print(follow_up.summary)

    # Verify no re-execution occurred
    execution_count_after = 0
    if missions_file.exists():
        with missions_file.open("r", encoding="utf-8") as handle:
            for line in handle:
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if record.get("event_type") == "mission_executed" and record.get("mission_id") == mission_id:
                    execution_count_after += 1

    if execution_count_after == execution_count_before:
        print("✅ No re-execution occurred during follow-up")
    else:
        print("❌ Execution re-ran during follow-up")


if __name__ == "__main__":
    run()

