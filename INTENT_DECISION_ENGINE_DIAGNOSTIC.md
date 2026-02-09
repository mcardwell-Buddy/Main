# INTENT & ACTION DECISION ENGINE - DIAGNOSTIC REPORT

**Date:** February 8, 2026  
**System:** Buddy Intent Detection & Action Routing Layer  
**Status:** Analysis Only (No Implementation)  
**Scope:** How Buddy decides what user is asking for and routes to actions

---

## 1. CURRENT SYSTEM BEHAVIOR (FACTUAL)

### 1.1 Message Flow Architecture

When a user sends a chat message, Buddy processes it through this deterministic pipeline:

```
User Message
    ↓
[STEP 0: Approval Bridge Check]
    ↓
[STEP 1: Intent Classification]
    → DeterministicIntentClassifier.classify()
    ↓
[STEP 2: Routing Decision]
    → RoutingDecision.route()
    ↓
[STEP 3: Handler Execution]
    → _handle_execute()
    → _handle_respond()
    → _handle_clarify()
    → _handle_acknowledge()
    → _handle_forecast()
    → _handle_status()
    → _handle_informational()
    ↓
ResponseEnvelope (to user)
```

**Location:** `backend/interaction_orchestrator.py`

---

### 1.2 Intent Classification (Step 1)

**Class:** `DeterministicIntentClassifier` (lines 64-350)

**How It Works (Deterministic Keyword Matching):**

1. **Keyword Set Definitions** (lines 73-127):
   - `EXECUTION_KEYWORDS`: get, fetch, scrape, extract, browse, navigate, visit, calculate, etc.
   - `QUESTION_KEYWORDS`: what, why, how, when, can, could, etc.
   - `FORECAST_KEYWORDS`: predict, forecast, estimate, trend
   - `STATUS_KEYWORDS`: status, progress, update, check, monitor
   - `INFORMATIONAL_KEYWORDS`: list, explain, describe, tell, show
   - `ACKNOWLEDGMENT_PATTERNS`: hi, hello, thanks, ok, understood

2. **Classification Logic** (lines 140-240):
   ```python
   def classify(self, message: str) -> IntentClassification:
       # Step A: Check acknowledgments first (regex patterns)
       if message matches ACKNOWLEDGMENT_PATTERN:
           return IntentType.ACKNOWLEDGMENT
       
       # Step B: Check if is question (? or starts with question word)
       if message.rstrip().endswith('?') or starts with ['how', 'what', ...]:
           return IntentType.QUESTION (non-actionable by default)
       
       # Step C: Count keyword matches across intent types
       execution_matches = count keywords from EXECUTION_KEYWORDS
       forecast_matches = count keywords from FORECAST_KEYWORDS
       status_matches = count keywords from STATUS_KEYWORDS
       informational_matches = count keywords from INFORMATIONAL_KEYWORDS
       
       # Step D: Determine primary intent by highest keyword count
       best_intent = max(execution_matches, forecast_matches, status_matches)
       
       # Step E: Decide actionable (True only for EXECUTION or FORECAST)
       actionable = (best_intent in [REQUEST_EXECUTION, FORECAST_REQUEST])
       
       # Step F: Return classification
       return IntentClassification(
           intent_type=best_intent,
           confidence=0.5 + (best_score / max(10, word_count)),
           keywords=matched_keywords,
           actionable=actionable,
           reasoning="..."
       )
   ```

3. **Intent Types Returned:**
   - `ACKNOWLEDGMENT` → Non-actionable (greeting)
   - `QUESTION` → Non-actionable (informational)
   - `INFORMATIONAL` → Non-actionable (requests for info only)
   - `CLARIFICATION_NEEDED` → Non-actionable (ambiguous)
   - `REQUEST_EXECUTION` → **Actionable** (propose mission)
   - `FORECAST_REQUEST` → **Actionable** (propose forecast)
   - `STATUS_CHECK` → Non-actionable (status info only)

**Key Property:** Intent classification is **deterministic and keyword-driven**. The same message always produces the same classification.

---

### 1.3 Routing Decision (Step 2)

**Class:** `RoutingDecision` (lines 353-399)

**How It Works:**

```python
@staticmethod
def route(intent, message, context) -> (handler_name, handler_kwargs):
    
    if intent.intent_type == ACKNOWLEDGMENT:
        return ("acknowledge", {message})
    
    if intent.intent_type == CLARIFICATION_NEEDED:
        return ("clarify", {message, context})
    
    if intent.intent_type == INFORMATIONAL:
        return ("informational", {message, context})
    
    if intent.intent_type == QUESTION:
        if intent.actionable:
            return ("execute", {message, context})
        else:
            return ("respond", {message, context})
    
    if intent.intent_type == REQUEST_EXECUTION:
        return ("execute", {message, context})
    
    if intent.intent_type == FORECAST_REQUEST:
        return ("forecast", {message, context})
    
    if intent.intent_type == STATUS_CHECK:
        return ("status", {message, context})
    
    # Default
    return ("respond", {message, context})
```

**Decision Invariant:** Exactly ONE handler per message, determined by `intent.intent_type` alone.

---

### 1.4 Handler Execution (Step 3)

Seven possible handlers:

#### A. `_handle_execute()` (lines 783-820)
- **Triggered by:** REQUEST_EXECUTION or actionable QUESTION
- **Does:**
  1. Calls `ChatIntakeCoordinator.process_chat_message()` (mission_control/chat_intake_coordinator.py)
  2. ChatIntakeCoordinator routes to intent router (chat_intent_router.py)
  3. If actionable, builds MissionDraft via MissionDraftBuilder
  4. Emits mission proposal via MissionProposalEmitter
  5. Returns mission_proposal_response()
