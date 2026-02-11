import sys
sys.path.insert(0, '.')

from Back_End.tool_registry import tool_registry
from Back_End.tools import register_foundational_tools
from Back_End.additional_tools import register_additional_tools
from Back_End.web_tools import register_web_tools
from Back_End.interaction_orchestrator import orchestrate_message

register_foundational_tools(tool_registry)
register_additional_tools(tool_registry)
register_web_tools(tool_registry)

session_id = "approval_bridge_session"

print("STEP 1: Request navigation mission")
resp1 = orchestrate_message("Browse https://example.com and tell me what page you land on", session_id=session_id)
print(resp1.summary)
mission_id_nav = resp1.missions_spawned[0].mission_id if resp1.missions_spawned else None
print(f"navigation_mission_id: {mission_id_nav}")

print("\nSTEP 2: Approve via chat")
resp2 = orchestrate_message("yes", session_id=session_id)
print(resp2.summary)

print("\nSTEP 3: Request extraction mission")
resp3 = orchestrate_message("Extract the title from https://example.com", session_id=session_id)
print(resp3.summary)
mission_id_extract = resp3.missions_spawned[0].mission_id if resp3.missions_spawned else None
print(f"extraction_mission_id: {mission_id_extract}")

print("\nSTEP 4: Approve via chat")
resp4 = orchestrate_message("approve", session_id=session_id)
print(resp4.summary)

print("\nSTEP 5: Follow-up")
resp5 = orchestrate_message("What did you find?", session_id=session_id, context={"mission_id": mission_id_extract})
print(resp5.summary)

