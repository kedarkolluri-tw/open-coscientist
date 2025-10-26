#!/usr/bin/env python3
"""
Quick script to check the progress of the current research run.
"""

import os
import pickle
from glob import glob

# Find the most recent state file
coscientist_dir = os.path.expanduser("~/.coscientist")
state_files = glob(os.path.join(coscientist_dir, "*/coscientist_state*.pkl"))

if not state_files:
    print("❌ No state files found.")
    exit(1)

# Get the most recent file
latest_file = max(state_files, key=os.path.getmtime)
print(f"📁 Loading state from: {latest_file}")

# Load the state
with open(latest_file, "rb") as f:
    state = pickle.load(f)

print("\n" + "="*80)
print(f"Goal: {state.goal}")
print("="*80)

print(f"\n✅ Has literature review: {state.literature_review is not None}")
print(f"📝 Generated hypotheses: {len(state.generated_hypotheses)}")
print(f"✅ Reviewed hypotheses: {len(state.reviewed_hypotheses)}")
print(f"🏆 Tournament: {'Yes' if state.tournament is not None else 'No'}")
print(f"📊 Meta reviews: {len(state.meta_reviews)}")
print(f"🔄 Reflection queue: {len(state.reflection_queue)}")
print(f"📋 Actions taken: {len(state.actions)}")
print(f"📄 Final report: {'Yes' if state.final_report else 'No'}")

if state.actions:
    print(f"\n📈 Last 5 actions:")
    for action in state.actions[-5:]:
        print(f"  - {action}")

if state.reviewed_hypotheses:
    print(f"\n🏆 Top hypotheses:")
    for i, hyp in enumerate(state.reviewed_hypotheses[:3]):
        print(f"  {i+1}. {hyp.hypothesis[:100]}...")

if state.meta_reviews:
    print(f"\n📊 Latest meta review:")
    latest = state.meta_reviews[-1]
    print(f"   {latest.get('result', 'N/A')[:200]}...")

print("\n" + "="*80)

