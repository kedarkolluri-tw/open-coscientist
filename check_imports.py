#!/usr/bin/env python3
"""
Check that all imports in coscientist_interact are correct.
"""
import sys

def test_imports():
    """Test that all modules can be imported."""
    errors = []
    
    # Test core coscientist modules
    try:
        from coscientist.framework import CoscientistConfig, CoscientistFramework
        print("✅ coscientist.framework imports")
    except Exception as e:
        errors.append(f"❌ coscientist.framework: {e}")
    
    try:
        from coscientist.global_state import CoscientistState, CoscientistStateManager
        print("✅ coscientist.global_state imports")
    except Exception as e:
        errors.append(f"❌ coscientist.global_state: {e}")
    
    # Test coscientist.interact modules
    try:
        from coscientist.interact.common import get_available_states
        print("✅ coscientist.interact.common imports")
    except Exception as e:
        errors.append(f"❌ coscientist.interact.common: {e}")
    
    try:
        from coscientist.interact.background import (
            check_coscientist_status,
            coscientist_process_target,
        )
        print("✅ coscientist.interact.background imports")
    except Exception as e:
        errors.append(f"❌ coscientist.interact.background: {e}")
    
    try:
        from coscientist.interact.tournament_viewer import main
        print("✅ coscientist.interact.tournament_viewer imports")
    except Exception as e:
        errors.append(f"❌ coscientist.interact.tournament_viewer: {e}")
    
    try:
        from coscientist.interact.resume_page import display_resume_page
        print("✅ coscientist.interact.resume_page imports")
    except Exception as e:
        errors.append(f"❌ coscientist.interact.resume_page: {e}")
    
    try:
        from coscientist.interact.tournament_page import display_tournament_page
        print("✅ coscientist.interact.tournament_page imports")
    except Exception as e:
        errors.append(f"❌ coscientist.interact.tournament_page: {e}")
    
    try:
        from coscientist.interact.configuration_page import display_configuration_page
        print("✅ coscientist.interact.configuration_page imports")
    except Exception as e:
        errors.append(f"❌ coscientist.interact.configuration_page: {e}")
    
    # Print results
    if errors:
        print("\n❌ Import errors found:")
        for error in errors:
            print(f"  {error}")
        return False
    else:
        print("\n✅ All imports successful!")
        return True

if __name__ == "__main__":
    sys.path.insert(0, '.')
    success = test_imports()
    sys.exit(0 if success else 1)

