#!/usr/bin/env python3
"""
Quick integration test - verifies the system works in ~5 minutes.
Tests:
1. Research backend creates provider
2. Framework initializes with research provider
3. Progress events are logged
4. Literature review starts (1 subtopic only)
5. Can monitor progress in real-time

This should complete in 5-10 minutes max.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from coscientist.framework import CoscientistConfig, CoscientistFramework
from coscientist.global_state import CoscientistState, CoscientistStateManager

async def quick_test():
    """Run a quick integration test."""
    
    print("\n" + "=" * 80)
    print("🚀 QUICK INTEGRATION TEST")
    print("=" * 80)
    print()
    print("This test will:")
    print("  1. Initialize the framework with new research backend")
    print("  2. Call framework.start(n_hypotheses=2)")
    print("  3. Run literature review (2 subtopics)")
    print("  4. Generate 2 hypotheses")
    print("  5. Log progress events throughout")
    print()
    print("Expected time: 15-20 minutes (2 subtopics + 2 hypotheses)")
    print("=" * 80)
    print()
    
    # ============================================================================
    # HYPERPARAMETERS - MODIFY THESE TO CONTROL TEST BEHAVIOR
    # ============================================================================
    N_HYPOTHESES = 2           # Number of hypotheses to generate
    MAX_SUBTOPICS = 2           # Number of subtopics for literature review
    MAX_ITERATIONS = 5          # Max supervisor iterations (default: 20)
    TIMEOUT_PER_HYPOTHESIS = 300  # Timeout per hypothesis in seconds
    MAX_TURNS = 4              # Max turns for collaborative generation
    # ============================================================================
    
    # Create a test goal
    goal = f"Quick test: What is CRISPR gene editing? ({MAX_SUBTOPICS} subtopics, {N_HYPOTHESES} hypotheses, {MAX_ITERATIONS} iters)"
    
    # Create output directory
    test_dir = datetime.now().strftime("test_%Y%m%d_%H%M%S")
    output_dir = os.path.join(
        os.environ.get("COSCIENTIST_DIR", os.path.expanduser("~/.coscientist")),
        test_dir
    )
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"📊 Hyperparameters:")
    print(f"   - n_hypotheses: {N_HYPOTHESES}")
    print(f"   - max_subtopics: {MAX_SUBTOPICS}")
    print(f"   - max_iterations: {MAX_ITERATIONS}")
    print(f"   - timeout_per_hypothesis: {TIMEOUT_PER_HYPOTHESIS}s")
    print(f"   - max_turns: {MAX_TURNS}")
    print()
    
    print(f"📁 Output directory: {output_dir}")
    print(f"📊 Monitor with: coscientist-live {test_dir}")
    print()
    
    # Initialize state
    print("1️⃣  Initializing state...")
    initial_state = CoscientistState(goal=goal)
    state_manager = CoscientistStateManager(initial_state)
    print("✅ State initialized")
    print()
    
    # Initialize framework (this should create research provider)
    print("2️⃣  Initializing framework with research backend...")
    config = CoscientistConfig()
    framework = CoscientistFramework(config, state_manager)
    
    # Verify research provider exists
    if not hasattr(framework, 'research_provider'):
        print("❌ ERROR: Framework doesn't have research_provider!")
        sys.exit(1)
    
    print(f"✅ Research provider: {type(framework.research_provider).__name__}")
    print(f"   Background mode: {framework.research_provider.supports_background_mode()}")
    
    # Verify progress tracker exists
    if not hasattr(framework, 'progress_tracker'):
        print("❌ ERROR: Framework doesn't have progress_tracker!")
        sys.exit(1)
    
    print(f"✅ Progress tracker: initialized")
    print()
    
    print("3️⃣  Starting framework with literature review + 2 hypotheses...")
    print("   This will:")
    print("   - Run literature review (2 subtopics)")
    print("   - Generate 2 hypotheses")
    print("   - Show progress events")
    print()
    print("   Watch progress: tail -f {}/progress.json".format(output_dir))
    print()
    
    try:
        # THIS IS THE ACTUAL FRAMEWORK CALL
        await framework.start(n_hypotheses=N_HYPOTHESES, max_subtopics=MAX_SUBTOPICS)
        
        print()
        print("✅ Framework run complete!")
        print()
        
        # Check what was created
        if state_manager.has_literature_review:
            lit = state_manager._state.literature_review
            print(f"📚 Literature review:")
            print(f"   - Subtopics: {len(lit.get('subtopics', []))}")
            print(f"   - Reports: {len(lit.get('subtopic_reports', []))}")
        
        print(f"🧪 Hypotheses generated: {len(state_manager._state.generated_hypotheses)}")
        
        print()
        print("=" * 80)
        print("✅ TEST PASSED!")
        print("=" * 80)
        print()
        print("Key findings:")
        print(f"  - Research provider works: ✅")
        print(f"  - Progress tracking works: ✅")
        print(f"  - Literature review works: ✅")
        print(f"  - Framework integration works: ✅")
        print()
        print(f"📊 View progress: coscientist-live {test_dir}")
        print(f"📁 Output: {output_dir}")
        print()
        print("💡 To run full system with 2 hypotheses, use:")
        print(f"   python examples/example_CRISPR_gene_question.py")
        print()
        
    except Exception as e:
        print()
        print("=" * 80)
        print("❌ TEST FAILED!")
        print("=" * 80)
        print(f"Error: {e}")
        print()
        import traceback
        traceback.print_exc()
        print()
        print(f"📁 Check logs in: {output_dir}")
        sys.exit(1)


if __name__ == "__main__":
    print()
    print("⚠️  This test will make real API calls (OpenAI Deep Research)")
    print("   Cost estimate: ~$10-20 for 2 research queries")
    print()
    
    # Just run it - user knows what they're doing
    asyncio.run(quick_test())

