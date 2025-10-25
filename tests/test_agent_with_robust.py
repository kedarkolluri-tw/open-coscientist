#!/usr/bin/env python3
"""
Test that agents actually work with the new robust parsing.
"""

import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

load_dotenv(".env.test")

from langchain_openai import ChatOpenAI
from coscientist.generation_agent import build_generation_agent, IndependentConfig
from coscientist.reasoning_types import ReasoningType

def test_generation_agent_with_robust_parsing():
    """Test generation agent uses robust parsing successfully."""

    print("\n" + "=" * 80)
    print("TESTING GENERATION AGENT WITH ROBUST PARSING")
    print("=" * 80 + "\n")

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

    # Create agent with independent generation
    config = IndependentConfig(
        field="biology",
        reasoning_type=ReasoningType.INDUCTIVE,
        llm=llm
    )

    agent = build_generation_agent(
        mode="independent",
        config=config
    )

    # Test input
    initial_state = {
        "goal": "How does exercise affect brain health?",
        "literature_review": "Studies show exercise increases BDNF levels.",
        "meta_review": "Focus on mechanistic hypotheses."
    }

    print("Running generation agent...")
    print(f"Goal: {initial_state['goal']}\n")

    try:
        result = agent.invoke(initial_state)

        if "hypothesis" in result:
            hyp = result["hypothesis"]
            print("✅ AGENT SUCCEEDED WITH ROBUST PARSING!\n")
            print(f"Hypothesis: {hyp.hypothesis[:100]}...")
            print(f"Predictions: {len(hyp.predictions)} items")
            print(f"Assumptions: {len(hyp.assumptions)} items")
            print(f"\nFirst prediction: {hyp.predictions[0][:80]}...")
            return True
        else:
            print("❌ No hypothesis in result")
            return False

    except Exception as e:
        print(f"❌ AGENT FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_generation_agent_with_robust_parsing()

    print("\n" + "=" * 80)
    if success:
        print("✅ ROBUST PARSING WORKS IN PRODUCTION AGENTS!")
        print("=" * 80)
        exit(0)
    else:
        print("❌ TEST FAILED - ROBUST PARSING HAS ISSUES")
        print("=" * 80)
        exit(1)
