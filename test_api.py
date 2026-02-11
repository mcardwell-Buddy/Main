import requests

base_url = "http://localhost:8000"

print("Testing root endpoint...")
r = requests.get(f"{base_url}/")
print(r.json())
print()

print("Testing /tools endpoint...")
r = requests.get(f"{base_url}/tools")
data = r.json()
print(f"Found {data['count']} tools:")
for tool in data['tools']:
    print(f"  - {tool['name']}: {tool['description']}")
    print(f"    Performance: {tool['performance']}")
print()

print("Testing /chat endpoint with a simple goal...")
r = requests.post(f"{base_url}/chat", params={"goal": "calculate 15 + 27"})
result = r.json()
print(f"Agent took {len(result['steps'])} steps")
print(f"Final state: {result['final']}")

