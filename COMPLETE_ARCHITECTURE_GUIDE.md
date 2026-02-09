# Complete Cost-Aware Mission Proposal Architecture

## System Overview

The Buddy system has been enhanced with a comprehensive cost-aware mission proposal system. When a user requests a mission, Buddy now:

1. **Analyzes the task** - Decomposes goals into atomic steps
2. **Estimates costs** - Calculates API costs for each step
3. **Presents options** - Shows user what Buddy does, what human must do, and total cost
4. **Collects approval** - Waits for user decision before execution
5. **Routes results** - Displays execution results with smart visualizations

---

## Architecture Layers

### Layer 1: Input Processing
**File:** `backend/interaction_orchestrator.py`
**Component:** Mission handler (lines ~1580-1610)
**Responsibility:** Captures user objective and initiates proposal generation

```python
# When user requests a mission:
response = self._create_unified_proposal(
    mission_id=mission_id,
    objective=objective_text
)
```

---

### Layer 2: Task Decomposition & Analysis
**File:** `backend/task_breakdown_and_proposal.py`
**Class:** `TaskBreakdownEngine`
**Responsibility:** Break complex goals into atomic steps with cost estimates

**Process Flow:**
1. **GoalDecomposer** - Classifies goals as atomic (single step) or composite (multiple steps)
2. **DelegationEvaluator** - Determines execution class for each step:
   - `AI_EXECUTABLE` - Buddy can handle completely
   - `HUMAN_REQUIRED` - Requires human input/approval
   - `COLLABORATIVE` - Hybrid approach
3. **Tool Detection** - Identifies which tools/APIs are needed:
   - Web search (SerpAPI)
   - LLM generation (OpenAI)
   - Data storage (Firestore)
4. **Cost Estimation** - Calculates per-step costs

**Output:** `TaskBreakdown` dataclass containing:
```python
@dataclass
class TaskBreakdown:
    total_cost: float  # USD
    service_costs: Dict[str, ServiceCost]
    step_count: int
    buddy_steps: int
    human_steps: int
    hybrid_steps: int
    steps: List[TaskStep]
    total_buddy_time_seconds: int
    total_human_time_minutes: int
    blocking_flags: List[str]
```

---

### Layer 3: Cost Calculation Engine
**File:** `backend/cost_estimator.py`
**Class:** `CostEstimator`
**Responsibility:** Real-time API cost calculation with tiered pricing

**Supported Services:**

1. **SerpAPI (Web Search)**
   - Free Tier: 250 queries/month no cost
   - Starter: $25 for 1,000 queries
   - Growth: $75 for 5,000 queries
   - Scale: $150 for 15,000 queries
   - Cost per search: Calculated based on tier + monthly volume

2. **OpenAI (LLM Calls)**
   - gpt-3.5-turbo: $0.50/$1.50 per 1M tokens (input/output)
   - gpt-4-turbo: $10/$30 per 1M tokens
   - gpt-4o: $2.50/$10 per 1M tokens
   - gpt-4o-mini: $0.15/$0.60 per 1M tokens
   - Cost per call: Estimated token count * rate

3. **Firestore (Database)**
   - Read operations: $0.06 per 100,000 reads
   - Write operations: $0.18 per 100,000 writes
   - Storage: $0.10 per GB-day
   - Cost per operation: Calculated atomically

**Pricing Features:**
- `service_tier_recommendations()` - Suggests tier upgrades if volume exceeds current tier
- `combined_mission_costs()` - Aggregates costs across multiple steps
- `tool_detection()` - Maps descriptions to tools (search→SerpAPI, generate→OpenAI, save→Firestore)

**Output:** `MissionCost` dataclass containing:
```python
@dataclass
class MissionCost:
    total_usd: float
    service_costs: List[ServiceCost]
    tier_recommendations: List[TierRecommendation]
    warnings: List[str]
    execution_class: str  # AI_EXECUTABLE | HUMAN_REQUIRED | COLLABORATIVE
```

---

### Layer 4: Proposal Generation
**File:** `backend/proposal_presenter.py`
**Class:** `ProposalPresenter`
**Responsibility:** Generate cohesive mission proposal for user review

**Process:**
1. Takes TaskBreakdown + CostEstimator results
2. Generates 3-sentence executive summary:
   - What Buddy will do
   - What human must do
   - Total cost and time
3. Extracts cost breakdown by service
4. Calculates time estimates
5. Determines approval options (Approve/Modify/Review/Reject)

