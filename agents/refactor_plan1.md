# Agent-Centric Configuration Refactor Plan

**Date**: 2025-01-24
**Status**: PLANNED (Not yet implemented)
**Effort Estimate**: 6-8 hours

## Problem Statement

Currently, the codebase has a confusing configuration architecture where:

1. **Framework decides for agents**: `CoscientistConfig` passes LLMs to agents
2. **Unclear ownership**: researcher_config.json has `FAST_LLM`, `SMART_LLM`, etc. but it's unclear which agent uses which
3. **No per-agent tuning**: All agents share the same LLM pool, can't customize temperature/tokens per agent
4. **Implicit dependencies**: Agents don't know what they need, framework guesses

### Current Flow (BAD)
```
researcher_config.json
  ↓
config_loader.py creates LLM pool
  ↓
CoscientistConfig assigns LLMs to agent groups
  ↓
framework.py passes LLMs to agent builders
  ↓
Agents use whatever LLM they're given
```

## Desired End State

**Each agent is self-contained and self-configuring:**
- Knows what model it needs
- Knows its temperature/max_tokens
- Knows which prompt file to use
- Reads its own config section
- Creates its own LLM instance

### Target Flow (GOOD)
```
agents_config.json (single source of truth)
  ↓
Agent builder reads its own section
  ↓
Agent creates its own LLM
  ↓
Agent loads its own prompt
  ↓
Framework just orchestrates, doesn't configure
```

## New Configuration Structure

### agents_config.json (NEW FILE)
```json
{
  "agents": {
    "generation_independent": {
      "description": "Generates hypothesis independently using literature review",
      "llm": {
        "provider": "google_genai",
        "model": "gemini-2.5-flash",
        "temperature": 0.7,
        "max_tokens": 16000,
        "max_retries": 3
      },
      "prompt_file": "prompts/independent_generation.md",
      "enabled": true
    },

    "generation_collaborative": {
      "description": "Multi-agent collaborative hypothesis generation",
      "llm": {
        "provider": "google_genai",
        "model": "gemini-2.5-flash",
        "temperature": 0.8,
        "max_tokens": 16000,
        "max_retries": 3
      },
      "prompt_file": "prompts/collaborative_generation.md",
      "enabled": true,
      "multi_agent_config": {
        "max_turns": 10,
        "agent_count": 3
      }
    },

    "reflection": {
      "description": "Deep verification and critique of hypotheses",
      "llm": {
        "provider": "google_genai",
        "model": "gemini-2.5-flash",
        "temperature": 0.3,
        "max_tokens": 8000,
        "max_retries": 3
      },
      "prompt_file": "prompts/deep_verification.md",
      "enabled": true
    },

    "evolution_feedback": {
      "description": "Evolves hypothesis based on reflection feedback",
      "llm": {
        "provider": "google_genai",
        "model": "gemini-2.5-flash",
        "temperature": 0.6,
        "max_tokens": 12000,
        "max_retries": 3
      },
      "prompt_file": "prompts/evolve_from_feedback.md",
      "enabled": true
    },

    "evolution_creative": {
      "description": "Generates creative out-of-the-box ideas",
      "llm": {
        "provider": "google_genai",
        "model": "gemini-2.5-flash",
        "temperature": 0.9,
        "max_tokens": 12000,
        "max_retries": 3
      },
      "prompt_file": "prompts/out_of_the_box.md",
      "enabled": true
    },

    "meta_review": {
      "description": "Reviews all hypotheses and provides strategic guidance",
      "llm": {
        "provider": "google_genai",
        "model": "gemini-2.5-flash",
        "temperature": 0.5,
        "max_tokens": 50000,
        "max_retries": 3
      },
      "prompt_file": "prompts/meta_review.md",
      "enabled": true
    },

    "supervisor": {
      "description": "Orchestrates the overall research workflow",
      "llm": {
        "provider": "google_genai",
        "model": "gemini-2.5-flash",
        "temperature": 0.4,
        "max_tokens": 8000,
        "max_retries": 3
      },
      "prompt_file": "prompts/supervisor.md",
      "enabled": true
    },

    "final_report": {
      "description": "Generates final research report",
      "llm": {
        "provider": "google_genai",
        "model": "gemini-2.5-flash",
        "temperature": 0.6,
        "max_tokens": 16000,
        "max_retries": 3
      },
      "prompt_file": "prompts/final_report.md",
      "enabled": true
    },

    "literature_review": {
      "description": "Decides research subtopics for GPTResearcher",
      "llm": {
        "provider": "google_genai",
        "model": "gemini-2.5-flash",
        "temperature": 0.5,
        "max_tokens": 8000,
        "max_retries": 3
      },
      "enabled": true
    },

    "ranking": {
      "description": "Runs tournaments to rank hypotheses",
      "llm": {
        "provider": "google_genai",
        "model": "gemini-2.5-flash",
        "temperature": 0.3,
        "max_tokens": 8000,
        "max_retries": 3
      },
      "prompt_file": "prompts/hypothesis_comparison.md",
      "enabled": true
    }
  },

  "embeddings": {
    "proximity_agent": {
      "provider": "google_genai",
      "model": "models/text-embedding-004"
    }
  },

  "gpt_researcher": {
    "config_file": "coscientist/researcher_config.json"
  }
}
```