- **Result:** Mission created in `outputs/phase25/missions.jsonl` with status="proposed"

#### B. `_handle_respond()` (lines 835-920)
- **Triggered by:** Non-actionable QUESTION, INFORMATIONAL
- **Does:**
  1. Checks for artifact follow-up patterns
  2. If matches "what did you find", "where did you go", "why did you navigate":
     - Retrieves latest artifact from `get_latest_artifact()`
     - Returns artifact data as text response
  3. If "how do i scrape" or "what can you" or "how do i":
     - Returns hardcoded capability help text
  4. Else: Returns generic capability help
- **Result:** Text response (no mission created)

#### C. `_handle_clarify()` (lines 922-942)
- **Triggered by:** CLARIFICATION_NEEDED
- **Does:**
  1. Generates clarifying question ("Can you provide more details?")
  2. Offers 4 options
  3. Returns clarification_response() with UI hints for buttons
- **Result:** Interactive UI with clarification options

#### D. `_handle_acknowledge()` (lines 745-771)
- **Triggered by:** ACKNOWLEDGMENT
- **Does:**
  1. Map message to response (hi → "Hey!", thanks → "You're welcome!")
  2. Return text_response(response_text)
- **Result:** Text greeting

#### E. `_handle_forecast()` (lines 974-1000)
- **Triggered by:** FORECAST_REQUEST
- **Does:**
  1. Builds forecast mission via ChatIntakeCoordinator
  2. Returns mission_proposal_response()
- **Result:** Forecast mission created

#### F. `_handle_status()` (lines 1002-1030)
- **Triggered by:** STATUS_CHECK
- **Does:**
  1. Queries missions.jsonl for status of recent missions
  2. Returns text response with status summary
- **Result:** Text response with mission statuses

#### G. `_handle_informational()` (lines 944-972)
- **Triggered by:** INFORMATIONAL
- **Does:**
  1. Checks message patterns
  2. Returns hardcoded help text for specific patterns
  3. Fallback generic response
- **Result:** Text response (capability help)

---

### 1.5 Mission Draft Creation (Within Execute Handler)

**File:** `backend/mission_control/mission_draft_builder.py`

When execute handler calls ChatIntakeCoordinator, this sequence occurs:

1. **Intent Router** (`chat_intent_router.py` lines 1-194):
   - Routes message to: `informational_question` | `exploratory_request` | `action_request` | `non_actionable`
   - Uses similar keyword matching to DeterministicIntentClassifier

2. **Draft Builder** (`mission_draft_builder.py` lines 44-244):
   ```python
   def build_draft(raw_message, intent_type, intent_keywords):
       mission_id = generate_unique_id()
       objective_type = determine_type(raw_message, keywords)  # search|extract|navigate
       objective_description = clean_objective(raw_message)    # Strips/normalizes message
       target_count = extract_target_count(raw_message)        # Heuristic for item count
       allowed_domains = extract_domains(raw_message)          # Regex: domain pattern
       max_pages = determine_max_pages(raw_message)            # Heuristic: 1-10
       max_duration = DEFAULT_MAX_DURATION                      # 5 minutes fixed
       
       return MissionDraft(
           mission_id, source='chat', status='proposed',
           objective_description,
           objective_type,
           target_count,
           allowed_domains, max_pages, max_duration,
           created_at, raw_chat_message, intent_keywords
       )
   ```

3. **Key Extraction Logic:**
   - **Domain extraction:** `DOMAIN_PATTERN = r'(?:from\s+)?(?:https?://)?(?:www\.)?([a-z0-9.-]+\.[a-z]{2,})(?:/\S*)?'`
     - Searches for domain in message
     - If not found, allowed_domains = []
   - **Objective description:** `raw_message` with basic punctuation cleanup
     - **⚠️ No explicit URL preservation**
     - **⚠️ No entity extraction beyond domain**

4. **Proposal Emission:**
   ```python
   emitter.emit_proposal(draft)
   # Writes to missions.jsonl with status="proposed"
   ```

---

### 1.6 Execution Service & Tool Selection

**File:** `backend/execution_service.py` (lines 1-795)

When user approves mission and execution begins:

1. **Intent Classification for Tool Selection** (lines 61-122):
   ```python
   def _classify_intent(objective):
       # Uses regex patterns to classify:
       objective_lower = objective.lower()
       
       if extract pattern "extract|pull|get|grab|fetch|scrape|retrieve" + "data|content|text|info":
           return 'extraction'
       elif calculation pattern found:
           return 'calculation'
       elif time pattern:
           return 'time'
       elif navigation pattern "navigate|go to|visit|browse|open" + "site|page|website|url":
           return 'navigation'
       elif file operations pattern:
           return 'file'
       ... etc
       else:
           return 'search'  # Safe default
   ```

2. **Tool Selection** (lines 413-475):
   ```python
   tool_name, tool_input, confidence = tool_selector.select_tool(objective_description)
   
   # tool_selector uses similar intent-based logic
   # Maps intent → allowed tools (INTENT_TOOL_RULES)
   ```

3. **Tool Input Normalization** (lines 426-451):
   ```python
   # For web_navigate: extracts valid URL before passing to tool
   if tool_name == 'web_navigate':
       if tool_input doesn't start with 'http':
           # Extract URL from objective_description or allowed_domains
           tool_input = resolved_url
   ```