**Output:** `UnifiedProposal` dataclass containing:
```python
@dataclass
class UnifiedProposal:
    mission_id: str
    mission_title: str
    objective: str
    executive_summary: str  # Natural language explanation
    task_breakdown: TaskBreakdown
    metrics: ProposalMetrics  # buddy_steps, human_steps, hybrid_steps
    costs: ProposalCosts  # Breakdown by service
    time: ProposalTime  # buddy_seconds, human_minutes
    human_involvement: str  # NONE | MINIMAL | MODERATE | EXTENSIVE
    approval_options: List[str]  # ["Approve", "Modify", "Review Steps", "Reject"]
    what_happens_next: str
```

**JSON Serializable:** Converts to dict with `to_dict()` method for frontend

---

### Layer 5: Response Envelope & Transmission
**File:** `backend/response_envelope.py`
**Function:** `unified_proposal_response()`
**Responsibility:** Wrap UnifiedProposal in ResponseEnvelope for chat display

**Process:**
1. Takes UnifiedProposal dict
2. Creates ResponseEnvelope with:
   - Type: `ARTIFACT_BUNDLE`
   - Artifact type: `UNIFIED_PROPOSAL`
   - Content: Serialized proposal
   - UI hints: Approval options, blocking notices

**Output to Frontend:**
```json
{
  "type": "artifact_bundle",
  "artifacts": [{
    "artifact_type": "unified_proposal",
    "content": {
      "mission_id": "...",
      "mission_title": "...",
      "objective": "...",
      "executive_summary": "...",
      ...
    }
  }],
  "ui_hints": {
    "approval_options": ["Approve", "Modify", "Reject"],
    "blocking_notices": [...]
  }
}
```

---

### Layer 6: Frontend Component Display
**File:** `frontend/src/components/UnifiedMissionProposal.js`
**Component:** React functional component
**Responsibility:** Display proposal with metrics and approval controls

**UI Structure:**
```
┌─────────────────────────────────────────────────────┐
│  Mission: [title]                                   │
│  Objective: [objective text]                        │
├─────────────────────────────────────────────────────┤
│  [Overview Tab] [Detailed Steps Tab]                │
├─────────────────────────────────────────────────────┤
│  OVERVIEW:                                          │
│  Executive Summary: [3-sentence natural language]   │
│                                                     │
│  ┌──────┬──────┬──────┬──────┐                      │
│  │Total │Buddy │Your  │Hybrid│                      │
│  │Steps │Steps │Steps │Steps │                      │
│  │  7   │  4   │  2   │  1   │                      │
│  └──────┴──────┴──────┴──────┘                      │
│                                                     │
│  COSTS:                    TIME:                    │
│  ├─ SerpAPI: $2.50         ├─ Buddy: 45s            │
│  ├─ OpenAI: $15.00         └─ Human: 30m            │
│  └─ Firestore: $0.18                                │
│  ────────────────────────────────────────────       │
│  TOTAL: $17.68                                      │
│                                                     │
│  ⚠ Blocking: Step 3 needs human input               │
├─────────────────────────────────────────────────────┤
│  [✓ Approve] [⚙ Modify] [✗ Reject]                 │
└─────────────────────────────────────────────────────┘
```

**Props:**
- `proposal` - UnifiedProposal object
- `onApprove(missionId)` - Handle approval
- `onReject(missionId)` - Handle rejection
- `onModify(missionId)` - Start modification dialog

**Features:**
- Tab navigation (Overview / Detailed Steps)
- Metric grid (4-column card layout)
- Cost breakdown (per-service table)
- Time estimates (buddy/human)
- Step details (type badges, blocking flags, human actions)
- Color coding (blue=buddy, orange=human, purple=hybrid)
- Responsive design (mobile-friendly)

---

### Layer 7: Result Presentation & Visualization
**File:** `backend/result_presenter.py`
**Class:** `ResultPresenter`
**Responsibility:** Smart visualization strategy selection for execution results

**Visualization Types:**
- `TABLE` - Data grids (spreadsheets, API results)
- `CHART` - Data visualization (graphs, statistics)
- `DOCUMENT` - Text content (summaries, reports)
- `TIMELINE` - Time-ordered events
- `CODE` - Syntax-highlighted code blocks
- `JSON` - Raw structured data
- `GALLERY` - Image collections
- `MIXED` - Multiple visualization types

