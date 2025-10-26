# State Management & Resume Guide

## Understanding the .pkl Checkpoint System

The Coscientist system automatically saves **full state checkpoints** as `.pkl` files at key points in the research process. This enables recovery from crashes and resuming interrupted research.

---

## How Checkpoints Work

### Auto-Save Mechanism

**Key concept**: Many methods in `CoscientistStateManager` are decorated with `@_maybe_save(n=1)`, which automatically saves state after every call.

**Auto-save triggers**:
- `add_reviewed_hypothesis()` - After reflection completes
- `add_evolved_hypothesis()` - After evolution completes  
- `add_action()` - After supervisor decides
- `update_literature_review()` - After literature review
- `update_meta_review()` - After meta-review
- `update_proximity_graph_edges()` - After proximity calculation
- ... and more

### Checkpoint Contents

Each `.pkl` file contains the **entire** `CoscientistState` object with:

- ✅ Research goal
- ✅ Literature review (full research results)
- ✅ All generated hypotheses (raw)
- ✅ All reviewed hypotheses (after reflection)
- ✅ Tournament rankings (ELO ratings)
- ✅ Evolved hypotheses
- ✅ Meta-reviews
- ✅ Proximity graph (for similarity visualization)
- ✅ Reflection queue
- ✅ Supervisor decisions
- ✅ Final report (when complete)
- ✅ Action history
- ✅ Trajectory metrics (diversity, clusters)

### Checkpoint Naming

```
coscientist_state_YYYYMMDD_HHMMSS_iter_NNNN.pkl
```

**Example**: `coscientist_state_20251025_145246_iter_0000.pkl`

- **Timestamp**: When it was saved
- **Iteration**: How many times this run has been saved
- **Sequential**: Each save increments iteration counter

### Storage Location

```
~/.coscientist/<goal_hash>/coscientist_state_*.pkl
```

**Goal hash**: First 12 characters of SHA256 hash of the research goal.

**Why hashes?**: 
- Consistent even if goal text is reformatted
- No collisions (SHA256 is collision-resistant)
- Predictable storage location

---

## How to Find Your Research

### Option 1: List All Goals Script

```bash
cd open-coscientist-agents
python3 list_research_goals.py
```

**Output**:
```
🔬 All Research Goals
================================================================================
📁 Hash: 8f3200309e4a
📝 Goal: What is CRISPR gene editing and how does it work?
⏰ Last updated: 2025-10-25 14:54:11
💾 State files: 2
--------------------------------------------------------------------------------
```

### Option 2: Browse Directory

```bash
ls -la ~/.coscientist/
```

Each hash directory contains:
- `goal.txt` - The research goal text
- `coscientist_state_*.pkl` - Checkpoint files (latest is newest)

### Option 3: Use Python API

```python
from coscientist.global_state import CoscientistState

# List all goals
goals = CoscientistState.list_all_goals()
for goal, hash_dir in goals:
    print(f"{hash_dir}: {goal}")

# Get latest checkpoint for a goal
state = CoscientistState.load_latest(goal="What is CRISPR...")
```

---

## How to Resume Research

### Option 1: Using Resume Script

```bash
cd open-coscientist-agents
python3 resume_research.py <goal_number>
```

**Example**:
```bash
python3 resume_research.py 1
```

First lists all goals, then resumes the selected one.

### Option 2: Manual Resume (Python)

```python
import asyncio
from coscientist.framework import CoscientistConfig, CoscientistFramework
from coscientist.global_state import CoscientistState, CoscientistStateManager

# Load latest state for your goal
state = CoscientistState.load_latest(goal="What is CRISPR...")

# Create framework
config = CoscientistConfig()
state_manager = CoscientistStateManager(state)
cosci = CoscientistFramework(config, state_manager)

# Continue research
final_report, meta_review = asyncio.run(cosci.run())
```

### Option 3: Load From Specific File

```python
from coscientist.global_state import CoscientistState

# Load specific checkpoint
state = CoscientistState.load("path/to/coscientist_state_*.pkl")

# Continue as above...
```

---

## Checking Research Progress

### Using Progress Checker

```bash
cd open-coscientist-agents
export $(cat .env.test | grep -v '^#' | xargs)
PYTHONPATH=. uv run python3 check_progress.py
```

**Output shows**:
- ✅ Whether literature review is done
- 📝 How many hypotheses generated
- ✅ How many reviewed  
- 🏆 Tournament status
- 📊 Meta-reviews count
- 🔄 Reflection queue size
- 📋 Actions taken
- 📄 Final report status

### Understanding the Output

```
✅ Has literature review: True      ← Research has been done
📝 Generated hypotheses: 4           ← 4 raw hypotheses created
✅ Reviewed hypotheses: 0            ← None passed reflection yet
🏆 Tournament: Yes                   ← Tournament initialized
📊 Meta reviews: 0                  ← No meta-reviews yet
🔄 Reflection queue: 0               ← No pending reflection
📋 Actions taken: 0                 ← No supervisor decisions yet
📄 Final report: No                 ← Not finished
```

**Interpretation**:
- Literature review completed ✅
- Hypotheses generated, but none have passed reflection
- System is ready for supervisor to decide next action
- No meta-reviews or final report yet

---

## Key Points

### ✅ Always Resumeable
- Every major state change is saved automatically
- Can resume from any `.pkl` checkpoint
- No data loss between checkpoints

### 📁 Storage Structure
- One directory per research goal (by hash)
- Multiple checkpoint files per goal
- `goal.txt` identifies the goal
- Latest checkpoint = most recent file

### 🔄 Resume vs. Restart
- **Resume**: Load latest checkpoint, continue from where it stopped
- **Restart**: Clear goal directory, start fresh

```python
# Clear goal to restart
CoscientistState.clear_goal_directory("What is CRISPR...")

# Or manually
import shutil
shutil.rmtree("~/.coscientist/<hash>")
```

---

## Troubleshooting

### Can't Find Goal?
```python
# List all goals
goals = CoscientistState.list_all_goals()
print(goals)
```

### State File Corrupted?
- `pickle.load()` will raise an error
- Try loading an earlier checkpoint
- Last resort: clear directory and restart

### Which Checkpoint to Load?
- Use `load_latest()` to get newest
- Or specify exact file path for older version

### Storage Getting Large?
- Clear old research goals
- Each checkpoint is full state (can be large)
- Consider archiving completed research

---

## Best Practices

1. **Check Progress Regularly**: Use `check_progress.py` to monitor
2. **Don't Delete Checkpoints**: They're your safety net
3. **One Goal Per Run**: Don't modify state files manually
4. **Track Which Goals Are Active**: Use `list_research_goals.py`
5. **Architecture Completed Goals**: Move to archive when done

---

This system ensures you **never lose progress** and can always resume research from the last saved state.
