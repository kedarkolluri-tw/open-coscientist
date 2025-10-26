# Progress Tracking: User-Friendly Options

## Current Problem

Users have **zero visibility** into research progress:
- Literature review is running GPT Researcher (hours, no feedback)
- Hypothesis generation happening silently
- Tournament running with no indication
- No way to know "where are we?" or "how much is left?"

---

## Option 1: Simple Markers in Logs (EASIEST) ✅ **RECOMMENDED**

### Implementation

Add structured log markers to framework:

```python
# In framework.py
logging.info("🚀 START: Literature Review")
await self.start(n_hypotheses=4)
logging.info("✅ DONE: Literature Review - 4 hypotheses generated")

# In main loop
logging.info(f"🎯 ITERATION {iteration}/{max_iterations}: Starting")
logging.info(f"💡 ACTION: {current_action}")
logging.info(f"📊 STATUS: {len(reviewed_hypotheses)} reviewed, {len(actions)} actions")
logging.info(f"⏱️  PROGRESS: ~{(iteration/max_iterations)*100:.0f}% complete")
logging.info(f"⏭️  NEXT: Supervisor deciding...")
```

### User Experience

```bash
# Grep for high-level progress
tail -f research.log | grep "🚀 START:\|✅ DONE:\|🎯 ITERATION\|💡 ACTION\|📊 STATUS"

# Output:
🚀 START: Literature Review
✅ DONE: Literature Review - 4 hypotheses generated
🎯 ITERATION 1/20: Starting
💡 ACTION: generate_new_hypotheses
📊 STATUS: 8 reviewed, 5 actions
🎯 ITERATION 2/20: Starting
💡 ACTION: run_tournament
📊 STATUS: 12 reviewed, 6 actions
...
```

**Pros**:
- ✅ Zero code changes beyond adding a few log statements
- ✅ Works with existing logger
- ✅ Easy to grep
- ✅ Visual markers (emojis)
- ✅ Contextual progress percentage

**Cons**:
- ❌ Logs can get long
- ❌ Need to grep to filter

---

## Option 2: Progress File (SIMPLE)

### Implementation

Write to `~/.coscientist/<hash>/progress.txt`:

```python
def log_progress(marker: str, info: str):
    """Write progress marker to file."""
    progress_file = os.path.join(state._output_dir, "progress.txt")
    with open(progress_file, "a") as f:
        f.write(f"{datetime.now().isoformat()} | {marker} | {info}\n")
        f.flush()

# In framework.py
log_progress("START", f"Literature Review")
log_progress("DONE", f"4 hypotheses generated")
log_progress("ITERATION", f"{iteration}/20: {action}")
log_progress("STATUS", f"{len(reviewed)} reviewed, {len(actions)} actions")
```

### User Experience

```bash
# Tail the progress file
tail -f ~/.coscientist/8f3200309e4a/progress.txt

# Output:
2025-10-25T15:00:00 | START | Literature Review
2025-10-25T15:05:30 | DONE | 4 hypotheses generated  
2025-10-25T15:05:31 | ITERATION | 1/20: generate_new_hypotheses
2025-10-25T15:10:15 | DONE | Generated 4 new hypotheses
2025-10-25T15:10:16 | ITERATION | 2/20: run_tournament
2025-10-25T15:12:00 | STATUS | 8 reviewed, 6 actions
...
```

**Pros**:
- ✅ Clean, structured file
- ✅ One line per major event
- ✅ Easy to parse programmatically
- ✅ Timestamped
- ✅ Separate from logs (no noise)

**Cons**:
- ❌ Need to check specific file location
- ❌ Slightly more code

---

## Option 3: Console Spinner (VISUAL)

### Implementation

Show spinner in terminal during long operations:

```python
from itertools import cycle
import sys

def show_progress(message: str, duration=1):
    spinner = cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
    for _ in range(20):
        sys.stdout.write(f'\r{next(spinner)} {message}...')
        sys.stdout.flush()
        time.sleep(duration/20)
    sys.stdout.write('\n')

# Usage
show_progress("Generating hypotheses", 30)
```

### User Experience

```bash
⠋ Generating hypotheses...
⠙ Running tournament...
⠹ Processing reflection...
```

