#!/usr/bin/env python3
"""
Quick test to verify the new research backend works.
Tests that we can:
1. Create a research provider
2. Initiate research
3. Get progress updates
"""

import asyncio
import logging
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO)

from coscientist.research_backend import create_research_provider
from coscientist.config_loader import load_researcher_config
from coscientist.progress_events import ProgressTracker

async def test_research_backend():
    """Test the new research backend."""
    
    print("🧪 Testing Research Backend")
    print("=" * 80)
    
    # Get config
    config = load_researcher_config()
    backend = config.get("RESEARCH_BACKEND", "openai_deep_research")
    print(f"📋 Backend: {backend}")
    
    # Create provider
    output_dir = f"/tmp/coscientist_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"📁 Output dir: {output_dir}")
    print()
    
    provider = create_research_provider(config, output_dir)
    print(f"✅ Provider created: {type(provider).__name__}")
    print(f"   Supports background: {provider.supports_background_mode()}")
    print()
    
    # Test query
    query = "What are the latest advances in CRISPR gene editing?"
    task_id = "test_1"
    
    print(f"🔬 Test query: {query[:60]}...")
    print()
    
    try:
        if provider.supports_background_mode():
            print("⏳ Starting background research...")
            response_id = await provider.conduct_research(query, task_id)
            print(f"📝 Response ID: {response_id}")
            print()
            
            print("🔄 Polling for results...")
            max_polls = 20  # Max 10 minutes
            for i in range(max_polls):
                result = await provider.get_result(task_id)
                if result:
                    print(f"✅ Research complete! ({len(result)} chars)")
                    print()
                    print("📄 First 500 chars of result:")
                    print(result[:500])
                    return
                
                # Show progress
                progress = provider.get_progress(task_id)
                print(f"   Poll {i+1}/{max_polls}: {progress['details']} ({progress['percent']}%)")
                
                await asyncio.sleep(30)  # Wait 30 seconds between polls
            
            print("⏱️  Test timed out after 10 minutes")
        else:
            print("⏳ Starting blocking research...")
            result = await provider.conduct_research(query, task_id)
            print(f"✅ Research complete! ({len(result)} chars)")
            print()
            print("📄 First 500 chars of result:")
            print(result[:500])
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n⚠️  NOTE: This will make an actual API call and cost money.")
    print("   Make sure you have:")
    print("   - OPENAI_API_KEY set (for OpenAI Deep Research)")
    print("   - Or PERPLEXITY_API_KEY (for Perplexity)")
    print("   - Or researcher_config.json configured for GPT-Researcher")
    print()
    user_input = input("Continue? (yes/no): ")
    
    if user_input.lower() == "yes":
        asyncio.run(test_research_backend())
    else:
        print("Test cancelled.")

