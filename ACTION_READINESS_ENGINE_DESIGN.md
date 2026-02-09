# ACTION READINESS ENGINE - DESIGN SPECIFICATION

**Date:** February 8, 2026  
**Status:** Design Only (No Implementation)  
**Purpose:** Deterministic decision layer for mission readiness validation  

---

## OVERVIEW

The **Action Readiness Engine** sits between intent classification and mission creation, answering one critical question:

> **Is this user request ready to become a mission right now?**

Current system: Classifies intent → immediately creates mission → fails at execution time

New system: Classifies intent → validates readiness → either creates mission OR asks targeted clarification

### Core Principle

**Never create a mission that will fail at execution time due to missing or ambiguous information.**

### Decision Tree

```
User Message + Session Context
    ↓
Generate Intent Candidates (top 3)
    ↓
Rank by Confidence & Applicability
    ↓
Select Best Candidate
    ↓
Validate Action Readiness
    │
    ├─ READY (all required fields present)
    │  └─→ Emit mission_proposal (to InteractionOrchestrator)
    │
    ├─ INCOMPLETE (missing required field)
    │  └─→ Generate targeted clarification_question
    │      └─→ Emit clarification_response (to InteractionOrchestrator)
    │
    ├─ AMBIGUOUS (top 2 candidates within 0.10 confidence)
    │  └─→ Ask which intent: "Did you mean X or Y?"
    │      └─→ Emit clarification_response (to InteractionOrchestrator)
    │
    ├─ QUESTION (intent is informational; no action needed)
    │  └─→ Route to _handle_respond()
    │
    └─ META (internal/meta-level intent)
       └─→ Route to _handle_meta()
```

---

## 1. INTENT CANDIDATE GENERATION

### 1.1 Multi-Intent Classification Process

**Input:** User message + session context

**Output:** Ranked list of `IntentCandidate` objects

```python
@dataclass
class IntentCandidate:
    """Ranked intent classification with confidence and metadata."""
    
    # Core classification
    intent_type: str                    # "navigate", "extract", "search", "calculate", etc.
    base_confidence: float              # 0.0-1.0, from keyword matching
    
    # Confidence adjustments
    semantic_adjustment: float          # ±0.20 (semantic type checking)
    context_adjustment: float           # ±0.30 (session history)
    execution_adjustment: float         # ±0.15 (execution likelihood)
    final_confidence: float             # base + adjustments (clamped 0-1)
    
    # Confidence tier
    confidence_tier: Tier               # CERTAIN | HIGH | MEDIUM | LOW
    
    # Semantic fields
    action_object: Optional[str]        # "emails", "prices", "product titles"
    action_target: Optional[str]        # "site.com", "table#data", "URL"
    source_url: Optional[str]           # Extracted or resolved URL
    constraints: Dict[str, Any]         # {"count": 10, "format": "csv"}
    
    # Readiness
    required_fields: List[str]          # Fields needed for this intent
    missing_fields: List[str]           # Fields that are currently missing
    is_ready: bool                      # All required fields present?
    
    # Context
    pronouns_resolved: Dict[str, str]   # {"it": "product_table", "there": "url"}
    session_entity_used: Optional[str]  # Which session entity was referenced
    
    # Reasoning (audit trail)
    reasoning: List[str]                # Why this intent was selected
```

### 1.2 Generation Steps

**Step A: Keyword-Based Initial Classification**

```
Message: "Extract the product names from amazon"

Keyword scoring:
  - "extract" → EXTRACT intent: +0.40
  - "product names" → specific object: +0.20
  - "from amazon" → source indicator: +0.30
  - "the" → article (neutral): 0.0
  
Initial candidates:
  1. EXTRACT (confidence: 0.90)
  2. SEARCH (confidence: 0.30)  ← Lower due to no search keywords
  3. NAVIGATE (confidence: 0.20) ← Lower due to no navigation keywords
```

**Step B: Semantic Type Checking** (±0.20)

```
For each candidate, check semantic consistency:

EXTRACT candidate:
  - action_object = "product names" → ACTION_CAPABLE? YES (+0.10)
  - action_target = "amazon" (domain) → VALID? YES (+0.10)
  - semantic_adjustment = +0.20
  - new_confidence = 0.90 + 0.20 = 1.0 (clamped)

SEARCH candidate:
  - No specific object → VAGUE? YES (-0.10)
  - domain present → some structure? YES (+0.05)
  - semantic_adjustment = -0.05
  - new_confidence = 0.30 - 0.05 = 0.25
```

**Step C: Context Application** (±0.30)