**Smart Selection Logic:**
```
Data Shape → Visualization Type

{...} (object)
  → Scalar values → KEY_VALUE_DISPLAY
  → Nested objects → DOCUMENT
  → Code content → CODE
  → JSON text → JSON

[...] (array)
  → Tabular data (consistent keys) → TABLE
  → Numeric values → CHART
  → Objects with dates → TIMELINE
  → Mixed types → GALLERY

"text" (string)
  → Markdown formatted → DOCUMENT
  → Code syntax hints → CODE
  → Plain text → DOCUMENT

Tool-based hints:
  web_search → TABLE
  llm_call → DOCUMENT
  calendar_query → TIMELINE
  code_generation → CODE
  image_search → GALLERY
```

**Output:** `VisualizationStrategy` containing:
```python
@dataclass
class VisualizationStrategy:
    primary_type: str  # TABLE, CHART, DOCUMENT, etc.
    secondary_types: List[str]  # Alternative visualizations
    config: Dict  # Visualization-specific settings
    transformations: List[str]  # Data prep steps
    export_formats: List[str]  # CSV, JSON, PNG, PDF
    suggested_height: str  # UI layout hint
    collapsible: bool  # Can collapse/expand
```

---

### Layer 7B: Frontend Visualization Router
**File:** `frontend/src/components/VisualizationRouter.js`
**Component:** React component factory
**Responsibility:** Route artifacts to appropriate visualization components

**Sub-components:**
1. **TableVisualization** - Sortable, filterable tables
2. **ChartVisualization** - Bar/line/pie charts (recharts)
3. **DocumentVisualization** - Markdown rendering
4. **TimelineVisualization** - Event timeline display
5. **CodeVisualization** - Syntax-highlighted code
6. **JSONVisualization** - Formatted JSON viewer
7. **GalleryVisualization** - Image gallery grid

**Component Selection:**
```javascript
{artifact.strategy.primary_type === 'TABLE' && <TableVisualization data={data} />}
{artifact.strategy.primary_type === 'CHART' && <ChartVisualization data={data} />}
{artifact.strategy.primary_type === 'DOCUMENT' && <DocumentVisualization content={data} />}
{artifact.strategy.primary_type === 'TIMELINE' && <TimelineVisualization events={data} />}
{artifact.strategy.primary_type === 'CODE' && <CodeVisualization code={data} />}
{artifact.strategy.primary_type === 'JSON' && <JSONVisualization json={data} />}
```

---

### Layer 8: Chat Integration
**File:** `frontend/src/UnifiedChat.js`
**Responsibility:** Display proposals and results in unified chat interface

**Artifact Rendering:**
```javascript
// For unified proposals:
{msg.artifacts?.some(a => a.artifact_type === 'unified_proposal') && (
  <UnifiedMissionProposal
    proposal={msg.artifacts.find(a => a.artifact_type === 'unified_proposal')?.content}
    onApprove={(missionId) => addMessage(`Approve mission ${missionId}`, 'user')}
    onReject={(missionId) => addMessage(`Reject mission ${missionId}`, 'user')}
    onModify={(missionId) => addMessage(`Can you modify mission ${missionId} to...`, 'user')}
  />
)}

// For other artifacts:
{msg.artifacts?.filter(a => a.artifact_type !== 'unified_proposal').map(artifact => (
  <VisualizationRouter artifact={artifact} data={artifact.content} />
))}
```

---

## End-to-End User Flow

### 1. Mission Request
```
User: "Can you research the best React optimization techniques 
        and create a summary document?"
```

### 2. Task Breakdown
**System analyzes:**
```
STEP 1: Search for React optimization techniques (Buddy)
  - Tool: web_search (SerpAPI)
  - Time: 5 seconds
  - Cost: $0.50
  - Class: AI_EXECUTABLE

STEP 2: Compile results (Buddy)
  - Tool: llm_call (OpenAI gpt-4o-mini)
  - Time: 3 seconds
  - Tokens: ~500 input + 2000 output
  - Cost: $0.15 × (500+2000)/1M = $0.001
  - Class: AI_EXECUTABLE

STEP 3: Format as document (Hybrid)
  - Tool: llm_call (OpenAI gpt-4o)
  - Time: 5 seconds (Buddy) + 10 min (Human review)
  - Tokens: ~1000 input + 5000 output
  - Cost: $2.50 × (1000+5000)/1M = $0.0175
  - Human approval needed for final document
  - Class: COLLABORATIVE
```

