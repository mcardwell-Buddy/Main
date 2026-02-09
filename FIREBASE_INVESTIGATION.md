# Firebase Persistence Investigation & Fix Plan

## Current Status Summary
- ✅ Firebase credentials configured and loaded
- ✅ Session creation syncs to Firebase (ConversationStore working)
- ✅ Chat messages sync to Firebase (append_message working)
- ⚠️ Agent learning data NOT syncing (memory_manager calls exist but not connected)
- ⚠️ Extract intent errors blocking workflows
- ❓ Other core logic persistence unclear

## Investigation Needed

### Phase 1: Map All Data That Should Persist
1. Session data (messages, metadata) - Status: ✅ WORKING
2. Goal completions and reflections - Status: ❓ UNKNOWN
3. Tool feedback and learning - Status: ❓ UNKNOWN  
4. Knowledge graph and relationships - Status: ❓ UNKNOWN
5. Observations from executions - Status: ❓ UNKNOWN
6. Learning synthesis - Status: ❓ UNKNOWN

### Phase 2: Identify Data Flow Bottlenecks
- Where are save_if_important() calls made?
- What memory backend are they using?
- Are they using MockMemory or FirebaseMemory?
- What happens to data after save_if_important()?

### Phase 3: Test Current Flow
- Backend to memory_manager flow
- memory_manager to memory backend
- memory backend to Firebase

### Phase 4: Identify Missing Connections
- Extract intent generation flow
- Agent execution and learning
- Tool selection and feedback

## Tests to Run
1. `test_memory_manager_flow.py` - Trace save_if_important calls
2. `test_agent_learning_persistence.py` - Verify goal/reflection saving
3. `test_tool_feedback_persistence.py` - Verify tool learning saved
4. `test_knowledge_persistence.py` - Verify knowledge graph saved
5. `test_extract_intent_flow.py` - Debug extract intent error