```
Session history:
  - Recent URLs: ["https://amazon.com/electronics", "https://ebay.com"]
  - Recent objects: ["prices", "emails"]
  - Last intent: EXTRACT
  - Last tool used: web_extract

EXTRACT candidate:
  - context matches recent pattern? YES (+0.10)
  - "amazon" matches recent domain? YES (+0.15)
  - confidence trend supporting extraction? YES (+0.05)
  - context_adjustment = +0.30
  - new_confidence = 1.0 + 0.30 = 1.0 (clamped)

SEARCH candidate:
  - context suggests search? NO (-0.20)
  - context_adjustment = -0.20
  - new_confidence = 0.25 - 0.20 = 0.05
```

**Step D: Execution Likelihood** (±0.15)

```
Can the tool successfully execute with current information?

EXTRACT candidate:
  - Tool: web_extract
  - Input quality: "product names" + "amazon" → HIGH QUALITY (+0.10)
  - URL found? YES (+0.05)
  - execution_adjustment = +0.15
  - final_confidence = 1.0 + 0.15 = 1.0 (clamped)

SEARCH candidate:
  - Tool: web_search
  - Input quality: NONE → LOW QUALITY (-0.10)
  - Query specificity: MISSING (-0.05)
  - execution_adjustment = -0.15
  - final_confidence = 0.05 - 0.15 = 0.0 (clamped)
```

**Step E: Final Ranking**

```
Final candidates:
  1. EXTRACT (confidence: 1.0)   ← CERTAIN
  2. SEARCH (confidence: 0.0)     ← Dropped (too low)
  3. NAVIGATE (confidence: 0.20)  ← Keep in case, but LOW

Return top 3 with confidence > 0.0
```

### 1.3 Extraction of Semantic Fields

**For each candidate, extract structured data:**

```python
def extract_semantic_fields(message: str, candidate: IntentType, session: Session) -> Dict:
    """
    Extract action_object, action_target, constraints from message.
    """
    
    # Action Object (what to extract/find/navigate)
    action_object = extract_noun_phrase(message)  # "product names", "emails", "prices"
    
    # Action Target (where to extract/find from)
    action_target = extract_domain_or_url(message)  # "amazon.com", "https://..."
    if not action_target and candidate == "NAVIGATE":
        action_target = extract_url(message)  # "https://example.com"
    
    # Source URL (resolved from target or session)
    source_url = None
    if action_target.startswith("http"):
        source_url = action_target
    else:
        source_url = resolve_domain_to_url(action_target, session)  # "amazon.com" → "https://amazon.com"
    
    # Constraints (count, format, filters)
    constraints = {
        "count": extract_count_constraint(message),      # "top 10" → {"count": 10}
        "format": extract_format_constraint(message),    # "csv", "json"
        "filter": extract_filter_constraint(message),    # "exclude spam"
        "time_horizon": extract_time_horizon(message)    # "current", "historical"
    }
    
    return {
        "action_object": action_object,
        "action_target": action_target,
        "source_url": source_url,
        "constraints": constraints
    }
```

**Example:**
```
Message: "Get the top 5 product names and prices from amazon this week"
Candidate: EXTRACT

Extracted fields:
  action_object: "product names and prices"
  action_target: "amazon"
  source_url: "https://amazon.com"  (resolved from session or defaults)
  constraints: {
    "count": 5,
    "format": None,
    "filter": None,
    "time_horizon": "current_week"
  }
```

---

## 2. CONFIDENCE TIERING

### 2.1 Tier Definitions

```python
class ConfidenceTier(Enum):
    """Intent classification confidence tiers and routing implications."""
    
    CERTAIN = "CERTAIN"        # 0.85-1.00 confidence
    HIGH = "HIGH"              # 0.70-0.84 confidence
    MEDIUM = "MEDIUM"          # 0.50-0.69 confidence
    LOW = "LOW"                # 0.20-0.49 confidence
    UNKNOWN = "UNKNOWN"        # 0.00-0.19 confidence
```

### 2.2 Tier Thresholds & Meanings

| Tier | Confidence Range | Meaning | Action |
|---|---|---|---|
| **CERTAIN** | 0.85-1.0 | "I'm 85%+ sure this is what you want" | ✅ Create mission immediately (if all fields present) |
| **HIGH** | 0.70-0.84 | "I'm pretty confident this is your intent" | ✅ Create mission + confirmation message ("I think you want to...") |
| **MEDIUM** | 0.50-0.69 | "This could be what you want, but unclear" | ⚠️ Ask for confirmation + offer alternative intents |
| **LOW** | 0.20-0.49 | "Weak signal; could mean several things" | ❌ Ask clarifying question with options |
| **UNKNOWN** | 0.00-0.19 | "Not enough information to classify" | ❌ Ask for more details |

### 2.3 Confidence Tier Calculation

```python
def calculate_tier(final_confidence: float) -> ConfidenceTier:
    """Map confidence score to tier."""
    
    if final_confidence >= 0.85:
        return ConfidenceTier.CERTAIN
    elif final_confidence >= 0.70:
        return ConfidenceTier.HIGH
    elif final_confidence >= 0.50:
        return ConfidenceTier.MEDIUM
    elif final_confidence >= 0.20:
        return ConfidenceTier.LOW
    else:
        return ConfidenceTier.UNKNOWN
```

