# Phase 8: Scoring Rubric
## Economic Tradeoff Reasoning

**Purpose**: Deterministic, heuristic-based scoring model for evaluating whether work is worth doing.

**No Learning**: Uses fixed constants and multipliers. Completely deterministic.

**No Autonomy**: Advisory only. Suggests decisions but never enforces them.

---

## Core Scoring Formula

$$\text{Final Value} = \text{ROI} \times M_{\text{cognitive}} \times M_{\text{value}} \times M_{\text{urgency}}$$

### Components

#### 1. ROI Ratio (Base Score)
$$\text{ROI} = \frac{\text{Payoff (minutes)}}{\text{Cost (minutes)}}$$

**Interpretation**:
- ROI > 2.0: Strong return on investment
- ROI = 1.0: Break-even
- ROI < 1.0: Negative return

**Examples**:
- Payoff 100 min, Cost 50 min → ROI = 2.0x
- Payoff 30 min, Cost 60 min → ROI = 0.5x

---

#### 2. Cognitive Load Multiplier
Represents mental/emotional friction to completing work.

| Load Level | Multiplier | Impact | Notes |
|-----------|-----------|--------|-------|
| LOW       | 0.8x      | Boosts value | Routine, familiar work |
| MEDIUM    | 1.0x      | Neutral | Moderate complexity |
| HIGH      | 1.5x      | Penalizes | Demanding, stressful |
| CRITICAL  | 3.0x      | Heavy penalty | Exhausting, risky |

**Interpretation**: Higher multiplier = harder to justify doing the work.

**Decision Rule**: If cognitive load is CRITICAL, nearly automatic REJECT regardless of ROI.

---

#### 3. Value Type Multiplier
Represents compounding benefits over time.

| Value Type | Multiplier | Impact | Notes |
|-----------|-----------|--------|-------|
| ONE_TIME  | 1.0x      | Single benefit | No ongoing value |
| REUSABLE  | 1.5x      | Boosts value | Can be applied multiple times |
| COMPOUNDING | 2.0x    | Major boost | Grows over time, blocks future friction |

**Interpretation**: Work that pays dividends repeatedly gets higher priority.

**Examples**:
- ONE_TIME: Fixing a one-off bug
- REUSABLE: Building a template
- COMPOUNDING: Writing documentation that prevents future questions

---

#### 4. Urgency Multiplier
Represents deadline pressure and time sensitivity.

| Urgency | Multiplier | Decision Impact | Notes |
|---------|-----------|-----------------|-------|
| low     | 0.7x      | Can defer | No immediate deadline |
| normal  | 1.0x      | Neutral | Standard deadline |
| high    | 1.2x      | Elevates score | Pressing but not critical |
| critical | 1.5x     | High priority | Blocking other work |

**Interpretation**: Urgent work is prioritized, but only if underlying ROI supports it.

---

## Decision Thresholds

$$\text{Decision} = \begin{cases}
\text{PROCEED} & \text{if } \text{Final Value} \geq 1.5 \\
\text{PAUSE} & \text{if } 0.5 \leq \text{Final Value} < 1.5 \\
\text{REJECT} & \text{if } \text{Final Value} < 0.5 \text{ OR Load} = \text{CRITICAL}
\end{cases}$$

### Decision Categories

#### PROCEED
- **Threshold**: Final Value ≥ 1.5
- **Meaning**: Worth doing now
- **Cognitive**: Go ahead, value justifies effort

#### PAUSE
- **Threshold**: 0.5 ≤ Final Value < 1.5
- **Meaning**: Borderline; consider deferring
- **Cognitive**: Marginal value; revisit when priorities are clearer or context changes

#### REJECT
- **Threshold**: Final Value < 0.5 OR Cognitive Load = CRITICAL
- **Meaning**: Not worth doing under current conditions
- **Cognitive**: Skip this unless context radically changes

---

## Opportunity Cost Score

$$\text{Opp Cost} = \frac{\text{Time Used}}{\text{Available Time}}$$

**Range**: 0.0 to 1.0

**Interpretation**:
- 0.0: Negligible time commitment
- 0.5: Uses 50% of available time
- 1.0: Uses all available time (not recommended)

**Usage**: Helps understand calendar pressure impact on decisions.

---

## Confidence Score

**Range**: 0.4 to 0.95

**Calculation**: Based on:
- ROI distance from decision boundaries
- Effort estimate uncertainty
- Payoff estimate clarity

**Interpretation**:
- 0.95: Very clear decision (ROI far from boundary)
- 0.70: Reasonable confidence
- 0.40: Borderline decision (ROI near boundary, high uncertainty)

**Usage**: Indicates when human review is important.

---

## Scoring Examples

### Example 1: Quick Win (PROCEED)

**Input**:
- Name: "Fix typo in docs"
- Time Cost: 15 minutes
- Payoff: 60 minutes (prevents 3 support questions × 20 min each)
- Cognitive Load: LOW
- Value Type: REUSABLE (helps multiple users)
- Urgency: normal
- Available Time: 120 minutes

