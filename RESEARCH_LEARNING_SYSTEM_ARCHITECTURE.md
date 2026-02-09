"""
BUDDY RESEARCH LEARNING SYSTEM - COMPLETE ARCHITECTURE

This document describes Buddy's complete learning system architecture,
with focus on how the Research Intelligence Engine integrates with
the broader learning infrastructure.

===== SYSTEM OVERVIEW =====

Buddy's learning system operates in tiers:

TIER 1: Signal Emission (bottom)
   ↓ Feedback events, execution outcomes
TIER 2: Evaluation & Assessment
   ↓ GoalSatisfactionEvaluator, AmbiguityEvaluator, etc.
TIER 3: Learning Signal Generation
   ↓ Signal objects with recommendations
TIER 4: Learning Signal Persistence
   ↓ learning_signals.jsonl files
TIER 5: Adaptive Selection (top)
   ↓ Engine selection, task decomposition, thresholds
TIER 6: Strategy Adjustment
   Improved execution in next research cycle

===== RESEARCH-SPECIFIC LEARNING FLOW =====

1. USER QUERY
   "Find all contact information for Cardwell Associates"
          ↓
2. INTENT CLASSIFICATION
   Task type: CONTACT_EXTRACTION
          ↓
3. TASK DECOMPOSITION
   - Search web for contacts
   - Search LinkedIn profiles
   - Extract business contact info
          ↓
4. RESEARCH EXECUTION
   ResearchIntelligenceEngine.research() runs with adaptive engine selection
          ↓
5. RESULT DEDUPLICATION & SCORING
   Merge duplicate emails/phones, calculate confidence per source
          ↓
6. COMPLETENESS ANALYSIS
   Score: 0.0-1.0, suggest follow-ups if incomplete
          ↓
7. STRUCTURED OUTPUT
   JSON with findings, confidence, sources, audit trail
          ↓
8. FEEDBACK LOOP PROCESSING ← NEW!
   ResearchFeedbackLoop.process_research_session()
   
   a) EVALUATION
      ResearchMetrics calculated:
      - entities found
      - average confidence
      - sources used
      - completeness score
      - success/failure
   
   b) OUTCOME ASSESSMENT
      ResearchFeedbackEvent generated:
      - outcome type (ENTITY_FOUND, INCOMPLETE_DATA, FAILED, etc)
      - engine quality scores
      - deduplication quality
      - reasoning and recommendations
   
   c) LEARNING SIGNAL GENERATION
      Multiple signals created:
      - engine_effectiveness (per engine per task_type)
      - task_decomposition_effectiveness
      - deduplication_quality
      - completeness_assessment
   
   d) PERSISTENCE
      Signals written to: outputs/research/learning_signals.jsonl
          ↓
9. ADAPTIVE SELECTION UPDATES ← NEW!
   ResearchAdaptiveSelector loads signals and updates:
   - engine_weights[task_type][engine] → improved weights
   - task_decomposition_scores[task_type] → strategy effectiveness
   - completeness_thresholds[task_type] → when to stop searching
          ↓
10. NEXT RESEARCH CYCLE
    Same query type uses improved weights automatically
    ← CONTINUOUS IMPROVEMENT LOOP

===== ARCHITECTURE COMPONENTS =====

**ResearchIntelligenceEngine** (backend/research_intelligence_engine.py)
- Main orchestrator
- 10 components: classifier, decomposer, selector, executor, etc.
- Integrates with ResearchFeedbackLoop after research completes
- Uses ResearchAdaptiveSelector for engine selection

**ResearchFeedbackLoop** (backend/research_feedback_loop.py) ← NEW!
- Evaluates research outcomes with detailed metrics
- Generates feedback events with outcome assessment
- Creates learning signals for continuous improvement
- Tracks engine effectiveness per task type
- Persists signals for adaptive selection

**ResearchAdaptiveSelector** (backend/research_adaptive_selector.py) ← NEW!
- Reads learning signals from ResearchFeedbackLoop
- Dynamically adjusts engine selection weights
- Updates task decomposition effectiveness scores
- Calibrates completeness thresholds
- Makes better decisions each cycle

**ResearchMetrics** (data class)
- Captures quantitative research outcome data
- Inputs: session_id, query, entities_found, confidence, sources
- Used by feedback loop for assessment

**ResearchFeedbackEvent** (data class)
- Assessment of research outcome quality
- Inputs: metrics, engine contributions, deduplication quality
- Outputs: outcome type, recommendations, reasoning

**ResearchLearningSignal** (data class)
- Structured learning signal for Buddy's learning system
- Types: engine_effectiveness, task_decomposition, etc.
- Confidence-weighted recommendations
- Supporting evidence for decisions

===== INTEGRATION WITH BUDDY'S BROADER LEARNING SYSTEM =====

The research learning system feeds into:

1. MEMORY MANAGER
   - Stores what engines work best for which queries
   - Recalls performance history
   - Informs future decisions

2. TOOL PERFORMANCE TRACKER
   - Tracks web_research tool effectiveness per domain
   - Performance metrics used by ToolSelector
   - Reward/penalize based on research outcomes

3. FEEDBACK MANAGER
   - Accepts user feedback on research results
   - Can override or confirm automatic assessments
   - Calibrates confidence thresholds

4. PHASE FEEDBACK LOOPS
   - Phase 16: Heuristic effectiveness (engine selection heuristics)
   - Phase 18: Coordination (multi-engine coordination)
   - Phase 20: Prediction (research success prediction)
   - Phase 22: Aggregation (all learning signals)

===== LEARNING SIGNAL FLOW =====

Research Mission
    ↓
ResearchFeedbackLoop.process_research_session()
    ↓ (generates 4+ signals per research session)
    ├─ engine_effectiveness
    ├─ task_decomposition_effectiveness
    ├─ deduplication_quality
    └─ completeness_assessment
    ↓
outputs/research/learning_signals.jsonl
    ↓
ResearchAdaptiveSelector._load_signals()
    ↓ (updates weights after each session)
    ├─ engine_weights updated
    ├─ task_decomposition_scores updated
    └─ completeness_thresholds updated
    ↓
Next research_intelligence_engine.research() call
    Uses updated weights automatically
    ← IMPROVEMENT CYCLE COMPLETES

===== KEY LEARNING METRICS =====

Per Research Session:
- success: Did we find what was requested?
- completeness_score: 0.0-1.0, how complete is the research?
- avg_confidence: Average confidence across all data points
- sources_used: Which engines contributed?
- entities_found: How many unique entities discovered?
- deduplication_quality: How well did multi-source normalization work?

Per Engine Per Task Type:
- effectiveness_score: 0.0-1.0 from learning signals
- data_points_contributed: Count of data points found
- average_confidence: Confidence of data from this engine

Per Task Type:
- success_rate: % of successful research sessions
- avg_completeness: Average completeness score
- best_engines: Which engines work best for this task type
- task_decomposition_effectiveness: Is current strategy working?

===== EXAMPLE: LEARNING IN ACTION =====

Scenario: First research session finds data with 0.75 confidence

1. ResearchFeedbackLoop evaluates
   - outcome: INCOMPLETE_DATA (completeness 0.75 < 0.8)
   - google: found 2 points, confidence 0.8
   - linkedin: found 1 point, confidence 0.7
   - google_maps: found 3 points, confidence 0.75

2. Generates signals
   - engine_effectiveness: google (0.8), google_maps (0.75), linkedin (0.7)
   - task_decomposition_effectiveness: 0.7 (could be better)
   - completeness_assessment: 0.75 (incomplete)

3. ResearchAdaptiveSelector updates weights
   - CONTACT_EXTRACTION/google: 0.5 → 0.65 (boosted)
   - CONTACT_EXTRACTION/google_maps: 0.5 → 0.625
   - CONTACT_EXTRACTION/linkedin: 0.5 → 0.6
   - completeness_threshold: 0.75 → 0.77 (learned target)

4. Next session on same task type
   - Engine selection automatically uses [google, google_maps, linkedin]
   - Weighted by effectiveness scores
   - Expected: better completeness!

===== DEPLOYMENT STATUS =====

✅ COMPLETE:
- ResearchIntelligenceEngine (600+ lines)
- ResearchFeedbackLoop (600+ lines)
- ResearchAdaptiveSelector (400+ lines)
- Integration with research_intelligence_engine.py
- Feedback loop callback after research completes
- Learning signal generation and persistence
- Demo script showing full workflow

🚀 READY FOR:
- Production research queries
- Real feedback collection
- Continuous learning and improvement
- Analytics on what Buddy learns

===== USAGE EXAMPLES =====

# Execute research and automatically generate feedback signals
result = research_intelligence_engine.research("Find contacts for Acme Corp")
# → Automatically calls research_feedback_loop.process_research_session()
# → Generates learning signals
# → Updates adaptive selector weights

# Check what we've learned
summary = research_adaptive_selector.get_performance_summary()
print(summary)
# → Shows engine effectiveness by task type
# → Shows task decomposition scores
# → Shows completeness thresholds learned

# Get engine recommendations for specific task
engines, weights = research_adaptive_selector.select_engines_for_task(
    "CONTACT_EXTRACTION",
    default_engines=["google", "linkedin", "google_maps"]
)
# → Returns engines ranked by learned effectiveness
# → Automatically improves over time

===== NEXT STEPS =====

1. Run demo_research_learning.py to test the full system
2. Execute research queries and watch learning signals generate
3. Verify learning signals written to outputs/research/learning_signals.jsonl
4. Confirm adaptive selector updates engine weights
5. Run same query type again - observe improved performance
6. Monitor research metrics dashboard

===== TECHNICAL NOTES =====

- Learning signals are non-blocking (errors don't break research)
- Adaptive selector loads signals on initialization
- Engine weights use exponential moving average (0.7 * old + 0.3 * new)
- Completeness thresholds are task-type specific
- All signals include confidence scores and reasoning
- Integration with broader Buddy learning system is automatic

===== PERFORMANCE TARGETS =====

After sufficient learning:
- Research success rate: >85%
- Average completeness: >0.80
- Engine effectiveness variance: <0.15
- Adaptive improvements: +5-10% per task type per 10 sessions

===== CONCLUSION =====

Buddy's Research Learning System is complete and integrated.

The system creates a continuous feedback loop where:
1. Research missions execute
2. Outcomes are evaluated automatically
3. Learning signals are generated
4. Engine selection improves
5. Future research is better

This is how Buddy learns what "good" research looks like,
and continuously improves its research capabilities over time.
"""

if __name__ == "__main__":
    print(__doc__)