## Refactoring Steps

### Phase 1: Create Agent Config Infrastructure (2 hours)

**1.1 Create agents_config.json**
- Location: `coscientist/agents_config.json`
- Copy structure from above
- Start with all agents using same model (gemini-2.5-flash)

**1.2 Update config_loader.py**

Add new functions:
```python
def load_agent_config(agent_name: str) -> dict:
    """Load config for a specific agent."""
    pass

def create_agent_llm(agent_name: str) -> BaseChatModel:
    """Create LLM for a specific agent from its config."""
    pass

def get_agent_prompt_path(agent_name: str) -> str:
    """Get prompt file path for an agent."""
    pass
```

**1.3 Add validation**
```python
def validate_agent_config(agent_name: str):
    """Validate agent config and test LLM with real API call."""
    pass
```

### Phase 2: Refactor Agent Builders (3 hours)

**Current pattern:**
```python
def build_generation_agent(
    field: str,
    reasoning_type: ReasoningType,
    llm: BaseChatModel  # ← Passed in
) -> StateGraph:
    ...
```

**Target pattern:**
```python
def build_generation_agent(
    mode: str,  # "independent" or "collaborative"
    field: str = None,
    reasoning_type: ReasoningType = None,
    config_override: dict = None  # For testing
) -> StateGraph:
    """
    Build generation agent. Agent reads its own config.

    Parameters
    ----------
    mode : str
        "independent" or "collaborative"
    field : str, optional
        Override specialist field from config
    reasoning_type : ReasoningType, optional
        Override reasoning type from config
    config_override : dict, optional
        For testing: override entire config
    """
    # Agent reads its own config
    agent_name = f"generation_{mode}"
    config = config_override or load_agent_config(agent_name)

    # Agent creates its own LLM
    llm = create_agent_llm(agent_name)

    # Load prompt from config
    prompt_path = get_agent_prompt_path(agent_name)

    # Build agent...
```

**Files to update:**
- `coscientist/generation_agent.py`
- `coscientist/reflection_agent.py`
- `coscientist/evolution_agent.py`
- `coscientist/meta_review_agent.py`
- `coscientist/supervisor_agent.py`
- `coscientist/final_report_agent.py`
- `coscientist/literature_review_agent.py`
- `coscientist/ranking_agent.py`

### Phase 3: Simplify Framework (1.5 hours)

**3.1 Remove LLM management from CoscientistConfig**

Before:
```python
class CoscientistConfig:
    def __init__(
        self,
        literature_review_agent_llm: BaseChatModel = None,
        generation_agent_llms: dict[str, BaseChatModel] = None,
        ...
    ):
        self.literature_review_agent_llm = ...
        self.generation_agent_llms = ...
```

After:
```python
class CoscientistConfig:
    def __init__(
        self,
        specialist_fields: list[str] = None,
        agents_config_path: str = None
    ):
        """
        Framework config. Agents configure themselves.

        Parameters
        ----------
        specialist_fields : list[str]
            Fields for generation agents
        agents_config_path : str
            Override path to agents_config.json (for testing)
        """
        self.specialist_fields = specialist_fields or ["biology"]
        self.agents_config_path = agents_config_path
```

**3.2 Update CoscientistFramework**

Remove all LLM passing:
```python
# Before
agent = build_generation_agent(field, reasoning_type, llm)

# After
agent = build_generation_agent("independent", field=field, reasoning_type=reasoning_type)
```

### Phase 4: Update Tests (1 hour)