### 2.4 Confidence Spread (Multi-Intent Disambiguation)

**If top 2 candidates within 0.10 confidence:**
- Treat as AMBIGUOUS (even if both HIGH or CERTAIN)
- Ask user to choose between them

**Example:**
```
Message: "Get the top 10 from site.com"

Candidate 1: EXTRACT (confidence: 0.75)  ← HIGH
Candidate 2: SEARCH (confidence: 0.68)   ← MEDIUM

Confidence spread: 0.75 - 0.68 = 0.07 (< 0.10 threshold)

Decision: AMBIGUOUS
→ Ask: "Did you want to extract data or search for information?"
```

---

## 3. ACTION READINESS RULES

### 3.1 Required Fields Per Intent

**Each intent type has mandatory fields that must be present for readiness.**

#### EXTRACT Intent

```
Required fields:
  ✓ action_object     (what to extract: "emails", "prices", "titles")
  ✓ action_target     (where to extract from: URL, domain, or resolvable)
  
Optional but recommended:
  ? constraints       (count, format, filters)
  ? time_horizon      (current, historical, future)

Examples:

Message: "Extract emails from linkedin.com"
  action_object: "emails" → PRESENT ✓
  action_target: "linkedin.com" → PRESENT ✓
  Decision: READY

Message: "Extract from the site"
  action_object: (missing) → MISSING ✗
  action_target: "the site" → AMBIGUOUS (not a URL/domain)
  Decision: INCOMPLETE
  Missing: ["action_object", "action_target (resolution)"]
  Question: "What should I extract, and which site?"

Message: "Extract emails"
  action_object: "emails" → PRESENT ✓
  action_target: (missing) → MISSING ✗
  Decision: INCOMPLETE (but can infer from session if recent URL exists)
  Missing: ["action_target"]
  Question: "Extract emails from where?" (offer recent URLs as options)
```

#### NAVIGATE Intent

```
Required fields:
  ✓ action_target     (URL or domain to navigate to)
  
Optional but recommended:
  ? action_object     (what to look for on the page)
  ? constraints       (wait time, scroll depth, etc.)

Examples:

Message: "Navigate to github.com"
  action_target: "github.com" → PRESENT ✓
  Decision: READY

Message: "Go to there"
  action_target: "there" (pronoun) → AMBIGUOUS
  Decision: INCOMPLETE (check session for recent URL)
  If session has recent URL:
    Decision: READY (resolved "there" → recent_url)
  Else:
    Decision: INCOMPLETE
    Missing: ["action_target (reference resolution)"]
    Question: "Where should I navigate?"

Message: "Open the page"
  action_target: "the page" (pronoun) → AMBIGUOUS
  Decision: INCOMPLETE
  Missing: ["action_target"]
  Question: "Which page?"
```

#### SEARCH Intent

```
Required fields:
  ✓ action_object     (what to search for: "Python news", "AI tools")
  
Optional but recommended:
  ? action_target     (where to search: domain, search engine)
  ? constraints       (count of results, language, etc.)

Examples:

Message: "Search for Python tutorials"
  action_object: "Python tutorials" → PRESENT ✓
  Decision: READY

Message: "Find it"
  action_object: "it" (pronoun) → AMBIGUOUS
  Decision: INCOMPLETE
  Missing: ["action_object"]
  Question: "What should I search for?"

Message: "Search"
  action_object: (missing) → MISSING ✗
  Decision: INCOMPLETE
  Missing: ["action_object"]
  Question: "What would you like me to search for?"
```

#### CALCULATE Intent

```
Required fields:
  ✓ action_object     (math expression or numbers: "12 * 19", "sum of 1,2,3")
  
Optional:
  ? constraints       (precision, format)

Examples:

Message: "Calculate 12 + 5"
  action_object: "12 + 5" → PRESENT ✓
  Decision: READY

Message: "What's the total"
  action_object: (missing; no numbers) → MISSING ✗
  Decision: INCOMPLETE
  Missing: ["action_object (numbers)"]
  Question: "What numbers should I calculate?"
```

### 3.2 Readiness Validation Algorithm