4. **Execution & Artifact Creation** (lines 476-508):
   ```python
   result = tool_registry.call(tool_name, tool_input)
   
   # Build artifact based on tool type
   if tool_name == 'web_navigate':
       artifact = _build_web_navigation_artifact(...)
   elif tool_name == 'web_extract':
       artifact = _build_web_extraction_artifact(...)
   ...
   
   # Persist artifact (append-only JSONL)
   get_artifact_writer().write_artifact(artifact)
   ```

---

## 2. KNOWN FAILURE MODES (WITH EXAMPLES)

### FAILURE #1: Valid Execution Request Misclassified as Question

**Example:**
```
User: "Tell me about products on amazon.com"
Expected: REQUEST_EXECUTION (propose mission to extract data)
Actual: QUESTION (non-actionable response)
```

**Why It Happens:**

Line 168-170 in `interaction_orchestrator.py`:
```python
if is_question:
    return IntentClassification(
        intent_type=IntentType.QUESTION,
        confidence=...,
        actionable=False,  # ← Always False for questions
        reasoning="Question detected (question word or ? punctuation)"
    )
```

**Root Cause:** Classification checks for question structure (starts with "what", "how", ends with "?") **BEFORE** checking execution keywords. A message starting with "Tell me" matches question pattern even though it contains execution keyword "products" and domain "amazon.com".

**Deterministic?** YES — Same message always misclassified the same way.

**Impact:** User cannot execute data collection missions using question phrasing like "Find X on Y" or "Show me data from Z". Requires specific imperative phrasing only.

---

### FAILURE #2: URLs & Critical Context Stripped from Mission

**Example:**
```
User: "Extract title and price from https://shop.example.com/products"
Classified: REQUEST_EXECUTION ✓ (correct)
Mission created:
  {
    mission_id: "mission_chat_abc123",
    objective_description: "Extract title and price from https://shop.example.com/products",
    allowed_domains: ["shop.example.com"],
    ...
  }
```

User later says "navigate there and get the homepage title"

Next mission created:
```
  {
    mission_id: "mission_chat_def456",
    objective_description: "navigate there and get the homepage title",
    allowed_domains: [],  # ← Empty! "there" is not a domain
    raw_chat_message: "navigate there and get the homepage title"
  }
```

Execution fails: No URL provided to web_navigate tool.

**Why It Happens:**

Line 133-137 in `mission_draft_builder.py`:
```python
DOMAIN_PATTERN = r'(?:from\s+)?(?:https?://)?(?:www\.)?([a-z0-9.-]+\.[a-z]{2,})(?:/\S*)?'

def _extract_domains(raw_message):
    # Searches for explicit domain/URL in message
    # If not found explicitly, returns []
```

**Root Cause:** 
1. Domain extraction is **explicit keyword-based** (looks for "from DOMAIN" or "http://")
2. No conversational context tracking across messages (no session-level URL memory)
3. No entity linking ("there" → previous URL not resolved)
4. Pronouns (there, it, that) treated as unknown text, not references

**Deterministic?** YES — Pronoun resolution always fails.

**Impact:** Multi-turn conversations lose context. User must repeat URLs explicitly each time. System cannot handle "navigate there", "extract it", "get more details" style navigation.

---

### FAILURE #3: Empty Missions Created, Tool Selection Fails at Execution

**Example:**
```
User: "get stuff"
Classified: REQUEST_EXECUTION (keyword "get" detected) ✓
Mission created:
  {
    objective_description: "get stuff",
    allowed_domains: [],
    ...
  }
```

User approves: "yes"

Execution attempts:
```
tool_selector.select_tool("get stuff") 
→ confidence = 0.15 (too low)
→ Tool selection fails
→ Mission fails with "Tool selection failed (confidence: 0.15)"
```

**Why It Happens:**

Line 63-75 in `mission_draft_builder.py`:
```python
def _clean_objective_description(raw_message):
    # Removes punctuation, normalizes
    # Returns: "get stuff" (no domain, no target)
    # No validation that objective is complete
```

Line 413-421 in `execution_service.py`:
```python
tool_name, tool_input, confidence = tool_selector.select_tool(objective_description)
if confidence < 0.15:
    return {'success': False, 'error': 'Tool selection failed'}
```

**Root Cause:**
1. Mission draft builder accepts any execution keyword, even without target/domain
2. No validation that drafted mission has required context
3. Tool selector fails on insufficient information
4. Failure occurs at execution time (too late) instead of mission creation time

**Deterministic?** YES — Vague requests always fail.

**Impact:** Users get generic "Tool selection failed" instead of immediately being told "You need to specify what to get and from where".

---

### FAILURE #4: Tool Selection Overridden by Intent Classification Mismatch

**Example:**
```
User: "Navigate to https://example.com and extract titles"
Classified intent: navigation (keyword "navigate" + URL found)
Expected tool: web_navigate

Mission created:
  {
    objective_description: "Navigate to https://example.com and extract titles",
    objective_type: "navigate"
  }

Execution:
  intent_classified_for_tool = 'extraction'  # (because also has "extract")
  tool_selected = 'web_extract'
  
  # Tool Selection Invariant Check:
  INTENT_TOOL_RULES['extraction'] = ['web_extract', 'web_search']
  'web_extract' IS in allowed tools for 'extraction' ✓
  
  # Execution proceeds with web_extract
  # But mission said navigate first!
```

**Why It Happens:**

Line 60-122 in `execution_service.py`:
```python
def _classify_intent(objective):
    # Re-classifies objective at execution time
    # Uses different patterns than mission creation
    # Returns FIRST matching pattern
    
    if re.search(r'\b(extract|pull|get|grab|fetch|scrape)\b.*\b(data|content|text)\b', obj):
        return 'extraction'  # ← This matches first
    elif re.search(r'\b(navigate|go to|visit)\b', obj):
        return 'navigation'
```

