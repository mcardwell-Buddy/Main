"""Test deep learning with store_knowledge"""
import sys
sys.path.insert(0, 'C:\\Users\\micha\\Buddy')

from Back_End.learning_tools import store_knowledge

print("="*70)
print("TESTING DEEP LEARNING: store_knowledge()")
print("="*70)

topic = "Python decorators"
print(f"\nLearning about: {topic}")
print("-"*70)

result = store_knowledge(topic)

print(f"\nStatus: {result['status']}")
print(f"Confidence: {result.get('confidence', 0):.2f}")
print(f"Searches Performed: {result.get('searches_performed', 0)}")
print(f"Results Analyzed: {result.get('results_analyzed', 0)}")
print(f"Facts Learned: {result.get('facts_learned', 0)}")
print(f"Stored in Memory: {result.get('stored', False)}")

if 'key_concepts' in result:
    print(f"\nKey Concepts ({len(result['key_concepts'])}):")
    for idx, concept in enumerate(result['key_concepts'][:5], 1):
        print(f"  {idx}. {concept}")

if 'summary' in result:
    print(f"\nSummary:")
    print(f"  {result['summary'][:300]}...")

print("\n" + "="*70)
print(f"Message: {result.get('message', 'N/A')}")
print("="*70)

