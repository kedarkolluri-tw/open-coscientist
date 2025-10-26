"""
Status Management for Coscientist Research Tasks

Provides simple, atomic status tracking that doesn't depend on state object internals.
"""

import os
import json
from pathlib import Path
from enum import Enum
from datetime import datetime
from typing import Optional


class ResearchStatus(str, Enum):
    """Research status states."""
    NEW = "new"           # No research started
    INITIALIZING = "initializing"  # State created, starting research
    RUNNING = "running"   # Research in progress
    PAUSED = "paused"     # Research paused (can resume)
    ERROR = "error"       # Research failed
    COMPLETED = "completed"  # Research finished


class StatusManager:
    """
    Manages research status in a simple, atomic way.
    
    Uses a single `status.json` file per research task that contains:
    - status: current status
    - last_updated: timestamp
    - error: error message if status is ERROR
    """
    
    def __init__(self, output_dir: str):
        """
        Initialize status manager.
        
        Parameters
        ----------
        output_dir : str
            The research output directory
        """
        self.output_dir = output_dir
        self.status_file = os.path.join(output_dir, "status.json")
    
    def update_status(self, status: ResearchStatus, error: Optional[str] = None) -> None:
        """
        Update research status atomically.
        
        Parameters
        ----------
        status : ResearchStatus
            The new status
        error : str, optional
            Error message if status is ERROR
        """
        status_data = {
            "status": status.value,
            "last_updated": datetime.now().isoformat(),
        }
        
        if error:
            status_data["error"] = error
        
        # Atomic write
        with open(self.status_file, "w") as f:
            json.dump(status_data, f, indent=2)
    
    def get_status(self) -> tuple[ResearchStatus, dict]:
        """
        Get current research status.
        
        Returns
        -------
        tuple[ResearchStatus, dict]
            Status enum and additional details (last_updated, error, etc.)
        """
        if not os.path.exists(self.status_file):
            return ResearchStatus.NEW, {}
        
        with open(self.status_file, "r") as f:
            data = json.load(f)
        
        status = ResearchStatus(data.get("status", "new"))
        details = {k: v for k, v in data.items() if k != "status"}
        
        return status, details
    
    def is_completed(self) -> bool:
        """Check if research is completed."""
        status, _ = self.get_status()
        return status == ResearchStatus.COMPLETED
    
    def is_running(self) -> bool:
        """Check if research is currently running."""
        status, _ = self.get_status()
        return status == ResearchStatus.RUNNING
    
    def has_error(self) -> bool:
        """Check if research encountered an error."""
        status, _ = self.get_status()
        return status == ResearchStatus.ERROR


def get_research_status(directory: str) -> tuple[ResearchStatus, dict]:
    """
    Get status for a research directory.
    
    Parameters
    ----------
    directory : str
        Full path to the research directory
    
    Returns
    -------
    tuple[ResearchStatus, dict]
        Current status and details
    """
    manager = StatusManager(directory)
    return manager.get_status()