Multi-step objectives ("navigate AND extract") get classified as single intent based on keyword order.

**Root Cause:**
1. Two separate intent classifiers exist: one in orchestrator, one in execution service
2. They use different keyword priority orders
3. Multi-intent objectives force choice of single tool
4. No concept of "sequence of actions" in mission structure

**Deterministic?** YES — Always chooses extraction over navigation due to regex pattern order.

**Impact:** Multi-step missions (navigate → extract → summarize) fail or execute incorrectly. System treats them as single-intent.

---

### FAILURE #5: "Help Text" Shown When Clarification Would Be Better

**Example:**
```
User: "data"
Classified: CLARIFICATION_NEEDED (1 word, unknown word)
Handler: _handle_clarify()

Response:
  "Can you provide more details? For example, what data do you want to collect and from where?"
  [Buttons: Execute a task | Get information | Check status | Something else]
```

**Problem:** User actually just wanted to know capabilities. But they sent 1-word message "data" which is ambiguous. System asks for clarification with execution-oriented buttons.

Next example:
```
User: "how to get titles from websites"
Classified: QUESTION (starts with "how", ends with ?)
Handler: _handle_respond()

Response:
  "I can help you answer that, but I'll need to collect data first. Try: 'Get [data] from [website]'"
  (hardcoded help text)
```

**Problem:** User is asking a procedural question ("how to"), not requesting data collection. But system shows help text suggesting format changes instead of answering the question.

**Why It Happens:**

Line 750-830 in `interaction_orchestrator.py`:
```python
def _handle_respond():
    if "how" in message_lower and "scrape" in message_lower:
        return hardcoded_help_about_scraping()
    elif "what can you" in message_lower:
        return hardcoded_capability_list()
    elif "how do i" in message_lower:
        return hardcoded_generic_help()
    else:
        return generic_fallback_help()  # ← Catches too much
```

Hardcoded pattern matching for help text is incomplete. Falls back to generic help for unmatched questions.

**Root Cause:**
1. System has predetermined help text for ~5 specific question patterns
2. Everything else gets generic fallback
3. No semantic understanding of question intent beyond pattern matching
4. No difference between "how do I?" (procedural) and "do I get?" (capability)

**Deterministic?** YES — Same questions always show same help text.

**Impact:** Users frustrated by irrelevant help suggestions. System cannot distinguish between procedural questions and capability questions.

---

## 3. MISSING ABSTRACTIONS & CONCEPTS

### Missing Concept #1: **Confidence Gradations**

**Current State:**
- Classification returns single `confidence: float` (0.0-1.0)
- Handlers treat all thresholds identically
- No distinction between "very confident" (0.95) and "weakly confident" (0.51)

**What's Missing:**
- Confidence tiers: CERTAIN | HIGH | MEDIUM | LOW | UNKNOWN
- Behavior should change based on tier:
  - CERTAIN (>0.85): Execute directly
  - HIGH (0.7-0.85): Execute with explicit confirmation
  - MEDIUM (0.5-0.7): Propose AND ask for clarification
  - LOW (0.2-0.5): Ask clarifying question first
  - UNKNOWN (<0.2): Request more details

**Impact:** All messages treated with same confidence, no adaptive routing.

---

### Missing Concept #2: **Intent Degree-of-Freedom (DoF)**

**Current State:**
- Intent is binary: either actionable or not
- No distinction between:
  - "definitely an action" (Get data from X)
  - "probably an action" (Find X on Y)
  - "could be action or info" (What about X)
  - "definitely not an action" (Hi there)

**What's Missing:**
- Confidence space separating intent types
- Probability distribution over possible intents
- Example: Message "Search Google for AI news"
  - 70% probability → REQUEST_EXECUTION (action)
  - 20% probability → QUESTION (procedural)
  - 10% probability → INFORMATIONAL (curiosity)

**Impact:** All-or-nothing routing. No graceful handling of ambiguity.

---

### Missing Concept #3: **Ask vs. Do**

**Current State:**
- All questions default to "respond with information"
- No distinction between:
  - "What are popular data science tools?" (ask for info)
  - "What data is on this page?" (do: navigate + extract + respond)
  - "Could you find me X?" (ask permission → do)
  - "Tell me about Y" (ambiguous ask or do)

**What's Missing:**
- Semantic classification: informational-ask | capability-ask | permission-ask | indirect-do
- Separate handler for "permission asks" that route to execution after confirmation
- Recognition that "Tell me about X from Y" is actually "Do: extract from Y, Then: respond with summary"

**Impact:** Valid "ask me to do something" requests treated as information requests.

---

### Missing Concept #4: **Multi-Step Intent**

**Current State:**
- Mission = single objective
- No concept of sequence
- Message "Navigate to site.com, extract all emails, group by domain" creates ONE mission
- At execution, first keyword wins (navigate OR extract, not both)

**What's Missing:**
- Intent decomposition: "navigate + extract + group" → sequence of 3 subtasks
- Dependency graph: extract depends on navigate
- Parallel vs. sequential logic
- Interleaved clarification ("Should I extract emails or just the page title?")

**Impact:** Complex requests fail or only partial execution.

---

### Missing Concept #5: **Context & Conversational Repair**

**Current State:**
- Each message classified independently
- No session-level context tracking
- No pronoun resolution ("it", "there", "that")
- No reference resolution ("the website" → which website?)
- No implicit continuation ("get the prices too" → prices from what?)

