# Setup Complete: Monolithic Package Structure

## Current Architecture

```
open-coscientist-agents/
├── coscientist/              ← Core research engine (agents, framework, state)
├── coscientist_interact/    ← Interactive UI and resume functionality
├── tests/                    ← Test suite
├── docs/                     ← Documentation
├── pyproject.toml            ← Single package definition
└── README.md
```

**Packages status**: ✅ Both have `__init__.py` and are installable as Python packages
**Dependencies**: ✅ All in `pyproject.toml` dependencies section
**Imports**: ✅ Fixed to use proper namespacing (`coscientist_interact.` prefix)
**Entry point**: ✅ `coscientist-interact` command defined

---

## Installation

```bash
cd open-coscientist-agents
uv pip install -e .
```

This installs:
- `coscientist` package (core engine)
- `coscientist_interact` package (UI)
- All dependencies (LangChain, Streamlit, etc.)

---

## Usage

### Running Research (Programmatic)

```python
import asyncio
from coscientist.framework import CoscientistConfig, CoscientistFramework
from coscientist.global_state import CoscientistState, CoscientistStateManager

goal = "What is CRISPR?"
state = CoscientistState(goal=goal)
config = CoscientistConfig()
state_manager = CoscientistStateManager(state)
framework = CoscientistFramework(config, state_manager)

final_report, meta_review = asyncio.run(framework.run())
```

### Launching UI

```bash
coscientist-interact
```

Or directly:
```bash
streamlit run coscientist_interact/tournament_viewer.py
```

---

## Key Files

### Core Engine (`coscientist/`)
- `framework.py` - Main orchestration
- `global_state.py` - State management and checkpoints
- `generation_agent.py` - Hypothesis generation
- `reflection_agent.py` - Deep verification
- `supervisor_agent.py` - Decision making
- ... and other agents

### Interactive UI (`coscientist_interact/`)
- `tournament_viewer.py` - Main Streamlit app (entry point)
- `resume_page.py` - Resume interrupted research
- `background.py` - Background execution and status
- `common.py` - State loading utilities
- ... and viewer pages

---

## Resume Functionality

**How it works**:
1. Research runs and saves `.pkl` checkpoints to `~/.coscientist/<hash>/`
2. UI loads checkpoints via `CoscientistState.load_latest()`
3. Can resume from any checkpoint
4. Background process continues research
5. Status tracked via `done.txt` and `error.log`

**To resume**:
```python
# In code
state = CoscientistState.load_latest(goal="...")
framework = CoscientistFramework(config, state_manager)
asyncio.run(framework.run())  # Continues from checkpoint

# In UI
# Go to "Resume from Checkpoint" page in coscientist-interact
```

---

## Import Structure

### Internal (within coscientist_interact)
```python
from coscientist_interact.common import ...
from coscientist_interact.background import ...
```

### External (importing from coscientist)
```python
from coscientist.framework import ...
from coscientist.global_state import ...
```

### Important: Version Parity

Both packages are part of the same project and **always shipped together**:
- ✅ Same version number
- ✅ Guaranteed pickle compatibility
- ✅ Resume always works
- ✅ No version drift

---

## Done ✅

- Restructured `app/` → `coscientist_interact/`
- Fixed all imports to use proper namespacing
- Added entry point `coscientist-interact`
- Created documentation
- Ensured version parity (monolithic package)
- Both packages have `__init__.py` and are installable

The project is now properly structured as a monolithic package with two subpackages that ship together.