**4.1 Update test_me.py**
```python
# Before
config = CoscientistConfig()

# After (exactly the same!)
config = CoscientistConfig()
```

**4.2 Add config validation test**
```python
def test_agent_config_validation():
    """Test each agent's config is valid."""
    for agent_name in get_all_agent_names():
        validate_agent_config(agent_name)
```

**4.3 Add override test**
```python
def test_agent_config_override():
    """Test we can override config for testing."""
    override = {
        "llm": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.5,
            "max_tokens": 8000
        }
    }
    agent = build_generation_agent("independent", config_override=override)
    # Verify agent uses override...
```

### Phase 5: Migration & Cleanup (0.5 hours)

**5.1 Deprecate old config**
- Keep `researcher_config.json` for gpt-researcher only
- Move to minimal format:
```json
{
  "RETRIEVER": "tavily",
  "FAST_LLM": "google_genai:gemini-2.5-flash",
  "SMART_LLM": "google_genai:gemini-2.5-flash",
  "STRATEGIC_LLM": "google_genai:gemini-2.5-flash",
  "EMBEDDING": "google_genai:models/text-embedding-004"
}
```

**5.2 Update documentation**
- README: How to configure agents
- Comment in agents_config.json explaining each field

**5.3 Remove dead code**
- `_CONFIG_LLMS` and `_LLM_POOL` from framework.py
- Old validation code

## Benefits After Refactor

### Clarity
✅ **One agent = one config section**: Crystal clear what each agent uses
✅ **Self-documenting**: Config file shows all agents and their settings
✅ **Easy to modify**: Want to use Claude for reflection? Just change that one section

### Flexibility
✅ **Per-agent tuning**: Different temperature/tokens for each agent
✅ **Mix providers**: Use OpenAI for some agents, Gemini for others
✅ **Easy A/B testing**: Override config for experiments

### Maintainability
✅ **No framework coupling**: Agents don't depend on framework passing LLMs
✅ **Testable**: Can test agents in isolation with override configs
✅ **Fail fast**: Validation catches bad configs before expensive operations

### Example Use Cases

**Use Claude for creative tasks:**
```json
"evolution_creative": {
  "llm": {
    "provider": "anthropic",
    "model": "claude-sonnet-4-20250514",
    "temperature": 0.9
  }
}
```

**Use o1 for complex reasoning:**
```json
"reflection": {
  "llm": {
    "provider": "openai",
    "model": "o1-preview",
    "temperature": 1.0
  }
}
```

**Disable expensive agents for quick testing:**
```json
"evolution_creative": {
  "enabled": false
}
```

## Backward Compatibility

The refactor will be **backward compatible** at the framework level:

```python
# This still works the same way
config = CoscientistConfig()
framework = CoscientistFramework(config, state_manager)
framework.run()
```

Only internal implementation changes. Tests should pass without modification.

## Testing Strategy

1. **Unit tests**: Each agent builder with override configs
2. **Integration test**: Full framework run with agents_config.json
3. **A/B test**: Run same goal with old vs new config, compare results
4. **Validation test**: Ensure all agents validate successfully

## Rollout Plan

1. ✅ Create agents_config.json
2. ✅ Update config_loader.py with agent functions
3. ✅ Refactor ONE agent (generation) as proof of concept
4. ✅ Test that one agent works end-to-end
5. ✅ Refactor remaining agents
6. ✅ Update framework.py
7. ✅ Run full integration test
8. ✅ Update documentation
9. ✅ Clean up old code

## Success Criteria

- [ ] All agents read their own config
- [ ] Can run full framework with agents_config.json only
- [ ] Can override any agent's config for testing
- [ ] Validation catches misconfigured agents immediately
- [ ] Each agent's temperature/tokens are documented and tunable
- [ ] No LLM passing in framework.py
- [ ] All existing tests pass without modification

## Future Enhancements

After this refactor, we can easily add:

1. **Runtime agent selection**: Enable/disable agents via config
2. **Agent composition**: Build new workflows by combining agents
3. **Agent marketplace**: Share agent configs
4. **Cost tracking**: Track costs per agent
5. **Performance tuning**: A/B test different model configs per agent

---

## Notes

- This is a REFACTOR, not a rewrite. Core agent logic stays the same.
- Focus on configuration architecture, not agent algorithms.
- Prioritize clarity over cleverness.
- Make it work, then make it pretty.
