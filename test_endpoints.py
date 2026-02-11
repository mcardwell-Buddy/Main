"""Quick test of self-improvement endpoints"""
import requests
import json

BASE_URL = "http://localhost:8000"

print("="*60)
print("TESTING SELF-IMPROVEMENT ENDPOINTS")
print("="*60)

# Test 1: Scan
print("\n1. Testing /self-improve/scan...")
try:
    response = requests.post(f"{BASE_URL}/self-improve/scan")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Success! Found {data.get('count', 0)} opportunities")
        if data.get('opportunities'):
            print("\nTop 3 opportunities:")
            for i, opp in enumerate(data['opportunities'][:3], 1):
                print(f"\n{i}. {opp['file']}")
                print(f"   Priority: {opp['priority']}")
                print(f"   Suggestions: {', '.join(opp['suggestions'][:2])}")
    else:
        print(f"✗ Failed with status {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"✗ Error: {e}")

# Test 2: Check if backend can handle self-improvement execution
print("\n\n2. Testing backend /reasoning/execute with self-improvement...")
try:
    response = requests.post(
        f"{BASE_URL}/reasoning/execute",
        json={
            "goal": "improve yourself",
            "context": {}
        }
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Success! Reasoning result:")
        result = data.get('result', {})
        print(f"   Message: {result.get('message', '')[:200]}...")
    else:
        print(f"✗ Failed with status {response.status_code}")
        print(response.text[:500])
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "="*60)
print("✓ ENDPOINT TESTS COMPLETE")
print("="*60)

