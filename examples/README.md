# Examples

Example scripts demonstrating how to use Coscientist for research tasks.

## Example 1: Basic Research Task

**File**: `example_CRISPR_gene_question.py`

Demonstrates running a complete research task from start to finish.

### Usage

```bash
# Run the example
python examples/example_CRISPR_gene_question.py

# Or make it executable and run directly
chmod +x examples/example_CRISPR_gene_question.py
./examples/example_CRISPR_gene_question.py
```

### What It Does

1. **Starts research** on the CRISPR gene editing question
2. **Conducts literature review** using GPT Researcher
3. **Generates hypotheses** through multiple reasoning approaches
4. **Ranks hypotheses** via tournament-style competition
5. **Generates meta-reviews** for strategic insights
6. **Produces final report** with comprehensive analysis

### Monitoring Progress

While research is running, monitor in another terminal:

```bash
# Monitor progress in real-time
coscientist-monitor "What is CRISPR gene editing and how does it work?"

# Or list all research
coscientist-list
```

### Resuming After Interruption

If research is interrupted (Ctrl+C, crash, etc.):

```bash
# Resume from checkpoint
python examples/example_CRISPR_gene_question.py resume
```

Or in code:

```python
from coscientist.framework import CoscientistConfig, CoscientistFramework
from coscientist.global_state import CoscientistState, CoscientistStateManager

goal = "What is CRISPR gene editing and how does it work?"
state = CoscientistState.load_latest(goal=goal)

config = CoscientistConfig()
state_manager = CoscientistStateManager(state)
cosci = CoscientistFramework(config, state_manager)

final_report, meta_review = asyncio.run(cosci.run())
```

## Example 2: Custom Storage Location

Want to store research data elsewhere?

```python
import os

# Set custom storage location
os.environ["COSCIENTIST_DIR"] = "./my_research_data"

# Now run research as normal
# Data will be saved to ./my_research_data/<hash>/
```

## Example 3: Quick Progress Check

Check if a specific research is still running:

```python
from coscientist.global_state import CoscientistState

# Load the state
goal = "What is CRISPR gene editing and how does it work?"
state = CoscientistState.load_latest(goal=goal)

if state:
    print(f"✅ Loaded: {len(state.reviewed_hypotheses)} hypotheses reviewed")
    print(f"📊 Progress: {len(state.actions)} actions taken")
    print(f"{'✅ Finished' if state.final_report else '⏳ Still running'}")
else:
    print("❌ No state found")
```

## Viewing Results

After research completes:

```bash
# Launch interactive UI
coscientist-interact

# Then explore:
# - Tournament Rankings: See which hypotheses scored highest
# - Proximity Graph: Visualize semantic relationships
# - Meta-Reviews: Read strategic insights
# - Final Report: Complete analysis
```

## Tips

1. **Monitor progress**: Always run `coscientist-monitor` in another terminal
2. **Resume capability**: Research auto-saves checkpoints - safe to interrupt
3. **Storage location**: Set `COSCIENTIST_DIR` to organize your research
4. **Multiple projects**: Each unique goal gets its own hash directory
5. **Cancel anytime**: Ctrl+C is safe - can always resume later

