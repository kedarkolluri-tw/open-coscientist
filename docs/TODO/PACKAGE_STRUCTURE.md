# Package Structure

## Overview

The project is organized into three main packages:

```
open-coscientist-agents/
├── coscientist/          ← Core research engine (agents, framework, state)
├── coscientist_interact/ ← Streamlit UI for visualizing results
└── tests/               ← Test suite
```

---

## Package: `coscientist`

The core research engine that provides multi-agent scientific discovery.

**Key components**:
- **Agents**: Literature review, generation, reflection, evolution, meta-review
- **Framework**: Orchestration and state management
- **State**: Checkpoint system for resumable research
- **Prompts**: Template system for agent interactions
- **Config**: LLM configuration and validation

**Usage**:
```python
from coscientist.framework import CoscientistConfig, CoscientistFramework
from coscientist.global_state import CoscientistState, CoscientistStateManager

# Create framework and run research
config = CoscientistConfig()
state = CoscientistState(goal="Your research question")
state_manager = CoscientistStateManager(state)
framework = CoscientistFramework(config, state_manager)

# Run research
asyncio.run(framework.run())
```

---

## Package: `coscientist_interact`

A Streamlit-based UI for visualizing, resuming, and managing research results.

**Key features**:
- 📋 **Configuration**: View and modify agent configurations
- 📚 **Literature Review**: Browse research findings
- 🏆 **Tournament Rankings**: See hypothesis ELO ratings and debates
- 🔗 **Proximity Graph**: Visualize semantic similarity between hypotheses
- 📊 **Meta-Reviews**: View strategic insights
- 🎯 **Supervisor Decisions**: Track action history
- 📄 **Final Report**: Read completed research
- 🔄 **Resume**: Continue interrupted research from checkpoints
- 🔧 **Background Execution**: Run research in background processes
- 📊 **Status Tracking**: Monitor research progress and completion

**Usage**:

After installation:
```bash
coscientist-interact
```

Or with streamlit directly:
```bash
streamlit run coscientist_interact/tournament_viewer.py
```

**Entry point**: `coscientist_interact.tournament_viewer:main`

---

## Installation

### Development Mode
```bash
cd open-coscientist-agents
uv pip install -e .
```

### With UI Support
```bash
uv pip install -e ".[viewer]"
```

### Production
```bash
uv pip install .
```

---

## Entry Points

### Command: `coscientist-interact`

Launches the Streamlit viewer interface.

**Usage**:
```bash
coscientist-interact
```

**What it does**:
1. Loads `.env.test` for API keys
2. Starts Streamlit server
3. Provides interactive dashboard for viewing research results

**Configuration**:
- Set environment variables in `.env.test`
- Or modify `coscientist_interact/tournament_viewer.py` to change config source

---

## Key Design Decisions

### Why Separate Packages?

1. **Modularity**: Core engine can be used without UI
2. **Optional Dependencies**: UI is optional (requires Streamlit)
3. **Clean Namespace**: Clear distinction between engine and interaction
4. **Independent Development**: UI and engine can evolve separately

### Why `coscientist_interact`?

1. **Installed Package**: Proper Python package, not orphaned code
2. **Entry Point**: CLI command `coscientist-interact` for easy access
3. **Namespace Clarity**: Clearly part of coscientist ecosystem
4. **Professional**: Follows Python packaging best practices

### Package Structure

```
coscientist_interact/
├── __init__.py                  ← Package initialization
├── tournament_viewer.py         ← Main Streamlit app (entry point)
├── background.py                ← Background execution & status tracking
├── common.py                    ← Shared utilities & state management
├── configuration_page.py         ← Configuration UI page
├── final_report_page.py         ← Final report viewer
├── literature_review_page.py    ← Literature review viewer
├── meta_reviews_page.py         ← Meta-review viewer
├── proximity_page.py            ← Similarity graph viewer
├── resume_page.py               ← Resume functionality & background processes
├── supervisor_page.py           ← Supervisor decisions viewer
└── tournament_page.py          ← Tournament rankings viewer
```

**Key components**:
- `background.py`: Executes research in background, tracks status, manages process lifecycle
- `resume_page.py`: UI for resuming interrupted research, background process management
- `common.py`: Loads checkpoints, manages state, gets available goals

---

## Usage Examples

### Running Research

```python
# tests/test_simple.py
import asyncio
from coscientist.framework import CoscientistConfig, CoscientistFramework
from coscientist.global_state import CoscientistState, CoscientistStateManager

goal = "What is CRISPR gene editing?"
state = CoscientistState(goal=goal)
config = CoscientistConfig()
state_manager = CoscientistStateManager(state)
framework = CoscientistFramework(config, state_manager)

final_report, meta_review = asyncio.run(framework.run())
```

### Viewing Results

```bash
# Launch viewer
coscientist-interact

# Or with streamlit
streamlit run coscientist_interact/tournament_viewer.py
```

### Checking Progress

```python
from coscientist.global_state import CoscientistState

# List all research goals
goals = CoscientistState.list_all_goals()

# Load latest state for a goal
state = CoscientistState.load_latest(goal="What is CRISPR...")

# Check progress
print(f"Hypotheses: {len(state.reviewed_hypotheses)}")
print(f"Actions: {state.actions}")
```

---

## Future Enhancements

1. **CLI Command**: `coscientist-research <goal>` for command-line execution
2. **Progress API**: REST endpoint for status checking
3. **Webhooks**: Notification system for completed research
4. **Batch Processing**: Run multiple research goals in parallel
5. **Export**: Export results to various formats (PDF, Markdown, etc.)

---

This structure ensures the project is professional, maintainable, and easy to use.
