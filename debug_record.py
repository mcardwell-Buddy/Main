import json
with open('outputs/phase25/missions.jsonl') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        record = json.loads(line)
        if 'mission_direct_1770559076786' in record.get('mission_id', ''):
            print(f"Event: {record.get('event_type')}")
            print(json.dumps(record, indent=2))
            print()