```python
def validate_action_readiness(
    candidate: IntentCandidate,
    message: str,
    session: Session
) -> ReadinessResult:
    """
    Determine if this intent candidate is ready for mission creation.
    
    Returns:
      ReadinessResult with decision, missing_fields, clarification_question
    """
    
    # Get required fields for this intent
    required = INTENT_REQUIREMENTS[candidate.intent_type]
    
    # Check each required field
    missing = []
    for field in required:
        value = candidate.get_field(field)
        
        if value is None:
            missing.append(field)
        
        elif field == "action_object" and is_generic_or_vague(value):
            # "stuff", "things", "data" are too vague
            missing.append(f"{field} (too vague)")
        
        elif field == "action_target" and is_pronoun(value):
            # Try to resolve pronoun from session
            resolved = session.resolve_pronoun(value)
            if resolved:
                candidate.action_target = resolved  # Update
                candidate.source_url = resolve_url(resolved)
            else:
                missing.append(f"{field} (pronoun unresolved)")
    
    # Decide readiness
    if len(missing) == 0:
        return ReadinessResult(
            decision="READY",
            missing_fields=[],
            clarification_question=None
        )
    
    elif candidate.confidence_tier in [CERTAIN, HIGH]:
        # High confidence but missing some fields
        # Ask specific clarification
        return ReadinessResult(
            decision="INCOMPLETE",
            missing_fields=missing,
            clarification_question=generate_clarification(missing, candidate)
        )
    
    else:
        # Low confidence AND missing fields
        # Ask more comprehensive clarification
        return ReadinessResult(
            decision="INCOMPLETE",
            missing_fields=missing,
            clarification_question=generate_comprehensive_clarification(candidate, message)
        )
```

---

## 4. CLARIFICATION STRATEGY

### 4.1 Targeted Clarifications (Not Generic Help)

**Current Problem:**
```
Message: "Get stuff"
Current response: "To scrape a website: 1. Specify target 2. Define what to extract..."
              → Generic help text; user already frustrated
```

**New Approach:**
```
Message: "Get stuff"
Readiness engine analysis:
  - Intent: EXTRACT (confidence: 0.65)
  - Missing: action_object, action_target
  - Session context: Recently navigated to amazon.com

Response: "I can help with that! To extract data, I need:
  1. WHAT to extract (e.g., prices, titles, emails)
  2. WHERE to extract from
  
  Did you want to extract from amazon.com (your recent site)?"

  [Options: "Prices", "Product titles", "Something else"]
```

### 4.2 Clarification Types

```python
class ClarificationType(Enum):
    """Types of clarifications the readiness engine can emit."""
    
    MISSING_OBJECT = "missing_object"              # "What?"
    MISSING_TARGET = "missing_target"              # "From where?"
    AMBIGUOUS_REFERENCE = "ambiguous_reference"    # "Which site is 'there'?"
    TOO_VAGUE = "too_vague"                       # "stuff" → "What kind of data?"
    MULTI_INTENT = "multi_intent"                 # "Navigate AND extract?"
    INTENT_AMBIGUOUS = "intent_ambiguous"         # "Extract OR search?"
    CONSTRAINT_UNCLEAR = "constraint_unclear"      # "How many results?"
    MISSING_STEP = "missing_step"                 # "Sequence unclear"

class ClarificationQuestion:
    """Targeted clarification for user."""
    
    clarification_type: ClarificationType
    question_text: str                            # Main question
    context: str                                  # Why we're asking
    options: List[str]                            # Suggested answers
    allow_free_text: bool                         # Can user type custom answer?
    inferred_answer: Optional[str]                # "Did you mean...?"
    session_reference: Optional[str]              # "Like your recent search for X?"
```

### 4.3 Clarification Generation

**Algorithm:**

```
Input: missing_fields, candidate, session_context

For each missing field:
  IF field == "action_object" AND message has generic word like "stuff":
    question_type = TOO_VAGUE
    question_text = "What kind of data?" + example(s)
    options = [common_targets_for_this_intent]
  
  ELIF field == "action_target" AND value is pronoun:
    question_type = AMBIGUOUS_REFERENCE
    question_text = "Which site?" + recent_urls_from_session
    options = recent_urls + "something else"
    inferred = recent_urls[0] if any else None
  
  ELIF field == "action_target" AND missing entirely:
    question_type = MISSING_TARGET
    question_text = "Where should I look?"
    options = recent_urls_from_session + "specify new site"
    inferred = recent_urls[0] if any else None
  
  ELSE:
    question_type = GENERIC
    question_text = f"Could you tell me the {field}?"
    options = []
    allow_free_text = True
```

**Example Clarifications:**

```
Message: "Extract it"
Session: Has recent URL "https://example.com"

Analysis:
  - action_object: "it" (pronoun, too vague)
  - action_target: missing

Clarification:
  type: AMBIGUOUS_REFERENCE
  question: "Extract what from example.com? (e.g., titles, emails, prices)"
  options: ["Product titles", "Email addresses", "Prices", "Something else"]
  inferred: "Did you mean extract from https://example.com?"

---

Message: "Get more"
Session: Recent extraction of "prices" from "amazon.com"

Analysis:
  - action_object: "more" (vague, but context suggests "prices")
  - action_target: missing (but context suggests "amazon.com")

Clarification:
  type: CONSTRAINT_UNCLEAR
  question: "Get more prices from amazon.com? How many?"
  options: ["10", "25", "50", "100", "All"]
  inferred: "Did you mean get 25 more prices?"

---

Message: "Navigate there and get the emails"
Session: Recent URL "https://linkedin.com"

Analysis:
  - Intent: MULTI_INTENT (navigate + extract)
  - Step 1: navigate to "there" (pronoun, resolves to linkedin.com)
  - Step 2: extract "emails"

Clarification:
  type: MULTI_INTENT
  question: "Should I: 1. Navigate to linkedin.com, 2. Extract emails?"
  options: ["Yes, do both", "Just navigate", "Just extract emails", "Custom"]
  inferred: "I can break this into steps for you..."
```

