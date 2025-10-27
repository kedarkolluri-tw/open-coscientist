"""
Agent state tracking callbacks for LangGraph/LangChain.
Emits events for every agent invocation to enable Airflow-style monitoring.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult


class AgentStateEvent:
    """A single agent state event."""
    
    def __init__(
        self,
        agent_name: str,
        event_type: str,  # "agent_start", "agent_complete", "node_start", "node_complete"
        node_name: Optional[str] = None,
        state_snapshot: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        duration_ms: Optional[float] = None,
    ):
        self.timestamp = datetime.now()
        self.agent_name = agent_name
        self.event_type = event_type
        self.node_name = node_name
        self.state_snapshot = state_snapshot or {}
        self.error = error
        self.duration_ms = duration_ms
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "agent_name": self.agent_name,
            "event_type": self.event_type,
            "node_name": self.node_name,
            "state_keys": list(self.state_snapshot.keys()) if self.state_snapshot else [],
            "error": self.error,
            "duration_ms": self.duration_ms,
        }
    
    def __repr__(self):
        return f"AgentStateEvent({self.agent_name}:{self.node_name or 'N/A'}:{self.event_type})"


class AgentStateTracker(BaseCallbackHandler):
    """
    Callback handler that tracks agent state for live monitoring.
    
    Usage:
        tracker = AgentStateTracker(output_dir)
        state = agent.invoke(input_state, config={"callbacks": [tracker]})
    """
    
    def __init__(self, output_dir: str, agent_name: str):
        self.output_dir = Path(output_dir)
        self.agent_name = agent_name
        self.events_file = self.output_dir / "agent_events.jsonl"
        self.current_invocation = None
        self.start_time = None
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Write initial event
        self._write_event(AgentStateEvent(
            agent_name=agent_name,
            event_type="tracker_initialized",
        ))
    
    def _write_event(self, event: AgentStateEvent):
        """Write event to JSONL file."""
        with open(self.events_file, 'a') as f:
            f.write(json.dumps(event.to_dict()) + '\n')
            f.flush()
    
    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: list[str],
        **kwargs: Any
    ) -> None:
        """Called when LLM starts."""
        # This is called for LLM invocations within the graph
        pass
    
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Called when LLM completes."""
        pass
    
    def on_llm_error(self, error: Exception, **kwargs: Any) -> None:
        """Called when LLM errors."""
        duration_ms = None
        if self.start_time:
            duration_ms = (time.time() - self.start_time) * 1000
        
        self._write_event(AgentStateEvent(
            agent_name=self.agent_name,
            event_type="agent_error",
            error=str(error),
            duration_ms=duration_ms,
        ))
    
    def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        **kwargs: Any
    ) -> None:
        """Called when a chain/node starts."""
        node_name = serialized.get("name", "unknown")
        
        # This is the actual node execution start
        self._write_event(AgentStateEvent(
            agent_name=self.agent_name,
            event_type="node_start",
            node_name=node_name,
            state_snapshot=inputs,  # Full state at node start
        ))
        
        self.start_time = time.time()
    
    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """Called when a chain/node completes."""
        duration_ms = None
        if self.start_time:
            duration_ms = (time.time() - self.start_time) * 1000
        
        self._write_event(AgentStateEvent(
            agent_name=self.agent_name,
            event_type="node_complete",
            duration_ms=duration_ms,
        ))
    
    def on_chain_error(self, error: Exception, **kwargs: Any) -> None:
        """Called when a chain/node errors."""
        duration_ms = None
        if self.start_time:
            duration_ms = (time.time() - self.start_time) * 1000
        
        self._write_event(AgentStateEvent(
            agent_name=self.agent_name,
            event_type="node_error",
            error=str(error),
            duration_ms=duration_ms,
        ))


def create_tracker(output_dir: str, agent_name: str) -> AgentStateTracker:
    """Create a tracker for an agent invocation."""
    return AgentStateTracker(output_dir, agent_name)

