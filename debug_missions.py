import json
with open('outputs/phase25/missions.jsonl') as f:
    lines = f.readlines()
    for line in lines[-6:]:
        record = json.loads(line)
        print(f"mission: {record.get('mission_id')}, event: {record.get('event_type')}, objective: {bool(record.get('objective'))}, status: {record.get('status')}")