---

## 5. SESSION CONTEXT MODEL

### 5.1 Session State Structure

```python
@dataclass
class SessionContext:
    """Persistent context across conversation turns."""
    
    session_id: str
    user_id: str
    
    # Entity memory
    recent_urls: List[str]              # Last 5 URLs mentioned/used (LIFO)
    recent_domains: List[str]           # Last 5 domains mentioned (LIFO)
    recent_tables: List[Dict]           # Last 3 structured tables (LIFO)
    recent_objects: List[str]           # Last 5 extracted objects (LIFO)
    
    # Mission history
    recent_missions: List[Mission]      # Last 5 missions (LIFO)
    recent_results: List[Result]        # Last 5 execution results (LIFO)
    
    # Contextual focus
    current_domain: Optional[str]       # Domain user is currently focused on
    current_object_type: Optional[str]  # Type of data being extracted ("prices", "emails")
    
    # Pronouns & references
    pronoun_map: Dict[str, str]         # {"there": "https://...", "it": "prices"}
    
    # Conversation state
    last_message_time: datetime
    message_count: int
    
    # Metadata
    created_at: datetime
    last_updated_at: datetime
    
    def resolve_pronoun(self, pronoun: str) -> Optional[str]:
        """Resolve pronouns: 'there' → URL, 'it' → object"""
        
        if pronoun in ["there", "that", "that site", "the site"]:
            return self.recent_urls[-1] if self.recent_urls else None
        
        elif pronoun in ["it", "them", "those"]:
            return self.current_object_type or \
                   self.recent_objects[-1] if self.recent_objects else None
        
        elif pronoun in ["here", "this site", "this page"]:
            return self.recent_urls[-1] if self.recent_urls else None
        
        else:
            return None
    
    def apply_implicit_context(self, message: str) -> Dict[str, str]:
        """Apply session context to fill in missing information."""
        
        result = {}
        
        # If message has verb but no object, infer from recent
        if has_verb(message) and not has_object(message):
            if self.current_object_type:
                result["inferred_object"] = self.current_object_type
        
        # If message lacks domain/URL, infer from recent
        if has_verb(message) and not has_domain(message):
            if self.current_domain:
                result["inferred_domain"] = self.current_domain
            elif self.recent_urls:
                result["inferred_url"] = self.recent_urls[-1]
        
        return result
    
    def update_on_mission_execution(self, mission: Mission, result: Result):
        """Update context after successful mission execution."""
        
        # Track what was extracted
        if mission.intent == "extract":
            self.current_object_type = mission.action_object
            if mission.action_target:
                self.current_domain = mission.action_target
                if mission.source_url:
                    self.recent_urls.append(mission.source_url)
                    self.recent_urls = self.recent_urls[-5:]  # Keep last 5
        
        # Track missions
        self.recent_missions.append(mission)
        self.recent_missions = self.recent_missions[-5:]  # Keep last 5
        
        # Track results
        self.recent_results.append(result)
        self.recent_results = self.recent_results[-5:]  # Keep last 5
        
        self.last_updated_at = datetime.now()
```

### 5.2 Pronoun Resolution Rules

```python
def resolve_reference(pronoun: str, session: SessionContext, message: str) -> Optional[str]:
    """
    Resolve pronouns and references to concrete values.
    
    Returns: Resolved value or None if unresolvable
    """
    
    pronoun_lower = pronoun.lower().strip()
    
    # URL/domain references
    url_pronouns = ["there", "that", "that site", "the site", "here", "this page", "that place"]
    if pronoun_lower in url_pronouns:
        if session.recent_urls:
            return session.recent_urls[-1]  # Most recent URL
        elif session.recent_domains:
            return f"https://{session.recent_domains[-1]}"  # Most recent domain
        else:
            return None  # Unresolvable
    
    # Object/data references
    object_pronouns = ["it", "them", "those", "that data", "this"]
    if pronoun_lower in object_pronouns:
        if session.current_object_type:
            return session.current_object_type
        elif session.recent_objects:
            return session.recent_objects[-1]  # Most recent object
        else:
            return None  # Unresolvable
    
    # Temporal references
    time_pronouns = ["then", "before", "previously"]
    if pronoun_lower in time_pronouns:
        # Not actionable; more of a context reference
        return None
    
    return None  # Unrecognized pronoun
```

### 5.3 Context Update Triggers

**Session context updated when:**