**What's Missing:**
- Session state with recent entities (URLs, domains, tables, etc.)
- Anaphora resolution: "Navigate there" → resolve "there" to most recent URL
- Implicit context application: "get more details" → add context from recent mission
- Conversational repair: "I meant X, not Y" → exception handling in decision logic

**Impact:** Multi-turn conversations lose critical context. Must repeat URLs, domains, targets on each turn.

---

### Missing Concept #6: **Need-for-Clarification Detection**

**Current State:**
- Fixed heuristic: messages <3 words are ambiguous
- No analysis of **semantic completeness**

**What's Missing:**
- Completeness checking:
  - "Get X from Y" has both object and source → complete
  - "Get X" has object but no source → incomplete
  - "Extract from Y" has source but no object → incomplete
  - "Go" has no object or source → incomplete
  
- Specificity checking:
  - "Get the 5 most popular products" is specific (clear target count)
  - "Get products" is vague (unclear target count)
  - "Get some data" is extremely vague (all unclear)
  
- Context sufficiency:
  - With prior URL in conversation, "Extract title" is complete
  - Without prior URL, "Extract title" is incomplete

**Impact:** Vague missions created that fail at execution time instead of immediately asking for details.

---

### Missing Concept #7: **Execution Confidence vs. Intent Confidence**

**Current State:**
- Tool selection returns confidence (0.0-1.0)
- Execution accepts if confidence >= 0.15
- No feedback to user about why tool was selected

**What's Missing:**
- Distinction between:
  - Intent confidence: "I think you want to do X" (0-1)
  - Tool confidence: "The best tool for X is Y" (0-1)
  - Execution confidence: "Tool Y will succeed" (0-1)
  
- Example: "Calculate the sum of 1, 2, 3"
  - Intent: 0.95 (clearly a calculation)
  - Tool: 0.95 (clearly calculate tool)
  - Execution: 0.85 (tool will parse and execute successfully)
  
- Example: "Extract emails from webpage"
  - Intent: 0.80 (probably data extraction)
  - Tool: 0.70 (web_extract is best guess)
  - Execution: 0.50 (might fail if page structure unexpected)

**Impact:** Low-confidence executions fail without user knowing why. No proactive warnings.

---

### Missing Concept #8: **Semantic Primacy vs. Keyword Primacy**

**Current State:**
- All decisions made via keyword matching
- Semantic meaning ignored if keywords don't match
- Example: "Get me some information" 
  - Has keyword "get" → classified as REQUEST_EXECUTION
  - But "information" is not actionable target
  - Should be QUESTION or INFORMATIONAL

**What's Missing:**
- Semantic categories:
  - Nouns: [action-capable, action-incapable]
    - Action-capable: "data", "emails", "prices", "titles"
    - Action-incapable: "information", "details", "explanation"
  - Verbs: [action-trigger, info-trigger]
    - Action-trigger: get, extract, fetch, retrieve
    - Info-trigger: explain, describe, tell, show (context-dependent)
  
- Multi-stage semantic analysis:
  - Stage 1: Keywords only → rough classification
  - Stage 2: Semantic types → refine classification
  - Stage 3: Pragmatics (user history, session) → final decision

**Impact:** Semantically vague requests misclassified. "Get information" creates failed missions.

---

## 4. ARCHITECTURAL ASSESSMENT

### 4.1 Classification Architecture

**Current:** Rule-Based (Deterministic Keyword Matching)

**Characteristics:**
- ✅ 100% deterministic (same input → same output)
- ✅ Fully auditable (can trace every classification decision)
- ✅ Fast (O(n) where n = keyword set size)
- ✅ No external dependencies (no API calls, no models)
- ❌ Brittle (easily broken by phrasing variations)
- ❌ No learning (same bugs forever unless manually fixed)
- ❌ No semantic understanding (pure surface-level pattern match)
- ❌ Keyword order dependency (first match wins)

**Is It Rule-Based?** YES. Exclusively keyword-driven with fixed priority order.

---

### 4.2 Decision Points & Rigidity Assessment

| Decision Point | Current Rigidity | Impact | Why Rigid |
|---|---|---|---|
| Question vs. Action | **Very Rigid** | Valid execution requests misclassified as questions | "Ends with ?" forces QUESTION, ignoring execution keywords |
| Clarification threshold | **Rigid** | Messages <3 words always ambiguous; messages >3 always treated as clear | Fixed word-count rule, no semantic completeness check |
| Help text routing | **Rigid** | ~5 hardcoded patterns; everything else gets generic help | Fixed if-elif chain with no fallback semantics |
| Domain extraction | **Very Rigid** | URLs/domains not found in message are lost forever | Exact regex pattern; no fuzzy matching or entity linking |
| Multi-step handling | **Very Rigid** | "Navigate AND extract" forced into single tool | Keyword order determines single intent; no sequencing |
| Context per-message | **Very Rigid** | Each message standalone; no session-level reference resolution | No concept of session state or anaphora |
| Approval bridge | **Very Rigid** | Only exact phrases "yes", "approve" trigger approval | Fixed regex pattern; no variation tolerance |

**Assessment:** System is overly rigid in most dimensions. Sensitivity to phrasing and keyword order creates many false negatives.

---

### 4.3 Permissiveness Assessment