**Pros**:
- ✅ Visual feedback
- ✅ Easy to see progress
- ✅ Works in terminals

**Cons**:
- ❌ Doesn't help with background processes
- ❌ Ugly in logs
- ❌ Requires active terminal

---

## Option 4: Simple Script: `watch_progress.py` (MOST USER-FRIENDLY)

### Implementation

Create a script that tail progress file AND shows current state:

```python
#!/usr/bin/env python3
"""Watch research progress in real-time."""
import os
import time
from coscientist.global_state import CoscientistState

def watch_progress(goal: str):
    state = CoscientistState.load_latest(goal=goal)
    
    if not state:
        print("❌ No research found")
        return
    
    progress_file = os.path.join(state._output_dir, "progress.txt")
    
    print(f"\n📊 Watching: {goal}\n")
    
    if os.path.exists(progress_file):
        with open(progress_file, "r") as f:
            for line in f:
                print(line.strip())
    
    print("\n🔄 Monitoring for updates...\n")
    
    # Tail the file
    with open(progress_file, "r") as f:
        # Go to end
        f.seek(0, 2)
        
        while True:
            line = f.readline()
            if line:
                print(line.strip())
            else:
                time.sleep(1)
```

### User Experience

```bash
# In terminal 1
python tests/test_simple.py

# In terminal 2
./watch_progress.py "What is CRISPR?"
```

**Output**:
```
📊 Research Progress: CRISPR gene editing

🎯 ITERATION 1/20
💡 Action: generate_new_hypotheses
📊 Status: 4 hypotheses generated, 1 action taken
⏱️  Progress: 5% complete

🎯 ITERATION 2/20
💡 Action: run_tournament
📊 Status: 8 hypotheses reviewed, 2 actions taken
⏱️  Progress: 10% complete
```

**Pros**:
- ✅ Real-time updates
- ✅ Clean output
- ✅ Shows exact status
- ✅ Can be run in separate terminal

**Cons**:
- ❌ Requires progress file infrastructure
- ❌ Need to run script separately

---

## Option 5: HTTP Endpoint (OVERKILL for now)

Provide simple HTTP endpoint:
```
GET localhost:8080/status
{
  "iteration": 5,
  "action": "generate_new_hypotheses",
  "progress": "25%",
  "hypotheses": 12,
  "actions": 5
}
```

**Pros**: Real-time, programmatic
**Cons**: Overkill, adds complexity

---

## **Recommendation: Option 1 + Option 2 (Hybrid)**

### Implementation

**Do both**:
1. Add emoji markers to existing logs (Option 1)
2. Write progress file for easy tailing (Option 2)
3. Provide simple script to tail progress file (Option 4)

### Why This Works

- **Option 1** (log markers): Users can grep existing logs
- **Option 2** (progress file): Clean, parseable file
- **Option 4** (watch script): User-friendly interface

### Minimal Changes Needed

```python
# In framework.py - just add these 5 lines:
def log_progress(marker: str, details: str):
    progress_file = os.path.join(self.state_manager._state._output_dir, "progress.txt")
    with open(progress_file, "a") as f:
        f.write(f"{datetime.now().isoformat()} | {marker} | {details}\n")
        f.flush()
    logging.info(f"📋 {marker}: {details}")

# Add at key points:
log_progress("START", "Literature Review")
log_progress("ITERATION", f"{iteration}/20: {action}")
log_progress("STATUS", f"{len(reviewed)} reviewed")
```

### User Workflow

```bash
# Terminal 1: Watch progress
tail -f ~/.coscientist/<hash>/progress.txt

# Terminal 2: Or use script
python watch_progress.py "What is CRISPR?"

# Terminal 3: Run research
python tests/test_simple.py
```

---

## Implementation Priority

1. **Phase 1 (NOW)**: Add Option 2 (progress file) - 5 log statements
2. **Phase 2**: Add Option 1 (emoji markers in logs) - 10 log statements  
3. **Phase 3**: Create `watch_progress.py` script
4. **Phase 4 (LATER)**: Real-time UI dashboard (from UI_IMPROVEMENT_PLAN.md)

**Total code changes**: ~20 lines in framework.py

