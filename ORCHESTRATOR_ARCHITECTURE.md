"""
INTERACTION ORCHESTRATOR - ARCHITECTURE & FLOW

═══════════════════════════════════════════════════════════════════════════════
SYSTEM FLOW
═══════════════════════════════════════════════════════════════════════════════

                            User Chat Message
                                   ↓
                    ┌──────────────────────────────┐
                    │   Interaction Orchestrator   │
                    └──────────────────────────────┘
                                   ↓
                    ┌──────────────────────────────┐
                    │  DeterministicIntentClassifier
                    │                              │
                    │  Analyze:                    │
                    │  • Keyword matching          │
                    │  • Message structure         │
                    │  • Question indicators       │
                    │  • (NO LLM calls)            │
                    └──────────────────────────────┘
                                   ↓
                    ┌──────────────────────────────┐
                    │    IntentClassification      │
                    │                              │
                    │  • intent_type               │
                    │  • confidence (0.0-1.0)      │
                    │  • keywords                  │
                    │  • actionable                │
                    │  • reasoning                 │
                    └──────────────────────────────┘
                                   ↓
                    ┌──────────────────────────────┐
                    │      RoutingDecision         │
                    │                              │
                    │  Deterministic mapping:      │
                    │  intent_type → handler       │
                    │  (ONE decision per message)  │
                    └──────────────────────────────┘
                                   ↓
        ┌───────────────────────────┼───────────────────────────┐
        ↓                           ↓                           ↓
  [execute]                  [respond]                  [other handlers...]
        │                           │                           │
        ↓                           ↓                           ↓
  Create Mission          Return Text Response        Return Specialized
  status='proposed'       (NO side effects)           Response Type

        │                           │                           │
        └───────────────────────────┴───────────────────────────┘
                                   ↓
                    ┌──────────────────────────────┐
                    │      ResponseEnvelope        │
                    │                              │
                    │  • response_type             │
                    │  • summary                   │
                    │  • artifacts[]               │
                    │  • missions_spawned[]        │
                    │  • signals_emitted[]         │
                    │  • ui_hints                  │
                    │  • timestamp                 │
                    │  • metadata                  │
                    └──────────────────────────────┘
                                   ↓
                            JSON Response
                                   ↓
                         Return to Chat UI

═══════════════════════════════════════════════════════════════════════════════
INTENT CLASSIFICATION TREE (Deterministic)
═══════════════════════════════════════════════════════════════════════════════

                          Parse Message
                                 │
                    ┌────────────┴────────────┐
                    ↓                         ↓
            Check Acknowledgments?      Check if Question?
            (exact match patterns)      (starts with who/what/how
                    │                    or ends with ?)
                 [YES]                           │
                    ↓                    ┌──────┴──────┐
            ACKNOWLEDGMENT              [YES]        [NO]
            (confidence: 0.95)           │             │
            (actionable: NO)        QUESTION      Continue...
                                  (confidence: 0.80)
                                  (actionable: NO)
                                        │
                                        └─→ Count execution keywords
                                            │
                                    ┌───────┴────────┐
                                   [HIGH]          [LOW]
                                    │               │
                              REQUEST_EXECUTION    │
                              (confidence: 0.6-0.9)│
                              (actionable: YES)    │
                                                   ↓
                                    Count forecast keywords
                                            │
                                    ┌───────┴────────┐
                                   [YES]           [NO]
                                    │               │
                              FORECAST_REQUEST    │
                              (actionable: YES)  │
                                                 ↓
                                  Count status keywords
                                          │
                                  ┌───────┴────────┐
                                 [YES]           [NO]
                                  │               │
                              STATUS_CHECK      │
                              (actionable: NO) │
                                               ↓
                                    Check ambiguity
                                    (keyword density < 30%
                                     or message length < 3)
                                          │
                                  ┌───────┴────────┐
                                 [YES]           [NO]
                                  │               │
                         CLARIFICATION_      QUESTION
                         NEEDED              (default)
                         (actionable: NO)    (actionable: NO)

═══════════════════════════════════════════════════════════════════════════════
HANDLER DISPATCH TABLE (Routing)
═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────┬──────────────────┬──────────────────────────┐
│ Intent Type         │ Handler          │ Response Type            │
├─────────────────────┼──────────────────┼──────────────────────────┤
│ REQUEST_EXECUTION   │ _handle_execute  │ TEXT (with mission_id)   │
├─────────────────────┼──────────────────┼──────────────────────────┤
│ QUESTION            │ _handle_respond  │ TEXT (informational)     │
├─────────────────────┼──────────────────┼──────────────────────────┤
│ FORECAST_REQUEST    │ _handle_forecast │ FORECAST or TEXT         │
├─────────────────────┼──────────────────┼──────────────────────────┤
│ STATUS_CHECK        │ _handle_status   │ TEXT (status info)       │
├─────────────────────┼──────────────────┼──────────────────────────┤
│ CLARIFICATION_NEEDED│ _handle_clarify  │ CLARIFICATION_REQUEST    │
├─────────────────────┼──────────────────┼──────────────────────────┤
│ ACKNOWLEDGMENT      │ _handle_acknowledge│ TEXT (friendly)         │
└─────────────────────┴──────────────────┴──────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
HARD CONSTRAINTS VALIDATION
═══════════════════════════════════════════════════════════════════════════════

CONSTRAINT 1: NO AUTONOMY
────────────────────────────────────────────────────────────────────────────────
  Pattern: All missions created with status='proposed'
  Validation:
    [execute handler]
         ↓
    Create mission via ChatIntakeCoordinator
         ↓
    Verify: mission.status == 'proposed' ✓
    Verify: mission.awaiting_approval == True ✓
    Verify: mission NOT in active/executing state ✓
         ↓
    Return ResponseEnvelope with missions_spawned
  Result: User MUST approve before execution

CONSTRAINT 2: NO LOOPS
────────────────────────────────────────────────────────────────────────────────
  Pattern: ONE message → ONE response (deterministic)
  Validation:
    Message A → Classify → Route → Handle → Response X
    Message A → Classify → Route → Handle → Response X  ✓ (identical)
    Message B → Different intent → Different handler → Response Y
  Result: No iterative refinement, no feedback loops

CONSTRAINT 3: ONE DECISION PER MESSAGE
────────────────────────────────────────────────────────────────────────────────
  Pattern: Single classification → single route → single handler
  Validation:
    [input message]
         ↓
    [classify] → ONE IntentClassification
         ↓
    [route] → ONE handler selected
         ↓
    [execute handler] → ONE response
  Result: Exactly one decision path per message

CONSTRAINT 4: NO EXECUTION WITHOUT EXPLICIT INTENT
────────────────────────────────────────────────────────────────────────────────
  Pattern: Only REQUEST_EXECUTION intent triggers mission creation
  Validation:
    QUESTION → _handle_respond → NO missions_spawned ✓
    AMBIGUOUS → _handle_clarify → NO missions_spawned ✓
    ACKNOWLEDGMENT → _handle_acknowledge → NO missions_spawned ✓
    FORECAST_REQUEST → _handle_forecast → NO mission (queued) ✓
    REQUEST_EXECUTION → _handle_execute → missions_spawned ✓
  Result: Missions ONLY from explicit execution requests

CONSTRAINT 5: NO LLM CALLS
────────────────────────────────────────────────────────────────────────────────
  Pattern: Pure heuristics + keyword matching
  Validation:
    [DeterministicIntentClassifier]
         ↓
    NO external API calls ✓
    NO language models ✓
    NO neural networks ✓
    ONLY:
      • String manipulation
      • Regex pattern matching
      • Keyword counting
      • Simple math (confidence calculation)
  Result: Fully deterministic, reproducible, observable

CONSTRAINT 6: NO UI CODE
────────────────────────────────────────────────────────────────────────────────
  Pattern: Pure data schemas, no rendering
  Validation:
    ResponseEnvelope
         ↓
    [contains]
      • Data fields (strings, enums, lists)
      • Dataclass instances
      • JSON-serializable objects
    [does NOT contain]
      • render() methods ✓
      • display() methods ✓
      • to_html() methods ✓
      • CSS/styling code ✓
      • UI framework calls ✓
    [UIHints]
      • Suggestions only (non-binding)
      • Layout preferences
      • Color recommendations
      • NOT rendering instructions
  Result: Pure schema, UI is user's responsibility

═══════════════════════════════════════════════════════════════════════════════
RESPONSE ENVELOPE STRUCTURE
═══════════════════════════════════════════════════════════════════════════════

ResponseEnvelope {
  response_type: ResponseType (enum)
    ├── TEXT
    ├── TABLE
    ├── REPORT
    ├── FORECAST
    ├── LIVE_EXECUTION
    ├── ARTIFACT_BUNDLE
    └── CLARIFICATION_REQUEST
  
  summary: str (human-readable summary)
  
  artifacts: List[Artifact]
    ├── Artifact (base)
    ├── TableArtifact
    ├── ChartArtifact
    ├── DocumentArtifact
    ├── CodeBlockArtifact
    ├── TimelineArtifact
    ├── FileReferenceArtifact
    └── ...
  
  missions_spawned: List[MissionReference]
    └── MissionReference {
        mission_id: str
        status: 'proposed'
        objective_type: str
        objective_description: str
      }
  
  signals_emitted: List[SignalReference]
    └── SignalReference {
        signal_type: str
        signal_layer: str
        signal_source: str
        timestamp: ISO datetime
        summary: str
      }
  
  ui_hints: UIHints (non-binding suggestions)
    ├── layout: 'compact' | 'expanded' | 'side_by_side'
    ├── priority: 'normal' | 'urgent' | 'background'
    ├── color_scheme: 'info' | 'warning' | 'error' | 'success'
    ├── icon: str (icon name)
    ├── suggested_actions: List[str]
    └── expandable: bool
  
  timestamp: ISO datetime (creation timestamp)
  
  metadata: dict (optional key-value pairs)
}

═══════════════════════════════════════════════════════════════════════════════
TEST COVERAGE MAP
═══════════════════════════════════════════════════════════════════════════════

DeterministicIntentClassifier
  ├─ test_execution_request_classification ✓
  ├─ test_question_classification ✓
  ├─ test_forecast_request_classification ✓
  ├─ test_status_check_classification ✓
  ├─ test_acknowledgment_classification ✓
  ├─ test_clarification_needed_classification ✓
  └─ test_very_short_message_is_ambiguous ✓

RoutingDecision
  ├─ test_route_execution_request ✓
  ├─ test_route_question_non_actionable ✓
  ├─ test_route_clarification_needed ✓
  ├─ test_route_acknowledgment ✓
  ├─ test_route_forecast_request ✓
  └─ test_route_status_check ✓

InteractionOrchestrator (5 real-world scenarios)
  ├─ test_scenario_1_execution_request ✓
  ├─ test_scenario_2_informational_question ✓
  ├─ test_scenario_3_ambiguous_request ✓
  ├─ test_scenario_4_acknowledgment ✓
  └─ test_scenario_5_forecast_request ✓

HardConstraints
  ├─ test_no_autonomy_single_message_always_proposed ✓
  ├─ test_no_loops_one_message_one_response ✓
  ├─ test_one_decision_per_message ✓
  ├─ test_no_execution_without_explicit_intent ✓
  ├─ test_no_ui_code_only_schemas ✓
  └─ test_deterministic_no_llm_calls ✓

ConvenienceFunction
  └─ test_orchestrate_message_function ✓

Total: 40+ assertions, all passing

═══════════════════════════════════════════════════════════════════════════════
INTEGRATION DIAGRAM
═══════════════════════════════════════════════════════════════════════════════

    Frontend (React)
           ↓
    UnifiedChat.js
           ↓
    fetch("/orchestrate", {message, session_id})
           ↓
    backend/main.py
           ↓
    @app.post("/orchestrate")
           ↓
    orchestrate_message()
           ↓
    InteractionOrchestrator.process_message()
           ↓
    DeterministicIntentClassifier.classify()
           ↓
    RoutingDecision.route()
           ↓
    [handler] → ResponseEnvelope
           ↓
    response.to_dict()
           ↓
    return to frontend
           ↓
    Display response + handle missions

═══════════════════════════════════════════════════════════════════════════════
KEYWORD REFERENCE
═══════════════════════════════════════════════════════════════════════════════

EXECUTION_KEYWORDS = {
  'get', 'fetch', 'scrape', 'extract', 'collect', 'gather',
  'search', 'find', 'retrieve', 'pull', 'download',
  'run', 'execute', 'do', 'perform', 'start', 'begin',
  'build', 'create', 'make', 'generate'
}

QUESTION_KEYWORDS = {
  'what', 'why', 'how', 'when', 'where', 'who',
  'can', 'could', 'should', 'would', 'is', 'are',
  'does', 'do', 'did', 'will', 'should'
}

FORECAST_KEYWORDS = {
  'predict', 'forecast', 'estimate', 'project', 'anticipate',
  'expect', 'trend', 'analyze', 'pattern'
}

STATUS_KEYWORDS = {
  'status', 'progress', 'update', 'state', 'check',
  'monitor', 'watch', 'track', 'how is', "what's",
  'current', 'latest'
}

ACKNOWLEDGMENT_PATTERNS = [
  'hi', 'hello', 'hey', 'thanks', 'thank you',
  'ok', 'okay', 'yes', 'no', 'sure', 'fine', 'good',
  'got it', 'understood', 'copy that', 'roger', 'ack'
]

═══════════════════════════════════════════════════════════════════════════════
"""
