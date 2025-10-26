# 🧪 Open CoScientist Agents

A comprehensive multi-agent system for AI-driven scientific discovery based on Google DeepMind's [AI co-scientist](https://arxiv.org/abs/2502.18864), built with LangGraph and [GPT Researcher](https://github.com/assafelovic/gpt-researcher). The aim is for this system to accelerate scientific research through collaborative AI agents that generate, critique, rank, and evolve scientific hypotheses using tournament-style competition.

This implementation uses `Gemini 2.5 Pro`, `Claude Sonnet 4`, and `o3` in collaboration and competition.

![App Demo](assets/app_demo.gif)

## Key Features

### Multi-Agent Architecture
- **Literature Review Agent**: Systematically decomposes research goals and conducts comprehensive literature analysis
- **Generation Agents**: Create novel scientific hypotheses using multiple reasoning approaches
- **Reflection Agents**: Perform deep verification and causal reasoning analysis
- **Evolution Agents**: Refine and improve hypotheses based on feedback and competition
- **Meta-Review Agent**: Synthesizes insights across multiple research directions
- **Supervisor Agent**: Orchestrates the entire research workflow -- decides which actions to take next and when to finish the research.
- **Final Report Agent**: Generates comprehensive research summaries

### Tournament-Style Hypothesis Competition
- **ELO Rating System**: Ranks hypotheses through head-to-head competitive analysis
- **Debate Transcripts**: Full records of why one hypothesis outperforms another
- **Win-Loss Statistics**: Track performance across multiple evaluation rounds
- **Hypothesis Evolution**: See how ideas improve through iterative refinement

### Interactive Web Interface
- **Streamlit Dashboard**: Comprehensive visualization of research results
- **Real-time Monitoring**: Track research progress and agent activities
- **Hypothesis Explorer**: Deep dive into individual hypotheses and their reasoning
- **Tournament Viewer**: Analyze competitive dynamics between ideas

## Installation

### Prerequisites
- Python 3.12 or higher
- A boatload of API keys

### Install from PyPI (Coming Soon)
```bash
pip install open-coscientist-agents
```

### Install from Source
```bash
git clone https://github.com/conradry/open-coscientist-agents.git
cd open-coscientist-agents
pip install -e .
```

## Configuration

### Environment Variables
Set up your API keys for model providers:
```bash
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
export GOOGLE_API_KEY="your-google-key"
```

Set up your API key for Tavily search:
```bash
export TAVILY_API_KEY='your-api-key'
```

Optional, but highly recommended for monitoring and debugging, set up API keys for LangSmith:
```bash
export LANGSMITH_ENDPOINT="https://api.smith.langchain.com"
export LANGSMITH_API_KEY="your-langsmith-api-key"
export LANGSMITH_PROJECT="your-langsmith-project"
```

### Web Interface
Launch the interactive dashboard:
```bash
cd app
pip install -r viewer_requirements.txt
streamlit run tournament_viewer.py
```

Features include:
- **Configuration Agent**: Set up research parameters
- **Literature Review**: Explore research foundation
- **Tournament Rankings**: View hypothesis competition results
- **Proximity Graph**: Semantic relationship visualization
- **Meta-Reviews**: Synthesized research insights
- **Supervisor Decisions**: Workflow orchestration logs
- **Final Report**: Comprehensive research summary

### Quick Start Example

#### 1. Run a Research Task

```python
# tests/test_simple.py
import asyncio
from coscientist.framework import CoscientistConfig, CoscientistFramework
from coscientist.global_state import CoscientistState, CoscientistStateManager

# Define your research question
goal = "What is CRISPR gene editing and how does it work?"
initial_state = CoscientistState(goal=goal)

# Create framework
config = CoscientistConfig()
state_manager = CoscientistStateManager(initial_state)
cosci = CoscientistFramework(config, state_manager)

# Run research (takes 1-2 hours)
final_report, final_meta_review = asyncio.run(cosci.run())

# Results
print(final_report)
print(final_meta_review)
```

#### 2. Monitor Progress (in another terminal)

```bash
# Start monitoring (in another terminal)
coscientist-monitor "What is CRISPR gene editing and how does it work?"

# Or list all research goals
coscientist-list
```

**Expected output**:
```
📊 Monitoring progress: What is CRISPR gene editing and how does it work?
📁 File: ~/.coscientist/8f3200309e4a/progress.txt

2025-10-25T15:00:00 | START | Literature Review and initial hypothesis generation
2025-10-25T15:05:30 | DONE | Literature review complete, 4 hypotheses generated
2025-10-25T15:05:31 | ITERATION | 1/20: Starting
2025-10-25T15:05:32 | ACTION | generate_new_hypotheses
2025-10-25T15:10:15 | STATUS | 0 reviewed, 8 total hypotheses, 5% complete
2025-10-25T15:10:16 | ITERATION | 2/20: Starting
...
```

#### 3. Resume Interrupted Research

```python
# Resume from last checkpoint
from coscientist.framework import CoscientistConfig, CoscientistFramework
from coscientist.global_state import CoscientistState, CoscientistStateManager

# Load existing state
goal = "What is CRISPR gene editing?"
state = CoscientistState.load_latest(goal=goal)

# Continue where we left off
config = CoscientistConfig()
state_manager = CoscientistStateManager(state)
cosci = CoscientistFramework(config, state_manager)

final_report, meta_review = asyncio.run(cosci.run())
```

#### 4. View Results in UI

```bash
# Launch interactive dashboard
coscientist-interact

# Then navigate to:
# - Tournament Rankings: See hypothesis rankings
# - Proximity Graph: Visualize similarity
# - Meta-Reviews: Read strategic insights
# - Final Report: Complete summary
```

### Custom Storage Location

```bash
# Use custom directory for research data
export COSCIENTIST_DIR=./my_research_data

# Then run research normally
python tests/test_simple.py

# Monitor progress
coscientist-monitor "<your goal>"
```

## Performance & Scalability

In principle, this system can be easily scaled with asynchronous execution of many tasks. In practice, API rate limits make it difficult to run in parallel. Future work will explore ways to get around this by smartly allocating work to different providers.

Currently designed to work with 20-30 hypotheses in a tournament. Scaling that to more will require optimizations like smarter prioritization of head-to-head matches, summarizing context to make meta-review tractable, and actually supporting asynchronous execution.


## Caveats and sharp edges

- The system isn't fully configurable and there are fields that are hardcoded (like number of hypotheses, subtopics for literature review, etc.).
- Obviously no tests or evaluations yet. Getting feedback will help to steer this project in the right direction for research usefulness.

## Contributing

We welcome contributions!

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by Google DeepMind's research on AI-assisted scientific discovery
- Built with [LangGraph](https://github.com/langchain-ai/langgraph) for agent orchestration
- Uses [GPT Researcher](https://github.com/assafelovic/gpt-researcher) for literature analysis
- Visualization powered by [Streamlit](https://streamlit.io/) and [Plotly](https://plotly.com/)
