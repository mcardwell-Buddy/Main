#!/usr/bin/env python
"""
Test the complete memory_manager -> memory -> Firebase flow.
"""
import sys
import os
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

from Back_End.memory_manager import memory_manager
from Back_End.memory import memory
from Back_End.config import Config

print("=" * 80)
print("MEMORY MANAGER → FIREBASE FLOW TEST")
print("=" * 80)

# 1. Check configuration
print(f"\n1. CONFIGURATION:")
print(f"   Firebase enabled: {Config.FIREBASE_ENABLED}")
print(f"   Memory backend: {memory.__class__.__name__}")
print(f"   Memory manager available: {memory_manager is not None}")

# 2. Check if memory is Firebase or Mock
print(f"\n2. MEMORY BACKEND TYPE:")
if memory.__class__.__name__ == "FirebaseMemory":
    print(f"   ✓ Using FirebaseMemory (correct)")
elif memory.__class__.__name__ == "MockMemory":
    print(f"   ✗ Using MockMemory (incorrect - should be FirebaseMemory)")
    print(f"   This means agent learning will NOT persist!")
else:
    print(f"   ? Using unknown memory: {memory.__class__.__name__}")

# 3. Test save_if_important flow
print(f"\n3. TESTING save_if_important() FLOW:")

# Test reflection save
test_key = "test_reflection:goal_123"
test_data = {
    'effectiveness_score': 0.8,
    'confidence_adjustment': 0.15,
    'strategy_adjustment': 'Use web search for company info extraction',
    'tool_feedback': {
        'web_search': {'usefulness': 0.9},
        'web_extract': {'usefulness': 0.7}
    }
}

try:
    # Calculate importance
    importance = memory_manager.calculate_importance('reflection', test_data)
    print(f"   Calculated importance for reflection: {importance:.2f}")
    
    # Should save?
    should_save = memory_manager.should_save('reflection', test_data)
    print(f"   Should save: {should_save}")
    
    # Actually save
    result = memory_manager.save_if_important(test_key, 'reflection', test_data)
    print(f"   Save result: {result}")
    
    if result:
        print(f"   ✓ Reflection saved via memory_manager")
    else:
        print(f"   ✗ Reflection NOT saved (failed at memory level)")
        
except Exception as e:
    print(f"   ✗ Error during save_if_important: {e}")
    import traceback
    traceback.print_exc()

# 4. Test observation save
print(f"\n4. TESTING OBSERVATION SAVE:")
test_obs_key = "observation:goal_456:step_1"
test_obs_data = {
    'goal': 'Extract company info',
    'step': 1,
    'action': 'web_search',
    'results': ['result1', 'result2', 'result3'],
    'execution_time_ms': 234
}

try:
    importance = memory_manager.calculate_importance('observation', test_obs_data)
    print(f"   Calculated importance for observation: {importance:.2f}")
    
    result = memory_manager.save_if_important(test_obs_key, 'observation', test_obs_data)
    print(f"   Save result: {result}")
    
    if result:
        print(f"   ✓ Observation saved")
    else:
        print(f"   ✗ Observation NOT saved")
        
except Exception as e:
    print(f"   ✗ Error: {e}")

# 5. Test learning save
print(f"\n5. TESTING LEARNING SAVE:")
test_learning_key = "learning:company_extraction"
test_learning_data = {
    'topic': 'company_extraction',
    'learnings': [
        'Web search works best for company info',
        'Multiple sources improve accuracy',
        'LinkedIn and company websites are authoritative'
    ],
    'confidence': 0.92,
    'sources': 3,
    'synthesis_method': 'multi_search'
}

try:
    importance = memory_manager.calculate_importance('learning', test_learning_data, context={'searches': 3})
    print(f"   Calculated importance for learning: {importance:.2f}")
    
    result = memory_manager.save_if_important(test_learning_key, 'learning', test_learning_data, context={'searches': 3})
    print(f"   Save result: {result}")
    
    if result:
        print(f"   ✓ Learning saved")
    else:
        print(f"   ✗ Learning NOT saved")
        
except Exception as e:
    print(f"   ✗ Error: {e}")

# 6. Verify data in Firebase
print(f"\n6. VERIFYING DATA IN FIREBASE:")
if hasattr(memory, '_db') and memory._db:
    try:
        from Back_End.conversation.session_store import get_conversation_store
        store = get_conversation_store()
        
        # Try to access the agent_memory collection
        collection_name = Config.FIREBASE_COLLECTION or 'agent_memory'
        collection = memory._db.collection(collection_name)
        
        docs = collection.stream()
        count = 0
        keys_found = []
        
        for doc in docs:
            count += 1
            keys_found.append(doc.id)
        
        print(f"   Total documents in '{collection_name}': {count}")
        
        if count > 0:
            print(f"   Documents found:")
            for key in keys_found[:10]:  # Show first 10
                print(f"     - {key}")
            if len(keys_found) > 10:
                print(f"     ... and {len(keys_found) - 10} more")
        else:
            print(f"   ⚠ WARNING: No documents found in Firebase collection!")
            print(f"   This means memory_manager save calls are not persisting to Firebase")
            
    except Exception as e:
        print(f"   ✗ Failed to query Firebase: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"   ✗ Firebase database not initialized in memory object")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)