| Decision Point | Current Permissiveness | Impact | Why Permissive |
|---|---|---|---|
| Mission creation without validation | **Too Permissive** | "get stuff" creates mission; fails at execution | No pre-flight check for completeness |
| Tool confidence threshold | **Too Permissive** | Tool accepted at 0.15 confidence (85% failure rate at that level) | Threshold not calibrated to actual tool success rate |
| Handler fallback | **Too Permissive** | Questions with no matching pattern get generic "I understand" help | No distinction between answerable and unanswerable questions |
| Approval bridge message matching | **Slightly Permissive** | "Yes." or "APPROVE!" accepted; variation is good but matches could be more semantic | Regex flexible but still keyword-based |

**Assessment:** Too permissive on mission creation; too rigid on everything else. Imbalance causes missions to be created that shouldn't be.

---

### 4.4 Safety Override vs. Usefulness Trade-off

| Feature | Safety Priority | Usefulness Priority | Current Stance | Gap |
|---|---|---|---|---|
| Mission auto-execution | Explicit blocks (no autonomy) | Should execute on clear intent | Heavy safety bias ✅ | GOOD: Prevents autonomy |
| Clarification questions | Ask before acting on ambiguous intent | Execute immediately on clear intent | Balanced | GOOD: Most cases work |
| Help text routing | Never execute on uncertain requests | Suggest action formats to user | Heavy safety bias | MINOR: Misses semantic ints |
| URL/domain handling | Fail safely if URL missing | Infer URL from context if possible | Heavy safety bias | MAJOR: Prevents multi-turn |
| Multi-step execution | Only execute single step | Decompose and execute sequence | Heavy safety bias | MAJOR: Blocks complex requests |
| Confirmation for low-confidence | Confirm before executing | Execute if confidence >70% | Balanced | GOOD: Prevents false positives |

**Assessment:** Safety generally prioritized over usefulness. Most gaps are acceptable except context handling (URLs lost) and multi-step (complex requests blocked).

---

### 4.5 Clarity vs. Usefulness Trade-off

| Feature | Clarity Priority | Usefulness Priority | Current Stance | Gap |
|---|---|---|---|---|
| Response to vague mission | "Tool selection failed" error | "You need to specify X. Are you looking for Y or Z?" | Clarity sacrificed ❌ | MAJOR: Error message uninformative |
| Handling of multi-intent | Fail with error | Decompose and clarify | Clarity sacrificed ❌ | MAJOR: User confusion |
| Pronoun resolution | Fail on "navigate there" | Infer "there" from session | Clarity sacrificed ❌ | MAJOR: Multi-turn broken |
| Help text | Generic fallback | Contextual help based on history | Clarity sacrificed ❌ | MAJOR: Help irrelevant |
| Intent reasoning | "Message is ambiguous" (vague) | Explain what's missing specifically | Clarity acceptable ✅ | GOOD: Reasoning included |

**Assessment:** Clarity consistently sacrificed. Error messages uninformative. User gets "failed" without knowing why. Multi-turn conversations frustrating due to context loss.

---

## 5. IDEAL DECISION ENGINE (CONCEPTUAL DESIGN)

### 5.1 Decision Flow Architecture

```
User Message (+ Session Context)
    ↓
[STEP 0: Session Context Loading]
    • Retrieve recent messages from session
    • Load recent entities (URLs, domains, tables)
    • Load recent missions and their results
    • Build "conversational context" object
    ↓
[STEP 1: Semantic Parsing]
    • Extract entities (URLs, emails, domains, keywords)
    • Resolve pronouns/references against context
    • Identify semantic intent (ask|do|permission|procedural)
    • Classify completeness (has object? has source? has constraints?)
    ↓
[STEP 2: Multi-Stage Intent Classification]
    Stage A: Keyword-based rough classification
    → intent_candidates = [REQUEST_EXECUTION: 0.8, QUESTION: 0.6, FORECAST: 0.3]
    
    Stage B: Semantic refinement
    → Apply intent-type rules:
       - "extract information" → downgrade to QUESTION (info-incapable target)
       - "get the emails" → upgrade to REQUEST_EXECUTION (action-capable target)
    
    Stage C: Context application
    → Use session history:
       - Prior URL in session → increase EXECUTE confidence for "extract it"
       - Recent status checks → increase STATUS_CHECK confidence for "what's happening"
    
    Stage D: Finalize
    → Sort by confidence, return top-3 candidates with confidence intervals
    ↓
[STEP 3: Confidence-Based Routing Decision]
    if top_confidence > 0.85:
        → CERTAIN → Execute directly (with explicit confirmation for HIGH-risk)
    elif top_confidence > 0.70:
        → HIGH → Propose with "I think you want to..." phrasing
    elif top_confidence > 0.50:
        → MEDIUM → Propose + ask for clarification in parallel
    else:
        → LOW/AMBIGUOUS → Ask clarifying question with option to override
    ↓
[STEP 4: Completeness Check (Pre-Mission Validation)]
    if intent requires action:
        Check required fields:
        - EXECUTE needs: object (what), source/target (where/on what), optionally: constraints (count/type)
        - FORECAST needs: what to predict, over what time period
        - SEARCH needs: query (what), optionally: domain (where)
        
        if any required field missing:
            → Ask specific clarification: "I need to know WHERE to extract from"
            → Do NOT create incomplete mission
        else:
            → Proceed to mission creation
    ↓
[STEP 5: Multi-Step Decomposition]
    if "navigate AND extract AND summarize" detected:
        → Decompose into 3 sequential missions
        → Create dependency graph: extract depends on navigate
        → Ask user: "Should I: 1. Navigate, 2. Extract emails, 3. Group by domain?"
        → Create missions only after confirmation
    else:
        → Single mission
    ↓
[STEP 6: Handler Execution]
    Execute appropriate handler with:
    - Intent (+ top 3 alternative intents)
    - Confidence (+ confidence interval)
    - Completeness validation result
    - Session context
    - Decomposed steps (if multi-step)
    ↓
ResponseEnvelope (to user)
```