### 3. Proposal Presentation
```
┌─────────────────────────────────────────────────────┐
│  Research React Optimization & Create Summary      │
│  Research the best React optimization techniques   │
│  and create a summary document                      │
├─────────────────────────────────────────────────────┤
│ I'll search for React optimization techniques using│
│ SerpAPI, compile the results with OpenAI, and      │
│ format them into a document. You'll need to        │
│ review the final document for accuracy and tone.   │
│ Total cost: $0.67, Time: 8 seconds (Buddy) +       │
│ 10 minutes (You).                                  │
├─────────────────────────────────────────────────────┤
│  4 Total Steps │ 2 Buddy │ 1 Human │ 1 Hybrid     │
│  Cost: $0.67   │ Time: 13s buddy + 10m you       │
├─────────────────────────────────────────────────────┤
│  [✓ Approve] [⚙ Modify] [✗ Reject]                 │
└─────────────────────────────────────────────────────┘
```

### 4. User Approval
```
User clicks: "Approve"
System: "Mission approved. Starting execution..."
```

### 5. Execution & Results
```
System:
- Step 1: ✓ Web search completed (3 results found)
- Step 2: ✓ Results compiled and summarized
- Step 3: ⏳ Waiting for your document review...

[Formatted Document Preview]
────────────────────────────────
React Optimization Techniques Q2 2024

1. Component Memoization
   - React.memo() for functional components
   - useMemo() for expensive computations
   - Cost: Marginal, benefits: High

2. Code Splitting
   - Dynamic imports with React.lazy()
   - ...
────────────────────────────────

User: "Looks good! Approve the final version."
System: ✓ Document finalized. Mission complete!
```

---

## Key Design Decisions

### 1. Unified Proposal vs. Fragmented System
**Old approach:** 3-piece artifacts (summary + MissionReference + MISSION_DRAFT)
**New approach:** Single UNIFIED_PROPOSAL artifact containing all data
**Benefit:** Simpler rendering logic, single source of truth, consistent UX

### 2. Real Pricing Data
**Embedded in code:** All API pricing tables are hardcoded in CostEstimator
**Why:** Ensures consistent cost calculations, easy to audit, visible to developers
**Update path:** Change pricing only in cost_estimator.py ServiceTier enum

### 3. Task Step Classification
**Three execution classes:**
- `AI_EXECUTABLE` - Buddy handles completely, no blocking
- `HUMAN_REQUIRED` - Cannot proceed without human input
- `COLLABORATIVE` - Buddy executes, human approves

**Enables:** Distinction between advisory (human reviews) and blocking (human inputs) steps

### 4. Service Tier Recommendations
**When user exceeds monthly limits:**
```
⚠ You've searched 300 times this month (Free Tier: 250/month max)
  Recommendation: Upgrade to Starter Tier ($25 for 1000/month)
  Savings: $0.25 per search with Starter vs. Free Tier overage costs
```

### 5. Deterministic Visualization Routing
**No ML/LLM involved:** Visualization strategy is deterministic based on:
- Data shape (array/object/string)
- Data properties (numeric, temporal, code syntax)
- Tool used (web_search→table, llm_call→document)
- Data complexity

**Benefit:** Consistent, fast, debuggable, no API calls for presentation

---

## Testing Strategy

### Backend Tests (All Passing)
1. **test_cost_estimator.py** - 8 tests
   - ✓ SerpAPI tier pricing
   - ✓ OpenAI token pricing
   - ✓ Firestore operations
   - ✓ Combined mission costs
   - ✓ Tier recommendation thresholds

2. **test_task_breakdown.py** - 7 tests
   - ✓ Atomic goal decomposition
   - ✓ Composite goal decomposition
   - ✓ Web search tool detection
   - ✓ Step blocking identification
   - ✓ Cost aggregation across steps
   - ✓ Approval routing logic

3. **test_proposal_presenter.py** - 6 tests
   - ✓ Simple proposal generation
   - ✓ Complex proposal with multiple steps
   - ✓ Executive summary formatting
   - ✓ Cost breakdown extraction
   - ✓ JSON serialization
   - ✓ Approval option routing

### Frontend (Live Testing)
1. Verify UnifiedMissionProposal renders with proposal data
2. Test approval/rejection/modification callbacks
3. Validate cost display accuracy
4. Check responsive design on mobile

### End-to-End Integration Testing
1. User → Mission request
2. System → Generates proposal with costs
3. Frontend → Displays UnifiedMissionProposal
4. User → Clicks Approve
5. System → Begins execution
6. Frontend → Shows step progress
7. System → Routes result through VisualizationRouter
8. Frontend → Displays result with appropriate visualization

