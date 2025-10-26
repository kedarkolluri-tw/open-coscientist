# Progress Tracking Setup

## How It Works

### Progress File

Every research run writes to: `<output_dir>/progress.txt`

**Format**:
```
2025-10-25T15:00:00 | START | Literature Review and initial hypothesis generation
2025-10-25T15:05:30 | DONE | Literature review complete, 4 hypotheses generated
2025-10-25T15:05:31 | ITERATION | 1/20: Starting
2025-10-25T15:05:32 | ACTION | generate_new_hypotheses
2025-10-25T15:10:15 | STATUS | 0 reviewed, 8 total hypotheses, 5% complete
2025-10-25T15:10:16 | ITERATION | 2/20: Starting
...
```

### Markers

- **START**: Major phase starting (literature review, final report)
- **DONE**: Phase complete
- **ITERATION**: New supervisor iteration (e.g., "5/20")
- **ACTION**: Supervisor's decided action
- **STATUS**: Current state (reviewed count, total hypotheses, progress %)
- **ERROR**: Error occurred

---

## Finding the Hash

### Option 1: Use `monitor_progress.py` Script

```bash
# Monitor specific research
python monitor_progress.py "What is CRISPR?"

# Or list all research
python monitor_progress.py list
```

**This auto-discovers the hash!**

### Option 2: Manual Discovery

```bash
# Find based on goal text
ls -lt ~/.coscientist/ | grep "What is CRISPR"
```

### Option 3: List Recent Research

```bash
python list_research_goals.py
```

Shows all goals with their hashes.

---

## Custom Storage Location

### Change Default Directory

Set environment variable:
```bash
export COSCIENTIST_DIR=/path/to/your/dir
```

**Example**:
```bash
export COSCIENTIST_DIR=./my_research_data
python tests/test_simple.py

# Progress file at: ./my_research_data/<hash>/progress.txt
```

### Or in Code

```python
import os
os.environ["COSCIENTIST_DIR"] = "/path/to/dir"

from coscientist.framework import CoscientistFramework
# ... rest of code
```

---

## Monitoring Progress

### Live Monitoring

```bash
# Terminal 1: Run research
python tests/test_simple.py

# Terminal 2: Watch progress
python monitor_progress.py "What is CRISPR?"
```

### Simple Tail

```bash
tail -f ~/.coscientist/<hash>/progress.txt
```

### Grep for Specific Info

```bash
tail -f ~/.coscientist/*/progress.txt | grep "ACTION"
tail -f ~/.coscientist/*/progress.txt | grep "STATUS"
```

---

## Example Output

```
📊 Monitoring progress: What is CRISPR?

📁 File: ~/.coscientist/8f3200309e4a/progress.txt

================================================================================
2025-10-25T15:00:00 | START | Literature Review and initial hypothesis generation
2025-10-25T15:05:30 | DONE | Literature review complete, 4 hypotheses generated
2025-10-25T15:05:31 | ITERATION | 1/20: Starting
2025-10-25T15:05:32 | ACTION | generate_new_hypotheses
2025-10-25T15:10:15 | STATUS | 4 reviewed, 8 total hypotheses, 5% complete
2025-10-25T15:10:16 | ITERATION | 2/20: Starting
2025-10-25T15:10:17 | ACTION | run_tournament
2025-10-25T15:12:00 | STATUS | 8 reviewed, 8 total hypotheses, 10% complete
================================================================================

🔄 Monitoring for updates...
```

---

## Summary

### To Monitor Progress

**Easiest**:
```bash
python monitor_progress.py "<your research goal>"
```

**Custom location**:
```bash
export COSCIENTIST_DIR=/custom/path
python tests/test_simple.py &
python monitor_progress.py "<goal>"
```

### To Find Hash

**Automatic** (recommended):
```bash
python list_research_goals.py
```

**Manual**:
```bash
ls -lt ~/.coscientist/
```

### Default Location

- **Default**: `~/.coscientist/`
- **Custom**: Set `COSCIENTIST_DIR` environment variable
- **Progress file**: `<dir>/<hash>/progress.txt`

