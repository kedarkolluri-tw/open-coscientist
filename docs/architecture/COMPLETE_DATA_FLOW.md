# Complete Data Flow: Step-by-Step from User Input to Output

## Initial Setup (Hardcoded Sequence)

### Step 1: User Provides Research Goal
```
User: "How can we prevent cognitive decline in aging?"
```
**Decision**: Hardcoded (user input)

---

### Step 2: Literature Review Agent
**Called by**: Framework (hardcoded)
**Agent**: `literature_review_agent` (LangGraph)
**Input**: 
  - Research goal
**Output**: 
  - Literature review object containing:
    - `subtopic_reports`: List of 5 research subtopics
    - Example: "neuroprotection", "exercise", "diet", "sleep", "inflammation"
    - Each subtopic has research summary from GPT Researcher

**Decision**: Hardcoded call - always happens first

**Sequential?**: Yes, happens AFTER step 1 completes

---

### Step 3: Generation Agent (4 times)
**Called by**: Framework (hardcoded)
**Agent**: `generation_agent` (LangGraph)
**Input**: 
  - Research goal (from user)
  - Literature review (from step 2 - ALL 5 subtopic reports joined together)
  - Meta-review (from step 6 if available, otherwise "Not Available")
**Output**: 
  - 1 ParsedHypothesis object per call
  - Each call creates ONE hypothesis using ALL literature subtopics
  - Total: 4 separate hypothesis generation calls = 4 hypotheses

**Decision**: Hardcoded - generates 4 initial hypotheses

**Sequential?**: Yes, happens AFTER step 2 completes
**Input from step 2**: `literature_review` (ALL 5 subtopic reports combined into one string)

**How it works**:
- Each generation agent call gets the SAME input (all 5 subtopics)
- Each call creates ONE hypothesis that can draw from any/all subtopics
- 4 separate calls = 4 different hypotheses
- Each hypothesis can focus on different subtopics or combine them

**Collaborative Mode Details**:
When mode = "collaborative", it creates a **multi-agent conversation**:
- **2 agents** with different fields/reasoning types
- **Moderator** manages turn-taking (round-robin)
- **Agents debate** and refine ideas together
- **Parser** extracts final hypothesis from conversation transcript
- **Max 10 turns** of discussion

**Example Collaborative Flow**:
```
Agent 1 (Biology + Analytical): "I propose exercise increases BDNF..."
Agent 2 (Biology + Creative): "But what about sleep's role in clearance?"
Moderator: "Continue discussion"
Agent 1: "Good point, let's combine both mechanisms..."
Agent 2: "Here's a refined hypothesis..."
Moderator: "Finished" → Parser extracts final hypothesis
```

---

### Step 4: Reflection Agent (4 times, automatic)
**Called by**: Framework (automatically after generation)
**Agent**: `reflection_agent` (LangGraph)
**Input**: Each generated hypothesis
**Output**: Reviewed hypotheses (passed desk reject filter)

**Decision**: Hardcoded - automatically called after generation

---

### Step 5: Tournament Ranking
**Called by**: Framework (hardcoded)
**System**: ELO tournament (hardcoded algorithm)
**Input**: All reviewed hypotheses
**Output**: Ranked hypotheses with ELO scores

**Decision**: Hardcoded - initial ranking always happens

---

### Step 6: Meta-Review Agent
**Called by**: Framework (hardcoded)
**Agent**: `meta_review_agent` (LangGraph)
**Input**: Tournament results
**Output**: Meta-review synthesis

**Decision**: Hardcoded - happens after initial tournament

---

## Main Research Loop (Supervisor-Driven)

### Step 7: Supervisor Agent - Analyzes State
**Called by**: Framework (main loop)
**Agent**: `supervisor_agent` (LangGraph)
**Input**: 
  - Research goal
  - Meta-review (latest + previous)
  - Tournament statistics (ELO ratings, match counts)
  - Hypothesis counts
  - Action history
  
**Output**: Action decision (one of 6 hardcoded actions)

**Decision**: LLM-based (supervisor agent decides)