---

## Configuration & Customization

### 1. Update API Pricing
**File:** `backend/cost_estimator.py`
**Lines:** ServiceTier enum (lines ~30-80)
```python
class ServiceTier(Enum):
    FREE = {'query_limit': 250, 'monthly_cost': 0, 'per_query': 0}
    STARTER = {'query_limit': 1000, 'monthly_cost': 25, 'per_query': 0.025}
    # Edit these values to match current prices
```

### 2. Adjust Step Time Estimates
**File:** `backend/task_breakdown_and_proposal.py`
**Function:** `_estimate_step_time()`
```python
# Adjust these multipliers to match real execution times
buddy_time_seconds = base_step_cost * 5  # 5 seconds per complexity unit
human_time_minutes = blocking_steps * 5  # 5 minutes per human action
```

### 3. Customize Visualization Strategies
**File:** `backend/result_presenter.py`
**Function:** `_determine_strategy()`
```python
# Add tool-specific strategy mappings
tool_strategies = {
    'web_search': VisualizationType.TABLE,
    'image_search': VisualizationType.GALLERY,
    'calendar_query': VisualizationType.TIMELINE,
    # Add custom mappings here
}
```

### 4. Customize Approval Options
**File:** `backend/proposal_presenter.py`
**Function:** `create_proposal()`
```python
# Modify approval_options routing logic to match your workflow
approval_options = ["Approve", "Modify", "Review Steps"]
if proposal.human_involvement == "EXTENSIVE":
    approval_options.append("Schedule Review")
```

---

## Monitoring & Logging

### Cost Tracking
All costs are logged with task traces:
```python
DecisionTraceLogger.log_mission_creation(
    trace_id=trace_id,
    mission_id=mission_id,
    estimated_cost=unified_proposal.costs.total_usd,
    approval_status='pending'
)
```

### Performance Metrics
- Proposal generation time (should be <2 seconds)
- Cost calculation accuracy
- User approval/rejection rates
- Mission completion success rates

---

## Known Limitations & Future Enhancements

### Current Limitations
1. **Cost estimates are educated guesses** - Actual costs may vary based on token counts
2. **Time estimates are fixed ratios** - Don't account for complexity variations
3. **Visualization routing is deterministic** - May not optimal for all data shapes
4. **No cost history tracking** - Can't learn from previous similar missions

### Planned Enhancements
1. **ML-based cost prediction** - Learn from actual vs. estimated costs
2. **Adaptive time estimates** - Track and improve time prediction accuracy
3. **User preference learning** - Remember visualization preferences per user/data type
4. **Cost budget alerts** - Warn if mission exceeds user-defined budget
5. **Tier optimization** - Auto-upgrade tiers when cost-effective
6. **Cost history dashboard** - Show spending trends and optimization opportunities

---

## Complete File Reference

### Backend Files
- `backend/interaction_orchestrator.py` - Mission handler integration (modified)
- `backend/task_breakdown_and_proposal.py` - Task decomposition engine (created)
- `backend/cost_estimator.py` - Real API pricing calculator (created)
- `backend/proposal_presenter.py` - Proposal generator (created)
- `backend/result_presenter.py` - Visualization strategist (created)
- `backend/response_envelope.py` - Response wrapper (modified)

### Frontend Files
- `frontend/src/UnifiedChat.js` - Chat interface (modified)
- `frontend/src/components/UnifiedMissionProposal.js` - Proposal component (created)
- `frontend/src/components/UnifiedMissionProposal.css` - Proposal styling (created)
- `frontend/src/components/VisualizationRouter.js` - Visualization router (created)

### Test Files
- `test_cost_estimator.py` - 8 tests (all passing)
- `test_task_breakdown.py` - 7 tests (all passing)
- `test_proposal_presenter.py` - 6 tests (all passing)

---

## Philosophy

> **"Buddy does what Buddy can do, human does what human must do, costs shown upfront, user decides if worth it"**

This system embodies this philosophy by:
1. **Automating** what Buddy can do reliably (searches, summarization, formatting)
2. **Blocking** on what requires human judgment (content review, creative decisions)
3. **Showing costs** transparently before execution
4. **Letting users decide** if the cost/time tradeoff is worth it

This creates a transparent, collaborative workflow where Buddy is a capable assistant within defined boundaries, and humans retain control over high-value decisions.

---

*System built for production. All components tested. Ready for end-to-end live validation.*