1. **URL Mentioned:** Add to `recent_urls`
   ```
   User: "Navigate to github.com"
   → recent_urls.append("https://github.com")
   ```

2. **Domain Extracted:** Add to `recent_domains`
   ```
   Mission objective: "Extract from amazon.com"
   → recent_domains.append("amazon.com")
   ```

3. **Mission Executed:** Update focus areas
   ```
   Mission: Extract prices from amazon.com (successful)
   → current_object_type = "prices"
   → current_domain = "amazon.com"
   → recent_missions.append(mission)
   ```

4. **Data Extracted:** Track object types
   ```
   Artifact result: {"extracted_data": ["email1@...", "email2@..."]}
   → current_object_type = "emails"
   → recent_objects.append("emails")
   ```

5. **New Message Received:** Update timing
   ```
   → last_message_time = now()
   → message_count += 1
   ```

---

## 6. FAILURE AVOIDANCE PATTERNS

### Pattern #1: Empty Missions

**Problem:** "Get stuff" → mission created → tool fails (no context)

**Prevention:**
```
Readiness engine catches this:

Message: "Get stuff"
Intent candidates: [EXTRACT (0.55), SEARCH (0.30)]
Confidence tier: MEDIUM

Semantic check:
  action_object: "stuff" → VAGUE (too generic)
  action_target: missing

Validation result:
  Decision: INCOMPLETE
  Missing: ["action_object (too vague)", "action_target"]
  
  Clarification:
    "What kind of data? (e.g., prices, emails, product titles)"
    "Where should I look? (e.g., recent sites: amazon.com)"

→ NEVER CREATE MISSION

Outcome:
  - User must answer clarification
  - Only then is mission created
  - No failed execution at tool time
```

### Pattern #2: Dropped URLs

**Problem:** User says "Navigate there" but "there" is undefined

**Prevention:**
```
Message: "Navigate there"
Intent: NAVIGATE (confidence: 0.80)

Semantic fields:
  action_target: "there" (pronoun)

Readiness validation:
  Required field: action_target
  Current value: "there" (pronoun)
  
  Session lookup:
    recent_urls = ["https://example.com"]
    session.resolve_pronoun("there") → "https://example.com"
  
  Update: action_target = "https://example.com"

Decision: READY
→ Create mission with resolved URL

Outcome:
  - Pronoun automatically resolved from session
  - No lost context
  - Mission has concrete URL
```

**If no session history:**
```
Message: "Navigate there"
Session: Empty (new conversation)

Resolution:
  session.resolve_pronoun("there") → None (no recent URLs)

Readiness validation:
  Required field: action_target
  Resolution attempt: FAILED
  
  Decision: INCOMPLETE
  Clarification: "Where should I navigate to?"

Outcome:
  - User forced to provide URL
  - No ambiguous mission created
```

### Pattern #3: Premature Execution

**Problem:** Low-confidence mission created and executed

**Prevention:**
```
Message: "Get more"
Session: Recent extraction of "prices" from "amazon.com"

Intent candidates:
  [EXTRACT (0.55), SEARCH (0.45)]  ← Both MEDIUM confidence, close spread

Analysis:
  Confidence spread: 0.55 - 0.45 = 0.10 (= ambiguous threshold)
  Decision: AMBIGUOUS

Readiness result:
  Decision: QUESTION (not READY)
  
  Clarification:
    "Did you mean:
    1. Extract more prices from amazon.com
    2. Search for more information
    
    Which one?"

→ NEVER EXECUTE; ASK FIRST

User answer:
  "Extract more prices"
  → Confidence updated to CERTAIN
  → Missing fields checked
  → Mission created if ready
```

### Pattern #4: Frustration from Generic Help

**Problem:** "How do I extract?" → Generic help text (not actionable)

**Prevention:**
```
Message: "How do I extract?"
Intent classification: QUESTION (not actionable)

Readiness engine: N/A (questions skip readiness check)

Current path: _handle_respond() → generic help text

New path:
  1. Detect question word ("How")
  2. Check if this is PROCEDURAL QUESTION vs CAPABILITY QUESTION
  3. If procedural: Offer to demonstrate
     → "I can extract data. What would you like me to extract?"
     → Give example format
  4. If capability: List options
     → "I can extract, search, navigate, calculate..."

Outcome:
  - More helpful response
  - User can immediately ask for action if desired
  - Less frustration
```

---

## 7. EXAMPLE WALKTHROUGHS

### Example 1: Simple Ready Request (Happy Path)