**6 Available Actions**:
1. `generate_new_hypotheses`
2. `evolve_hypotheses`
3. `run_tournament`
4. `run_meta_review`
5. `expand_literature_review`
6. `finish`

---

### Step 8: Execute Chosen Action

#### If Action = "generate_new_hypotheses":

**8a. Generation Agent** (2 times)
- **Called by**: Framework
- **Agent**: `generation_agent` (LangGraph)
- **Input**: Goal + literature + meta-review
- **Output**: 2 new hypotheses

**8b. Reflection Agent** (2 times, automatic)
- **Called by**: Framework (automatically)
- **Agent**: `reflection_agent` (LangGraph)
- **Input**: Each generated hypothesis
- **Output**: Reviewed hypotheses

**Decision**: Hardcoded - automatically triggered

---

#### If Action = "evolve_hypotheses":

**8a. Evolution Agent** (4 times)
- **Called by**: Framework
- **Agent**: `evolution_agent` (LangGraph)
- **Input**: Top ranked hypotheses + meta-review
- **Output**: 4 evolved hypotheses

**8b. Reflection Agent** (4 times, automatic)
- **Called by**: Framework (automatically)
- **Agent**: `reflection_agent` (LangGraph)
- **Input**: Each evolved hypothesis
- **Output**: Reviewed hypotheses

**Decision**: Hardcoded - automatically triggered

---

#### If Action = "run_tournament":

**Tournament Ranking**
- **Called by**: Framework
- **System**: ELO tournament (hardcoded)
- **Input**: All unranked hypotheses
- **Output**: Updated ELO rankings

**Decision**: Hardcoded algorithm

---

#### If Action = "run_meta_review":

**Meta-Review Agent**
- **Called by**: Framework
- **Agent**: `meta_review_agent` (LangGraph)
- **Input**: Tournament results
- **Output**: Meta-review synthesis

**Decision**: LLM-based

---

#### If Action = "expand_literature_review":

**Literature Review Agent**
- **Called by**: Framework
- **Agent**: `literature_review_agent` (LangGraph)
- **Input**: Research goal
- **Output**: Additional literature subtopics

**Decision**: LLM-based

---

#### If Action = "finish":

**Final Report Agent**
- **Called by**: Framework
- **Agent**: `final_report_agent` (LangGraph)
- **Input**: Top ranked hypotheses + tournament results
- **Output**: Final research report

**Decision**: LLM-based

---

### Step 9: Update Global State
**Called by**: Framework (automatically after each action)
**System**: State manager (hardcoded)
**Action**: Updates all state variables (hypotheses, rankings, meta-reviews, etc.)

**Decision**: Hardcoded

---

### Step 10: Check if Finished
**Called by**: Framework
**Decision**: Hardcoded logic
- If supervisor chose "finish" → Done
- If max iterations reached → Done
- Otherwise → Go back to Step 7

---

### Step 11: Repeat Loop
Go back to Step 7 (Supervisor Agent) and repeat until finished.

---

## Key Difference: Generation vs Evolution

**Generation Agent** (Step 3):
- **Input**: Research goal + literature review + meta-review
- **Output**: New hypotheses from scratch
- **Purpose**: Create original, diverse ideas
- **Prompt**: "Formulate a creative hypothesis about [goal]"

**Evolution Agent** (Step 8 when action = "evolve_hypotheses"):
- **Input**: Existing hypothesis + feedback + meta-review
- **Output**: Improved version of existing hypothesis
- **Purpose**: Refine and improve existing hypotheses
- **Prompt**: "Refine this hypothesis based on feedback to make it more competitive"

**Two Evolution Modes**:
1. **Evolve from Feedback**: Takes a specific hypothesis, reads its review/feedback, and creates an improved version
2. **Out of the Box**: Takes top-ranked hypotheses, draws analogies, creates novel divergent ideas

---

## Who Decides: Generate vs Evolve?

**Answer: The Supervisor Agent (LLM-based decision)**

The Supervisor Agent analyzes the research state and chooses:

