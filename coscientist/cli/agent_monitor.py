#!/usr/bin/env python3
"""
Airflow-style agent state monitor.
Shows live DAG of agent invocations and their current state.
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

# Import _OUTPUT_DIR without importing global_state module
# This avoids loading LLM config at import time
_OUTPUT_DIR = os.environ.get("COSCIENTIST_DIR", os.path.expanduser("~/.coscientist"))


class AgentDAGNode:
    """A node in the agent DAG."""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.nodes: Set[str] = set()
        self.current_node: Optional[str] = None
        self.status: str = "pending"  # pending, running, completed, error
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.duration_ms: Optional[float] = None
        self.error: Optional[str] = None
    
    def update_from_event(self, event: Dict):
        """Update node state from event."""
        event_type = event["event_type"]
        
        if event_type == "tracker_initialized":
            self.status = "initialized"
        
        elif event_type == "node_start":
            node_name = event["node_name"]
            self.nodes.add(node_name)
            self.current_node = node_name
            self.status = "running"
            
            # Parse timestamp
            self.start_time = datetime.fromisoformat(event["timestamp"])
        
        elif event_type == "node_complete":
            if "duration_ms" in event:
                self.duration_ms = event["duration_ms"]
            self.status = "completed"
            
            # Parse timestamp
            if "timestamp" in event:
                self.end_time = datetime.fromisoformat(event["timestamp"])
        
        elif event_type in ("node_error", "agent_error"):
            self.status = "error"
            self.error = event.get("error")
            
            if "timestamp" in event:
                self.end_time = datetime.fromisoformat(event["timestamp"])
    
    def __repr__(self):
        return f"AgentDAGNode({self.agent_name}:{self.status})"


def load_agent_events(directory: str) -> List[Dict]:
    """Load agent events from file."""
    events_file = Path(directory) / "agent_events.jsonl"
    
    if not events_file.exists():
        return []
    
    events = []
    try:
        with open(events_file, 'r') as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line.strip()))
    except Exception as e:
        print(f"Error reading events: {e}", file=sys.stderr)
    
    return events


def build_dag(events: List[Dict]) -> Dict[str, AgentDAGNode]:
    """Build agent DAG from events."""
    dag: Dict[str, AgentDAGNode] = {}
    
    for event in events:
        agent_name = event.get("agent_name")
        if not agent_name:
            continue
        
        if agent_name not in dag:
            dag[agent_name] = AgentDAGNode(agent_name)
        
        dag[agent_name].update_from_event(event)
    
    return dag


def display_dag(dag: Dict[str, AgentDAGNode]):
    """Display agent DAG in Airflow-style format."""
    os.system('clear')  # Clear screen
    
    print("🔬 COSCIENTIST AGENT MONITOR")
    print("=" * 80)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    for agent_name, node in sorted(dag.items()):
        # Color code based on status
        status_icon = {
            "pending": "⏳",
            "initialized": "🔄",
            "running": "▶️",
            "completed": "✅",
            "error": "❌",
        }.get(node.status, "❓")
        
        print(f"{status_icon} {agent_name}")
        print(f"   Status: {node.status}")
        
        if node.current_node:
            print(f"   Current Node: {node.current_node}")
        
        if node.nodes:
            print(f"   Nodes: {', '.join(sorted(node.nodes))}")
        
        if node.start_time:
            print(f"   Started: {node.start_time.strftime('%H:%M:%S')}")
        
        if node.duration_ms:
            print(f"   Duration: {node.duration_ms:.0f}ms")
        
        if node.error:
            print(f"   Error: {node.error[:60]}...")
        
        print()


def monitor_directory(directory: str):
    """Monitor agent events in a directory."""
    print(f"📁 Monitoring: {directory}")
    print(f"Press Ctrl+C to stop")
    print()
    
    last_event_count = 0
    
    try:
        while True:
            events = load_agent_events(directory)
            
            if len(events) > last_event_count:
                dag = build_dag(events)
                display_dag(dag)
                last_event_count = len(events)
            
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n👋 Monitor stopped")


def main():
    if len(sys.argv) < 2:
        print("Usage: agent-monitor <directory>")
        print()
        print("Monitor agent state for a research run.")
        print()
        print("Examples:")
        print("  agent-monitor ~/.coscientist/research_20251026_180000")
        print("  agent-monitor ./research_20251026_180000")
        sys.exit(1)
    
    directory = sys.argv[1]
    
    # Handle relative paths
    if not os.path.isabs(directory):
        directory = os.path.join(_OUTPUT_DIR, directory)
    
    if not os.path.exists(directory):
        print(f"❌ Directory not found: {directory}")
        sys.exit(1)
    
    monitor_directory(directory)


if __name__ == "__main__":
    main()

