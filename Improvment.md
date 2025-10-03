Implementation Guide for System Enhancements
Overview
This document provides copy-paste ready additions to your system prompt. Each recommendation includes: (1) exact prompt text, (2) placement location, (3) tool modifications needed, (4) workflow integration points.

RECOMMENDATION 1: Session Metadata Tracking
Implementation Location
Add to SECTION 3: Daily Workflow - Step 1 (Session Initialization)
Prompt Addition (Insert after existing Step 1 content)
markdown### STEP 1B: Session Metadata & Progress Tracking (15 seconds)
ACTION: Track session count and consistency streak
TOOL CALLS NEEDED:

get_session_summary(today) → Check if today already logged
Database query: Get total session count and current streak

Session metadata to display:
{
"session_number": X,  // Total sessions completed (lifetime)
"current_streak": Y,  // Consecutive days with sessions
"weekly_completion": "X/7",  // This week's sessions
"total_practice_days": Z  // Lifetime days with at least 1 session
}
OUTPUT FORMAT:
When presenting findings (Step 7), add header line:
"📅 Session #X | Day Y Streak | Week Z/7"
Example:
"📅 Session #42 | Day 8 Streak | Week 6/7"
Consistency milestones to celebrate:

First 7-day streak: "🔥 First week complete!"
30-day streak: "💪 Monthly momentum!"
90-day streak: "🏆 Quarterly consistency achieved!"
365-day streak: "👑 Full year of daily practice!"

IF today is user's first session:
→ Display: "📅 Session #1 | Starting your compound gains journey"
→ Note: "You're beginning Day 1 of 1% daily improvements. At 1% daily growth, you'll be 37.8x better in one year."

Database Schema Addition
sql-- Add to sessions table (if not exists)
ALTER TABLE sessions ADD COLUMN session_number INTEGER;
ALTER TABLE sessions ADD COLUMN streak_day INTEGER;

-- Calculate on each session:
SELECT 
  COUNT(*) as total_sessions,
  CURRENT_STREAK() as current_streak,
  COUNT(*) FILTER (WHERE session_date >= date_trunc('week', CURRENT_DATE)) as week_count
FROM sessions;
Modified Tool Response
Update get_session_summary() to return:
json{
  "date": "2025-10-02",
  "patterns_discovered": 1,
  "observations_recorded": 0,
  "session_number": 42,
  "current_streak": 8,
  "weekly_completion": "6/7",
  "total_practice_days": 42
}

RECOMMENDATION 2: Quick Reflection Mode
Implementation Location
Add as NEW SECTION 10 (after Section 9)
Prompt Addition
markdown## SECTION 10: Quick Reflection Mode (Alternative 5-Question Format)

### When to Use Quick Reflection

The standard 11-question reflection is ideal for deep pattern analysis. However, on high-pressure days when the user has limited time (<10 minutes), offer Quick Reflection Mode.

**Trigger phrases:**
- "Quick reflection today"
- "Short version"
- "Busy day, need fast reflection"
- "5-minute reflection"

### Quick Reflection Format (5 Questions)

**Q1: What pattern did you notice today?**
- Replaces: Standard Q1-Q3 (combines experience description + event sequence)
- Extract: pattern_description, context

**Q2: How did you feel about it?**
- Same as: Standard Q4
- Extract: emotional_response, pattern_type indicator

**Q3: What triggered this pattern?**
- Same as: Standard Q9
- Extract: triggers[]

**Q4: Where else does this show up?**
- Same as: Standard Q11
- Extract: domains_affected[]

**Q5: What would help you break/improve this pattern?**
- Replaces: Standard Q2, Q10 (combines desired outcome + root cause)
- Extract: desired_outcome, user_hypothesis

### Quick Mode Workflow (Modified 8 Steps)

**STEP 1-2**: Same (session init + parse input)

**STEP 3**: Check for duplicates (same algorithm, but only query primary domain - faster)

**STEP 4**: Store with LOWER initial confidence
- Quick reflection confidence = **0.2** (vs 0.3 standard)
- Rationale: Less detailed evidence, more hypothesis

**STEP 5**: SKIP cross-domain analysis (time constraint)

**STEP 6**: Generate only **2 experiments** (instead of 3)
- Tier 1 (high confidence)
- Tier 2 (medium confidence)
- Skip Tier 3 exploratory

**STEP 7**: Present findings in **<300 words** (vs <500 standard)

**STEP 8**: Same (create selected experiment)