```
=== SCENARIO ===
Message: "Extract email addresses from linkedin.com"
Session: First message (empty context)

=== PROCESSING ===

Step 1: Generate Intent Candidates
  Keyword scoring:
    "extract" → EXTRACT +0.50
    "email addresses" → object +0.20
    "from linkedin.com" → target +0.30
  
  Candidates:
    1. EXTRACT (base: 0.95)
    2. SEARCH (base: 0.15)

Step 2: Semantic Adjustments
  EXTRACT:
    action_object: "email addresses" → ACTION_CAPABLE (+0.05)
    action_target: "linkedin.com" → VALID_DOMAIN (+0.05)
    adjustment: +0.10
    confidence: 1.0 (clamped)
  
  SEARCH:
    adjustment: -0.05
    confidence: 0.10

Step 3: Context Application
  No session history
  adjustment: 0.0
  EXTRACT confidence: 1.0
  SEARCH confidence: 0.10

Step 4: Tier Assignment
  EXTRACT: 1.0 → CERTAIN
  SEARCH: 0.10 → UNKNOWN (dropped)

Step 5: Semantic Field Extraction
  action_object: "email addresses"
  action_target: "linkedin.com"
  source_url: "https://linkedin.com"  (resolved)
  constraints: {}

Step 6: Readiness Validation
  Required for EXTRACT: [action_object, action_target]
  Actual: [action_object✓, action_target✓]
  
  Missing: []
  Decision: READY

=== OUTPUT ===

{
  "decision": "READY",
  "intent": "extract",
  "confidence": 1.0,
  "confidence_tier": "CERTAIN",
  "action_object": "email addresses",
  "action_target": "linkedin.com",
  "source_url": "https://linkedin.com",
  "missing_fields": [],
  "clarification_question": null
}

=== RESULT ===
✅ Mission created immediately
✅ No clarification needed
✅ User sees: "I'll extract email addresses from linkedin.com. Approved?"
```

### Example 2: Incomplete Request with Targeted Clarification

```
=== SCENARIO ===
Message: "Extract emails"
Session: Recent URL: https://amazon.com, Recent object: prices

=== PROCESSING ===

Step 1: Generate Intent Candidates
  "extract" → EXTRACT +0.60
  "emails" → object +0.20
  
  Candidate: EXTRACT (base: 0.75)

Step 2: Semantic Adjustments
  action_object: "emails" → ACTION_CAPABLE (+0.10)
  action_target: missing (-0.10)
  adjustment: 0.0
  confidence: 0.75

Step 3: Context Application
  "emails" is different from recent "prices"
  No explicit target mentioned
  adjustment: 0.0
  confidence: 0.75 → MEDIUM tier

Step 4: Semantic Field Extraction
  action_object: "emails" ✓
  action_target: missing ✗
  
  Attempt resolution:
    session.resolve_pronoun("") → None
    recent_urls exist? YES: ["https://amazon.com"]
    inferred_target: None (not explicit, needs clarification)
  
  source_url: None (unresolved)

Step 5: Readiness Validation
  Required: [action_object, action_target]
  Actual: [action_object✓, action_target✗]
  
  Missing: ["action_target"]
  Confidence tier: MEDIUM
  
  Decision: INCOMPLETE
  
  Generate clarification:
    type: MISSING_TARGET
    recent_urls: ["amazon.com"]
    
    Question: "Where should I extract emails from?"
    
    Context: "I see you recently worked with amazon.com"
    
    Options: [
      "amazon.com",
      "linkedin.com",
      "another website"
    ]
    
    Inferred: "Extract from amazon.com?"

=== OUTPUT ===

{
  "decision": "INCOMPLETE",
  "intent": "extract",
  "confidence": 0.75,
  "confidence_tier": "MEDIUM",
  "action_object": "emails",
  "action_target": null,
  "missing_fields": ["action_target"],
  "clarification": {
    "type": "MISSING_TARGET",
    "question": "Extract emails from where?",
    "context": "You recently worked with amazon.com",
    "options": ["amazon.com", "linkedin.com", "another website"],
    "inferred_answer": "amazon.com"
  }
}

=== RESULT ===
⚠️ Mission NOT created yet
✅ Targeted question asked
✅ User sees: "Extract emails from where? (I see you recently used amazon.com)"
✅ User can reply: "amazon.com" or "Actually, try linkedin.com"
✅ Only then is mission created
```

### Example 3: Ambiguous Multi-Intent