### When to GENERATE NEW:
- Total hypotheses < 8-10 (need more exploration)
- High similarity score (>0.85) - hypotheses too similar
- Poor performance (median ELO < 1300)
- Low diversity

### When to EVOLVE:
- Enough hypotheses (4+ strong performers)
- Good diversity exists (similarity < 0.85)
- Meta-review suggests promising directions
- Quality improving

### How Supervisor Makes Decision:

**Input to Supervisor**:
- Research goal
- Meta-reviews (latest + previous)
- ELO statistics (ratings, counts, trends)
- Hypothesis counts (total, unranked, new since meta-review)
- Diversity metrics (similarity trajectory, cluster counts)
- Action history

**Output**: One of 6 actions:
1. `generate_new_hypotheses` - Create new ideas
2. `evolve_hypotheses` - Refine existing ideas
3. `run_tournament` - Rank hypotheses
4. `run_meta_review` - Synthesize results
5. `expand_literature_review` - Get more literature
6. `finish` - Complete research

**Decision Logic** (from prompt):
- **Early Stage (< 12 hypotheses)**: Generate more
- **Mid Stage (12-25 hypotheses)**: Balance generate + evolve
- **Late Stage (25+ hypotheses)**: Evolve top performers

---

## When Does the Supervisor Stop?

**Two Stopping Conditions**:

### 1. **LLM Decides to Finish** (ideal):
- **At least 3+ high-quality hypotheses** (ELO > 1400)
- **Diminishing returns** evident (ELO plateauing over last 3+ meta-reviews)
- **Research goal** appears sufficiently addressed
- **Most recent action** was `run_meta_review`

### 2. **Max Iterations Reached** (hardcoded limit):
- **Default: 20 iterations** (can be configured)
- If supervisor doesn't choose "finish" after 20 iterations, system stops anyway
- Returns warning: "Reached maximum iterations"

**Typical Flow**:
- Initialization: 4 hypotheses + tournament + meta-review (~4 iterations)
- Then: Supervisor decides actions for ~15-16 more iterations
- Most runs should finish before hitting the 20-iteration limit

**If Supervisor Doesn't Finish**:
The system stops at iteration 20, returns whatever has been generated, even if incomplete.

## Complete Flow Summary:

```
1. User Input (hardcoded)
   ↓
2. Literature Review Agent (LLM decision) ← hardcoded call
   ↓
3. Generation Agent ×4 (LLM decision) ← hardcoded call
   ↓
4. Reflection Agent ×4 (LLM decision) ← automatic
   ↓
5. Tournament Ranking (hardcoded algorithm)
   ↓
6. Meta-Review Agent (LLM decision) ← hardcoded call
   ↓
7. Supervisor Agent (LLM decision) ← main loop
   ↓
8. Execute chosen action (depends on supervisor decision)
   ↓
9. Update Global State (hardcoded)
   ↓
10. Check if finished (hardcoded)
   ↓
11. Repeat or finish (hardcoded)
```

## Key Decisions:

- **Hardcoded**: Steps 1, 2, 3, 4 (initialization sequence)
- **LLM-Based**: Supervisor decides which action (Step 7)
- **Hardcoded**: Tournament uses ELO algorithm
- **Automatic**: Reflection Agent always runs after generation/evolution
- **Hardcoded**: State updates and loop control

## Agent Calls:

1. **Literature Review Agent** - Called by framework (hardcoded)
2. **Generation Agent** - Called by framework (hardcoded or supervisor)
3. **Reflection Agent** - Called automatically by framework after generation/evolution
4. **Evolution Agent** - Called by framework (supervisor decision)
5. **Meta-Review Agent** - Called by framework (hardcoded initially, supervisor decision later)
6. **Supervisor Agent** - Called by framework (main loop)
7. **Final Report Agent** - Called by framework (supervisor decision)

## LLM vs Hardcoded:

- **LLM Decisions**: Literature review, generation, reflection, evolution, meta-review, supervisor decisions, final report
- **Hardcoded**: Tournament ranking (ELO), state updates, loop control, reflection triggering