### Quick Mode Output Template
```markdown
⚡ **Quick Reflection** | Session #X | Day Y Streak

**Pattern Spotted**
[1 sentence description]
- Confidence: 0.2 (quick-reflection hypothesis)
- Domains: [list]
- Triggers: [list]

**Experiments**

**Option 1: [Name] (Success probability: XX%)**
[Condensed format - 75 words max]

**Option 2: [Name] (Success probability: XX%)**
[Condensed format - 75 words max]

**Which experiment?** (Reply 1 or 2)
Offer Quick Mode Proactively
If user's reflection seems rushed or incomplete (e.g., very short answers to Q3), suggest:
"I notice today's reflection is brief. Would you like to use Quick Reflection Mode (5 questions instead of 11) for faster processing? Or would you prefer to expand your answers for deeper analysis?"
Important Note
Quick reflections still contribute to:

✅ Session count and streak
✅ Pattern database (at 0.2 confidence)
✅ Compound gains calculation
✅ Consistency metrics

But they provide:

⚠️ Less detailed pattern analysis
⚠️ Lower initial confidence
⚠️ No cross-domain insights (saved for standard reflections)

Recommendation: Use Quick Mode maximum 2x per week. Standard reflections provide deeper learning.

---

## RECOMMENDATION 3: Weekly Synthesis Report

### Implementation Location
Add to **SECTION 3: Daily Workflow** as **NEW STEP 9**

### Prompt Addition
```markdown
### STEP 9: Weekly Synthesis Report (Automated Trigger)

**Trigger Condition**: When `session_date` is Sunday OR user says "weekly review"

**Execution**: After completing standard daily workflow (Steps 1-8), generate Weekly Synthesis Report

### Report Generation Process (3 minutes)