**Calculation**:
1. ROI = 60 / 15 = 4.0x
2. Cognitive Multiplier (LOW) = 0.8x
3. Value Type Multiplier (REUSABLE) = 1.5x
4. Urgency Multiplier (normal) = 1.0x
5. Final Value = 4.0 × 0.8 × 1.5 × 1.0 = **4.8x**
6. Opp Cost = 15 / 120 = 12.5%
7. Decision: **PROCEED** (4.8 ≥ 1.5) ✓

---

### Example 2: Marginal Work (PAUSE)

**Input**:
- Name: "Refactor utilities module"
- Time Cost: 120 minutes
- Payoff: 180 minutes (future debugging prevented)
- Cognitive Load: HIGH
- Value Type: COMPOUNDING (prevents future issues)
- Urgency: low
- Available Time: 300 minutes

**Calculation**:
1. ROI = 180 / 120 = 1.5x
2. Cognitive Multiplier (HIGH) = 1.5x
3. Value Type Multiplier (COMPOUNDING) = 2.0x
4. Urgency Multiplier (low) = 0.7x
5. Final Value = 1.5 × 1.5 × 2.0 × 0.7 = **3.15x**
6. Opp Cost = 120 / 300 = 40%
7. Decision: **PROCEED** (3.15 ≥ 1.5) ✓

*Note: High cognitive load penalizes, but compounding value + urgency still justify.*

---

### Example 3: Not Worth It (REJECT)

**Input**:
- Name: "Polish obscure feature"
- Time Cost: 180 minutes
- Payoff: 45 minutes (rarely used feature)
- Cognitive Load: HIGH
- Value Type: ONE_TIME
- Urgency: low
- Available Time: 240 minutes

**Calculation**:
1. ROI = 45 / 180 = 0.25x
2. Cognitive Multiplier (HIGH) = 1.5x
3. Value Type Multiplier (ONE_TIME) = 1.0x
4. Urgency Multiplier (low) = 0.7x
5. Final Value = 0.25 × 1.5 × 1.0 × 0.7 = **0.26x**
6. Opp Cost = 180 / 240 = 75%
7. Decision: **REJECT** (0.26 < 0.5) ✗

---

### Example 4: Critical Load Override (REJECT)

**Input**:
- Name: "Implement complex algorithm"
- Time Cost: 60 minutes
- Payoff: 240 minutes (if it works)
- Cognitive Load: **CRITICAL** ← Key issue
- Value Type: COMPOUNDING
- Urgency: high

**Calculation**:
1. ROI = 240 / 60 = 4.0x (excellent on paper)
2. Cognitive Multiplier (CRITICAL) = 3.0x ← PENALTY
3. Value Type Multiplier (COMPOUNDING) = 2.0x
4. Urgency Multiplier (high) = 1.2x
5. Final Value = 4.0 × 3.0 × 2.0 × 1.2 = **28.8x**
6. **BUT**: Cognitive Load = CRITICAL → **Auto-REJECT override**
7. Decision: **REJECT** (or PAUSE at best)

*Rationale*: High ROI can't overcome critical cognitive burden. Doing this work when burned out is too risky.

---

## Constraints & Safety

### Design Constraints
- ✓ **No Autonomy**: Advisor only, never executes
- ✓ **No Learning Loops**: Fixed multipliers, fully deterministic
- ✓ **No Mission Killing**: Advisory suggestions, user can override
- ✓ **No External APIs**: Pure heuristic model, offline-capable
- ✓ **No Side Effects**: Read-only analysis, immutable results

### Thread Safety
- All multipliers are constants (no state)
- TradeoffScore is frozen (immutable)
- Signals are append-only JSONL (no mutations)

### Determinism Guarantee
- Same input → Same output (100% reproducible)
- No randomization anywhere
- No dependency on execution order or timing

---

## Integration Points

### Input Sources
- Human estimation (time, payoff, load)
- Work priority classification (urgency)
- Context flags (cognitive load, value type)

### Output Destinations
- Whiteboard economic panel (visualization)
- Signal stream (JSONL logging)
- Delegation layer (Phase 7 integration)
- Operator controls (future Phase 9)

---

## FAQ

**Q: Why is cognitive load multiplied instead of added?**  
A: Multiplicative penalty better represents "this is too hard to justify" rather than incremental friction. HIGH load can override even good ROI.

**Q: What if cognitive load is CRITICAL but ROI is 10x?**  
A: CRITICAL → auto-reject or heavy PAUSE. The model says "you're too exhausted to do this well, even if it's valuable."

**Q: Can a user override REJECT decisions?**  
A: Yes. This is advisory only. The panel explains reasoning; user decides.

**Q: How do I change multipliers?**  
A: Edit `TradeoffScoringRubric` constants in `tradeoff_evaluator.py`. All scores recalculate automatically.

**Q: Why is COMPOUNDING 2.0x but ONE_TIME 1.0x?**  
A: Compounding work builds momentum and reduces future friction. That's worth double weight in priority.

---

## Reference

**Files**:
- Implementation: `backend/tradeoff_evaluator.py`
- Signals: `backend/tradeoff_signal_emitter.py`
- UI: `backend/tradeoff_whiteboard_panel.py`
- Tests: `backend/test_phase8_tradeoff.py`

**Related**:
- Phase 7: Delegation & Handoff Intelligence
- Phase 6: Cognition Layer (Reality Reasoner)
- Phase 9: Operator Controls (future)
