#!/usr/bin/env python3
"""
List all research goals and their state.
"""
import os
from glob import glob

coscientist_dir = os.path.expanduser("~/.coscientist")

if not os.path.exists(coscientist_dir):
    print("❌ No research goals found.")
    exit(0)

print("🔬 All Research Goals\n")
print("="*80)

for item in sorted(os.listdir(coscientist_dir)):
    item_path = os.path.join(coscientist_dir, item)
    if not os.path.isdir(item_path):
        continue
    
    goal_file = os.path.join(item_path, "goal.txt")
    if not os.path.exists(goal_file):
        continue
    
    # Read goal
    with open(goal_file, "r") as f:
        goal = f.read().strip()
    
    # Find state files
    state_files = glob(os.path.join(item_path, "coscientist_state*.pkl"))
    
    # Get the latest one
    if state_files:
        latest = max(state_files, key=os.path.getmtime)
        mtime = os.path.getmtime(latest)
        import time
        mtime_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mtime))
    else:
        mtime_str = "No state files"
    
    print(f"📁 Hash: {item}")
    print(f"📝 Goal: {goal}")
    print(f"⏰ Last updated: {mtime_str}")
    print(f"💾 State files: {len(state_files)}")
    print("-"*80)

