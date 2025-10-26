#!/usr/bin/env python3
"""
Resume a research goal from the latest checkpoint.
"""
import sys
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")

import logging
logging.basicConfig(level=logging.INFO)

from coscientist.framework import CoscientistConfig, CoscientistFramework
from coscientist.global_state import CoscientistState, CoscientistStateManager

def list_goals():
    """List all available research goals."""
    goals = CoscientistState.list_all_goals()
    
    if not goals:
        print("❌ No research goals found.")
        return None
    
    print("\n📋 Available Research Goals:\n")
    for i, (goal, goal_hash) in enumerate(goals, 1):
        # Get latest checkpoint info
        checkpoints = CoscientistState.list_checkpoints(goal=goal)
        if checkpoints:
            import time
            mtime = os.path.getmtime(checkpoints[0])
            mtime_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mtime))
        else:
            mtime_str = "No checkpoints"
        
        print(f"{i}. [{goal_hash}]")
        print(f"   {goal[:80]}...")
        print(f"   Last updated: {mtime_str}")
        print()
    
    return goals

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 resume_research.py <goal_number>")
        print("\nListing available goals...")
        list_goals()
        sys.exit(1)
    
    goal_number = int(sys.argv[1])
    goals = CoscientistState.list_all_goals()
    
    if not goals or goal_number < 1 or goal_number > len(goals):
        print(f"❌ Invalid goal number. Please choose 1-{len(goals) if goals else 0}")
        list_goals()
        sys.exit(1)
    
    goal, goal_hash = goals[goal_number - 1]
    
    print(f"\n🔄 Resuming research for:")
    print(f"📝 Goal: {goal}")
    print(f"📁 Hash: {goal_hash}\n")
    
    # Load the latest state
    state = CoscientistState.load_latest(goal=goal)
    
    if not state:
        print("❌ No checkpoint found for this goal.")
        sys.exit(1)
    
    print(f"✅ Loaded checkpoint from: {state._output_dir}")
    print(f"📊 State: {len(state.generated_hypotheses)} generated, {len(state.reviewed_hypotheses)} reviewed")
    
    # Continue research
    config = CoscientistConfig()
    state_manager = CoscientistStateManager(state)
    cosci = CoscientistFramework(config, state_manager)
    
    print("\n🚀 Continuing research...\n")
    final_report, final_meta_review = asyncio.run(cosci.run())
    
    print("\n" + "="*80)
    print("✅ FINAL REPORT:")
    print("="*80)
    print(final_report)
    print("\n" + "="*80)
    print("📊 META REVIEW:")
    print("="*80)
    print(final_meta_review)
    print("="*80)

if __name__ == "__main__":
    main()

