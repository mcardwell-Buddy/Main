import json
with open('outputs/phase25/missions.jsonl') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        record = json.loads(line)
        # Find a proposed mission record (event_type is None)
        if record.get('event_type') is None and 'mission_chat' in record.get('mission_id', ''):
            print("Real mission record structure:")
            print(json.dumps(record, indent=2)[:500])
            print("\n\n")
            break

# Also show test mission
with open('outputs/phase25/missions.jsonl') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        record = json.loads(line)
        if record.get('mission_id') == 'mission_direct_1770559016348':
            print("Test mission record structure:")
            print(json.dumps(record, indent=2))
            break

