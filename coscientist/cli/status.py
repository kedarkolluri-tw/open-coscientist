#!/usr/bin/env python3
"""
Check the status of a research task.

Usage:
    coscientist-status <directory>
    
Examples:
    coscientist-status ~/.coscientist/research_20251025_143000
    coscientist-status research_20251025_143000
"""

import sys
import os
from pathlib import Path

from coscientist.global_state import CoscientistState
from coscientist.status_manager import get_research_status, ResearchStatus


def get_status(directory: str) -> str:
    """
    Check the status of a research directory.
    
    Parameters
    ----------
    directory : str
        Path to the research directory (full path or directory name)
    
    Returns one of:
    - "new" - No research started
    - "initializing" - Research initializing
    - "running" - Research in progress
    - "paused" - Research paused (can resume)
    - "error" - Research failed
    - "completed" - Research finished
    - "not_found" - Directory not found
    """
    # Handle relative paths
    if not os.path.isabs(directory):
        coscientist_dir = os.environ.get("COSCIENTIST_DIR", os.path.expanduser("~/.coscientist"))
        directory = os.path.join(coscientist_dir, directory)
    
    if not os.path.exists(directory):
        return "not_found"
    
    try:
        status, details = get_research_status(directory)
        return status.value
    except:
        return "unknown"




def main():
    if len(sys.argv) < 2:
        print("Usage: coscientist-status <directory>")
        print("\nExamples:")
        print("  coscientist-status ~/.coscientist/research_20251025_143000")
        print("  coscientist-status research_20251025_143000")
        sys.exit(1)
    
    directory = sys.argv[1]
    status = get_status(directory)
    
    print(f"\n📊 Status for: {directory}\n")
    
    if status == "not_found":
        print("❌ Not found: No research started for this goal")
    elif status == "initial":
        print("⏳ Initial: Directory created but research hasn't started")
    elif status == "running":
        print("🔄 Research is currently running")
    elif status == "paused":
        print("⏸️  Research is paused (can resume)")
    elif status == "completed":
        print("✅ Research completed successfully")
    elif status == "error":
        print("❌ Research encountered an error")
    else:
        print(f"📊 Status: {status}")
    
    print()


if __name__ == "__main__":
    main()

