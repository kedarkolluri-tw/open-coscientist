#!/usr/bin/env python3
"""
Monitor research progress in real-time.

Usage:
    python monitor_progress.py <goal>
    
Or if running in background:
    tail -f ~/.coscientist/*/progress.txt
"""

import sys
import os
import time
from pathlib import Path

def find_progress_file(goal: str) -> str:
    """Find the progress file for a given goal."""
    from coscientist.global_state import CoscientistState
    
    coscientist_dir = os.environ.get("COSCIENTIST_DIR", os.path.expanduser("~/.coscientist"))
    normalized_goal = CoscientistState._normalize_goal(goal)
    matching_progress_files = []
    
    # Search all directories for matching goal.txt
    if os.path.exists(coscientist_dir):
        for item in os.listdir(coscientist_dir):
            item_path = os.path.join(coscientist_dir, item)
            if os.path.isdir(item_path):
                goal_file = os.path.join(item_path, "goal.txt")
                progress_file = os.path.join(item_path, "progress.txt")
                
                if os.path.exists(goal_file):
                    try:
                        with open(goal_file, encoding="utf-8") as f:
                            existing_goal = f.read().strip()
                        if CoscientistState._normalize_goal(existing_goal) == normalized_goal and os.path.exists(progress_file):
                            matching_progress_files.append((progress_file, os.path.getmtime(progress_file)))
                    except:
                        continue
    
    if not matching_progress_files:
        return None
    
    # Return most recent progress file
    most_recent = max(matching_progress_files, key=lambda x: x[1])[0]
    return most_recent


def monitor_progress(goal: str):
    """Monitor progress file for a given goal."""
    progress_file = find_progress_file(goal)
    
    if not os.path.exists(progress_file):
        print(f"❌ No progress file found for: {goal}")
        print(f"💡 Trying to find progress file...")
        print(f"    Looking in: {os.environ.get('COSCIENTIST_DIR', os.path.expanduser('~/.coscientist'))}")
        return
    
    print(f"\n📊 Monitoring progress: {goal}")
    print(f"📁 File: {progress_file}\n")
    print("="*80)
    
    # Display existing content
    if os.path.exists(progress_file):
        with open(progress_file, "r") as f:
            lines = f.readlines()
            for line in lines[-20:]:  # Show last 20 lines
                print(line.rstrip())
    
    print("\n" + "="*80)
    print("🔄 Monitoring for updates...\n")
    
    # Tail the file
    with open(progress_file, "r") as f:
        f.seek(0, 2)  # Go to end
        
        while True:
            line = f.readline()
            if line:
                print(line.rstrip())
            else:
                time.sleep(1)


def list_all_progress():
    """List all available research goals."""
    coscientist_dir = os.environ.get("COSCIENTIST_DIR", os.path.expanduser("~/.coscientist"))
    
    if not os.path.exists(coscientist_dir):
        print("❌ No research found")
        return
    
    print("📋 Available Research Goals:\n")
    
    for item in sorted(os.listdir(coscientist_dir)):
        item_path = os.path.join(coscientist_dir, item)
        if not os.path.isdir(item_path):
            continue
        
        goal_file = os.path.join(item_path, "goal.txt")
        progress_file = os.path.join(item_path, "progress.txt")
        
        if not os.path.exists(goal_file):
            continue
        
        with open(goal_file, "r") as f:
            goal = f.read().strip()
        
        status = "📊 Has progress" if os.path.exists(progress_file) else "⏳ No progress file yet"
        
        print(f"{item}: {goal[:60]}...")
        print(f"  Status: {status}")
        
        if os.path.exists(progress_file):
            with open(progress_file, "r") as f:
                last_line = f.readlines()[-1].strip()
                print(f"  Latest: {last_line}")
        print()


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            list_all_progress()
        else:
            monitor_progress(sys.argv[1])
    else:
        print("Usage:")
        print("  python monitor_progress.py <goal>     # Monitor specific research")
        print("  python monitor_progress.py list       # List all research goals")
        print()
        print("Example:")
        print('  python monitor_progress.py "What is CRISPR?"')


if __name__ == "__main__":
    main()

