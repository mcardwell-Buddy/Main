# Execution Stream Observability (Read-Only)

## Purpose
Provide a read-only, append-only execution stream so the UI can observe mission execution step-by-step without any control or intervention.

## Hard Constraints (Enforced)
- **READ-ONLY**
- **NO execution control**
- **NO retries**
- **NO pausing**
- **NO autonomy**

## Schema
Events are JSONL-compatible and emitted during mission execution. Each line is a single `ExecutionStreamEvent`:

- `timestamp` (ISO 8601)
- `mission_id`
- `event_type` (`navigation`, `extraction`, `signal`, `status`)
- `payload` (typed, minimal)

See [backend/execution_stream_events.py](backend/execution_stream_events.py) for the canonical schema and helpers.

## Append-Only Emission
Events are written via [backend/execution_stream_emitter.py](backend/execution_stream_emitter.py) using append-only JSONL.

- Default output directory: `outputs/execution_streams/`
- One file per `live_stream_id`

## Response Envelope Integration
`ResponseEnvelope` now optionally includes `live_stream_id`. The UI can use this to locate the correct stream and observe progress.

Reference: [backend/response_envelope.py](backend/response_envelope.py)

## How the UI Can Subscribe (Read-Only)
The UI should subscribe through a **read-only** server endpoint that tails the JSONL stream. Recommended patterns:

1. **Server-Sent Events (SSE):**
   - Server reads new lines from the JSONL stream.
   - Each new line is streamed to the UI as an event.

2. **WebSocket (read-only channel):**
   - Server tails the JSONL file and pushes new lines.
   - UI only receives events, no control messages.

3. **Polling (fallback):**
   - UI requests new events since a timestamp/offset.
   - Server returns only appended lines.

## Operational Notes
- Streams are append-only and immutable.
- The UI must not send commands or control signals.
- This design does not modify mission execution behavior.

## Example Event (Shape)

- `event_type`: `navigation`
- `payload` (minimal): `{ "url": "https://example.com", "action": "click", "detail": "next page" }`

All other event types use similarly minimal, typed payloads defined in the schema module.