```
=== SCENARIO ===
Message: "Go there and get the stuff"
Session: Recent URL: https://example.com, Recent object: product names

=== PROCESSING ===

Step 1: Generate Intent Candidates
  "go" → NAVIGATE +0.40
  "get" → EXTRACT +0.40
  
  Candidates:
    1. NAVIGATE (base: 0.65)
    2. EXTRACT (base: 0.60)

Step 2: Semantic Analysis
  "there" (pronoun) + "stuff" (vague)
  
  NAVIGATE:
    action_target: "there" (pronoun, resolvable)
    adjustment: +0.10
    confidence: 0.75
  
  EXTRACT:
    action_object: "stuff" (too vague)
    action_target: missing
    adjustment: -0.20
    confidence: 0.40

Step 3: Tier Assignment
  NAVIGATE: 0.75 → HIGH
  EXTRACT: 0.40 → LOW
  
  But also: MULTI-INTENT detected
    "go" AND "get" in same sentence
    → Sequential steps: [navigate, then extract]

Step 4: Ambiguity Check
  Primary: NAVIGATE (0.75)
  Secondary: EXTRACT (0.40) or MULTI_INTENT
  Spread: 0.75 - 0.40 = 0.35 (> 0.10 threshold)
  
  Not ambiguous in confidence, but MULTI-INTENT structure unclear

Step 5: Readiness Validation
  Detected: MULTI_INTENT (navigate + extract)
  
  Step 1 - Navigate:
    Required: [action_target]
    Actual: ["there" → resolve to "https://example.com"]
    Status: READY
  
  Step 2 - Extract:
    Required: [action_object, action_target]
    Actual: ["stuff" (vague), (depends on navigate)]
    Status: INCOMPLETE (stuff too vague)
  
  Overall: INCOMPLETE + MULTI_INTENT
  
  Decision type: MULTI_INTENT_WITH_INCOMPLETE_STEP
  
  Generate clarification:
    type: MULTI_INTENT
    question: "Should I: 1. Navigate to example.com, 2. Extract ____?"
    context: "I see you want to navigate there and extract something"
    options: [
      "Yes, do both (after I know what to extract)",
      "Just navigate first",
      "Just extract (no navigation)"
    ]
    
    Follow-up: "And what should I extract? (e.g., 'product names' like before)"

=== OUTPUT ===

{
  "decision": "INCOMPLETE",
  "intent": "multi_intent",
  "steps": [
    {
      "step": 1,
      "intent": "navigate",
      "confidence": 0.75,
      "status": "READY",
      "action_target": "https://example.com"
    },
    {
      "step": 2,
      "intent": "extract",
      "confidence": 0.40,
      "status": "INCOMPLETE",
      "action_object": null,
      "missing_fields": ["action_object (too vague)"]
    }
  ],
  "clarification": {
    "type": "MULTI_INTENT",
    "question": "I can break this into steps. Should I: 1. Navigate to example.com, 2. Extract product names (like before)?",
    "options": [
      "Yes, do both",
      "Just navigate",
      "Just extract",
      "Let me specify what to extract first"
    ]
  }
}

=== RESULT ===
⚠️ Missions NOT created yet
✅ Multi-step structure clarified
✅ Vague "stuff" identified and flagged
✅ Context applied (recent "product names")
✅ User must confirm: step sequence + what to extract
✅ Only then are missions created in correct order
```

---

## 8. INTEGRATION POINTS

### Where Action Readiness Engine Sits

```
User Message (chat)
        ↓
InteractionOrchestrator.process_message()
        ↓
DeterministicIntentClassifier.classify()  ← CURRENT (will still exist)
        ↓
[NEW] ActionReadinessEngine.validate()    ← NEW LAYER
        │
        ├─ READY
        │  → emit mission_proposal()
        │
        ├─ INCOMPLETE / AMBIGUOUS / QUESTION
        │  → emit clarification_response()
        │
        └─ META (internal intent)
           → route to appropriate handler
        ↓
ResponseEnvelope (to user)
```

### Data Flow

```
ReadinessResult:
{
  decision: "READY" | "INCOMPLETE" | "AMBIGUOUS" | "QUESTION" | "META"
  intent: str
  confidence: float
  confidence_tier: ConfidenceTier
  
  # For READY decisions
  action_object: Optional[str]
  action_target: Optional[str]
  source_url: Optional[str]
  constraints: Dict[str, Any]
  
  # For INCOMPLETE/AMBIGUOUS decisions
  missing_fields: List[str]
  clarification_question: Optional[str]
  clarification_options: List[str]
  
  # Audit
  reasoning: List[str]
  confidence_adjustments: Dict[str, float]
}
```

---

## 9. SUMMARY

### Core Behaviors

1. **Never create a mission that will fail at execution**
   - Pre-validate all required fields
   - Check for vague/generic objects
   - Resolve pronouns from session

2. **Ask targeted clarifications, not generic help**
   - Identify specifically what's missing
   - Offer context-aware options
   - Use session history to infer answers

3. **Support multi-turn conversations**
   - Track recent URLs, domains, extracted data
   - Resolve "there", "it", "them" to recent entities
   - Apply implicit context ("get more" = "get more [of recent type]")

4. **Handle ambiguity gracefully**
   - Detect when intents are equally likely
   - Ask user to choose between them
   - Don't force a decision

5. **Preserve all context**
   - Store URLs in session
   - Track what was extracted
   - Remember mission history
   - Use when filling in user requests

### Success Criteria

✅ "Get stuff" → Clarification, not failed mission  
✅ "Navigate there" → URL resolved from session  
✅ "Extract more" → Context applied (more of what? from where?)  
✅ "Go there and extract" → Sequenced as 2 missions  
✅ "How do I extract?" → Helpful offer to demonstrate, not generic help  

---

**Design ready for implementation.**
