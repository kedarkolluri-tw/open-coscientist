# Datetime-Based Research Directories

## The Problem

Original design used **hash-based** directory names:
- Goal: "What is CRISPR?"
- Directory: `a3f5b8c1d2e4` (first 12 chars of SHA256 hash)

**Issues:**
- ❌ Cryptic, unreadable directory names
- ❌ Same goal = same hash = same directory (can only have one run per goal)
- ❌ Can't tell WHEN research was done
- ❌ Harder to debug and locate files

---

## The Solution: Datetime Directories

Now uses **datetime-based** directory names:
- Goal: "What is CRISPR?"
- Directory: `research_20251025_205309` (research_YYYYMMDD_HHMMSS)

**Benefits:**
- ✅ **Readable** - can see exactly when research ran
- ✅ **Unique** - each run gets its own folder
- ✅ **Discoverable** - easy to find recent research
- ✅ **Multiple runs** - can have many research runs for same goal

---

## How It Works

### Directory Structure

```
~/.coscientist/
├── research_20251025_143000/  ← Research run from Oct 25, 2:30 PM
│   ├── goal.txt               ← Goal text
│   ├── progress.txt            ← Progress tracking
│   ├── status.json             ← Atomic status
│   └── coscientist_state_*.pkl ← Checkpoints
├── research_20251025_150000/  ← Another research run
│   ├── goal.txt
│   └── ...
└── research_20251026_091500/  ← Next day's research
    └── ...
```

### Finding Research by Goal

Since multiple directories can have the same goal:

```python
from coscientist.global_state import CoscientistState

# Get ALL research for a specific goal
all_research = CoscientistState.list_all_goals()
# Returns: [("What is CRISPR?", "research_20251025_143000"), 
#           ("What is CRISPR?", "research_20251025_150000"), ...]

# Get MOST RECENT research for a specific goal
latest_state = CoscientistState.load_latest(goal="What is CRISPR?")
# Automatically finds the most recent directory with matching goal.txt
```

### Multiple Runs for Same Goal

**Before (hash-based):**
```bash
~/.coscientist/
└── a3f5b8c1d2e4/  # Only ONE directory per goal!
```

**Now (datetime-based):**
```bash
~/.coscientist/
├── research_20251025_143000/  # First run
├── research_20251025_150000/  # Second run
└── research_20251026_091500/  # Third run - next day
```

All three directories contain the same goal, but are **different research runs**!

---

## Implementation Details

### Directory Naming

```python
# In global_state.py
@staticmethod
def _hash_goal(goal: str) -> str:
    """Generate datetime-based directory name (old name kept for compatibility)"""
    return datetime.now().strftime("research_%Y%m%d_%H%M%S")
```

**Format:** `research_YYYYMMDD_HHMMSS`

### Goal Lookup

Since goal text is stored in `goal.txt`:

```python
def load_latest(goal: str):
    # 1. Search all directories for matching goal.txt
    # 2. Find most recent checkpoint (.pkl file)
    # 3. Return that state
```

### Listing All Research

```python
def list_all_goals():
    # Read goal.txt from all research_* directories
    # Sort by directory name (datetime) - most recent first
    return sorted(by_datetime, reverse=True)
```

---

## Migration Strategy

### Existing Research

Old hash-based directories:
- `a3f5b8c1d2e4/` ← Still valid!
- Code reads `goal.txt` to find research
- No migration needed - both formats work

### New Research

All new research uses datetime format:
- `research_20251025_143000/` ← New format

---

## Usage Examples

### Start Research (Creates Datetime Folder)

```python
from coscientist.framework import CoscientistFramework
from coscientist.global_state import CoscientistState, CoscientistStateManager

goal = "What is CRISPR?"
state = CoscientistState(goal=goal)  # Creates: research_20251025_143000/

config = CoscientistConfig()
state_manager = CoscientistStateManager(state)
cosci = CoscientistFramework(config, state_manager)

# Research creates: ~/.coscientist/research_20251025_143000/
```

### Find All Research for a Goal

```python
from coscientist.global_state import CoscientistState

all_research = CoscientistState.list_all_goals()
for goal_text, directory_name in all_research:
    print(f"{directory_name}: {goal_text}")

# Output:
# research_20251026_091500: What is CRISPR?
# research_20251025_150000: What is CRISPR?
# research_20251025_143000: What is CRISPR?
```

### Load Most Recent Research

```python
from coscientist.global_state import CoscientistState

goal = "What is CRISPR?"
latest_state = CoscientistState.load_latest(goal=goal)
# Automatically finds research_20251026_091500/ (most recent)
```

### List Recent Research by Date

```bash
ls -lt ~/.coscientist/
```

```
drwxr-xr-x research_20251026_091500  # Most recent
drwxr-xr-x research_20251025_150000
drwxr-xr-x research_20251025_143000  # Oldest
```

---

## Benefits Summary

| Feature | Hash-Based | Datetime-Based |
|---------|-----------|----------------|
| **Readability** | ❌ Cryptic (a3f5b8c1d2e4) | ✅ Readable (research_20251025_143000) |
| **Multiple Runs** | ❌ Overwrites | ✅ Separate folders |
| **Chronological** | ❌ No timestamp | ✅ Sortable by date |
| **Debugging** | ❌ Hard to navigate | ✅ Easy to find recent |
| **Uniqueness** | ✅ Deterministic | ✅ Timestamp ensures uniqueness |

---

## CLI Commands Updated

All CLI tools automatically work with datetime directories:

```bash
# List all research (sorted by date, newest first)
coscientist-list

# Check status (finds most recent directory for goal)
coscientist-status "What is CRISPR?"

# Monitor progress (finds most recent directory for goal)
coscientist-monitor "What is CRISPR?"

# Resume research (finds most recent directory for goal)
coscientist-resume
```

---

## Summary

- **Old:** Cryptic hashes, one folder per goal
- **New:** Readable datetime folders, multiple runs per goal
- **Result:** Better visibility, easier debugging, can re-run research

