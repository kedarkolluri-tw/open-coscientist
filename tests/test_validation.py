#!/usr/bin/env python3
"""
Test that framework validation catches config errors at initialization.
"""

import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)

# Load environment
load_dotenv(".env.test")

from coscientist.framework import CoscientistConfig, CoscientistFramework
from coscientist.global_state import CoscientistState, CoscientistStateManager
from coscientist.validation import ValidationError

def test_validation():
    """Test that framework validates configs at initialization."""
    print("\n" + "=" * 80)
    print("TESTING FRAMEWORK VALIDATION")
    print("=" * 80 + "\n")

    try:
        # This should trigger validation automatically
        goal = "Test goal"
        CoscientistState.clear_goal_directory(goal)  # Clear any previous test
        initial_state = CoscientistState(goal=goal)
        config = CoscientistConfig()
        state_manager = CoscientistStateManager(initial_state)

        print("\nCreating CoscientistFramework (this will validate configs)...\n")
        cosci = CoscientistFramework(config, state_manager)

        print("\n" + "=" * 80)
        print("✅ VALIDATION TEST PASSED - Framework initialized successfully")
        print("=" * 80 + "\n")
        return 0

    except ValidationError as e:
        print("\n" + "=" * 80)
        print("❌ VALIDATION TEST FAILED")
        print("=" * 80)
        print(f"\nValidationError: {e}\n")
        return 1
    except Exception as e:
        print("\n" + "=" * 80)
        print("❌ UNEXPECTED ERROR")
        print("=" * 80)
        print(f"\nError: {e}\n")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(test_validation())
