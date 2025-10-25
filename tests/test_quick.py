#!/usr/bin/env python3

import asyncio
from dotenv import load_dotenv

# Load environment variables before importing anything else
load_dotenv(".env.test")

from coscientist.framework import CoscientistConfig, CoscientistFramework
from coscientist.global_state import CoscientistState, CoscientistStateManager

# Use a very simple, quick goal
goal = "What is CRISPR and how does it work?"

# Clear any existing directory for this goal to start fresh
try:
    CoscientistState.clear_goal_directory(goal)
except:
    pass

initial_state = CoscientistState(goal=goal)

config = CoscientistConfig()
state_manager = CoscientistStateManager(initial_state)
cosci = CoscientistFramework(config, state_manager)

print("=" * 80)
print("Starting Coscientist framework with goal:", goal)
print("=" * 80)

try:
    final_report, final_meta_review = asyncio.run(cosci.run())

    print("\n" + "="*80)
    print("SUCCESS! FINAL REPORT:")
    print("="*80)
    print(final_report)
    print("\n" + "="*80)
    print("META REVIEW:")
    print("="*80)
    print(final_meta_review)
    print("\n" + "="*80)
    print("Test completed successfully!")
    print("="*80)
except Exception as e:
    print(f"\n{'='*80}")
    print(f"ERROR: {e}")
    print(f"{'='*80}")
    import traceback
    traceback.print_exc()
