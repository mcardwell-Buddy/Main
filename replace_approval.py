import re

# Read file
with open(r'c:\Users\micha\Buddy\backend\interaction_orchestrator.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Define new function
new_function = """    def _handle_approval_bridge(self, message: str, session_id: str) -> ResponseEnvelope:
        \"\"\"
        Handle approval phrases ("yes", "approve", "do it").
        
        PHASE 3C: Uses pending mission from session context (single source of truth).
        
        Returns:
            ResponseEnvelope with execution results or error message
        \"\"\"
        # Get session context
        session_context_obj = self._session_context_manager.get_or_create(session_id)
        
        # Check for pending mission
        pending_mission = session_context_obj.get_pending_mission()
        if not pending_mission:
            return text_response("There's nothing to approve yet.")
        
        mission_id = pending_mission.get('mission_id')
        if not mission_id:
            return text_response("There's nothing to approve yet.")

        # Verify mission is still in proposed state
        status = self._get_latest_mission_status(mission_id)
        if status != 'proposed':
            # Clear stale pending mission
            session_context_obj.clear_pending_mission()
            return text_response("There's nothing to approve yet.")

        from Back_End.mission_approval_service import approve_mission
        from Back_End.execution_service import execute_mission

        # Approve the mission
        approval_result = approve_mission(mission_id)
        if not approval_result.get('success'):
            error_msg = approval_result.get('message', 'Approval failed')
            return text_response(f"Approval failed: {error_msg}")

        # Execute the mission
        exec_result = execute_mission(mission_id)
        if not exec_result.get('success'):
            error_msg = exec_result.get('error', 'Execution failed')
            return text_response(f"Execution failed: {error_msg}")

        # Clear pending mission after successful execution
        session_context_obj.clear_pending_mission()

        tool_used = exec_result.get('tool_used') or 'unknown'
        result_summary = exec_result.get('result_summary') or 'Execution completed.'
        artifact_message = exec_result.get('artifact_message')

        response_lines = [
            f"Approved and executed mission {mission_id}.",
            f"Tool used: {tool_used}",
            result_summary
        ]
        if artifact_message:
            response_lines.append(artifact_message)

        return text_response("\\n".join(response_lines))"""

# Replace using regex to match the entire function
pattern = r'    def _handle_approval_bridge\(self, message: str, session_id: str\) -> ResponseEnvelope:.*?return text_response\("\\\\n"\.join\(response_lines\)\)'
content = re.sub(pattern, new_function, content, flags=re.DOTALL)

# Write back
with open(r'c:\Users\micha\Buddy\backend\interaction_orchestrator.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Replaced approval handler successfully')

