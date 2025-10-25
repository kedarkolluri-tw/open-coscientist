# Agent Development Guide

This document outlines the standards and patterns for developing agents in the Open CoScientist system.

## Agent Architecture Overview

The CoScientist system uses a multi-agent architecture where different agents specialize in specific aspects of scientific research:

- **Literature Review Agent**: Systematic literature analysis and research decomposition
- **Generation Agents**: Create novel scientific hypotheses using various reasoning approaches
- **Reflection Agents**: Deep verification and causal reasoning analysis
- **Evolution Agents**: Refine and improve hypotheses based on feedback
- **Meta-Review Agent**: Synthesize insights across research directions
- **Supervisor Agent**: Orchestrate the entire research workflow
- **Final Report Agent**: Generate comprehensive research summaries

## Agent Development Standards

### 1. Agent Structure

All agents should follow this standard structure:

```python
from coscientist.common import load_prompt, validate_llm_response, parse_hypothesis_with_llm
from coscientist.custom_types import ParsedHypothesis
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

def build_agent_name(llm: BaseChatModel, **kwargs) -> Agent:
    """
    Build an agent for [specific purpose].
    
    Parameters
    ----------
    llm : BaseChatModel
        The language model to use
    **kwargs
        Additional configuration parameters
        
    Returns
    -------
    Agent
        Configured agent ready for use
    """
    # Agent implementation
    pass
```

### 2. Required Imports

Every agent must import:
- `validate_llm_response` from `coscientist.common` - for response validation
- `load_prompt` from `coscientist.common` - for prompt management
- `parse_hypothesis_with_llm` from `coscientist.common` - for structured parsing
- Relevant custom types from `coscientist.custom_types`

### 3. Response Validation

**CRITICAL**: All agents must validate LLM responses:

```python
def agent_function(state):
    # ... agent logic ...
    
    response = llm.invoke(messages)
    
    # ALWAYS validate response - crashes if empty
    response_content = validate_llm_response(
        response=response,
        agent_name="AgentName",
        prompt=str(messages),
        context={"goal": state.get("goal", "unknown")}
    )
    
    # Process validated response
    return processed_result
```

### 4. Prompt Management

Use the centralized prompt system:

```python
# Load prompts from prompts/ directory
prompt_template = load_prompt("agent_prompt_name", 
    variable1=value1,
    variable2=value2
)

messages = [
    SystemMessage(content=prompt_template),
    HumanMessage(content=user_input)
]
```

### 5. Structured Output Parsing

Use LLM-based parsing for structured data:

```python
# For hypothesis parsing
parsed_hypothesis = parse_hypothesis_with_llm(
    llm=llm,
    text=response_content,
    use_robust_parsing=True
)

# For other structured data
structured_data = parse_with_llm(
    llm=llm,
    text=response_content,
    output_model=YourPydanticModel
)
```

### 6. Error Handling

Agents should fail fast on critical errors:

```python
try:
    # Agent logic
    result = process_data()
except ValidationError as e:
    # Log and re-raise - don't silently continue
    logger.error(f"Validation failed in {agent_name}: {e}")
    raise
except Exception as e:
    # Log unexpected errors
    logger.error(f"Unexpected error in {agent_name}: {e}")
    raise
```

### 7. Logging Standards

Use structured logging:

```python
import logging

logger = logging.getLogger(__name__)

# Log agent actions
logger.info(f"[{agent_name}] Starting {action}")
logger.info(f"[{agent_name}] Processing {len(items)} items")
logger.warning(f"[{agent_name}] Warning: {message}")
logger.error(f"[{agent_name}] Error: {error}")
```

## Agent Types and Patterns

### Generation Agents

Generation agents create new hypotheses using different reasoning approaches:

- **Independent Generation**: Single agent with specific reasoning type
- **Collaborative Generation**: Multiple agents working together
- **Reasoning Types**: Causal, Analogical, Deductive, Inductive, Abductive

### Reflection Agents

Reflection agents perform deep verification:

- **Deep Verification**: Comprehensive hypothesis analysis
- **Causal Reasoning**: Analyze cause-and-effect relationships
- **Assumption Research**: Validate underlying assumptions

### Evolution Agents

Evolution agents improve existing hypotheses:

- **Evolve from Feedback**: Improve based on tournament results
- **Out of the Box**: Generate novel variations

## Configuration Management

All agents use centralized configuration:

```python
from coscientist.config_loader import create_llms_from_config

# Load LLMs from researcher_config.json
llms = create_llms_from_config()
agent_llm = llms['SMART_LLM']  # or FAST_LLM, STRATEGIC_LLM
```

## Testing Standards

Every agent should have comprehensive tests:

```python
# tests/test_agent_name.py
import pytest
from coscientist.agent_name import build_agent_name

def test_agent_basic_functionality():
    """Test basic agent functionality."""
    pass

def test_agent_with_mock_llm():
    """Test agent with mocked LLM responses."""
    pass

def test_agent_error_handling():
    """Test agent error handling."""
    pass
```

## Documentation Requirements

Each agent should have:

1. **Docstring**: Clear description of purpose and parameters
2. **Type Hints**: Complete type annotations
3. **Examples**: Usage examples in docstring
4. **Tests**: Comprehensive test coverage
5. **Prompt Templates**: Well-documented prompts in `prompts/` directory

## Best Practices

1. **Fail Fast**: Validate inputs and crash on configuration errors
2. **Structured Output**: Use Pydantic models for all structured data
3. **Robust Parsing**: Use LLM-based parsing instead of regex
4. **Comprehensive Logging**: Log all important actions and decisions
5. **Error Propagation**: Don't silently swallow errors
6. **Configuration Driven**: Use centralized config, avoid hardcoded values
7. **Test Coverage**: Maintain high test coverage for all agents

## Adding New Agents

When adding a new agent:

1. Create agent file in `coscientist/` directory
2. Add prompt templates to `prompts/` directory
3. Create comprehensive tests in `tests/` directory
4. Update this documentation
5. Add agent to framework configuration
6. Document agent in main README

## Agent Communication Patterns

Agents communicate through the global state manager:

```python
# Reading from state
hypotheses = state_manager.get_hypotheses()
literature_review = state_manager.literature_review

# Writing to state
state_manager.add_hypothesis(new_hypothesis)
state_manager.update_literature_review(review_data)
```

This ensures consistent data flow and state management across all agents.
