"""
Live monitor for research progress.
Shows user-friendly progress from progress.json file.
"""

import json
import os
import sys
import time
from datetime import datetime


def tail_progress_file(directory: str):
    """Monitor progress.json file and display live updates."""
    progress_file = os.path.join(directory, "progress.json")
    
    if not os.path.exists(progress_file):
        print(f"❌ Progress file not found: {progress_file}")
        print(f"📁 Directory: {directory}")
        sys.exit(1)
    
    print(f"📊 Live Progress Monitor")
    print(f"📁 Watching: {directory}\n")
    print("=" * 80)
    
    events_read = set()
    
    try:
        while True:
            # Read all events from file
            try:
                with open(progress_file, 'r') as f:
                    events = []
                    for line in f:
                        if line.strip():
                            events.append(json.loads(line.strip()))
                
                # Display new events
                for event in events:
                    event_id = f"{event['timestamp']}_{event['phase']}_{event.get('task', '')}"
                    if event_id not in events_read:
                        display_event(event)
                        events_read.add(event_id)
                
                # Keep only last 100 events in memory
                if len(events_read) > 100:
                    events_read = set(list(events_read)[-50:])
                
            except json.JSONDecodeError:
                pass  # File might be incomplete, wait
            except FileNotFoundError:
                print("⚠️  Progress file removed")
                break
            
            time.sleep(2)  # Check every 2 seconds
            
    except KeyboardInterrupt:
        print("\n✅ Monitoring stopped")


def display_event(event: dict):
    """Display a single progress event in human-readable format."""
    timestamp = event['timestamp']
    event_type = event['event_type']
    phase = event['phase']
    task = event.get('task', '')
    details = event['details']
    progress = event.get('progress')
    
    # Format timestamp
    try:
        dt = datetime.fromisoformat(timestamp)
        time_str = dt.strftime("%H:%M:%S")
    except:
        time_str = timestamp[:8]
    
    # Format based on event type
    if event_type == "PHASE_START":
        print(f"\n🚀 [{time_str}] Starting: {phase}")
        print(f"   {details}")
        
    elif event_type == "PHASE_COMPLETE":
        print(f"\n✅ [{time_str}] Completed: {phase}")
        print(f"   {details}")
        
    elif event_type == "TASK_START":
        print(f"\n▶️  [{time_str}] {phase} - {task}: Starting")
        if details:
            print(f"   {details}")
            
    elif event_type == "TASK_COMPLETE":
        progress_pct = f" ({progress}%)" if progress else ""
        print(f"\n✓ [{time_str}] {phase} - {task}: Done{progress_pct}")
        if details and details != "Complete":
            print(f"   {details}")
            
    elif event_type == "PROGRESS_UPDATE":
        progress_bar = "█" * (progress // 5) + "░" * (20 - (progress // 5))
        print(f"   [{time_str}] {progress_bar} {progress}% - {details}")


def list_all_directories():
    """List all research directories."""
    base_dir = os.environ.get("COSCIENTIST_DIR", os.path.expanduser("~/.coscientist"))
    
    if not os.path.exists(base_dir):
        print("❌ No research directories found")
        return []
    
    dirs = []
    for item in os.listdir(base_dir):
        item_path = os.path.join(base_dir, item)
        progress_file = os.path.join(item_path, "progress.json")
        
        if os.path.isdir(item_path) and os.path.exists(progress_file):
            dirs.append((item, item_path))
    
    return sorted(dirs, key=lambda x: x[0], reverse=True)  # Newest first


def main():
    """Main entry point for live monitor."""
    if len(sys.argv) < 2:
        # List available directories
        print("📋 Available Research Directories:\n")
        dirs = list_all_directories()
        
        if not dirs:
            print("❌ No research directories found")
            sys.exit(1)
        
        for name, path in dirs[:10]:  # Show top 10
            print(f"📁 {name}")
            print(f"   {path}\n")
        
        print("\nUsage: coscientist-live <directory_name>")
        sys.exit(0)
    
    directory_arg = sys.argv[1]
    
    # Resolve directory path
    if os.path.isabs(directory_arg):
        directory = directory_arg
    else:
        base_dir = os.environ.get("COSCIENTIST_DIR", os.path.expanduser("~/.coscientist"))
        directory = os.path.join(base_dir, directory_arg)
    
    if not os.path.exists(directory):
        print(f"❌ Directory not found: {directory}")
        sys.exit(1)
    
    # Start monitoring
    tail_progress_file(directory)


if __name__ == "__main__":
    main()

