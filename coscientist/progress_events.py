"""
Simple progress event system for user visibility.
Not for debugging - purely for showing "where are we now?"
"""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class ProgressEventType(str, Enum):
    """Types of progress events."""
    PHASE_START = "PHASE_START"      # Starting a major phase
    PHASE_COMPLETE = "PHASE_COMPLETE"  # Finished a major phase
    TASK_START = "TASK_START"         # Starting a task
    TASK_COMPLETE = "TASK_COMPLETE"   # Finished a task
    PROGRESS_UPDATE = "PROGRESS_UPDATE"  # Percentage or status update


@dataclass
class ProgressEvent:
    """A single progress event."""
    timestamp: datetime
    event_type: ProgressEventType
    phase: str  # e.g., "literature_review", "hypothesis_generation"
    task: str | None  # e.g., "subtopic_1", "hypothesis_2"
    details: str  # Human-readable description
    progress: int | None = None  # 0-100 if applicable
    
    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "phase": self.phase,
            "task": self.task,
            "details": self.details,
            "progress": self.progress
        }


class ProgressTracker:
    """
    Simple progress tracker that writes to a file.
    Only logs high-level user-relevant events, not technical debug info.
    """
    
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.events_file = f"{output_dir}/progress.json"
        self.events = []
    
    def phase_start(self, phase: str, details: str):
        """Log start of a major phase."""
        event = ProgressEvent(
            timestamp=datetime.now(),
            event_type=ProgressEventType.PHASE_START,
            phase=phase,
            task=None,
            details=details,
            progress=None
        )
        self._log_event(event)
    
    def phase_complete(self, phase: str, details: str):
        """Log completion of a major phase."""
        event = ProgressEvent(
            timestamp=datetime.now(),
            event_type=ProgressEventType.PHASE_COMPLETE,
            phase=phase,
            task=None,
            details=details,
            progress=100
        )
        self._log_event(event)
    
    def task_start(self, phase: str, task: str, details: str):
        """Log start of a task within a phase."""
        event = ProgressEvent(
            timestamp=datetime.now(),
            event_type=ProgressEventType.TASK_START,
            phase=phase,
            task=task,
            details=details,
            progress=None
        )
        self._log_event(event)
    
    def task_complete(self, phase: str, task: str, details: str, progress: int = None):
        """Log completion of a task."""
        event = ProgressEvent(
            timestamp=datetime.now(),
            event_type=ProgressEventType.TASK_COMPLETE,
            phase=phase,
            task=task,
            details=details,
            progress=progress
        )
        self._log_event(event)
    
    def update(self, phase: str, details: str, progress: int):
        """Update progress percentage."""
        event = ProgressEvent(
            timestamp=datetime.now(),
            event_type=ProgressEventType.PROGRESS_UPDATE,
            phase=phase,
            task=None,
            details=details,
            progress=progress
        )
        self._log_event(event)
    
    def _log_event(self, event: ProgressEvent):
        """Write event to file."""
        self.events.append(event)
        
        # Write immediately (no buffering)
        import json
        with open(self.events_file, 'a') as f:
            f.write(json.dumps(event.to_dict()) + '\n')
            f.flush()
    
    def get_recent_events(self, last_n: int = 10) -> list[dict]:
        """Get most recent N events."""
        return [e.to_dict() for e in self.events[-last_n:]]


# Singleton instance (created once per framework)
_tracker = None

def get_tracker(output_dir: str = ".") -> ProgressTracker:
    """Get or create singleton progress tracker."""
    global _tracker
    if _tracker is None:
        _tracker = ProgressTracker(output_dir)
    return _tracker


# Convenience functions
def phase_start(phase: str, details: str, output_dir: str):
    get_tracker(output_dir).phase_start(phase, details)

def phase_complete(phase: str, details: str, output_dir: str):
    get_tracker(output_dir).phase_complete(phase, details)

def task_start(phase: str, task: str, details: str, output_dir: str):
    get_tracker(output_dir).task_start(phase, task, details)

def task_complete(phase: str, task: str, details: str, output_dir: str, progress: int = None):
    get_tracker(output_dir).task_complete(phase, task, details, progress)

def update(phase: str, details: str, progress: int, output_dir: str):
    get_tracker(output_dir).update(phase, details, progress)

