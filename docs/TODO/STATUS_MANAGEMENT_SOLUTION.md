# Status Management Solution

## The Problem

Original status detection was **fragile and unreliable**:

1. **Heuristic-based detection**: Tried to guess status from file existence
   - `progress.txt` exists` = assuming "stopped"
   - `final_report` exists = assuming "done"
   - No reliable way to know if it's actually running

2. **State object inspection**: Hardcoded field names
   ```python
   len(state.generated_hypotheses)  # What if I rename this?
   ```
   Breaks when refactoring internal state structure.

3. **Multi-process detection**: Can't tell if research is actually running vs. just paused

---

## The Solution: Atomic Status File

### `status.json` - Single Source of Truth

Each research task maintains ONE atomic status file:

```json
{
  "status": "running",
  "last_updated": "2025-10-25T15:30:00.123456",
  "error": "Reached max iterations (20)"
}
```

### Status States

- **`new`**: No research started
- **`initializing`**: State created, starting research
- **`running`**: Research actively in progress
- **`paused`**: Research stopped but can resume
- **`error`**: Research failed with error
- **`completed`**: Research finished successfully

### Why This Works

1. **Atomic writes**: Single JSON file, single write operation
2. **No heuristics**: Status is explicitly written, not guessed
3. **Process-independent**: Doesn't depend on running processes
4. **Refactor-safe**: Doesn't inspect state object internals
5. **Clear semantics**: Status names are self-explanatory

---

## Implementation

### 1. StatusManager Class

```python
from coscientist.status_manager import StatusManager, ResearchStatus

manager = StatusManager(output_dir)
manager.update_status(ResearchStatus.RUNNING)
status, details = manager.get_status()
```

### 2. Framework Integration

```python
# In framework.py run() method
status_manager = StatusManager(output_dir)

try:
    status_manager.update_status(ResearchStatus.RUNNING)
    # ... do research ...
    status_manager.update_status(ResearchStatus.COMPLETED)
except Exception as e:
    status_manager.update_status(ResearchStatus.ERROR, error=str(e))
```

### 3. Status Detection

```python
from coscientist.cli.status import get_status

status = get_status("What is CRISPR?")
# Returns: "running", "completed", "error", etc.
```

---

## Usage

### Check Status

```bash
coscientist-status "What is CRISPR?"
```

### In Code

```python
from coscientist.cli.status import get_status

status = get_status("What is CRISPR?")

if status == "completed":
    print("Done!")
elif status == "running":
    print("Still running...")
elif status == "paused":
    print("Stopped, can resume")
elif status == "error":
    print("Failed")
```

### Auto-Resume Example

```python
from coscientist.cli.status import get_status
from coscientist.framework import CoscientistFramework
from coscientist.global_state import CoscientistState, CoscientistStateManager

goal = "What is CRISPR?"
status = get_status(goal)

if status == "paused" or status == "error":
    # Resume from checkpoint
    state = CoscientistState.load_latest(goal=goal)
    config = CoscientistConfig()
    state_manager = CoscientistStateManager(state)
    cosci = CoscientistFramework(config, state_manager)
    asyncio.run(cosci.run())  # Continues from where it stopped
```

---

## Benefits

### 1. Reliable Detection
- Status is **written**, not **inferred**
- No guessing based on file existence
- Atomic JSON write ensures consistency

### 2. Refactor-Safe
- Doesn't inspect state object internals
- Status file is independent of state structure
- Can refactor `CoscientistState` without breaking status

### 3. Process-Independent
- Status persists across crashes
- Can check status without process running
- Multiple processes can't interfere

### 4. Clear Semantics
- Status names are self-documenting
- No ambiguous states like "exists" vs "stopped"
- Error messages included in status file

---

## Migration Path

### Old Status Detection (REMOVE)

```python
# ❌ DON'T DO THIS
if os.path.exists("progress.txt"):
    status = "exists"  # Not reliable!
```

### New Status Detection (USE)

```python
# ✅ DO THIS
from coscientist.status_manager import get_research_status

status, details = get_research_status(goal)
# Returns actual status from status.json
```

---

## File Structure

```
~/.coscientist/<hash>/
├── status.json         ← Single source of truth
├── progress.txt        ← Human-readable progress
├── goal.txt           ← Research question
├── coscientist_state*.pkl  ← Checkpoints
└── error.log          ← Error details (if applicable)
```

### status.json Example

```json
{
  "status": "running",
  "last_updated": "2025-10-25T15:30:00.123456"
}
```

### When Research Errors

```json
{
  "status": "error",
  "last_updated": "2025-10-25T15:35:00.123456",
  "error": "API rate limit exceeded"
}
```

### When Research Completes

```json
{
  "status": "completed",
  "last_updated": "2025-10-25T16:00:00.123456"
}
```

---

## Summary

- **Old approach**: Fragile heuristics, hardcoded field names, unreliable
- **New approach**: Atomic JSON file, explicit status writes, reliable
- **Result**: Can always know exactly what status research is in, regardless of crashes or refactoring