### 5.2 Intent Classification Refinement

**From:** Binary (actionable | not) + single intent type  
**To:** Probability distribution + multi-level confidence + semantic enrichment

**Intent Candidates with Confidence:**
```python
@dataclass
class IntentCandidate:
    intent_type: IntentType
    base_confidence: float          # Keyword-based (0-1)
    semantic_adjustment: float      # ±0.2 based on semantic analysis
    context_adjustment: float       # ±0.3 based on session history
    final_confidence: float         # Combined
    reasoning: List[str]            # Audit trail of adjustments
    confidence_tier: Tier           # CERTAIN|HIGH|MEDIUM|LOW|UNKNOWN
    required_fields_missing: List[str]  # ["source_url", "target_count"]
    suggested_actions: List[str]    # ["Ask for domain", "Clarify target"]
```

**Example Classification Result:**
```python
Intent classification for: "Extract the emails from there"

candidates = [
    IntentCandidate(
        intent_type=REQUEST_EXECUTION,
        base_confidence=0.75,           # "extract" keyword
        semantic_adjustment=+0.10,      # "emails" is action-capable
        context_adjustment=+0.15,       # "there" resolved to recent URL
        final_confidence=0.90,          # → CERTAIN
        confidence_tier=CERTAIN,
        required_fields_missing=[],
        suggested_actions=[]
    ),
    IntentCandidate(
        intent_type=QUESTION,
        base_confidence=0.15,
        semantic_adjustment=-0.05,
        context_adjustment=0.0,
        final_confidence=0.10,          # → UNLIKELY
        confidence_tier=LOW
    )
]

chosen = candidates[0]  # REQUEST_EXECUTION with 0.90 confidence
```

---

### 5.3 Semantic Field Enrichment

**What the system should extract and maintain:**

```python
@dataclass
class SemanticFields:
    entities: Dict[str, str]            # {"url": "https://...", "email": "admin@..."}
    action_object: Optional[str]        # "emails", "prices", "product titles"
    action_target: Optional[str]        # "site.com", "table#prices", "search results"
    constraints: Dict[str, Any]         # {"count": 10, "format": "csv", "exclude": ["spam"]}
    time_horizon: Optional[str]         # "current", "historical", "future"
    scope: Dict[str, str]               # {"domain": "site.com", "pages": 5}
    pronouns_resolved: Dict[str, str]   # {"there": "https://site.com", "it": "table#data"}
    implicit_context: str               # "from recent conversation: extract prices like before"
```

**Example:**
```python
User: "Get the top 10 product names and prices from there"
Session context: Recent URL = "https://amazon.com/category/electronics"

semantic_fields = SemanticFields(
    entities={"url": "https://amazon.com/category/electronics"},
    action_object="product names and prices",
    action_target="amazon.com/category/electronics",
    constraints={"count": 10, "fields": ["name", "price"]},
    scope={"domain": "amazon.com", "pages": 1},
    pronouns_resolved={"there": "https://amazon.com/category/electronics"}
)
```

---

### 5.4 Clarification Strategy

**From:** Binary (clarify | proceed)  
**To:** Clarification with multiple paths

**Clarification Types:**
```python
class ClarificationType(Enum):
    MISSING_OBJECT = "missing_object"        # "Get X" but no X specified
    MISSING_SOURCE = "missing_source"        # "From X" but no X specified
    AMBIGUOUS_INTENT = "ambiguous_intent"    # 3-way tie in intent confidence
    MISSING_CONSTRAINT = "missing_constraint" # "Get 50" but no indication of count
    MULTI_INTENT = "multi_intent"            # Multiple sequential steps
    REFERENCE_AMBIGUOUS = "reference_ambiguous"  # "it" or "there" unclear
    LOW_CONFIDENCE = "low_confidence"        # Confidence 0.5-0.7

class ClarificationQuestion:
    clarification_type: ClarificationType
    question_text: str                   # "What domain should I search?"
    options: List[str]                   # ["option1", "option2"]
    allow_free_text: bool                # User can type custom answer
    inferred_answer: Optional[str]       # "Did you mean: ___?"
    confidence_if_accepted: float        # 0.90 if user confirms inferred answer
```

**Examples:**

```python
# MISSING_OBJECT
user = "Extract from amazon.com"
clarification = ClarificationQuestion(
    clarification_type=MISSING_OBJECT,
    question_text="What should I extract? (e.g., product names, prices, reviews)",
    options=["Product names", "Prices", "Reviews", "All of the above"],
    inferred_answer=None,
    allow_free_text=True
)

# REFERENCE_AMBIGUOUS with inference
user = "Get it from there"
session_history = ["Recent URL: amazon.com", "Recent table: sales_data"]
clarification = ClarificationQuestion(
    clarification_type=REFERENCE_AMBIGUOUS,
    question_text="Which of these should I use?",
    options=["amazon.com", "sales_data table", "Something else"],
    inferred_answer="Did you mean: extract from amazon.com?",
    confidence_if_accepted=0.88
)

# MULTI_INTENT
user = "Navigate to the site, extract emails, and group them"
clarification = ClarificationQuestion(
    clarification_type=MULTI_INTENT,
    question_text="I can break this into 3 steps. Should I: 1. Navigate to site, 2. Extract emails, 3. Group by domain?",
    options=["Yes, do all 3", "Just navigate", "Just extract", "Custom sequence"],
    allow_free_text=False
)
```