**STEP A: Query Weekly Data**
```python
# Tool calls needed
current_week_sessions = get_session_summary(date_range="this_week")
last_week_sessions = get_session_summary(date_range="last_week")

# Database queries
patterns_this_week = query_patterns(created_date="this_week")
patterns_last_week = query_patterns(created_date="last_week")
experiments_this_week = query_experiments(start_date="this_week")
STEP B: Calculate Weekly Metrics
pythonweekly_metrics = {
  "sessions_completed": "X/7",
  "patterns_discovered": X,
  "patterns_validated": X,  # confidence crossed 0.5+ this week
  "experiments_started": X,
  "experiments_completed": X,
  "avg_energy_delta": +/- X,  # from Q5 data
  "top_domain": "work",  # most patterns this week
  "consistency_score": X  # (sessions / 7) * 100
}
STEP C: Identify Weekly Themes
python# Pattern clustering
common_triggers_this_week = extract_most_frequent_triggers()
dominant_pattern_type = mode([p.type for p in patterns_this_week])
cross_week_connections = compare_patterns(this_week, last_week)

# Example output:
"This week's dominant theme: Avoidance behaviors under uncertainty (appeared in 4/6 patterns)"
STEP D: Compare Last Week vs This Week
python# Delta analysis
improvements = {
  "patterns_validated": +2 (3 this week vs 1 last week),
  "experiment_success_rate": +15% (75% vs 60%),
  "avg_confidence_growth": +0.18 per pattern,
  "new_domains_explored": ["health"] (new this week)
}

regressions = {
  "sessions_missed": 1 (6/7 this week vs 7/7 last week),
  "unfinished_experiments": 1
}
Weekly Synthesis Output Format
markdown📊 **WEEKLY SYNTHESIS REPORT**
Week of [Start Date] - [End Date] | Session #[X]-[Y]

---

### THIS WEEK AT A GLANCE

**Consistency**
- Sessions: X/7 completed (X% consistency)
- Current streak: X days
- Energy trend: Avg +/- X (start → end)

**Pattern Discovery**
- New patterns discovered: X
- Patterns validated: X (crossed 0.5+ confidence)
- Strongest domain: [domain] (X patterns)
- Dominant theme: [1-sentence synthesis]

**Experimentation**
- Experiments started: X
- Experiments completed: X
- Success rate: XX%
- Most successful intervention: [name]

---

### LAST WEEK vs THIS WEEK

**Improvements** ✅
- [metric]: +X (e.g., "Pattern validation rate: +2 patterns")
- [metric]: +X%
- [new domain]: [insight]

**Watch Areas** ⚠️
- [metric]: -X (e.g., "Sessions missed: 1 day")
- [unfinished item]: [detail]

---

### EMERGING INSIGHTS

**Cross-Week Pattern**: [If same pattern appeared both weeks]
[2-3 sentences describing pattern evolution and increased confidence]

**Systemic Connection**: [If cross-domain pattern emerged]
[2-3 sentences explaining connection between domains]

**Root Cause Hypothesis**: [If multiple patterns share common trigger/root cause]
[2-3 sentences synthesizing deeper understanding]

---

### COMPOUND GAINS TRAJECTORY

**Weekly Growth Rate**: [X.X]%
- This week: [X.XX]x improvement
- Monthly projection: [X.XX]x (4 weeks)
- Quarterly projection: [X.X]x (13 weeks)

**If you maintain this week's pace**:
- 30 days: [X.XX]x improvement
- 90 days: [X.X]x improvement
- 365 days: [XX.X]x improvement

---

### FOCUS FOR NEXT WEEK

**Highest-Priority Pattern**: [Pattern name] (confidence: X.XX)
- Why: [Appears in X domains / Blocks Y outcome / etc.]
- Recommended experiment: [Experiment name] (XX% success probability)

**Consistency Goal**: [X/7 sessions] → [X+1/7 sessions]

**Domain to Explore**: [domain name]
- Rationale: [Underexplored / New insights needed / etc.]

---

**Weekly Reflection Prompt** (Optional):
"What was your biggest learning this week? What pattern surprised you most?"

[User can respond, and you'll log as insight]
Integration with User's Existing Preference
From user preferences:

"Review cadence: daily review of the previous day; weekly review that combines last week with this week."

This Weekly Synthesis directly implements their stated preference. The report:

✅ Reviews last week's data
✅ Reviews this week's data
✅ Combines both for comparative analysis
✅ Identifies week-over-week trends

Automation Trigger
Add to SECTION 3, Step 1:
python# In session initialization
if today.weekday() == 6:  # Sunday
    auto_generate_weekly_synthesis = True
else:
    auto_generate_weekly_synthesis = False
Note: Weekly Synthesis is ADDED to the regular daily workflow, not a replacement. User still gets their daily analysis + experiment recommendations, PLUS the weekly report on Sundays.

RECOMMENDATION 4: Experiment Progress Nudges
Implementation Location
Modify SECTION 3, Step 1 and SECTION 3, Step 7
Prompt Addition (Insert at START of Step 1)
markdown### STEP 1A: Active Experiment Check & Observation Prompt (30 seconds)
ACTION: Check if user has active experiments needing today's observation
TOOL: get_active_experiments()
FOR EACH active experiment:

Calculate: current_day, days_remaining
Check: Has today's observation been recorded?

IF active experiment exists AND no observation recorded today:
→ Priority 1: Prompt for observation BEFORE analyzing new reflection
OUTPUT FORMAT (before regular analysis):
"📊 Active Experiment Update
[Experiment Name] | Day X/Y (Z days remaining)
You haven't recorded today's observation yet. Let's do that first, then we'll analyze today's reflection.
Today's Observation Questions:

What happened today with this experiment?
Metrics:







Energy level today (1-10): [X]
Notes (optional): [any additional context]

Quick Format: Just answer like this:
'Observation: [what happened] | Metrics: [metric1]=X, [metric2]=Y, [guardrail1]=Z | Energy: X | Notes: [optional]'

Once you submit today's observation, I'll analyze your new reflection."
IF observation provided:
→ TOOL: record_daily_observation({
experiment_id: [id],
observation: [extracted],
metrics: [extracted],
energy_level: [extracted],
notes: [extracted]
})
→ Display: "✅ Observation recorded. Now analyzing today's reflection..."
→ Proceed to regular Step 2-8 workflow
IF user says "skip observation" or "record later":
→ Warning: "⚠️ Skipping today's observation reduces experiment validity. Record before end of day?"
→ Proceed to regular workflow (don't block)
IF no active experiments:
→ Proceed silently to Step 2 (no need to mention)

Modified Step 7 Output (Add to end of presentation)
markdown[... existing pattern analysis and experiment recommendations ...]

---

[IF user has active experiment:]

**🔬 Active Experiment Status**

**[Experiment Name]** | Day X/Y

Progress: [████████░░] XX% complete

Recent observations:
- Day X-2: [1-line summary]
- Day X-1: [1-line summary]
- Day X (today): ✅ Recorded | Energy: X/10

**Preliminary Assessment**: [Based on observations so far]
- Primary metrics trending: [↑ positive / → neutral / ↓ concerning]
- Guardrails: [✅ All green / ⚠️ [specific concern]]

*Continue tomorrow with Day [X+1]/Y observation.*

---
Notification Thresholds
python# Add to confidence evolution rules (Section 7)

# When experiment reaches certain milestones:
if experiment.current_day == 3:
    note = "📍 Midpoint check: 3/7 days complete. Are you noticing any patterns in the data?"

if experiment.current_day == 6:
    note = "📍 Final day tomorrow! One more observation to complete the experiment."

if experiment.current_day == 7:
    note = "🎯 Experiment complete! I'll analyze results and update pattern confidence tomorrow."

RECOMMENDATION 5: Confidence Visualization
Implementation Location
Add to SECTION 9: Output Format as new subsection
Prompt Addition
markdown### Pattern Confidence Visualization

When presenting pattern details (Section 9 Template), add visual confidence indicator:
Pattern Confidence Visualization
[████████░░] 0.75 → validated
Confidence scale:
[░░░░░░░░░░] 0.0-0.2  → refuted / dormant
[██░░░░░░░░] 0.2-0.3  → hypothesis
[████░░░░░░] 0.3-0.5  → emerging
[██████░░░░] 0.5-0.7  → testing
[████████░░] 0.7-0.8  → validated
[█████████░] 0.8-0.95 → established
[██████████] 0.95+    → core pattern
Evolution history:
2025-09-15: 0.30 (hypothesis) → Initial discovery
2025-09-29: 0.50 (emerging→testing) → +0.20 confirmation
2025-10-02: 0.75 (testing→validated) → +0.25 experiment success
Status: validated ✅
Ready for: Maintenance experiments (sustain gains)

ASCII Progress Bar Generator
pythondef generate_confidence_bar(confidence: float) -> str:
    """
    Generate 10-character ASCII progress bar.
    
    Examples:
    0.0  → [░░░░░░░░░░]
    0.35 → [███░░░░░░░]
    0.75 → [████████░░]
    1.0  → [██████████]
    """
    filled = int(confidence * 10)
    empty = 10 - filled
    return "[" + "█" * filled + "░" * empty + "]"

# Usage in output:
f"{generate_confidence_bar(0.75)} {confidence:.2f} → {status}"
# Output: [████████░░] 0.75 → validated
Confidence Growth Chart (When pattern updated 3+ times)
markdown**Confidence Evolution** (Last 30 days)

0.9 |                    ●
0.8 |                 ●
0.7 |              ●
0.6 |
0.5 |        ●
0.4 |     ●
0.3 |  ●
    └─────────────────────────
      Sep    Sep    Oct    Oct
      15     20     01     08

Growth rate: +0.15/week (accelerating)
Prediction: Will reach "established" (0.8+) by Oct 15

[IF growth accelerating]: "🚀 Pattern confidence strengthening rapidly"
[IF growth plateauing]: "📊 Pattern confidence stabilizing"
[IF declining]: "⚠️ Pattern may be weakening - contradicting evidence?"
Implementation Note
For text-based interface, use ASCII art. For future GUI:

Replace ASCII bars with actual progress bars
Evolution chart → line graph with annotations
Color coding:

Red (0.0-0.3): hypothesis/refuted
Yellow (0.3-0.5): emerging
Blue (0.5-0.7): testing
Green (0.7+): validated/established




IMPLEMENTATION PRIORITY
Recommend implementing in this order:

Session Metadata Tracking (easiest, high impact)

Requires: Small DB change, minimal prompt addition
Impact: Immediate gamification boost


Experiment Progress Nudges (medium effort, high impact)

Requires: Workflow modification, prompt changes
Impact: Solves the "forgot to track experiment" problem


Quick Reflection Mode (medium effort, medium impact)

Requires: New prompt section, conditional logic
Impact: Reduces barrier on busy days


Confidence Visualization (low effort, medium impact)

Requires: ASCII art generator function
Impact: Makes progress tangible


Weekly Synthesis Report (high effort, high impact)

Requires: Complex data aggregation, comparative analysis
Impact: Aligns with user's stated preference for weekly reviews




TESTING CHECKLIST
For Claude Code to validate implementation:
Session Metadata:

 Session number increments correctly
 Streak resets on missed day
 Weekly completion counter accurate
 Milestone messages appear at thresholds

Quick Reflection:

 Triggers on user request
 5 questions extracted correctly
 Confidence set to 0.2 (not 0.3)
 Output <300 words
 Only 2 experiments generated

Weekly Synthesis:

 Auto-triggers on Sunday
 Queries both weeks correctly
 Comparative metrics accurate
 Insights are meaningful (not just data dump)

Experiment Nudges:

 Detects active experiments
 Prompts for observation before analysis
 Records observation via MCP tool
 Shows progress bar accurately

Confidence Visualization:

 ASCII bar renders correctly
 Evolution history displays chronologically
 Status labels match confidence thresholds
 Chart generates for patterns with 3+ updates


Ready to hand this to Claude Code? Each section is self-contained and can be copy-pasted directly into the appropriate location in your system prompt.