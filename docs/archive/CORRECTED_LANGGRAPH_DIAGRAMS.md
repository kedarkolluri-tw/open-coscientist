# How Co-Scientist Actually Works: The Real Execution Flow

## Main Loop: What Actually Happens

```mermaid
graph TB
    START[User Starts Research] --> INIT[Create Framework]
    INIT --> LITERATURE[Literature Review Agent<br/>LangGraph executes: topic → research]
    LITERATURE --> GENERATE[Generate Agent<br/>LangGraph executes: generation → parser]
    GENERATE --> RANK[Tournament Ranks Hypotheses]
    RANK --> LOOP
    
    LOOP[Supervisor Loop Iteration] --> SUPERVISOR[Supervisor Agent<br/>LangGraph: analyzes state → decides action]
    
    SUPERVISOR --> CHOICE{Supervisor Decision}
    
    CHOICE -->|generate_new| GENERATE
    CHOICE -->|evolve| EVOLVE[Evolution Agent<br/>LangGraph: refines hypotheses]
    CHOICE -->|tournament| RANK
    CHOICE -->|reflection| REFLECT[Reflection Agent<br/>LangGraph: multi-step verification]
    CHOICE -->|meta_review| META[Meta-Review Agent<br/>LangGraph: synthesis]
    CHOICE -->|finish| FINAL[Final Report Agent<br/>LangGraph: report generation]
    
    GENERATE --> UPDATE[Update Global State]
    EVOLVE --> UPDATE
    RANK --> UPDATE
    REFLECT --> UPDATE
    META --> UPDATE
    FINAL --> DONE
    
    UPDATE --> CHECK{Finished?}
    CHECK -->|No| LOOP
    CHECK -->|Yes| DONE[Done: Return Results]
    
    classDef userNode fill:#fff9c4,stroke:#f9a825,stroke-width:3px
    classDef decisionNode fill:#c8e6c9,stroke:#388e3c,stroke-width:2px
    classDef agentNode fill:#e1f5fe,stroke:#0277bd,stroke-width:2px
    classDef stateNode fill:#ffebee,stroke:#c62828,stroke-width:2px
    
    class START,INIT,DONE userNode
    class CHOICE,CHECK decisionNode
    class LITERATURE,SUPERVISOR,GENERATE,EVOLVE,RANK,REFLECT,META,FINAL agentNode
    class UPDATE,LOOP stateNode
```

## Key Points:

1. **No agent calls another agent** - Agents never directly invoke each other
2. **Supervisor is a "traffic controller"** - It's a LangGraph that analyzes system state and picks ONE action from 6 hardcoded options
3. **Framework executes the action** - After supervisor decides, framework calls the corresponding method (e.g., `await self.generate_new_hypotheses()`)
4. **State is global** - All agents read/write to CoscientistStateManager
5. **No cross-agent composition** - Framework can't create custom workflows spanning multiple agents

## What "Supervisor Decision" Actually Means:

The supervisor agent is like a **traffic controller** that:
- Analyzes current research state (hypotheses, rankings, meta-reviews, etc.)
- Uses an LLM to decide what to do next
- Returns ONE action from this hardcoded list:
  - `generate_new_hypotheses` → calls Generation Agent
  - `evolve_hypotheses` → calls Evolution Agent  
  - `run_tournament` → runs tournament ranking
  - `run_meta_review` → calls Meta-Review Agent
  - `expand_literature_review` → calls Literature Review Agent
  - `finish` → calls Final Report Agent

**Yes, the supervisor DOES invoke other agents** - it's just that the framework code handles the actual `.invoke()` calls. The supervisor is the "brain" that decides which agent to run next.

## Framework Architecture:

- **CoscientistFramework** = Custom Python class (NOT LangGraph/LangChain)
- **Individual Agents** = LangGraph StateGraphs (built with LangGraph)
- **Framework orchestration** = Custom Python while loop + method dispatch

So the architecture is:
- **LangGraph**: Used for individual agent workflows (each agent is a StateGraph)
- **Custom Python**: Used for the main orchestration loop and agent coordination
- **LangChain**: Used for LLM interfaces and embeddings

## What This Means:

- ✅ **Good**: Each agent internally is dynamic with complex LangGraph workflows
- ❌ **Bad**: Framework can't compose agents into larger dynamic workflows
- ❌ **Bad**: No conditional orchestration (e.g., "if quality < X, run reflection")
- ❌ **Bad**: All orchestration is hardcoded in the framework's `available_actions()` method

## Code Reference

If you want to see the actual LangGraph code for individual agents:

- **Supervisor Agent**: `coscientist/supervisor_agent.py::build_supervisor_agent()`
- **Literature Review Agent**: `coscientist/literature_review_agent.py::build_literature_review_agent()`
- **Generation Agent**: `coscientist/generation_agent.py::build_generation_agent()`
- **Reflection Agent**: `coscientist/reflection_agent.py::build_deep_verification_agent()`
- **Evolution Agent**: `coscientist/evolution_agent.py::build_evolution_agent()`
- **Meta-Review Agent**: `coscientist/meta_review_agent.py::build_meta_review_agent()`
- **Final Report Agent**: `coscientist/final_report_agent.py::build_final_report_agent()`
- **Framework Loop**: `coscientist/framework.py::run()` (line 496)
- **Global State**: `coscientist/global_state.py::CoscientistStateManager`