---

### 5.5 Error Message Strategy

**From:** Generic technical errors  
**To:** User-centered, actionable feedback

**Current:**
```
"Tool selection failed (confidence: 0.15)"
"Mission status is not 'approved', cannot execute"
```

**Ideal:**
```python
class UserFacingError:
    user_message: str                   # What to show user
    technical_reason: str               # Internal audit trail
    actionable_suggestion: str          # What user should do next
    context: Dict[str, Any]             # Debug info for support

# Examples
error1 = UserFacingError(
    user_message="I need more details to get started. What should I extract?",
    technical_reason="Tool selection confidence 0.15 due to missing action_object",
    actionable_suggestion="Try: 'Extract product names from amazon.com'",
    context={"objective": "get stuff", "confidence_scores": {"web_extract": 0.15, "web_search": 0.12}}
)

error2 = UserFacingError(
    user_message="Let me check that page first. What's the URL?",
    technical_reason="Pronoun 'there' could not be resolved to recent URL; session context empty",
    actionable_suggestion="Provide the URL: 'Navigate to https://...'",
    context={"pronoun": "there", "session_history_length": 0}
)
```

---

### 5.6 Multi-Turn Conversation Support

**Session State Model:**

```python
@dataclass
class ConversationSession:
    session_id: str
    user_id: str
    messages: List[Message]             # All messages in chronological order
    
    # Entity memory
    recent_urls: List[str]              # Last 5 URLs mentioned
    recent_domains: List[str]           # Last 5 domains
    recent_tables: List[Dict]           # Last 3 tables extracted
    recent_missions: List[Mission]      # Last 5 missions (executed or proposed)
    
    # Context
    current_action_object: Optional[str] # "prices" if user has been extracting prices
    current_action_target: Optional[str] # URL if user has been focusing on one site
    
    # Pronouns
    pronouns: Dict[str, str]            # {"it": last_entity, "there": last_url}
    
    def resolve_pronoun(pronoun: str) -> Optional[str]:
        """Resolve "it", "there", "that" to recent entity"""
        if pronoun == "it":
            return self.recent_tables[-1] if self.recent_tables else None
        elif pronoun in ["there", "that"]:
            return self.recent_urls[-1] if self.recent_urls else None
        ...

    def apply_implicit_context(new_objective: str) -> str:
        """Apply session context to new objective"""
        if new_objective == "extract more":
            return f"Extract from {self.current_action_target}"
        if "extract it" in new_objective:
            return new_objective.replace("it", self.current_action_object)
        ...
```

---

### 5.7 Handler Evolution

**New Handler Signature:**

```python
def _handle_execute(
    intent_candidates: List[IntentCandidate],  # Top 3 with confidence
    semantic_fields: SemanticFields,            # Extracted entities + context
    session_context: ConversationSession,       # History + pronouns
    message: str,
    session_id: str
) -> ResponseEnvelope:
    """
    Execute handler with rich context and multi-level confidence.
    
    Decision logic:
    1. If top_confidence > 0.85 AND all required fields present:
       → Create mission immediately
    2. Elif top_confidence > 0.70 AND minor fields missing:
       → Create mission with clarification_note
    3. Elif top_confidence > 0.50 AND major fields missing:
       → Ask specific clarification, offer to create mission when answered
    4. Else:
       → Ask clarifying question with suggested actions
    """
    ...
```

---

## 6. SUMMARY: ARCHITECTURAL WEAKNESSES

### Rigid Dimensions
1. **Keyword order dependency** — Keyword priority order determines intent; "Tell me about X from Y" misclassified as QUESTION
2. **Binary actionable flag** — No gradation between "definitely executable" and "might be executable"
3. **Message independence** — Each message classified separately; session context ignored
4. **Single-intent constraint** — Multi-step objectives forced into single intent
5. **Semantic blindness** — "Get information" treated same as "Get data"

### Permissive Dimensions
1. **Mission creation without validation** — "Get stuff" creates mission that fails at execution
2. **Tool confidence threshold** — Accepted at 0.15 (too low); many false starts
3. **Handler fallback** — Generic help for unmatched patterns

### Missing Dimensions
1. **Conversational context** — Pronouns, references, entity linking
2. **Multi-step decomposition** — No sequencing or dependencies
3. **Semantic completeness** — No pre-flight check for required fields
4. **User-facing error clarity** — "Failed" without explanation
5. **Confidence tiers & gradation** — All intents treated uniformly

---

## CONCLUSION

**Current State:** Buddy's decision engine is a **rigid, keyword-driven rule system** optimized for simple, unambiguous, explicitly phrased requests. It fails gracefully (doesn't auto-execute) but frustrates users with poor error messages and context loss.

**When It Works Well:**
- ✅ Explicit imperative requests: "Get prices from amazon.com"
- ✅ Single-turn, complete requests
- ✅ Requests with all required context in one message

**When It Fails:**
- ❌ Question-phrased actions: "Can you find me X?"
- ❌ Multi-turn conversations: "Navigate there and extract it"
- ❌ Vague/incomplete requests: "Get stuff"
- ❌ Complex multi-step missions: "Navigate, extract, summarize"
- ❌ Context-dependent requests: "Get more details"

**Ideal Future State:** A **confidence-aware, context-preserving, multi-intent-decomposing** system that gracefully handles:
1. Vague requests with targeted clarifications (not generic help)
2. Multi-turn conversations with entity/pronoun resolution
3. Multi-step missions with decomposition
4. Low-confidence intents with adaptive behavior
5. Semantic understanding (not just keyword matching)

---

**Ready for design decisions.**
