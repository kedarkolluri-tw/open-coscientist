#!/usr/bin/env python3
"""
Example: Running a research task on CRISPR gene editing.

This example demonstrates:
1. Starting a new research task
2. Monitoring progress in real-time  
3. Resuming from checkpoints if interrupted
4. Viewing results in the interactive UI

Usage:
    # Terminal 1: Run the research
    python examples/example_CRISPR_gene_question.py

    # Terminal 2: Monitor progress
    coscientist-monitor research_20251025_143000

    # Or view results when finished
    coscientist-interact
"""

import asyncio
import logging
import os

# Set up logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from coscientist.framework import CoscientistConfig, CoscientistFramework
from coscientist.global_state import CoscientistState, CoscientistStateManager
from coscientist.status_manager import get_research_status, ResearchStatus

# Optional: Use a custom storage location
# os.environ["COSCIENTIST_DIR"] = "./my_research_data"


def main():
    """Run a research task on CRISPR gene editing."""
    
    # Define your research question
    goal = "What is CRISPR gene editing and how does it work?"
    
    print(f"\n🚀 Starting research on: {goal}\n")
    print("="*80)
    
    # Create new state (gets datetime-based directory)
    initial_state = CoscientistState(goal=goal)
    output_dir = initial_state._output_dir
    dir_name = os.path.basename(output_dir)
    
    print(f"📁 Research directory: {dir_name}")
    print(f"📝 Progress tracking: {output_dir}/progress.txt")
    print(f"📊 Status file: {output_dir}/status.json")
    
    # Check if directory already exists (shouldn't happen with datetime)
    status, details = get_research_status(output_dir)
    
    if status == ResearchStatus.COMPLETED:
        print("\n✅ This research has already completed!")
        print("💡 View results with: coscientist-interact")
        return
    elif status == ResearchStatus.ERROR:
        print("\n❌ Previous research encountered an error.")
        print("💡 Check error.log for details")
        error_msg = details.get("error", "Unknown error")
        print(f"   Error: {error_msg}")
        return
    elif status == ResearchStatus.RUNNING:
        print("\n⚠️  Research appears to be running in another process.")
        print("💡 Check the status: coscientist-status " + dir_name)
        return
    
    # Create framework
    print("\n⚙️  Configuring framework...")
    config = CoscientistConfig()
    state_manager = CoscientistStateManager(initial_state)
    cosci = CoscientistFramework(config, state_manager)
    
    print("\n🎯 Starting research process...")
    print("="*80 + "\n")
    
    # Run research (takes 1-2 hours for complete run)
    # The system will:
    # 1. Conduct literature review
    # 2. Generate initial hypotheses
    # 3. Review and rank hypotheses through tournament
    # 4. Generate meta-reviews
    # 5. Continue for up to 20 iterations
    # 6. Generate final report
    
    try:
        final_report, final_meta_review = asyncio.run(cosci.run())
        
        print("\n" + "="*80)
        print("✅ RESEARCH COMPLETE!")
        print("="*80)
        print("\n📄 Final Report:\n")
        print(final_report)
        print("\n" + "="*80)
        print("📊 Meta Review:\n")
        print(final_meta_review)
        print("="*80)
        
        print(f"\n📁 Research directory: {dir_name}")
        print("\n💡 To view results interactively:")
        print("   coscientist-interact")
        print()
        
    except KeyboardInterrupt:
        print("\n⚠️  Research interrupted by user")
        print(f"💡 To resume later, work with directory: {dir_name}")
        print("\n💡 To resume from this directory:")
        print(f"   state = CoscientistState.load_latest(goal=\"{goal}\")")
        print(f"   # Or manually load from: {output_dir}")
        print()
    except Exception as e:
        print(f"\n❌ Error during research: {e}")
        import traceback
        traceback.print_exc()
        print(f"\n💡 Progress is saved in: {output_dir}")
        print("💡 Status can be checked with:")
        print(f"   coscientist-status {dir_name}")


def resume_from_directory(directory_name: str):
    """
    Example: Resume research from a specific directory.
    
    This is useful when:
    - Research was interrupted (KeyboardInterrupt, crash)
    - Want to continue from last checkpoint
    - Know the exact directory name
    
    Usage:
        python examples/example_CRISPR_gene_question.py resume research_20251025_143000
    """
    
    print(f"\n🔄 Resuming research from: {directory_name}\n")
    
    # Find the directory
    coscientist_dir = os.environ.get("COSCIENTIST_DIR", os.path.expanduser("~/.coscientist"))
    
    if not os.path.isabs(directory_name):
        full_dir = os.path.join(coscientist_dir, directory_name)
    else:
        full_dir = directory_name
    
    if not os.path.exists(full_dir):
        print(f"❌ Directory not found: {full_dir}")
        return
    
    # Read goal from directory
    goal_file = os.path.join(full_dir, "goal.txt")
    with open(goal_file, "r") as f:
        goal = f.read().strip()
    
    print(f"📝 Goal: {goal}")
    
    # Load the latest state from this directory
    state = CoscientistState.load_latest(directory=full_dir)
    
    if not state:
        print("❌ No checkpoints found in this directory")
        return
    
    print("✅ Loaded existing state")
    print(f"   Generated: {len(state.generated_hypotheses)} hypotheses")
    print(f"   Reviewed: {len(state.reviewed_hypotheses)} hypotheses")
    print(f"   Actions: {len(state.actions)} actions taken")
    
    # Create framework with existing state
    config = CoscientistConfig()
    state_manager = CoscientistStateManager(state)
    cosci = CoscientistFramework(config, state_manager)
    
    # Continue from where we left off
    final_report, meta_review = asyncio.run(cosci.run())
    
    print("\n✅ Research completed!")
    print(final_report)


def list_research():
    """List all available research projects."""
    from coscientist.global_state import CoscientistState
    
    print("\n📋 Available Research Projects:\n")
    
    goals = CoscientistState.list_all_goals()
    
    if not goals:
        print("  No research found")
        return
    
    for i, (goal_text, dir_name) in enumerate(goals, 1):
        print(f"{i}. {dir_name}")
        print(f"   Goal: {goal_text[:70]}...")
        
        # Check status
        coscientist_dir = os.environ.get("COSCIENTIST_DIR", os.path.expanduser("~/.coscientist"))
        full_dir = os.path.join(coscientist_dir, dir_name)
        
        try:
            status, _ = get_research_status(full_dir)
            print(f"   Status: {status.value}")
        except:
            print(f"   Status: unknown")
        print()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "resume" and len(sys.argv) > 2:
            resume_from_directory(sys.argv[2])
        elif sys.argv[1] == "list":
            list_research()
        else:
            print("Usage:")
            print("  python examples/example_CRISPR_gene_question.py           # Start new research")
            print("  python examples/example_CRISPR_gene_question.py resume <dir>  # Resume from directory")
            print("  python examples/example_CRISPR_gene_question.py list      # List all research")
    else:
        main()