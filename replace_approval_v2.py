with open(r'c:\Users\micha\Buddy\backend\interaction_orchestrator.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# New function implementation (lines 592-627 inclusive will be replaced)
new_function_lines = [
    "    def _handle_approval_bridge(self, message: str, session_id: str) -> ResponseEnvelope:\n",
    "        \"\"\"\n",
    "        Handle approval phrases (\"yes\", \"approve\", \"do it\").\n",
    "        \n",
    "        PHASE 3C: Uses pending mission from session context (single source of truth).\n",
    "        \n",
    "        Returns:\n",
    "            ResponseEnvelope with execution results or error message\n",
    "        \"\"\"\n",
    "        # Get session context\n",
    "        session_context_obj = self._session_context_manager.get_or_create(session_id)\n",
    "        \n",
    "        # Check for pending mission\n",
    "        pending_mission = session_context_obj.get_pending_mission()\n",
    "        if not pending_mission:\n",
    "            return text_response(\"There's nothing to approve yet.\")\n",
    "        \n",
    "        mission_id = pending_mission.get('mission_id')\n",
    "        if not mission_id:\n",
    "            return text_response(\"There's nothing to approve yet.\")\n",
    "\n",
    "        # Verify mission is still in proposed state\n",
    "        status = self._get_latest_mission_status(mission_id)\n",
    "        if status != 'proposed':\n",
    "            # Clear stale pending mission\n",
    "            session_context_obj.clear_pending_mission()\n",
    "            return text_response(\"There's nothing to approve yet.\")\n",
    "\n",
    "        from Back_End.mission_approval_service import approve_mission\n",
    "        from Back_End.execution_service import execute_mission\n",
    "\n",
    "        # Approve the mission\n",
    "        approval_result = approve_mission(mission_id)\n",
    "        if not approval_result.get('success'):\n",
    "            error_msg = approval_result.get('message', 'Approval failed')\n",
    "            return text_response(f\"Approval failed: {error_msg}\")\n",
    "\n",
    "        # Execute the mission\n",
    "        exec_result = execute_mission(mission_id)\n",
    "        if not exec_result.get('success'):\n",
    "            error_msg = exec_result.get('error', 'Execution failed')\n",
    "            return text_response(f\"Execution failed: {error_msg}\")\n",
    "\n",
    "        # Clear pending mission after successful execution\n",
    "        session_context_obj.clear_pending_mission()\n",
    "\n",
    "        tool_used = exec_result.get('tool_used') or 'unknown'\n",
    "        result_summary = exec_result.get('result_summary') or 'Execution completed.'\n",
    "        artifact_message = exec_result.get('artifact_message')\n",
    "\n",
    "        response_lines = [\n",
    "            f\"Approved and executed mission {mission_id}.\",\n",
    "            f\"Tool used: {tool_used}\",\n",
    "            result_summary\n",
    "        ]\n",
    "        if artifact_message:\n",
    "            response_lines.append(artifact_message)\n",
    "\n",
    "        return text_response(\"\\n\".join(response_lines))\n",
]

# Replace lines 592-627 (36 lines) with new function
new_lines = lines[:592] + new_function_lines + lines[628:]

# Write back
with open(r'c:\Users\micha\Buddy\backend\interaction_orchestrator.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f'Replaced {len(lines[592:628])} lines with {len(new_function_lines)} lines')
print('Approval handler updated successfully')

